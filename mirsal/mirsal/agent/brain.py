"""The model behind the agent: a few SMALL, schema-checked calls. The rules decide first (resolver.py); the model only classifies what the
rules are unsure about, picks a sticker the words do not name, answers a question from the structured state, and writes the narrative
summary. Every call goes through `llm.complete` (OpenAI or the local LM Studio), is logged to out/model_calls.jsonl, gets one repair
round, and on failure returns None so the graph falls back to the deterministic answer. The model never generates media and never
judges pixels."""
from __future__ import annotations

import json
import os
import re
import time

from .. import llm

INTENTS = ("NEW", "ANOTHER", "EDIT_STICKERS", "ANIMATE", "FEEDBACK", "REVIEW", "ASK", "CHANGE_SETTINGS", "SEARCH", "SMALLTALK", "AMBIGUOUS")

CLASSIFY_SYSTEM = f"""You route one chat message in a sticker studio to intents. Reply with ONE JSON object only:
{{"intents": [..], "confidence": 0.0-1.0}}
Intents: {", ".join(INTENTS)}.
NEW: a request for a new set ("make me falcon stickers", "teddy bear with a book"). ANOTHER: more of the same subject. EDIT_STICKERS: change specific stickers
("make number 3 happier"). ANIMATE: make them move. FEEDBACK: likes/dislikes ("I like 2 but not 3"). REVIEW: approve or reject ("approve all but 5").
ASK: a question about what exists ("which one is the shocked banana?"). CHANGE_SETTINGS: grid, style, animation, asking before spending. SEARCH: find an old
sticker. SMALLTALK: greetings and thanks. AMBIGUOUS: you cannot tell. A message can carry two intents ("I like 2 but make 5 happier" = FEEDBACK + EDIT_STICKERS)."""

PICK_SYSTEM = """You map a phrase to sticker numbers. You get the numbered stickers of one batch and the user's phrase. Reply with ONE JSON object only:
{"numbers": [..], "confidence": 0.0-1.0}. Use only numbers from the list. If the phrase names none of them, return an empty list."""

ANSWER_SYSTEM = """You answer a question about the user's sticker batches, using ONLY the facts you are given. Be short and warm (one or two sentences).
Always quote ids as G012/S3. If the facts do not answer it, say so plainly. Never invent stickers."""

SUMMARY_SYSTEM = """You compress the older turns of a sticker chat into 2-4 short sentences: what the user asked for, what they liked and rejected, what they
want next. Keep every generation and sticker id (G012, G012/S3) exactly. Do not invent anything."""


def target() -> dict:
    """Which model runs the agent: MIRSAL_AGENT_PROVIDER local|openai|auto. Auto prefers the local model (free) when it answers."""
    llm._load_dotenv()
    want = os.environ.get("MIRSAL_AGENT_PROVIDER", "auto").lower()
    if want == "auto":
        want = "local" if llm.local_reachable() else ("openai" if os.environ.get(llm.KEY_VAR) else "none")
    model = os.environ.get("MIRSAL_AGENT_MODEL") or (llm.local_model() if want == "local" else os.environ.get("MIRSAL_LLM_MODEL", llm.DEFAULT_MODEL))
    return {"provider": want, "model": model}


def _first_json(text: str):
    from ..vision.judge import _first_json as fj
    return fj(text)


class Brain:
    def __init__(self, complete=None, out=None):
        """`complete(system, user, **kw) -> (text, meta)`. Tests pass a fake; production uses llm.complete on `target()`."""
        self._complete = complete
        self.out = out
        self.calls = 0

    @property
    def available(self) -> bool:
        return self._complete is not None or target()["provider"] != "none"

    def _ask(self, kind: str, system: str, user: str, max_tokens: int = 400):
        t = target()
        t0 = time.perf_counter()
        try:
            if self._complete is not None:
                text, meta = self._complete(system, user)
            else:
                text, meta = llm.complete(system, user, temperature=0, max_tokens=max_tokens, timeout=45,
                                          provider_=t["provider"], model_=t["model"])
        except llm.LLMError:
            if self.out is not None:
                from .. import model_calls
                model_calls.append(self.out, kind, t["provider"], t["model"], status="ERROR", latency_ms=int((time.perf_counter() - t0) * 1000),
                                   prompt_version="agent_v1")
            return None
        self.calls += 1
        if self.out is not None and self._complete is None:
            from .. import model_calls
            model_calls.append(self.out, kind, meta.get("provider", t["provider"]), meta.get("model", t["model"]), status="OK",
                               latency_ms=meta.get("ms"), tokens_in=meta.get("tokens_in"), tokens_out=meta.get("tokens_out"), prompt_version="agent_v1")
        return text

    def _json(self, kind: str, system: str, user: str):
        text = self._ask(kind, system, user)
        if text is None:
            return None
        try:
            return _first_json(text)
        except ValueError as first:                                  # one repair round
            text = self._ask(kind, system, f"{user}\n\nYour previous answer was not valid JSON ({first}). Reply with the JSON object only.")
            try:
                return _first_json(text) if text else None
            except ValueError:
                return None

    # ---- the four jobs ----------------------------------------------------------------------------------------------------------
    def classify(self, text: str, summary: str) -> list | None:
        d = self._json("LLM_INTENT", CLASSIFY_SYSTEM, f"What this chat has so far:\n{summary}\n\nMessage: {text}")
        if not isinstance(d, dict):
            return None
        got = [str(i).upper() for i in (d.get("intents") or []) if str(i).upper() in INTENTS]
        return got or None

    def pick_stickers(self, phrase: str, stickers: list) -> list | None:
        listing = "\n".join(f"{s['index']}: {s.get('key', '')} {''.join(s.get('emoji') or []) if isinstance(s.get('emoji'), list) else s.get('emoji') or ''}"
                            for s in stickers)
        d = self._json("LLM_RESOLVE", PICK_SYSTEM, f"Stickers:\n{listing}\n\nPhrase: {phrase}")
        if not isinstance(d, dict):
            return None
        valid = {s["index"] for s in stickers}
        nums = [int(n) for n in (d.get("numbers") or []) if str(n).isdigit() and int(n) in valid]
        return nums or None

    def answer(self, question: str, facts: str) -> str | None:
        text = self._ask("LLM_ANSWER", ANSWER_SYSTEM, f"Facts:\n{facts}\n\nQuestion: {question}", 300)
        return re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip() or None

    def summarise(self, digest: str, previous: str) -> str | None:
        text = self._ask("LLM_SUMMARY", SUMMARY_SYSTEM, f"Earlier summary: {previous or '(none)'}\n\nNew turns:\n{digest}", 300)
        return re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip() or None
