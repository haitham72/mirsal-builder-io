# Deployment plan: putting Mirsal Builder online (PAUSED)

**Status: deployment remains PAUSED.** Hosting, OAuth, credits and external activation are groundwork only; retain the prepared files and held questions. **The local FastAPI + pydantic HTTP migration is authorized after particles (Haitham, 2026-10-04)** under [fastapi_plan.md](fastapi_plan.md). That authorization does not enable deployment or activate rate limiting. Prepared deployment files remain on `deployment`; `better_ui/ux` branches from it.

## Glossary (the words this file keeps using)

- **Engine** — the pure, deterministic core in `mirsal/engine/` (no I/O, no network, no model client). Everything else is built on top of it.
- **Golden path** — how a sticker is made: plan, sheet, stills, video sheet, video, animations, pack. A human approves at five gates (G1-G5).
- **Contract** — the stable JSON API in [`api.md`](api.md). A migration must not change it by one byte.
- **Trackers** — what needs a person is in [`waiting-for-haitham.md`](waiting-for-haitham.md); what is open to build is in [`backlog.md`](backlog.md); what is built is in the other files of `docs/`.
- **Paused** — external deployment, OAuth, credit infrastructure and rate-limit activation. The local HTTP migration is separately authorized.

**Status (2026-10-02, end of the unattended session): the plan is written, and the first slice of it is PREPARED on this branch in new folders. Nothing is switched on:** no Supabase project, no Vercel project, no Render service and no Google OAuth client exist; nothing was pushed to any of them.
**2026-10-04:** the local HTTP migration follows particle acceptance; the rest of deployment remains paused. Its executable spec is `fastapi_plan.md`.
This file lives on the `deployment` branch only (`git switch deployment`), never on `merge/generate-advanced`. Every phase is still scheduled work that becomes real only when it is built, tested and documented like any other change (`CLAUDE.md` rules 3, 8, 11, 12, 13).

## 0. Builds on

The prepared files are mapped in `deploy/README.md`; the app's own pieces it extends are in the area docs (`api.md`, `store-and-search.md`).

## 1. The seven asks

| # | Ask | Where it lands | Phase |
|---|---|---|---|
| 1 | The app runs on **FastAPI** instead of the stdlib server | `mirsal/mirsal/console/` split into routing/app vs. the transport-free `Console` core | 0 |
| 2 | Hosted **online for free**: Vercel + Supabase + Redis, **or** Render (sleep timers) running all the Python | §6 | 0 + 6 |
| 3 | Every user gets **10 Higgsfield credits to test**, all through the project's **private API**; a public launch wipes all history first | §7 + §8 | 2 + 6 |
| 4 | **Google OAuth** sign-in | §5 | 1 |
| 5 | **Telegram export never duplicates a pack** — an already exported pack is shown, not re-sent | §9 | 4 |
| 6 | **Two more Supabase tables**: Google-signed-up users, and that user's analysis with IP address | §4 + §10 | 1 + 3 |
| 7 | **Each user gets their own AI-agent session with persistent LangGraph memory**, the name from the Google profile | §11 | 5 |

---

## 2. Shape of the deployed app

```
browser  ── the Studio (mirsal/mirsal/console) or the Mirsal app, or a Vercel-hosted front end
   │  HTTPS, same origin, httpOnly cookie holding the Google/Supabase JWT
   ▼
FastAPI (uvicorn, 1 worker to start; the web service is stateless)
   ├── routes = today's console/server.py, same paths, same JSON (docs/api.md)
   ├── middleware = Host/Origin guard, rate limit per u_id, request id, tracing hook
   ├── Postgres @ Supabase        the mirror, the pool, accounts + user_analysis, LangGraph checkpoints
   ├── Redis @ Upstash            cache, idempotency keys, SSE fan-out, rate counters, live previews, job locks
   ├── object storage             the media (out/ cannot be a local disk once the worker is another machine)
   └── Higgsfield CLI (one shared login, server-side only) + ffmpeg/libvpx-vp9
   ▼
background worker  ── sheet jobs, Kling jobs, video slicing, VP9 encode, caption jobs, retention jobs
   reads the same Postgres/Redis/storage; claims jobs from out/jobs/*.json (durable, resumable, ticket-first)
```

