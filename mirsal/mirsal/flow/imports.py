"""Bring a file into Mirsal, never twice (Haitham, 2026-10-05: "there should be a way of import with deduplication").

A sheet you made yourself, or a Higgsfield result (downloaded by hand, `hf_20261004_033516_<job id>.mp4`, or picked from Higgsfield's own history) comes in through
one door. Before anything is made, `known` asks whether Mirsal already has it:
- by its **Higgsfield job id**: Higgsfield names its downloads after the job (`hf_<date>_<time>_<job id>.<ext>`), the same id Mirsal records as a job's ticket
  (`external_task_id` in `out/jobs/J###.json`, `out/tasks/*.json`, `out/model_calls.jsonl`);
- by its **bytes** (sha256): `out/model_calls.jsonl` keeps the hash of every result Mirsal downloaded, and `out/imports.jsonl` of every file imported.
A known file answers where it already is (the job, the batch, the effect) and nothing is made. Free: nothing here calls a paid provider."""
from __future__ import annotations

import hashlib
import json
import re
import time
import threading
import uuid
import contextvars
from pathlib import Path

from ..runtime import atomic

JOB_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
IMAGE = (".png", ".jpg", ".jpeg", ".webp")
VIDEO = (".mp4", ".mov", ".webm")
_LOCK = threading.RLock()


class ImportError(Exception):
    def __init__(self, message: str, code: int = 400):
        super().__init__(message)
        self.code = code


def job_id_of(name: str) -> str | None:
    """The Higgsfield job id in a file name (`hf_20261004_033516_b16dc424-22fe-4ad2-8242-e8a36f10209b.mp4`), else None."""
    m = JOB_ID.search(str(name or ""))
    return m.group(0).lower() if m else None


def _ledger(out: Path) -> Path:
    return Path(out) / "imports.jsonl"


def _lines(p: Path):
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    yield row
            except ValueError:
                continue
    except OSError:
        return


def known(out: Path, name: str = "", data: bytes | None = None, job_id: str | None = None) -> dict | None:
    """Where Mirsal already has this file, or None: {by: ticket|bytes, job?, generation?, effect?, import?}."""
    out = Path(out)
    tid = (job_id or job_id_of(name) or "").lower() or None
    sha = hashlib.sha256(data).hexdigest() if data else None
    if tid:
        for f in sorted((out / "jobs").glob("J*.json")):
            try:
                j = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if str(j.get("external_task_id") or "").lower() == tid:
                eff = ((j.get("request") or {}).get("effect") or {})
                if j.get("status") in ("FAILED", "CANCELLED", "DISMISSED") and not j.get("generation"):
                    continue  # A manually recovered result may still be imported.
                return {"by": "ticket", "job": j.get("id"), "generation": j.get("generation"), "effect": eff.get("id") if isinstance(eff, dict) else None,
                        "status": j.get("status"), "recoverable": j.get("status") != "DONE"}
        for f in sorted((out / "tasks").glob("*.json")):
            try:
                task = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if str(task.get("external_task_id") or "").lower() == tid:
                return {"by": "ticket", "task": task.get("id"), "generation": task.get("generation"), "status": task.get("status"), "recoverable": True}
    for d in _lines(out / "model_calls.jsonl"):
        if d.get("status") not in (None, "OK", "DONE") or not d.get("sha256"):
            continue
        if (tid and str(d.get("external_task_id") or "").lower() == tid) or (sha and d.get("sha256") == sha):
            return {"by": "ticket" if tid and str(d.get("external_task_id") or "").lower() == tid else "bytes", "job": d.get("job"), "generation": d.get("generation_id")}
    for d in _lines(_ledger(out)):
        if (tid and d.get("job_id") == tid) or (sha and d.get("sha256") == sha):
            return {"by": "ticket" if tid and d.get("job_id") == tid else "bytes", "import": d.get("id"), "generation": d.get("generation"),
                    "status": d.get("status", "ACCEPTED"), "recoverable": d.get("status") in ("PREPARING", "PROCESSING", "FAILED")}
    return None


def save(out: Path, name: str, data: bytes) -> Path:
    """The imported file, kept under `out/imports/` (never in the watch folders, which are Haitham's)."""
    ext = Path(str(name or "")).suffix.lower()
    if ext not in IMAGE + VIDEO:
        raise ValueError(f"import a picture ({', '.join(IMAGE)}) or a video ({', '.join(VIDEO)})")
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(name).stem)[:60].strip("_") or "import"
    d = Path(out) / "imports"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}-{stem}-{uuid.uuid4().hex[:12]}{ext}"
    atomic.write_bytes(f, data)
    return f


