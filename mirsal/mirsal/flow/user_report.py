"""What each person made and spent (the Users dashboard, docs/api.md "Users"): aggregates computed on request from the stores that already exist, nothing new is written.

- `users.json` (runtime/users.py): identity, role, status, credits left / spent.
- `out/jobs/J###.json` (generation/jobs.py): every paid provider job, its person (`request.user`), its estimate and its real cost, DONE / FAILED.
- `out/model_calls.jsonl`: the paid lines carry the job id, so a person's ledger is the lines of their jobs.
- `out/G###/result.json` (flow/pipeline.py): every batch with its `owner`, prompts, stickers and family (`flow/groups.py`); its folder size is the storage footprint.

`overview` is for the owner and admins (every person, one row each); `detail` is one person, and a member only ever gets their own (the routes check, `console/app.py`).
Nothing here reads another person's data into a row: every list is filtered by the person's id first."""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import pipeline as pl
from ..generation import jobs as jb
from ..generation import model_calls

DAYS = 30
OK_JOBS = ("DONE",)
BAD_JOBS = ("FAILED", "TIMEOUT")


def _day(ts) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(float(ts or 0)))


def _days(now: float | None = None, n: int = DAYS) -> list[str]:
    now = time.time() if now is None else now
    return [_day(now - 86400 * i) for i in range(n - 1, -1, -1)]


def _owner_of_job(j: dict) -> str:
    return str((j.get("request") or {}).get("user") or "local")


def _all_jobs(out: Path) -> list[dict]:
    try:
        return jb.list(Path(out))
    except Exception:
        return []


def _batches(out: Path) -> list[dict]:
    rows = []
    for gid in pl.list_ids(Path(out)):
        try:
            res = pl.read_result(Path(out), gid)
        except Exception:
            continue
        rows.append(res)
    return rows


def _paid_lines(out: Path) -> list[dict]:
    """The model-call lines that cost credits or belong to a job (the local chat model's free lines are not a person's spend)."""
    p = model_calls.log_path(out)
    if not p.is_file():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if isinstance(d, dict) and (d.get("job") or d.get("cost")):
            rows.append(d)
    return rows


def _size(d: Path) -> int:
    total = 0
    if d.is_dir():
        for f in d.rglob("*"):
            try:
                if f.is_file() and not f.is_symlink():
                    total += f.stat().st_size
            except OSError:
                continue
    return total


def _cost(j: dict) -> float:
    try:
        return float(j.get("cost") or 0) if j.get("status") in OK_JOBS else 0.0
    except (TypeError, ValueError):
        return 0.0


def _estimate(j: dict):
    v = j.get("cost_estimate", (j.get("request") or {}).get("estimate"))
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _series(days: list[str], jobs: list[dict], batches: list[dict]) -> dict:
    spend = {d: 0.0 for d in days}
    made = {d: 0 for d in days}
    for j in jobs:
        d = _day(j.get("completed_at") or j.get("created_at"))
        if d in spend:
            spend[d] = round(spend[d] + _cost(j), 3)
    for r in batches:
        d = _day(r.get("created"))
        if d in made:
            made[d] += 1
    return {"days": days, "spend": [spend[d] for d in days], "batches": [made[d] for d in days]}


def _people(users) -> list[dict]:
    """The accounts plus the owner of this machine ("local"), who has no account row but owns batches and jobs."""
    rows = [dict(u) for u in users]
    if not any(u.get("id") == "local" for u in rows):
        rows.insert(0, {"id": "local", "name": "Owner (this machine)", "role": "owner", "status": "active"})
    return rows


def _row(u: dict, jobs: list[dict], batches: list[dict], out: Path, days: list[str]) -> dict:
    ok = [j for j in jobs if j.get("status") in OK_JOBS]
    bad = [j for j in jobs if j.get("status") in BAD_JOBS]
    last = max([float(j.get("created_at") or 0) for j in jobs] + [float(r.get("created") or 0) for r in batches] + [float(u.get("last_seen") or 0)] or [0]) or None
    return {"id": u["id"], "name": u.get("name"), "email": u.get("email"), "role": u.get("role"), "status": u.get("status") or "active",
            "credits_left": u.get("credits_left"), "credits_spent": u.get("credits_spent"),
            "batches": len(batches), "stickers": sum(1 for r in batches for s in r.get("stickers") or [] if s.get("status") == "READY"),
            "animated": sum(1 for r in batches for s in r.get("stickers") or [] if s.get("anim_status") == "READY"),
            "jobs_ok": len(ok), "jobs_failed": len(bad), "spent": round(sum(_cost(j) for j in jobs), 3),
            "estimated": round(sum(_estimate(j) or 0 for j in ok), 3),
            "bytes": sum(_size(pl.gen_dir(out, int(r.get("number") or 0))) for r in batches if r.get("number")),
            "last_active": last, "series": _series(days, jobs, batches)}


