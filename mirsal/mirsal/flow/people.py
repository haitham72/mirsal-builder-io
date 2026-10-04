"""Account requests on the office LAN (docs/api.md, Office accounts on the LAN): a sign-up waiting for approval, a forgotten password, a request for more
credits. Each is one record in `out/account_requests.json` (git-ignored: emails), decided by Haitham in Settings > People or with a button in the
Telegram bot (`services/admin_bot.py`); every decision says who made it and when. Nothing is decided automatically: no credit refills on its own,
no password is reset without Haitham."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from ..runtime import atomic

KINDS = ("signup", "password", "credits")
STATES = ("waiting", "approved", "rejected", "ignored")
_LOCK = threading.RLock()


def _path(out: Path) -> Path:
    return Path(out) / "account_requests.json"


def _read(out: Path) -> list:
    try:
        return json.loads(atomic.read_text(_path(out))).get("requests", [])
    except (OSError, ValueError):
        return []


def _write(out: Path, rows: list) -> None:
    Path(out).mkdir(parents=True, exist_ok=True)
    atomic.write_text(_path(out), json.dumps({"requests": rows}, indent=1, ensure_ascii=False))


def add(out: Path, kind: str, user: dict, reason: str = "") -> dict:
    """A new request (one waiting request of a kind per person: asking twice returns the waiting one)."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    with _LOCK:
        rows = _read(out)
        same = next((r for r in rows if r["kind"] == kind and r["user"] == user["id"] and r["status"] == "waiting"), None)
        if same:
            return same
        r = {"id": f"R{max([int(x['id'][1:]) for x in rows] or [0]) + 1:03d}", "kind": kind, "user": user["id"], "name": user.get("name"), "email": user.get("email"),
             "reason": str(reason or "")[:300], "status": "waiting", "at": round(time.time(), 3), "decided_by": None, "decided_at": None, "telegram_message_id": None}
        rows.append(r)
        _write(out, rows)
    _notify(out, r)
    return r


def get(out: Path, rid: str) -> dict:
    r = next((x for x in _read(out) if x["id"] == rid), None)
    if r is None:
        raise KeyError(f"no request {rid}")
    return r


def update(out: Path, rid: str, **fields) -> dict:
    with _LOCK:
        rows = _read(out)
        r = next((x for x in rows if x["id"] == rid), None)
        if r is None:
            raise KeyError(f"no request {rid}")
        r.update(fields)
        _write(out, rows)
    return r


def close(out: Path, rid: str, status: str, by: str) -> dict:
    if status not in STATES[1:]:
        raise ValueError(f"status must be one of {STATES[1:]}")
    return update(out, rid, status=status, decided_by=by, decided_at=round(time.time(), 3))


def waiting(out: Path, user: str | None = None) -> list:
    return [r for r in _read(out) if r["status"] == "waiting" and (user is None or r["user"] == user)]


def latest(out: Path, user: str, kind: str) -> dict | None:
    return next((r for r in reversed(_read(out)) if r["user"] == user and r["kind"] == kind), None)


def _notify(out: Path, r: dict) -> None:
    """Haitham's card in the Telegram bot; never stops the request."""
    try:
        from ..services import admin_bot
        admin_bot.notify_request(out, r)
    except Exception:
        pass
