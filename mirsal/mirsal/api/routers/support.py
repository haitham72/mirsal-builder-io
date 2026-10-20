"""Support native HTTP routes."""
from __future__ import annotations
import asyncio
from fastapi import APIRouter, Request
from ..dependencies import _native_headers
from ...flow import faq as fq, notifications as nt, support as sup, support_kb as skb
from ...flow import tickets as tk
from .tickets import _can_see
from ...console.server import NO_ROUTE as _NO_ROUTE
from ..schemas.support import FaqEdit, NotificationsRead, SupportAsk, SupportEscalate, SupportFeedback, SupportForget, SupportReopen, SupportText, TicketResolve

def build_router(ctx):
    router = APIRouter()
    c = ctx.console
    _j = ctx.json
    _body = ctx.body
    _member = ctx.member
    _REINDEX: dict = {"running": False, "last": None, "error": None}

    def _serr(request, e):
        if isinstance(e, KeyError):
            return _j(request, 404, {"error": "not found"})
        return _j(request, getattr(e, "code", 400), {"error": str(e)})

    async def _staff(request, path):
        user, resp = await _member(request, path)
        if resp:
            return None, resp
        if not sup.is_staff(user):
            return None, _j(request, 403, {"error": "this account cannot do that (owner or admin only)"})
        return user, None

    def _image(raw):
        import base64
        import binascii
        if not raw:
            return None
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[-1]
        try:
            return base64.b64decode(raw, validate=False)
        except (binascii.Error, ValueError):
            raise sup.SupportError("the screenshot could not be read")

    @router.get("/api/support/conversations", include_in_schema=False)
    @router.get("/api/v1/support/conversations", include_in_schema=False)
    async def support_list(request: Request):
        user, resp = await _member(request, "/api/support/conversations")
        if resp:
            return resp
        rows = await asyncio.to_thread(sup.listing, c.out, user)
        return _j(request, 200, {"conversations": rows, "unread": (await asyncio.to_thread(nt.listing, c.out, user.get("id")))["unread"]})

    @router.post("/api/support/ask", include_in_schema=False)
    @router.post("/api/v1/support/ask", include_in_schema=False)
    async def support_ask(request: Request):
        user, resp = await _member(request, "/api/support/ask")
        if resp:
            return resp
        body, bad = await _body(request, SupportAsk)
        if bad:
            return _j(request, 400, {"error": bad})
        try:
            cv = await asyncio.to_thread(sup.ask, c.out, user, body.text, body.conversation, _image(body.image), body.client_id)
        except (sup.SupportError, KeyError) as e:
            return _serr(request, e)
        return _j(request, 200, sup.view(cv, user))

    @router.get("/api/support/conversations/{cid}", include_in_schema=False)
    @router.get("/api/v1/support/conversations/{cid}", include_in_schema=False)
    async def support_one(request: Request, cid: str):
        user, resp = await _member(request, f"/api/support/conversations/{cid}")
        if resp:
            return resp
        try:
            await asyncio.to_thread(sup.check_watches, c.out, user)                          # a job asked about here may have finished
            cv = await asyncio.to_thread(sup.mine, c.out, user, cid)
        except KeyError as e:
            return _serr(request, e)
        if cv.get("user") == user.get("id"):
            await asyncio.to_thread(nt.mark_read, c.out, user.get("id"), None, cv["id"])       # opening it reads its notifications
        return _j(request, 200, sup.view(cv, user))

    @router.get("/api/support/conversations/{cid}/images/{name}", include_in_schema=False)
    @router.get("/api/v1/support/conversations/{cid}/images/{name}", include_in_schema=False)
    async def support_image(request: Request, cid: str, name: str):
        user, resp = await _member(request, f"/api/support/conversations/{cid}/images/{name}")
        if resp:
            return resp
        from starlette.responses import FileResponse
        try:
            cv = await asyncio.to_thread(sup.mine, c.out, user, cid)
            f = sup.image_path(c.out, cv, name)
        except KeyError as e:
            return _serr(request, e)
        return FileResponse(f, media_type="image/png", headers=_native_headers(request))

    @router.post("/api/support/conversations/{cid}/{act}", include_in_schema=False)
    @router.post("/api/v1/support/conversations/{cid}/{act}", include_in_schema=False)
    async def support_act(request: Request, cid: str, act: str):
        if act not in ("feedback", "escalate", "reply", "reopen", "forget"):
            return _j(request, 404, {"error": _NO_ROUTE})
        user, resp = await _member(request, f"/api/support/conversations/{cid}/{act}")
        if resp:
            return resp
        model = {"feedback": SupportFeedback, "reply": SupportText, "reopen": SupportReopen, "escalate": SupportEscalate, "forget": SupportForget}.get(act)
        body = None
        if model:
            body, bad = await _body(request, model)
            if bad:
                return _j(request, 400, {"error": bad})
        try:
            if act == "feedback":
                cv = await asyncio.to_thread(sup.feedback, c.out, user, cid, body.solved)
            elif act == "escalate":
                cv = await asyncio.to_thread(sup.escalate, c.out, user, cid, body.kind)
            elif act == "forget":
                cv = await asyncio.to_thread(sup.forget, c.out, user, cid, body.message)
            elif act == "reply":
                cv = await asyncio.to_thread(sup.reply_user, c.out, user, cid, body.text, body.client_id)
            else:
                cv = await asyncio.to_thread(sup.reopen, c.out, user, cid, body.text)
        except (sup.SupportError, KeyError) as e:
            return _serr(request, e)
        return _j(request, 200, sup.view(cv, user))

    @router.get("/api/notifications", include_in_schema=False)
    @router.get("/api/v1/notifications", include_in_schema=False)
    async def notifications_list(request: Request):
        user, resp = await _member(request, "/api/notifications")
        if resp:
            return resp
        try:
            await asyncio.to_thread(sup.check_watches, c.out, user)                          # read every 30 s by the page: a finished job notifies here
        except Exception:
            pass
        return _j(request, 200, await asyncio.to_thread(nt.listing, c.out, user.get("id")))

    @router.post("/api/notifications/read", include_in_schema=False)
    @router.post("/api/v1/notifications/read", include_in_schema=False)
    async def notifications_read(request: Request):
        user, resp = await _member(request, "/api/notifications/read")
        if resp:
            return resp
        body, bad = await _body(request, NotificationsRead)
        if bad:
            return _j(request, 400, {"error": bad})
        return _j(request, 200, await asyncio.to_thread(nt.mark_read, c.out, user.get("id"), body.ids, body.conversation))

    @router.get("/api/support/queue", include_in_schema=False)
    @router.get("/api/v1/support/queue", include_in_schema=False)
    async def support_queue(request: Request, status: str | None = "active"):
        user, resp = await _staff(request, "/api/support/queue")
        if resp:
            return resp
        return _j(request, 200, {"tickets": await asyncio.to_thread(sup.queue, c.out, status)})

    @router.get("/api/support/tickets/{tid}", include_in_schema=False)
    @router.get("/api/v1/support/tickets/{tid}", include_in_schema=False)
    async def support_ticket(request: Request, tid: str):
        """The admin's view of one escalated issue: the ticket and the person's conversation (screenshots, what the vision model saw, what was read)."""
        user, resp = await _staff(request, f"/api/support/tickets/{tid}")
        if resp:
            return resp
        try:
            t = await asyncio.to_thread(tk.read, c.out, tid)
        except KeyError as e:
            return _serr(request, e)
        if not _can_see(user, t):
            return _j(request, 404, {"error": "not found"})
        cv = sup._cv_of(c.out, t)
        return _j(request, 200, {"ticket": t, "conversation": sup.view(cv, user) if cv else None})

    @router.post("/api/tickets/{tid}/reply", include_in_schema=False)
    @router.post("/api/v1/tickets/{tid}/reply", include_in_schema=False)
    async def tickets_reply(request: Request, tid: str):
        user, resp = await _staff(request, f"/api/tickets/{tid}/reply")
        if resp:
            return resp
        body, bad = await _body(request, SupportText)
        if bad:
            return _j(request, 400, {"error": bad})
        try:
            t = await asyncio.to_thread(tk.read, c.out, tid)
            if not _can_see(user, t):
                return _j(request, 404, {"error": "not found"})
            return _j(request, 200, await asyncio.to_thread(sup.admin_reply, c.out, user, tid, body.text, body.client_id, body.private))
        except (sup.SupportError, KeyError, ValueError) as e:
            return _serr(request, e)

    @router.post("/api/tickets/{tid}/resolve", include_in_schema=False)
    @router.post("/api/v1/tickets/{tid}/resolve", include_in_schema=False)
    async def tickets_resolve(request: Request, tid: str):
        user, resp = await _staff(request, f"/api/tickets/{tid}/resolve")
        if resp:
            return resp
        body, bad = await _body(request, TicketResolve)
        if bad:
            return _j(request, 400, {"error": bad})
        try:
            t = await asyncio.to_thread(tk.read, c.out, tid)
            if not _can_see(user, t):
                return _j(request, 404, {"error": "not found"})
            return _j(request, 200, await asyncio.to_thread(sup.resolve, c.out, user, tid, body.text, body.client_id))
        except (sup.SupportError, KeyError, ValueError) as e:
            return _serr(request, e)

    @router.get("/api/faq", include_in_schema=False)
    @router.get("/api/v1/faq", include_in_schema=False)
    async def faq_list(request: Request, status: str | None = None):
        """Everyone: the published entries. Staff: any status (`pending` = drafts and proposed revisions waiting for review, `all`)."""
        user, resp = await _member(request, "/api/faq")
        if resp:
            return resp
        if not sup.is_staff(user) or status in (None, "published"):
            return _j(request, 200, {"faq": await asyncio.to_thread(fq.listing, c.out, "published")})
        return _j(request, 200, {"faq": await asyncio.to_thread(fq.listing, c.out, None if status == "all" else status)})

    @router.get("/api/faq/{fid}", include_in_schema=False)
    @router.get("/api/v1/faq/{fid}", include_in_schema=False)
    async def faq_one(request: Request, fid: str):
        user, resp = await _member(request, f"/api/faq/{fid}")
        if resp:
            return resp
        try:
            f = await asyncio.to_thread(fq.read, c.out, fid)
            return _j(request, 200, f if sup.is_staff(user) else fq.public(f))
        except KeyError as e:
            return _serr(request, e)

    @router.post("/api/faq/{fid}/{act}", include_in_schema=False)
    @router.post("/api/v1/faq/{fid}/{act}", include_in_schema=False)
    async def faq_act(request: Request, fid: str, act: str):
        if act not in ("publish", "edit", "archive", "discard"):
            return _j(request, 404, {"error": _NO_ROUTE})
        user, resp = await _staff(request, f"/api/faq/{fid}/{act}")
        if resp:
            return resp
        try:
            if act == "edit":
                body, bad = await _body(request, FaqEdit)
                if bad:
                    return _j(request, 400, {"error": bad})
                return _j(request, 200, await asyncio.to_thread(fq.edit, c.out, fid, user.get("id"), title=body.title, question=body.question, answer=body.answer))
            fn = {"publish": fq.publish, "archive": fq.archive, "discard": fq.discard}[act]
            return _j(request, 200, await asyncio.to_thread(fn, c.out, fid, user.get("id")))
        except (fq.FAQError, KeyError) as e:
            return _serr(request, e)

    @router.get("/api/support/status", include_in_schema=False)
    @router.get("/api/v1/support/status", include_in_schema=False)
    async def support_status(request: Request):
        user, resp = await _staff(request, "/api/support/status")
        if resp:
            return resp
        return _j(request, 200, {**await asyncio.to_thread(skb.status, c.out), "reindex": dict(_REINDEX)})

    @router.post("/api/support/reindex", include_in_schema=False)
    @router.post("/api/v1/support/reindex", include_in_schema=False)
    async def support_reindex(request: Request):
        """Cut docs/ and the code again in the background (free; vectors from the local model only). 202, then GET /api/support/status."""
        user, resp = await _staff(request, "/api/support/reindex")
        if resp:
            return resp
        if _REINDEX["running"]:
            return _j(request, 202, {"started": False, "running": True})

        def run():
            _REINDEX.update(running=True, error=None)
            try:
                _REINDEX["last"] = skb.reindex(c.out)
            except Exception as e:
                _REINDEX["error"] = str(e)[:300]
            finally:
                _REINDEX["running"] = False
        import threading
        threading.Thread(target=run, daemon=True, name="support-reindex").start()
        return _j(request, 202, {"started": True, "running": True})
    return router
