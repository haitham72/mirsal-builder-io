"""Path config. Cross-platform (pathlib only). Override with env vars MIRSAL_INPUT / MIRSAL_OUT."""
from __future__ import annotations

import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent.parent   # .../Mirsal-Builder/mirsal
REPO = PROJECT.parent                                     # .../Mirsal-Builder


def input_root() -> Path:
    """The folder that holds Images_gen/ and videos_gen/ (the watch folders). `inputs/` in the repo; an older checkout that still keeps
    them under Phase_01/ keeps working (nothing is renamed or moved). MIRSAL_INPUT overrides both."""
    env = os.environ.get("MIRSAL_INPUT")
    if env:
        return Path(env)
    legacy = REPO / "Phase_01"
    return legacy if (legacy / "Images_gen").is_dir() and not (REPO / "inputs" / "Images_gen").is_dir() else REPO / "inputs"


def out_root() -> Path:
    return Path(os.environ.get("MIRSAL_OUT", PROJECT / "out"))
