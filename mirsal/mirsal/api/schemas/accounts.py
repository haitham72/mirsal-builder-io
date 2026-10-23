"""Accounts HTTP schemas."""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field


class SignUp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=254)
    name: str = Field(max_length=60)
    password: str = Field(max_length=200)


class SignIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)


class Forgot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=254)


class NewPassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    old: str = Field(default="", max_length=200)      # may be left out while the account still has the password it was given
    new: str = Field(max_length=200)


class AddPeople(BaseModel):
    model_config = ConfigDict(extra="forbid")
    emails: list[str] = Field(min_length=1, max_length=100)


class Decide(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(max_length=20)
    role: str | None = None
    credits: int | None = None
    name: str | None = Field(default=None, max_length=60)
    email: str | None = Field(default=None, max_length=254)


class CreditAsk(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(default="", max_length=300)
