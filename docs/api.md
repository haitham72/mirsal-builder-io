# HTTP API

All JSON, served by `python -m mirsal serve` (FastAPI on uvicorn, `127.0.0.1:8770`; `console/app.py`). **Every route below is served by an adapter over the original handler, so its answer is byte-identical to the stdlib server** (`serve --stdlib` / `MIRSAL_SERVER=stdlib` still runs that one); new routes are native FastAPI with pydantic models. An open stream (the generation events) is framed as chunked on HTTP/1.1 (the stdlib server closed the connection instead): the event bytes are the same. **The Studio is a sandbox over this API** (CLAUDE.md rule 11): every feature is an
engine function and a stable JSON shape first, a screen second, so the existing Mirsal app can call the same routes. Everything is addressable by id
(generation `12` in a URL and `G012` in `result.json` and the chat, sticker `G012/S3`, job `J004`, session `S002`, video sheet `A1`).

## Sections

This is an index: each section is its own file under [`api-parts/`](api-parts/); read only the one a task needs.

| section | what it covers |
|---|---|
| [Safety on every request](api-parts/01-safety-on-every-request.md) | Host / Origin guard: the Host header must be this server's own (`127.0.0.1`, `localhost`, `[::1]` with its port), and on anything that is not a read a brow… |
| [Accounts (`runtime/users.py`, `console/server.py` `_who` / `_authorize`)](api-parts/02-accounts-runtime-users-py-console-server-py-who.md) | `mirsal user add NAME [--owner] [--spend] / list / disable ID / enable ID / rotate ID / allow-spend ID / deny-spend ID` (or the routes below) manages `out/us… |
| [Contract](api-parts/03-contract.md) | `GET /api/openapi.json` is the machine-readable contract (OpenAPI 3.1; `console/openapi.py` is one hand-written table next to the server). `tests/test_openap… |
| [Chat (docs/agent-and-chat.md)](api-parts/04-chat-docs-agent-and-chat-md.md) |  |
| [Generations, gates and animation (docs/engine-and-studio.md, docs/generation.md)](api-parts/05-generations-gates-and-animation-docs-engine-and.md) | `GET /api/generations` (list) · `GET /api/generations/{id}` (full snapshot: `result.json` + events + `problem`: the plain-words reason when the sheet was blo… |
| [Events (SSE)](api-parts/06-events-sse.md) | `GET /api/ai` (the active AI backend, the person's choice and what is available) · `POST /api/ai/backend {backend?: auto / local / cloud, model?: <id>}` (own… |
| [Files](api-parts/07-files.md) | `GET /out/{path}` serves a generated file. The path is resolved first (`..`, `%2e%2e` and links included) and everything is decided on the RESOLVED file: it… |
| [Library, packs, Telegram, projects, search, health](api-parts/08-library-packs-telegram-projects-search-health.md) | `GET /api/generations/{id}/export.zip` (the Studio's Download .zip: the batch's accepted stickers, animated where ready, renamed to the export contract `{emo… |
| [Export to the AddCollection API (native FastAPI; `services/collection.py`)](api-parts/09-export-to-the-addcollection-api-native-fastapi-s.md) | The Mirsal Creator API's "Submit a Pack for Approval", an external emoji CMS (`docs/Api/AddCollection-API .md`): the collection goes into its approval workfl… |
| [Office accounts on the LAN (native FastAPI, `console/app.py`; `runtime/users.py`, `flow/people.py`, `services/admin_bot.py`)](api-parts/10-office-accounts-on-the-lan-native-fastapi-consol.md) | `python -m mirsal serve --lan` serves the office network (0.0.0.0) with HTTPS (`out/tls/cert.pem` + `key.pem` made once with mkcert, certificate-guide.md, or… |
| [Trending (native FastAPI; `flow/trending.py`)](api-parts/11-trending-native-fastapi-flow-trending-py.md) | Public packs everyone signed in and approved can open, like, comment on and copy (state in `out/trending.json`, git-ignored). `GET /api/trending?order=trendi… |
| [Tickets (native FastAPI; `flow/tickets.py`, docs/store-and-search.md "Tickets")](api-parts/12-tickets-native-fastapi-flow-tickets-py-docs-stor.md) | `GET /api/tickets?status=` -> `{tickets: [...]}` (the owner sees every ticket, a member their own); `GET /api/tickets/{id}` -> the whole ticket (404 for anot… |
| [Help & Support (native FastAPI; `flow/support.py`, `flow/faq.py`, `flow/notifications.py`; docs/agent-and-chat.md "Support")](api-parts/13-help-support-native-fastapi-flow-support-py-flow.md) | Every route also answers under `/api/v1/`. A body that does not match answers `400 {"error": "bad request: ..."}`. Another person's conversation, ticket, scr… |
| [Not built yet](api-parts/14-not-built-yet.md) | See `docs/backlog.md` (API and production). |
| [Hosted mode (branch `deployment`)](api-parts/15-hosted-mode-branch-deployment.md) | With `MIRSAL_GATEWAY_SECRET` set (32+ characters) the engine listens on loopback and trusts exactly one front door, `deploy/gateway` (FastAPI): a request tha… |
| [Trash and purge (owner only; `flow/purge.py`, `store/purge_rows.py`, `media/library.py`, `flow/batches.py`)](api-parts/16-trash-and-purge-owner-only-flow-purge-py-store-p.md) | Remove batch, Delete pack (soft since 2026-10-03: `POST /api/packs/{id}/delete` moves the pack to `trash.packs` in library.json, files untouched, answers… |
| [Particle effects (`/api/effects`, `docs/effects.md`)](api-parts/17-particle-effects-api-effects-docs-effects-md.md) | Owner only for now. `GET /api/effects` (list) · `POST /api/effects {pack_id, sticker_ids / "all", mode: "video" / "sim", grid: "2x2" / "3x3", note?, allow_vl… |
| [Reaction sets (`/api/particles`, `docs/reaction.md`)](api-parts/18-reaction-sets-api-particles-docs-reaction-md.md) | Particle sets (`P###`, `out/particles/P###/`) belong to library stickers through `owner:[{pack_id,sticker_id,generation,index}]`. `packs[]` and `used_in[… |
| [Edits and the AI (2026-10-03, UI/UX spec P8-P13)](api-parts/19-edits-and-the-ai-2026-10-03-ui-ux-spec-p8-p13.md) | `POST /api/generations/{id}/edit {index, png}` (and the animated `studio_edit` commit) now also answers `sheet_fixed: {file, cells}` (or null): the batch's s… |
| [Import an existing sheet or video (native FastAPI)](api-parts/20-import-an-existing-sheet-or-video-native-fastapi.md) | The Studio offers Use my own sheet and Import from Higgsfield to the owner. These routes never generate or spend credits and also have `/api/v1/` ali… |
| [Expanded emoji resolution and LLM selection](api-parts/21-expanded-emoji-resolution-and-llm-selection.md) | ZIP manifest v1 assets carry `bank_version`; unresolved assets also carry `resolution_reason` (`unmapped`, `ambiguous_alias`, `invalid_emoji`) and canonical… |
