"""Particle sets `P###`: the DURABLE particle asset (docs/particles_plan.md).

A Telegram particle burst is the effect played when someone reacts to a message with an emoji. A **sticker pack is only the group it is attached to**: a
Barbie pack bursts hearts and flowers, a Batman pack bat signals, and every sticker of the pack shares them. So the unit is **not a sticker** — it is a
**Particle set**, which belongs to one pack, to several packs, or to none (stand-alone). `flow/effects.py` keeps the `E###` *working session* (this run's
analysis, ideas, drawing, picking, previews); this module owns the thing that survives it.

    out/particles/P001/set.json      {id, name, created, user, elements[], source{kind, effect, generation, job}, cells[{n, file, status, warnings[], picked}],
                                     motion{preset, params}, packs[pack ids], credits, history[]}
    out/particles/P001/cells/c01.png the cut particle images (KEPT even when unpicked, so generate-more never loses a variant)
    out/particles/P001/renders/      bursts rendered from this set
    out/trash/particles/P001/        delete moves the folder here; Restore puts it back (rule 9's spirit: nothing is destroyed on a click)

Nothing is approved for a person here: this is a library of particle images and their default motion. **Only Telegram's own limits can make a rendered
burst FAILED** (`engine/effect_video.TECHNICAL`); every other check is a warning the person decides on. A set is never deleted by a click (trash + restore),
never silently re-pointed (assigning is a list edit, never a copy of files), and a set in use says which packs before it goes to the trash."""
from __future__ import annotations

import json
import shutil
import threading
import time
from pathlib import Path

from ..runtime import atomic

_LOCK = threading.RLock()
MAX_NAME = 60
MAX_ELEMENTS = 12
KINDS = ("drawn", "stickers", "video")
VERSION = 1


class SetError(Exception):
    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code


# ---------- storage ----------
def sets_dir(out: Path) -> Path:
    return Path(out) / "particles"


def trash_dir(out: Path) -> Path:
    return Path(out) / "trash" / "particles"


def _dir(out: Path, pid: str) -> Path:
    pid = str(pid).upper()
    d = sets_dir(out) / pid
    if not pid.startswith("P") or not pid[1:].isdigit() or not (d / "set.json").is_file():
        raise SetError(f"no particle set {pid}", 404)
    return d


def _trash(out: Path, pid: str) -> Path:
    pid = str(pid).upper()
    d = trash_dir(out) / pid
    if not pid.startswith("P") or not pid[1:].isdigit() or not (d / "set.json").is_file():
        raise SetError(f"no deleted particle set {pid}", 404)
    return d


def _next_id(out: Path) -> str:
    n = max([int(p.name[1:]) for p in sets_dir(out).glob("P[0-9]*") if p.name[1:].isdigit()]
            + [int(p.name[1:]) for p in trash_dir(out).glob("P[0-9]*") if p.name[1:].isdigit()] or [0]) + 1
    return f"P{n:03d}"


def read(out: Path, pid: str) -> dict:
    return json.loads(atomic.read_text(_dir(out, pid) / "set.json"))


def read_deleted(out: Path, pid: str) -> dict:
    return json.loads(atomic.read_text(_trash(out, pid) / "set.json"))


def _write(out: Path, s: dict) -> dict:
    s["updated"] = round(time.time(), 3)
    atomic.write_text(_dir(out, s["id"]) / "set.json", json.dumps(s, indent=2, ensure_ascii=False))
    return s


def hist(s: dict, actor: str, decision: str, reason: str | None = None, detail=None) -> None:
    s.setdefault("history", []).append({"ts": round(time.time(), 3), "actor": actor, "decision": decision, "reason": reason, "detail": detail})


def _clean_name(name, fallback: str = "") -> str:
    n = " ".join(str(name or "").split())[:MAX_NAME].strip()
    return n or fallback


def _clean_elements(elements) -> list[str]:
    if elements is None:
        return []
    if not isinstance(elements, list) or any(not isinstance(x, str) for x in elements):
        raise SetError("elements must be a list of particle names")
    out: list[str] = []
    for e in elements:
        e = " ".join(str(e).split())[:60].strip(" .,;")
        if e and e.lower() not in {x.lower() for x in out}:
            out.append(e)
    return out[:MAX_ELEMENTS]


def _lib_pack(lib, pid: str) -> dict:
    """One pack of the library (the same call `flow/effects.py` makes), or `SetError` 404 when there is no such pack."""
    from ..media.library import LibraryError
    with lib.lock:
        db = lib._load()
    try:
        return lib._pack(db, pid)
    except LibraryError as ex:
        raise SetError(str(ex), getattr(ex, "code", 404)) from ex


def _clean_packs(packs, lib=None) -> list[str]:
    """The packs a set lives in. With a library, every id must exist (a typo would be a set that belongs to nothing and looks assigned)."""
    if packs is None:
        return []
    if not isinstance(packs, list) or any(not isinstance(x, str) for x in packs):
        raise SetError("packs must be a list of pack ids")
    out: list[str] = []
    for p in packs:
        p = str(p)
        if lib is not None:
            _lib_pack(lib, p)
        if p not in out:
            out.append(p)
    return out


def _clean_motion(motion) -> dict:
    """The set's default motion: {preset, params}. The preset must be one the engine has (`engine/particles.PRESETS`); the params are the engine's own
    `ParticleParams` keys, so a set's motion can never mean something the renderer does not read."""
    if not isinstance(motion, dict):
        return {}
    from ..engine import particles
    out = {}
    if "preset" in motion:
        p = str(motion["preset"])
        if p not in particles.PRESETS:
            raise SetError(f"preset must be one of {', '.join(particles.PRESETS)}")
        out["preset"] = p
    params = motion.get("params")
    if isinstance(params, dict):
        try:
            particles.ParticleParams.from_dict({k: v for k, v in params.items() if k != "preset"})
        except ValueError as e:
            raise SetError(str(e))
        out["params"] = params
    return out


# ---------- what a person sees ----------
def view(out: Path, lib, pid: str) -> dict:
    """The set as the API shows it: the record with the cell files resolved to `/out/` urls, how many cells there are and how many are picked
    (the wizard's numbers), `used_in` the names of the packs it is assigned to, and `trashed: false`. A pure read: nothing is rendered, nothing is written."""
    s = read(out, pid)
    d = _dir(out, pid)
    cells = [cell_view(out, d, c) for c in s.get("cells") or []]
    picked = [c["n"] for c in cells if c.get("picked")]
    return {**s, "cells": cells, "n_cells": len(cells), "n_picked": len(picked), "picked": picked,
            "used_in": pack_names(lib, s.get("packs") or []), "trashed": False}


def cell_view(out: Path, d: Path, c: dict) -> dict:
    f = d / (c.get("file") or "")
    return {**c, "url": f"/out/particles/{d.name}/{c['file']}" if (c.get("file") and f.is_file()) else None, "missing": not (c.get("file") and f.is_file())}


def pack_names(lib, ids) -> list[dict]:
    """The packs a set is in, by id and name (the Library card says "used in: Barbie, Princess"). A pack that is gone is marked `missing`, never dropped silently."""
    out = []
    for p in ids:
        try:
            pk = _lib_pack(lib, p) if lib is not None else {"name": p}
            out.append({"id": p, "name": pk.get("name") or p})
        except SetError:
            out.append({"id": p, "name": p, "missing": True})
    return out


def list_sets(out: Path, lib) -> list[dict]:
    """Every set that is not in the trash, newest first: the Library > Particles cards (cells strip, name, used_in, cost, created)."""
    rows = []
    for p in sorted(sets_dir(out).glob("P[0-9]*")):
        try:
            s = json.loads(atomic.read_text(p / "set.json"))
        except (OSError, ValueError):
            continue
        d = p
        cells = [cell_view(out, d, c) for c in s.get("cells") or []]
        picked = [c for c in cells if c.get("picked")]
        rows.append({"id": s.get("id", p.name), "name": s.get("name") or p.name, "created": s.get("created"), "user": s.get("user"),
                     "kind": (s.get("source") or {}).get("kind"), "elements": list(s.get("elements") or []), "packs": list(s.get("packs") or []),
                     "used_in": pack_names(lib, s.get("packs") or []), "cells": cells, "picked": [c["n"] for c in picked],
                     "n_cells": len(cells), "n_picked": len(picked), "renders": len(s.get("renders") or []),
                     "credits": s.get("credits"), "trashed": False})
    rows.sort(key=lambda r: (r.get("created") or 0, r["id"]), reverse=True)
    return rows


def for_pack(out: Path, lib, pack_id: str) -> dict:
    """The pack's particle studio in one read: every set assigned to it and every burst rendered for it. One source of truth: `set.packs`."""
    all_ = list_sets(out, lib)
    mine = [r for r in all_ if pack_id in (r.get("packs") or [])]
    bursts = []
    for r in mine:
        try:
            s = read(out, r["id"])
        except SetError:
            continue
        for b in s.get("renders") or []:
            if b.get("pack_id") != pack_id:
                continue
            f = sets_dir(out) / r["id"] / (b.get("file") or "")
            bursts.append({"set": r["id"], "set_name": r["name"], **{k: b.get(k) for k in ("id", "preset", "status", "bytes", "warnings", "blocks", "added_to", "created")},
                           "url": f"/out/particles/{r['id']}/{b['file']}" if (b.get("file") and f.is_file()) else None, "missing": not (b.get("file") and f.is_file())})
    bursts.sort(key=lambda b: (b.get("created") or 0, b["set"], b.get("id") or ""), reverse=True)
    return {"pack_id": pack_id, "sets": mine, "bursts": bursts}


# ---------- make one: the working session becomes a durable asset ----------
def set_from_effect(out: Path, lib, eid: str, *, name=None, packs=None, picked=None, user: str = "local") -> dict:
    """**Use as particle set** (`POST /api/particles {from_effect: E###}`): save what this run drew as a durable `P###`.

    The drawn sheet's cells become the set's cells (copied into `out/particles/P###/cells/`, so the set survives the `E###` and the batch); a set made
    of the pack's own stickers has no cells file yet (its particles are the stickers, recorded in `source.kind: stickers`); a video set's cells are the
    keyed cell clips and its render is the clip itself. `packs` defaults to the effect's own pack. Nothing is deleted: the effect and its batch stay."""
    from . import effects as fx
    e = fx.view(out, eid)
    s0 = fx.set_of(e) or {}
    gen = s0.get("generation")
    kind = "video" if e.get("mode") == "video" else "drawn"
    rows, notes = [], []
    cells: list[dict] = []
    if gen is not None:
        from . import pipeline as pl
        try:
            res = pl.read_result(out, int(gen))
        except Exception:
            res = None
        if res is not None:
            d = pl.gen_dir(out, int(gen))
            chosen = {int(i) for i in picked} if picked else None
            for st in res.get("stickers") or []:
                f = d / (st.get("png") or "")
                if not st.get("png") or not f.is_file():
                    continue
                if chosen is not None and int(st["index"]) not in chosen:
                    continue
                rows.append((int(st["index"]), f, st))
    if not rows:
        kind = "stickers" if kind != "video" else kind
        notes.append("This set has no drawn cells yet: the burst uses the pack's own stickers (generate more to add drawn particles).")
    default_name = f"{e.get('pack_name') or 'particles'} particles"
    with _LOCK:
        pid = _next_id(out)
        d = sets_dir(out) / pid
        (d / "cells").mkdir(parents=True)
        for n, (idx, f, st) in enumerate(sorted(rows), 1):
            name_rel = f"cells/c{n:02d}.png"
            atomic.write_bytes(d / name_rel, f.read_bytes())
            cells.append({"n": n, "cell": idx, "file": name_rel, "status": st.get("status"), "warnings": list(((st.get("metrics") or {}).get("warnings")) or []),
                          "key": st.get("key"), "picked": True, "created": round(time.time(), 3)})
        pack_ids = _clean_packs(e.get("pack_id") and [e["pack_id"]] if packs is None else packs, lib)
        s = {"id": pid, "name": _clean_name(name, default_name), "created": round(time.time(), 3), "user": user,
             "elements": _clean_elements(s0.get("elements") or [x for g in e.get("groups") or [] for x in g.get("elements") or []]),
             "source": {"kind": kind, "effect": eid, "generation": f"G{int(gen):03d}" if gen is not None else None,
                        "job": s0.get("job"), "grid": s0.get("grid"), "by": s0.get("by"), "options": list(s0.get("options") or [])},
             "cells": cells, "motion": {}, "packs": pack_ids, "renders": [], "credits": 0.0, "notes": notes, "history": []}
        hist(s, user, "CREATE", f"from {eid}: {len(cells)} cell(s), {len(pack_ids)} pack(s)", {"effect": eid, "generation": s["source"]["generation"]})
        atomic.write_text(d / "set.json", json.dumps(s, indent=2, ensure_ascii=False))
    return view(out, lib, pid)


