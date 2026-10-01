"""Placeholder art for the Studio until real images are dropped into console/assets/styles/ and console/assets/vendors/.
`find()` returns a real file when one exists (png, jpg, webp, svg), otherwise a generated SVG, so the UI never shows a broken image."""
from __future__ import annotations

import re
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"
EXTS = (".png", ".jpg", ".jpeg", ".webp", ".svg")
SAFE = re.compile(r"^[a-z0-9_]{1,40}$")
BRAND = re.compile(r"^[a-z0-9_-]{1,40}\.(png|jpg|svg|webp)$")

# a small teddy-style head drawn in the way each style looks, so the tile says something before the real art arrives
STYLE_ART = {
    "flat_vector": ("#ffe9c9", "#f4a259", "#f4a259", None),
    "toon_shade": ("#dff3ff", "#f4a259", "#c9772e", "toon"),
    "glossy_3d": ("#e8e4ff", "url(#g)", "url(#g)", "gloss"),
    "clay_3d": ("#fdebd8", "url(#c)", "url(#c)", "clay"),
    "realistic": ("#e9e2d6", "url(#r)", "url(#r)", "fur"),
    "hand_drawn": ("#fff7d6", "#f6c177", "#f6c177", "sketch"),
}
LABELS = {"openai": "O", "xai": "xAI", "kuaishou": "K", "kling": "K"}


def style_svg(sid: str) -> str:
    bg, face, ears, fx = STYLE_ART.get(sid, ("#eeeeee", "#bbbbbb", "#bbbbbb", None))
    defs = ('<defs><radialGradient id="g" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#ffd9a8"/><stop offset=".55" stop-color="#f08a3c"/><stop offset="1" stop-color="#b95a1a"/></radialGradient>'
            '<radialGradient id="c" cx=".4" cy=".35" r=".8"><stop offset="0" stop-color="#f6c79a"/><stop offset="1" stop-color="#d9965b"/></radialGradient>'
            '<radialGradient id="r" cx=".4" cy=".35" r=".8"><stop offset="0" stop-color="#c79a63"/><stop offset="1" stop-color="#7d5630"/></radialGradient></defs>')
    extra = ""
    if fx == "toon":
        extra = '<path d="M62 150a58 58 0 0 0 116 0 58 58 0 0 1-116 0z" fill="#00000022"/>'
    elif fx == "gloss":
        extra = '<ellipse cx="96" cy="86" rx="26" ry="14" fill="#ffffff" opacity=".65" transform="rotate(-25 96 86)"/>'
    elif fx == "clay":
        extra = '<ellipse cx="120" cy="170" rx="46" ry="10" fill="#00000014"/>'
    elif fx == "fur":
        extra = "".join(f'<path d="M{70 + i * 11} {96 + (i % 3) * 18}l5 9M{74 + i * 11} {150 - (i % 2) * 14}l-4 10" stroke="#5a3b1d" stroke-opacity=".5" stroke-width="2" fill="none"/>' for i in range(10))
    elif fx == "sketch":
        extra = "".join(f'<path d="M{78 + i * 9} {158}l12 -14" stroke="#9a6a2e" stroke-opacity=".5" stroke-width="2"/>' for i in range(8))
    line = ' stroke="#4a3320" stroke-width="3"' if fx in ("toon", "sketch") else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240">{defs}<rect width="240" height="240" rx="22" fill="{bg}"/>'
            f'<circle cx="68" cy="68" r="26" fill="{ears}"{line}/><circle cx="172" cy="68" r="26" fill="{ears}"{line}/>'
            f'<circle cx="120" cy="128" r="62" fill="{face}"{line}/>{extra}'
            f'<circle cx="98" cy="118" r="7" fill="#2b1d12"/><circle cx="142" cy="118" r="7" fill="#2b1d12"/>'
            f'<ellipse cx="120" cy="146" rx="12" ry="9" fill="#2b1d12"/></svg>')


def vendor_svg(vid: str) -> str:
    t = LABELS.get(vid, (vid[:1] or "?").upper())
    size = 22 if len(t) == 1 else 17
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><circle cx="24" cy="24" r="23" fill="#e9ecf2" stroke="#c8cdd8"/>'
            f'<text x="24" y="31" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700" font-size="{size}" fill="#5b6475">{t}</text></svg>')


def find(kind: str, name: str):
    """(bytes, content-type) for assets/<kind>/<name>.<ext>, else a generated placeholder. None for an unknown kind or unsafe name."""
    if kind == "brand":                       # real files only (the app logo), no generated placeholder
        f = ASSETS / "brand" / name
        if not BRAND.match(name) or not f.is_file():
            return None
        return f.read_bytes(), {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml"}[f.suffix.lower()]
    if kind not in ("styles", "vendors") or not SAFE.match(name):
        return None
    for ext in EXTS:
        f = ASSETS / kind / (name + ext)
        if f.is_file():
            return f.read_bytes(), {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml"}[ext]
    return (style_svg(name) if kind == "styles" else vendor_svg(name)).encode("utf-8"), "image/svg+xml"
