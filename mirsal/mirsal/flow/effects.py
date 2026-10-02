"""Particle effects, the lifecycle of one effect `E###` (docs/effects.md).

An effect belongs to a PACK of the library: a person picks a pack (an emoji pack) and some of its stickers, a vision model (or a built-in table) decides what bursts out of each
(`vision/effect_plan.py`), and the result is one 3-second Telegram video sticker per source sticker, added to the pack tagged with the source emoji. Two ways to make the burst:

- **"sim"**: the engine simulates it (`engine/particles.py`) from sprites (the pack's own stickers, or the approved stickers of a sprite-sheet batch) with gravity / explosion / vortex
  sliders. Preview and render are free.
- **"video"**: Kling draws it from text only (`generation/effect_prompts.py`, no start image); the returned clip is cut into cells (`engine/effect_video.py`), one result per cell.

Everything is a file under `out/effects/E###/` (`effect.json`, `src/`, `results/`, `previews/`): addressable by id and reproducible from what is stored (rule 11). Nothing here approves
anything for a person: **adding a result to a pack is the person's click**, recorded in the history. Only Telegram's own limits can make a result FAILED; every other check is a warning."""
from __future__ import annotations

import hashlib
import io
import json
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image

from ..engine import effect_video as ev, particles
from ..generation import effect_prompts as ep
from ..runtime import atomic
from ..vision import effect_plan

MODES = ("video", "sim")
MAX_STICKERS = 24
_LOCK = threading.RLock()


class EffectError(Exception):
    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code


# ---------- storage ----------
def effects_dir(out: Path) -> Path:
    return Path(out) / "effects"


def _dir(out: Path, eid: str) -> Path:
    eid = str(eid).upper()
    d = effects_dir(out) / eid
    if not eid.startswith("E") or not eid[1:].isdigit() or not (d / "effect.json").is_file():
        raise EffectError(f"no effect {eid}", 404)
    return d


def next_id(out: Path) -> str:
    n = max([int(p.name[1:]) for p in effects_dir(out).glob("E[0-9]*") if p.name[1:].isdigit()] or [0]) + 1
    return f"E{n:03d}"


def read(out: Path, eid: str) -> dict:
    return json.loads(atomic.read_text(_dir(out, eid) / "effect.json"))


def _write(out: Path, e: dict) -> dict:
    e["updated"] = round(time.time(), 3)
    atomic.write_text(effects_dir(out) / e["id"] / "effect.json", json.dumps(e, indent=2, ensure_ascii=False))
    return e


def list_effects(out: Path) -> list[dict]:
    rows = []
    for p in sorted(effects_dir(out).glob("E[0-9]*")):
        try:
            e = json.loads(atomic.read_text(p / "effect.json"))
        except (OSError, ValueError):
            continue
        rows.append({k: e.get(k) for k in ("id", "pack_id", "pack_name", "mode", "status", "created", "updated", "title")} | {"stickers": len(e.get("stickers") or []), "results": len(e.get("results") or [])})
    return rows


def hist(e: dict, actor: str, decision: str, reason: str | None = None, detail=None) -> None:
    e.setdefault("history", []).append({"ts": round(time.time(), 3), "actor": actor, "decision": decision, "reason": reason, "detail": detail})


# ---------- the stickers of a pack ----------
def _pack(lib, pack_id: str) -> dict:
    from ..media.library import LibraryError
    with lib.lock:
        db = lib._load()
    try:
        return lib._pack(db, pack_id)
    except LibraryError as ex:
        raise EffectError(str(ex), getattr(ex, "code", 404))


def sticker_rgba(lib, s: dict) -> np.ndarray | None:
    """A sticker of the library as one RGBA picture: a static one as it is, an animated one as the frame with the most on screen (its first second)."""
    f = lib.files / s["file"]
    if not f.is_file():
        return None
    try:
        if s.get("type") == "animated" or f.suffix.lower() == ".webm":
            from ..engine import ffmpeg as ff
            fr = ff.decode_alpha(f, 30, (512, 512))
            if not len(fr):
                return None
            return np.asarray(fr[int(np.argmax([(x[..., 3] > 127).sum() for x in fr]))], np.uint8)
        return np.asarray(Image.open(f).convert("RGBA"), np.uint8)
    except Exception:
        return None


