"""Users native HTTP routes."""
from __future__ import annotations
import asyncio
from fastapi import APIRouter, Request
from ...flow import user_report as ur

def build_router(ctx):
    router = APIRouter()
    c = ctx.console
    _j = ctx.json
    _member = ctx.member
    _admin = ctx.admin

    @router.get("/api/users/overview", include_in_schema=False)
    async def users_overview(request: Request):
        """The Users dashboard (owner, admin): every person's batches, stickers, jobs that worked / failed, spend, storage and 30-day series (flow/user_report.py)."""
        user, resp = await _admin(request, "/api/users/overview")
        if resp:
            return resp
        return _j(request, 200, await asyncio.to_thread(ur.overview, c.out, c.users.list()))

    @router.get("/api/users/{uid}", include_in_schema=False)
    async def users_one(request: Request, uid: str):
        """One person's page: the owner and admins open anyone; a member opens only their own (`me` or their id): anyone else is a 404, never a disclosure."""
        user, resp = await _member(request, "/api/users")
        if resp:
            return resp
        target = user["id"] if uid == "me" else uid
        if target != user["id"] and user.get("role") not in ("owner", "admin"):
            return _j(request, 404, {"error": "not found"})
        who = await asyncio.to_thread(c.users.get, target)
        if not who:
            return _j(request, 404, {"error": "not found"})
        return _j(request, 200, await asyncio.to_thread(ur.detail, c.out, who))
    return router
