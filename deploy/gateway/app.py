"""The hosted front door of Mirsal: a FastAPI gateway in front of the unchanged engine server (the strangler pattern of plan.md, phase 0 done safely).

    browser --HTTPS--> gateway (this file) --loopback--> engine (`python -m mirsal serve`, console/server.py, every route and test as before)

The gateway does what a hosted app needs and the engine must not know about: the Host / Origin / CORS rules for a public name, the Google sign-in (a Supabase JWT, verified here), a rate limit per person,
body-size limits, health probes, and a streaming pass-through (the SSE of `/api/generations/{id}/events` and the chat polls included). It vouches for the person to the engine with
`X-Mirsal-Gateway-Secret` + `X-Mirsal-Subject` + `X-Mirsal-Name` (runtime/users.py `authenticate_gateway`); a header of that family sent by a client is dropped, and so are the client's Authorization,
Cookie, Origin and Sec-Fetch-* (the engine would trust them). A person is always a `member` of the engine: the owner's powers (library, Telegram setup, user list) are not reachable from the internet.

Nothing here touches the engine's code, the golden path or the gates. `create_app` takes its collaborators as arguments so every piece is tested without a network."""
from __future__ import annotations

import time
import uuid
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from starlette.background import BackgroundTask

from .auth import AuthError, Verifier
from .config import Settings
from .ratelimit import Limiter, hashed

HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade", "host", "content-length"}
STRIP_IN = HOP | {"authorization", "cookie", "origin", "referer", "accept-encoding"}
PUBLIC_PREFIXES = ("/ui/", "/assets/")
PAID = ("/api/live/sheet", "/api/live/video")
UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}

CALLBACK_HTML = """<!doctype html><meta charset=utf-8><title>Signing in</title><body style="font:16px system-ui;padding:40px">Signing you in…<script>
(async()=>{const p=new URLSearchParams(location.hash.slice(1));const t=p.get('access_token');
if(!t){document.body.textContent='No sign-in token in the address.';return}
const r=await fetch('/auth/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({access_token:t})});
if(r.ok){location.replace('/')}else{document.body.textContent='This sign-in was refused.'}})()</script>"""


