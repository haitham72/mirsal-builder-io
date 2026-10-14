"""Lottie style reactions (Haitham, 2026-10-14; console/reactions.js "Style: Lottie"): every particle is a whole Lottie animation from the drop zone.

Emoji style (flow/emoji_reactions.py) stays as it is; this is the second, permanent style. No emoji bank, no glyphs, no motion presets: each file
in `mirsal/lottie/` (`emoji_reactions.handpicked_dir`) is one reaction, named by its file. Its settings (the neutral engine defaults until saved),
its morph targets and its children live in out/particles/lottie/library.json `{files: {file: {settings, morph_targets, updated}}}`. The export
(`compose`) embeds the origin and every morph target in ONE self-contained Lottie (`engine.lottie.export_lottie_burst`), 512 x 512, 2 s.
docs/reaction/17-17-lottie-style-reactions.md. Errors are particle_sets.SetError (the HTTP layer maps its code). Free: nothing here spends.
"""
from __future__ import annotations

import io
import json
import threading
import time
import zipfile
from pathlib import Path

from ..runtime import atomic
from .emoji_reactions import REACTION_SECONDS, handpicked_blob, handpicked_files
from .particle_sets import SetError, sets_dir

_LOCK = threading.Lock()
SIZE = 512                                                                      # the export's canvas = the dashboard's viewer
# The sliders, in the editor's order; every one is a ParticleParams field except size_var (re-spreads size_min / size_max around their middle).
SETTINGS = ("magnitude", "speed_var", "speed_pulse", "pulse_hz", "gravity", "vortex", "spin", "flip", "flip_var", "count", "spread",
            "particle_size", "size_var", "size_in_dur", "size_out_dur", "fade_start", "fade_dur", "fade_var",
            "morph_at", "morph_var", "children", "child_size", "child_size_var", "seed")
# The neutral start (Haitham: "just pure default", no vortex / confetti / motion preset): the engine's own defaults.
START = {"magnitude": 1.0, "speed_var": 0.0, "speed_pulse": 0.0, "pulse_hz": 2.0, "gravity": 1.0, "vortex": 0.0, "spin": 1.0, "flip": 0.0, "flip_var": 0.0,
         "count": 28, "spread": 360.0, "particle_size": 1.0, "size_var": 0.375, "size_in_dur": 0.0, "size_out_dur": 0.0,
         "fade_start": 0.0, "fade_dur": 0.0, "fade_var": 0.0, "morph_at": 0.0, "morph_var": 0.0, "children": 0, "child_size": 0.5, "child_size_var": 0.0, "seed": 1}
_SIZE_MID = 0.16                                                                # the middle of the engine's default size range (0.10 .. 0.22)


def _lib_path(out: Path) -> Path:
    return sets_dir(out) / "lottie" / "library.json"


def _read(out: Path) -> dict:
    f = _lib_path(out)
    try:
        d = json.loads(atomic.read_text(f)) if f.is_file() else {}
    except (OSError, ValueError):
        d = {}
    if not isinstance(d, dict) or not isinstance(d.get("files"), dict):
        d = {"files": {}}
    return d


def clean_settings(settings) -> dict:
    """Only known keys, only numbers (400 otherwise). Values are clamped by the engine, not here."""
    if settings is None:
        return {}
    if not isinstance(settings, dict):
        raise SetError("settings must be an object")
    bad = sorted(set(settings) - set(SETTINGS))
    if bad:
        raise SetError(f"unknown setting(s): {', '.join(bad)}")
    out = {}
    for k, v in settings.items():
        if v is None or v == "":
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise SetError(f"{k} must be a number")
        out[k] = v
    return out


def _targets(files: set, origin: str, targets) -> list:
    if targets is None:
        return []
    if not isinstance(targets, list) or any(not isinstance(t, str) for t in targets):
        raise SetError("morph_targets must be a list of file names")
    seen = []
    for t in targets:
        if t not in files:
            raise SetError(f"no Lottie file {t}", 404)
        if t != origin and t not in seen:
            seen.append(t)
    return seen


