"""Reaction effects (Create > + New, console/reactions.js): one bank emoji -> its fixed motion, flying as the literal glyph -> a Lottie file.

No set, no pack, no sticker: the sprite IS the emoji glyph (`engine.emoji_glyph.render_emoji`), flown by the simulator (`engine.particles`), exported by
`engine.lottie`. Storage is out/particles/emoji/<token>/ (never a P### folder, so the set scans never see it): renders/L###.lottie.json + .png + .webp and
emoji.json (lottie[], history). docs/reaction.md section 13. Errors are particle_sets.SetError (the HTTP handler maps its code). Free: nothing here spends.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from ..runtime import atomic
from .particle_sets import SetError, hist, sets_dir

_LOCK = threading.Lock()

EMOJI_OPTIONS = {"size_in_dur": 0.4, "size_out_dur": 0.4, "hue_var": 25.0}    # the screen's defaults; 0 / 0 / 0 is the plain look
EMOJI_SIM = ("magnitude", "gravity", "vortex", "spin", "count", "spread")    # the Simulation group: Speed, Gravity, Swirl, Rotation, Amount, Spread
EMOJI_PX = 160                                                                  # the glyph's longest side: sharp at the biggest a particle is drawn on 512


def emoji_dir(out: Path, token: str) -> Path:
    return sets_dir(out) / "emoji" / token                                      # never a P### name: the set scans skip it


def emoji_token(token) -> tuple[str, str]:
    """(token, glyph) of one bank emoji, named by its token ("kiss") or by the glyph itself (`actions.token_for_emoji`).
    409 when the bank has neither (the bank is fixed: an unknown emoji is a conflict with it, not a malformed request)."""
    from ..generation import actions as bank
    raw = str(token or "").strip()
    gen = bank.generation_bank()
    t = raw.lower() if raw.lower() in gen else (bank.token_for_emoji(raw) if raw else None)
    if not t or t not in gen:
        raise SetError(f"{raw or 'nothing'} is not an emoji of the bank", 409)
    return t, gen[t]["emoji"]


def emoji_burst(token, *, preset=None, seed=1, size_in_dur=None, size_out_dur=None, hue_var=None, particle_size=None, size_var=None, sim=None, size=512) -> tuple[str, str, str, object]:
    """(token, glyph, preset name, ParticleParams) of one bank emoji: its fixed motion (`emoji_motion.motion_for_token`), or a
    preset override (the override takes the preset's own look: the token's pinned values belong to its own preset), with the
    options on top (None = the screen's default). `particle_size` is how big every emoji looks (0.25-3, None = the motion's own, 1);
    `size_var` is how much the emojis differ in size (0 = all the same, 1 = from almost nothing to twice the average; None = the
    motion's own range): the motion's size range is re-spread around its own average. `sim` overrides the motion's own simulation
    (EMOJI_SIM: magnitude, gravity, vortex, spin, count, spread; a key left out keeps the motion's value; the engine clamps). Deterministic: same emoji + options + seed
    -> the same params. 400 for a bad option."""
    from ..engine import emoji_motion as em, particles as _p
    t, glyph = emoji_token(token)
    motion = em.motion_for_token(t)
    name = str(preset or motion["preset"])
    if name not in _p.PRESETS:
        raise SetError(f"unknown preset {name!r}; choose one of {', '.join(_p.PRESETS)}")
    over = dict(motion["params"]) if name == motion["preset"] else {}
    opts = {k: (EMOJI_OPTIONS[k] if v is None else v) for k, v in (("size_in_dur", size_in_dur), ("size_out_dur", size_out_dur), ("hue_var", hue_var))}
    if particle_size is not None:
        opts["particle_size"] = particle_size
    if sim is not None and not isinstance(sim, dict):
        raise SetError("sim must be an object")
    bad = sorted(set(sim or {}) - set(EMOJI_SIM))
    if bad:
        raise SetError(f"unknown simulation setting(s): {', '.join(bad)}")
    over.update({k: v for k, v in (sim or {}).items() if v is not None})
    for k, v in (*opts.items(), *((k, v) for k, v in over.items() if k in EMOJI_SIM), ("seed", seed), ("size", size), *((("size_var", size_var),) if size_var is not None else ())):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise SetError(f"{k} must be a number")
    try:
        p = _p.preset(name, **over, **opts, seed=int(seed), size=int(size))
        if size_var is not None:
            mid, v = (p.size_min + p.size_max) / 2, min(max(float(size_var), 0.0), 1.0)
            p = _p.ParticleParams.from_dict({**p.to_dict(), "origin": p.origin, "size_min": mid * (1 - v), "size_max": mid * (1 + v)}).clamped()
        return t, glyph, name, p
    except ValueError as ex:
        raise SetError(str(ex))


def _glyph(glyph: str):
    from ..engine import emoji_glyph
    try:
        return emoji_glyph.render_emoji(glyph, EMOJI_PX)
    except RuntimeError as ex:                                                   # no colour emoji font on this machine
        raise SetError(str(ex), 503)


def emoji_preview(out: Path, token, *, preset=None, seed=1, size_in_dur=None, size_out_dur=None, hue_var=None, particle_size=None, size_var=None, sim=None, size=256) -> dict:
    """The emoji's burst as a small looping WebP for the screen, by the same simulator as the Lottie (free). Cached by what it was
    made from, so the same options are the same file."""
    import hashlib
    from ..engine import particles as _p
    if isinstance(size, bool) or not isinstance(size, (int, float)) or not 64 <= size <= 512:
        raise SetError("size must be a whole number from 64 to 512")
    t, glyph, name, p = emoji_burst(token, preset=preset, seed=seed, size_in_dur=size_in_dur, size_out_dur=size_out_dur, hue_var=hue_var,
                                  particle_size=particle_size, size_var=size_var, sim=sim, size=int(size))
    img = _glyph(glyph)
    key = hashlib.sha256(json.dumps({"p": p.to_dict(), "glyph": glyph}, sort_keys=True).encode() + img.tobytes()).hexdigest()[:16]
    f = emoji_dir(out, t) / "previews" / f"{key}-{int(size)}.webp"
    if not f.is_file():
        f.parent.mkdir(parents=True, exist_ok=True)
        atomic.write_bytes(f, _p.preview_webp(_p.simulate([img], p), size=int(size)))
    return {"token": t, "emoji": glyph, "preset": name, "params": p.to_dict(), "url": f"/out/particles/emoji/{t}/previews/{f.name}"}


def export_emoji_lottie(out: Path, token, *, preset=None, seed=1, size_in_dur=None, size_out_dur=None, hue_var=None, particle_size=None, size_var=None, sim=None, size=512, user: str = "local") -> dict:
    """The end of the Reaction effects flow: one bank emoji's fixed motion, flying as the literal glyph, as a playable Lottie JSON
    (web only; Telegram stays WebM). Stores `out/particles/emoji/<token>/renders/L###.lottie.json`, `L###.png` (the glyph asset,
    for inspection) and `L###.webp` (the same burst as a 256 px loop, for its card) and appends to that emoji's `emoji.json` (`lottie[]`, history `LOTTIE`). Same emoji + options + seed -> the same
    JSON bytes on the same machine (the glyph comes from its emoji font). 409 for an emoji outside the bank. Free."""
    from ..engine import lottie, particles as _p
    if isinstance(size, bool) or not isinstance(size, (int, float)) or not 128 <= size <= 1024:
        raise SetError("size must be a whole number from 128 to 1024")
    t, glyph, name, p = emoji_burst(token, preset=preset, seed=seed, size_in_dur=size_in_dur, size_out_dur=size_out_dur, hue_var=hue_var,
                                  particle_size=particle_size, size_var=size_var, sim=sim, size=int(size))
    img = _glyph(glyph)
    png = _p.png_bytes(img)
    doc = lottie.export_lottie(p, png, size=p.size)
    loop = _p.preview_webp(_p.simulate([img], _p.ParticleParams.from_dict({**p.to_dict(), "size": 256})), size=256)
    doc["nm"] = f"{glyph} {t} ({name})"
    data = json.dumps(doc, separators=(",", ":"))
    d = emoji_dir(out, t)
    with _LOCK:                                                                  # one writer per emoji.json
        rec_f = d / "emoji.json"
        rec = json.loads(atomic.read_text(rec_f)) if rec_f.is_file() else {"token": t, "emoji": glyph, "lottie": [], "history": []}
        nums = [int(str(r.get("id"))[1:]) for r in rec.get("lottie") or [] if str(r.get("id", ""))[1:].isdigit()]
        rid = f"L{max(nums + [0]) + 1:03d}"
        (d / "renders").mkdir(parents=True, exist_ok=True)
        atomic.write_text(d / f"renders/{rid}.lottie.json", data)
        atomic.write_bytes(d / f"renders/{rid}.png", png)
        atomic.write_bytes(d / f"renders/{rid}.webp", loop)
        rec.setdefault("lottie", []).append({"id": rid, "preset": name, "params": p.to_dict(), "file": f"renders/{rid}.lottie.json",
                                             "glyph": f"renders/{rid}.png", "preview": f"renders/{rid}.webp", "bytes": len(data), "created": round(time.time(), 3)})
        hist(rec, user, "LOTTIE", f"exported {rid} as Lottie ({name})", {"preset": name, "seed": p.seed})
        atomic.write_text(rec_f, json.dumps(rec, ensure_ascii=False, indent=1))
    return {"id": rid, "token": t, "emoji": glyph, "preset": name, "params": p.to_dict(), "file": f"renders/{rid}.lottie.json",
            "url": f"/out/particles/emoji/{t}/renders/{rid}.lottie.json", "preview": f"/out/particles/emoji/{t}/renders/{rid}.webp",
            "layers": len(doc["layers"]), "assets": len(doc["assets"]), "bytes": len(data)}


def emoji_lotties(out: Path) -> list[dict]:
    """Every created reaction (one per Lottie export), newest first: {id, token, emoji, preset, params, url, preview, bytes, created}.
    `preview` is the export's own looping WebP (None for an export made before it was kept). Read-only, free."""
    rows = []
    for rec_f in sorted((sets_dir(out) / "emoji").glob("*/emoji.json")):
        try:
            rec = json.loads(atomic.read_text(rec_f))
        except (OSError, ValueError):
            continue
        t, base = rec.get("token") or rec_f.parent.name, f"/out/particles/emoji/{rec_f.parent.name}/"
        for x in rec.get("lottie") or []:
            pv = x.get("preview")
            rows.append({"id": x.get("id"), "token": t, "emoji": rec.get("emoji", ""), "preset": x.get("preset"), "params": x.get("params") or {},
                         "url": base + x["file"], "preview": base + pv if pv and (rec_f.parent / pv).is_file() else None,
                         "bytes": x.get("bytes"), "created": x.get("created")})
    rows.sort(key=lambda r: (r.get("created") or 0, r["token"], r["id"] or ""), reverse=True)
    return rows


# ---------- presets: a saved set of editor settings ("Save preset"), applied to many emojis at once ----------
# A preset holds the request settings without the emoji: `preset` (a motion override; absent = each emoji keeps its own motion), the Simulation keys
# that were moved (EMOJI_SIM) and the Shape values. Applied to an emoji it is exactly what the editor would have sent for it. Stored in
# out/particles/emoji/presets.json (a file, so the per-emoji folder scan never sees it); ids preset01, preset02 ... are never reused.
PRESET_KEYS = ("preset", "particle_size", "size_var", "size_in_dur", "size_out_dur", "hue_var", *EMOJI_SIM)
MANY_MAX = 24                                                                   # emojis per Create: one request, a few seconds of simulation each


def _presets_file(out: Path) -> Path:
    return sets_dir(out) / "emoji" / "presets.json"


def _read_presets(out: Path) -> dict:
    f = _presets_file(out)
    return json.loads(atomic.read_text(f)) if f.is_file() else {"presets": [], "next": 1}


def _kwargs(settings: dict) -> dict:
    """A preset's (or a request's) settings as emoji_burst keywords: the Simulation keys go into `sim`."""
    s = dict(settings or {})
    return {**{k: s[k] for k in PRESET_KEYS if k in s and k not in EMOJI_SIM}, "sim": {k: s[k] for k in EMOJI_SIM if s.get(k) is not None}}


def emoji_presets(out: Path) -> list[dict]:
    """The saved presets, oldest first: [{id, name, settings, created}]. Read-only, free."""
    return list(_read_presets(out)["presets"])


def save_emoji_preset(out: Path, settings: dict, *, name=None, user: str = "local") -> dict:
    """Save the editor's settings as the next preset (Preset 01, Preset 02 ...). Strict: an unknown key or a bad value is a 400, checked by
    building the burst once (for the core `happy`), so a preset that saves always applies."""
    if not isinstance(settings, dict):
        raise SetError("settings must be an object")
    bad = sorted(set(settings) - set(PRESET_KEYS))
    if bad:
        raise SetError(f"unknown preset setting(s): {', '.join(bad)}")
    clean = {k: v for k, v in settings.items() if v is not None and v != ""}
    emoji_burst("happy", **_kwargs(clean))
    with _LOCK:
        data = _read_presets(out)
        n = int(data.get("next") or 1)
        rec = {"id": f"preset{n:02d}", "name": (str(name).strip()[:40] if name else "") or f"Preset {n:02d}", "settings": clean,
               "created": round(time.time(), 3), "user": user}
        data["presets"].append(rec)
        data["next"] = n + 1
        _presets_file(out).parent.mkdir(parents=True, exist_ok=True)
        atomic.write_text(_presets_file(out), json.dumps(data, ensure_ascii=False, indent=1))
    return rec


def delete_emoji_preset(out: Path, pid: str) -> dict:
    """Remove one preset (the reactions made with it keep their own params). 404 for an unknown id."""
    with _LOCK:
        data = _read_presets(out)
        keep = [p for p in data["presets"] if p["id"] != pid]
        if len(keep) == len(data["presets"]):
            raise SetError(f"no preset {pid}", 404)
        data["presets"] = keep
        atomic.write_text(_presets_file(out), json.dumps(data, ensure_ascii=False, indent=1))
    return {"deleted": pid, "presets": keep}


def export_many(out: Path, tokens, *, preset_id=None, user: str = "local") -> dict:
    """Create one reaction per emoji with the same settings: a saved preset's, or none (each emoji's own motion with the screen's defaults).
    One emoji that fails does not stop the others: {reactions: [...as export_emoji_lottie, newest last], errors: [{token, error}]}."""
    if not isinstance(tokens, list) or not tokens:
        raise SetError("tokens must be a non-empty list")
    if len(tokens) > MANY_MAX:
        raise SetError(f"at most {MANY_MAX} emojis at once")
    settings = {}
    if preset_id:
        settings = next((p["settings"] for p in emoji_presets(out) if p["id"] == preset_id), None)
        if settings is None:
            raise SetError(f"no preset {preset_id}", 404)
    made, errors = [], []
    for token in dict.fromkeys(str(t) for t in tokens):                    # order kept, repeats dropped
        try:
            made.append(export_emoji_lottie(out, token, user=user, **_kwargs(settings)))
        except SetError as ex:
            errors.append({"token": token, "error": str(ex)})
    return {"reactions": made, "errors": errors, "preset": preset_id or None}
