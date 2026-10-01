"""Every paid or model call is one line in out/model_calls.jsonl (what, parameters, latency,
credits if shown, output path). Phase 3 imports it as model_calls. Never raises; never holds bytes."""
from __future__ import annotations

import json
import time
from pathlib import Path


def log_path(out=None) -> Path:
    if out is not None:
        return Path(out) / "model_calls.jsonl"
    from .paths import out_root
    return out_root() / "model_calls.jsonl"


def append(out, kind: str, provider: str, model: str, status: str = "OK", latency_ms: int | None = None,
           tokens_in: int | None = None, tokens_out: int | None = None, cost=None, attempt: int = 1,
           seed=None, prompt_version: str | None = None, generation_id: str | None = None,
           sticker_id: str | None = None, error: str | None = None, extra: dict | None = None) -> None:
    row = {"ts": round(time.time(), 3), "kind": kind, "provider": provider, "model": model,
           "status": status, "attempt": attempt, "latency_ms": latency_ms,
           "tokens_in": tokens_in, "tokens_out": tokens_out, "cost": cost, "seed": seed,
           "prompt_version": prompt_version, "generation_id": generation_id, "sticker_id": sticker_id,
           "error": (str(error)[:500] if error else None)}
    for k, v in (extra or {}).items():
        if isinstance(v, (bytes, bytearray)):
            continue
        try:
            json.dumps(v)
            row[k] = v
        except (TypeError, ValueError):
            row[k] = str(v)[:500]
    try:
        p = log_path(out)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass
