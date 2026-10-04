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

Hosted (branch `deployment`, deploy/gateway): the engine listens on loopback only and a FastAPI gateway in front of it verifies the person (Supabase / Google JWT) and forwards the request with
`X-Mirsal-Gateway-Secret` (MIRSAL_GATEWAY_SECRET, at least 32 characters, compared in constant time), `X-Mirsal-Subject` (the identity provider's stable id) and `X-Mirsal-Name`. A request that carries the right
secret AND comes from a loopback address is that person, a `member` created on first sight (`UserStore.ensure_external`) with `external` = the subject; a wrong or missing secret is an ordinary request (it gets
no identity from these headers). Setting the secret also means authentication is on (`any()`), so the open sandbox can never be reached by accident on a hosted box.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from pathlib import Path

ROLES = ("owner", "admin", "member")
LOOPBACK = ("127.0.0.1", "::1", "localhost")
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
        from . import atomic
        atomic.write_text(self.path, json.dumps({"users": users}, indent=1))

    @staticmethod
    def public(u: dict) -> dict:
        return {k: u[k] for k in ("id", "name", "role", "can_spend", "created", "disabled", "email", "status", "must_change_password", "credits_left",
                                  "credits_spent", "last_seen") if k in u}

    def any(self) -> bool:
        """Is authentication on? (any account exists, disabled or not, or the env token is set). Disabling the only user must never open the server:
        to go back to the open sandbox, delete out/users.json on purpose."""
        return bool(os.environ.get("MIRSAL_API_TOKEN")) or bool(os.environ.get("MIRSAL_GATEWAY_SECRET")) or bool(self._read())

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

    SUBJECT = re.compile(r"^[A-Za-z0-9_.:@|-]{6,128}$")

    def ensure_external(self, subject: str, name: str = "", can_spend: bool = True) -> dict:
        """The member that belongs to an identity provider's subject (a Google sub through Supabase): found, or created on first sight. The name follows the provider's profile
        until a person renames the account here (a profile name is never trusted as anything but text)."""
        if not self.SUBJECT.match(str(subject or "")):
            raise UserError("a valid subject is required")
        name = " ".join(str(name or "").split())[:60] or "New user"
        with _LOCK:
            users = self._read()
            u = next((x for x in users if x.get("external") == subject), None)
            if u is None:
                n = max([int(x["id"][1:]) for x in users if str(x.get("id", "")).startswith("U") and x["id"][1:].isdigit()] or [0]) + 1
                u = {"id": f"U{n:03d}", "name": name, "role": "member", "can_spend": bool(can_spend), "token_sha256": "", "created": round(time.time(), 3),
                     "disabled": False, "external": subject}
                users.append(u)
                self._write(users)
        return self.public(u)

    def authenticate_gateway(self, secret: str | None, subject: str | None, name: str | None, client_ip: str) -> dict | None:
        """A person the gateway vouches for (see the module doc), or None. Needs the configured secret, a loopback peer and a well-formed subject; a disabled account is refused."""
        want = os.environ.get("MIRSAL_GATEWAY_SECRET", "")
        if len(want) < 32 or not secret or not hmac.compare_digest(_digest(secret), _digest(want)):
            return None
        if client_ip not in ("127.0.0.1", "::1", "localhost"):
            return None
        try:
            u = self.ensure_external(subject or "", name or "")
        except UserError:
            return None
        return None if u.get("disabled") else dict(u, via="gateway")

    # ---------- office accounts on the LAN (docs/api.md, Office accounts on the LAN): email + password, approval, sessions ----------
    DOMAIN = os.environ.get("MIRSAL_EMAIL_DOMAIN", "nadi.ae")

    def _norm_email(self, email: str) -> str:
        e = str(email or "").strip().lower()
        if not re.fullmatch(r"[a-z0-9._%+-]{1,64}@[a-z0-9.-]{1,190}", e):
            raise UserError("a valid email is required")
        if self.DOMAIN and not e.endswith("@" + self.DOMAIN):
            raise UserError(f"only @{self.DOMAIN} accounts can join")
        return e

    @staticmethod
    def hash_password(pw: str) -> str:
        salt = secrets.token_bytes(16)
        n, r, p = 2 ** 14, 8, 1
        h = hashlib.scrypt(str(pw).encode(), salt=salt, n=n, r=r, p=p, dklen=32)
        return f"scrypt${n}${r}${p}${salt.hex()}${h.hex()}"

    @staticmethod
    def check_password(pw: str, stored: str) -> bool:
        try:
            _, n, r, p, salt, h = str(stored).split("$")
            got = hashlib.scrypt(str(pw).encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=32)
            return hmac.compare_digest(got.hex(), h)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _check_new_password(pw: str) -> None:
        if len(str(pw or "")) < 8:
            raise UserError("a password of at least 8 characters is required")

    @staticmethod
    def new_password() -> str:
        return secrets.token_urlsafe(12)[:16]

    def by_email(self, email: str) -> dict | None:
        e = str(email or "").strip().lower()
        return next((u for u in self._read() if u.get("email") == e), None)

    def _next_uid(self, users: list) -> str:
        return f"U{max([int(u['id'][1:]) for u in users if str(u.get('id', '')).startswith('U') and u['id'][1:].isdigit()] or [0]) + 1:03d}"

    def signup(self, email: str, name: str, password: str) -> dict:
        """Self sign-up in onboarding: the account waits for Haitham (status `pending`) and can do nothing until approved."""
        e = self._norm_email(email)
        name = " ".join(str(name or "").split())[:60]
        if not name:
            raise UserError("a name is required")
        self._check_new_password(password)
        with _LOCK:
            users = self._read()
            if any(u.get("email") == e for u in users):
                raise UserError("this email already has an account: sign in, or use Forgot password", 409)
            u = {"id": self._next_uid(users), "name": name, "email": e, "role": "member", "status": "pending", "can_spend": True, "token_sha256": "",
                 "password_hash": self.hash_password(password), "must_change_password": False, "credits_left": 0, "credits_spent": 0,
                 "created": round(time.time(), 3), "disabled": True}
            users.append(u)
            self._write(users)
        return self.public(u)

    def add_people(self, emails, credits: int = 10) -> list[dict]:
        """Haitham's 'Add people': each email gets an active account and a generated password, returned ONCE (to send by hand; there is no email)."""
        made = []
        with _LOCK:
            users = self._read()
            for raw in emails:
                e = self._norm_email(raw)
                if any(u.get("email") == e for u in users):
                    raise UserError(f"{e} already has an account", 409)
                pw = self.new_password()
                u = {"id": self._next_uid(users), "name": e.split("@")[0].replace(".", " ").title(), "email": e, "role": "member", "status": "active", "can_spend": True,
                     "token_sha256": "", "password_hash": self.hash_password(pw), "must_change_password": True, "credits_left": int(credits), "credits_spent": 0,
                     "created": round(time.time(), 3), "disabled": False}
                users.append(u)
                made.append({**self.public(u), "password": pw})
            self._write(users)
        return made

    def decide(self, uid: str, action: str, *, role: str | None = None, credits: int | None = None, name: str | None = None, email: str | None = None,
               start_credits: int = 10) -> tuple[dict, str | None]:
        """approve | reject | disable | enable | role | password | edit | credits -> (the account, a new password when one was made). The owner cannot be demoted or disabled."""
        new_pw = None
        with _LOCK:
            users = self._read()
            u = next((x for x in users if x["id"] == uid), None)
            if not u:
                raise UserError(f"no user {uid}", 404)
            if u.get("role") == "owner" and action in ("reject", "disable", "role"):
                raise UserError("the owner account cannot be changed this way", 409)
            if action == "approve":
                if u.get("status") != "active":
                    u["credits_left"] = int(u.get("credits_left") or 0) or int(start_credits)
                u.update(status="active", disabled=False)
            elif action == "reject":
                u.update(status="rejected", disabled=True)
            elif action == "disable":
                u.update(status="disabled", disabled=True)
            elif action == "enable":
                u.update(status="active", disabled=False)
            elif action == "role":
                if role not in ("admin", "member"):
                    raise UserError("role must be admin or member")
                u["role"] = role
            elif action == "password":
                new_pw = self.new_password()
                u.update(password_hash=self.hash_password(new_pw), must_change_password=True)
            elif action == "edit":
                if name is not None:
                    n = " ".join(str(name).split())[:60]
                    if not n:
                        raise UserError("a name is required")
                    u["name"] = n
                if email is not None:
                    e = self._norm_email(email)
                    if any(x.get("email") == e and x["id"] != uid for x in users):
                        raise UserError(f"{e} already has an account", 409)
                    u["email"] = e
            elif action == "credits":
                if credits is None or int(credits) < 0 or int(credits) > 10000:
                    raise UserError("credits must be 0-10000")
                u["credits_left"] = int(u.get("credits_left") or 0) + int(credits)
            else:
                raise UserError(f"unknown action {action}")
            self._write(users)
        return self.public(u), new_pw

    def change_password(self, uid: str, old: str, new: str) -> dict:
        self._check_new_password(new)
        with _LOCK:
            users = self._read()
            u = next((x for x in users if x["id"] == uid), None)
            if not u or not self.check_password(old, u.get("password_hash", "")):
                raise UserError("the current password is wrong", 403)
            u.update(password_hash=self.hash_password(new), must_change_password=False)
            self._write(users)
        return self.public(u)

    def charge(self, uid: str, credits: float) -> dict | None:
        """Credits per person (docs/api.md, Office accounts on the LAN): `credits` > 0 spends, < 0 gives back. The owner `local` has no balance."""
        if uid == "local":
            return None
        with _LOCK:
            users = self._read()
            u = next((x for x in users if x["id"] == uid), None)
            if not u or "credits_left" not in u:
                return None
            u["credits_left"] = round(float(u.get("credits_left") or 0) - float(credits), 3)
            u["credits_spent"] = round(float(u.get("credits_spent") or 0) + float(credits), 3)
            self._write(users)
        return self.public(u)

    # sessions: a random cookie value, kept only as a digest with its expiry (out/auth_sessions.json, git-ignored)
    SESSION_HOURS = 8

    def _sessions_path(self) -> Path:
        return self.path.parent / "auth_sessions.json"

    def _sessions(self) -> dict:
        try:
            return json.loads(self._sessions_path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_sessions(self, ss: dict) -> None:
        from . import atomic
        now = time.time()
        atomic.write_text(self._sessions_path(), json.dumps({k: v for k, v in ss.items() if v.get("expires", 0) > now}))

    def login(self, email: str, password: str) -> tuple[dict, str]:
        """-> (the account, the session cookie value). The same words for a wrong email and a wrong password, so emails cannot be probed."""
        u = self.by_email(email)
        bad = UserError("email or password is wrong", 401)
        if not u or not u.get("password_hash"):
            self.check_password(password, "scrypt$16384$8$1$" + "00" * 16 + "$" + "00" * 32)      # the same work either way
            raise bad
        if not self.check_password(password, u["password_hash"]):
            raise bad
        if u.get("status") == "rejected":
            raise UserError("this account was not approved", 403)
        if u.get("status") == "disabled":
            raise UserError("this account is disabled", 403)
        token = secrets.token_urlsafe(32)
        with _LOCK:
            ss = self._sessions()
            ss[_digest(token)] = {"uid": u["id"], "expires": time.time() + self.SESSION_HOURS * 3600}
            self._save_sessions(ss)
        return self.public(u), token

    def logout(self, token: str) -> None:
        with _LOCK:
            ss = self._sessions()
            ss.pop(_digest(token or ""), None)
            self._save_sessions(ss)

    def by_session(self, token: str | None) -> dict | None:
        """The account behind a session cookie (rolling: each use moves the expiry), or None. A pending account is returned so the page can say
        'Waiting for approval'; the server refuses it everything else."""
        if not token:
            return None
        with _LOCK:
            ss = self._sessions()
            rec = ss.get(_digest(token))
            if not rec or rec.get("expires", 0) < time.time():
                return None
            u = next((x for x in self._read() if x["id"] == rec["uid"]), None)
            if not u or u.get("status") in ("rejected", "disabled"):
                return None
            rec["expires"] = time.time() + self.SESSION_HOURS * 3600
            self._save_sessions(ss)
        return self.public(u)

    def authenticate(self, header: str | None, same_origin_page: bool, session: str | None = None, client_ip: str = "127.0.0.1", lan: bool = False) -> dict | None:
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
        if session:
            u = self.by_session(session)
            if u:
                return dict(u, via="session")
        if lan and client_ip not in LOOPBACK:            # on the office LAN another machine is never the owner by loading the page: it signs in
            return None
        if same_origin_page:
            return dict(LOCAL, via="page")
        return None if self.any() else dict(LOCAL, via="open")
