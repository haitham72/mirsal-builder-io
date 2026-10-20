"""Collection native HTTP routes."""
from __future__ import annotations
import asyncio
from fastapi import APIRouter, Request
from ...flow import pipeline as pl
from ...services import collection as col
from ..schemas.collection import CollectionExport

def build_router(ctx):
    router = APIRouter()
    c = ctx.console
    _j = ctx.json
    _who = ctx.who
    _body = ctx.body

    @router.get("/api/collection", include_in_schema=False)
    @router.get("/api/v1/collection", include_in_schema=False)
    async def collection_status(request: Request):
        user, err = await _who(request, "/api/collection")
        if err:
            return _j(request, *err)
        return _j(request, 200, col.status())

    async def _collection(request, path, what, make_zip, mine):
        user, err = await _who(request, path)
        if err:
            return _j(request, *err)
        if user.get("role") != "owner" or user.get("status") == "pending":
            return _j(request, 403, {"error": "Exporting to the collection API is available to the owner only"})
        if not await asyncio.to_thread(mine, user):                       # the owner's own packs and batches, as everywhere (library privacy applies to the owner too)
            return _j(request, 404, {"error": "not found"})
        body, bad = await _body(request, CollectionExport)
        if bad:
            return _j(request, 400, {"error": bad})
        try:                                                               # queued: the zip (retime: what the person chose for clips under 3 s) and the upload run in the background
            return _j(request, 202, col.enqueue(c.out, what, lambda: make_zip(body.retime, body.light), body.name, body.description, user.get("id") or "human"))
        except col.CollectionError as e:
            return _j(request, e.code, {"error": str(e)})

    @router.get("/api/collection/exports/{xid}", include_in_schema=False)
    @router.get("/api/v1/collection/exports/{xid}", include_in_schema=False)
    async def collection_export_state(request: Request, xid: str):
        user, err = await _who(request, f"/api/collection/exports/{xid}")
        if err:
            return _j(request, *err)
        st = await asyncio.to_thread(col.export_state, c.out, xid)
        if not st or user.get("role") != "owner" or st.get("by") != (user.get("id") or "human"):      # only its sender sees it
            return _j(request, 404, {"error": "not found"})
        return _j(request, 200, st)

    @router.post("/api/packs/{pid}/export-collection", include_in_schema=False)
    @router.post("/api/v1/packs/{pid}/export-collection", include_in_schema=False)
    async def pack_collection(request: Request, pid: str):
        from ...media.library import LibraryError

        def make(retime=False, light=False):
            try:
                return c.lib.export_zip(pid, light=light, retime=retime)[0]
            except LibraryError as e:
                raise col.CollectionError(str(e), getattr(e, "code", 409))
        return await _collection(request, f"/api/packs/{pid}/export-collection", f"pack {pid}", make, lambda u: c.lib.owns(pid, u["id"]))

    @router.post("/api/generations/{gid}/export-collection", include_in_schema=False)
    @router.post("/api/v1/generations/{gid}/export-collection", include_in_schema=False)
    async def generation_collection(request: Request, gid: str):
        from ...flow import batches as _batches
        from ...flow.pipeline import PipelineError

        def make(retime=False, light=False):
            try:
                n = int(str(gid).upper().lstrip("G"))
                return _batches.export_zip(c.out, n, light=light, retime=retime)[0]
            except (ValueError, FileNotFoundError, PipelineError) as e:
                missing = isinstance(e, (FileNotFoundError, PipelineError)) or "invalid literal" in str(e)
                raise col.CollectionError("not found" if missing else str(e), 404 if missing else 409)
        def mine(u):
            try:
                n = int(str(gid).upper().lstrip("G"))
                return pl.gen_dir(c.out, n).is_dir() and c.visible(u, n)                  # checked now: the zip is built later, in the queue
            except (ValueError, PipelineError, FileNotFoundError):
                return False
        return await _collection(request, f"/api/generations/{gid}/export-collection", gid.upper() if gid.upper().startswith("G") else f"G{gid}", make, mine)
    return router
