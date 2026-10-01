"""Part B: prepared grid MP4 (3x3 / 2x2 / 1x1) -> transparent looping WEBM per cell. Same keyer as stills, same settings."""
from __future__ import annotations

import math
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import ffmpeg as ff
from .chroma import calibrate, despill, key_image, remove_specks
from .render import Report, bbox_of, fit_scale, render_sticker


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
    a1, a2 = last[..., 3].astype(np.float32), first[..., 3].astype(np.float32)
    w = np.maximum(a1, a2) / 255.0
    d = np.abs(last[..., :3].astype(np.float32) - first[..., :3].astype(np.float32)).mean(-1)
    return float((w * d + np.abs(a1 - a2)).sum() / max(float(w.sum()), 1.0))


def close_loop(frames: np.ndarray, m: int) -> np.ndarray:
    """Blend the tail into the head and drop the tail, so the last frame flows into the first."""
    n = len(frames)
    if m < 1 or n < 2 * m + 2:
        return frames
    out = frames[: n - m].astype(np.float32).copy()
    for k in range(m):
        w = k / m               # first frame = pure tail (continues the last frame), then fade to the head
        out[k] = (1 - w) * frames[n - m + k].astype(np.float32) + w * frames[k].astype(np.float32)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def vp9_missing(cells) -> list[AnimationResult] | None:
    """Fail fast with a named reason instead of one 'exception' per cell when ffmpeg cannot encode VP9+alpha."""
    if ff.has_vp9():
        return None
    return [AnimationResult(i, "FAILED", "no_vp9_encoder",
                            metrics={"error": f"{ff.ffmpeg_exe()} has no libvpx-vp9: pip install imageio-ffmpeg (see doctor)"})
            for i in cells]


def process_video(mp4, cfg, cells: list[int] | None = None, on_probe=None, on_cell=None,
                  rects: list | None = None, sheet_wh: tuple | None = None) -> list[AnimationResult]:
    """rects/sheet_wh: the still's measured cell rects on the sheet; mapped onto the video (same layout, any size).
    Without them: equal thirds."""
    from .grid import scale_rects
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
    results = []
    for idx in cells:
        try:
            res = _one_cell(mp4, idx, vr[idx - 1], fps, cap_fps, max_frames, cfg)
        except Exception as e:  # an animation failure never raises past here
            res = AnimationResult(idx, "FAILED", "exception", metrics={"error": str(e)[:300]})
        results.append(res)
        if on_cell:
            on_cell(res)
    return results


def _one_cell(mp4, idx, rect, fps, cap_fps, max_frames, cfg) -> AnimationResult:
    x, y, cw, ch = rect
    frames = ff.decode_cell(mp4, x, y, cw, ch, max_frames, cap_fps)   # one cell at a time
    calib = calibrate(frames[0], cfg.chroma, cfg.border_px, cfg.threshold)      # sample bg ONCE
    keyed = [key_image(f, cfg, calib).rgba for f in frames]
    return _finish(idx, keyed, fps, cfg, {"source": "3x3 mp4", "threshold": round(calib[1], 1)})


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


def process_clips(clips: dict, cfg, on_cell=None) -> list[AnimationResult]:
    """clips = {cell: {"mov": path, "webm": path}} of pre-sliced transparent clips."""
    failed = vp9_missing(list(clips))
    if failed:
        for r in failed:
            on_cell and on_cell(r)
        return failed
    results = []
    for idx, formats in clips.items():
        try:
            fmt, path = pick_clip(formats, cfg)
            info = ff.probe(path)
            w, h = info["width"], info["height"]
            fps = info["fps"] or 24.0
            cap_fps = cfg.video_max_fps if fps > cfg.video_max_fps else None
            fps = cfg.video_max_fps if cap_fps else fps
            frames = ff.decode_full(path, w, h, int(math.floor(cfg.video_max_seconds * fps)), cap_fps)
            keyed = [_clean_clip(f, cfg) for f in frames]
            res = _finish(idx, keyed, fps, cfg, {"source": f"clip:{fmt}", "clip": path.name, "clip_size": f"{w}x{h}"})
        except Exception as e:
            res = AnimationResult(idx, "FAILED", "exception", metrics={"error": str(e)[:300]})
        results.append(res)
        if on_cell:
            on_cell(res)
    return results


def _finish(idx, keyed, fps, cfg, m) -> AnimationResult:
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
    scale = min(fit_scale(union, cfg), cfg.max_fit * cfg.size / max(union[2] - union[0], union[3] - union[1]))
    m["scale"] = round(scale, 4)
    out = np.stack([render_sticker(k, union, scale, cfg) for k in keyed])       # ONE transform per clip
    # A seam is only visible if it is bigger than the clip's own normal frame-to-frame change.
    motion = lambda a: float(np.median([loop_seam(a[i], a[i + 1]) for i in range(len(a) - 1)])) if len(a) > 1 else 0.0
    limit = lambda a: max(cfg.loop_seam_max, cfg.loop_seam_ratio * motion(a))
    m["loop_seam_before"] = round(loop_seam(out[-1], out[0]), 2)
    if m["loop_seam_before"] > limit(out):
        out = close_loop(out, cfg.loop_fade_frames)
    m["loop_seam"] = round(loop_seam(out[-1], out[0]), 2)
    m["loop_limit"] = round(limit(out), 2)
    m["frames_out"] = len(out)
    rep = Report()
    with tempfile.TemporaryDirectory() as td:
        path, data = Path(td) / "clip.webm", None
        for crf in cfg.crf_ladder:
            ff.encode_webm(out, fps, crf, path)
            data = path.read_bytes()
            m["crf"] = crf
            if len(data) <= cfg.video_max_bytes:
                break
        rep.add("size_budget", len(data) <= cfg.video_max_bytes, f"{len(data) // 1024}KB @crf{m['crf']}")
        info = ff.probe(path)
        rep.add("codec_vp9", info["codec"] == "vp9", info["codec"])
        rep.add("dimensions", (info["width"], info["height"]) == (cfg.size, cfg.size), f"{info['width']}x{info['height']}")
        rep.add("fps", 0 < info["fps"] <= cfg.video_max_fps + 0.01, info["fps"])
        rep.add("duration", info["duration"] <= cfg.video_max_seconds + 0.02, round(info["duration"], 3))
        rep.add("no_audio", not info["audio"])
        rep.add("alpha_mode_tag", ff.probe(path, vp9_native=True)["alpha_mode"] or info["alpha_mode"])
        al = ff.decode_alpha(path)
        rep.add("alpha_decoded", len(al) > 0 and al[..., 3].min() < 8 and al[..., 3].max() > 247)
        rep.add("loop_seam", m["loop_seam"] <= m["loop_limit"], f"{m['loop_seam']} <= {m['loop_limit']}")
    m["kb"] = round(len(data) / 1024, 1)
    if rep.ok:
        return AnimationResult(idx, "READY", None, rep, m, data)
    return AnimationResult(idx, "FAILED", rep.first_failure, rep, m)
