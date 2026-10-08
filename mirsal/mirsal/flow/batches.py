"""Remove a batch (Haitham, 2026-10-03, "like remove pack"): `out/G###` moves to `out/trash/batches/G###` and Restore moves it back. Nothing is deleted by a Remove (a batch is paid work; rule 9's
spirit: the folder keeps its name and its files keep theirs). Stickers already added to a pack are copies in the library and stay in their packs. A removed number is never given to a
new batch while it is in the trash (`pipeline.next_gid`), so a Restore can never collide. Plain functions over the files: no HTTP, no database (CLAUDE.md rules 3 and 11).

The only real delete is the purge of a batch that is ALREADY in the trash (`describe` shows what it would remove, `purge_files` removes the trash entry; flow/purge.py orchestrates it with the
database rows, the ledger and the confirmations). It is idempotent: every step tolerates a half-done earlier run."""
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
        if src.is_dir():
            raise pl.PipelineError(f"No generation G{gid:03d}: that folder holds no batch data (no result.json). It is not removed through the trash: clear it with `python -m mirsal prune-orphans --apply`.", 404)
        raise pl.PipelineError(f"No generation G{gid:03d}", 404)
    busy = [j["id"] for j in jobs.list(out) if j.get("status") in OPEN_JOBS and _gid(j) == gid]
    if busy:
        raise pl.PipelineError(f"G{gid:03d} cannot be removed while {', '.join(busy)} is still working on it. Wait for it to finish, then remove the batch.", 409)
    if trash_entry(out, gid).exists():
        raise pl.PipelineError(f"G{gid:03d} is already in the trash.", 409)
    dest = pl.trash_batches_dir(out) / src.name                 # the folder keeps its label (G111-dog_as_banana-...) in the trash and back
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    meta = {"id": f"G{gid:03d}", "number": gid, "removed": round(time.time(), 3), "by": by}
    atomic.write_text(dest.parent / f"G{gid:03d}.meta.json", json.dumps(meta, indent=2))
    return meta


def restore(out: Path, gid: int) -> dict:
    """Put a removed batch back under the same name. Never overwrites: if something is there now, it says so and the removed one stays safe."""
    out = Path(out)
    src = trash_entry(out, gid)
    if not src.is_dir():
        raise pl.PipelineError(f"G{gid:03d} is not in the trash.", 404)
    dest = out / src.name
    if dest.exists() or pl.gen_dir(out, gid).exists():
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
            r = json.loads((trash_entry(out, gid) / "result.json").read_text(encoding="utf-8"))
            meta["subject"] = (r.get("source") or {}).get("subject") or r.get("task_slug")
        except (OSError, ValueError):
            meta["subject"] = None
        rows.append(meta)
    return sorted(rows, key=lambda m: m.get("removed") or 0, reverse=True)


# ---- purge: the real delete of a batch that is already in the trash (flow/purge.py is the caller; the database rows are store/purge_rows.py's)
def trash_entry(out: Path, gid: int) -> Path:
    return pl.labelled_dir(pl.trash_batches_dir(Path(out)), f"G{gid:03d}")


def _meta_file(out: Path, gid: int) -> Path:
    return pl.trash_batches_dir(Path(out)) / f"G{gid:03d}.meta.json"


def tree(root: Path) -> list[tuple[str, int]]:
    """Every file under `root` as (path relative to it with forward slashes, bytes), sorted. A symlink is counted as the link, never followed."""
    rows = []
    if root.is_dir():
        for f in sorted(root.rglob("*")):
            try:
                if f.is_file() or f.is_symlink():
                    rows.append((f.relative_to(root).as_posix(), 0 if f.is_symlink() else f.stat().st_size))
            except OSError:
                continue
    return rows


def open_jobs(out: Path, gid: int) -> list[str]:
    return [j["id"] for j in jobs.list(Path(out)) if j.get("status") in OPEN_JOBS and _gid(j) == gid]


