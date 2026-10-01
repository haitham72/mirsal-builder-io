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

# Animated WebP download limit (the editor's WebP/GIF downloads; Telegram needs none of it).
WA_ANIM_MAX = 500 * 1024
CUTOUT_MAX_SIDE = 1024
GREEN_RING_MIN = 40      # median key-channel excess on the border ring that means "this is a green/blue screen"



def readable_name(key: str) -> str:
    """'generic_emojis_laughing' -> 'Generic emojis laughing' ({subject} {action}), what the user sees; the file name stays in `file_name`."""
    t = " ".join(str(key).replace("-", " ").replace("_", " ").split())
    return (t[:1].upper() + t[1:])[:60] or "Sticker"


_GEN_NAME = re.compile(r"^(?:img|vid)-\d{3,}-[a-z0-9_]+-(?P<key>.+)$")


def _legacy_names(db: dict) -> dict:
    """Stickers added before the readable name existed carry the file-style name; move it to `file_name` and show the readable one."""
    for p in db.get("packs", []):
        for s in p.get("stickers", []):
            if "file_name" not in s and (s.get("source") or {}).get("generation"):
                m = _GEN_NAME.match(s.get("name", ""))
                if m:
                    s["file_name"] = s["name"]
                    s["name"] = readable_name(m["key"])
    return db


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
                from .engine.video import _encode_fit            # the same fit the animations get: the best crf that is under the budget
                info["crf"], data, _ = _encode_fit(frames, fps, cfg, out)
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
            return _legacy_names(json.loads(self.db_path.read_text(encoding="utf-8")))
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

    def add_from_generation(self, out: Path, pid: str, gid: int, index: int, kind: str = "static", name: str | None = None, emoji: str | None = None) -> dict:
        st = pl.state(out, gid)
        t = st["stickers"][index - 1]
        rel = t.get("webm") if kind == "animated" else t.get("png")
        if not rel or (kind == "animated" and t.get("anim_status") != "READY") or (kind != "animated" and t.get("status") != "READY"):
            raise LibraryError("that sticker is not READY" + (" (animate it first)" if kind == "animated" else ""), 409)
        f = Path(out) / st["generation_id"] / rel
        if not f.is_file():
            raise LibraryError("sticker file is missing", 404)
        s = self.add_bytes(pid, f.read_bytes(), f.suffix.lstrip("."), (name or "").strip()[:60] or readable_name(t.get("key") or f.stem), kind, (emoji or "").strip()[:20] or t.get("emoji") or "🙂",
                           {"generation": st["generation_id"], "index": index})
        return self.set_file_name(pid, s["id"], t.get("name") or f.stem)

    def replace_file(self, pid: str, sid: str, data: bytes, ext: str) -> dict:
        """New content for an existing sticker (same id, name, emoji, position, cover). A different extension renames the file (png -> webp)."""
        with self.lock:
            db = self._load(); p = self._pack(db, pid)
            s = next((s for s in p["stickers"] if s["id"] == sid), None)
            if not s:
                raise LibraryError("no such sticker", 404)
            fname = f"{Path(s['file']).stem}.{ext}"
            (self.files / fname).write_bytes(data)
            if fname != s["file"]:
                self._unlink(db, s["file"]); s["file"] = fname
            s["kb"] = max(1, len(data) // 1024); s["edited"] = time.time()
            self._save(db)
            return s

    def refresh_from_generation(self, out: Path, gen_id: str, index: int, png: Path | None, webm: Path | None) -> int:
        """A sticker edited in the Studio is the single source: every pack copy of that generation sticker takes the new file (static copies the image,
        animated copies the animation). Names, emoji and order stay."""
        with self.lock:
            targets = [(p["id"], s["id"], s["type"]) for p in self._load()["packs"] for s in p["stickers"]
                       if (s.get("source") or {}).get("generation") == gen_id and (s.get("source") or {}).get("index") == index]
        n = 0
        for pid, sid, kind in targets:
            f = webm if kind == "animated" else png
            if f and f.is_file():
                self.replace_file(pid, sid, f.read_bytes(), f.suffix.lstrip(".")); n += 1
        return n

    def set_file_name(self, pid: str, sid: str, file_name: str) -> dict:
        """The generator's file name (img-027-generic_emojis-generic_emojis_laughing) is kept as metadata, apart from the readable name."""
        with self.lock:
            db = self._load(); s = next(s for s in self._pack(db, pid)["stickers"] if s["id"] == sid)
            s["file_name"] = file_name
            self._save(db)
            return s

    def static_twins(self, pid: str, gen_id: str, indices: list[int]) -> list[dict]:
        """The still stickers of this pack that came from the same sticker (generation + index) as the animated ones about to be added."""
        with self.lock:
            p = self._pack(self._load(), pid)
        return [s for s in p["stickers"] if s["type"] == "static" and (s.get("source") or {}).get("generation") == gen_id and (s.get("source") or {}).get("index") in indices]

    def replace_static_with_animated(self, pid: str, gen_id: str, indices: list[int]) -> int:
        """Each animated sticker takes the place (position, cover) of its still twin and the still is deleted."""
        with self.lock:
            db = self._load(); p = self._pack(db, pid); n = 0
            for i in indices:
                src = lambda s: (s.get("source") or {}).get("generation") == gen_id and (s.get("source") or {}).get("index") == i
                old = next((s for s in p["stickers"] if s["type"] == "static" and src(s)), None)
                new = next((s for s in reversed(p["stickers"]) if s["type"] == "animated" and src(s)), None)
                if not old or not new:
                    continue
                at = p["stickers"].index(old)
                p["stickers"].remove(new); p["stickers"].remove(old)
                p["stickers"].insert(at, new)
                if p["cover"] == old["id"]:
                    p["cover"] = new["id"]
                self._unlink(db, old["file"]); n += 1
            self._save(db)
            return n

    def add_final(self, out: Path, pid: str, gid: int) -> dict:
        """G5 -> Library: add every sticker of the approved final pack (approved at G2 AND G4) as an animated sticker."""
        st = pl.state(out, gid)
        pack = st["reviews"].get("pack")
        if not pack or pack["decision"] != "APPROVE":
            raise LibraryError("The pack is not final yet (G5): approve it first.", 409)
        added = [self.add_from_generation(out, pid, gid, i, "animated") for i in pack["stickers"]]
        return {"added": len(added), "stickers": [a.get("id") for a in added] if isinstance(added[0], dict) else []}

    def set_telegram(self, pid: str, kind: str, block: dict) -> None:
        """Remember the Telegram set made from this pack (one per kind), so sending again only adds what is new."""
        with self.lock:
            db = self._load(); p = self._pack(db, pid)
            sets = [t for t in p.setdefault("telegram", {}).setdefault("sets", []) if t["kind"] != kind]
            p["telegram"]["sets"] = sets + [block]
            self._save(db)

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

    def delete_stickers(self, items: list[dict]) -> int:
        """Bulk delete: items = [{pack_id, id}, ...]. One save; a cover that goes is replaced by the pack's first sticker."""
        n = 0
        with self.lock:
            db = self._load()
            for it in items:
                p = next((p for p in db["packs"] if p["id"] == it.get("pack_id")), None)
                s = next((s for s in (p or {}).get("stickers", []) if s["id"] == it.get("id")), None)
                if not s:
                    continue
                p["stickers"].remove(s)
                if p["cover"] == s["id"]:
                    p["cover"] = p["stickers"][0]["id"] if p["stickers"] else None
                self._unlink(db, s["file"]); n += 1
            self._save(db)
        return n

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