def _png(rgba: np.ndarray) -> bytes:
    b = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(b, "PNG")
    return b.getvalue()


# ---------- create / analyse ----------
def create(out: Path, lib, *, pack_id: str, sticker_ids, mode: str = "video", grid=(2, 2), user: str = "local", note: str = "") -> dict:
    if mode not in MODES:
        raise EffectError(f"mode must be one of {MODES}")
    rows, cols = (int(grid[0]), int(grid[1])) if not isinstance(grid, str) else tuple(int(x) for x in grid.lower().split("x"))
    if not (1 <= rows <= ep.MAX_GRID and 1 <= cols <= ep.MAX_GRID):
        raise EffectError(f"the grid is at most {ep.MAX_GRID}x{ep.MAX_GRID}")
    p = _pack(lib, pack_id)
    by_id = {s["id"]: s for s in p["stickers"]}
    ids = [s["id"] for s in p["stickers"]] if sticker_ids in (None, "all", ["all"]) else list(dict.fromkeys(str(i) for i in sticker_ids))
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise EffectError(f"not in this pack: {', '.join(missing[:3])}", 404)
    if not ids:
        raise EffectError("this pack has no stickers yet")
    if len(ids) > MAX_STICKERS:
        raise EffectError(f"at most {MAX_STICKERS} stickers at a time (pick some)")
    with _LOCK:
        eid = next_id(out)
        d = effects_dir(out) / eid
        (d / "src").mkdir(parents=True)
        stickers = []
        for i in ids:
            s = by_id[i]
            rgba = sticker_rgba(lib, s)
            if rgba is not None:
                (d / "src" / f"{i}.png").write_bytes(_png(rgba))
            stickers.append({"sticker_id": i, "name": s.get("name"), "emoji": s.get("emoji") or "🙂", "file": s.get("file"), "type": s.get("type"), "src": f"src/{i}.png" if rgba is not None else None})
        e = {"id": eid, "created": round(time.time(), 3), "user": user, "pack_id": pack_id, "pack_name": p["name"], "mode": mode, "grid": [rows, cols], "note": (note or "")[:300],
             "title": f"{p['name']} · effects", "status": "NEW", "stickers": stickers, "groups": [], "results": [], "video": {}, "history": []}
        hist(e, user, "CREATE", f"{len(ids)} sticker(s), {mode}")
        return _write(out, e)


def analyse(out: Path, eid: str, *, allowed=None, vlm=None) -> dict:
    """What bursts out of each sticker. `allowed` is the person's yes to sending the pictures to a vision model (None / False: the built-in table answers and the record says so)."""
    e = read(out, eid)
    d = _dir(out, eid)
    items = [{"id": s["sticker_id"], "name": s["name"], "emoji": s["emoji"], "png": (d / s["src"]).read_bytes() if s.get("src") and (d / s["src"]).is_file() else None} for s in e["stickers"]]
    r = effect_plan.analyse(items, vlm=vlm, allowed=allowed, note=e.get("note") or "", out=out)
    with _LOCK:
        e = read(out, eid)
        e.update(groups=r["groups"], per_sticker=r["per_sticker"], notes=r["notes"], analysed_by=r["model"] or "table", status="READY")
        for g in e["groups"]:
            g.setdefault("sprites", "own")
        hist(e, "python", "ANALYSE", ", ".join(f"{g['subject']}: {', '.join(g['elements'])}" for g in e["groups"])[:300], {"model": r["model"]})
        return _write(out, e)


def _group(e: dict, gid: str) -> dict:
    g = next((g for g in e["groups"] if g["id"] == gid), None)
    if not g:
        raise EffectError(f"no group {gid}", 404)
    return g


def set_pieces(out: Path, eid: str, gid: str, *, elements=None, subject=None, style=None, by: str = "you") -> dict:
    """The person edits what bursts (a group's subject / pieces / look). Linted like everything else; the screen colour follows the pieces."""
    with _LOCK:
        e = read(out, eid)
        g = _group(e, gid)
        try:
            clean = ep.lint_plan({"subject": subject if subject is not None else g["subject"], "elements": elements if elements is not None else g["elements"], "style": style if style is not None else g.get("style")})
        except ValueError as ex:
            raise EffectError(str(ex))
        g.update(clean, key=ep.key_colour_for(clean["elements"]), by="you")
        hist(e, by, "EDIT", f"{gid}: {', '.join(clean['elements'])}")
        return _write(out, e)