def describe(out: Path, gid: int, limit: int = 40) -> dict:
    """What a purge of the removed batch `gid` would remove, from the files: its `list_removed` row plus `stickers` (cells in result.json), `content` (stickers | particles), `files_total`, `bytes`, the first `limit`
    files as [{path, bytes}] (`files_truncated` says there are more) and `in_flight` (open jobs that still write into it, which refuse the purge)."""
    out = Path(out)
    row = next((m for m in list_removed(out) if m["number"] == gid), None)
    if row is None:
        raise pl.PipelineError(f"G{gid:03d} is not in the trash.", 404)
    d = trash_entry(out, gid)
    try:
        res = json.loads((d / "result.json").read_text(encoding="utf-8"))
        row["stickers"] = len(res.get("stickers") or [])
        row["content"] = res.get("kind") or "stickers"
    except (OSError, ValueError):
        row["stickers"], row["content"] = 0, "stickers"
    files = tree(d)
    row.update(files_total=len(files), bytes=sum(b for _, b in files), files=[{"path": p, "bytes": b} for p, b in files[:limit]], files_truncated=len(files) > limit,
               in_flight=open_jobs(out, gid))
    return row


def purge_files(out: Path, gid: int) -> dict:
    """Delete the trash entry of batch `gid` (its whole folder and its meta file). Idempotent: nothing there is `{already: True}`. Refused 409 while a live `out/G###` of the same number
    exists (it would be a different batch: nothing here ever touches a live batch) or while a job is in flight for it. Returns what went: {files, bytes}."""
    out = Path(out)
    if pl.gen_dir(out, gid).exists():
        raise pl.PipelineError(f"G{gid:03d} exists as a live batch as well as in the trash; nothing was deleted. Remove or restore one of them first.", 409)
    busy = open_jobs(out, gid)
    if busy:
        raise pl.PipelineError(f"G{gid:03d} cannot be deleted for good while {', '.join(busy)} is still working on it. Wait for it to finish.", 409)
    d, meta = trash_entry(out, gid), _meta_file(out, gid)
    files = tree(d)
    if d.is_dir():
        shutil.rmtree(d)
    meta.unlink(missing_ok=True)
    return {"files": len(files), "bytes": sum(b for _, b in files), "already": not files and not d.exists()}


def export_zip(out: Path, gid: int) -> tuple[bytes, str]:
    """One batch as a download from the Studio (the pack's Download .zip, for a batch): every sticker that is READY and not rejected, as its animation
    when that is ready and not rejected, otherwise its still, under the engine's file names, plus a `manifest.json` (batch, prompt, and per sticker
    its S#, key, emoji, tags, kind and size). Nothing is changed. Returns (zip bytes, a safe file stem)."""
    import io
    import json
    import re
    import zipfile
    from . import pipeline
    r = pipeline.read_result(out, int(gid))
    d = pipeline.gen_dir(out, int(gid))
    rows, buf = [], io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:                     # webm / png are already compressed
        for s in r.get("stickers") or []:
            rev = s.get("review") or {}
            if s.get("status") != "READY" or rev.get("still") == "REJECTED" or not s.get("png"):
                continue
            animated = s.get("anim_status") == "READY" and s.get("webm") and rev.get("anim") != "REJECTED" and (d / s["webm"]).is_file()
            f = d / (s["webm"] if animated else s["png"])
            if not f.is_file():
                continue
            z.write(f, f.name)
            rows.append({"file": f.name, "sticker": f"S{s.get('index')}", "key": s.get("key"), "name": s.get("name"), "emoji": s.get("emoji"),
                         "tags": s.get("tags"), "type": "animated" if animated else "static", "kb": round(f.stat().st_size / 1024, 1)})
        if not rows:
            raise ValueError("this batch has no accepted sticker yet")
        z.writestr("manifest.json", json.dumps({"batch": r.get("generation_id"), "prompt": r.get("prompt"), "count": len(rows), "stickers": rows},
                                               indent=2, ensure_ascii=False))
    stem = re.sub(r"[^a-z0-9]+", "-", f"{r.get('generation_id') or gid}-{r.get('task_slug') or 'stickers'}".lower()).strip("-")
    return buf.getvalue(), stem or "batch"
