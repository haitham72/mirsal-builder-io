"""Grey stand-ins for every exported animation (Haitham, 2026-10-12): beside each video in a Download .zip, its sticker's STILL (the image
sheet's cell, the same S#) as a flat grey silhouette — one colour, 75% white and 25% black (#BFBFBF), the still's own alpha kept as the shape —
named `{emoji full name}_grey.png` (`grinning_face_grey.png`) in the zip's `grey/` folder, compressed hard: a palette PNG with 4 alpha levels
(transparent, two edge steps, solid), about 2-3 KB a sticker. They are listed in `manifest.json` under `grey`, never under `assets`, so Export to
collection still sends only the stickers. Pillow + numpy only."""
from __future__ import annotations

import io
import re
import unicodedata
from pathlib import Path

import numpy as np

GREY = 191                 # 75% white + 25% black: round(0.75 * 255)
ALPHA_LEVELS = 4           # transparent, 1/3, 2/3, solid: soft edges at a fraction of the bytes of a full alpha

_SKIN = {0x1F3FB: "light skin tone", 0x1F3FC: "medium light skin tone", 0x1F3FD: "medium skin tone",
         0x1F3FE: "medium dark skin tone", 0x1F3FF: "dark skin tone"}
_JOINERS = {0xFE0E, 0xFE0F, 0x200D, 0x20E3}


def emoji_name(emoji: str | None) -> str:
    """The emoji's full Unicode name in snake case: 😀 -> grinning_face, 👍🏽 -> thumbs_up_sign_medium_skin_tone, 🇦🇪 -> flag_ae, 1️⃣ -> digit_one_keycap.
    A code point newer than this Python's Unicode table is written as u1fae8. Empty -> sticker."""
    e = str(emoji or "")
    cps = [ord(c) for c in e if ord(c) not in _JOINERS]
    if cps and all(0x1F1E6 <= c <= 0x1F1FF for c in cps):
        return "flag_" + "".join(chr(c - 0x1F1E6 + 97) for c in cps)
    parts = []
    for c in cps:
        if c in _SKIN:
            parts.append(_SKIN[c])
            continue
        try:
            parts.append(unicodedata.name(chr(c)))
        except ValueError:
            parts.append(f"u{c:04x}")
    if "⃣" in e:
        parts.append("keycap")
    return re.sub(r"[^a-z0-9]+", "_", " ".join(parts).lower()).strip("_") or "sticker"


def grey_png(alpha: np.ndarray) -> bytes:
    """A flat #BFBFBF silhouette of `alpha` (HxW uint8) as a palette PNG with ALPHA_LEVELS transparency steps."""
    from PIL import Image
    step = 255 // (ALPHA_LEVELS - 1)
    q = np.round(alpha.astype(np.float32) / step).astype(np.uint8)          # 0 .. ALPHA_LEVELS-1, used directly as the palette index
    img = Image.fromarray(q, "P")
    img.putpalette([GREY, GREY, GREY] * ALPHA_LEVELS)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True, transparency=bytes(min(255, i * step) for i in range(ALPHA_LEVELS)))
    return buf.getvalue()


def alpha_of(still: Path | None, video: Path | None) -> np.ndarray | None:
    """The shape to grey: the sticker's still when it is on disk, else the video's first frame. None when neither can be read."""
    from PIL import Image
    if still is not None and Path(still).is_file():
        try:
            return np.array(Image.open(still).convert("RGBA"))[..., 3]
        except Exception:
            pass
    if video is not None and Path(video).is_file():
        try:
            from ..engine import ffmpeg as ff
            info = ff.probe(video, vp9_native=True)
            frames = ff.decode_full(video, info["width"], info["height"], 1, None)
            return frames[0][..., 3]
        except Exception:
            pass
    return None


class Writer:
    """Adds the grey PNGs to an open zip, one per animation, never two under one name (a repeated emoji gets _2, _3 before `_grey`)."""

    def __init__(self, z):
        self.z, self.used, self.rows = z, set(), []

    def add(self, emoji: str | None, still: Path | None, video: Path | None, sticker_id: str) -> None:
        a = alpha_of(still, video)
        if a is None:
            return
        base, n = emoji_name(emoji), 1
        name = f"grey/{base}_grey.png"
        while name in self.used:
            n += 1
            name = f"grey/{base}_{n}_grey.png"
        self.used.add(name)
        data = grey_png(a)
        self.z.writestr(name, data)
        self.rows.append({"sticker_id": sticker_id, "emoji": emoji, "filename": name, "kb": round(len(data) / 1024, 1)})