**The hard fact that decides the hosting question:** the heavy work needs ffmpeg, ~1 GB RAM and minutes per job (2K sheet keying with OpenCV, VP9 encode, video slicing, GIF
previews). A serverless request/response platform cannot hold a process, cannot ship a 40 MB ffmpeg, and kills work that outlives a request. **The engine and the worker must run
on a machine with a disk and real CPU**; only thin stateless things may be serverless.

---

## 3. Phase 0 — FastAPI and "hostable" (the enabler; everything else depends on it)

> **The local FastAPI + pydantic migration is authorized after particles (2026-10-04)** under `docs/fastapi_plan.md`. External deployment and infrastructure activation remain paused; implement only the authorized local HTTP-layer scope.

Nothing else in this plan is safe before this phase: a local-disk `out/`, an in-process session list and an optional Redis all break the moment there are two machines.

### 3.1 What the code looks like today

| Piece | File | Lines that matter |
|---|---|---|
| stdlib HTTP server | `mirsal/mirsal/console/server.py` | the `Handler(BaseHTTPRequestHandler)` with a `do_GET` / `do_POST` dispatch table (~1.4k lines), `_foreign()` (Host/Origin), `_authorize()`, `idem()`, `_json()`, `_send()` |
| JSON contract | `mirsal/mirsal/console/openapi.py` | a hand-written OpenAPI dict served at `/openapi.json` |
| transport-free core | the same file | `class Console` — every method returns a dict, takes `self.out` / `self.inp` / `self.cfg`; no HTTP types |
| SSE | `runtime/events.py` + `console/server.py` | a long-lived GET that polls `events.list()` and writes `text/event-stream` |
| static files | `/ui/*`, `/assets/*`, `/out/*` | served from disk, with the `/out/` containment check (`_out_batch`) |
| tests | `tests/test_console.py`, `tests/test_api_contract.py`, `tests/test_phase5_api.py`, `tests/test_hardening.py`, `tests/test_live.py` | all of them call `serve(...)` from `tests/__init__.py` and talk HTTP to it |

### 3.2 The migration, step by step

1. **Keep `Console` exactly as it is** and treat it as the application core: `Console.live()`, `.chat()`, `.plan()`, etc. already return plain dicts and raise
   `pl.PipelineError(msg, code)`. That is the seam. No engine or service code changes.
2. **Add `console/app.py`**: a `FastAPI()` instance with a lifespan that builds one `Console` (Redis cache handle, Postgres pool, `AssetStore`) and closes it on shutdown.
3. **Routes** become thin functions: `@app.get("/api/generations/{gid}")` → `return _j(c.state(c.out, gid))`. One helper converts `PipelineError` to `JSONResponse({"error": ...}, code)` and
   `JobError` / `CatalogError` / `UserError` likewise. Keep the *paths*, the *methods* and the *bodies* of `docs/api.md`; `docs/api.md` is the contract, not the implementation.
4. **Middleware, in this order** (the guard must run before anything reads a body):
   `TrustedHostMiddleware` (the Host check of `_foreign`) → `CORSMiddleware` with **no origins** (same-origin only; do not "temporarily" allow any) → the `Origin` /
   `Sec-Fetch-Site` check for unsafe methods → rate limit (per `u_id`, then per hashed IP) → request id + access log.
5. **Authentication** stays in `runtime/users.py` (rule: it is tested there). FastAPI gets a dependency that reads the `Authorization` header or the cookie and calls the same
   `users.authenticate(...)`, then sets `request.state.user`. `_authorize()`'s role map becomes one table (`MEMBER_GET`, owner-only writes) reused verbatim.
