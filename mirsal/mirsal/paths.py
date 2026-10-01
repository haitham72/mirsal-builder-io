"""Path config. Cross-platform (pathlib only). Override with env vars MIRSAL_INPUT / MIRSAL_OUT."""
from __future__ import annotations

import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent          # .../Mirsal-Builder/mirsal
REPO = PROJECT.parent                                     # .../Mirsal-Builder


def input_root() -> Path:
    return Path(os.environ.get("MIRSAL_INPUT", REPO / "Phase_01"))


def out_root() -> Path:
    return Path(os.environ.get("MIRSAL_OUT", PROJECT / "out"))
