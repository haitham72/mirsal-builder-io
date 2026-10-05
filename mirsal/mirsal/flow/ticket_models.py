"""The ticket shapes (docs/tickets_plan.md), pydantic, written once: `flow/tickets.py` validates the local model's draft with them and the native routes
(console/app.py, re-exported by console/app_models.py) validate requests and answers. The engine never imports this (rule 3)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ISSUES = ("wrong_result", "crash", "stuck_job", "duplicate", "ui", "slow", "spend", "feature", "access", "other")     # feature / access: Help & Support requests
Issue = Literal["wrong_result", "crash", "stuck_job", "duplicate", "ui", "slow", "spend", "other"]
Status = Literal["open", "answered", "fixed", "wont_fix"]


class TicketQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=3, max_length=200)
    choices: list[str] = Field(min_length=2, max_length=4)
    allow_other: bool = True

    @field_validator("choices")
    @classmethod
    def _short(cls, v):
        v = [str(x).strip()[:80] for x in v if str(x).strip()]
        if len(v) < 2:
            raise ValueError("a question needs at least two choices")
        return v


class TicketDraft(BaseModel):
    """What the local model returns for a ticket: checked strictly; anything else falls back to the preset questions of the issue."""
    model_config = ConfigDict(extra="ignore")
    issue: Issue
    summary: str = Field(min_length=3, max_length=300)
    proposed_fix: str = Field(min_length=3, max_length=600)
    questions: list[TicketQuestion] = Field(default_factory=list, max_length=4)


class TicketTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["generation", "sticker", "particle_set", "chat", "pack", "other"] = "other"
    id: str | None = Field(default=None, max_length=64)
    sticker: str | None = Field(default=None, max_length=64)


class TicketReport(BaseModel):
    """POST /api/tickets: a person's Report."""
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=2000)
    target: TicketTarget = Field(default_factory=TicketTarget)


class TicketAnswer(BaseModel):
    """POST /api/tickets/{id}/answer: one question answered by a choice or in words."""
    model_config = ConfigDict(extra="forbid")
    question: int = Field(ge=0, le=9)
    choice: str | None = Field(default=None, max_length=80)
    text: str | None = Field(default=None, max_length=1000)


class TicketStatusChange(BaseModel):
    """POST /api/tickets/{id}/status (owner): the ticket's state, with the commit that fixed it when there is one."""
    model_config = ConfigDict(extra="forbid")
    status: Status
    fixed_by: str | None = Field(default=None, max_length=80)
