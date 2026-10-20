"""Collection HTTP schemas."""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field


class CollectionExport(BaseModel):
    """Export to the AddCollection API (services/collection.py): the collection's name (default: the pack's; at most 40) and its description (at most 160;
    empty = the name). Longer values are a 400 with a sentence from services/collection.send, before anything is uploaded."""
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, max_length=200)
    description: str = Field(default="", max_length=2000)
    retime: bool = False          # animations shorter than 3 s are sent stretched to 3 s (the Studio asks first)
    light: bool = False
