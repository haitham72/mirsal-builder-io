# HTTP API

All JSON, served by `python -m mirsal serve` (stdlib server, `127.0.0.1:8770`). **The Studio is a sandbox over this API** (CLAUDE.md rule 11): every feature is an
engine function and a stable JSON shape first, a screen second, so the existing Mirsal app can call the same routes. Everything is addressable by id
(generation `12` in a URL and `G012` in `result.json` and the chat, sticker `G012/S3`, job `J004`, session `S002`, video sheet `A1`).

## Safety on every request

- **Host / Origin guard**: the Host header must be this server's own (`127.0.0.1`, `localhost`, `[::1]` with its port), and on anything that is not a read a browser-sent
  `Origin` must be its own and `Sec-Fetch-Site` must not be cross-site. A web page the owner visits cannot POST to the server; a client that sends no `Origin` (curl, the
  tests, the CLI) passes. Refusals are `403`.
- **Accounts** (below): with no account and no `MIRSAL_API_TOKEN` the local sandbox is open exactly as before; once one account exists every caller that is not the Studio's own
  page must send `Authorization: Bearer <token>` (`401` otherwise).
- **Rate limits**: a token holder gets 240 writes and 3000 reads a minute (`MIRSAL_RATE_WRITE`, `MIRSAL_RATE_READ`; `0` switches one off); over it the answer is `429` with `Retry-After`
  (seconds). Health checks and event streams are exempt, and the open sandbox and the owner's own page are never limited (the Studio polls a lot). Counters live in Redis (or in memory
  without it), one per user, per minute.
