"""Phase 2 S2: jobs as files. Mirsal writes the job, an operator session fulfils it with the
Higgsfield MCP tools, Mirsal reads the result. The engine stays ignorant of who fulfils the job,
so a plain HTTP provider can replace the MCP operator later behind the same interface.

Ticket first (CLAUDE.md rule 10): claim() writes external_task_id BEFORE the operator waits, so a
crashed operator re-run resumes by ticket instead of paying twice."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

KINDS = ("sheet", "video", "single")
STATUSES = ("REQUESTED", "CLAIMED", "DONE", "FAILED", "TIMEOUT")
PROVIDER = "higgsfield-mcp"

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
    if job.get("task"):  # the task ticket is stored first too (phase_03.md "hard truth" on the file store)
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
               cost=job["cost"], extra={"job": job["id"], "sha256": digest})
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
