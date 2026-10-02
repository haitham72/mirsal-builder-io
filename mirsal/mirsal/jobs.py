"""Phase 2: jobs as files. Mirsal writes the job; it is fulfilled by `fulfil()` (the Higgsfield CLI, see higgsfield.py) or by an operator
session using the same claim/done/fail calls. The engine stays ignorant of who fulfils the job, so another provider can replace the CLI
behind the same interface.

Ticket first (CLAUDE.md rule 10): claim() writes external_task_id BEFORE the operator waits, so a
crashed operator re-run resumes by ticket instead of paying twice."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import time
from pathlib import Path

KINDS = ("sheet", "video", "single")
STATUSES = ("REQUESTED", "CLAIMED", "DONE", "FAILED", "TIMEOUT")
PROVIDER = "higgsfield-cli"

KIND_CALL = {"sheet": "IMAGE_SHEET", "video": "VIDEO", "single": "IMAGE_SINGLE"}


class JobError(Exception):
    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code


def jobs_dir(out: Path) -> Path:
    d = Path(out) / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def timeout_s() -> int:
    try:
        return max(60, int(os.environ.get("MIRSAL_JOB_TIMEOUT", 20 * 60)))
    except ValueError:
        return 20 * 60


def _now() -> float:
    return round(time.time(), 3)


def next_id(out: Path) -> str:
    n = 0
    d = jobs_dir(out)
    for f in d.glob("J*.json"):
        try:
            n = max(n, int(f.stem[1:]))
        except ValueError:
            pass
    return f"J{n + 1:03d}"


def _path(out: Path, jid: str) -> Path:
    p = (jobs_dir(out) / f"{jid.upper()}.json").resolve()
    if p.parent != jobs_dir(out).resolve() or not p.is_file():
        raise JobError(f"no job {jid.upper()}", 404)
    return p


def _write(p: Path, job: dict) -> dict:
    p.write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
    try:  # Phase 3A write-through: a claimed job is a provider task row; best effort, never raises
        from .store import sync
        sync.sync_job(p.parent.parent, job)
    except Exception:
        pass
    return job


def _expired(job: dict) -> bool:
    if job["status"] not in ("REQUESTED", "CLAIMED"):
        return False
    ref = job.get("claimed_at") or job.get("created_at") or 0
    return _now() - ref > timeout_s()


def read(out: Path, jid: str) -> dict:
    job = json.loads(_path(out, jid).read_text(encoding="utf-8"))
    if _expired(job):
        job = {**job, "status": "TIMEOUT"}
    return job


def list(out: Path, status: str | None = None) -> list[dict]:
    rows = []
    for f in sorted(jobs_dir(out).glob("J*.json")):
        try:
            job = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if _expired(job):
            job = {**job, "status": "TIMEOUT"}
        if status and job["status"] != status.upper():
            continue
        rows.append(job)
    return rows


def create(out: Path, kind: str, task: str | None = None, generation: str | None = None,
           request: dict | None = None, provider: str = PROVIDER) -> dict:
    if kind not in KINDS:
        raise JobError(f"kind must be one of {KINDS}")
    jid = next_id(out)
    return _write(jobs_dir(out) / f"{jid}.json", {
        "id": jid, "kind": kind, "task": task, "generation": generation,
        "provider": provider, "model": None,
        "request": request or {},
        "status": "REQUESTED", "external_task_id": None,
        "result": None, "cost": None, "error": None,
        "created_at": _now(), "claimed_at": None, "completed_at": None})


def claim(out: Path, jid: str, ticket: str) -> dict:
    """Store the provider ticket BEFORE waiting (idempotent retry). Mirrors it into the task file."""
    p = _path(out, jid)
    job = json.loads(p.read_text(encoding="utf-8"))
    if job["status"] not in ("REQUESTED", "TIMEOUT"):
        raise JobError(f"{job['id']} is {job['status']}, cannot claim", 409)
    if not str(ticket or "").strip():
        raise JobError("a ticket is required (the provider job id)", 400)
    job.update(status="CLAIMED", external_task_id=str(ticket).strip(), claimed_at=_now(), error=None)
    _write(p, job)
    if job.get("task"):  # the task ticket is stored first too (CLAUDE.md rule 10, "Hard truth", on the file store)
        try:
            from . import tasks as _t
            t = _t.read_task(out, str(job["task"]))
            t["external_task_id"] = job["external_task_id"]
            t["status"] = "running"
            _t._write(_t.tasks_dir(Path(out)) / f"{int(t['number']):03d}.json", t)
        except Exception:
            pass
    return read(out, jid)


def done(out: Path, jid: str, file: str, model: str, cost=None) -> dict:
    """Attach the fulfilled result. A sheet job then starts the stills run exactly as a prepared sheet does (S3)."""
    from . import model_calls as _mc
    p = _path(out, jid)
    job = json.loads(p.read_text(encoding="utf-8"))
    if job["status"] != "CLAIMED":
        raise JobError(f"{job['id']} is {job['status']}, claim it first", 409)
    src = Path(str(file or ""))
    if not src.is_file():
        raise JobError(f"result file not found: {file}", 400)
    if not str(model or "").strip():
        raise JobError("the model name is required", 400)
    dest = jobs_dir(out) / job["id"] / ("result" + src.suffix.lower())
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    t0 = _now()
    job.update(status="DONE", model=str(model).strip(), completed_at=t0, error=None,
               result={"file": str(dest.relative_to(Path(out))).replace("\\", "/"),
                       "sha256": digest, "bytes": dest.stat().st_size})
    if cost is not None:
        try:
            job["cost"] = float(cost)
        except (TypeError, ValueError):
            raise JobError("cost must be a number", 400)
    _write(p, job)
    _mc.append(out, KIND_CALL[job["kind"]], job["provider"], job["model"], status="OK",
               latency_ms=int((t0 - (job.get("claimed_at") or t0)) * 1000),
               cost=job["cost"], extra={"job": job["id"], "sha256": digest, "external_task_id": job.get("external_task_id"),
                                        "task": job.get("task"), "params": job.get("params"), "output": job["result"]["file"]})
    return job


def fail(out: Path, jid: str, reason: str) -> dict:
    from . import model_calls as _mc
    p = _path(out, jid)
    job = json.loads(p.read_text(encoding="utf-8"))
    if job["status"] not in ("REQUESTED", "CLAIMED", "TIMEOUT"):
        raise JobError(f"{job['id']} is {job['status']}", 409)
    job.update(status="FAILED", error=str(reason or "unknown")[:500], completed_at=_now())
    _write(p, job)
    _mc.append(out, KIND_CALL[job["kind"]], job["provider"], job.get("model") or "unknown",
               status="ERROR", error=job["error"], extra={"job": job["id"]})
    return job


def requeue(out: Path, jid: str) -> dict:
    """A human re-queues a TIMEOUT or FAILED job; a new claim starts it again (never an automatic retry)."""
    p = _path(out, jid)
    job = json.loads(p.read_text(encoding="utf-8"))
    if _expired(job):
        job = {**job, "status": "TIMEOUT"}
    if job["status"] not in ("TIMEOUT", "FAILED"):
        raise JobError(f"{job['id']} is {job['status']}, nothing to re-queue", 409)
    job.update(status="REQUESTED", error=None, claimed_at=None, created_at=_now())  # a fresh waiting period
    return _write(p, job)


def resume(out: Path, jid: str) -> dict:
    """A human retry of a FAILED or TIMEOUT job. With a Higgsfield ticket the job goes back to CLAIMED, so `fulfil` waits for the SAME Higgsfield job again (a transient
    503 while waiting must not lose a paid video, and must not pay twice). Without a ticket nothing was created yet: it is simply requested again."""
    cur = read(out, jid)
    if cur["status"] not in ("FAILED", "TIMEOUT"):
        raise JobError(f"{cur['id']} is {cur['status']}, nothing to retry", 409)
    p = _path(out, jid)
    job = json.loads(p.read_text(encoding="utf-8"))
    if job.get("external_task_id"):
        job.update(status="CLAIMED", error=None, claimed_at=_now(), completed_at=None, stage="working")
    else:
        job.update(status="REQUESTED", error=None, claimed_at=None, completed_at=None, created_at=_now())
    return _write(p, job)


def update(out: Path, jid: str, **fields) -> dict:
    """Merge bookkeeping fields (params, cost_estimate, generation) into a job file."""
    p = _path(out, jid)
    job = json.loads(p.read_text(encoding="utf-8"))
    job.update(fields)
    return _write(p, job)


def attach_generation(out: Path, jid: str, gid: int) -> dict:
    return update(out, jid, generation=f"G{int(gid):03d}")


_PAID = threading.Lock()      # one paid provider call at a time, whoever asks


def _daily_cap() -> float | None:
    try:
        v = float(os.environ.get("MIRSAL_DAILY_CREDITS", ""))
        return v if v > 0 else None
    except ValueError:
        return None


def fulfil(out: Path, jid: str, hf=None, on_done=None) -> dict:
    """Run one job through the Higgsfield CLI. Ticket first: the job is created WITHOUT waiting, its id is stored with `claim` before the
    wait begins, and a job that is already CLAIMED (a crashed run) resumes by its ticket instead of paying twice. Never retries a paid call.
    Returns the job (DONE or FAILED); `on_done(job)` runs after a successful completion."""
    from . import higgsfield as _hf, model_catalog as _mcat, usage as _usage
    hf = hf or _hf
    out = Path(out)
    job = read(out, jid)
    resume = job["status"] == "CLAIMED" and bool(job.get("external_task_id"))
    if not resume and job["status"] not in ("REQUESTED", "TIMEOUT"):
        raise JobError(f"{job['id']} is {job['status']}, nothing to run", 409)
    req = job.get("request") or {}
    kind = "video" if job["kind"] == "video" else "image"
    try:
        model, params = _mcat.resolve(kind, req.get("model"), req.get("options"))
        prompt = str(req.get("prompt") or "")
        if not prompt.strip():
            raise JobError("the job has no prompt", 400)
        media = {}
        refs = [Path(r) if Path(r).is_absolute() else out / r for r in (req.get("refs") or [])]
        if refs:
            if not _mcat.find(kind, model).get("refs"):
                raise JobError(f"{_mcat.find(kind, model)['label']} does not take reference images", 400)
            missing = [str(r) for r in refs if not r.is_file()]
            if missing:
                raise JobError(f"reference image missing: {missing[0]}", 400)
            media["image_references"] = [str(r) for r in refs]
        if kind == "video":
            start = Path(str(req.get("start_image") or ""))
            start = start if start.is_absolute() else out / start
            if not start.is_file():
                raise JobError(f"the start image is missing: {start}", 400)
            media["start_image"] = str(start)
            if _mcat.find("video", model).get("end_image") and req.get("loop", False):
                media["end_image"] = str(start)
        with _PAID:
            if resume:
                ticket, est = job["external_task_id"], job.get("cost_estimate")
            else:
                est = hf.cost(model, params, prompt, **media)
                cap = _daily_cap()
                if cap is not None and _usage.spent_today(out) + est > cap:
                    raise JobError(f"the daily credit cap ({cap:g}) would be exceeded by this {est:g}-credit call", 402)
                ticket = hf.create(model, params, prompt, **media)
                claim(out, jid, ticket)                      # IMMEDIATELY, before waiting
                update(out, jid, params=dict(params, **({"references": len(refs)} if refs else {})), cost_estimate=est, model=model, stage="working")
            if resume:
                update(out, jid, stage="working")
            res = hf.wait(ticket, timeout_s=max(120, min(timeout_s(), 3600) - 60))
            update(out, jid, stage="downloading")
            ext = (res["result_url"].split("?")[0].rsplit(".", 1)[-1] or "bin")[:5].lower()
            tmp = jobs_dir(out) / jid.upper() / f"download.{ext}"
            hf.download(res["result_url"], tmp)
        job = done(out, jid, str(tmp), model, cost=est)
        try:
            tmp.unlink()
        except OSError:
            pass
    except (JobError, _mcat.CatalogError, _hf.HiggsError) as e:
        code = getattr(e, "code", 500)
        if job["status"] in ("REQUESTED", "CLAIMED", "TIMEOUT") or read(out, jid)["status"] in ("REQUESTED", "CLAIMED", "TIMEOUT"):
            fail(out, jid, str(e))
        return read(out, jid)
    if on_done:
        try:
            on_done(job)
        except Exception as e:                             # the sheet is safe in out/jobs; say what did not follow
            job = update(out, jid, follow_up_error=str(e)[:300])
    return job