- **Versioning and tracing**: every route is also served under `/api/v1/...` (pin it before anything changes); every answer carries `X-API-Version` (the OpenAPI document's version) and `X-Request-Id` (your own `X-Request-Id`, when it is 1-64 of `A-Za-z0-9._-`, is echoed; otherwise a fresh one). An internal `500` includes the `request_id`, and the console line carries it. `MIRSAL_ACCESS_LOG=1` prints one JSON line per request on the server's stderr (`ts, request_id, method, path, status, ms, user, via, generation_id?, session_id?`; never the query string).
- **Pagination** is opt-in: `GET /api/generations`, `/api/jobs` and `/api/chat/sessions` take `?limit=1-500&offset=N` and then add `{total, limit, offset}`; without either, the whole list comes back as before (`400` for a bad value; an offset past the end is an empty page). A `429` is `Cache-Control: no-store`. The event stream starts with `retry: 3000`.
- **One writer of `result.json`** per `out/` across processes (`.writer.lock`): the server and the CLI commands that write results refuse to run together.
- **Idempotency**: `POST /api/generations` (both forms), `POST /api/live/sheet | video` (the routes that spend credits) and `POST /api/chat/sessions/{id}/messages` accept `Idempotency-Key`; the same key within 24 h
  returns the first answer with `"idempotent": true` and runs nothing again. Without a key nothing is compared. The cache (Redis, or memory when it is down) answers first; the answer is also kept for 24 h in Postgres (`idempotency_keys`, migration 008, `store/idem.py`: the key hashed, scoped by route and caller, the first answer wins), so a restart without Redis does not forget it. Like every write-through it only works for the real `out/` and never blocks the request.
- **AI vision needs consent in the request**: `POST .../judge` and `POST .../captions` answer `409 {error, consent_required: true}` and send nothing unless the body carries `allow_vlm: true` (the person's yes, asked once: `vision/consent.py`). Reading stored captions needs none. The chat session setting is `allow_vlm` (`null` until asked).
- Errors are `{"error": "..."}` with the HTTP status that says why (400 bad input, 401, 403, 404, 409 busy or wrong state, 413 too large, 503 provider missing), **always JSON**: an unexpected exception is a `500 {"error": "internal error"}` (the detail goes to the server console with absolute paths scrubbed, never into the answer), an unsupported method is a JSON `501`, and a URL the server does not serve is `404 {"error": "no such route"}` (a missing batch, pack or job says so in its own words).

## Accounts (`runtime/users.py`, `console/server.py` `_who` / `_authorize`)

`mirsal user add NAME [--owner] [--spend] | list | disable ID | enable ID | rotate ID | allow-spend ID | deny-spend ID` (or the routes below) manages `out/users.json`. A token
(`mk_…`) is shown **once** and only its SHA-256 is stored; it is compared in constant time. Authentication stays on once any account exists, even a disabled one (disabling the
only account must never open the server: delete `out/users.json` on purpose to go back).

- **Who is calling**: a user token is that user (checked first, so a client cannot widen itself by also sending `Sec-Fetch-Site`); the Studio's own page (`Sec-Fetch-Site: same-origin`)
  and `MIRSAL_API_TOKEN` are the implicit owner `local`. The page's own files (`/`, `/ui/…`, `/assets/…`) and a signed link need no header: they hold no data / the link is the credential.
  *A reverse proxy in front of the server must strip `Sec-Fetch-Site` from outside requests*, because that header is what marks the page.
- **Roles**: an `owner` sees and does everything. A `member` reaches only the chat, search, `GET /api/me`, `GET /api/health` (not `/api/health/models` or `/api/health/storage`), the OpenAPI document and **what they own**: their chats, the
  batches they started (and those batches' files, events, jobs and links) and the actions on them (`review, more, regen, animate, video_sheet, quick_sheet, drop, allow, judge, appearance,
  edge, reslice, recheck`). A stranger's chat, batch, job or file is **`404`** (never a `403` that says it exists). Everything else is owner-only (`403`): the library, packs, projects,
  Telegram, watch folders, tasks, usage and credits, the operator's job actions, `files` / `reveal` / `add` on a batch, and the user list.
- **Spending**: live generation (`POST /api/live/sheet | video`, and the chat's Create / Animate on the live path) needs `can_spend`, because it spends the owner's Higgsfield credits; the check
  comes before anything about the provider is revealed. A member never sees the owner's balance.
- **Ownership** is stamped on the batch at creation (`result.json` `owner`, `generations.owner`), on the chat (`sessions.user_id`) and on the job (`request.user`), so a sheet that comes back
  minutes later still belongs to whoever asked for it. A chat turn runs in a thread and acts as its user.

| route | |
|---|---|
| `GET /api/me` | `{id, name, role, can_spend, via}` for the caller (`via`: `token`, `page`, `open`) |
| `GET /api/users` · `POST /api/users {name, role?, can_spend?}` | owner only; the create answer is `{user, token}` (the only time the token is visible) |
| `POST /api/users/{id}/update {name?, role?, can_spend?}` · `disable` · `enable` · `rotate` | owner only; `rotate` answers `{user, token}` and the old token stops working at once |

Not per user yet: the library and packs (owner-only; per-user packs wait for the app's pack curation) and reference images (`out/refs/R###`, shared by id).

## Contract

`GET /api/openapi.json` is the machine-readable contract (OpenAPI 3.1; `console/openapi.py` is one hand-written table next to the server). `tests/test_openapi.py` guards it **both ways**: it fails when a route exists in the
server that the table does not describe, and it calls every documented operation on a scratch server and fails when one answers `no such route`. `python -m mirsal openapi [--json FILE] [--ts FILE]` writes it and TypeScript types for the app.

## Chat (docs/agent-and-chat.md)

| route | |
|---|---|
| `GET /api/chat/agent` | which model runs the assistant and the vision judge, whether live generation is available, what is available (`availability.local.ok` is a REAL readiness probe: one tiny chat completion, cached 60 s / 15 s, with `why` in plain words when the model cannot answer), `agent_status: {fallback, reason}` (`fallback: true` = the chat is on its rules only, and why) and the style presets (`styles`, `default_style`) the AI screen shows |
| `GET /api/llm/models` | the local server's chat models for the model dropdown (member-readable): `{models: [{id, loaded: null \| bool}], current, preference, chosen, configured, ok, why}`. `models` is `GET {MIRSAL_LOCAL_URL}/models` without the embedding models, in the server's order (cached 30 s; `[]` when the server is down); `current` is the id every local call sends (the person's pick, else `MIRSAL_LOCAL_MODEL`, else it without a `:N` instance suffix, else the first listed model); `loaded` is `true` for the model the probe just heard from, else `null`; `ok` / `why` are the probe (`why` is `null` when it answers). `/api/models` is the Higgsfield catalogue, not this |
| `GET /api/chat/sessions` · `POST /api/chat/sessions {title?, settings?}` | list · create |
| `GET /api/chat/sessions/{id}` | the whole session for display: messages with steps and cards (each generation card carries its live stickers with file urls, or its job state), subjects with their passes, settings, `working`, `summary_text` |
| `POST /api/chat/sessions/{id}/messages {text, selected?, action?}` | start a turn in the background (`202`); `action` is `{type: "confirm" | "cancel"}`; `409` while the last turn is still running |
| `POST /api/chat/sessions/{id}/settings {grid?, ask_before_spending?, ai?, style_id?}` | the visible settings (grid, ask before spending, style) and two quiet ones; a `style_id` that is not one of the presets is a 400 `unknown style`, nothing is stored |
| `POST /api/chat/sessions/{id}/delete` | delete the chat (its stickers stay) |

## Generations, gates and animation (docs/engine-and-studio.md, docs/generation.md)

`GET /api/generations` (list) · `GET /api/generations/{id}` (full snapshot: `result.json` + events + `problem`: the plain-words reason when the sheet was blocked, else null) · `GET /api/generations/{id}/captions` (the stored AI caption of every cell, read-only) · `POST /api/generations/{id}/captions {allow_vlm: true, force?}` (writes the missing ones in the background) · `GET /api/generations/{id}/history[?index=N]` (every sticker's generation history, decisions grouped by stage in the order they happened, newest line first, trimmed to readable facts: `flow/sticker_history.py`; a member sees only their own batch) · `POST /api/generations {prompt, variant?, outline?, erode?}` ·
`POST /api/generations/{id}/…`: `more`, `regen`, `review {gate, decision, index?, note?}`, `drop`, `allow`, `video_sheet`, `quick_sheet`, `animate`, `add`, `pack_add`, `edge`,
`appearance`, `reslice`, `recheck`, `edit`, `studio_edit`, `reveal`, **`judge {scope: still | anim, force?}`** (the vision pre-review, `202`); an unknown batch is a `404` before anything starts. A batch is removed from the Studio through `/api/watch/remove` (to the trash); there is no `delete`, `render`, `stickers` or `telegram` on a generation (the pack routes below do those).
Live generation (Higgsfield): `POST /api/live/cost | sheet | video`, `POST /api/live/ref` (a reference image), `GET /api/jobs`, `GET /api/jobs/{id}`, the operator's `POST /api/jobs/{id}/claim | done | fail | requeue` and a human's `retry` (owner only; `requeue` / `retry` of a job that holds a provider ticket wait for the same provider job), `GET /api/models`, `GET /api/higgsfield`
(credits), `GET /api/usage` (the ledger roll-up). The Inbox: `GET /api/inbox`, `POST /api/plan`, `GET/POST /api/tasks`.

## Events (SSE)

`GET /api/ai` (the active AI backend, the person's choice and what is available) · `POST /api/ai/backend {backend?: auto | local | cloud, model?: <id>}` (owner only; `model` must be one of the ids `GET /api/llm/models` lists, else `400 {error, models: [...]}` and nothing is saved; both are kept in `out/ai_backend.json`, a call with neither is a 400; the answer is `GET /api/ai`'s) · `GET /api/generations/{id}/events` (`Last-Event-ID` or `?after=` to replay): `text/event-stream`, one frame per event, `id:` is the stream id.
Names: `generation_started, sheet_generated, sticker_processing, sticker_ready, sticker_failed, animation_started, animation_ready, video_sheet_ready, review_decided,
pack_complete, generation_failed`. Payload: `{event, generation_id, stage, status, ts, ms, actor?, decision?, gate?, index?, sticker_id?, asset_url?, trace_run_id?}`.

## Files

- `GET /out/{path}` serves a generated file. The path is resolved first (`..`, `%2e%2e` and links included) and everything is decided on the RESOLVED file: it must stay inside `out/`, and a member may read it only when it lies inside a batch folder they own (`out/users.json` or `out/telegram.json` are never reachable, however the URL is spelled).
- **Signed links**: `POST /api/assets/sign {key, ttl?}` (a path under `out/` such as `G002/slices/….png`, ttl 5-3600 s) returns `{url, expires_in}`; `GET /api/assets/{token}`
  serves it until it expires. The token is an HMAC over key, user and expiry; an edited token is `403`.

## Library, packs, Telegram, projects, search, health

`/api/library`, `/api/packs…` (create, rename, reorder, send to Telegram, `GET /api/packs/{id}/export.zip` to download the pack as a zip: the files as stored, `.webm` / `.png` / `.webp`, plus `manifest.json`; `GET /api/packs/{id}/telegram.zip` is the same files renamed with `@stickers` instructions, `POST /api/packs/{id}/stickers/{sid}/move {to}` for one sticker), `/api/stickers/move {to, items}` (bulk, all or nothing) and `/api/stickers/delete`, `/api/cutout`, `/api/projects…` (video / GIF projects),
`/api/telegram…` (status, config, disconnect; the token is never returned), `GET /api/search?q=` (Postgres when the database is up, else files),
`/api/watch…` (the watch folders: list, remove to the trash, restore, purge), `GET /api/history` (every batch, newest edit first, a page at a time: each item carries `grid: [rows, cols]` and `cells: [{index, row, col, png, status, animated}]`, so a card draws the sheet's own 3x3 / 2x2 as it was cut).

**Health** (every dependency reports itself; nothing raises): `GET /api/health` (database with write-through counters, Redis engine, models, providers, storage, the job queue's mode and counts),
`/api/health/models`, `/api/health/storage`, `GET /api/vision`. **Metrics**: `GET /api/metrics` (owner only; `python -m mirsal metrics` prints it): from what is already on disk, the time from a batch's request to its first cut sticker (median, p90, max), the share approved of the stickers a human decided at G2 (stills) and G4 (animations), the share of batches that are a redo, batches with no sticker, and one line per batch (`flow/metrics.py`).

## Not built yet

See `HANDOFF.md`.

## Hosted mode (branch `deployment`)

With `MIRSAL_GATEWAY_SECRET` set (32+ characters) the engine listens on loopback and trusts exactly one front door, `deploy/gateway` (FastAPI): a request that carries `X-Mirsal-Gateway-Secret`, comes from loopback and names a well-formed `X-Mirsal-Subject` is that person, a `member` created on
first sight; every other request needs an API token as before (`runtime/users.py`). The gateway verifies the Google sign-in (a Supabase JWT, `Authorization: Bearer` or the `mirsal_session` cookie set by `POST /auth/session`), adds `GET /healthz`, `GET /readyz`, `GET /auth/config`, `GET /auth/me`,
`POST /auth/session`, `POST /auth/logout`, and passes everything else through unchanged (this contract, SSE included). It answers `401` without a valid sign-in, `429` with `Retry-After` over the rate limit (paid routes have their own, lower one), `403` for a cross-origin POST, `400` for an unknown Host.
Telegram: `POST /api/packs/{id}/telegram {name?, mode?}`, `mode` = `once` (default), `replace` or `new_set`; a pack whose exact content was already sent answers `already: true` with the earlier sets and never calls Telegram.
