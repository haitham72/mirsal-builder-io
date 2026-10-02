"""What was spent and on which models: a read-only roll-up of out/model_calls.jsonl (the ledger every paid or model call appends to) and
out/jobs/*.json (which task and generation a call belonged to). The UI's credits chip and Usage log show this; the daily cap reads
`spent_today`. Credits are Higgsfield's own unit; LLM calls have tokens, not credits."""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import jobs, model_catalog

GROUPS = (("IMAGE", "image"), ("VIDEO", "video"), ("LLM", "llm"))


def _group(kind: str) -> str:
    return next((g for p, g in GROUPS if str(kind).startswith(p)), "other")


def read_rows(out: Path) -> list[dict]:
    f = Path(out) / "model_calls.jsonl"
    rows = []
    try:
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    except OSError:
        pass
    return rows


def _day_start(now: float | None = None) -> float:
    t = time.localtime(now or time.time())
    return time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, -1))


def _credits(r: dict) -> float:
    try:
        return float(r.get("cost") or 0) if r.get("status", "OK") == "OK" else 0.0
    except (TypeError, ValueError):
        return 0.0


def spent_today(out: Path) -> float:
    t0 = _day_start()
    return round(sum(_credits(r) for r in read_rows(out) if (r.get("ts") or 0) >= t0 and str(r.get("provider", "")).startswith("higgsfield")), 2)


def _labels() -> dict:
    return {m["id"]: (m["label"], m["logo"]) for k in model_catalog.KINDS.values() for m in k}


def typical(out: Path) -> dict:
    """Median seconds per 'image:<model>' / 'video:<model>' from the ledger, for the queue's 'about 2:45' estimate."""
    by: dict = {}
    for r in read_rows(out):
        if str(r.get("provider", "")).startswith("higgsfield") and r.get("status", "OK") == "OK" and r.get("latency_ms") and r.get("kind") in ("IMAGE_SHEET", "IMAGE_SINGLE", "VIDEO"):
            by.setdefault(("video:" if r["kind"] == "VIDEO" else "image:") + str(r.get("model")), []).append(r["latency_ms"] / 1000)
    return {k: round(sorted(v)[len(v) // 2]) for k, v in by.items()}


def summary(out: Path, limit: int = 100) -> dict:
    out = Path(out)
    rows, labels = read_rows(out), _labels()
    job_of = {j["id"]: j for j in jobs.list(out)}
    t0 = _day_start()
    by_model, by_group = {}, {}
    total_credits = 0.0
    shown = []
    for r in sorted(rows, key=lambda r: r.get("ts") or 0, reverse=True):
        g = _group(r.get("kind", ""))
        c = _credits(r)
        j = job_of.get(r.get("job") or "") or {}
        lab = labels.get(r.get("model"), (str(r.get("model") or "?"), None))
        if str(r.get("provider", "")).startswith("higgsfield"):
            total_credits += c
            m = by_model.setdefault(r.get("model"), {"model": r.get("model"), "label": lab[0], "logo": lab[1], "group": g, "calls": 0, "credits": 0.0})
            m["calls"] += 1
            m["credits"] = round(m["credits"] + c, 2)
            b = by_group.setdefault(g, {"calls": 0, "credits": 0.0})
            b["calls"] += 1
            b["credits"] = round(b["credits"] + c, 2)
        if len(shown) < limit:
            p = r.get("params") or {}
            shown.append({"ts": r.get("ts"), "group": g, "kind": r.get("kind"), "model": r.get("model"), "label": lab[0], "logo": lab[1],
                          "provider": r.get("provider"), "status": r.get("status"), "credits": c if c else None, "latency_ms": r.get("latency_ms"),
                          "tokens": (r.get("tokens_in") or 0) + (r.get("tokens_out") or 0) or None,
                          "job": r.get("job"), "task": j.get("task"), "generation": j.get("generation") or r.get("generation_id"),
                          "params": ", ".join(f"{k} {v}" for k, v in p.items() if k not in ("aspect_ratio", "start_image", "end_image")) if isinstance(p, dict) else "",
                          "error": r.get("error")})
    runs = {}
    for j in sorted(job_of.values(), key=lambda j: j.get("created_at") or 0):
        key = j.get("task") or j["id"]
        run = runs.setdefault(key, {"run": key, "task": j.get("task"), "prompt": (j.get("request") or {}).get("label") or (j.get("request") or {}).get("prompt", "")[:80],
                                    "generation": None, "credits": 0.0, "jobs": [], "ts": j.get("created_at")})
        run["generation"] = j.get("generation") or run["generation"]
        run["credits"] = round(run["credits"] + float(j.get("cost") or 0), 2)
        run["jobs"].append({"id": j["id"], "kind": j["kind"], "model": j.get("model"), "status": j["status"], "credits": j.get("cost")})
    return {"credits_spent": round(total_credits, 2), "today": spent_today(out), "calls": len(rows),
            "by_model": sorted(by_model.values(), key=lambda m: -m["credits"]), "by_group": by_group,
            "runs": sorted(runs.values(), key=lambda r: -(r["ts"] or 0))[:50], "rows": shown}