def record(out: Path, name: str, data: bytes, generation: str | None, by: str, job_id: str | None = None) -> dict:
    """One line per import in `out/imports.jsonl`: what came in (name, hash, Higgsfield job id) and the batch it became."""
    row = {"id": "I" + uuid.uuid4().hex, "at": round(time.time(), 3), "name": str(name or "")[:200], "sha256": hashlib.sha256(data).hexdigest(),
           "job_id": (job_id or job_id_of(name) or "").lower() or None, "generation": generation, "by": by, "status": "ACCEPTED"}
    with _LOCK:
        Path(out).mkdir(parents=True, exist_ok=True)
        rows = list(_lines(_ledger(out))) + [row]
        atomic.write_text(_ledger(out), "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    return row


def _update(out: Path, iid: str, **values) -> dict:
    with _LOCK:
        rows = list(_lines(_ledger(out)))
        row = next(r for r in rows if r["id"] == iid)
        row.update(values)
        atomic.write_text(_ledger(out), "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        return row


def generation_id(value) -> int:
    if not re.fullmatch(r"G?0*[1-9][0-9]*", str(value or ""), re.I):
        raise ImportError("generation must be a batch number, such as G104")
    return int(str(value).upper().removeprefix("G"))


def destination(c, generation, sheet=None):
    from . import pipeline as pl, gates
    gid = generation_id(generation)
    res = pl.read_result(c.out, gid)
    aid = sheet or next((v["id"] for v in res.get("video_sheets", []) if v.get("status") in ("APPROVED", "VIDEO_BLOCKED")), None)
    if not aid or not re.fullmatch(r"A[1-9][0-9]*", str(aid)):
        raise ImportError("Approve a video sheet (G3) in the destination batch first", 409)
    v = gates.sheet_of(res, aid)
    if v.get("status") not in ("APPROVED", "VIDEO_BLOCKED"):
        raise ImportError("Approve this video sheet (G3) before importing its video", 409)
    return gid, aid


def import_file(c, user: dict, name: str, data: bytes, prompt: str = "", generation=None, sheet=None, job_id=None, retry=False) -> tuple[int, dict]:
    """One serialized import lifecycle. Console holds the cross-process writer lock.

    The ledger reserves bytes before mutation, records the batch before background
    work, and makes failures addressable. An explicit retry reuses that batch.
    """
    from . import pipeline as pl, gates, sources
    from ..media.video_project import MAX_UPLOAD
    if not data or len(data) > MAX_UPLOAD:
        raise ImportError("empty upload" if not data else "file too large", 400 if not data else 413)
    ext = Path(name).suffix.lower()
    if ext not in IMAGE + VIDEO:
        raise ImportError("Import a PNG, JPEG, WebP, MP4, MOV or WebM file")
    with _LOCK:
        hit = known(c.out, name, data, job_id)
        if hit and not (retry and hit.get("import") and hit.get("recoverable")):
            return 200, {"duplicate": True, **hit}
        if not c.lock.acquire(blocking=False):
            raise ImportError("busy: a job is running, wait for it to finish", 409)
        row = None
        handed_off = False
        try:
            old = next((r for r in _lines(_ledger(c.out)) if hit and r.get("id") == hit.get("import")), None)
            if old and old.get("by") != user["id"]:
                raise ImportError("not found", 404)
            is_video = ext in VIDEO
            resume_video = False
            if is_video and old and old.get("generation"):
                gid, aid = generation_id(old["generation"]), old.get("sheet")
                res = pl.read_result(c.out, gid)
                status = gates.sheet_of(res, aid).get("status")
                if status == "SLICED" and not res.get("error"):
                    _update(c.out, old["id"], status="READY", error=None)
                    return 200, {"duplicate": True, **hit, "status": "READY", "recoverable": False}
                resume_video = status == "VIDEO_RETURNED"
                if not resume_video:
                    gid, aid = destination(c, gid, aid)
            if is_video and not resume_video:
                if not old or not old.get("generation"):
                    gid, aid = destination(c, generation, sheet)
            elif not is_video:
                gid, aid = None, None
            f = Path(old["file"]) if old and old.get("file") and Path(old["file"]).is_file() else save(c.out, name, data)
            if is_video:
                from ..engine.ffmpeg import probe
                try:
                    info = probe(f)
                    if not info.get("codec") or not info.get("width") or not info.get("height"):
                        raise ValueError("no video stream")
                except Exception as e:
                    raise ImportError("This video cannot be opened; choose a valid MP4, MOV or WebM") from e
            if not is_video:
                try:
                    pl.load_rgb(f)
                except Exception as e:
                    f.unlink(missing_ok=True)
                    raise ImportError("This image cannot be opened; choose a valid PNG, JPEG or WebP") from e
            row = old or record(c.out, name, data, None, user["id"], job_id)
            _update(c.out, row["id"], status="PREPARING", file=str(f), kind="video" if is_video else "sheet", sheet=aid)
            if is_video:
                _update(c.out, row["id"], generation=f"G{gid:03d}")
                if not resume_video:
                    gates.attach_video(c.out, gid, aid, data, name, custom=True)
                work = lambda: gates.slice_video(c.out, gid, aid, c.cfg, c.pace)
            else:
                subject = subject_of(name, prompt)
                # A crash after start but before the ledger update is recovered by source path.
                previous = old.get("generation") if old else None
                if old and not previous and old.get("file"):
                    for n in pl.list_ids(c.out):
                        try:
                            saved = pl.read_result(c.out, n)
                        except pl.PipelineError as e:
                            if e.code == 404:
                                continue
                            raise
                        if saved.get("source", {}).get("sheet_path") == old["file"]:
                            previous = f"G{n:03d}"
                            break
                if previous:
                    gid = generation_id(previous)
                else:
                    pick = sources.Pick(subject=re.sub(r"\W+", "_", subject.lower()).strip("_")[:40] or "import", subject_id="import", variant=1, n_variants=1, sheet=f, video=None)
                    tok = pl.OWNER.set(user["id"])
                    try:
                        gid = pl.start(subject, c.out, c.inp, pick=pick)
                    finally:
                        pl.OWNER.reset(tok)
                work = lambda: pl.run_stills(c.out, gid, c.cfg, c.pace)
            _update(c.out, row["id"], generation=f"G{gid:03d}", status="PROCESSING")
            ctx = contextvars.copy_context()
            ctx.run(pl.OWNER.set, user["id"])

            def run():
                try:
                    work()
                    res = pl.read_result(c.out, gid)
                    _update(c.out, row["id"], status="FAILED" if res.get("error") else "READY", error=res.get("error"))
                except Exception as e:
                    _update(c.out, row["id"], status="FAILED", error=str(e)[:300])
                finally:
                    c.lock.release()
            threading.Thread(target=ctx.run, args=(run,), daemon=True).start()
            handed_off = True
            return 202, {"id": gid, "kind": "video" if is_video else "sheet", "import": row["id"], **({"sheet": aid} if is_video else {"subject": subject})}
        except Exception as e:
            if row:
                _update(c.out, row["id"], status="FAILED", error=str(e)[:300])
            raise
        finally:
            if not handed_off:
                c.lock.release()


def history(c, size: int = 40) -> dict:
    from ..generation import higgsfield as hf
    if not 1 <= size <= 100:
        raise ImportError("size must be 1 to 100")
    if not hf.available():
        raise ImportError("The Higgsfield CLI is not installed or signed in", 503)
    rows = []
    try:
        for kind in ("image", "video"):
            got = hf._json(["generate", "list", f"--{kind}", "--size", str(size), "--json"], timeout=90)
            if not isinstance(got, list) or any(not isinstance(r, dict) for r in got):
                raise ImportError("Higgsfield returned an unreadable job list", 502)
            for r in got:
                params = r.get("params") if isinstance(r.get("params"), dict) else {}
                rows.append({"id": r.get("id"), "kind": kind, "model": r.get("job_type"), "status": r.get("status"), "created": r.get("created_at"),
                             "prompt": str(params.get("prompt") or "")[:200], "thumb": r.get("min_result_url") or r.get("thumbnail_url") or r.get("result_url"), "known": known(c.out, job_id=r.get("id"))})
    except hf.HiggsError as e:
        raise ImportError(str(e), 502) from e
    rows.sort(key=lambda r: str(r.get("created") or ""), reverse=True)
    return {"jobs": rows}


def import_job(c, user: dict, job: str, **options) -> tuple[int, dict]:
    from ..generation import higgsfield as hf
    from ..media.video_project import MAX_UPLOAD
    from urllib.parse import urlparse
    import tempfile
    if not JOB_ID.fullmatch(job or ""):
        raise ImportError("id must be a Higgsfield job id")
    hit = known(c.out, job_id=job)
    if hit and not options.get("retry"):
        return 200, {"duplicate": True, **hit}
    try:
        g = hf._json(["generate", "get", job, "--json"], timeout=60)
        g = g[0] if isinstance(g, list) and len(g) == 1 else g
        if not isinstance(g, dict):
            raise ImportError("Higgsfield returned an unreadable job", 502)
        url = g.get("result_url")
        if g.get("status") != "completed" or not isinstance(url, str) or not url:
            raise ImportError("That Higgsfield job has no finished file yet", 409)
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ImportError("Higgsfield returned an invalid result URL", 502)
        ext = Path(parsed.path).suffix.lower()
        if ext not in IMAGE + VIDEO:
            raise ImportError("Higgsfield result must be a supported image or video", 400)
        if ext in VIDEO and not (hit and options.get("retry") and hit.get("import")):
            destination(c, options.get("generation"), options.get("sheet"))
        with tempfile.TemporaryDirectory(prefix="mirsal-hf-import-") as tmp:
            f = Path(tmp) / ("result" + ext)
            hf.download(url, f, max_bytes=MAX_UPLOAD)
            data = f.read_bytes()
    except hf.HiggsError as e:
        raise ImportError(str(e), 413 if "too large" in str(e) else 502) from e
    return import_file(c, user, f"hf_{job}{ext}", data, job_id=job, **options)


def subject_of(name: str, prompt: str = "") -> str:
    """What the batch is about: the person's words, else the file's name without Higgsfield's date and job id."""
    if str(prompt or "").strip():
        return " ".join(str(prompt).split())[:120]
    s = JOB_ID.sub(" ", Path(str(name or "")).stem)
    s = re.sub(r"[_-]+", " ", s)
    s = re.sub(r"\bhf\b|\b\d{6,8}\b", " ", s, flags=re.I)
    return " ".join(s.split())[:120] or "imported sheet"
