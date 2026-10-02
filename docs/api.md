# HTTP API

All JSON, served by `python -m mirsal serve` (stdlib server, `127.0.0.1:8770`). **The Studio is a sandbox over this API** (CLAUDE.md rule 11): every feature is an
engine function and a stable JSON shape first, a screen second, so the existing Mirsal app can call the same routes. Everything is addressable by id
(generation `G012`, sticker `G012/S3`, job `J004`, session `S002`, video sheet `A1`).

## Safety on every request

- **Host / Origin guard**: the Host header must be this server's own (`127.0.0.1`, `localhost`, `[::1]` with its port), and on anything that is not a read a browser-sent
  `Origin` must be its own and `Sec-Fetch-Site` must not be cross-site. A web page the owner visits cannot POST to the server; a client that sends no `Origin` (curl, the
  tests, the CLI) passes. Refusals are `403`.
- **Accounts** (below): with no account and no `MIRSAL_API_TOKEN` the local sandbox is open exactly as before; once one account exists every caller that is not the Studio's own
  page must send `Authorization: Bearer <token>` (`401` otherwise).
- **Rate limits**: a token holder gets 240 writes and 3000 reads a minute (`MIRSAL_RATE_WRITE`, `MIRSAL_RATE_READ`; `0` switches one off); over it the answer is `429` with `Retry-After`
  (seconds). Health checks and event streams are exempt, and the open sandbox and the owner's own page are never limited (the Studio polls a lot). Counters live in Redis (or in memory
  without it), one per user, per minute.
- **One writer of `result.json`** per `out/` across processes (`.writer.lock`): the server and the CLI commands that write results refuse to run together.
- **Idempotency**: `POST /api/generations` and `POST /api/chat/sessions/{id}/messages` accept `Idempotency-Key`; the same key within 24 h returns the first answer with
  `"idempotent": true` and runs nothing again.
- Errors are `{"error": "..."}` with the HTTP status that says why (400 bad input, 401, 403, 404, 409 busy or wrong state, 413 too large, 503 provider missing).

## Accounts (`users.py`, `console/server.py` `_who` / `_authorize`)

`mirsal user add NAME [--owner] [--spend] | list | disable ID | enable ID | rotate ID | allow-spend ID | deny-spend ID` (or the routes below) manages `out/users.json`. A token
(`mk_…`) is shown **once** and only its SHA-256 is stored; it is compared in constant time. Authentication stays on once any account exists, even a disabled one (disabling the
only account must never open the server: delete `out/users.json` on purpose to go back).

- **Who is calling**: a user token is that user (checked first, so a client cannot widen itself by also sending `Sec-Fetch-Site`); the Studio's own page (`Sec-Fetch-Site: same-origin`)
  and `MIRSAL_API_TOKEN` are the implicit owner `local`. The page's own files (`/`, `/ui/…`, `/assets/…`) and a signed link need no header: they hold no data / the link is the credential.
  *A reverse proxy in front of the server must strip `Sec-Fetch-Site` from outside requests*, because that header is what marks the page.
- **Roles**: an `owner` sees and does everything. A `member` reaches only the chat, search, `GET /api/me`, health, the OpenAPI document and **what they own**: their chats, the
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

`GET /api/openapi.json` is the machine-readable contract (OpenAPI 3.1; `console/openapi.py` is one hand-written table next to the server, and `tests/test_openapi.py` fails when a route exists in the
server that the table does not describe). `python -m mirsal openapi [--json FILE] [--ts FILE]` writes it and TypeScript types for the app.

## Chat (docs/agent-and-chat.md)

| route | |
|---|---|
| `GET /api/chat/agent` | which model runs the assistant and the vision judge, and whether live generation is available |
| `GET /api/chat/sessions` · `POST /api/chat/sessions {title?, settings?}` | list · create |
| `GET /api/chat/sessions/{id}` | the whole session for display: messages with steps and cards (each generation card carries its live stickers with file urls, or its job state), subjects with their passes, settings, `working`, `summary_text` |
| `POST /api/chat/sessions/{id}/messages {text, selected?, action?}` | start a turn in the background (`202`); `action` is `{type: "confirm" | "cancel"}`; `409` while the last turn is still running |
| `POST /api/chat/sessions/{id}/settings {grid?, ask_before_spending?, ai?, style_id?}` | the two visible settings (and two quiet ones) |
| `POST /api/chat/sessions/{id}/delete` | delete the chat (its stickers stay) |

## Generations, gates and animation (docs/engine-and-studio.md, docs/generation.md)

`GET /api/generations` (list) · `GET /api/generations/{id}` (full snapshot: `result.json` + events) · `POST /api/generations {prompt, variant?, outline?, erode?}` ·
`POST /api/generations/{id}/…`: `more`, `regen`, `review {gate, decision, index?, note?}`, `drop`, `allow`, `video_sheet`, `quick_sheet`, `animate`, `add`, `pack_add`, `edge`,
`appearance`, `reslice`, `recheck`, `edit`, `studio_edit`, `render`, `stickers`, `telegram`, `reveal`, `delete`, **`judge {scope: still | anim, force?}`** (the vision pre-review, `202`).
Live generation (Higgsfield): `POST /api/live/cost | sheet | video`, `POST /api/live/ref` (a reference image), `GET /api/jobs`, `GET /api/jobs/{id}`, `GET /api/models`, `GET /api/higgsfield`
(credits), `GET /api/usage` (the ledger roll-up). The Inbox: `GET /api/inbox`, `POST /api/plan`, `GET/POST /api/tasks`.

## Events (SSE)

`GET /api/generations/{id}/events` (`Last-Event-ID` or `?after=` to replay): `text/event-stream`, one frame per event, `id:` is the stream id.
Names: `generation_started, sheet_generated, sticker_processing, sticker_ready, sticker_failed, animation_started, animation_ready, video_sheet_ready, review_decided,
pack_complete, generation_failed`. Payload: `{event, generation_id, stage, status, ts, ms, actor?, decision?, gate?, index?, sticker_id?, asset_url?, trace_run_id?}`.

## Files

- `GET /out/{path}` serves a generated file (path checked against the root after resolving it, so a link or `..` cannot leave `out/`).
- **Signed links**: `POST /api/assets/sign {key, ttl?}` (a path under `out/` such as `G002/slices/….png`, ttl 5-3600 s) returns `{url, expires_in}`; `GET /api/assets/{token}`
  serves it until it expires. The token is an HMAC over key, user and expiry; an edited token is `403`.

## Library, packs, Telegram, projects, search, health

`/api/library`, `/api/packs…` (create, rename, reorder, export `.wastickers`, send to Telegram), `/api/stickers/delete`, `/api/cutout`, `/api/projects…` (video / GIF projects),
`/api/telegram…` (status, config, disconnect; the token is never returned), `GET /api/search?q=` (Postgres when the database is up, else files),
`/api/watch…` (the watch folders: list, remove to the trash, restore, purge), `GET /api/history` (every batch, newest edit first).

**Health** (every dependency reports itself; nothing raises): `GET /api/health` (database with write-through counters, Redis engine, models, providers, storage, the job queue's mode and counts),
`/api/health/models`, `/api/health/storage`, `GET /api/vision`.

## Not built yet

Postgres as the durable idempotency backstop. See `HANDOFF.md`.
