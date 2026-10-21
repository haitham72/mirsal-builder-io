# docs/api-integration.md — the HTTP contract and the outside world

All JSON, served by `python -m mirsal serve` (FastAPI on uvicorn, `127.0.0.1:8770`). Every route below is served by an adapter over the original handler, so its answer is byte-identical to the stdlib server (`serve --stdlib` still runs that one); new routes are native FastAPI with pydantic models. **The Studio is a sandbox over this API** (rule 11): every feature is an engine function and a stable JSON shape first, a screen second. Everything is addressable by id (generation `12` in a URL and `G012` in `result.json` and the chat, sticker `G012/S3`, job `J004`, session `S002`, video sheet `A1`).

Converged 2026-10-21 (branch `code-audit`); it supersedes the former `docs/api.md`, `docs/api-parts/`, the frozen `docs/http_route_inventory.md`, `docs/Api/AddCollection-API .md` and the draft `docs/integration/API_DOCUMENTATION.md`. Full text of all of them lives in git history.

## Contract

- JSON only, `GET` + `POST` only (anything else is 501). Every route also answers under `/api/v1/`.
- Every answer carries `X-API-Version` + `X-Request-Id` (1–64 `[A-Za-z0-9._-]`), including 500s. A body that does not match answers `400 {"error": ...}` — never 422.
- **The live route inventory is `GET /api/openapi.json`** (OpenAPI 3.1, one hand-written table in `mirsal/mirsal/api/openapi.py`, guarded both ways by `tests/test_openapi.py`). This doc names families and rules, never the full route list.
- `GET /out/{path}` serves a generated file: the path is resolved first and everything is decided on the RESOLVED file (it cannot escape `out/`). Signed asset links (`/api/assets/sign` → `/api/assets/{token}`) are HMAC, expiring, 403 when forged.
- Native transport: `api/app.py` `create_app` + 10 domain routers, `api/dependencies.py` guards, `api/schemas/` models, `api/legacy_adapter.py` last.

## Guards on every request

- Host must be this server's own (`127.0.0.1`/`localhost`/`[::1]` + port); on non-reads a browser Origin / `Sec-Fetch-Site` must be ours too, else 403.
- Sign-in: owner/member token (`Authorization: Bearer`), the page's same-origin fetch, cookie session on LAN, or the open sandbox. Owner/member/pending roles; **404-not-403 privacy** (a stranger's batch/pack/session is "not found", even to the owner on Library reads). Pending accounts get 403 "waiting for approval" almost everywhere.
- Rate limits: 240 writes / 3000 reads per minute per token holder + `Retry-After` (health/events exempt). `Idempotency-Key` answers kept 24h (generations, live sheet/video, chat messages). `allow_vlm` 409-consent gates the judge/captions. One `.writer.lock` per `out/` for `result.json`.

## Accounts

`mirsal user add NAME [--owner] [--spend] / list / disable / enable / rotate / allow-spend / deny-spend` over `out/users.json` (SHA-256 `mk-` tokens, shown once). Routes: `/api/me`, `/api/users` CRUD. Per-batch/session/job ownership stamps; `can_spend` gates paid buttons.

## Route families

Generations + gates (`more`/`regen`/`review`/`drop`/`allow`/`video_sheet`/`quick_sheet`/`animate`/`add`, resize/position/keep_size, prepared sheets, batch families, job recovery Refresh/Check/Continue/Dismiss/retry); chat (sessions/messages + `stream` SSE, settings incl. `allow_vlm`); live sheet/video/cost/refs; Library + packs (export.zip, Telegram send once/replace/new_set, merge, cutout, projects); effects (`/api/effects` analyse/plan/estimate/render/add) and reaction sets (`/api/particles` lifecycle + Echo lookup + bank/lottie/preset families); imports (raw bytes + grid detect/override, Higgsfield history/import, ticket dedup); Trending (share/unshare/like/comment/use-copy, 5-day half-life, orders trending/new/liked); tickets; Help & Support (conversations/escalate/forget/feedback, notifications, staff queue/reply/resolve, FAQ lifecycle); files, search, jobs, tasks/Inbox, usage, watch, prefs, health/metrics, LLM catalog.

## Files out: export.zip

`{emoji}-{slug}-{tag}-{sNN}-{G###}-{date}` + `manifest.json` v1; animations compressed small by default (`?light=0` keeps full size; each row records crf/kb/frames/fps/fits); `?retime=1` stretches sub-3s clips to 3s (`retimed_from` on the row); grey `_grey.png` stand-ins ride along. Manifest v1 assets carry `bank_version`; unresolved assets carry `resolution_reason` + canonical candidates; resolutions persist in `out/export_resolutions.json`. Short public codes, the claim ledger wiring and the exporter bank picker are open (backlog).

## Export to collection (the Mirsal Creator CMS)

A pack or one Studio batch sent, as its Download .zip holds it, to the external CMS's "Submit a Pack for Approval" (`POST {base}/api/v1/Upload/AddCollection`, multipart). What Mirsal sends is exactly the zip's stickers in its order — the manifest is read back, so the two exports can never disagree.

| CMS field | value |
|---|---|
| `CollectionName` | pack/batch name, **≤40 chars** (400 with a sentence before anything uploads; the dialog offers a word-cut name) |
| `Description` | **≤160 chars**; empty = the name |
| `ContentSubType` | `webm` for animated packs (and mixes), else the stills' own type (`png`/`webp`) |
| `Media` | once per asset (`.webm`/`.png`/`.webp`), in order |
| `MediaThumbnails` | one PNG per asset, **same order, paired by index** (`.png` as is, `.webp` converted, `.webm` grey silhouette = the zip's `{stem}_grey.png`) |
| `MediaMetadata` | ONE JSON string `[{emoji_utf, tags}]`, same length, paired by index (`emoji_utf` = first grapheme cluster, `tags` = action tokens joined by `_`, never empty, fallback `sticker`) |

Auth: `MIRSAL_COLLECTION_API_CREDENTIALS` = `sk-…` developer key (Bearer; a legacy `user:password`/base64 still sends Basic). URL: `MIRSAL_COLLECTION_API_URL` (default `https://emojicms.ehub.ae`). Answers: `{Success, Result, ErrorMessages}` — a 2xx with `Success: false` is a refusal (words from `ErrorMessages`, list joined with `; `, else `message`/validation answer/status); 401 = bad key with replacement instructions; `Result` passthrough on success. Every export is a line in `out/collection_exports.jsonl`, never the key. Keys: CMS Developer Keys page → generate → `mirsal/.env` only → restart; a lost/leaked key is deleted there and replaced.

Mirsal's side (owner only, sender-scoped reads, all under `/api/` and `/api/v1/`): `POST /api/packs/{id}/export-collection` and `POST /api/generations/{id}/export-collection` (`{name?, description?, retime?, light?}`) answer `202 {id, state: queued, position}` at once — one worker builds the zip and sends it (`queued → preparing → sending → done|failed`); `GET /api/collection/exports/{xid}` gives the outcome; `GET /api/collection` gives `{configured, url}`. A restart turns unfinished exports `failed`. The sender is notified.

## Events (SSE)

`GET /api/generations/{id}/events` and the chat stream send turn/done events as chunked JSON (`Last-Event-ID` / `?after=` replay). Same bytes on both servers.

## Office LAN

`serve --lan` serves 0.0.0.0 over HTTPS (`out/tls/cert.pem` + `key.pem`, or `MIRSAL_TLS_CERT/KEY`; `--no-tls` escapes). Sign-up with an allowed-domain email (`MIRSAL_EMAIL_DOMAIN`, default `nadi.ae,cpd.gov.ae`), approval in Users > People (+ the Telegram admin bot mirror), HttpOnly Strict cookie sessions, per-person credits with reserve/settle (402 when short). The LAN PC must stay on. Users dashboard aggregates spend/work per person. Rate limiting and Google OAuth stay parked.

## Trying the integration (owner)

```
# mirsal/.env (never in git):
MIRSAL_COLLECTION_API_URL=https://emojicms.devinprocess.com
MIRSAL_COLLECTION_API_CREDENTIALS=sk-...
python -m mirsal serve                      # restart to load .env
curl -H "Authorization: Bearer <owner-token>" localhost:8770/api/collection
# {"configured":true,"url":"..."} — then export one pack:
curl -X POST -H "Authorization: Bearer <owner-token>" -H "Content-Type: application/json" \
  -d '{"name":"My Pack","description":"test"}' localhost:8770/api/packs/<pid>/export-collection
# {"id":"X...","state":"queued",...} — poll it:
curl -H "Authorization: Bearer <owner-token>" localhost:8770/api/collection/exports/X...
```

A fake CMS covers this in `tests/test_collection.py` (multipart pairing by index, queue lifecycle, restart-failure, both servers). Open CMS questions for Haitham: comma- vs underscore-joined tags acceptance, whether `Price` is ignored or rejected, per-collection caps, the full `ContentSubType` set, what `Result` holds — code + the CMS doc above are the only oracles so far.
