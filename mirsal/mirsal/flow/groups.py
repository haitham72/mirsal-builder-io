"""Batch groups (Haitham, 2026-10-04): variations of one idea are ONE family. Earlier batches shows a family as one entry with a strip of its variations, and the
family shares its particles.

A batch's group is derived when it is read, so nothing needs migrating:
- `group: "G104"` in result.json (written by Add to group, or by dragging a batch onto another) names the family's root;
- otherwise the batch follows its recorded `parent` (a chat edit, "more", a redo) to that parent's family;
- otherwise it is its own root.
The target is always the parent: "add X to Y" (or drag X onto Y) puts X and everything in X's family under Y's root. The family is shown with its root's title.
`relation` says why a batch is in its family: `joined` (by hand), `redo` (`regen_of`), `edit` (a `parent`), or None for the root."""
from __future__ import annotations

import time
from pathlib import Path

from . import pipeline as pl


def _num(v) -> int | None:
    s = str(v or "").upper().lstrip("G")
    return int(s) if s.isdigit() else None


def _alive(out: Path, gid: int) -> bool:
    return (pl.gen_dir(out, gid) / "result.json").is_file()


def root_of(out: Path, gid: int) -> int:
    """The family root of a batch: its explicit group, else its parent's root, else itself. A parent that was removed or a loop stops the walk."""
    seen, cur = set(), int(gid)
    while cur not in seen:
        seen.add(cur)
        res = pl.read_result(out, cur)
        nxt = _num(res.get("group"))
        if nxt == cur:                          # left its family: its own root on purpose
            return cur
        if nxt is None:
            nxt = _num(res.get("parent"))
        if nxt is None or not _alive(out, nxt):
            return cur
        cur = nxt
    return cur


def relation(res: dict) -> str | None:
    gid = res.get("number")
    if _num(res.get("group")) not in (None, gid):
        return "joined"
    if res.get("regen_of"):
        return "redo"
    if res.get("parent"):
        return "edit"
    return None


def families(out: Path, ids=None) -> dict[int, list[int]]:
    """root -> its members (root first, then by number) for the batches given (default: every batch on disk)."""
    fam: dict[int, list[int]] = {}
    for gid in (ids if ids is not None else pl.list_ids(out)):
        try:
            fam.setdefault(root_of(out, gid), []).append(gid)
        except Exception:
            continue
    return {r: sorted(m, key=lambda g: (g != r, g)) for r, m in fam.items()}


def members(out: Path, gid: int) -> list[int]:
    r = root_of(out, gid)
    return families(out).get(r, [r])


@pl.serialized
def join(out: Path, gid: int, to: int, by: str = "human") -> dict:
    """Add batch `gid` (and its whole family) to the family of `to`: `to`'s root becomes the parent of all of them (written on `gid`'s old root only). Free, reversible (`leave`)."""
    gid, to = int(gid), int(to)
    for g in (gid, to):
        if not _alive(out, g):
            raise pl.PipelineError(f"G{g:03d} is not a batch on disk", 404)
    new_root, old_root = root_of(out, to), root_of(out, gid)
    if new_root == old_root:
        raise pl.PipelineError(f"G{gid:03d} is already in the family of G{new_root:03d}", 409)
    res = pl.read_result(out, old_root)          # only the old root points at the new one: its members follow it (their parent or an earlier join), so one can still leave with its own edits
    res["group"] = f"G{new_root:03d}"
    res.setdefault("group_history", []).append({"ts": round(time.time(), 3), "actor": by, "decision": "JOIN", "to": f"G{new_root:03d}", "via": f"G{gid:03d}"})
    pl.write_result(out, old_root, res)
    return {"id": f"G{gid:03d}", "root": f"G{new_root:03d}", "members": [f"G{g:03d}" for g in members(out, new_root)]}


@pl.serialized
def leave(out: Path, gid: int, by: str = "human") -> dict:
    """Take a batch out of its family: it becomes its own root again (its own edits follow it). The root itself cannot leave: its family would have no parent."""
    gid = int(gid)
    if not _alive(out, gid):
        raise pl.PipelineError(f"G{gid:03d} is not a batch on disk", 404)
    root = root_of(out, gid)
    if root == gid:
        raise pl.PipelineError(f"G{gid:03d} is the parent of its family; move the others out instead", 409)
    res = pl.read_result(out, gid)
    res["group"] = f"G{gid:03d}"
    res.setdefault("group_history", []).append({"ts": round(time.time(), 3), "actor": by, "decision": "LEAVE", "from": f"G{root:03d}"})
    pl.write_result(out, gid, res)
    return {"id": f"G{gid:03d}", "root": f"G{gid:03d}", "left": f"G{root:03d}", "members": [f"G{g:03d}" for g in members(out, gid)]}
