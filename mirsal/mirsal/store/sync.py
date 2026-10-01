"""Best-effort write-through: pipeline.write_result() calls sync_result(), which persists the
generation when Postgres is up. Never raises, never slows the pipeline: availability is cached per
process, and test temp dirs (any out/ that is not the default one) are skipped so suites stay clean."""
from __future__ import annotations

import os
from pathlib import Path

from . import db
from . import repo


def _default_out() -> Path:
    from ..paths import out_root
    try:
        return out_root().resolve()
    except Exception:
        return Path("")


def is_default_out(out) -> bool:
    """True only for the real out/ (tests and MIRSAL_OUT copies never touch the shared database)."""
    try:
        return Path(out).resolve() == _default_out() and os.environ.get("MIRSAL_OUT") in (None, "")
    except Exception:
        return False


def enabled(out) -> bool:
    flag = os.environ.get("MIRSAL_DB_WRITE", "").lower()
    if flag in ("0", "no", "off", "false"):
        return False
    if flag in ("1", "on", "true", "yes"):
        return True
    return is_default_out(out)  # default: only the real out/ (MIRSAL_OUT copies use `db import`)


def sync_result(out, gid: int, res: dict) -> bool:
    try:
        if not enabled(out):
            return False
        if not db.available():
            return False
        with db.connect() as c:
            repo.save_generation(c, Path(out), gid)
        return True
    except Exception:
        return False
