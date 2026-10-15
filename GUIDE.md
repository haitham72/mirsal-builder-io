# Mirsal Builder — where everything happens (interview guide)

Flashy animated Telegram stickers. One deterministic engine (`mirsal/mirsal/engine/`), one free import/flow layer (`flow/`), two interfaces (AI chat, Studio web UI in `console/`). All code lives under `mirsal/mirsal/`; tests mirror it under `mirsal/tests/`.

## Layout in 30 seconds

| area | lives in | notes |
|---|---|---|
| Sticker engine (cut, key, render, verify) | `engine/` (`sheet.py`, `video.py`, `verify.py`, `ffmpeg.py`) | Pure + deterministic; never imports DB/LLM |
| Pipeline, gates, golden path | `flow/` (`pipeline.py`, `gates.py`, `imports.py`, `batches.py`) | Request → plan → sheet → stills → video → animations → pack |
| Web UI (Studio, Library, chat) | `console/` (`*.js`, `studio.css`, `index.html`) | No logic lives only in JS (rule) — every control posts to an API |
| HTTP routes | `console/app.py` (native FastAPI), `console/server.py` (legacy), `console/openapi.py` (contract), `console/app_models.py` (pydantic) | Route list: `docs/http_route_inventory.md` |
| Packs, stickers, files on disk | `media/` (`library.py`, `grey.py`) | `out/library/`, `out/G###-*/` |
| Paid generation (Higgsfield/Kling/jobs) | `generation/`, `services/llm*.py` | Every call logged to `out/model_calls.jsonl` |
| Telegram send, collection CMS send | `services/telegram.py`, `services/collection.py` | The only two backends that receive files |
| Postgres/search | `store/` | |
| Area docs (the real spec) | `docs/<area>.md` + section files | Engine+Studio, reactions, export, API parts… |

## The golden path (the spine of every demo)

Request → plan (G1) → sheet → stills (G2) → video sheet → video → animations (G4) → pack (G5). Batch folders: `out/G###-<slug>-<UTC>/` (`slices/`, `source/`, `result.json`, `prompts.json`). A human approves at every gate; blocks are technical-only or have a "Use it anyway".

## The Studio screen (what you click → where it posts)

- Batch header (Resize, Size, Download .zip, Export to collection): `studio-core.js` (`motionRow`, `ACT.gzipdl`, `ACT.colsend` via `packs.js`)
- Tiles + per-tile Size/X/Y sliders + Reset: `studio-core.js` (`vsizeRow`, `vslSend`, `ACT.vslreset`) → `POST /api/generations/{id}/position`
- Frame editor (grid/scrubber/Centre): `studio-core.js` (`vzCard`) → same `/position`, preview via `/anim_preview`
- Library / pack / Reactions tab / 3 reaction tabs: `library.js`, `packs.js`, `particles.js`, `reactions.js`, `lottiestyle.js`
- Import dialogs: `console/imports.js` → `POST /api/import` → `flow/imports.py` (no duplicate check: a used file is cut fresh)
- All action names are inventoried: `console/inventory.py` + `mirsal/tests/data/ui_baseline.json` (a removed action needs a `retired` entry or tests fail)

## Exports — "update the export field" recipes

**Download .zip (batch):** `flow/batches.py` `export_zip` builds `manifest.json` (`assets[]` per sticker + `grey[]`). **Pack zip:** same shape in `media/library.py` `export_zip`.
→ Per-sticker manifest field? Edit the row dicts in those two functions. Telegram/zip limits are checks in `engine/verify.py`, stage `telegram`.

**Grey stand-ins:** `media/grey.py` (`alpha_of` = animation's first visible frame, `grey_png` = #BFBFBF silhouette). One `{stem}_grey.png` beside every animation; listed under `grey`, never `assets`.

**Export to collection (the CMS):** `services/collection.py` — reads the zip's manifest, sends `Media` (files) + `MediaThumbnails` (PNG: sticker as-is, `.webm` → grey) + `MediaMetadata` (one JSON `[{emoji_utf, tags}]`, tags via `tags_of`). CMS reference: `docs/Api/AddCollection-API .md`. The CMS shows our thumbnail PNG at `user_media/Emoji_Assets/{emoji}.png` — so a wrong picture there means our `thumbnail()` sent it, not a CMS bug. Sends are queued (`enqueue` → background thread), state in `out/collection_exports/`, log in `out/collection_exports.jsonl`.

**Send to Telegram:** `services/telegram.py` (urllib, token from env/Settings, never logged).

**API shape change:** `console/app_models.py` (pydantic) + `console/openapi.py` (document it) + the area doc under `docs/api-parts/` + UI label in `console/*.js`.

## Finding anything fast

- Code: `rg <name>` from repo root (functions are unique-ish: `vsizeRow`, `export_zip`, `thumbnail`, `spLibHtml`).
- UI action → backend: search the `data-act=<name>` string, then `ACT.<name>` in the same file for its `post(...)` URL.
- Contract doubt? `docs/http_route_inventory.md` (every route) and `docs/api.md`.
- Behavior doubt? `docs/<area>.md` index → read only the section file you need. Design questions → `docs/design.md`.

## Run it

`mirsal/.venv` (Windows), server `python -m mirsal serve` (owner :8770 — don't disturb it; use your own `--port` + `MIRSAL_OUT=<copy>`). Providers off for checks: `MIRSAL_NO_REAL_CLI=1`, `MIRSAL_LLM_PROVIDER=none`. Tests: narrowest only (`mirsal test fast|focused|area <module>`); full `unittest discover` is retired.
