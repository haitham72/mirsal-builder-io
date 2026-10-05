"""In-app notifications (docs/agent-and-chat.md "Support"): what reaches a person when an admin answers or resolves their issue.

One file per person, `out/notifications/<user>.json` (newest last), mirrored to Postgres (migration 011). Every notification carries the EVENT KEY that
caused it (`reply:T012:3`, `resolved:T012:2`): adding the same key again is a no-op, so a retried request or a replayed step never notifies twice.
A person reads only their own file; nothing here decides who may see what (the route does)."""
from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path

from ..runtime import atomic

_LOCK = threading.RLock()
KINDS = ("reply", "resolved", "update")      # update: a job the person asked about in Help has finished (support.check_watches)
KEEP = 200                                  # the newest 200 per person


def _path(out: Path, user: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(user or "")) or "_"
    return Path(out) / "notifications" / f"{safe}.json"


def _read(out: Path, user: str) -> list[dict]:
    p = _path(out, user)
    try:
        rows = json.loads(atomic.read_text(p)) if p.is_file() else []
    except (OSError, ValueError):
        rows = []
    return [r for r in rows if isinstance(r, dict) and r.get("key")]


def _write(out: Path, user: str, rows: list[dict]) -> None:
    p = _path(out, user)
    p.parent.mkdir(parents=True, exist_ok=True)
    atomic.write_text(p, json.dumps(rows[-KEEP:], indent=1, ensure_ascii=False))


def add(out: Path, user: str, key: str, kind: str, text: str, *, ticket: str | None = None, conversation: str | None = None) -> dict:
    """One notification for `user`, once per `key`: returns the stored one (the earlier one when the key was seen before)."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    if not user or not key:
        raise ValueError("a notification needs a person and an event key")
    with _LOCK:
        rows = _read(out, user)
        old = next((r for r in rows if r["key"] == key), None)
        if old:
            return old
        n = {"id": f"N{int(time.time() * 1000):x}{len(rows):02x}", "key": key, "kind": kind, "at": round(time.time(), 3), "text": str(text)[:400],
             "ticket": ticket, "conversation": conversation, "read": False}
        rows.append(n)
        _write(out, user, rows)
    _mirror(out, user, n)
    return n


def listing(out: Path, user: str, limit: int = 50) -> dict:
    rows = _read(out, user)
    return {"notifications": list(reversed(rows))[:limit], "unread": sum(1 for r in rows if not r.get("read"))}


def mark_read(out: Path, user: str, ids: list[str] | None = None, conversation: str | None = None) -> dict:
    """Mark the given ids (or every notification of one conversation, or all of them) read; returns the new listing."""
    changed = []
    with _LOCK:
        rows = _read(out, user)
        for r in rows:
            hit = (ids is None and conversation is None) or (ids is not None and r["id"] in ids) or (conversation is not None and r.get("conversation") == conversation)
            if hit and not r.get("read"):
                r["read"] = True
                changed.append(r)
        if changed:
            _write(out, user, rows)
    for r in changed:
        _mirror(out, user, r)
    return listing(out, user)


def _mirror(out: Path, user: str, n: dict) -> None:
    try:
        from ..store import sync
        sync.sync_support(out, "notification", user, n)
    except Exception:
        pass
