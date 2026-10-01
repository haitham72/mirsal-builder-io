"""A minimal OpenAI (ChatGPT) Chat Completions client over urllib (no new dependency). The key (OPENAI_API_KEY) is read from the environment or from
mirsal/.env, never logged, never returned by the API. Everything that calls a model goes through `complete`, so tests replace one function."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_MODEL = "gpt-4.1-mini"          # override with MIRSAL_LLM_MODEL (any chat model your key can use)
API = "https://api.openai.com/v1/chat/completions"
KEY_VAR = "OPENAI_API_KEY"
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
    return bool(os.environ.get(KEY_VAR))


def model() -> str:
    _load_dotenv()
    return os.environ.get("MIRSAL_LLM_MODEL", DEFAULT_MODEL)


def status() -> dict:
    return {"configured": configured(), "model": model() if configured() else None}


def _post(body: dict, key: str, timeout: float) -> dict:
    req = urllib.request.Request(API, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"content-type": "application/json", "authorization": "Bearer " + key})
    from .telegram import _ssl_context          # the same tolerant TLS context (a damaged Windows certificate store must not break this either)
    with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as r:
        return json.loads(r.read().decode("utf-8"))


def complete(system: str, user: str, *, max_tokens: int = 2500, timeout: float = 60.0, temperature: float = 0.8, json_mode: bool = False) -> tuple[str, dict]:
    """-> (text, meta{model, ms, tokens_in, tokens_out}). Raises LLMError with a plain message that never contains the key.
    json_mode asks for a JSON object (the prompt must say JSON). Reasoning models (gpt-5*, o*) take no temperature; a model that refuses an
    optional parameter (HTTP 400) is retried once without temperature and json_mode."""
    if not configured():
        raise LLMError(f"No AI key: add {KEY_VAR} to mirsal/.env (or the environment).")
    key = os.environ[KEY_VAR]
    m = model()
    body = {"model": m, "max_completion_tokens": max_tokens, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    optional = {}
    if not m.lower().startswith(("gpt-5", "o1", "o3", "o4")):
        optional["temperature"] = temperature
    if json_mode:
        optional["response_format"] = {"type": "json_object"}
    t0 = time.perf_counter()
    data = None
    for attempt in (0, 1):
        try:
            data = _post({**body, **(optional if attempt == 0 else {})}, key, timeout)
            break
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")
            except Exception:
                msg = ""
            if e.code == 400 and attempt == 0 and optional:
                continue
            raise LLMError(f"The AI service refused the request (HTTP {e.code}){': ' + msg.replace(key, '<key>') if msg else ''}")
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise LLMError("Cannot reach the AI service: " + str(getattr(e, "reason", e)).replace(key, "<key>"))
    try:
        text = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise LLMError("The AI service answered in an unexpected shape.")
    u = data.get("usage") or {}
    return text, {"model": data.get("model") or m, "ms": int((time.perf_counter() - t0) * 1000), "tokens_in": u.get("prompt_tokens"), "tokens_out": u.get("completion_tokens")}