def create(out: Path, lib, *, name=None, elements=None, packs=None, kind: str = "drawn", user: str = "local") -> dict:
    """A stand-alone set the person names now (no sheet yet): `Library > Particles > New particle set`. Its cells arrive with *Generate more*."""
    if kind not in KINDS:
        raise SetError(f"kind must be one of {', '.join(KINDS)}")
    with _LOCK:
        pid = _next_id(out)
        d = sets_dir(out) / pid
        (d / "cells").mkdir(parents=True)
        s = {"id": pid, "name": _clean_name(name, "particles"), "created": round(time.time(), 3), "user": user, "elements": _clean_elements(elements),
             "source": {"kind": kind}, "cells": [], "motion": {}, "packs": _clean_packs(packs, lib), "renders": [], "credits": 0.0, "notes": [], "history": []}
        hist(s, user, "CREATE", f"a new set ({kind})")
        atomic.write_text(d / "set.json", json.dumps(s, indent=2, ensure_ascii=False))
    return view(out, lib, pid)


# ---------- edit ----------
def update(out: Path, lib, pid: str, *, name=None, elements=None, packs=None, picked=None, motion=None, user: str = "local") -> dict:
    """Rename, re-pick the cells, set the default motion, or move the set between packs. A pick never deletes a file: an unpicked cell stays
    (`generate more` appends; nothing is lost)."""
    with _LOCK:
        s = read(out, pid)
        if name is not None:
            s["name"] = _clean_name(name, s["name"])
        if elements is not None:
            s["elements"] = _clean_elements(elements)
        if packs is not None:
            s["packs"] = _clean_packs(packs, lib)
        if motion is not None:
            s["motion"] = _clean_motion(motion)
        if picked is not None:
            keep = _clean_picks(picked)
            have = {int(c["n"]) for c in s.get("cells") or []}
            bad = sorted(set(keep) - have)
            if bad:
                raise SetError(f"cell {', '.join(map(str, bad))} is not in this set")
            if not keep:
                raise SetError("a set needs at least one picked cell (or its own stickers)")
            for c in s.get("cells") or []:
                c["picked"] = int(c["n"]) in keep
        hist(s, user, "EDIT", ", ".join(k for k, v in (("name", name is not None), ("elements", elements is not None), ("packs", packs is not None),
                                                   ("picked", picked is not None), ("motion", motion is not None)) if v))
        _write(out, s)
    return view(out, lib, pid)


def _clean_picks(picked) -> list[int]:
    if not isinstance(picked, list) or any(isinstance(i, bool) or not isinstance(i, int) or i < 1 for i in picked):
        raise SetError("picked must be a list of cell numbers (1 is the first cell)")
    return sorted({int(i) for i in picked})


def assign(out: Path, lib, pid: str, packs, user: str = "local") -> dict:
    """Add packs to the set (it is then used by every sticker of each). A list edit: no file is copied and no batch is touched."""
    with _LOCK:
        s = read(out, pid)
        add = _clean_packs(packs, lib)
        s["packs"] = sorted(set(s.get("packs") or []) | set(add))
        hist(s, user, "ASSIGN", f"now in {', '.join(s['packs']) or 'nothing'}", {"packs": add})
        _write(out, s)
    return view(out, lib, pid)


