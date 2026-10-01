"""Sticker library: packs, imported/edited stickers, photo cutout, pack export (desktop builder).

Storage is plain files under <out>/library/: library.json + files/<name>. Writes are atomic and locked.
Naming follows the repo convention: <media>-<NNN>-<pack_slug>-<sticker_slug>.<ext> (NNN counts inside the pack)."""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import threading
import time
import uuid
import zipfile
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from . import matte
from . import pipeline as pl
from .engine import ffmpeg as ff
from .engine.chroma import calibrate, key_diff, key_image, remove_specks
from .engine.config import EngineConfig
from .engine.sheet import encode_static
from .prompter import slug

# Export limits live here, not in the UI (adjust when a target changes).
WA_STATIC_MAX = 100 * 1024
WA_TRAY_MAX = 50 * 1024
WA_ANIM_MAX = 500 * 1024
WA_PACK_MIN, WA_PACK_MAX = 3, 30
CUTOUT_MAX_SIDE = 1024
GREEN_RING_MIN = 40      # median key-channel excess on the border ring that means "this is a green/blue screen"


class LibraryError(Exception):
    def __init__(self, msg, code=400):
        super().__init__(msg)
        self.code = code


def decode_image(data: bytes) -> np.ndarray:
    """Any browser-common image (png/jpg/webp/gif first frame/bmp) -> RGBA uint8."""
    try:
        im = Image.open(io.BytesIO(data)); im.load()
    except Exception as e:
        raise LibraryError(f"not an image I can read: {e}")
    return np.array(im.convert("RGBA"))


def _bbox(alpha: np.ndarray, thr=127):
    ys, xs = np.where(alpha > thr)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else None


def _grabcut(rgb: np.ndarray) -> np.ndarray:
    """OpenCV GrabCut seeded with an inset rectangle. Offline, no weights; fine for simple backgrounds."""
    h, w = rgb.shape[:2]
    k = min(1.0, 640 / max(h, w))
    small = cv2.resize(rgb, (max(8, int(w * k)), max(8, int(h * k))), interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]
    mx, my = max(2, int(sw * 0.04)), max(2, int(sh * 0.04))
    mask = np.zeros((sh, sw), np.uint8)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(cv2.cvtColor(small, cv2.COLOR_RGB2BGR), mask, (mx, my, sw - 2 * mx, sh - 2 * my), bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    m = np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n > 1:                                   # keep the main subject plus anything at least 15% of it
        big = st[1:, cv2.CC_STAT_AREA].max()
        keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= 0.15 * big
        m = keep[lab].astype(np.uint8)
    soft = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2)
    return cv2.resize(soft, (w, h), interpolation=cv2.INTER_LINEAR)


