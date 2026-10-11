"""Shared, cached model catalog and provider routing. Lists never spend credits."""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import urllib.request

DEFAULT_MODEL = "gpt-5.6-luna"
MODEL_ALIASES = {DEFAULT_MODEL: "openai:" + DEFAULT_MODEL,
                 "nararouter:" + DEFAULT_MODEL: "openai:" + DEFAULT_MODEL}
NARAROUTER_VISION = (
    "agnes-2.5-flash", "exo-stealh", "agnes-3-flash",
    "mimo-v2.6-flash-free", "muse-spark-1.3-contributor-free",
    "step-5-preview", "stepfun-3.7-flash", "mimo-v2.6-flash",
)
OPENAI_VISION = (DEFAULT_MODEL, "gpt-5.6-terra", "gpt-5.6-sol", "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini")
_CACHE: dict = {}
_LOCK = threading.Lock()


def default_provider() -> str:
    from . import llm
    return "openai" if llm.cloud_url().startswith("https://api.openai.com/") else "nararouter"


def key_setting(provider: str) -> str:
    """Cloud credentials belong to their provider, regardless of the default URL."""
    from . import llm
    return llm.KEY_VAR if provider == "openai" else llm.ROUTER_KEY_VAR


def endpoint(provider: str) -> tuple[str, str | None]:
    from . import llm
    llm._load_dotenv()
    if provider == "local":
        return llm.local_url(), None
    if provider == "nararouter":
        return llm.cloud_url(), os.environ.get(llm.ROUTER_KEY_VAR) if default_provider() == "nararouter" else None
    if provider == "openai":
        return "https://api.openai.com/v1", os.environ.get(llm.KEY_VAR)
    raise llm.LLMError("Unknown model provider: choose Local, Nararouter or OpenAI")


def normalize_model(value: str) -> str:
    """Luna uses official OpenAI, including selections saved before provider separation."""
    value = str(value or "")
    return MODEL_ALIASES.get(value, value)


def split_model(value: str, *, legacy_local: bool = False) -> tuple[str, str]:
    from . import llm
    value = normalize_model(value)
    head, sep, tail = value.partition(":")
    if sep and head in ("local", "nararouter", "openai"):
        if not tail:
            raise llm.LLMError("Choose a model id after the provider")
        return head, tail
    if legacy_local or value in llm.list_local_models():
        return "local", value
    return default_provider(), value


def _fetch(url: str, key: str) -> dict:
    from .telegram import _ssl_context
    req = urllib.request.Request(url + "/models", headers={"accept": "application/json", "authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=2.0, context=_ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def cloud_models(provider: str, force: bool = False) -> list[dict]:
    from . import llm
    url, key = endpoint(provider)
    # Tests and disabled installations must never contact an external endpoint.
    if not key or os.environ.get("MIRSAL_LLM_PROVIDER") == "none":
        return []
    cache_key = (provider, url, hashlib.sha256(key.encode()).hexdigest())
    with _LOCK:
        previous = _CACHE.get(cache_key)
        if previous and not force and time.monotonic() - previous[0] < previous[1]:
            return [dict(row) for row in previous[2]]
        rows, ttl = [], 10.0
        try:
            data = _fetch(url, key)
            listed = {str(row["id"]) for row in data.get("data", []) if isinstance(row, dict) and row.get("id")}
            allow = NARAROUTER_VISION if provider == "nararouter" else OPENAI_VISION
            rows = [{"id": f"{provider}:{mid}", "model": mid, "label": mid, "provider": provider,
                     "vision": True, "free": mid.endswith("-free")} for mid in allow if mid in listed]
            ttl = 30.0
        except Exception:
            # No speculative options when the authenticated catalog cannot be read.
            pass
        _CACHE[cache_key] = (time.monotonic(), ttl, rows)
        return [dict(row) for row in rows]


def groups(force: bool = False) -> dict:
    from . import llm
    return {"local": [{"id": "local:" + mid, "model": mid, "label": mid, "provider": "local",
                       "vision": None, "free": True} for mid in llm.list_local_models(force)],
            "nararouter": cloud_models("nararouter", force), "openai": cloud_models("openai", force)}


def choices(force: bool = False) -> list[dict]:
    return [row for rows in groups(force).values() for row in rows]


def validate(value: str) -> str:
    from . import llm
    provider, mid = split_model(value)
    if provider != "local" and not endpoint(provider)[1]:
        raise llm.LLMError(f"No AI key for {provider}: set {key_setting(provider)} in mirsal/.env and restart.")
    qualified = provider + ":" + mid
    if qualified not in {row["id"] for row in choices()}:
        raise llm.LLMError("That model is not available in the model catalog; refresh the model list and choose a listed model")
    return qualified


def supports_images(provider: str, mid: str) -> bool:
    # Local models remain server-selected; local capability discovery is not standardized.
    if provider == "local":
        return True
    return mid in (NARAROUTER_VISION if provider == "nararouter" else OPENAI_VISION)