def unassign(out: Path, lib, pid: str, packs, user: str = "local") -> dict:
    """Take the set off packs. **The set stays** (and its cells): unassigning is not deleting."""
    with _LOCK:
        s = read(out, pid)
        drop = set(_clean_packs(packs))
        s["packs"] = [p for p in (s.get("packs") or []) if p not in drop]
        hist(s, user, "UNASSIGN", f"now in {', '.join(s['packs']) or 'nothing'}", {"packs": sorted(drop)})
        _write(out, s)
    return view(out, lib, pid)


def duplicate(out: Path, lib, pid: str, *, name=None, user: str = "local") -> dict:
    """A copy of the set under a new id, cells and all, with the same packs. The copy is independent: unpicking or deleting one leaves the other."""
    with _LOCK:
        s = read(out, pid)
        src = _dir(out, pid)
        nid = _next_id(out)
        dst = sets_dir(out) / nid
        (dst / "cells").mkdir(parents=True)
        for c in s.get("cells") or []:
            f = src / (c.get("file") or "")
            if f.is_file():
                atomic.write_bytes(dst / c["file"], f.read_bytes())
        for sub in ("renders",):
            if (src / sub).is_dir():
                shutil.copytree(src / sub, dst / sub)
        copy = {**s, "id": nid, "name": _clean_name(name, f"{s.get('name')} (copy)"), "created": round(time.time(), 3), "user": user, "history": [],
                "source": {**(s.get("source") or {}), "duplicated_from": pid}}
        hist(copy, user, "DUPLICATE", f"a copy of {pid}")
        atomic.write_text(dst / "set.json", json.dumps(copy, indent=2, ensure_ascii=False))
    return view(out, lib, nid)


# ---------- delete / restore: nothing is destroyed on a click (rule 9's spirit) ----------
def delete(out: Path, lib, pid: str, *, confirm_packs: bool = False, user: str = "local") -> dict:
    """Move the set to `out/trash/particles/P###/`. A set that is assigned to packs **says which** and needs `confirm_packs` (the screen asks first):
    without it the call is refused with the list, so a set in use can never disappear under a pack by accident. Nothing is deleted from disk."""
    with _LOCK:
        s = read(out, pid)
        used = list(s.get("packs") or [])
        if used and not confirm_packs:
            raise SetError(f"This set is used by {', '.join(n['name'] for n in pack_names(lib, used))}. Deleting it takes it off those packs; "
                           f"confirm to go on.", 409)
        hist(s, user, "DELETE", f"moved to the trash ({', '.join(used) or 'stand-alone'})")
        _write(out, s)
        src, dst = _dir(out, pid), trash_dir(out) / str(pid).upper()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    return {"ok": True, "id": str(pid).upper(), "trashed": True, "was_in": used}


def restore(out: Path, lib, pid: str, user: str = "local") -> dict:
    """Put a deleted set back, under the same id and the same packs. Refused when that id is taken by a live set (duplicate it instead)."""
    with _LOCK:
        s = read_deleted(out, pid)
        if (sets_dir(out) / str(pid).upper() / "set.json").is_file():
            raise SetError(f"{str(pid).upper()} is in use again; duplicate that one instead.", 409)
        dst = sets_dir(out) / str(pid).upper()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(_trash(out, pid)), str(dst))
        s = read(out, pid)
        hist(s, user, "RESTORE", "back from the trash")
        _write(out, s)
    return view(out, lib, pid)


def list_deleted(out: Path, lib) -> list[dict]:
    rows = []
    for p in sorted(trash_dir(out).glob("P[0-9]*")):
        try:
            s = json.loads(atomic.read_text(p / "set.json"))
        except (OSError, ValueError):
            continue
        rows.append({"id": s.get("id", p.name), "name": s.get("name") or p.name, "packs": list(s.get("packs") or []), "deleted": True,
                     "deleted_at": (s.get("history") or [{}])[-1].get("ts")})
    rows.sort(key=lambda r: (r.get("deleted_at") or 0, r["id"]), reverse=True)
    return rows