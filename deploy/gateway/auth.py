"""Verifying the person: a Supabase Auth JWT (Google provider). No password code, no session table of ours.

The token is checked for signature (the project's JWKS, or the legacy HS256 secret), `iss` (the project URL + /auth/v1), `aud` and `exp`. What the engine learns is only the stable subject,
the display name and the e-mail: never the token (the gateway strips Authorization and Cookie before forwarding)."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import httpx
import jwt

JWKS_TTL = 3600


class AuthError(Exception):
    pass


@dataclass
class Identity:
    sub: str
    name: str
    email: str
    avatar: str
    provider: str
    exp: float


class Verifier:
    def __init__(self, settings, fetch=None):
        self.s = settings
        self._fetch = fetch or self._http_fetch
        self._keys: dict = {}
        self._at = 0.0
        self._lock = threading.Lock()

    @staticmethod
    def _http_fetch(url: str) -> dict:
        r = httpx.get(url, timeout=8.0)
        r.raise_for_status()
        return r.json()

    def _jwks(self, force: bool = False) -> dict:
        with self._lock:
            if force or not self._keys or time.time() - self._at > JWKS_TTL:
                data = self._fetch(self.s.jwks())
                self._keys = {k["kid"]: k for k in data.get("keys", []) if k.get("kid")}
                self._at = time.time()
            return self._keys

    def reachable(self) -> bool:
        try:
            return bool(self._jwks(force=True)) if self.s.jwks() else bool(self.s.jwt_secret)
        except Exception:
            return False

    def verify(self, token: str) -> Identity:
        if not token or token.count(".") != 2:
            raise AuthError("not a token")
        try:
            head = jwt.get_unverified_header(token)
        except jwt.PyJWTError:
            raise AuthError("not a token")
        alg = head.get("alg")
        try:
            if alg == "HS256":
                if not self.s.jwt_secret:
                    raise AuthError("HS256 tokens are not accepted here")
                key = self.s.jwt_secret
            elif alg in ("RS256", "ES256"):
                kid = head.get("kid")
                keys = self._jwks()
                if kid not in keys:
                    keys = self._jwks(force=True)                     # a rotated key: look again once
                if kid not in keys:
                    raise AuthError("unknown signing key")
                key = jwt.PyJWK(keys[kid]).key
            else:
                raise AuthError("unsupported signing algorithm")      # includes "none": an unsigned token is never accepted
            claims = jwt.decode(token, key, algorithms=[alg], audience=self.s.jwt_audience, issuer=f"{self.s.supabase_url}/auth/v1",
                                options={"require": ["exp", "sub", "iss", "aud"]}, leeway=10)
        except AuthError:
            raise
        except jwt.PyJWTError as e:
            raise AuthError(type(e).__name__)
        meta = claims.get("user_metadata") or {}
        app = claims.get("app_metadata") or {}
        provider = str(app.get("provider") or "")
        if self.s.only_google and provider != "google":
            raise AuthError("only the Google sign-in is accepted")
        name = str(meta.get("full_name") or meta.get("name") or "").strip()
        return Identity(sub=str(claims["sub"]), name=name, email=str(claims.get("email") or ""), avatar=str(meta.get("avatar_url") or meta.get("picture") or ""),
                        provider=provider, exp=float(claims["exp"]))
