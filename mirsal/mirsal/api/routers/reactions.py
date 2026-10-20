"""Reactions native HTTP routes."""
from __future__ import annotations
import asyncio
from fastapi import APIRouter, Request
from ..dependencies import _native_headers
from ...flow import lottie_reactions as lr
from starlette.responses import Response as _Raw
from ..schemas.reactions import LottieReactionBody, SuperExportBody, SuperReactionBody

def build_router(ctx):
    router = APIRouter()
    c = ctx.console
    _j = ctx.json
    _body = ctx.body
    _member = ctx.member

    def _lr_err(request, e):
        return _j(request, getattr(e, "code", 400), {"error": str(e)})

    @router.get("/api/particles/lottie-reactions", include_in_schema=False)
    async def lottie_reactions(request: Request):
        user, resp = await _member(request, "/api/particles/lottie-reactions")
        if resp:
            return resp
        return _j(request, 200, await asyncio.to_thread(lr.listing, c.out))

    @router.get("/api/particles/lottie-reactions.zip", include_in_schema=False)
    async def lottie_reactions_zip(request: Request):
        user, resp = await _member(request, "/api/particles/lottie-reactions.zip")
        if resp:
            return resp
        data = await asyncio.to_thread(lr.export_zip, c.out)
        return _Raw(data, media_type="application/zip", headers={**_native_headers(request), "Content-Disposition": 'attachment; filename="lottie-reactions.zip"'})

    @router.get("/api/particles/lottie-reactions/{file}/export.json", include_in_schema=False)
    async def lottie_reaction_export(request: Request, file: str):
        user, resp = await _member(request, "/api/particles/lottie-reactions/export")
        if resp:
            return resp
        try:
            doc = await asyncio.to_thread(lr.compose, c.out, file)
        except lr.SetError as e:
            return _lr_err(request, e)
        import json as _json
        return _Raw(_json.dumps(doc, separators=(",", ":")).encode(), media_type="application/json", headers=_native_headers(request))

    @router.post("/api/particles/lottie-reactions/{file}/preview", include_in_schema=False)
    async def lottie_reaction_preview(request: Request, file: str):
        user, resp = await _member(request, "/api/particles/lottie-reactions/preview")
        if resp:
            return resp
        body, err = await _body(request, LottieReactionBody)
        if err:
            return _j(request, 400, {"error": err})
        try:
            return _j(request, 200, await asyncio.to_thread(lr.compose, c.out, file, body.settings or {}, body.morph_targets or []))
        except lr.SetError as e:
            return _lr_err(request, e)

    @router.post("/api/particles/lottie-reactions/{file}", include_in_schema=False)
    async def lottie_reaction_save(request: Request, file: str):
        user, resp = await _member(request, "/api/particles/lottie-reactions/save")
        if resp:
            return resp
        body, err = await _body(request, LottieReactionBody)
        if err:
            return _j(request, 400, {"error": err})
        try:
            return _j(request, 200, await asyncio.to_thread(lr.save, c.out, file, body.settings, body.morph_targets))
        except lr.SetError as e:
            return _lr_err(request, e)
    @router.get("/api/particles/super", include_in_schema=False)
    async def super_reactions(request: Request):
        user, resp = await _member(request, "/api/particles/super")
        if resp:
            return resp
        return _j(request, 200, await asyncio.to_thread(lr.super_listing))

    @router.post("/api/particles/super", include_in_schema=False)
    async def super_reaction(request: Request):
        user, resp = await _member(request, "/api/particles/super/compose")
        if resp:
            return resp
        body, err = await _body(request, SuperReactionBody)
        if err:
            return _j(request, 400, {"error": err})
        try:
            return _j(request, 200, await asyncio.to_thread(lr.super_compose, c.out, body.file, body.aspect, glow=body.glow,
                                                             color=body.color, colors=body.colors, settings=body.settings))
        except lr.SetError as e:
            return _lr_err(request, e)

    @router.post("/api/particles/super/export.zip", include_in_schema=False)
    async def super_export(request: Request):
        user, resp = await _member(request, "/api/particles/super/export.zip")
        if resp:
            return resp
        body, err = await _body(request, SuperExportBody)
        if err:
            return _j(request, 400, {"error": err})
        try:
            data = await asyncio.to_thread(lr.super_export_zip, c.out, files=body.files, glow=body.glow, color=body.color,
                                           colors=body.colors, settings=body.settings)
        except lr.SetError as e:
            return _lr_err(request, e)
        return _Raw(data, media_type="application/zip", headers={**_native_headers(request), "Content-Disposition": 'attachment; filename="superReactions.zip"'})

    return router