# ---------- mode "video": Kling from text ----------
def video_plan(out: Path, eid: str, gid: str, grid=None) -> dict:
    """What the page shows before anything is spent: the prompt that will be sent, the screen colour, the grid. (The price is asked of the provider by the caller.)"""
    e = read(out, eid)
    g = _group(e, gid)
    rows, cols = tuple(grid) if grid else tuple(e["grid"])
    d = ep.describe({"subject": g["subject"], "elements": g["elements"], "style": g.get("style")}, rows, cols)
    return {**d, "group": gid, "cells": rows * cols, "stickers": len(g["stickers"])}


def new_video_job(out: Path, eid: str, gid: str, *, grid=None, user: str = "local", model=None, options=None) -> dict:
    """Create (not start) the text-only Kling job of a group. The caller shows the price and starts it with `fulfil_async(job, after=...)`."""
    from ..generation import jobs, model_catalog
    plan = video_plan(out, eid, gid, grid)
    m, params = model_catalog.resolve("video", model, options)
    job = jobs.create(out, "video", request={"model": m, "options": options or {}, "prompt": plan["prompt"], "t2v": True, "label": f"effect {eid} {gid}", "user": user,
                                            "effect": {"id": eid, "group": gid, "grid": plan["grid"], "template": plan["template"], "version": plan["version"], "key": plan["key"], "plan": plan["plan"]}})
    with _LOCK:
        e = read(out, eid)
        e["video"][gid] = {"job": job["id"], "grid": plan["grid"], "key": plan["key"], "status": "REQUESTED"}
        e["status"] = "VIDEO_REQUESTED"
        hist(e, user, "REQUEST", f"{gid}: video job {job['id']} ({plan['grid'][0]}x{plan['grid'][1]})", {"job": job["id"]})
        _write(out, e)
    return job


def on_video_done(out: Path, eid: str, gid: str, job: dict, cfg) -> dict:
    """The clip is back: cut it into cells, make one sticker of each, store the results. Never raises on a bad cell (it comes back FAILED with the reason)."""
    f = Path(out) / (job.get("result") or {}).get("file", "")
    e = read(out, eid)
    v = e["video"].get(gid) or {}
    rows, cols = v.get("grid") or e["grid"]
    cells = ev.cut_cells(f, rows, cols, cfg, v.get("key") or "green")
    d = _dir(out, eid)
    (d / "results").mkdir(exist_ok=True)
    made = []
    for cell in cells:
        r = ev.finish_cell(cell, cfg)
        made.append((cell["index"], r))
    with _LOCK:
        e = read(out, eid)
        for idx, r in made:
            rid = f"R{len(e['results']) + 1:03d}"
            fname = None
            if r.get("data"):
                fname = f"results/{rid}.webm"
                atomic.write_bytes(d / fname, r["data"])
            e["results"].append({"id": rid, "mode": "video", "group": gid, "cell": idx, "file": fname, "bytes": len(r["data"]) if r.get("data") else 0, "status": r["status"],
                                 "checks": r["checks"], "warnings": r["warnings"], "blocks": r["blocks"], "metrics": r["metrics"], "job": job["id"]})
        e["video"][gid] = {**(e["video"].get(gid) or {}), "status": "DONE", "cells": len(made), "cost": job.get("cost")}
        e["status"] = "RESULTS"
        hist(e, "python", "CUT", f"{gid}: {sum(1 for _, r in made if r['status'] == 'READY')} of {len(made)} cells are stickers", {"job": job["id"]})
        return _write(out, e)


