"""A minimal Anthropic Messages client over urllib (no new dependency). The key is read from the environment or from mirsal/.env, never logged,
never returned by the API. Everything that calls a model goes through `complete`, so tests replace one function."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_MODEL = "claude-sonnet-5-5"
API = "https://api.anthropic.com/v1/messages"
_ENV_LOADED = False


class LLMError(Exception):
    pass


def _load_dotenv() -> None:
    """mirsal/.env (git-ignored): KEY=VALUE lines. The real environment wins."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    f = Path(__file__).resolve().parent.parent / ".env"
    try:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


def configured() -> bool:
    _load_dotenv()
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def model() -> str:
    _load_dotenv()
    return os.environ.get("MIRSAL_LLM_MODEL", DEFAULT_MODEL)


def status() -> dict:
    return {"configured": configured(), "model": model() if configured() else None}


def complete(system: str, user: str, *, max_tokens: int = 2500, timeout: float = 60.0, temperature: float = 0.8) -> tuple[str, dict]:
    """-> (text, meta{model, ms, tokens_in, tokens_out}). Raises LLMError with a plain message that never contains the key."""
    if not configured():
        raise LLMError("No AI key: add ANTHROPIC_API_KEY to mirsal/.env (or the environment).")
    key = os.environ["ANTHROPIC_API_KEY"]
    body = json.dumps({"model": model(), "max_tokens": max_tokens, "temperature": temperature, "system": system,
                       "messages": [{"role": "user", "content": user}]}).encode("utf-8")
    req = urllib.request.Request(API, data=body, method="POST",
                                 headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    from .telegram import _ssl_context          # the same tolerant TLS context (a damaged Windows certificate store must not break this either)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")
        except Exception:
            msg = ""
        raise LLMError(f"The AI service refused the request (HTTP {e.code}){': ' + msg.replace(key, '<key>') if msg else ''}")
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise LLMError("Cannot reach the AI service: " + str(getattr(e, "reason", e)).replace(key, "<key>"))
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    u = data.get("usage") or {}
    return text, {"model": data.get("model") or model(), "ms": int((time.perf_counter() - t0) * 1000), "tokens_in": u.get("input_tokens"), "tokens_out": u.get("output_tokens")}
