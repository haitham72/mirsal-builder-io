"""Path config. Cross-platform (pathlib only). Override with env vars MIRSAL_INPUT / MIRSAL_OUT."""
from __future__ import annotations

import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent.parent   # .../Mirsal-Builder/mirsal
REPO = PROJECT.parent                                     # .../Mirsal-Builder


def input_root() -> Path:
    """The folder that holds Images_gen/ and videos_gen/ (the watch folders). `inputs/` in the repo. MIRSAL_INPUT overrides."""
    env = os.environ.get("MIRSAL_INPUT")
    if env:
        return Path(env)
    return REPO / "inputs"


def out_root() -> Path:
    return Path(os.environ.get("MIRSAL_OUT", PROJECT / "out"))
