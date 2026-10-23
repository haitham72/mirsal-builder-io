"""Tickets native HTTP routes."""
from __future__ import annotations
import asyncio
from fastapi import APIRouter, Request
from ...flow import tickets as tk
from ...flow.ticket_models import TicketAnswer, TicketReport, TicketStatusChange

def _can_see(user, t):
    return user.get("role") == "owner" or t.get("user") == user.get("id") or (user.get("role") == "admin" and t.get("source") in ("support", "report"))

def build_router(ctx):
    router = APIRouter()
    c = ctx.console
    _j = ctx.json
    _who = ctx.who
    _body = ctx.body

    def _ticket_view(user, t):
        """A member sees what was said and decided, never the internal fields (fingerprint, context, proposed fix, who drafted it)."""
        if user.get("role") in ("owner", "admin"):
            return t
        return {k: t.get(k) for k in ("id", "source", "at", "last_at", "status", "issue", "summary", "intent", "questions", "answers", "conversation")} | {
            "thread": [{k: m.get(k) for k in ("n", "role", "text", "ts")} for m in t.get("thread") or []]}

    @router.get("/api/tickets", include_in_schema=False)
    @router.get("/api/v1/tickets", include_in_schema=False)
    async def tickets_list(request: Request, status: str | None = None):
        user, err = await _who(request, "/api/tickets")
        if err:
            return _j(request, *err)
        mine = None if user.get("role") == "owner" else user.get("id")
        return _j(request, 200, {"tickets": await asyncio.to_thread(tk.listing, c.out, status=status, user=mine)})

    @router.get("/api/tickets/{tid}", include_in_schema=False)
    @router.get("/api/v1/tickets/{tid}", include_in_schema=False)
    async def tickets_one(request: Request, tid: str):
        user, err = await _who(request, f"/api/tickets/{tid}")
        if err:
            return _j(request, *err)
        try:
            t = await asyncio.to_thread(tk.read, c.out, tid)
        except KeyError:
            return _j(request, 404, {"error": "not found"})
        return _j(request, 200, _ticket_view(user, t)) if _can_see(user, t) else _j(request, 404, {"error": "not found"})

    @router.post("/api/tickets", include_in_schema=False)
    @router.post("/api/v1/tickets", include_in_schema=False)
    async def tickets_report(request: Request):
        user, err = await _who(request, "/api/tickets")
        if err:
            return _j(request, *err)
        body, bad = await _body(request, TicketReport)
        if bad:
            return _j(request, 400, {"error": bad})
        t = await asyncio.to_thread(tk.report, c.out, user=user.get("id"), text=body.text, target=body.target.model_dump())
        return _j(request, 201, t)

    @router.post("/api/tickets/{tid}/answer", include_in_schema=False)
    @router.post("/api/v1/tickets/{tid}/answer", include_in_schema=False)
    async def tickets_answer(request: Request, tid: str):
        user, err = await _who(request, f"/api/tickets/{tid}/answer")
        if err:
            return _j(request, *err)
        body, bad = await _body(request, TicketAnswer)
        if bad:
            return _j(request, 400, {"error": bad})
        try:
            t = await asyncio.to_thread(tk.read, c.out, tid)
            if not _can_see(user, t):
                return _j(request, 404, {"error": "not found"})
            return _j(request, 200, await asyncio.to_thread(tk.answer, c.out, tid, body.question, body.choice, body.text, user.get("id"), body.question_text))
        except KeyError:
            return _j(request, 404, {"error": "not found"})
        except ValueError as e:
            return _j(request, 400, {"error": f"bad request: {e}"})

    @router.post("/api/tickets/{tid}/status", include_in_schema=False)
    @router.post("/api/v1/tickets/{tid}/status", include_in_schema=False)
    async def tickets_status(request: Request, tid: str):
        user, err = await _who(request, f"/api/tickets/{tid}/status")
        if err:
            return _j(request, *err)
        if user.get("role") != "owner":
            return _j(request, 403, {"error": "this account cannot do that (owner only)"})
        body, bad = await _body(request, TicketStatusChange)
        if bad:
            return _j(request, 400, {"error": bad})
        try:
            return _j(request, 200, await asyncio.to_thread(tk.set_status, c.out, tid, body.status, body.fixed_by, user.get("id")))
        except KeyError:
            return _j(request, 404, {"error": "not found"})
    return router