def create_app(settings: Settings | None = None, verifier: Verifier | None = None, limiter: Limiter | None = None, client: httpx.AsyncClient | None = None) -> FastAPI:
    s = settings or Settings()
    ver = verifier or Verifier(s)
    lim = limiter or Limiter(s.redis_url)
    app = FastAPI(title="Mirsal gateway", docs_url=None, redoc_url=None, openapi_url=None)       # the engine's own OpenAPI is the contract (/api/openapi.json, through the gateway)
    app.state.settings, app.state.verifier, app.state.limiter = s, ver, lim
    app.state.client = client or httpx.AsyncClient(base_url=s.engine_url, timeout=httpx.Timeout(None, connect=5.0), follow_redirects=False)
    engine_host = urlparse(s.engine_url).netloc

    def err(status: int, msg: str, **h) -> JSONResponse:
        return JSONResponse({"error": msg}, status, headers=h)

    def allowed_origins(request: Request) -> set:
        if s.public_origin:
            return {s.public_origin}
        host = request.headers.get("host", "")
        return {f"https://{host}", f"http://{host}"}

    def person(request: Request):
        tok = ""
        a = request.headers.get("authorization", "")
        if a.lower().startswith("bearer "):
            tok = a[7:].strip()
        tok = tok or request.cookies.get(s.cookie_name, "")
        return ver.verify(tok)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        host = (request.headers.get("host") or "").split(":")[0].lower()
        if s.allowed_hosts and host not in {h.lower() for h in s.allowed_hosts} and request.url.path != "/healthz":      # a platform probes liveness under its own internal name
            return err(400, "unexpected Host header", **{"x-request-id": rid})
        if request.method in UNSAFE:
            origin = request.headers.get("origin")
            if origin is not None and origin.rstrip("/") not in allowed_origins(request):
                return err(403, "cross-origin request refused", **{"x-request-id": rid})
            if request.headers.get("sec-fetch-site", "same-origin") not in ("same-origin", "none"):
                return err(403, "cross-site request refused", **{"x-request-id": rid})
            if int(request.headers.get("content-length") or 0) > s.max_body:
                return err(413, "file too large", **{"x-request-id": rid})
        resp = await call_next(request)
        resp.headers["x-request-id"] = rid
        resp.headers.setdefault("x-content-type-options", "nosniff")
        resp.headers.setdefault("referrer-policy", "same-origin")
        resp.headers.setdefault("x-frame-options", "DENY")
        return resp

    # ---- probes ---------------------------------------------------------------------------------------------------------------------------------
    @app.get("/healthz")
    async def healthz():
        return {"ok": True}                                           # liveness: no dependency (a platform restarts the box when this fails)

    @app.get("/readyz")
    async def readyz():
        out = {"engine": False, "auth": (not s.auth_required) or ver.reachable(), "rate_limit": lim.engine, "problems": s.problems()}
        try:
            r = await app.state.client.get("/api/health", headers={"host": engine_host}, timeout=5.0)
            out["engine"] = r.status_code < 500
        except httpx.HTTPError:
            out["engine"] = False
        ok = out["engine"] and out["auth"] and not out["problems"]
        return JSONResponse(out, 200 if ok else 503)

    # ---- the Google sign-in -----------------------------------------------------------------------------------------------------------------
    @app.get("/auth/config")
    async def auth_config():
        return {"supabase_url": s.supabase_url, "anon_key": s.supabase_anon_key, "provider": "google", "callback": "/auth/callback", "required": s.auth_required}

    @app.get("/auth/callback")
    async def auth_callback():
        return HTMLResponse(CALLBACK_HTML, headers={"cache-control": "no-store"})

    @app.post("/auth/session")
    async def auth_session(request: Request):
        try:
            body = await request.json()
            who = ver.verify(str(body.get("access_token") or ""))
        except AuthError as e:
            return err(401, f"sign-in refused ({e})")
        except Exception:
            return err(400, "send {access_token}")
        r = JSONResponse({"name": who.name, "email": who.email, "avatar": who.avatar})
        r.set_cookie(s.cookie_name, str(body["access_token"]), max_age=max(60, int(who.exp - time.time())), httponly=True, secure=s.cookie_secure, samesite="lax", path="/")
        return r

    @app.post("/auth/logout")
    async def auth_logout():
        r = JSONResponse({"ok": True})
        r.delete_cookie(s.cookie_name, path="/")
        return r

    @app.get("/auth/me")
    async def auth_me(request: Request):
        try:
            who = person(request)
        except AuthError as e:
            return err(401, f"not signed in ({e})")
        return {"sub": who.sub, "name": who.name, "email": who.email, "avatar": who.avatar}

    # ---- everything else is the engine -------------------------------------------------------------------------------------------------------
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"])
    async def proxy(path: str, request: Request):
        full = "/" + path
        headers = {k: v for k, v in request.headers.items() if k.lower() not in STRIP_IN and not k.lower().startswith(("x-mirsal-", "sec-fetch-", "x-forwarded-"))}
        headers["host"] = engine_host
        headers["x-forwarded-for"] = hashed(request.client.host if request.client else "")      # only a hash ever leaves the gateway, and the engine does not use it
        public = request.method in ("GET", "HEAD") and (full == "/" or full.startswith(PUBLIC_PREFIXES))
        key = hashed(request.client.host if request.client else "")
        if not public and s.auth_required:
            try:
                who = person(request)
            except AuthError as e:
                return err(401, f"sign in first ({e})", **{"www-authenticate": "Bearer"})
            key = who.sub
            headers.update({"x-mirsal-gateway-secret": s.gateway_secret, "x-mirsal-subject": who.sub, "x-mirsal-name": who.name})
        if not public:
            ok, wait = lim.hit(key, s.rate_per_minute)
            if ok and request.method in UNSAFE and full in PAID:
                ok, wait = lim.hit(key + ":paid", s.paid_rate_per_minute)
            if not ok:
                return err(429, "too many requests, slow down", **{"retry-after": str(wait)})
        body = await request.body() if request.method in UNSAFE else None
        if body is not None and len(body) > s.max_body:
            return err(413, "file too large")
        req = app.state.client.build_request(request.method, full, params=request.query_params, headers=headers, content=body)
        try:
            up = await app.state.client.send(req, stream=True)
        except httpx.HTTPError:
            return err(502, "the engine is not answering")
        out = {k: v for k, v in up.headers.items() if k.lower() not in HOP and k.lower() not in ("content-encoding",)}
        if request.method == "HEAD":
            await up.aclose()
            return Response(status_code=up.status_code, headers=out)
        return StreamingResponse(up.aiter_raw(), status_code=up.status_code, headers=out, background=BackgroundTask(up.aclose))

    return app