def params(settings=None):
    """The ParticleParams of one reaction: START, the saved / sent settings on top, 2 s, 512 px, centred. 400 for a bad value."""
    from ..engine import particles as _p
    s = {**START, **clean_settings(settings)}
    v = min(max(float(s.pop("size_var")), 0.0), 1.0)
    try:
        return _p.ParticleParams.from_dict({**s, "size_min": _SIZE_MID * (1 - v) if v < 1 else 0.02, "size_max": _SIZE_MID * (1 + v),
                                            "duration": REACTION_SECONDS, "size": SIZE}).clamped()
    except ValueError as ex:
        raise SetError(str(ex))


def listing(out: Path) -> dict:
    """GET lottie-reactions: {files: [{file, name, bytes, w, h, fps, frames, layers, images, base64, saved, settings, morph_targets}], start, keys}."""
    lib = _read(out)["files"]
    rows = []
    for f in handpicked_files():
        rec = lib.get(f["file"]) or {}
        rows.append({**f, "saved": bool(rec), "settings": {**START, **(rec.get("settings") or {})}, "morph_targets": rec.get("morph_targets") or []})
    return {"files": rows, "start": START, "keys": list(SETTINGS), "seconds": REACTION_SECONDS, "size": SIZE}


def save(out: Path, file: str, settings=None, morph_targets=None) -> dict:
    """POST lottie-reactions/{file}: keep its settings and morph targets. 404 for a file not in the drop zone, 400 for a bad setting."""
    names = {f["file"] for f in handpicked_files()}
    if file not in names:
        raise SetError(f"no Lottie file {file}", 404)
    clean = clean_settings(settings)
    params(clean)                                                               # a value the engine refuses is a 400 now, not at export
    tg = _targets(names, file, morph_targets)
    with _LOCK:
        d = _read(out)
        d["files"][file] = {"settings": clean, "morph_targets": tg, "updated": round(time.time(), 3)}
        f = _lib_path(out)
        f.parent.mkdir(parents=True, exist_ok=True)
        atomic.write_text(f, json.dumps(d, ensure_ascii=False, indent=1))
    return {"file": file, "settings": {**START, **clean}, "morph_targets": tg}


def _doc(file: str) -> dict:
    try:
        return json.loads(handpicked_blob(file).decode("utf-8"))
    except (ValueError, UnicodeError):
        raise SetError(f"{file} is not a readable Lottie", 409)


def compose(out: Path, file: str, settings=None, morph_targets=None) -> dict:
    """The reaction as ONE self-contained Lottie: the origin file and every morph target embedded once each. `settings` / `morph_targets` given =
    the editor's unsaved values (the viewer), None = the saved ones (the download). 404 for an unknown file, 400 for a bad setting or a too big burst."""
    from ..engine import lottie
    names = {f["file"] for f in handpicked_files()}
    if file not in names:
        raise SetError(f"no Lottie file {file}", 404)
    rec = _read(out)["files"].get(file) or {}
    s = (rec.get("settings") or {}) if settings is None else settings
    tg = _targets(names, file, (rec.get("morph_targets") or []) if morph_targets is None else morph_targets)
    try:
        return lottie.export_lottie_burst(params(s), _doc(file), [_doc(t) for t in tg], size=SIZE, name=Path(file).stem)
    except ValueError as ex:
        raise SetError(str(ex))


def export_zip(out: Path) -> bytes:
    """GET lottie-reactions.zip: every file of the drop zone composed with its saved settings, `<name>.json`, plus manifest.json
    {reactions: [{file, json, morph_targets, settings}], seconds, size}."""
    buf = io.BytesIO()
    man = []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in handpicked_files():
            try:
                doc = compose(out, f["file"])
            except SetError:
                continue
            arc = f["file"]
            z.writestr(arc, json.dumps(doc, separators=(",", ":")))
            rec = _read(out)["files"].get(f["file"]) or {}
            man.append({"file": f["file"], "json": arc, "morph_targets": rec.get("morph_targets") or [], "settings": {**START, **(rec.get("settings") or {})}})
        z.writestr("manifest.json", json.dumps({"reactions": man, "seconds": REACTION_SECONDS, "size": SIZE}, ensure_ascii=False, indent=1))
    return buf.getvalue()
