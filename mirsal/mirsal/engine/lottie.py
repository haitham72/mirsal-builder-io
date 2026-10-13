"""A particle burst as a playable Lottie JSON (web only; Telegram stays WebM): engine/particles.py's deterministic trajectories mapped onto image layers
over the real sprite PNGs. Pure (numpy + Pillow + stdlib JSON); no new dependency.
"""
from __future__ import annotations

import base64
import io
import math

import numpy as np
from PIL import Image

from .particles import ParticleParams, hue_rotate, png_bytes, trajectories, trim_sprite

HUE_STEP = 10.0         # Lottie cannot turn an image's hue: each particle's hue is rounded to this step and every step used is one embedded asset


def export_lottie(p: ParticleParams, emoji_png, *, size: int = 512) -> dict:
    """A playable Lottie JSON of one burst (web use only; Telegram stays WebM): the deterministic `trajectories()` mapped onto
    image layers (`ty: 2`) that show the real sprite, so any standard player (lottie-web, the LottieFiles preview) plays the
    picture flying, never a placeholder shape.

    `emoji_png` is the sprite as PNG bytes (RGBA), or a list of PNG bytes, one per sprite index. Each sprite is embedded ONCE as a
    base64 data URI asset (`e: 1`) and every particle that shows it references it. With `hue_var` > 0 the particle's hue is
    rounded to HUE_STEP degrees and each distinct (sprite, hue) is one more asset, tinted by hue_rotate(); with `hue_var` 0
    one sprite is exactly one asset. A layer lives only from its particle's birth to its death (`ip`/`op`), with one hold
    keyframe per frame for position, scale, rotation and opacity. Same params + same PNG bytes -> the same JSON. Pure."""
    pngs = [emoji_png] if isinstance(emoji_png, (bytes, bytearray)) else list(emoji_png or [])
    if not pngs:
        raise ValueError("no sprite given")
    sprites = []
    for data in pngs:
        try:
            img = np.asarray(Image.open(io.BytesIO(bytes(data))).convert("RGBA"), np.uint8)
        except Exception:
            raise ValueError("a sprite must be PNG bytes") from None
        tight = trim_sprite(img, pad=1)
        if tight is None:
            raise ValueError("a sprite is fully transparent")
        sprites.append(tight)
    p = p.clamped()
    W = H = int(size)
    cap = max(8, math.ceil(min(p.size_max * p.particle_size, 0.9) * W * 1.2))      # the biggest it is drawn: no point embedding more pixels
    for k, img in enumerate(sprites):
        h, w = img.shape[:2]
        if max(h, w) > cap:
            r = cap / max(h, w)
            sprites[k] = np.asarray(Image.fromarray(img, "RGBA").resize((max(1, round(w * r)), max(1, round(h * r))), Image.LANCZOS), np.uint8)
    tr = trajectories(p, len(sprites))
    F, fps = tr.frames, float(p.fps)
    assets, ids = [], {}

    def asset(k: int, hue: float) -> tuple[str, int]:
        key = (k, hue)
        if key not in ids:
            img = sprites[k] if hue == 0 else hue_rotate(sprites[k], hue)
            ids[key] = f"sprite_{k}" + ("" if hue == 0 else f"_hue{int(hue):+d}")
            assets.append({"id": ids[key], "w": int(img.shape[1]), "h": int(img.shape[0]), "u": "",
                           "p": "data:image/png;base64," + base64.b64encode(png_bytes(img)).decode("ascii"), "e": 1})
        return ids[key], max(sprites[k].shape[:2])

    def keys(frames, vals):
        return {"a": 1, "k": [{"t": f, "s": v, "h": 1} for f, v in zip(frames, vals)]}

    layers = []
    for i in tr.draw_order[::-1].tolist():                          # Lottie draws its first layer on top: the biggest particle first, as simulate() does last
        alive = np.flatnonzero(tr.scale[:, i] > 0)
        if not len(alive):
            continue
        ip, op = int(alive[0]), int(alive[-1]) + 1
        fr = list(range(ip, op))
        hue = 0.0 if p.hue_var == 0 else float(round(float(tr.hue[i]) / HUE_STEP) * HUE_STEP)
        ref, long_side = asset(int(tr.sprite[i]), hue + 0.0)
        k_scale = 100.0 * float(tr.size_frac[i]) * W / long_side
        img_h, img_w = sprites[int(tr.sprite[i])].shape[:2]
        layers.append({
            "ddd": 0, "ind": len(layers) + 1, "ty": 2, "nm": f"particle {i + 1}", "refId": ref, "sr": 1, "ao": 0, "bm": 0,
            "ks": {
                "o": keys(fr, [[round(float(tr.opacity[f, i]) * 100.0, 1)] for f in fr]),
                "r": keys(fr, [[round(math.degrees(float(tr.angle[f, i])), 1)] for f in fr]),
                "p": keys(fr, [[round(float(tr.pos[f, i, 0]) * W, 1), round(float(tr.pos[f, i, 1]) * H, 1), 0] for f in fr]),
                "a": {"a": 0, "k": [img_w / 2.0, img_h / 2.0, 0]},
                "s": keys(fr, [[round(float(tr.scale[f, i]) * k_scale, 2)] * 2 + [100] for f in fr]),
            },
            "ip": ip, "op": op, "st": 0,
        })
    return {"v": "5.7.4", "fr": fps, "ip": 0, "op": F, "w": W, "h": H, "nm": f"reaction burst ({p.count} particles)",
            "ddd": 0, "assets": assets, "layers": layers}