def overview(out: Path, users: list) -> dict:
    """One row per person (owner and admins see this): counts, spend, storage and a 30-day series each, plus the totals."""
    out = Path(out)
    days = _days()
    all_jobs, all_batches = _all_jobs(out), _batches(out)
    rows = []
    for u in _people(users):
        uid = u["id"]
        rows.append(_row(u, [j for j in all_jobs if _owner_of_job(j) == uid], [r for r in all_batches if str(r.get("owner") or "local") == uid], out, days))
    rows = [r for r in rows if r["id"] != "local" or r["batches"] or r["jobs_ok"] or r["jobs_failed"]]
    totals = {k: round(sum(r[k] or 0 for r in rows), 3) for k in ("batches", "stickers", "jobs_ok", "jobs_failed", "spent", "bytes")}
    totals["series"] = {"days": days, "spend": [round(sum(r["series"]["spend"][i] for r in rows), 3) for i in range(len(days))],
                        "batches": [sum(r["series"]["batches"][i] for r in rows) for i in range(len(days))]}
    return {"users": rows, "totals": totals}


def detail(out: Path, user: dict, limit: int = 60) -> dict:
    """One person: identity, credits, their 30-day series, their jobs (cost vs estimate), their ledger lines, their storage, and their batches grouped by family with
    prompts and media links. Only rows whose owner is this person are read into it."""
    out = Path(out)
    uid = user["id"]
    days = _days()
    jobs = [j for j in _all_jobs(out) if _owner_of_job(j) == uid]
    batches = [r for r in _batches(out) if str(r.get("owner") or "local") == uid]
    mine = {j["id"] for j in jobs}
    ledger = [{"ts": d.get("ts"), "kind": d.get("kind"), "model": d.get("model"), "status": d.get("status"), "cost": d.get("cost"), "job": d.get("job")}
              for d in _paid_lines(out) if d.get("job") in mine][-200:][::-1]
    fams: dict = {}
    for r in sorted(batches, key=lambda r: -float(r.get("created") or 0))[:limit]:
        gid = r.get("generation_id") or f"G{int(r.get('number') or 0):03d}"
        root = str(r.get("group") or (f"G{int(r['parent']):03d}" if str(r.get("parent") or "").isdigit() else gid))
        fams.setdefault(root, []).append({
            "id": gid, "number": r.get("number"), "created": r.get("created"), "stage": r.get("stage"), "kind": r.get("kind") or "stickers",
            "prompt": r.get("prompt"), "sheet_prompt": r.get("sheet_prompt"), "video_prompt": r.get("video_prompt"), "grid": r.get("grid"),
            "stickers": [{"index": s.get("index"), "key": s.get("key"), "status": s.get("status"),
                          "png": f"/out/{gid}/{s['png']}" if s.get("png") else None, "webm": f"/out/{gid}/{s['webm']}" if s.get("webm") else None}
                         for s in r.get("stickers") or []]})
    row = _row(user, jobs, batches, out, days)
    return {"user": {k: row[k] for k in ("id", "name", "email", "role", "status", "credits_left", "credits_spent", "last_active")},
            "summary": {k: row[k] for k in ("batches", "stickers", "animated", "jobs_ok", "jobs_failed", "spent", "estimated", "bytes")},
            "series": row["series"],
            "jobs": [{"id": j["id"], "kind": j.get("kind"), "status": j.get("status"), "cost": j.get("cost"), "estimate": _estimate(j), "generation": j.get("generation"),
                      "label": (j.get("request") or {}).get("label"), "created": j.get("created_at"), "error": j.get("error")}
                     for j in sorted(jobs, key=lambda j: -float(j.get("created_at") or 0))[:100]],
            "ledger": ledger,
            "families": [{"root": k, "batches": v} for k, v in fams.items()]}
