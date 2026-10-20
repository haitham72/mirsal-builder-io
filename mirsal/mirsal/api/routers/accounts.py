"""Accounts native HTTP routes."""
from __future__ import annotations
import asyncio
from fastapi import APIRouter, Request
import time as _time
from collections import defaultdict, deque
from ...flow import people as pp
from ...runtime.users import UserError
from ...runtime import users as users_mod
from ..schemas.accounts import SignUp, SignIn, Forgot, NewPassword, AddPeople, Decide, CreditAsk

def build_router(ctx):
    router = APIRouter()
    c = ctx.console
    _j = ctx.json
    _who = ctx.who
    _body = ctx.body
    _admin = ctx.admin
    _open_guard = ctx.open_guard
    _cookie = ctx.cookie
    _uerr = ctx.error
    tries: dict = defaultdict(deque)

    def _throttled(*keys) -> bool:
        """Ten sign-in attempts per email and per address in 15 minutes."""
        now = _time.time()
        hit = False
        for k in keys:
            q = tries[k]
            while q and q[0] < now - 900:
                q.popleft()
            q.append(now)
            hit = hit or len(q) > 10
        return hit

    @router.get("/api/auth/me", include_in_schema=False)
    async def auth_me(request: Request):
        """Who this browser is: an account (with its status: `pending` waits for approval), or 401 {signed_out: true} = show the sign-in page."""
        err = _open_guard(request, "/api/auth/me")
        if err:
            return _j(request, *err)
        user, e2 = await _who(request, "/api/auth/me")
        if e2 or user is None:
            return _j(request, 401, {"error": "not signed in", "signed_out": True, "lan": c.lan, "domains": users_mod.email_domains()})
        return _j(request, 200, {"user": {k: v for k, v in user.items() if k != "token_sha256"}, "lan": c.lan, "domains": users_mod.email_domains(),
                                 "requests": pp.waiting(c.out, user.get("id")) if user.get("id") != "local" else []})

    @router.post("/api/auth/signup", include_in_schema=False)
    async def auth_signup(request: Request):
        err = _open_guard(request, "/api/auth/signup")
        if err:
            return _j(request, *err)
        body, bad = await _body(request, SignUp)
        if bad:
            return _j(request, 400, {"error": bad})
        try:
            u = await asyncio.to_thread(c.users.signup, body.email, body.name, body.password)
        except UserError as e:
            return _uerr(request, e)
        await asyncio.to_thread(pp.add, c.out, "signup", u)
        _, tok = await asyncio.to_thread(c.users.login, body.email, body.password)
        return _cookie(_j(request, 201, {"user": u, "waiting": True}), tok)

    @router.post("/api/auth/login", include_in_schema=False)
    async def auth_login(request: Request):
        err = _open_guard(request, "/api/auth/login")
        if err:
            return _j(request, *err)
        body, bad = await _body(request, SignIn)
        if bad:
            return _j(request, 400, {"error": bad})
        if _throttled("e:" + body.email.strip().lower(), "a:" + (request.client.host if request.client else "")):
            return _j(request, 429, {"error": "too many attempts: wait 15 minutes"})
        try:
            u, tok = await asyncio.to_thread(c.users.login, body.email, body.password)
        except UserError as e:
            return _uerr(request, e)
        return _cookie(_j(request, 200, {"user": u}), tok)

    @router.post("/api/auth/logout", include_in_schema=False)
    async def auth_logout(request: Request):
        err = _open_guard(request, "/api/auth/logout")
        if err:
            return _j(request, *err)
        await asyncio.to_thread(c.users.logout, request.cookies.get("mirsal_session") or "")
        return _cookie(_j(request, 200, {"ok": True}), None)

    @router.post("/api/auth/forgot", include_in_schema=False)
    async def auth_forgot(request: Request):
        """Always the same sentence (emails cannot be probed); a real account gets a request Haitham decides (dashboard or Telegram)."""
        err = _open_guard(request, "/api/auth/forgot")
        if err:
            return _j(request, *err)
        body, bad = await _body(request, Forgot)
        if bad:
            return _j(request, 400, {"error": bad})
        u = await asyncio.to_thread(c.users.by_email, body.email)
        if u and u.get("status") == "active":
            await asyncio.to_thread(pp.add, c.out, "password", c.users.public(u))
        return _j(request, 200, {"ok": True, "message": "If this email has an account, Haitham will be asked to give it a new password."})

    @router.post("/api/auth/password", include_in_schema=False)
    async def auth_password(request: Request):
        user, err = await _who(request, "/api/auth/password")
        if err:
            return _j(request, *err)
        body, bad = await _body(request, NewPassword)
        if bad:
            return _j(request, 400, {"error": bad})
        try:
            return _j(request, 200, {"user": await asyncio.to_thread(c.users.change_password, user["id"], body.old, body.new)})
        except UserError as e:
            return _uerr(request, e)

    @router.post("/api/auth/credits", include_in_schema=False)
    async def auth_credits(request: Request):
        """Request credits: a waiting request Haitham approves in Telegram or Users > People. Nothing refills on its own."""
        user, err = await _who(request, "/api/auth/credits")
        if err:
            return _j(request, *err)
        if user.get("id") == "local":
            return _j(request, 409, {"error": "the owner spends from the Higgsfield account directly"})
        body, bad = await _body(request, CreditAsk)
        if bad:
            return _j(request, 400, {"error": bad})
        return _j(request, 201, await asyncio.to_thread(pp.add, c.out, "credits", user, body.reason))

    @router.get("/api/people", include_in_schema=False)
    async def people_list(request: Request):
        user, resp = await _admin(request, "/api/people")
        if resp:
            return resp
        return _j(request, 200, {"people": await asyncio.to_thread(c.users.list), "requests": await asyncio.to_thread(pp.waiting, c.out),
                                 "recent": await asyncio.to_thread(pp.recent, c.out)})

    @router.post("/api/people", include_in_schema=False)
    async def people_add(request: Request):
        user, resp = await _admin(request, "/api/people")
        if resp:
            return resp
        body, bad = await _body(request, AddPeople)
        if bad:
            return _j(request, 400, {"error": bad})
        try:
            return _j(request, 201, {"people": await asyncio.to_thread(c.users.add_people, body.emails)})
        except UserError as e:
            return _uerr(request, e)

    @router.post("/api/people/{uid}", include_in_schema=False)
    async def people_decide(request: Request, uid: str):
        user, resp = await _admin(request, f"/api/people/{uid}")
        if resp:
            return resp
        body, bad = await _body(request, Decide)
        if bad:
            return _j(request, 400, {"error": bad})
        from ...services import admin_bot
        try:
            u, pw = await asyncio.to_thread(admin_bot.apply, c, uid, body.action, user.get("id"), role=body.role, credits=body.credits, name=body.name, email=body.email)
        except UserError as e:
            return _uerr(request, e)
        return _j(request, 200, {"user": u, **({"password": pw} if pw else {})})
    return router
