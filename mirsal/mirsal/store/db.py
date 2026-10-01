"""psycopg 3 connection. DATABASE_URL from the environment or mirsal/.env (git-ignored).
Default is the local mirsal-db on 5434 (never the workspace's other databases)."""
from __future__ import annotations

import os
from pathlib import Path

DEFAULT_URL = "postgresql://mirsal:mirsal_local@localhost:5434/mirsal"

_state: dict = {"ok": None}   # process-cached availability: None = untried, True/False


def _load_dotenv() -> None:
    f = Path(__file__).resolve().parent.parent.parent / ".env"
    try:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


def url() -> str:
    _load_dotenv()
    return os.environ.get("MIRSAL_DATABASE_URL") or os.environ.get("DATABASE_URL") or DEFAULT_URL


def connect():
    try:
        import psycopg
    except ImportError:
        raise RuntimeError("psycopg is not installed: pip install -r requirements.txt")
    return psycopg.connect(url(), connect_timeout=2)


def available() -> bool:
    """Cached per process: is Postgres reachable right now? A first failure disables the process silently."""
    if _state["ok"] is None:
        try:
            with connect() as c:
                c.execute("select 1")
            _state["ok"] = True
        except Exception:
            _state["ok"] = False
    return _state["ok"]


def reset_cache() -> None:
    _state["ok"] = None


def migrate() -> list[str]:
    """Apply mirsal/migrations/*.sql in order. Re-runnable. Returns the files applied now."""
    mig = sorted((Path(__file__).resolve().parent.parent.parent / "migrations").glob("*.sql"))
    done = []
    with connect() as c:
        for f in mig:
            with c.cursor() as cur:
                cur.execute(f.read_text(encoding="utf-8"))
                cur.execute("INSERT INTO schema_migrations (name) VALUES (%s) ON CONFLICT DO NOTHING", (f.name,))
            done.append(f.name)
    reset_cache()
    return done


def reset(confirm: str = "") -> None:
    """DEV ONLY: drop all Mirsal tables. The caller must pass confirm='yes'."""
    if confirm != "yes":
        raise RuntimeError("refusing: pass confirm='yes' (dev only, destroys the local Mirsal database)")
    tables = ["search_log", "tasks", "generation_events", "reviews", "assets",
              "video_sheets", "stickers", "generations", "schema_migrations"]
    with connect() as c:
        with c.cursor() as cur:
            for t in tables:
                cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
            cur.execute("DROP SEQUENCE IF EXISTS generation_seq")
            cur.execute("DROP FUNCTION IF EXISTS array_to_text(text[])")
            cur.execute("DROP FUNCTION IF EXISTS mirsal_words(text)")
    reset_cache()
