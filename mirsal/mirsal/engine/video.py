"""Part B: prepared grid MP4 (3x3 / 2x2 / 1x1) -> transparent looping WEBM per cell. Same keyer as stills, same settings."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

import cv2
import numpy as np

from . import ffmpeg as ff
from . import verify
from .chroma import calibrate, despill, key_image, remove_specks
from .render import bbox_of, fit_scale, render_sticker
from .verify import Report


@dataclass
class AnimationResult:
    index: int
    status: str            # READY | FAILED
    reason: str | None = None
    report: Report = field(default_factory=Report)
    metrics: dict = field(default_factory=dict)
    data: bytes | None = None


def loop_seam(last: np.ndarray, first: np.ndarray) -> float:
    """Alpha-weighted mean abs difference between the last and first frame (0-255 scale)."""
    a1, a2 = last[..., 3], first[..., 3]
    w = cv2.max(a1, a2).astype(np.float32) * (1 / 255.0)
    d = cv2.absdiff(last[..., :3], first[..., :3]).sum(-1, dtype=np.uint16).astype(np.float32) * (1 / 3.0)
    return float((w * d + cv2.absdiff(a1, a2)).sum() / max(float(w.sum()), 1.0))


def edge_energy(rgba: np.ndarray) -> float:
    """Mean luminance gradient over the opaque subject: how much edge detail a frame carries (a blur lowers it). Used as a ratio, decoded / encoded input."""
    y = cv2.cvtColor(np.ascontiguousarray(rgba[..., :3]), cv2.COLOR_RGB2GRAY).astype(np.float32)
    g = np.hypot(cv2.Sobel(y, cv2.CV_32F, 1, 0), cv2.Sobel(y, cv2.CV_32F, 0, 1))
    m = rgba[..., 3] > 8
    return float(g[m].mean()) if m.any() else 0.0


def detail_vs_ref(frames: np.ndarray, ref_rgba: np.ndarray, n: int = 3) -> float | None:
    """How much of the approved STILL's edge detail the animation carries: mean edge energy of the first frames over the still's. The old encode-only
    ratio (decoded / encoder input) could not see softening that happened BEFORE the encode (a 320 px source cell upscaled to 512, a cheaper video
    model), because both sides were already soft. Measured on the real G001-G005 animations (2026-10-02): batches that were as sharp as their stills read
    0.89 and up (above 1.0 where the video is sharper than the still), the soft G002 batch (320 px cells, Kling std) read 0.58-0.72 (mean 0.65). None when there is no still or it has no edges."""
    if ref_rgba is None or getattr(ref_rgba, "ndim", 0) != 3 or ref_rgba.shape[2] != 4:
        return None
    e_ref = edge_energy(ref_rgba)
    if e_ref <= 0:
        return None
    return float(np.mean([edge_energy(f) for f in frames[:n]])) / e_ref


def soft_sigma(ref_rgba: np.ndarray, ratio: float) -> float:
    """The Gaussian blur radius (px) that takes the still down to `ratio` of its own edge detail: 'as soft as the still blurred N px'.
    0.0 when the animation is as sharp as the still; capped at 4 px."""
    if ratio is None or ratio >= 1.0:
        return 0.0
    e0 = edge_energy(ref_rgba)
    best, prev_s, prev_r = 4.0, 0.0, 1.0
    for s in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
        b = ref_rgba.copy()
        b[..., :3] = cv2.GaussianBlur(np.ascontiguousarray(ref_rgba[..., :3]), (0, 0), s)
        r = edge_energy(b) / e0
        if r <= ratio:
            span = prev_r - r
            best = prev_s + (s - prev_s) * ((prev_r - ratio) / span if span > 1e-9 else 1.0)
            break
        prev_s, prev_r = s, r
    return round(best, 1)


def support(frames: np.ndarray) -> np.ndarray:
    """The part of the frames where anything is ever opaque. Outside it both frames are transparent and a seam adds exactly 0, so the
    seam maths is the same on this crop and 2-3x cheaper."""
    ys, xs = np.where(frames[..., 3].max(0) > 0)
    return frames[:, ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else frames


def close_loop(frames: np.ndarray, m: int) -> np.ndarray:
    """Close a clip that does not loop by easing its LAST `m` frames into frame 0 (the last frame becomes frame 0 itself, so the wrap has no jump).
    The head is never touched: the clip starts on its own first frame, the approved pose and the thumbnail. (It used to start on the tail's pose and
    dissolve into the head, which showed as a ghost on the first frames.) The last `m` source frames are dropped to make room for the fade."""
    n = len(frames)
    if m < 1 or n < 2 * m + 2:
        return frames
    out = frames[: n - m].astype(np.float32).copy()
    head = frames[0].astype(np.float32)
    for j in range(m):
        t = (j + 1) / m
        w = t * t * (3 - 2 * t)         # smoothstep: starts gently, ends on frame 0 and slows into it
        out[n - 2 * m + j] = (1 - w) * out[n - 2 * m + j] + w * head
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def vp9_missing(cells) -> list[AnimationResult] | None:
    """Fail fast with a named reason instead of one 'exception' per cell when ffmpeg cannot encode VP9+alpha."""
    if ff.has_vp9():
        return None
    return [AnimationResult(i, "FAILED", "no_vp9_encoder",
                            metrics={"error": f"{ff.ffmpeg_exe()} has no libvpx-vp9: pip install imageio-ffmpeg (see doctor)"})
            for i in cells]


CACHE_VERSION = 3      # bump when an engine change makes old cached animations wrong


class AnimCache:
    """A finished animation is saved by what made it (the source file's size and time, the cell, every engine setting, the verifier version),
    so the same prepared video animated again, in a new batch or after a restart, is read back instead of rendered, encoded and checked again."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def key(self, cfg, *parts) -> str:
        c = asdict(cfg); c.pop("anim_workers", None)
        raw = json.dumps([CACHE_VERSION, verify.VERIFY_VERSION, c, parts], sort_keys=True, default=str)
        return hashlib.sha1(raw.encode()).hexdigest()[:24]

    def get(self, key: str, idx: int):
        j = self.root / f"{key}.json"
        try:
            d = json.loads(j.read_text(encoding="utf-8"))
            data = (self.root / f"{key}.webm").read_bytes() if d["has_data"] else None
        except (OSError, ValueError, KeyError):
            return None
        rep = Report([verify.Check(c["name"], c["stage"], c["severity"], c["ok"], c["value"], c["limit"], c["data"], c["detail"]) for c in d["checks"]])
        m = dict(d["metrics"], cache="hit")
        return AnimationResult(idx, d["status"], d["reason"], rep, m, data)

    def put(self, key: str, r: AnimationResult) -> None:
        if r.reason in ("exception", "no_video_source", "probe_failed") or "error" in r.metrics:
            return                                                    # a hiccup, not an answer: try again next time
        self.root.mkdir(parents=True, exist_ok=True)
        tag = f"{os.getpid()}.{threading.get_ident()}"
        if r.data:
            (self.root / f"{key}.webm.{tag}").write_bytes(r.data)
            os.replace(self.root / f"{key}.webm.{tag}", self.root / f"{key}.webm")
        body = {"status": r.status, "reason": r.reason, "metrics": verify._plain(r.metrics), "checks": r.report.checks, "has_data": bool(r.data)}
        (self.root / f"{key}.json.{tag}").write_text(json.dumps(body), encoding="utf-8")
        os.replace(self.root / f"{key}.json.{tag}", self.root / f"{key}.json")      # the json lands last: a half-written entry is never read


def _stat_id(path) -> list:
    st = Path(path).stat()
    return [str(Path(path).resolve()), st.st_size, st.st_mtime_ns]


def _cached(cache, key, idx, compute) -> AnimationResult:
    if cache is not None and key:
        hit = cache.get(key, idx)
        if hit is not None:
            return hit
    res = compute()
    if cache is not None and key:
        cache.put(key, res)
    return res


def _ms(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


class _Polite:
    """While a batch of cells renders: this process at below-normal priority (Windows) and OpenCV on 2 threads, so N parallel cells do not each
    start one OpenCV thread per core. Both are put back afterwards."""
    def __enter__(self):
        self.cv = cv2.getNumThreads()
        cv2.setNumThreads(2)
        self.prio = None
        if sys.platform == "win32":
            try:
                import ctypes
                k = ctypes.windll.kernel32
                self.prio = k.GetPriorityClass(k.GetCurrentProcess())
                k.SetPriorityClass(k.GetCurrentProcess(), ff.LOW_PRIORITY)
            except Exception:
                self.prio = None
        return self

    def __exit__(self, *a):
        cv2.setNumThreads(self.cv)
        if self.prio:
            try:
                import ctypes
                k = ctypes.windll.kernel32
                k.SetPriorityClass(k.GetCurrentProcess(), self.prio)
            except Exception:
                pass


def _run_cells(cells, fn, cfg, on_cell=None) -> list[AnimationResult]:
    """fn(cell) -> AnimationResult for every cell, a few at a time (ffmpeg, OpenCV and numpy release the GIL).
    on_cell is called one at a time, so a caller may mutate and save shared state in it. A cell never raises past here."""
    lock = threading.Lock()

    def job(idx):
        try:
            res = fn(idx)
        except Exception as e:
            res = AnimationResult(idx, "FAILED", "exception", metrics={"error": str(e)[:300]})
        if on_cell:
            with lock:
                on_cell(res)
        return res
    cells = list(cells)
    with _Polite(), ThreadPoolExecutor(max_workers=max(1, min(cfg.anim_workers, len(cells)))) as ex:
        return list(ex.map(job, cells))


def process_video(mp4, cfg, cells: list[int] | None = None, on_probe=None, on_cell=None,
                  rects: list | None = None, sheet_wh: tuple | None = None, layout: dict | None = None, refs: dict | None = None,
                  cache: AnimCache | None = None, waive: dict | None = None) -> list[AnimationResult]:
    """waive = {slot: {check ids}}: slot-geometry blocks (inside_slot, cross_slot) that a human has allowed for that cell; they become warnings.
    rects/sheet_wh: the still's measured cell rects on the sheet; mapped onto the video (same layout, any size).
    Without them: equal thirds. layout (a video sheet's layout.json): its exact slot rectangles, plus the slot checks
    (inside_slot, cross_slot) on every frame; refs = {slot: approved still's alpha} for identity_kept."""
    from .grid import scale_rects
    if layout:
        rects, sheet_wh = [tuple(sl["rect"]) for sl in layout["slots"]], tuple(layout["canvas"])
    cells = cells or list(range(1, (len(rects) if rects else 9) + 1))
    failed = vp9_missing(cells)
    if failed:
        for r in failed:
            on_cell and on_cell(r)
        return failed
    info = ff.probe(mp4)
    if on_probe:
        on_probe(info)
    if not info["width"] or not info["fps"]:
        return [AnimationResult(i, "FAILED", "probe_failed") for i in cells]
    W, H = info["width"], info["height"]
    if rects and sheet_wh:
        vr = scale_rects(rects, sheet_wh, (W, H))
    else:
        cw, ch = W // 3, H // 3
        vr = [(c * cw, r * ch, cw, ch) for r in range(3) for c in range(3)]
    cap_fps = cfg.video_max_fps if info["fps"] > cfg.video_max_fps else None
    fps = cfg.video_max_fps if cap_fps else info["fps"]
    max_frames = int(math.floor(cfg.video_max_seconds * fps))
    src = _stat_id(mp4)
    def refkey(idx):                                        # a video sheet is judged against its own approved still, so the still is part of the key
        a = (refs or {}).get(idx)
        return hashlib.sha1(a.tobytes()).hexdigest()[:16] if a is not None else None
    use_cache = cache
    return _run_cells(cells, lambda idx: _cached(use_cache, use_cache and use_cache.key(cfg, "mp4", src, list(vr[idx - 1]), fps, cap_fps, max_frames, bool(layout), refkey(idx), sorted((waive or {}).get(idx, ()))), idx,
                                                  lambda: _one_cell(mp4, idx, vr[idx - 1], fps, cap_fps, max_frames, cfg, bool(layout), (refs or {}).get(idx), (waive or {}).get(idx, ()))),
                      cfg, on_cell)


def _one_cell(mp4, idx, rect, fps, cap_fps, max_frames, cfg, slot=False, ref_alpha=None, waive=()) -> AnimationResult:
    x, y, cw, ch = rect
    t0 = time.perf_counter()
    frames = ff.decode_cell(mp4, x, y, cw, ch, max_frames, cap_fps)   # one cell at a time
    t_dec = _ms(t0); t1 = time.perf_counter()
    try:
        calib = calibrate(frames[0], cfg.chroma, cfg.border_px, cfg.threshold, validate=True)      # sample bg ONCE, validate the key difference
    except ValueError as e:
        # Wrong chroma key used (e.g., green key on a blue screen) - fail immediately instead of producing a "blue screen" result
        return AnimationResult(idx, "FAILED", "wrong_chroma_key", metrics={"error": str(e)[:200], "chroma": cfg.chroma})
    keyed = [key_image(f, cfg, calib).rgba for f in frames]
    return _finish(idx, keyed, fps, cfg, {"source": "video sheet" if slot else "3x3 mp4", "threshold": round(calib[1], 1), "ms": {"decode": t_dec, "key": _ms(t1)}}, slot, ref_alpha, waive)


def keyed_cell(mp4, rect, cap_fps, max_frames, cfg) -> list:
    """One cell of the prepared 3x3 video as keyed RGBA frames (decode + key only: no render, no encode)."""
    x, y, cw, ch = rect
    frames = ff.decode_cell(mp4, x, y, cw, ch, max_frames, cap_fps)
    calib = calibrate(frames[0], cfg.chroma, cfg.border_px, cfg.threshold)
    return [key_image(f, cfg, calib).rgba for f in frames]


def keyed_clip(path, cfg) -> list:
    """One pre-sliced transparent clip as cleaned RGBA frames (decode + clean only)."""
    info = ff.probe(path)
    w, h, fps = info["width"], info["height"], info["fps"] or 24.0
    cap_fps = cfg.video_max_fps if fps > cfg.video_max_fps else None
    fps = cfg.video_max_fps if cap_fps else fps
    return [_clean_clip(f, cfg) for f in ff.decode_full(path, w, h, int(math.floor(cfg.video_max_seconds * fps)), cap_fps)]


def bounds_check(keyed, cfg):
    """The inside_frame Check on keyed cell frames (the same rule every new animation gets before it is encoded)."""
    return verify.run("slot", {"cell_frames": keyed, "metrics": {}}, cfg)[0]


def _clean_clip(frame: np.ndarray, cfg) -> np.ndarray:
    """Pre-sliced clips already carry alpha. Floor the haze, drop specks, despill the edge band."""
    a = frame[..., 3].astype(np.float32) / 255.0
    a = np.where(a < cfg.clip_alpha_floor / 255.0, 0.0, a).astype(np.float32)
    a = remove_specks(a, cfg.min_component_px)
    rgb = despill(frame[..., :3], a, cfg.chroma, cfg.despill_band_px)
    return np.dstack([rgb, np.clip(a * 255.0 + 0.5, 0, 255).astype(np.uint8)])


def pick_clip(formats: dict, cfg):
    for f in cfg.clip_prefer:
        if f in formats:
            return f, Path(formats[f])
    f = next(iter(formats))
    return f, Path(formats[f])


def process_clips(clips: dict, cfg, on_cell=None, cache: AnimCache | None = None) -> list[AnimationResult]:
    """clips = {cell: {"mov": path, "webm": path}} of pre-sliced transparent clips."""
    failed = vp9_missing(list(clips))
    if failed:
        for r in failed:
            on_cell and on_cell(r)
        return failed
    def one(idx):
        fmt, path = pick_clip(clips[idx], cfg)
        t0 = time.perf_counter()
        info = ff.probe(path)
        w, h = info["width"], info["height"]
        fps = info["fps"] or 24.0
        cap_fps = cfg.video_max_fps if fps > cfg.video_max_fps else None
        fps = cfg.video_max_fps if cap_fps else fps
        frames = ff.decode_full(path, w, h, int(math.floor(cfg.video_max_seconds * fps)), cap_fps)
        t_dec = _ms(t0); t1 = time.perf_counter()
        keyed = [_clean_clip(f, cfg) for f in frames]
        return _finish(idx, keyed, fps, cfg, {"source": f"clip:{fmt}", "clip": path.name, "clip_size": f"{w}x{h}", "ms": {"decode": t_dec, "key": _ms(t1)}})
    return _run_cells(clips, lambda idx: _cached(cache, cache and cache.key(cfg, "clip", _stat_id(pick_clip(clips[idx], cfg)[1])), idx, lambda: one(idx)), cfg, on_cell)


CRF_START = 3         # ladder index every fit starts at (3 = crf 42): most clips land within a rung or two of it


def _encode_fit(frames, fps, cfg, path, start: int = CRF_START) -> tuple[int, bytes, int]:
    """The best quality (lowest crf of the ladder) whose WEBM fits the size budget. Starts at `start` and walks to the boundary, so most
    clips take 2 encodes instead of walking the whole ladder from the top. The start is an argument, never shared state: VP9 size is not
    strictly monotonic in crf, so a start that depended on which clip another worker thread fitted last made the same clip get different
    crfs. If nothing fits the last rung is returned (the size_budget check then blocks it)."""
    ladder = cfg.crf_ladder
    got: dict[int, bytes] = {}

    def fits(i: int) -> bool:
        ff.encode_webm(frames, fps, ladder[i], path)
        got[i] = path.read_bytes()
        return len(got[i]) <= cfg.video_max_bytes
    i = min(start, len(ladder) - 1)
    if fits(i):
        while i > 0 and fits(i - 1):
            i -= 1
    else:
        i += 1
        while i < len(ladder) and not fits(i):
            i += 1
        i = min(i, len(ladder) - 1)
    return ladder[i], got[i], len(got)


def _finish(idx, keyed, fps, cfg, m, slot=False, ref_alpha=None, waive=()) -> AnimationResult:
    ms = m.setdefault("ms", {})                       # where the time went, per stage (read by `python -m mirsal profile` and kept in result.json)
    t_all = time.perf_counter(); t = time.perf_counter()
    union = None
    for k in keyed:
        b = bbox_of(k[..., 3])
        if b:
            union = b if union is None else (min(union[0], b[0]), min(union[1], b[1]), max(union[2], b[2]), max(union[3], b[3]))
    m.update({"frames": len(keyed), "fps": fps, "bbox": list(union) if union else None})
    if union is None:
        return AnimationResult(idx, "FAILED", "empty_subject", metrics=m)
    h, w = keyed[0].shape[:2]
    ring = np.zeros((h, w), bool)
    ring[:2] = True; ring[-2:] = True; ring[:, :2] = True; ring[:, -2:] = True
    touch = sum(1 for k in keyed if (k[..., 3][ring] > 127).any())
    m["edge_touch_frames"] = touch                      # warning only: the slice may clip the character
    # The cell's own geometry, judged BEFORE the (expensive) encode: a block here saves the encode.
    # A returned video sheet gets inside_slot + cross_slot; a cell of a prepared 3x3 video or a pre-sliced clip gets inside_frame (the still's inside_cell, per frame).
    if slot:
        m["subject_px_in_video"] = int(max(union[2] - union[0], union[3] - union[1]))     # metric only: no warning, no gate
    pre = verify.run("slot", {"slot_frames" if slot else "cell_frames": keyed, "metrics": m}, cfg)
    ms["bounds"] = _ms(t)
    blocks = [c for c in pre if not c.ok and c.severity == verify.BLOCK]
    if any(c.id not in waive for c in blocks):
        rep = Report(pre)
        return AnimationResult(idx, "FAILED", rep.first_failure, rep, m)
    if blocks:                       # every block was allowed by a human click (stored on the sticker): kept as a warning, still listed
        m["waived"] = [c.id for c in blocks]
        pre = [dataclasses.replace(c, severity=verify.WARN, note=(c.note + " (allowed by you)").strip()) if c in blocks else c for c in pre]
    scale = min(fit_scale(union, cfg), cfg.max_fit * cfg.size / max(union[2] - union[0], union[3] - union[1]))
    m["scale"] = round(scale, 4)
    t = time.perf_counter()
    out = np.stack([render_sticker(k, union, scale, cfg) for k in keyed])       # ONE transform per clip
    ms["render"] = _ms(t); t = time.perf_counter()
    # A seam is only visible if it is bigger than the clip's own normal frame-to-frame change.
    def motion(a):
        a = support(a)
        return float(np.median([loop_seam(a[i], a[i + 1]) for i in range(len(a) - 1)])) if len(a) > 1 else 0.0
    seam = lambda a: loop_seam(support(a)[-1], support(a)[0])
    limit = lambda mo: max(cfg.loop_seam_max, cfg.loop_seam_ratio * mo)
    mo = motion(out)
    m["motion"] = round(mo, 2)
    m["loop_seam_before"] = round(seam(out), 2)
    if m["loop_seam_before"] > limit(mo):
        out = close_loop(out, cfg.loop_fade_frames)
        mo = motion(out)             # the faded frames change the clip's own motion
    m["loop_seam"] = round(seam(out), 2)
    m["loop_limit"] = round(limit(mo), 2)
    m["frames_out"] = len(out)
    ms["seam"] = _ms(t)
    rep = Report()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "clip.webm"
        t = time.perf_counter()
        crf, data, n_enc = _encode_fit(out, fps, cfg, path)
        m["crf"] = crf
        ms["encode"] = _ms(t); ms["encodes"] = n_enc; t = time.perf_counter()
        dec = ff.decode_alpha(path, 4, (out.shape[2], out.shape[1]))
        if len(dec) == len(out[:4]):                                    # the edge detail that survived the encode (first frames, decoded with the alpha-aware decoder)
            e_in = float(np.mean([edge_energy(f) for f in out[:len(dec)]]))
            m["sharp_kept"] = round(float(np.mean([edge_energy(f) for f in dec])) / max(e_in, 1e-6), 2) if e_in > 0 else None
        if ref_alpha is not None and getattr(ref_alpha, "ndim", 0) == 3:                  # the approved still (RGBA): how soft is the animation next to it?
            dv = detail_vs_ref(out, ref_alpha)
            if dv is not None:
                m["detail_vs_still"] = round(dv, 2)
                m["soft_sigma"] = soft_sigma(ref_alpha, dv)
        inp = {"data": data, "info": ff.probe(path), "info_native": ff.probe(path, vp9_native=True), "alpha": dec, "metrics": m,
               "frames_out": out, "ref_alpha": ref_alpha}
        ms["probe"] = _ms(t); t = time.perf_counter()
        rep = Report(pre + verify.run("anim", inp, cfg))
        ms["verify"] = _ms(t)
    ms["finish"] = _ms(t_all)
    m["kb"] = round(len(data) / 1024, 1)
    if rep.ok:
        return AnimationResult(idx, "READY", None, rep, m, data)
    return AnimationResult(idx, "FAILED", rep.first_failure, rep, m)


def check_returned_video(mp4, layout: dict, sheet_rgb: np.ndarray, cfg, on_probe=None) -> list:
    """The video-stage checks on a returned video, before any slicing: decodes, specs, layout_match (first frame vs the
    video sheet), blank_slots_stay_empty (foreground in a slot that was blank on the sheet, any frame)."""
    from .grid import scale_rects
    info = ff.probe(mp4)
    if on_probe:
        on_probe(info)
    first = None
    if info["width"] and info["height"]:
        try:
            first = ff.decode_cell(mp4, 0, 0, info["width"] // 2 * 2, info["height"] // 2 * 2, 1, None)[0]
        except Exception:
            first = None
    inp = {"info": info, "first_frame": first, "layout": layout, "sheet": sheet_rgb, "metrics": {}}
    if first is not None:
        W, H = info["width"], info["height"]
        blank = [sl for sl in layout["slots"] if not sl["sticker"]]
        rects = scale_rects([tuple(sl["rect"]) for sl in layout["slots"]], tuple(layout["canvas"]), (W, H))
        fps = min(info["fps"] or cfg.video_max_fps, cfg.video_max_fps)
        share = {}
        for sl in blank:
            x, y, w, h = rects[sl["slot"] - 1]
            try:
                frames = ff.decode_cell(mp4, x, y, w, h, int(cfg.video_max_seconds * fps), cfg.video_max_fps if info["fps"] > cfg.video_max_fps else None)
                calib = calibrate(frames[0], cfg.chroma, cfg.border_px, cfg.threshold)
                share[sl["slot"]] = max(float((key_image(f, cfg, calib).rgba[..., 3] > 127).mean()) for f in frames)
            except Exception:
                share[sl["slot"]] = 0.0
        inp["blank_share"] = share
    return verify.run("video", inp, cfg)
