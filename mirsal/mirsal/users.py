"""Users and tokens (Phase 5C): who is calling, and what they may see.

File first, like everything else: `out/users.json` holds `{users: [{id, name, role, can_spend, token_sha256, created, disabled}]}`; Postgres mirrors it (`users` table, `db import`).
Tokens are random, shown ONCE at creation, and stored only as a SHA-256 digest; they are compared in constant time. There is always an implicit owner, `local`: the Studio's own page
(same-origin) and a caller holding `MIRSAL_API_TOKEN` are `local`, and `local` sees everything.

Rules the server applies (console/server.py):
- no users and no MIRSAL_API_TOKEN: the local sandbox is open exactly as before (everyone is `local`);
- as soon as one account exists (disabled or not; or the env token is set) every caller that is not the Studio's own page must present a valid token (401 otherwise);
- a `member` sees only what they own (their chats, their generations and the files, jobs and events of those); an `owner` sees everything;
- members cannot spend: live generation and animation need `can_spend`, because they would spend the owner's Higgsfield credits;
- library, packs, projects, Telegram, watch folders, usage and the user list are owner-only (per-user packs are not built).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path

ROLES = ("owner", "member")
LOCAL = {"id": "local", "name": "local", "role": "owner", "can_spend": True, "disabled": False}
_LOCK = threading.RLock()


class UserError(Exception):
    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code


def _digest(token: str) -> str:
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


class UserStore:
    def __init__(self, out: Path):
        self.path = Path(out) / "users.json"

    def _read(self) -> list:
        try:
            return json.loads(self.path.read_text(encoding="utf-8")).get("users", [])
        except (OSError, ValueError):
            return []

    def _write(self, users: list) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps({"users": users}, indent=1), encoding="utf-8")
        for attempt in range(40):               # Windows: os.replace fails while anything has the target open
            try:
                os.replace(tmp, self.path)
                return
            except PermissionError:
                if attempt == 39:
                    raise
                time.sleep(0.05)

    @staticmethod
    def public(u: dict) -> dict:
        return {k: u[k] for k in ("id", "name", "role", "can_spend", "created", "disabled") if k in u}

    def any(self) -> bool:
        """Is authentication on? (any account exists, disabled or not, or the env token is set). Disabling the only user must never open the server:
        to go back to the open sandbox, delete out/users.json on purpose."""
        return bool(os.environ.get("MIRSAL_API_TOKEN")) or bool(self._read())

    def list(self) -> list:
        return [self.public(u) for u in self._read()]

    def create(self, name: str, role: str = "member", can_spend: bool = False) -> tuple[dict, str]:
        name = str(name or "").strip()
        if not name or len(name) > 60:
            raise UserError("a name of 1-60 characters is required")
        if role not in ROLES:
            raise UserError(f"role must be one of {ROLES}")
        with _LOCK:
            users = self._read()
            n = max([int(u["id"][1:]) for u in users if str(u.get("id", "")).startswith("U") and u["id"][1:].isdigit()] or [0]) + 1
            token = "mk_" + secrets.token_hex(24)
            u = {"id": f"U{n:03d}", "name": name, "role": role, "can_spend": bool(can_spend), "token_sha256": _digest(token),
                 "created": round(time.time(), 3), "disabled": False}
            users.append(u)
            self._write(users)
        return self.public(u), token

    def find_by_token(self, token: str) -> dict | None:
        if not token:
            return None
        want = _digest(token)
        found = None
        for u in self._read():                      # compare every digest in constant time (no early exit on the first match)
            if hmac.compare_digest(u.get("token_sha256", ""), want) and not u.get("disabled"):
                found = u
        return self.public(found) if found else None

    def get(self, uid: str) -> dict | None:
        if uid == "local":
            return dict(LOCAL)
        return next((self.public(u) for u in self._read() if u["id"] == uid), None)

    def set_disabled(self, uid: str, disabled: bool = True) -> dict:
        with _LOCK:
            users = self._read()
            u = next((x for x in users if x["id"] == uid), None)
            if not u:
                raise UserError(f"no user {uid}", 404)
            u["disabled"] = bool(disabled)
            self._write(users)
        return self.public(u)

    def rotate(self, uid: str) -> tuple[dict, str]:
        with _LOCK:
            users = self._read()
            u = next((x for x in users if x["id"] == uid), None)
            if not u:
                raise UserError(f"no user {uid}", 404)
            token = "mk_" + secrets.token_hex(24)
            u["token_sha256"] = _digest(token)
            self._write(users)
        return self.public(u), token

    def update(self, uid: str, can_spend: bool | None = None, role: str | None = None, name: str | None = None) -> dict:
        with _LOCK:
            users = self._read()
            u = next((x for x in users if x["id"] == uid), None)
            if not u:
                raise UserError(f"no user {uid}", 404)
            if role is not None:
                if role not in ROLES:
                    raise UserError(f"role must be one of {ROLES}")
                u["role"] = role
            if can_spend is not None:
                u["can_spend"] = bool(can_spend)
            if name is not None:
                if not str(name).strip() or len(str(name)) > 60:
                    raise UserError("a name of 1-60 characters is required")
                u["name"] = str(name).strip()
            self._write(users)
        return self.public(u)

    def authenticate(self, header: str | None, same_origin_page: bool) -> dict | None:
        """The caller, with `via` saying how: `token` (a user token, or MIRSAL_API_TOKEN = the owner `local`), `page` (the Studio's own page: a browser
        marks its fetches same-origin, and a user token is checked FIRST so a client cannot widen itself by also sending that header), `open` (no
        authentication is configured: the local sandbox as before). None = refused (401)."""
        tok = header[7:].strip() if header and header.startswith("Bearer ") else ""
        env = os.environ.get("MIRSAL_API_TOKEN", "")
        if tok:
            if env and hmac.compare_digest(_digest(tok), _digest(env)):
                return dict(LOCAL, via="token")
            u = self.find_by_token(tok)
            if u:
                return dict(u, via="token")
        if same_origin_page:
            return dict(LOCAL, via="page")
        return None if self.any() else dict(LOCAL, via="open")
