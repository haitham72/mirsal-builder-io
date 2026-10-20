"""Support HTTP schemas."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class SupportAsk(BaseModel):
    """One turn: the person's words, optionally a screenshot (base64, or a data: URL) and the conversation it continues. `client_id` makes a retry a no-op."""
    model_config = ConfigDict(extra="forbid")
    text: str = Field(default="", max_length=4000)
    conversation: str | None = Field(default=None, pattern=r"^[Cc]\d{3,}$")
    image: str | None = Field(default=None, max_length=12_000_000)
    client_id: str | None = Field(default=None, max_length=80)


class SupportFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    solved: bool


class SupportText(BaseModel):
    """`private` (an admin's reply only): a token or a password, shown to that person alone and kept out of the ticket, Postgres, notifications and the FAQ."""
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=4000)
    client_id: str | None = Field(default=None, max_length=80)
    private: bool = False


class SupportEscalate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["problem", "feature", "access"] = "problem"


class SupportForget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=20)


class SupportReopen(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str | None = Field(default=None, max_length=4000)


class TicketResolve(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str | None = Field(default=None, max_length=4000)
    client_id: str | None = Field(default=None, max_length=80)


class FaqEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, max_length=200)
    question: str | None = Field(default=None, max_length=1000)
    answer: str | None = Field(default=None, max_length=6000)


class NotificationsRead(BaseModel):
    """Which to mark read: these ids, or one conversation's, or (both empty) all of them."""
    model_config = ConfigDict(extra="forbid")
    ids: list[str] | None = None
    conversation: str | None = None
