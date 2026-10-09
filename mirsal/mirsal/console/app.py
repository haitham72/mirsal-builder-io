"""The HTTP server: FastAPI on uvicorn.

Every existing route is served by an ADAPTER over the existing handler (`server.make_handler`): the request is handed to the same `do_GET` / `do_POST` code, in a
worker thread, writing into a pipe; the adapter reads the status line and the headers it wrote and streams the body. So every answer is byte-identical to the
stdlib server by construction (the same guards in the same order: Host, Origin, sign-in, roles, rate limit), and the streams (generation events, files with Range)
work unchanged. New routes are native FastAPI with pydantic models (`console/app_models.py`) and are added before the catch-all.

`python -m mirsal serve` runs this; `serve --stdlib` (or MIRSAL_SERVER=stdlib) runs the old ThreadingHTTPServer for one release."""
from __future__ import annotations

import asyncio
import http.client
import io
import queue
import socket
import threading
from types import SimpleNamespace

import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import StreamingResponse

_END = object()
_HOP = {b"server", b"date", b"connection", b"keep-alive", b"transfer-encoding"}     # uvicorn writes these itself


def quiet_loop():
    """Event loop for `Server`: identical, except a client that vanishes mid-connection stays silent. On Windows every
    aborted keep-alive (a closed tab, a parallel fetch, antivirus) otherwise prints a ConnectionResetError traceback
    from the event loop; the disconnect itself is harmless and anything else still goes to the default handler."""
    loop = asyncio.new_event_loop()

    def _quiet(failed, context):
        if isinstance(context.get("exception"), (ConnectionResetError, BrokenPipeError)):
            return
        failed.default_exception_handler(context)

    loop.set_exception_handler(_quiet)
    return loop


class _Pipe:
    """The handler's `wfile`: what it writes goes to the adapter; once the client is gone a write raises BrokenPipeError, so a long stream (SSE) stops."""

    def __init__(self):
        self.q: queue.Queue = queue.Queue()
        self.closed = False

    def write(self, b) -> int:
        if self.closed:
            raise BrokenPipeError("the client went away")
        if b:
            self.q.put(bytes(b))
        return len(b)

    def flush(self) -> None:
        if self.closed:
            raise BrokenPipeError("the client went away")


def _handle(H, method: str, target: str, raw_headers: bytes, body: bytes, client: str, port: int, pipe: _Pipe) -> None:
    """Run the existing handler on one request without a socket: the same object the stdlib server builds, minus the connection."""
    h = H.__new__(H)
    h.rfile, h.wfile = io.BytesIO(body), pipe
    h.client_address = (client, 0)
    h.server = SimpleNamespace(server_address=("127.0.0.1", port))
    h.command, h.path, h.request_version = method, target, "HTTP/1.1"
    h.requestline = f"{method} {target} HTTP/1.1"
    h.close_connection = True
    h.headers = http.client.parse_headers(io.BytesIO(raw_headers))
    try:
        fn = getattr(h, "do_" + method, None)
        if fn is None:
            h.send_error(501, f"Unsupported method ({method!r})")
        else:
            fn()
    except (BrokenPipeError, ConnectionError):
        pass
    finally:
        pipe.q.put(_END)


def _split_head(buf: bytes) -> tuple[int, list[tuple[bytes, bytes]], bytes]:
    head, _, rest = buf.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    status = int(lines[0].split(b" ", 2)[1])
    headers = []
    for ln in lines[1:]:
        k, _, v = ln.partition(b":")
        if k.strip().lower() not in _HOP:
            headers.append((k.strip(), v.strip()))              # the handler's own casing (Content-Type, Retry-After): the bytes stay the same
    return status, headers, rest


def _legacy_call(H, method: str, target: str, raw_headers: bytes, client: str, port: int) -> tuple[int, bytes]:
    """One in-process request through the original handler (the same guards: Host, sign-in, roles, ownership); the whole answer at once."""
    pipe = _Pipe()
    _handle(H, method, target, raw_headers, b"", client, port, pipe)
    buf = b""
    while True:
        chunk = pipe.q.get()
        if chunk is _END:
            break
        buf += chunk
    status, _, body = _split_head(buf)
    return status, body


