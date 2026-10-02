"""A fixed-window rate limit per key (the signed-in person, else a hashed address). Redis when it answers (shared by every replica), memory otherwise (one process).

The key is never an address in clear and never leaves the gateway; a refusal says how long to wait."""
from __future__ import annotations

import hashlib
import threading
import time


def hashed(ip: str, salt: str = "mirsal") -> str:
    return hashlib.sha256(f"{salt}|{ip}".encode()).hexdigest()[:20]


class Limiter:
    def __init__(self, redis_url: str = ""):
        self._mem: dict = {}
        self._lock = threading.Lock()
        self._r = None
        if redis_url:
            try:
                import redis
                r = redis.Redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=1.0)
                r.ping()
                self._r = r
            except Exception:
                self._r = None

    @property
    def engine(self) -> str:
        return "redis" if self._r is not None else "memory"

    def hit(self, key: str, limit: int, window: int = 60) -> tuple[bool, int]:
        """-> (allowed, seconds to wait when refused)."""
        slot = int(time.time() // window)
        k = f"mirsal:gw:rate:{key}:{slot}"
        retry = window - int(time.time() % window)
        if self._r is not None:
            try:
                n = self._r.incr(k)
                if n == 1:
                    self._r.expire(k, window + 5)
                return (n <= limit, retry)
            except Exception:
                pass                                                  # Redis went away: fall back to this process's own count
        with self._lock:
            for old in [x for x in self._mem if not x.endswith(f":{slot}")]:
                self._mem.pop(old, None)
            n = self._mem.get(k, 0) + 1
            self._mem[k] = n
        return (n <= limit, retry)