6. **Idempotency**: `Console.idem(scope, key, fn)` is already transport-free — call it from a small dependency/helper with the same scope strings, so `tests/test_live.py`'s
   idempotency tests keep passing unchanged.
7. **SSE**: `@app.get("/api/generations/{gid}/events")` returning `StreamingResponse(media_type="text/event-stream")` with an `async` generator that polls `events.list()` (already
   Redis-backed with an in-memory fallback). One keep-alive comment every 15 s, and a hard cap per connection.
8. **Static**: `StaticFiles` for `/ui`, `/assets`, `/out` — keep the `/out/` containment check as a dependency that resolves and rejects `..`, symlinks and absolute paths
   (`tests/test_hardening.py` must still pass).
9. **OpenAPI**: delete the hand-written document and serve FastAPI's `/openapi.json`; keep `console/openapi.py` only as the *test* that compares the generated schema with the
   routes `tests/test_api_contract.py` expects (that test already exists and is the safety net).
10. **`serve`**: `python -m mirsal serve` starts uvicorn; `--stdlib` keeps the old server for A/B on a PC. `tests/__init__.py::serve()` gets a `flask`-free switch so the suite can run
    against either; the default becomes FastAPI, and `tests/test_api_contract.py` is run against both for one release.
11. **Dependencies**: `fastapi`, `uvicorn[standard]`, `httpx` (test client only). Nothing CDN at runtime (rule 8); no new wheels in `engine/`.

### 3.3 Making the state survivable

| Today (PC) | On two machines | Work |
|---|---|---|
| `out/` on the local disk | not shared | media behind `AssetStore` (S3/Supabase Storage); `out/` becomes a *cache* of what the store already holds. This is already open work in `docs/backlog.md` |
| Redis optional (`runtime/cache.py` falls back to memory) | mandatory | make "memory" a deliberate local-only mode: `doctor` says RED as a warning on a hosted box; refuse to start a worker with `MIRSAL_ALLOW_MEMORY_CACHE=0` unset |
| Postgres optional (files) | mandatory for accounts, pool, checkpoints, ledger | `MIRSAL_DB_REQUIRED=1` fails fast at boot; `db check` must pass before the health route answers `ok` |
| Jobs as files in `out/jobs/*.json` | already durable | keep; a worker claims with the existing lock; the web never runs a job when `MIRSAL_JOB_MODE=queue` |
| `runtime/users.py` in `out/users.json` (a secret file with a race) | Postgres | move accounts to Postgres (phase 1); the file becomes a dev-only fallback |
| Live preview canvases in the browser | fine | they are per-connection state; no server state |

### 3.4 Container and config

- `Dockerfile`: `python:3.14-slim`, `apt-get install ffmpeg libvpx-tools` (the VP9 encoder — `doctor` must say `libvpx-vp9 OK` in the image), `pip install -r requirements.txt`,
  non-root user, `CMD uvicorn mirsal.console.app:app --host 0.0.0.0 --port $PORT`.
- `docker-compose.yml` (exists, for Postgres :5434 / Redis :6380) gains an `app` and a `worker` service for the VM option only; on Render the same image is the web service and the
  worker, with `MIRSAL_JOB_MODE=queue`.
