"""Trending native HTTP routes."""
from __future__ import annotations
import asyncio
from fastapi import APIRouter, Request
from ..dependencies import _native_headers
from ...flow import trending as tr
from ..schemas.trending import Comment

def build_router(ctx):
    router = APIRouter()
    c = ctx.console
    _j = ctx.json
    _body = ctx.body
    _member = ctx.member

    def _terr(request, e):
        return _j(request, getattr(e, "code", 400), {"error": str(e)})

    @router.get("/api/trending", include_in_schema=False)
    @router.get("/api/v1/trending", include_in_schema=False)
    async def trending_list(request: Request, order: str = "trending"):
        user, resp = await _member(request, "/api/trending")
        if resp:
            return resp
        try:
            return _j(request, 200, {"packs": await asyncio.to_thread(tr.listing, c.out, c.lib, user["id"], order, c.users.list()), "order": order,
                                     "can_share": True})
        except tr.TrendingError as e:
            return _terr(request, e)

    @router.get("/api/trending/{pid}", include_in_schema=False)
    @router.get("/api/v1/trending/{pid}", include_in_schema=False)
    async def trending_one(request: Request, pid: str):
        user, resp = await _member(request, f"/api/trending/{pid}")
        if resp:
            return resp
        try:
            return _j(request, 200, await asyncio.to_thread(tr.detail, c.out, c.lib, pid, user["id"], c.users.list()))
        except tr.TrendingError as e:
            return _terr(request, e)

    @router.get("/api/trending/{pid}/file/{sid}", include_in_schema=False)
    @router.get("/api/v1/trending/{pid}/file/{sid}", include_in_schema=False)
    async def trending_file(request: Request, pid: str, sid: str):
        user, resp = await _member(request, f"/api/trending/{pid}/file/{sid}")
        if resp:
            return resp
        import mimetypes
        from starlette.responses import FileResponse
        try:
            f = await asyncio.to_thread(tr.file_of, c.out, c.lib, pid, sid)
        except tr.TrendingError as e:
            return _terr(request, e)
        return FileResponse(f, media_type=mimetypes.guess_type(f.name)[0] or "application/octet-stream", headers=_native_headers(request))

    @router.post("/api/trending/{pid}/{act}", include_in_schema=False)
    @router.post("/api/v1/trending/{pid}/{act}", include_in_schema=False)
    async def trending_act(request: Request, pid: str, act: str):
        user, resp = await _member(request, f"/api/trending/{pid}/{act}")
        if resp:
            return resp
        try:
            if act in ("share", "unshare"):
                if not c.lib.owns(pid, user["id"]) and user.get("role") not in ("owner", "admin"):
                    return _j(request, 404, {"error": "not found"})
                if act == "share" and not c.lib.owns(pid, user["id"]):
                    return _j(request, 403, {"error": "only the maker makes a pack public"})
                if act == "share":
                    return _j(request, 200, {"shared": await asyncio.to_thread(tr.share, c.out, c.lib, pid, user["id"])})
                await asyncio.to_thread(tr.unshare, c.out, pid)
                return _j(request, 200, {"ok": True})
            if act in ("like", "unlike"):
                return _j(request, 200, {"likes": await asyncio.to_thread(tr.like, c.out, pid, user["id"], act == "like")})
            if act == "comments":
                body, bad = await _body(request, Comment)
                if bad:
                    return _j(request, 400, {"error": bad})
                return _j(request, 201, await asyncio.to_thread(tr.comment, c.out, pid, user["id"], user.get("name") or user["id"], body.text))
            if act == "view":
                return _j(request, 200, await asyncio.to_thread(tr.view, c.out, c.lib, pid, user["id"]))
            if act == "use":
                return _j(request, 201, {"copied": await asyncio.to_thread(tr.copy_pack, c.out, c.lib, pid, user["id"])})
        except tr.TrendingError as e:
            return _terr(request, e)
        return _j(request, 404, {"error": "no such action"})

    @router.post("/api/trending/{pid}/comments/{cid}/delete", include_in_schema=False)
    @router.post("/api/v1/trending/{pid}/comments/{cid}/delete", include_in_schema=False)
    async def trending_uncomment(request: Request, pid: str, cid: str):
        user, resp = await _member(request, f"/api/trending/{pid}/comments/{cid}/delete")
        if resp:
            return resp
        try:
            await asyncio.to_thread(tr.delete_comment, c.out, pid, cid, user["id"], user.get("role"))
            return _j(request, 200, {"ok": True})
        except tr.TrendingError as e:
            return _terr(request, e)
    return router