def cutout(rgba: np.ndarray, cfg: EngineConfig | None = None, method: str = "auto"):
    """Photo/graphic -> transparent subject, cropped with a small pad. Returns (rgba, info).
    Already-transparent input is kept; green/blue screens use the engine's chroma key; anything else uses the learned matte
    (U2-Net via onnxruntime, see matte.py) when installed, else GrabCut. method: auto | matte | grabcut forces one of the last two."""
    cfg = cfg or EngineConfig()
    h, w = rgba.shape[:2]
    if max(h, w) > CUTOUT_MAX_SIDE:
        k = CUTOUT_MAX_SIDE / max(h, w)
        rgba = cv2.resize(rgba, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
        h, w = rgba.shape[:2]
    info = {"width": w, "height": h}
    if method not in ("auto", "matte", "grabcut"):
        raise LibraryError("method must be auto, matte or grabcut")
    if method == "auto" and (rgba[..., 3] < 250).mean() > 0.02:
        info["method"] = "existing_alpha"
        out = rgba.copy()
    else:
        rgb = np.ascontiguousarray(rgba[..., :3])
        ring = max(2, min(h, w) // 100)
        score = {}
        for ch in ("green", "blue"):
            m = np.zeros((h, w), bool); m[:ring] = m[-ring:] = True; m[:, :ring] = m[:, -ring:] = True
            score[ch] = float(np.median(key_diff(rgb, ch)[m]))
        ch = max(score, key=score.get)
        if method == "auto" and score[ch] >= GREEN_RING_MIN:
            c = replace(cfg, chroma=ch, border_px=ring)
            out = key_image(rgb, c, calibrate(rgb, ch, ring, None)).rgba
            info.update(method=f"chroma_{ch}", ring_excess=round(score[ch], 1))
        else:
            st = matte.status()
            if method == "matte" and not st["ok"]:
                raise LibraryError("AI matte is not available: " + st["reason"], 409)
            if method != "grabcut" and st["ok"]:
                a = remove_specks(matte.alpha(rgb), cfg.min_component_px)
                info["method"] = "matte_" + st["model"]
            else:
                a = remove_specks(_grabcut(rgb), cfg.min_component_px)
                info["method"] = "grabcut"
                if method == "auto":
                    info["hint"] = "GrabCut assumes the subject fills the frame; install the AI matte for photos (python -m mirsal doctor)"
            out = np.dstack([rgb, np.clip(a * 255 + .5, 0, 255).astype(np.uint8)])
    bb = _bbox(out[..., 3])
    frac = float((out[..., 3] > 127).mean())
    info["foreground"] = round(frac, 3)
    if not bb or frac < 0.01:
        raise LibraryError("no subject found (cutout came back empty); try a photo with a clearer subject")
    if frac > 0.92:
        info["warning"] = "almost everything was kept; use Erase to remove the background"
    pad = max(4, int(0.02 * max(h, w)))
    x0, y0, x1, y1 = max(0, bb[0] - pad), max(0, bb[1] - pad), min(w, bb[2] + pad), min(h, bb[3] + pad)
    return np.ascontiguousarray(out[y0:y1, x0:x1]), info


def png_bytes(rgba: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    return buf.tobytes()


def validate_render(data: bytes, cfg: EngineConfig):
    """The editor's exported 512x512 canvas -> (bytes, ext, checks). Same rules as engine stickers."""
    rgba = decode_image(data)
    S = cfg.size
    checks = [("dimensions", rgba.shape[:2] == (S, S), f"{rgba.shape[1]}x{rgba.shape[0]}")]
    if not checks[0][1]:
        raise LibraryError(f"canvas must be {S}x{S}, got {rgba.shape[1]}x{rgba.shape[0]}")
    fg = int((rgba[..., 3] > 127).sum())
    checks.append(("foreground", fg >= cfg.min_foreground_px, f"{fg}px"))
    if fg < cfg.min_foreground_px:
        raise LibraryError("sticker is empty")
    body, ext = encode_static(rgba, cfg)
    checks.append(("size", len(body) <= cfg.static_max_bytes, f"{len(body) // 1024}KB {ext}"))
    if len(body) > cfg.static_max_bytes:
        raise LibraryError(f"{len(body) // 1024}KB is over the {cfg.static_max_bytes // 1024}KB limit; simplify the sticker")
    return body, ext, checks


def anim_frames(path: Path, start: float, end: float, fps: float, cfg: EngineConfig):
    """Decode a sticker WEBM and pick frames for [start, end) resampled to `fps` (nearest source frame)."""
    info = ff.probe(path, vp9_native=True)
    src_fps, dur = info["fps"] or 30.0, info["duration"]
    if not info["width"] or dur <= 0:
        raise LibraryError("cannot read that animation (is ffmpeg with libvpx-vp9 installed? run: python -m mirsal doctor)", 409)
    start, end = max(0.0, float(start)), min(dur, float(end))
    fps = max(1.0, min(float(fps), cfg.video_max_fps))
    if end - start < 0.1:
        raise LibraryError("trim range is too short")
    end = min(end, start + cfg.video_max_seconds)
    try:
        allf = ff.decode_full(path, info["width"], info["height"], int(dur * src_fps) + 3, None)
    except RuntimeError as e:
        raise LibraryError(str(e), 409)
    idx = [min(len(allf) - 1, int((start + k / fps) * src_fps + 1e-6)) for k in range(max(1, int(round((end - start) * fps))))]
    return allf[idx], fps, {"src_fps": round(src_fps, 2), "frames": len(idx), "start": round(start, 3), "end": round(end, 3)}


def anim_export(path: Path, start, end, fps, fmt: str, loop: bool, cfg: EngineConfig):
    """-> (bytes, mime, ext, info). webm = Telegram (VP9+alpha, <=256KB ladder); webp = WhatsApp (<=500KB); gif = anywhere (no soft alpha)."""
    frames, fps, info = anim_frames(path, start, end, fps, cfg)
    return encode_frames(frames, fps, fmt, loop, cfg, info)


def encode_frames(frames, fps: float, fmt: str, loop: bool, cfg: EngineConfig, info: dict | None = None, gif_colors: int = 256):
    """RGBA frames -> (bytes, mime, ext, info) with the platform size ladders. Shared by sticker trimming and video projects."""
    info = dict(info or {})
    info.update(format=fmt, fps=fps)
    try:
        if fmt == "webm":
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                out = Path(td) / "o.webm"
                for crf in cfg.crf_ladder:
                    ff.encode_webm(frames, fps, crf, out)
                    data = out.read_bytes(); info["crf"] = crf
                    if len(data) <= cfg.video_max_bytes:
                        break
                if len(data) > cfg.video_max_bytes:
                    raise LibraryError(f"{len(data) // 1024}KB is over the {cfg.video_max_bytes // 1024}KB limit even at the lowest quality; trim it or lower the frame rate")
            mime = "video/webm"
        elif fmt == "webp":
            for q in (75, 60, 45, 30, 20):
                data = ff.encode_anim(frames, fps, "webp", q, loop); info["quality"] = q
                if len(data) <= WA_ANIM_MAX:
                    break
            if len(data) > WA_ANIM_MAX:
                raise LibraryError(f"{len(data) // 1024}KB is over WhatsApp's {WA_ANIM_MAX // 1024}KB animated limit; trim it or lower the frame rate")
            mime = "image/webp"
        elif fmt == "gif":
            data, mime = ff.encode_anim(frames, fps, "gif", 0, loop, gif_colors), "image/gif"
        else:
            raise LibraryError("format must be webm, webp or gif")
    except RuntimeError as e:
        raise LibraryError(str(e), 409)
    info["kb"] = max(1, len(data) // 1024)
    return data, mime, fmt, info


class Library:
    def __init__(self, out: Path):
        self.root = Path(out) / "library"
        self.files = self.root / "files"
        self.db_path = self.root / "library.json"
        self.lock = threading.RLock()
        self.files.mkdir(parents=True, exist_ok=True)

    # ---- persistence
    def _load(self) -> dict:
        if not self.db_path.exists():
            return {"packs": []}
        try:
            return json.loads(self.db_path.read_text(encoding="utf-8"))
        except ValueError:
            shutil.copy(self.db_path, self.db_path.with_suffix(".corrupt.json"))
            return {"packs": []}

    def _save(self, db: dict) -> None:
        tmp = self.db_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self.db_path)

    def _pack(self, db, pid):
        p = next((p for p in db["packs"] if p["id"] == pid), None)
        if not p:
            raise LibraryError("no such pack", 404)
        return p

    # ---- reads
    def snapshot(self, recent: int = 30) -> dict:
        with self.lock:
            db = self._load()
        allst = [dict(s, pack_id=p["id"], pack=p["name"]) for p in db["packs"] for s in p["stickers"]]
        allst.sort(key=lambda s: s["created"], reverse=True)
        return {"packs": db["packs"], "recent": allst[:recent], "total": len(allst)}

    # ---- packs
    def create_pack(self, name: str) -> dict:
        name = (name or "").strip() or "My Pack"
        with self.lock:
            db = self._load()
            p = {"id": uuid.uuid4().hex[:8], "name": name[:60], "slug": slug(name) or "pack", "cover": None, "next": 1,
                 "created": time.time(), "stickers": []}
            db["packs"].append(p)
            self._save(db)
            return p

    def update_pack(self, pid: str, name=None, cover=None, order=None) -> dict:
        with self.lock:
            db = self._load(); p = self._pack(db, pid)
            if name is not None and name.strip():
                p["name"] = name.strip()[:60]
            if cover is not None:
                if cover and not any(s["id"] == cover for s in p["stickers"]):
                    raise LibraryError("cover must be a sticker of this pack")
                p["cover"] = cover or None
            if order is not None:
                by = {s["id"]: s for s in p["stickers"]}
                if sorted(order) != sorted(by):
                    raise LibraryError("order must list every sticker of the pack exactly once")
                p["stickers"] = [by[i] for i in order]
            self._save(db)
            return p

    def delete_pack(self, pid: str) -> None:
        with self.lock:
            db = self._load(); p = self._pack(db, pid)
            for s in p["stickers"]:
                self._unlink(db, s["file"], skip=pid)
            db["packs"].remove(p)
            self._save(db)

    def _unlink(self, db, fname, skip=None):
        if not any(s["file"] == fname for q in db["packs"] if q["id"] != skip for s in q["stickers"]):
            (self.files / fname).unlink(missing_ok=True)

    # ---- stickers
    def add_bytes(self, pid: str, data: bytes, ext: str, name: str, kind: str = "static", emoji: str = "🙂",
                  source: dict | None = None, w: int = 512, h: int = 512) -> dict:
        with self.lock:
            db = self._load(); p = self._pack(db, pid)
            n = p["next"]; p["next"] = n + 1
            media = "vid" if kind == "animated" else "img"
            base = slug(name) or "sticker"
            fname = f"{media}-{n:03d}-{p['slug']}-{base}.{ext}"
            (self.files / fname).write_bytes(data)
            s = {"id": uuid.uuid4().hex[:8], "name": (name or base)[:60], "file": fname, "type": kind, "emoji": emoji or "🙂",
                 "kb": max(1, len(data) // 1024), "w": w, "h": h, "source": source or {}, "created": time.time()}
            p["stickers"].append(s)
            if not p["cover"]:
                p["cover"] = s["id"]
            self._save(db)
            return s

    def add_render(self, pid: str, png: bytes, name: str, emoji: str, cfg: EngineConfig, source=None) -> dict:
        body, ext, checks = validate_render(png, cfg)
        s = self.add_bytes(pid, body, ext, name, "static", emoji, source)
        s["checks"] = checks
        return s

    def add_from_generation(self, out: Path, pid: str, gid: int, index: int, kind: str = "static") -> dict:
        st = pl.state(out, gid)
        t = st["stickers"][index - 1]
        rel = t.get("webm") if kind == "animated" else t.get("png")
        if not rel or (kind == "animated" and t.get("anim_status") != "READY") or (kind != "animated" and t.get("status") != "READY"):
            raise LibraryError("that sticker is not READY" + (" (animate it first)" if kind == "animated" else ""), 409)
        f = Path(out) / st["generation_id"] / rel
        if not f.is_file():
            raise LibraryError("sticker file is missing", 404)
        return self.add_bytes(pid, f.read_bytes(), f.suffix.lstrip("."), t.get("name") or f.stem, kind, t.get("emoji") or "🙂",
                              {"generation": st["generation_id"], "index": index})

    def delete_sticker(self, pid: str, sid: str) -> None:
        with self.lock:
            db = self._load(); p = self._pack(db, pid)
            s = next((s for s in p["stickers"] if s["id"] == sid), None)
            if not s:
                raise LibraryError("no such sticker", 404)
            p["stickers"].remove(s)
            if p["cover"] == sid:
                p["cover"] = p["stickers"][0]["id"] if p["stickers"] else None
            self._unlink(db, s["file"])
            self._save(db)

    def move_sticker(self, pid: str, sid: str, to: str) -> dict:
        """Move a sticker to another pack (file is renamed to the target pack's naming convention)."""
        with self.lock:
            db = self._load(); src = self._pack(db, pid); dst = self._pack(db, to)
            if src is dst:
                raise LibraryError("sticker is already in that pack")
            s = next((s for s in src["stickers"] if s["id"] == sid), None)
            if not s:
                raise LibraryError("no such sticker", 404)
            n = dst["next"]; dst["next"] = n + 1
            ext = s["file"].rsplit(".", 1)[-1]
            media = "vid" if s["type"] == "animated" else "img"
            fname = f"{media}-{n:03d}-{dst['slug']}-{slug(s['name']) or 'sticker'}.{ext}"
            (self.files / s["file"]).replace(self.files / fname)
            s["file"] = fname
            src["stickers"].remove(s)
            if src["cover"] == sid:
                src["cover"] = src["stickers"][0]["id"] if src["stickers"] else None
            dst["stickers"].append(s)
            if not dst["cover"]:
                dst["cover"] = sid
            self._save(db)
            return s

    def rename_sticker(self, pid: str, sid: str, name=None, emoji=None) -> dict:
        with self.lock:
            db = self._load(); p = self._pack(db, pid)
            s = next((s for s in p["stickers"] if s["id"] == sid), None)
            if not s:
                raise LibraryError("no such sticker", 404)
            if name and name.strip():
                s["name"] = name.strip()[:60]
            if emoji:
                s["emoji"] = emoji
            self._save(db)
            return s

    def sticker_path(self, pid: str, sid: str) -> tuple[Path, dict]:
        with self.lock:
            db = self._load(); p = self._pack(db, pid)
        s = next((s for s in p["stickers"] if s["id"] == sid), None)
        if not s:
            raise LibraryError("no such sticker", 404)
        return self.files / s["file"], s

    def animate(self, pid: str, sid: str, start, end, fps, fmt: str, loop: bool, cfg: EngineConfig, save: bool = False, name: str = ""):
        path, s = self.sticker_path(pid, sid)
        if s["type"] != "animated":
            raise LibraryError("only animated stickers can be edited on the timeline")
        data, mime, ext, info = anim_export(path, start, end, fps, fmt, loop, cfg)
        if not save:
            return data, mime, ext, info
        if fmt != "webm":
            raise LibraryError("only WEBM can be saved back to the pack (webp/gif are downloads)")
        new = self.add_bytes(pid, data, "webm", name.strip() or s["name"] + " trimmed", "animated", s["emoji"],
                             {"from": s["id"], "trim": [info["start"], info["end"]], "fps": info["fps"]})
        new["info"] = info
        return new

    # ---- export
    def export_wastickers(self, pid: str, author: str = "Mirsal", cfg: EngineConfig | None = None) -> tuple[bytes, dict]:
        """<pack>.wastickers = zip of title.txt, author.txt, tray.png (96x96), static 512x512 WebP <=100KB and animated WebP <=500KB.
        The format sticker-import apps read. Animated stickers that cannot be converted (no ffmpeg/libwebp) are skipped and reported."""
        cfg = cfg or EngineConfig()
        with self.lock:
            db = self._load(); p = self._pack(db, pid)
        items = p["stickers"][:WA_PACK_MAX]
        if len(p["stickers"]) < WA_PACK_MIN:
            raise LibraryError(f"a WhatsApp pack needs at least {WA_PACK_MIN} stickers (this pack has {len(p['stickers'])})", 409)
        bio, report = io.BytesIO(), {"stickers": 0, "skipped_animated": [], "files": []}
        with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("title.txt", p["name"]); z.writestr("author.txt", author)
            cover = next((s for s in items if s["id"] == p["cover"]), items[0])
            if cover["type"] != "static":
                cover = next((s for s in items if s["type"] == "static"), cover)
            if cover["type"] == "static":
                tray = Image.open(self.files / cover["file"]).convert("RGBA")
            else:
                f0 = ff.decode_full(self.files / cover["file"], 512, 512, 1, None)[0]
                tray = Image.fromarray(f0, "RGBA")
            tray = tray.resize((96, 96), Image.LANCZOS)
            tb = io.BytesIO(); tray.save(tb, "PNG", optimize=True)
            if tb.tell() > WA_TRAY_MAX:
                raise LibraryError("tray icon is over 50KB")
            z.writestr("tray.png", tb.getvalue())
            for i, s in enumerate(items, 1):
                stem = f"{i:02d}-{Path(s['file']).stem}"
                if s["type"] == "animated":
                    try:
                        data, _, _, info = anim_export(self.files / s["file"], 0, cfg.video_max_seconds, 15, "webp", True, cfg)
                    except LibraryError as e:
                        report["skipped_animated"].append(f"{s['name']} ({e})"); continue
                    z.writestr(stem + ".webp", data)
                    report["files"].append({"name": s["name"], "kb": info["kb"], "quality": info.get("quality"), "animated": True})
                    report["stickers"] += 1
                    continue
                im = Image.open(self.files / s["file"]).convert("RGBA")
                for q in (90, 80, 70, 60, 50, 40, 30):
                    b = io.BytesIO(); im.save(b, "WEBP", quality=q, method=4, exact=True)
                    if b.tell() <= WA_STATIC_MAX:
                        break
                if b.tell() > WA_STATIC_MAX:
                    raise LibraryError(f"'{s['name']}' cannot be compressed under 100KB")
                z.writestr(stem + ".webp", b.getvalue())
                report["files"].append({"name": s["name"], "kb": b.tell() // 1024, "quality": q})
                report["stickers"] += 1
        return bio.getvalue(), report
