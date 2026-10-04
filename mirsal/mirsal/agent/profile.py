"""What the chat learns about a person's taste, across chats (`out/profile/<user>.json`).

The signals are the person's own decisions: a style they asked a change toward ("more cartoonish"), a size ("bigger"), a colour, a subject they liked. A taste is only applied to a later request
after TWO consistent signals, an explicit style in the sentence always wins, and the plan card says what it assumed (with the way to undo it). Plain counters in a file: a person can read it, delete
it, and see exactly why the chat chose a style ("you asked for cartoonish twice")."""
from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path

MIN_SIGNALS = 2
_LOCK = threading.RLock()


class Profile:
    def __init__(self, out: Path, user: str = "local"):
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", str(user) or "local")[:40] or "local"
        self.path = Path(out) / "profile" / f"{safe}.json"

    def load(self) -> dict:
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            d = {}
        for k in ("style", "size", "colour", "liked"):
            d.setdefault(k, {})
        d.setdefault("log", [])
        return d

    def save(self, d: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(f".{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def vote(self, kind: str, key: str, why: str = "") -> dict:
        """Count one signal (`kind`: style | size | colour | liked)."""
        if kind not in ("style", "size", "colour", "liked") or not key:
            return self.load()
        with _LOCK:
            d = self.load()
            d[kind][key] = int(d[kind].get(key, 0)) + 1
            d["log"] = (d["log"] + [{"ts": round(time.time(), 1), "kind": kind, "key": key, "why": why[:120]}])[-60:]
            self.save(d)
            return d

    def vote_delta(self, delta: dict, said: str = "") -> None:
        if delta.get("style_id"):
            self.vote("style", delta["style_id"], said)
        if delta.get("size"):
            self.vote("size", delta["size"], said)
        if delta.get("colour"):
            self.vote("colour", delta["colour"], said)

    def top(self, kind: str) -> tuple[str, int] | None:
        """The most voted value of a kind and its count, only when it is ahead of every other value (a split taste is no taste)."""
        d = self.load()[kind]
        if not d:
            return None
        ranked = sorted(d.items(), key=lambda kv: -kv[1])
        if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
            return None
        return ranked[0]

    def defaults(self) -> dict:
        """The tastes strong enough to apply: {"style_id": (id, n) | None, "size": (value, n) | None}."""
        out = {}
        for kind, name in (("style", "style_id"), ("size", "size")):
            t = self.top(kind)
            out[name] = t if t and t[1] >= MIN_SIGNALS else None
        return out

    def name(self) -> str | None:
        """What the person told the chat to call them ("my name is Haitham"), or None."""
        return self.load().get("name") or None

    def set_name(self, name: str) -> None:
        with _LOCK:
            d = self.load()
            d["name"] = str(name or "").strip()[:60] or None
            self.save(d)

    def forget(self) -> None:
        try:
            self.path.unlink()
        except OSError:
            pass
