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

FACT_KEYS = ("name", "place", "age", "likes", "dislikes", "extra")
LISTS = ("likes", "dislikes")
MAX_TEXT, MAX_ITEMS, MAX_EXTRA = 60, 20, 8
_CTRL = re.compile(r"[\x00-\x1f\x7f<>{}\[\]`\\]")


def _text(v, limit: int = MAX_TEXT) -> str | None:
    s = " ".join(_CTRL.sub(" ", str(v)).split()) if isinstance(v, (str, int, float)) and not isinstance(v, bool) else ""
    return s if 0 < len(s) <= limit else None


def validate_facts(d) -> dict:
    """The one gate before anything reaches the profile, whether the rules or a model proposed it: only FACT_KEYS, short plain text, an age of 3..120, at most a few
    extras with short snake_case keys. Anything else (unknown keys, long values, markup, nested objects) is dropped, never stored."""
    if not isinstance(d, dict):
        return {}
    out = {}
    for k in ("name", "place"):
        v = _text(d.get(k), 40 if k == "name" else MAX_TEXT)
        if v:
            out[k] = v
    age = d.get("age")
    if isinstance(age, str) and age.strip().isdigit():
        age = int(age.strip())
    if isinstance(age, int) and not isinstance(age, bool) and 3 <= age <= 120:
        out["age"] = age
    for k in LISTS:
        raw = d.get(k)
        items = [raw] if isinstance(raw, str) else raw if isinstance(raw, list) else []
        keep = list(dict.fromkeys(x for x in (_text(i) for i in items[:MAX_ITEMS]) if x))
        if keep:
            out[k] = keep
    ex = d.get("extra")
    if isinstance(ex, dict):
        keep = {}
        for k, v in list(ex.items())[:MAX_EXTRA]:
            key, val = re.sub(r"[^a-z0-9_]", "_", str(k).lower())[:24].strip("_"), _text(v)
            if key and val and key not in FACT_KEYS:
                keep[key] = val
        if keep:
            out["extra"] = keep
    return out


def profile_said(saved: dict) -> str:
    """What was just saved, in words, so the person can correct it: "your name (Haitham) and that you live in Dubai"."""
    bits = []
    if "name" in saved:
        bits.append(f"your name ({saved['name']})")
    if "place" in saved:
        bits.append(f"that you live in {saved['place']}")
    if "age" in saved:
        bits.append(f"that you are {saved['age']}")
    if saved.get("likes"):
        bits.append(f"that you like {', '.join(saved['likes'])}")
    if saved.get("dislikes"):
        bits.append(f"that you don't like {', '.join(saved['dislikes'])}")
    bits += [f"your {k.replace('_', ' ')}: {v}" for k, v in (saved.get("extra") or {}).items()]
    return ", ".join(bits[:-1]) + (" and " if len(bits) > 1 else "") + bits[-1] if bits else "nothing"


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

    # ---- what the person told the chat about themselves (FACTS): one fixed schema, every value validated before it is written, timestamped, last write wins ----
    def facts(self) -> dict:
        """{name, place, age, likes, dislikes, extra}, plain values (None / [] / {} when never said)."""
        d = self.load()
        f = dict(d.get("facts") or {})
        if d.get("name") and "name" not in f:                       # written by the first version (a bare "name" key)
            f["name"] = {"value": d["name"]}
        return {k: (f.get(k) or {}).get("value", [] if k in LISTS else {} if k == "extra" else None) for k in FACT_KEYS}

    def name(self) -> str | None:
        return self.facts()["name"]

    def set_facts(self, new: dict, said: str = "") -> dict:
        """Write what `validate_facts` keeps of `new`: a scalar replaces the old value, a like / dislike is added (and taken out of the other list), an extra key replaces its own value.
        Returns exactly what was saved ({} when nothing passed the validator), so the reply can say it and the person can correct it."""
        clean = validate_facts(new)
        if not clean:
            return {}
        with _LOCK:
            d = self.load()
            f = d.setdefault("facts", {})
            now = round(time.time(), 3)
            for k, v in clean.items():
                if k in LISTS:
                    other = "dislikes" if k == "likes" else "likes"
                    have = [x for x in (f.get(k) or {}).get("value", []) if x.lower() not in {y.lower() for y in v}]
                    f[k] = {"value": (have + v)[-MAX_ITEMS:], "at": now}
                    if f.get(other):
                        f[other] = {"value": [x for x in f[other]["value"] if x.lower() not in {y.lower() for y in v}], "at": now}
                elif k == "extra":
                    f["extra"] = {"value": {**(f.get("extra") or {}).get("value", {}), **v}, "at": now}
                else:
                    f[k] = {"value": v, "at": now}
            d["log"] = (d["log"] + [{"ts": now, "kind": "fact", "key": ",".join(clean), "why": said[:120]}])[-60:]
            self.save(d)
        try:                                       # the Postgres copy (migration 011); the file stays the record and wins when the database is down
            from ..store import sync
            sync.sync_profile(self.path.parent.parent, self.path.stem, d["facts"])
        except Exception:
            pass
        return clean

    def set_name(self, name: str) -> dict:
        return self.set_facts({"name": name})

    def facts_text(self) -> str:
        """The facts as one line for a model ("The person: name Haitham; lives in Dubai; likes camels"), '' when nothing is known."""
        f = self.facts()
        bits = ([f"name {f['name']}"] if f["name"] else []) + ([f"lives in {f['place']}"] if f["place"] else []) + ([f"age {f['age']}"] if f["age"] else []) \
            + ([f"likes {', '.join(f['likes'])}"] if f["likes"] else []) + ([f"dislikes {', '.join(f['dislikes'])}"] if f["dislikes"] else []) \
            + [f"{k} {v}" for k, v in f["extra"].items()]
        return ("The person: " + "; ".join(bits) + ".") if bits else ""

    def forget(self) -> None:
        try:
            self.path.unlink()
        except OSError:
            pass
