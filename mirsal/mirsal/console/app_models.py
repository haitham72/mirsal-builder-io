"""The pydantic models of the NATIVE FastAPI routes (console/app.py). Existing routes keep their dict shapes behind the adapter; every route added after the
migration declares its request and answer here, once, and validates at the route edge only (the engine never imports pydantic: rule 3)."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..flow.ticket_models import TicketAnswer, TicketDraft, TicketQuestion, TicketReport, TicketStatusChange, TicketTarget  # noqa: F401  (the ticket routes' shapes, written once in flow/)


class ChatTurnEvent(BaseModel):
    """`event: turn` of GET /api/chat/sessions/{id}/stream: the turn in progress, sent each time it changes (the step trace grows, a card arrives, the reply lands)."""
    model_config = ConfigDict(extra="forbid")
    working: bool
    count: int                              # how many messages the session holds now
    message: dict[str, Any] | None          # the last message as GET /api/chat/sessions/{id} shows it (steps, cards, text)


class ChatDoneEvent(BaseModel):
    """`event: done`: the turn has finished; the page reads the whole session once."""
    model_config = ConfigDict(extra="forbid")
    working: Literal[False] = False
    count: int


class ImportOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(default="import.png", max_length=200)
    prompt: str = Field(default="", max_length=2000)
    generation: str | int | None = None
    sheet: str | None = None
    retry: bool = False


class ProviderImport(ImportOptions):
    id: str = Field(pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


class ImportResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int | None = None
    duplicate: bool | None = None
    kind: Literal["sheet", "video"] | None = None
    generation: str | None = None
    recoverable: bool | None = None


# ---------- Help & Support (flow/support.py, flow/faq.py, flow/notifications.py; docs/api.md "Help & Support")
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
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=4000)
    client_id: str | None = Field(default=None, max_length=80)


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