# ---------- mode "sim": the engine's own burst ----------
def sprites_of(out: Path, lib, eid: str, gid: str) -> list[np.ndarray]:
    """The pieces of a group: its own stickers (default) or the approved stickers of a sprite-sheet batch ({"generation": 12})."""
    e = read(out, eid)
    g = _group(e, gid)
    src = g.get("sprites") or "own"
    pcs: list[np.ndarray] = []
    if isinstance(src, dict) and src.get("generation") is not None:
        from . import pipeline as pl
        gn = int(str(src["generation"]).upper().lstrip("G"))
        res = pl.read_result(out, gn)
        d = pl.gen_dir(out, gn)
        for st in res["stickers"]:
            if st.get("status") == "READY" and st.get("png") and (st.get("review") or {}).get("still") != "REJECTED":
                pcs.append(np.asarray(Image.open(d / st["png"]).convert("RGBA"), np.uint8))
    else:
        d = _dir(out, eid)
        for sid in g["stickers"]:
            s = next(x for x in e["stickers"] if x["sticker_id"] == sid)
            if s.get("src") and (d / s["src"]).is_file():
                pcs.append(np.asarray(Image.open(d / s["src"]).convert("RGBA"), np.uint8))
    if not pcs:
        raise EffectError("there are no pieces to burst: the sprite batch has no approved stickers yet" if isinstance(src, dict) else "the stickers of this group have no picture", 409)
    return pcs


def set_sprites(out: Path, eid: str, gid: str, source) -> dict:
    """Where a group's pieces come from: "own" or {"generation": N} (an AI sprite sheet cut and approved in the Studio)."""
    if source != "own" and not (isinstance(source, dict) and source.get("generation") is not None):
        raise EffectError('sprites must be "own" or {"generation": N}')
    with _LOCK:
        e = read(out, eid)
        _group(e, gid)["sprites"] = source
        hist(e, "you", "EDIT", f"{gid}: pieces from {source if source == 'own' else 'G%03d' % int(str(source['generation']).upper().lstrip('G'))}")
        return _write(out, e)


def params_for(out: Path, eid: str, sticker_id: str, overrides: dict | None = None) -> particles.ParticleParams:
    """The preset the sticker's mood picked, with the person's slider values on top. Unknown keys raise (the contract is the dataclass)."""
    e = read(out, eid)
    g = next((g for g in e["groups"] if sticker_id in g["stickers"]), None)
    if not g:
        raise EffectError(f"{sticker_id} is not part of this effect", 404)
    try:
        return particles.preset(g["preset"].get(sticker_id, "burst"), **(overrides or {}))
    except ValueError as ex:
        raise EffectError(str(ex))


def _digest(sprites, p) -> str:
    h = hashlib.sha256(json.dumps(p.to_dict(), sort_keys=True).encode())
    for s in sprites:
        h.update(s.tobytes()[:4096])
        h.update(str(s.shape).encode())
    return h.hexdigest()[:16]


def sim_preview(out: Path, lib, eid: str, sticker_id: str, overrides: dict | None = None, size: int = 256) -> dict:
    """The burst as a small looping WebP, rendered by the same engine as the final file (the sliders are live). Cached by what it was made from."""
    e = read(out, eid)
    g = next((g for g in e["groups"] if sticker_id in g["stickers"]), None)
    if not g:
        raise EffectError(f"{sticker_id} is not part of this effect", 404)
    p = params_for(out, eid, sticker_id, overrides)
    pcs = sprites_of(out, lib, eid, g["id"])
    key = _digest(pcs, p) + f"-{int(size)}"
    f = _dir(out, eid) / "previews" / f"{key}.webp"
    if not f.is_file():
        small = particles.ParticleParams.from_dict({**p.to_dict(), "size": int(size)})
        fr = particles.simulate(pcs, small)
        f.parent.mkdir(exist_ok=True)
        atomic.write_bytes(f, particles.preview_webp(fr, size=int(size)))
    return {"url": f"/out/effects/{e['id']}/previews/{f.name}", "file": f"previews/{f.name}", "params": p.to_dict(), "sprites": len(pcs)}