- Env only (no file config on a hosted box): `MIRSAL_OUT` (a writable temp dir), `MIRSAL_INPUT` (empty or prepared sheets baked in), `PG*` (Supabase pooler URL — the
  **transaction pooler, port 5432, and `?pgbouncer=true`**, because free tiers cap connections), `MIRSAL_REDIS_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`,
  `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `MIRSAL_STORAGE_*`, `MIRSAL_JOB_MODE=queue`, `MIRSAL_TRACE` (off), `MIRSAL_FFMPEG`.
- Health: `GET /healthz` (liveness, no DB), `GET /readyz` (DB + Redis + storage + `doctor` summary). The platform's health check uses `/healthz`; the deploy gate uses `/readyz`.

### 3.5 Definition of done for phase 0

- The migration's contract suites (`tests.test_openapi`, `test_api_contract`, `test_hardening`, `test_live`) and the routine tiers green against the FastAPI app (the two known-red idempotency tests are a separate item, §14).
- `docs/api.md` unchanged except the OpenAPI provenance note; `console/openapi.py` reduced to a test.
- `doctor` reports: server kind (FastAPI), Postgres required+reachable, Redis required+reachable, storage writable, `libvpx-vp9`, Higgsfield CLI presence (never credentials).
- A second process on another machine can serve the same media and claim the same jobs.

---

## 4. The two new tables

Both live in the same Postgres the app already mirrors into (`migrations/`), with RLS enabled, and are never written by the browser. Migration files, `db check` entries and the
`docs/store-and-search.md` lines ship in the same step (rule 12).

```sql
-- 006_accounts.sql : the account created by the Google sign-in
create table if not exists accounts (
  id            uuid primary key default gen_random_uuid(),
  u_id          text unique not null,           -- the app's own U### (runtime/users.py), so nothing else has to change
  google_sub    text unique not null,           -- Supabase auth.users.id == the JWT "sub"
  email         text,
  name          text,                           -- Google profile full_name / name; the greeting and the default pack name
  avatar_url    text,
  locale        text,
  role          text not null default 'member', -- member | owner (the app's own roles)
  can_spend     boolean not null default false, -- may start paid generation
  test_credits  numeric(10,2) not null default 10,
  disabled      boolean not null default false,
  telegram_bot  text,                           -- only if §9 decides per-user bots; ciphertext, never returned by the API
  created_at    timestamptz not null default now(),
  last_seen_at  timestamptz
);

-- 007_user_analysis.sql : per-user analysis (read §10 before writing anything into detail)
create table if not exists user_analysis (
  id          bigserial primary key,
  u_id        text not null references accounts(u_id) on delete cascade,
  ts          timestamptz not null default now(),
  ip_hash     text,          -- salted hash: counts uniques without locating a person
  ip_full     text,          -- full IP, ONLY for abuse handling, nulled after ip_retention_days
  user_agent  text,
  country     text,          -- from the platform's CDN header, never from a geo-IP service
  device      text,          -- phone | tablet | desktop, derived
  event       text not null, -- sign_in | batch_created | gate_approved | pack_exported | sticker_sent | error | credits_spent
  detail      jsonb          -- ids, counts, durations, model names, error codes: NEVER a prompt, caption, filename or media
);
create index if not exists user_analysis_u_ts on user_analysis (u_id, ts desc);
create index if not exists user_analysis_ts on user_analysis (ts desc);
alter table accounts enable row level security;      -- the API uses the service role; the browser never queries these directly
alter table user_analysis enable row level security;
create policy accounts_self on accounts for select using (auth.uid()::text = google_sub);
```

Notes: `gen_random_uuid`/`pgcrypto` and `pgvector` are already available in the image; `detail` gets a check that it is an object; a `CHECK (event = ANY (array[...]))` keeps the
vocabulary closed so the table cannot become a dumping ground; `db check` must be taught both tables (`docs/backlog.md` "frozen constraints": report any drift, never auto-upgrade).

---

## 5. Google OAuth

**Recommendation: Supabase Auth** (Google provider). It issues a JWT the API verifies with the project's public key: no password code, no session table of ours, one client that also
serves a future front end. Rolling our own (authlib + sessions) is ~150 lines we would own forever, for no gain.

What has to be built:

1. **First sight**: a JWT arrives, `sub` is unknown → insert `accounts` with `test_credits = 10`, `can_spend = true`, `name` from `user_metadata.full_name || user_metadata.name`.
   `u_id` is allocated with the existing `U###` scheme so every other table keeps its shape.
2. **A second authenticator** in `runtime/users.py`: `Bearer <supabase JWT>` verified (signature against the JWKS, `aud` = client id, `iss` = the project URL, `exp`) *before* the
   existing API tokens. Today's `owner`/`member`, `can_spend`, `disabled` and the local-open sandbox all stay; `tests/test_users.py` keeps passing and gains the JWT path.
3. **Cookie session** for the browser: httpOnly, Secure, SameSite=Lax, short access + rotating refresh. With a real session the `Sec-Fetch-Site: same-origin` trick in
   `runtime/users.py` stops being the way a person signs in — which closes the "who is the owner's page" decision in `docs/waiting-for-haitham.md`.
4. **One origin**: the page and the API on the same host, so there is no CORS and no CSRF token to get wrong. If they must differ (Vercel front end), then SameSite=None + a double-submit
   CSRF token, and `CORSMiddleware` with an explicit origin allow-list (never `*`).
5. **Redirect URIs**: `https://<host>/auth/callback` only; `localhost` allowed in dev; the Studio has a tiny `/auth/callback` route that posts the session cookie and returns to `/#/`.
6. **`doctor`** checks: Supabase reachable, JWKS fetchable, client id/secret set, RLS on both tables, and that the signed-in account exists.
7. **Offline / PC mode stays**: no Google, no accounts configured → the open local sandbox exactly as today (this is what the tests use).

Decide: Supabase Auth (recommended) or our own client; and whether Google is the only door (keeping a local door for the PC).

---

## 6. Hosting: the two options, and one better one

Free-tier numbers move; verify each against the provider's page before relying on it. The *shape* of the trap is what matters.

| | **Vercel + Supabase + Redis** | **Render (Python) + Supabase + Redis** |
|---|---|---|
| Fits the engine? | **No.** Serverless functions: no ffmpeg, a deployment-size limit, a request must finish inside the platform's time limit, no worker that outlives a request | **Yes.** One Docker image with ffmpeg, OpenCV, numpy, Pillow; a real background worker; a disk |
| Sleep / cold start | n/a (instances are ephemeral; every cold request re-imports cv2) | Free web services **auto-suspend when idle** and are capped by a monthly instance-hours quota; the old "sleep timer" toggle is no longer the mechanism. A wake means re-importing cv2/numpy and re-reading the plan: tens of seconds |
| A job when the instance sleeps | — | dies and resumes from `out/jobs/*.json` (ticket-first, no second charge) after the wake; the UI must say so |
| Postgres / Redis | native there (Supabase + Upstash) | the same two over the internet, through the **transaction pooler** (free tiers cap connections) |
| Media | object storage only | **shared** storage: a worker is a different service with a different disk → `AssetStore` is mandatory, a mounted disk works only if both services mount the same one |
| Ops | none | Docker, env, logs, a free instance that disappears |
| Free? | yes | yes for a hobby app, with the suspend quota |

**Recommendation.** Render **web service + background worker** from one image, Supabase for Postgres/Auth/Storage, Upstash (or Supabase's) Redis. Add Vercel later only if a
Next.js front end is wanted; **the engine must never run on Vercel.**

**The genuinely-free alternative** (name it, because it is the only one with enough RAM): an **Oracle Cloud Always Free** ARM VM (or any small VPS) running the repo's existing
`docker-compose.yml` (Postgres :5434, Redis :6380) plus `app` + `worker`. No suspend, a real disk, one box to reason about. Choose by appetite for maintenance, not by feature list.

Decision inputs to write down when choosing: expected concurrent users, peak job minutes/hour, media volume (Storage egress), whether the operator accepts a suspend wake, and whether a
card is acceptable for Render's worker (workers are a paid instance class on most plans — **verify**, because "free" may stop at the worker).

---

## 7. Higgsfield: 10 test credits per user, one private API

1. **The CLI login lives only on the server.** The browser never sees a Higgsfield token, never names a model it cannot price, never runs the CLI.
2. **Per-user credits.** `accounts.test_credits` starts at 10. The estimate is checked against the user's remaining credits **before** the job starts, in the same place the daily
   cap is checked today (`generation/jobs.py`, `MIRSAL_DAILY_CREDITS`), and debited when the job is paid (a reservation, then a settle on the real cost, so a failed job refunds).
   At 0 credits the user can still use prepared sheets and every free path; the Studio says why the button is off.
3. **Rule 13 stays absolute**: the price is on the button and the plan card; a paid call happens only after the user's yes (or with "Ask before spending" off). The shared account's
   balance is the operator's problem and shows on the owner's health page only, never to a member.
4. **One paid call at a time** across all users (today's paid lock) **plus** a per-user in-flight limit, so one user cannot hold the queue for everyone.
5. **Ledger**: every call is already a line in `out/model_calls.jsonl`; mirror it to Postgres with `u_id` and `credits` (and `event: credits_spent` in `user_analysis`) so "who spent
   what" is answerable per user and per day.
6. **Ask the provider first.** Sharing or reselling one provider account across users may breach Higgsfield's terms. That is a question for Higgsfield, not a technical detail, and it
   gates any public launch. The same question for the local→hosted model question in §11.

---

## 8. Going public: the scrub runbook (write it before the launch, run it once)

Order matters: **rotate first, rewrite second, never the other way round.**

1. **Rotate everything** (new values live, old ones dead): Higgsfield CLI login, Google OAuth client secret, Telegram bot token, Supabase service-role key, the database password,
   Upstash credentials, the LangSmith key. A secret that was ever in git history is compromised even after it is deleted from the tip.
2. **Untrack the data**: add `mirsal/out/` (real generations, prompts, `model_calls.jsonl`, `sessions/`, `library/` files, `users.json`, `.asset_secret`, `telegram.json`,
   `cache/`) and `inputs/` (media) to `.gitignore`; `git rm -r --cached mirsal/out inputs`; keep `docs/`, `mirsal/mirsal/`, `tests/`, `migrations/`, `*.md`.
3. **Purge the working copy**: keep an empty `out/` skeleton with a README that explains what appears there; delete G001–G093 and the ledger from the public branch.
4. **Rewrite the history** (only with Haitham's explicit go-ahead, never unasked):
   `git filter-repo --force --invert-paths --path mirsal/out --path inputs` (add `--replace-text` for any secret value that must be scrubbed from history),
   then force-push **every** branch and tag, and tell collaborators to re-clone (a normal pull cannot repair it).
5. **Verify**: `git log --all -S '<old token>'` is empty; a fresh clone has no `out/` data; `python -m mirsal doctor` is clean on the clone.
6. **Keep an offline backup** of the pre-scrub repository — it is the only copy of the real generations.

Also decide, before the launch, whether `mirsal/out/` is ever tracked again (the open question in `docs/waiting-for-haitham.md`); the honest answer for a public repo is "no".

---

## 9. Telegram: never export the same pack twice

1. **A pack gets a fingerprint at export time**: `sha256` over its sorted sticker entries — `file_name` + `sha256(bytes)` + type (static/animated) — **not** the pack name (people retype
   names) and not the pack id (packs get duplicated by accident, which is exactly the case to catch). Stored as
   `packs.telegram = {fingerprint, set_name, sticker_ids, sent_at, bot_id}` (a migration + `db check`).
2. **Export checks it first.** `POST /api/packs/{id}/send` (and the Studio's Send button): if the pack carries an export record, **return that record** — set name, links, when, by whom —
   and do not call Telegram again. Re-uploading to the same set creates duplicate stickers; this is the bug the requirement exists for.
3. **Two explicit escape hatches**, both recorded in the pack's history: *Replace* (resend on purpose) and *Send as a new set* (append the subject to the name). Neither is a default.
4. **One bot or one per user?** A shared bot puts every user's sets in one namespace (the user must add the bot, and rate limits are shared); a per-user token means an encrypted
   column, a setup screen, and no shared limits. **Decide with Haitham** — it changes §4's table and the UX.
5. **Double-click safety**: the route keeps the existing `Idempotency-Key` handling, so even a bypassed fingerprint cannot produce two sends.
6. Tests: sending twice returns the first send; changing one sticker's bytes changes the fingerprint; *Send as a new set* creates a second set and says so.

---

## 10. Privacy, before the analysis table exists

An **IP address is personal data**. Under UAE PDPL (and GDPR for any EU user) it needs a lawful basis, a notice, a purpose and an erasure path. Minimum, no exceptions:

- Notice at sign-in, in plain words: what is recorded (IP, device, country, what you did, when), why, how long, and how to delete it.
- `ip_full` only for abuse handling, nulled by a scheduled worker after `ip_retention_days` (7 / 30 / 90 — **decide**); `ip_hash` (salted, per deployment) for unique counting.
- `country` from the platform's CDN header, never from a geo-IP lookup service.
- `detail` carries ids, counts, durations, model names, error codes. **Never** a prompt, a caption, a filename, a path or media bytes. A test should assert this (scan `detail` keys against a
  forbidden list).
- Export and delete for every user (`GET /api/me/export`, `DELETE /api/me`) covering `accounts`, `user_analysis`, their generations, their packs, their chats and their agent memory; the
  delete is a real cascade and is tested against a row count.
- No third-party analytics, no pixels, no session replay. LangSmith stays off unless the operator turns it on for their own runs (`MIRSAL_TRACE`), and never with user media.
- Rate limits keyed by `u_id` (falling back to a hashed IP), never by raw IP in a response body or a log line.

---

## 11. Per-user agent session and persistent LangGraph memory

1. **Sessions**: `chat_sessions (id, u_id, title, google_name, created_at, updated_at)`. The name comes from the Google profile (`accounts.name`) and is used for the greeting and the
   default pack name; the user can rename. The name is never treated as an instruction — it goes through the same fencing as any other fetched text (`services/llm.py`).
2. **Graph state**: LangGraph's Postgres checkpointer (`langgraph-checkpoint-postgres`) with `thread_id = "<u_id>:<session_id>"`. Durable across restarts and shared by every replica —
   which is exactly why it cannot be in-process or Redis-only.
3. **Memory** keeps its current meaning (`docs/agent-and-chat.md`): structured subjects / passes / likes from `agent/memory.py`, never a transcript. Move it from `out/sessions/*.json`
   to Postgres (`memories (u_id, subject, summary jsonb, embedding vector, updated_at)`) using the pool's own embedder; the reducer's rules (it may trim raw interactions, never a
   subject or a pass) are enforced by tests that already exist.
4. **The spend guard is unchanged**: every paid tool checks `_may_spend()` *and* the user's remaining credits, and only `n_confirm` can reach a create tool. A per-user turn is one
   Redis lock, so two tabs of the same user cannot run two turns.
5. **Models**: the local models (`qwen3.5-4b:2`, `nomic-embed-text-v1.5`) are hardcoded and free and simply **absent** on a hosted box. Decide: a hosted LLM provider with a monthly budget
   and a shown price (rule 13 — this is the open "OpenAI calls without a plan card" decision in `docs/waiting-for-haitham.md` and it must be settled *before* the first public user), or self-hosted
   weights (RAM, cold starts, GPU for the judge).

---

## 12. Phases, in order, each ending in tests and docs

| Phase | Work | Done when |
|---|---|---|
| **0. Hostable** | §3 in full: FastAPI, env-only config, Redis/Postgres mandatory, `AssetStore`, `doctor`, Dockerfile | the suite is green against FastAPI; two processes share media and jobs; `/healthz` + `/readyz` |
| **1. Accounts** | §5 + `accounts`: Google sign-in, JWT auth, cookie session, RLS, `me/export/delete` | `tests/test_users.py` covers the JWT path; a stranger is 404; a delete really removes rows |
| **2. Money** | §7: 10 credits per user, reserve/settle ledger with `u_id`, price before every paid call, per-user in-flight limit | a user with 1 credit cannot start a 2-credit sheet; the ledger attributes every call to a user |
| **3. Analysis** | §4's `user_analysis` + §10: the notice, the retention worker, per-user rate limits | the retention worker nulls old IPs; no prompt text in `detail`; export/delete covers the table |
| **4. Telegram** | §9: fingerprint, export record, never duplicate, *Replace* / *new set* | sending twice returns the first send; changed bytes change the fingerprint |
| **5. Agent** | §11: per-user sessions, Postgres checkpointer, memory in Postgres, name from Google | two users' memories never mix; a restart resumes a thread; a user cannot spend another user's credits |
| **6. Launch** | §6 hosting choice, §8 scrub runbook, staging smoke test, docs | a fresh clone has no user data; `doctor` green online; the two scrub verifications pass |

Rough effort, for planning only (one engineer, tests and docs included): 0 ≈ 3-5 days, 1 ≈ 2-3, 2 ≈ 2, 3 ≈ 1-2, 4 ≈ 1, 5 ≈ 3-4, 6 ≈ 2-3 (plus the provider's answer on §7.6).

Dependencies: 0 before everything; 1 before 2, 3, 5; 2 before any public user; 4 can run in parallel with 2; 6 last.

---

## 13. Risks

| Risk | Why it bites | Answer |
|---|---|---|
| Free tier sleeps mid-job | the user waits; a request may time out | jobs are resumable files; the UI says "waking up"; a ping keeps a free instance awake (read the terms) |
| `out/` on two machines | the worker writes where the web cannot see | `AssetStore` in phase 0, not after the first bug report |
| A shared Higgsfield account | rate limits, ToS, one bad actor | per-user credits, one paid call at a time, the provider's answer first |
| A leaked secret in history | it stays leaked after a rewrite | rotate, then rewrite, then verify (§8) |
| Cold local models | the hosted chat has no LM Studio | a hosted provider with a budget, or self-hosted weights (§11.5) |
| IP addresses collected | PDPL/GDPR exposure | notice, purpose, retention, export/delete (§10) |
| ffmpeg/VP9 missing on the platform | encoding silently fails | `doctor` checks `libvpx-vp9` at boot; the platform is chosen so the binary exists |
| Free-tier database pauses | Supabase free projects pause after inactivity; the first request after a pause is slow | a scheduled ping from a platform cron, or accept the latency |
| Rate limits per IP break behind a proxy | everyone shares one IP | key on `u_id` once signed in, hashed IP only for anonymous calls |

---

## 15. What must not change

- The engine stays pure and independently testable (`CLAUDE.md` rule 3): FastAPI, Supabase, Redis, OAuth and S3 live in `console/` / `runtime/` / `store/`, never in `engine/`.
- The golden path, the five gates, "Python's blocks are final", the vision model never approves, the verifier's 44 checks.
- The JSON contract of `docs/api.md` (paths, shapes, idempotency keys, signed links, SSE) and the engine's file names (rule 9).
- The Studio stays a sandbox over the API (rule 11): every feature above is an engine/service function first, a screen second.
- No paid call without a shown price and a go (rule 13); no secret ever in git; docs updated in the same step (rule 12).

---

---

## 17. Open questions for Haitham (numbered in `docs/waiting-for-haitham.md`; an answer goes into this file and deletes its question there and here)

1. Supabase Auth for Google, or our own OAuth client? (Recommendation: Supabase Auth.)
2. Render (suspend quota, is the worker free?) or an Oracle Always Free VM (ops)? (Recommendation: Render + Supabase + Upstash; VM if the suspend is unwelcome.)
3. Is one shared Higgsfield account for all users acceptable to Higgsfield's terms?
4. One shared Telegram bot, or one bot token per user?
5. For the hosted chat: a hosted LLM provider with a monthly budget and a shown price, or self-hosted weights?
6. Is `out/` untracked in the public repo, and is the pre-scrub history kept offline as the backup?
7. Which IP retention: 7, 30 or 90 days?
8. Do the Studio's screens ship to the public deployment, or does the public API serve only the Mirsal app?
9. Do the two new tables live in the same Supabase project as the mirror, or a separate one?
