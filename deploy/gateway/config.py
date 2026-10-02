"""Gateway settings, from the environment only (a hosted box has no config files). Every secret is read here and nowhere else."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _list(name: str, default: str = "") -> list[str]:
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


@dataclass
class Settings:
    engine_url: str = field(default_factory=lambda: os.environ.get("MIRSAL_ENGINE_URL", "http://127.0.0.1:8789").rstrip("/"))
    gateway_secret: str = field(default_factory=lambda: os.environ.get("MIRSAL_GATEWAY_SECRET", ""))
    supabase_url: str = field(default_factory=lambda: os.environ.get("SUPABASE_URL", "").rstrip("/"))
    supabase_anon_key: str = field(default_factory=lambda: os.environ.get("SUPABASE_ANON_KEY", ""))     # public by design (the browser needs it to start a Google sign-in)
    jwt_audience: str = field(default_factory=lambda: os.environ.get("SUPABASE_JWT_AUDIENCE", "authenticated"))
    jwks_url: str = field(default_factory=lambda: os.environ.get("SUPABASE_JWKS_URL", ""))
    jwt_secret: str = field(default_factory=lambda: os.environ.get("SUPABASE_JWT_SECRET", ""))          # only for projects that still sign with HS256
    allowed_hosts: list = field(default_factory=lambda: _list("MIRSAL_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver"))
    public_origin: str = field(default_factory=lambda: os.environ.get("MIRSAL_PUBLIC_ORIGIN", "").rstrip("/"))   # https://mirsal.example.com ; empty = same host only
    rate_per_minute: int = field(default_factory=lambda: int(os.environ.get("MIRSAL_RATE_PER_MIN", "120")))
    paid_rate_per_minute: int = field(default_factory=lambda: int(os.environ.get("MIRSAL_PAID_RATE_PER_MIN", "6")))
    redis_url: str = field(default_factory=lambda: os.environ.get("MIRSAL_REDIS_URL", ""))
    cookie_name: str = "mirsal_session"
    cookie_secure: bool = field(default_factory=lambda: os.environ.get("MIRSAL_COOKIE_SECURE", "1") not in ("0", "false", "no"))
    auth_required: bool = field(default_factory=lambda: os.environ.get("MIRSAL_AUTH_REQUIRED", "1") not in ("0", "false", "no"))
    max_body: int = 40 * 1024 * 1024
    only_google: bool = field(default_factory=lambda: os.environ.get("MIRSAL_ONLY_GOOGLE", "1") not in ("0", "false", "no"))

    def jwks(self) -> str:
        return self.jwks_url or (f"{self.supabase_url}/auth/v1/.well-known/jwks.json" if self.supabase_url else "")

    def problems(self) -> list[str]:
        """What is missing for a hosted start; the gateway refuses to start with any of these (an open door by accident is worse than no site)."""
        out = []
        if len(self.gateway_secret) < 32:
            out.append("MIRSAL_GATEWAY_SECRET must be at least 32 characters (the same value in the engine's environment)")
        if self.auth_required and not (self.jwks() or self.jwt_secret):
            out.append("SUPABASE_URL (or SUPABASE_JWKS_URL / SUPABASE_JWT_SECRET) is required to verify the Google sign-in")
        if self.auth_required and not self.supabase_url:
            out.append("SUPABASE_URL is required (it is the JWT issuer)")
        return out