def sim_render(out: Path, lib, eid: str, sticker_id: str, cfg, overrides: dict | None = None) -> dict:
    """The final 512 px WebM of one sticker's burst, judged. A result is stored whatever the checks say (only Telegram's own limits make it FAILED); the person decides."""
    e = read(out, eid)
    g = next((g for g in e["groups"] if sticker_id in g["stickers"]), None)
    if not g:
        raise EffectError(f"{sticker_id} is not part of this effect", 404)
    p = params_for(out, eid, sticker_id, overrides)
    pcs = sprites_of(out, lib, eid, g["id"])
    fr = particles.simulate(pcs, p)
    r = ev.encode_and_check(fr, cfg, label=f"{sticker_id} burst")
    d = _dir(out, eid)
    (d / "results").mkdir(exist_ok=True)
    with _LOCK:
        e = read(out, eid)
        rid = f"R{len(e['results']) + 1:03d}"
        fname = None
        if r.get("data"):
            fname = f"results/{rid}.webm"
            atomic.write_bytes(d / fname, r["data"])
        res = {"id": rid, "mode": "sim", "group": g["id"], "sticker_id": sticker_id, "file": fname, "bytes": len(r["data"]) if r.get("data") else 0, "status": r["status"], "checks": r["checks"],
               "warnings": r["warnings"], "blocks": r["blocks"], "metrics": r["metrics"], "params": p.to_dict()}
        e["results"].append(res)
        e["status"] = "RESULTS"
        hist(e, "python", "RENDER", f"{sticker_id}: {r['status']} {res['bytes'] // 1024} KB", {"result": rid, "warnings": r["warnings"]})
        _write(out, e)
    return res


# ---------- add to the pack (the person's click) ----------
def targets(e: dict, result_ids=None) -> list[tuple[dict, dict]]:
    """(source sticker, result) pairs. A sim result belongs to its sticker; a video result (one per cell) goes to the stickers of its group in order, cell by cell, round robin."""
    res = {r["id"]: r for r in e["results"]}
    chosen = [res[i] for i in (result_ids or [r["id"] for r in e["results"] if r["status"] == "READY"]) if i in res]
    by_sid = {s["sticker_id"]: s for s in e["stickers"]}
    pairs = []
    for r in chosen:
        if r["mode"] == "sim":
            pairs.append((by_sid[r["sticker_id"]], r))
    for gid in {r["group"] for r in chosen if r["mode"] == "video"}:
        g = _group(e, gid)
        cells = sorted((r for r in chosen if r["mode"] == "video" and r["group"] == gid), key=lambda r: r["cell"])
        for n, sid in enumerate(g["stickers"]):
            if cells:
                pairs.append((by_sid[sid], cells[n % len(cells)]))
    return pairs


def add_to_pack(out: Path, lib, eid: str, result_ids=None, pack_id: str | None = None, user: str = "local") -> dict:
    """Put results into a pack as animated stickers tagged with their source sticker's emoji. This click is the person's approval of the effect (history `APPROVE`); a FAILED result (a
    Telegram limit is broken) cannot be added, everything else can, warnings included."""
    e = read(out, eid)
    pairs = targets(e, result_ids)
    if not pairs:
        raise EffectError("there is nothing to add yet: render an effect first", 409)
    bad = [r["id"] for _, r in pairs if r["status"] != "READY" or not r.get("file")]
    if bad:
        raise EffectError(f"{', '.join(sorted(set(bad)))} breaks a Telegram limit (see its checks) and cannot be added", 409)
    pack_id = pack_id or e["pack_id"]
    d = _dir(out, eid)
    added = []
    for s, r in pairs:
        name = f"{(s.get('name') or 'sticker')[:40]} burst"
        st = lib.add_bytes(pack_id, (d / r["file"]).read_bytes(), "webm", name, "animated", s.get("emoji") or "🙂",
                           source={"effect": eid, "result": r["id"], "source_sticker": s["sticker_id"], "source_pack": e["pack_id"]})
        added.append({"sticker": st["id"], "name": st["name"], "result": r["id"], "of": s["sticker_id"]})
    with _LOCK:
        e = read(out, eid)
        for r in e["results"]:
            if r["id"] in {a["result"] for a in added}:
                r["added_to"] = pack_id
        e["status"] = "DONE"
        hist(e, user, "APPROVE", f"{len(added)} effect sticker(s) added to the pack", {"pack": pack_id, "added": added})
        _write(out, e)
    return {"added": added, "pack_id": pack_id}
