"""Remove a batch (Haitham, 2026-10-03, "like remove pack"): `out/G###` moves to `out/trash/batches/G###` and Restore moves it back. Nothing is deleted (a batch is paid work; rule 9's
spirit: the folder keeps its name and its files keep theirs). Stickers already added to a pack are copies in the library and stay in their packs. A removed number is never given to a
new batch while it is in the trash (`pipeline.next_gid`), so a Restore can never collide. Plain functions over the files: no HTTP, no database (CLAUDE.md rules 3 and 11)."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from ..generation import jobs
from ..runtime import atomic
from . import pipeline as pl

OPEN_JOBS = ("REQUESTED", "CLAIMED")


def _gid(job) -> int | None:
    g = job.get("generation")
    try:
        return int(str(g).lstrip("G")) if g not in (None, "") else None
    except ValueError:
        return None


def remove(out: Path, gid: int, by: str = "human") -> dict:
    """Move batch `gid` to the trash. Refused in words while a job for it is in flight (the job would write into a folder that is gone)."""
    out = Path(out)
    src = pl.gen_dir(out, gid)
    if not (src / "result.json").is_file():
        raise pl.PipelineError(f"No generation G{gid:03d}", 404)
    busy = [j["id"] for j in jobs.list(out) if j.get("status") in OPEN_JOBS and _gid(j) == gid]
    if busy:
        raise pl.PipelineError(f"G{gid:03d} cannot be removed while {', '.join(busy)} is still working on it. Wait for it to finish, then remove the batch.", 409)
    dest = pl.trash_batches_dir(out) / f"G{gid:03d}"
    if dest.exists():
        raise pl.PipelineError(f"G{gid:03d} is already in the trash.", 409)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    meta = {"id": f"G{gid:03d}", "number": gid, "removed": round(time.time(), 3), "by": by}
    atomic.write_text(dest.parent / f"G{gid:03d}.meta.json", json.dumps(meta, indent=2))
    return meta


def restore(out: Path, gid: int) -> dict:
    """Put a removed batch back under the same name. Never overwrites: if something is there now, it says so and the removed one stays safe."""
    out = Path(out)
    src = pl.trash_batches_dir(out) / f"G{gid:03d}"
    if not src.is_dir():
        raise pl.PipelineError(f"G{gid:03d} is not in the trash.", 404)
    dest = pl.gen_dir(out, gid)
    if dest.exists():
        raise pl.PipelineError(f"G{gid:03d} cannot be restored: a batch with that number exists now.", 409)
    shutil.move(str(src), str(dest))
    (src.parent / f"G{gid:03d}.meta.json").unlink(missing_ok=True)
    return {"id": f"G{gid:03d}", "number": gid, "restored": True}


def list_removed(out: Path) -> list[dict]:
    """The trash, newest first: [{id, number, removed, by, subject}] (the subject is read from the batch's own result so the person can tell them apart)."""
    rows = []
    for gid in pl.removed_ids(Path(out)):
        meta = {"id": f"G{gid:03d}", "number": gid, "removed": None, "by": None}
        f = pl.trash_batches_dir(Path(out)) / f"G{gid:03d}.meta.json"
        try:
            meta.update(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
        try:
            r = json.loads((pl.trash_batches_dir(Path(out)) / f"G{gid:03d}" / "result.json").read_text(encoding="utf-8"))
            meta["subject"] = (r.get("source") or {}).get("subject") or r.get("task_slug")
        except (OSError, ValueError):
            meta["subject"] = None
        rows.append(meta)
    return sorted(rows, key=lambda m: m.get("removed") or 0, reverse=True)
