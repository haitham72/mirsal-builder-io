"""Collection HTTP schemas."""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ...runtime.pricing import normalize_price


class CollectionExport(BaseModel):
    """Export to the AddCollection API (services/collection.py): the collection's name (default: the pack's; at most 40) and its description (at most 160;
    empty = the name). Longer values are a 400 with a sentence from services/collection.send, before anything is uploaded."""
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, max_length=200)
    description: str = Field(default="", max_length=2000)
    price: str | None = None     # omitted inherits the pack's saved price; explicit null omits it
    retime: bool = False          # animations shorter than 3 s are sent stretched to 3 s (the Studio asks first)
    light: bool = False

    @field_validator("price", mode="before")
    @classmethod
    def valid_price(cls, value):
        return normalize_price(value)