def _native_headers(request) -> dict:
    """The two headers every answer of this server carries (docs/api.md): the API version and the request id (the caller's when it is well formed)."""
    import re
    import uuid
    from .openapi import VERSION
    rid = request.headers.get("x-request-id") or ""
    return {"X-API-Version": VERSION, "X-Request-Id": rid if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", rid) else uuid.uuid4().hex[:16], "Cache-Control": "no-store"}


def _identify(H, request, port: int, path: str):
    """The caller of a NATIVE route, checked by the original handler's own guard steps in the same order (Host and Origin, sign-in, the token rate limit):
    -> (user, None) or (None, (status, body))."""
    raw_headers = b"".join(k + b": " + v + b"\r\n" for k, v in request.headers.raw) + b"\r\n"
    h = H.__new__(H)
    h.headers = http.client.parse_headers(io.BytesIO(raw_headers))
    h.command, h.path = request.method, path
    h.client_address = (request.client.host if request.client else "127.0.0.1", 0)
    h.server = SimpleNamespace(server_address=("127.0.0.1", port))
    why = h._foreign()
    if why:
        return None, (403, {"error": why})
    user = h._who(path)
    if user is None:
        return None, (401, {"error": "an API token is required (Authorization: Bearer <token>)"})
    wait = h._wait(user, path)
    if wait:
        return None, (429, {"error": f"too many requests: wait {wait} s"})
    return user, None


def _sse(event: str, data: str) -> bytes:
    return f"event: {event}\ndata: {data}\n\n".encode()


def create_app(c, port: int, secure: bool = False) -> FastAPI:
    """The app for one Console. `port` is the port it is served on (the Host check compares against it); `secure`: served over TLS (the session cookie is Secure)."""
    from .server import make_handler
    H = make_handler(c)
    app = FastAPI(title="Mirsal Builder", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.console = c

    from fastapi.responses import JSONResponse
    from pydantic import ValidationError

    def _j(request, status: int, obj) -> JSONResponse:
        """JSON exactly as the original handler writes it (ensure_ascii off, the same headers)."""
        import json
        from starlette.responses import Response
        return Response(json.dumps(obj, ensure_ascii=False).encode(), status_code=status, media_type="application/json; charset=utf-8", headers=_native_headers(request))

    async def _who(request, path):
        return await asyncio.to_thread(_identify, H, request, port, path)

    async def _body(request, model):
        """A body that does not match the model answers in this server's own words (400 {"error"}), never FastAPI's 422."""
        import json
        raw = await request.body()
        try:
            return model.model_validate(json.loads(raw or b"{}")), None
        except (ValueError, ValidationError) as e:
            msg = e.errors()[0]["msg"] if isinstance(e, ValidationError) else str(e)
            return None, f"bad request: {msg}"

    # ---------- office accounts (docs/api.md, Office accounts on the LAN): sign-up, sign-in, sign-out, forgot password, change password; Users > People
    from .app_models import ImportOptions, ProviderImport, ImportResult
    from ..flow import imports as im, pipeline as pl
    from ..media.video_project import MAX_UPLOAD

    async def _import_owner(request):
        user, err = await _who(request, "/api/import")
        if err:
            return None, _j(request, *err)
        if user.get("role") != "owner" or user.get("status") == "pending":
            return None, _j(request, 403, {"error": "this account cannot do that (owner only)"})
        return user, None

    @app.post("/api/import", include_in_schema=False)
    @app.post("/api/v1/import", include_in_schema=False)
    async def import_upload(request: Request):
        user, resp = await _import_owner(request)
        if resp:
            return resp
        try:
            options = ImportOptions.model_validate(dict(request.query_params))
            data = bytearray()
            async for chunk in request.stream():
                if len(data) + len(chunk) > MAX_UPLOAD:
                    return _j(request, 413, {"error": "file too large"})
                data.extend(chunk)
            status, body = await asyncio.to_thread(im.import_file, c, user, data=bytes(data), **options.model_dump())
            ImportResult.model_validate(body)
            return _j(request, status, body)
        except ValidationError as e:
            return _j(request, 400, {"error": "bad request: " + e.errors()[0]["msg"]})
        except (im.ImportError, pl.PipelineError) as e:
            return _j(request, e.code, {"error": str(e), **getattr(e, "hint", {})})

    @app.get("/api/higgsfield/history", include_in_schema=False)
    @app.get("/api/v1/higgsfield/history", include_in_schema=False)
    async def import_history(request: Request):
        _, resp = await _import_owner(request)
        if resp:
            return resp
        try:
            return _j(request, 200, await asyncio.to_thread(im.history, c, int(request.query_params.get("size", "40"))))
        except ValueError:
            return _j(request, 400, {"error": "size must be 1 to 100"})
        except im.ImportError as e:
            return _j(request, e.code, {"error": str(e)})

    @app.post("/api/higgsfield/import", include_in_schema=False)
    @app.post("/api/v1/higgsfield/import", include_in_schema=False)
    async def import_provider(request: Request):
        user, resp = await _import_owner(request)
        if resp:
            return resp
        body, bad = await _body(request, ProviderImport)
        if bad:
            return _j(request, 400, {"error": bad})
        try:
            options = body.model_dump(exclude={"id", "name", "job", "as_new"}, exclude_none=True)
            status, result = await asyncio.to_thread(im.import_job, c, user, body.id, **options)
            ImportResult.model_validate(result)
            return _j(request, status, result)
        except (im.ImportError, pl.PipelineError) as e:
            return _j(request, e.code, {"error": str(e), **getattr(e, "hint", {})})

    import time as _time
    from collections import defaultdict, deque
    from pydantic import BaseModel as _BM, ConfigDict as _CD, Field as _F
    from ..flow import people as pp
    from ..runtime.users import UserError

    class SignUp(_BM):
        model_config = _CD(extra="forbid")
        email: str = _F(max_length=254)
        name: str = _F(max_length=60)
        password: str = _F(max_length=200)

    class SignIn(_BM):
        model_config = _CD(extra="forbid")
        email: str = _F(max_length=254)
        password: str = _F(max_length=200)

    class Forgot(_BM):
        model_config = _CD(extra="forbid")
        email: str = _F(max_length=254)

    class NewPassword(_BM):
        model_config = _CD(extra="forbid")
        old: str = _F(default="", max_length=200)      # may be left out while the account still has the password it was given
        new: str = _F(max_length=200)

    class AddPeople(_BM):
        model_config = _CD(extra="forbid")
        emails: list[str] = _F(min_length=1, max_length=100)

    class Decide(_BM):
        model_config = _CD(extra="forbid")
        action: str = _F(max_length=20)
        role: str | None = None
        credits: int | None = None
        name: str | None = _F(default=None, max_length=60)
        email: str | None = _F(default=None, max_length=254)

    class CreditAsk(_BM):
        model_config = _CD(extra="forbid")
        reason: str = _F(default="", max_length=300)

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

    def _open_guard(request, path):
        """The checks a route reachable before signing in still gets: the Host and the Origin (no sign-in yet)."""
        h = H.__new__(H)
        h.headers = http.client.parse_headers(io.BytesIO(b"".join(k + b": " + v + b"\r\n" for k, v in request.headers.raw) + b"\r\n"))
        h.command, h.path = request.method, path
        h.client_address = (request.client.host if request.client else "127.0.0.1", 0)
        h.server = SimpleNamespace(server_address=("127.0.0.1", port))
        why = h._foreign()
        return (403, {"error": why}) if why else None

    def _cookie(resp, value: str | None):
        if value is None:
            resp.delete_cookie("mirsal_session", path="/")
        else:
            resp.set_cookie("mirsal_session", value, max_age=c.users.SESSION_HOURS * 3600, path="/", httponly=True, samesite="strict", secure=secure)
        return resp

    def _uerr(request, e):
        return _j(request, getattr(e, "code", 400), {"error": str(e)})

    from ..runtime import users as users_mod

    @app.get("/api/auth/me", include_in_schema=False)
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

    @app.post("/api/auth/signup", include_in_schema=False)
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

    @app.post("/api/auth/login", include_in_schema=False)
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

    @app.post("/api/auth/logout", include_in_schema=False)
    async def auth_logout(request: Request):
        err = _open_guard(request, "/api/auth/logout")
        if err:
            return _j(request, *err)
        await asyncio.to_thread(c.users.logout, request.cookies.get("mirsal_session") or "")
        return _cookie(_j(request, 200, {"ok": True}), None)

    @app.post("/api/auth/forgot", include_in_schema=False)
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

    @app.post("/api/auth/password", include_in_schema=False)
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

    @app.post("/api/auth/credits", include_in_schema=False)
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

    async def _admin(request, path):
        user, err = await _who(request, path)
        if err:
            return None, _j(request, *err)
        if user.get("role") not in ("owner", "admin") or user.get("status") == "pending":
            return None, _j(request, 403, {"error": "this account cannot do that (owner or admin only)"})
        return user, None

    @app.get("/api/people", include_in_schema=False)
    async def people_list(request: Request):
        user, resp = await _admin(request, "/api/people")
        if resp:
            return resp
        return _j(request, 200, {"people": await asyncio.to_thread(c.users.list), "requests": await asyncio.to_thread(pp.waiting, c.out),
                                 "recent": await asyncio.to_thread(pp.recent, c.out)})

    @app.post("/api/people", include_in_schema=False)
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

    @app.post("/api/people/{uid}", include_in_schema=False)
    async def people_decide(request: Request, uid: str):
        user, resp = await _admin(request, f"/api/people/{uid}")
        if resp:
            return resp
        body, bad = await _body(request, Decide)
        if bad:
            return _j(request, 400, {"error": bad})
        from ..services import admin_bot
        try:
            u, pw = await asyncio.to_thread(admin_bot.apply, c, uid, body.action, user.get("id"), role=body.role, credits=body.credits, name=body.name, email=body.email)
        except UserError as e:
            return _uerr(request, e)
        return _j(request, 200, {"user": u, **({"password": pw} if pw else {})})

    # ---------- Trending (docs/api.md, Office accounts on the LAN): shared packs everyone signed in can open, like, comment on and use
    from ..flow import trending as tr

    class Comment(_BM):
        model_config = _CD(extra="forbid")
        text: str = _F(min_length=1, max_length=500)

    async def _member(request, path):
        """Anyone signed in and approved (a pending account is refused like everywhere)."""
        user, err = await _who(request, path)
        if err:
            return None, _j(request, *err)
        if user.get("status") == "pending":
            return None, _j(request, 403, {"error": "waiting for approval"})
        return user, None

    def _terr(request, e):
        return _j(request, getattr(e, "code", 400), {"error": str(e)})

    from ..flow import user_report as ur

    @app.get("/api/users/overview", include_in_schema=False)
    async def users_overview(request: Request):
        """The Users dashboard (owner, admin): every person's batches, stickers, jobs that worked / failed, spend, storage and 30-day series (flow/user_report.py)."""
        user, resp = await _admin(request, "/api/users/overview")
        if resp:
            return resp
        return _j(request, 200, await asyncio.to_thread(ur.overview, c.out, c.users.list()))

    @app.get("/api/users/{uid}", include_in_schema=False)
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

    @app.get("/api/trending", include_in_schema=False)
    @app.get("/api/v1/trending", include_in_schema=False)
    async def trending_list(request: Request, order: str = "trending"):
        user, resp = await _member(request, "/api/trending")
        if resp:
            return resp
        try:
            return _j(request, 200, {"packs": await asyncio.to_thread(tr.listing, c.out, c.lib, user["id"], order, c.users.list()), "order": order,
                                     "can_share": True})
        except tr.TrendingError as e:
            return _terr(request, e)

    @app.get("/api/trending/{pid}", include_in_schema=False)
    @app.get("/api/v1/trending/{pid}", include_in_schema=False)
    async def trending_one(request: Request, pid: str):
        user, resp = await _member(request, f"/api/trending/{pid}")
        if resp:
            return resp
        try:
            return _j(request, 200, await asyncio.to_thread(tr.detail, c.out, c.lib, pid, user["id"], c.users.list()))
        except tr.TrendingError as e:
            return _terr(request, e)

    @app.get("/api/trending/{pid}/file/{sid}", include_in_schema=False)
    @app.get("/api/v1/trending/{pid}/file/{sid}", include_in_schema=False)
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

    @app.post("/api/trending/{pid}/{act}", include_in_schema=False)
    @app.post("/api/v1/trending/{pid}/{act}", include_in_schema=False)
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

    @app.post("/api/trending/{pid}/comments/{cid}/delete", include_in_schema=False)
    @app.post("/api/v1/trending/{pid}/comments/{cid}/delete", include_in_schema=False)
    async def trending_uncomment(request: Request, pid: str, cid: str):
        user, resp = await _member(request, f"/api/trending/{pid}/comments/{cid}/delete")
        if resp:
            return resp
        try:
            await asyncio.to_thread(tr.delete_comment, c.out, pid, cid, user["id"], user.get("role"))
            return _j(request, 200, {"ok": True})
        except tr.TrendingError as e:
            return _terr(request, e)

    # ---------- tickets (docs/tickets_plan.md): the owner sees every ticket; a member sees and answers their own
    from ..flow import tickets as tk
    from .app_models import TicketAnswer, TicketReport, TicketStatusChange

    def _can_see(user, t):
        return user.get("role") == "owner" or t.get("user") == user.get("id") or (user.get("role") == "admin" and t.get("source") in ("support", "report"))

    def _ticket_view(user, t):
        """A member sees what was said and decided, never the internal fields (fingerprint, context, proposed fix, who drafted it)."""
        if user.get("role") in ("owner", "admin"):
            return t
        return {k: t.get(k) for k in ("id", "source", "at", "last_at", "status", "issue", "summary", "intent", "questions", "answers", "conversation")} | {
            "thread": [{k: m.get(k) for k in ("n", "role", "text", "ts")} for m in t.get("thread") or []]}

    @app.get("/api/tickets", include_in_schema=False)
    @app.get("/api/v1/tickets", include_in_schema=False)
    async def tickets_list(request: Request, status: str | None = None):
        user, err = await _who(request, "/api/tickets")
        if err:
            return _j(request, *err)
        mine = None if user.get("role") == "owner" else user.get("id")
        return _j(request, 200, {"tickets": await asyncio.to_thread(tk.listing, c.out, status=status, user=mine)})

    @app.get("/api/tickets/{tid}", include_in_schema=False)
    @app.get("/api/v1/tickets/{tid}", include_in_schema=False)
    async def tickets_one(request: Request, tid: str):
        user, err = await _who(request, f"/api/tickets/{tid}")
        if err:
            return _j(request, *err)
        try:
            t = await asyncio.to_thread(tk.read, c.out, tid)
        except KeyError:
            return _j(request, 404, {"error": "not found"})
        return _j(request, 200, _ticket_view(user, t)) if _can_see(user, t) else _j(request, 404, {"error": "not found"})

    @app.post("/api/tickets", include_in_schema=False)
    @app.post("/api/v1/tickets", include_in_schema=False)
    async def tickets_report(request: Request):
        user, err = await _who(request, "/api/tickets")
        if err:
            return _j(request, *err)
        body, bad = await _body(request, TicketReport)
        if bad:
            return _j(request, 400, {"error": bad})
        t = await asyncio.to_thread(tk.report, c.out, user=user.get("id"), text=body.text, target=body.target.model_dump())
        return _j(request, 201, t)

    @app.post("/api/tickets/{tid}/answer", include_in_schema=False)
    @app.post("/api/v1/tickets/{tid}/answer", include_in_schema=False)
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

    @app.post("/api/tickets/{tid}/status", include_in_schema=False)
    @app.post("/api/v1/tickets/{tid}/status", include_in_schema=False)
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

    @app.get("/api/generations/{gid}/export.zip", include_in_schema=False)
    @app.get("/api/v1/generations/{gid}/export.zip", include_in_schema=False)
    async def generation_zip(request: Request, gid: str):
        """The Studio's Download .zip: the batch's accepted stickers (animated where ready) and a manifest. The owner, or the batch's own person; a stranger's is a 404."""
        user, err = await _who(request, f"/api/generations/{gid}/export.zip")
        if err:
            return _j(request, *err)
        from starlette.responses import Response
        from ..flow import batches as _batches
        from ..flow.pipeline import PipelineError
        try:
            n = int(str(gid).upper().lstrip("G"))
            if not c.visible(user, n):
                raise KeyError(gid)
            data, stem = await asyncio.to_thread(_batches.export_zip, c.out, n)
        except (KeyError, ValueError, FileNotFoundError, PipelineError) as e:                # PipelineError: no such batch
            missing = isinstance(e, (KeyError, FileNotFoundError, PipelineError)) or "invalid literal" in str(e)
            return _j(request, 404 if missing else 409, {"error": "not found" if missing else str(e)})
        return Response(data, media_type="application/zip", headers={**_native_headers(request), "Content-Disposition": f'attachment; filename="{stem}.zip"'})

    # ---------- Help & Support (flow/support.py; docs/api.md "Help & Support"): every person their own conversations and notifications,
    # the owner and admins the queue, the replies, resolving and the FAQ. Nothing a person or a retrieved text writes can authorize anything: roles are checked here.
    from ..flow import faq as fq, notifications as nt, support as sup, support_kb as skb
    from .app_models import FaqEdit, NotificationsRead, SupportAsk, SupportEscalate, SupportFeedback, SupportForget, SupportReopen, SupportText, TicketResolve
    from .server import NO_ROUTE as _NO_ROUTE

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

    @app.get("/api/support/conversations", include_in_schema=False)
    @app.get("/api/v1/support/conversations", include_in_schema=False)
    async def support_list(request: Request):
        user, resp = await _member(request, "/api/support/conversations")
        if resp:
            return resp
        rows = await asyncio.to_thread(sup.listing, c.out, user)
        return _j(request, 200, {"conversations": rows, "unread": (await asyncio.to_thread(nt.listing, c.out, user.get("id")))["unread"]})

    @app.post("/api/support/ask", include_in_schema=False)
    @app.post("/api/v1/support/ask", include_in_schema=False)
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

    @app.get("/api/support/conversations/{cid}", include_in_schema=False)
    @app.get("/api/v1/support/conversations/{cid}", include_in_schema=False)
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

    @app.get("/api/support/conversations/{cid}/images/{name}", include_in_schema=False)
    @app.get("/api/v1/support/conversations/{cid}/images/{name}", include_in_schema=False)
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

    @app.post("/api/support/conversations/{cid}/{act}", include_in_schema=False)
    @app.post("/api/v1/support/conversations/{cid}/{act}", include_in_schema=False)
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

    @app.get("/api/notifications", include_in_schema=False)
    @app.get("/api/v1/notifications", include_in_schema=False)
    async def notifications_list(request: Request):
        user, resp = await _member(request, "/api/notifications")
        if resp:
            return resp
        try:
            await asyncio.to_thread(sup.check_watches, c.out, user)                          # read every 30 s by the page: a finished job notifies here
        except Exception:
            pass
        return _j(request, 200, await asyncio.to_thread(nt.listing, c.out, user.get("id")))

    @app.post("/api/notifications/read", include_in_schema=False)
    @app.post("/api/v1/notifications/read", include_in_schema=False)
    async def notifications_read(request: Request):
        user, resp = await _member(request, "/api/notifications/read")
        if resp:
            return resp
        body, bad = await _body(request, NotificationsRead)
        if bad:
            return _j(request, 400, {"error": bad})
        return _j(request, 200, await asyncio.to_thread(nt.mark_read, c.out, user.get("id"), body.ids, body.conversation))

    @app.get("/api/support/queue", include_in_schema=False)
    @app.get("/api/v1/support/queue", include_in_schema=False)
    async def support_queue(request: Request, status: str | None = "active"):
        user, resp = await _staff(request, "/api/support/queue")
        if resp:
            return resp
        return _j(request, 200, {"tickets": await asyncio.to_thread(sup.queue, c.out, status)})

    @app.get("/api/support/tickets/{tid}", include_in_schema=False)
    @app.get("/api/v1/support/tickets/{tid}", include_in_schema=False)
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

    @app.post("/api/tickets/{tid}/reply", include_in_schema=False)
    @app.post("/api/v1/tickets/{tid}/reply", include_in_schema=False)
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

    @app.post("/api/tickets/{tid}/resolve", include_in_schema=False)
    @app.post("/api/v1/tickets/{tid}/resolve", include_in_schema=False)
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

    @app.get("/api/faq", include_in_schema=False)
    @app.get("/api/v1/faq", include_in_schema=False)
    async def faq_list(request: Request, status: str | None = None):
        """Everyone: the published entries. Staff: any status (`pending` = drafts and proposed revisions waiting for review, `all`)."""
        user, resp = await _member(request, "/api/faq")
        if resp:
            return resp
        if not sup.is_staff(user) or status in (None, "published"):
            return _j(request, 200, {"faq": await asyncio.to_thread(fq.listing, c.out, "published")})
        return _j(request, 200, {"faq": await asyncio.to_thread(fq.listing, c.out, None if status == "all" else status)})

    @app.get("/api/faq/{fid}", include_in_schema=False)
    @app.get("/api/v1/faq/{fid}", include_in_schema=False)
    async def faq_one(request: Request, fid: str):
        user, resp = await _member(request, f"/api/faq/{fid}")
        if resp:
            return resp
        try:
            f = await asyncio.to_thread(fq.read, c.out, fid)
            return _j(request, 200, f if sup.is_staff(user) else fq.public(f))
        except KeyError as e:
            return _serr(request, e)

    @app.post("/api/faq/{fid}/{act}", include_in_schema=False)
    @app.post("/api/v1/faq/{fid}/{act}", include_in_schema=False)
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

    _REINDEX: dict = {"running": False, "last": None, "error": None}

    @app.get("/api/support/status", include_in_schema=False)
    @app.get("/api/v1/support/status", include_in_schema=False)
    async def support_status(request: Request):
        user, resp = await _staff(request, "/api/support/status")
        if resp:
            return resp
        return _j(request, 200, {**await asyncio.to_thread(skb.status, c.out), "reindex": dict(_REINDEX)})

    @app.post("/api/support/reindex", include_in_schema=False)
    @app.post("/api/v1/support/reindex", include_in_schema=False)
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

    @app.get("/api/chat/sessions/{sid}/stream", include_in_schema=False)
    @app.get("/api/v1/chat/sessions/{sid}/stream", include_in_schema=False)
    async def chat_stream(request: Request, sid: str):
        """The chat turn as it happens: `turn` each time the last message changes (its steps, cards, text), then `done`; a comment every 15 s keeps
        the connection open; the stream ends after 10 minutes (EventSource reconnects). Access is the session route's own: the same headers go through the handler."""
        import json
        from starlette.responses import Response
        from .app_models import ChatDoneEvent, ChatTurnEvent
        raw_headers = b"".join(k + b": " + v + b"\r\n" for k, v in request.headers.raw) + b"\r\n"
        client = request.client.host if request.client else "127.0.0.1"
        target = f"/api/chat/sessions/{sid}"
        status, body = await asyncio.to_thread(_legacy_call, H, "GET", target, raw_headers, client, port)
        if status != 200:                                # 401 / 403 / 404 exactly as the session route answers
            return Response(body, status_code=status, media_type="application/json; charset=utf-8", headers=_native_headers(request))

        async def events():
            nonlocal status, body
            loop = asyncio.get_running_loop()
            end, last, quiet = loop.time() + 600, None, loop.time()
            yield b"retry: 3000\n\n"
            while loop.time() < end:
                if await request.is_disconnected():
                    return
                s = json.loads(body)
                msgs = s.get("messages") or []
                turn = ChatTurnEvent(working=bool(s.get("working")), count=len(msgs), message=msgs[-1] if msgs else None)
                sig = turn.model_dump_json()
                if sig != last:
                    last, quiet = sig, loop.time()
                    yield _sse("turn", sig)
                if not turn.working:
                    yield _sse("done", ChatDoneEvent(count=len(msgs)).model_dump_json())
                    return
                if loop.time() - quiet > 15:
                    quiet = loop.time()
                    yield b": ping\n\n"
                await asyncio.sleep(0.4)
                status, body = await asyncio.to_thread(_legacy_call, H, "GET", target, raw_headers, client, port)
                if status != 200:
                    return

        return StreamingResponse(events(), media_type="text/event-stream; charset=utf-8", headers={**_native_headers(request), "X-Accel-Buffering": "no"})

    @app.api_route("/{rest:path}", methods=["GET", "POST", "HEAD", "PUT", "PATCH", "DELETE", "OPTIONS"], include_in_schema=False)
    async def legacy(request: Request, rest: str):
        raw_path = request.scope.get("raw_path") or request.url.path.encode()
        qs = request.scope.get("query_string") or b""
        target = raw_path.decode("latin-1") + ("?" + qs.decode("latin-1") if qs else "")
        raw_headers = b"".join(k + b": " + v + b"\r\n" for k, v in request.headers.raw) + b"\r\n"
        body = await request.body()
        pipe = _Pipe()
        threading.Thread(target=_handle, args=(H, request.method, target, raw_headers, body, request.client.host if request.client else "127.0.0.1", port, pipe),
                         daemon=True, name="mirsal-request").start()
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = await asyncio.to_thread(pipe.q.get)
            if chunk is _END:
                break
            buf += chunk
        status, headers, first = _split_head(buf) if b"\r\n\r\n" in buf else (500, [(b"content-type", b"application/json; charset=utf-8")], b'{"error": "internal error"}')
        done = b"\r\n\r\n" not in buf

        async def stream():
            try:
                if first:
                    yield first
                if done:
                    return
                while True:
                    chunk = await asyncio.to_thread(pipe.q.get)
                    if chunk is _END:
                        return
                    yield chunk
            finally:
                pipe.closed = True

        resp = StreamingResponse(stream(), status_code=status)
        resp.raw_headers = headers
        return resp

    return app


class Server:
    """uvicorn with the interface the rest of the code and the tests use of the stdlib server: `server_address`, `serve_forever()`, `shutdown()`, `server_close()`."""

    def __init__(self, c, host: str = "127.0.0.1", port: int = 8770, tls: dict | None = None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(128)
        self.server_address = self.sock.getsockname()[:2]
        tls = tls or {}
        self.app = create_app(c, self.server_address[1], secure=bool(tls))
        self.uv = uvicorn.Server(uvicorn.Config(self.app, log_level="warning", access_log=False, lifespan="off", timeout_keep_alive=5,
                                                loop="mirsal.console.app:quiet_loop",
                                                ssl_certfile=tls.get("cert"), ssl_keyfile=tls.get("key")))
        self._stopped = threading.Event()

    def serve_forever(self, poll_interval: float | None = None) -> None:      # the stdlib signature (poll_interval is uvicorn's own business)
        try:
            self.uv.run(sockets=[self.sock])
        finally:
            self._stopped.set()

    def shutdown(self) -> None:
        self.uv.should_exit = True
        self._stopped.wait(10)

    def server_close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass
