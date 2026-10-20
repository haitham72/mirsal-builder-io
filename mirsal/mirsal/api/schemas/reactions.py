"""Reactions HTTP schemas."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ConfigDict


class LottieReactionBody(BaseModel):
    """POST /api/particles/lottie-reactions/{file} (save) and .../{file}/preview (the viewer): the editor's settings and morph targets. Keys and
    numbers are checked by flow/lottie_reactions.py (one list of settings, one 400 wording); left out = the saved values."""
    model_config = ConfigDict(extra="forbid")
    settings: dict[str, Any] | None = None
    morph_targets: list[str] | None = None
