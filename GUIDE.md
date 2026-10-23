# Mirsal Builder — visual guide

> Flashy **animated Telegram stickers**. One deterministic engine, one flow layer,
> two interfaces (AI chat + Studio web UI). All code lives under `mirsal/mirsal/`;
> tests mirror it under `mirsal/tests/`.

---

## The big picture

```
                        ┌────────────── Studio web UI ──────────────┐
                        │  console/*.js + studio.css + index.html   │
                        │  (buttons only — every click posts to     │
                        │   an API; no logic lives in the browser)  │
                        └──────────────┬──────────────┬─────────────┘
                                       │              │
                        ┌──────────────▼──────────────▼─────────────┐
                        │            HTTP routes                     │
                        │  console/app.py  (native FastAPI)          │
                        │  console/server.py (legacy adapter)       │
                        │  console/openapi.py (the contract)        │
                        └──────────────┬──────────────┬─────────────┘
                                       │              │
              ┌────────────────────────▼──┐   ┌───────▼───────────────────┐
              │  FLOW  flow/              │   │  MEDIA  media/            │
              │  pipeline.py · gates.py  │   │  library.py (packs)       │
              │  imports.py · batches.py │   │  grey.py (silhouettes)    │
              │  golden path G1–G5       │   │  out/library, out/G###    │
              └────────────┬──────────────┘   └───────┬───────────────────┘
                           │                        │
              ┌────────────▼──────────────┐   ┌───────▼───────────────────┐
              │  ENGINE  engine/         │   │  BACKENDS  services/      │
              │  sheet · video · verify  │   │  telegram.py → Telegram  │
              │  ffmpeg · particles      │   │  collection.py → CMS      │
              │  pure + deterministic    │   │  (the only two receivers) │
              └──────────────────────────┘   └───────────────────────────┘

  Paid generation ── generation/ + services/llm*.py ──► every call logged
                                                        to out/model_calls.jsonl
  Postgres/search ── store/
```

---

## Repo map

```
mirsal/mirsal/
├── engine/        cut · key · render · verify · ffmpeg   (never imports DB/LLM)
├── flow/          pipeline · gates · imports · batches  (the golden path)
├── console/       Studio/Library/chat UI + routes + contract
│   ├── studio-core.js    batch header, tiles, sliders, frame editor
│   ├── studio-tiles.js   tile markup (what each tile shows)
│   ├── packs.js · library.js    packs, stickers, Reactions sections
│   ├── reactions.js · lottiestyle.js · particles.js    reaction screens
│   ├── live.js · composer.js     generation composer, job polling
│   ├── imports.js    import dialogs
│   ├── app.py · server.py · app_models.py · openapi.py    routes + contract
│   └── studio.css · theme.css · agent.css · index.html
├── media/         library.py (packs) · grey.py (silhouettes)
├── generation/    jobs · prompter · expander (paid calls)
├── services/      telegram.py · collection.py · llm*.py
├── store/         postgres, search, pool
└── runtime/       names.py (every filename), atomic writes, activity

mirsal/tests/     mirrors the above, plus tests/js/ (browser-less UI tests)
mirsal/out/       runtime data — batches, jobs, library, logs (never committed)
docs/             the real spec, one area per doc (see docs/<area>.md)
```

---

## A sticker's journey (the golden path)

```
 request ──► plan (G1) ──► sheet ──► stills (G2) ──► video sheet
     ──► video ──► per-frame check ──► animations (G4) ──► pack (G5)
```

| stage | happens in | stored in |
|---|---|---|
| Plan, prompt | `generation/prompter.py`, `flow/pipeline.py` | `out/G###-*/prompts.json` |
| Sheet + stills | `engine/sheet.py`, `flow/imports.py` (own files) | `out/G###-*/source/`, `slices/` |
| Video + animations | `engine/video.py` (ffmpeg VP9+alpha) | `out/G###-*/slices/*.webm` |
| Verdicts | `engine/verify.py` (44 checks, `OVERRIDABLE` vs `TECHNICAL`) | `result.json` + `reviews` rows |
| Human gates | Studio tiles, sheet cells, chat cards | `history` lines, never deletions |

Naming (never hand-build paths): batches `out/G###-<slug>-<UTC>/`, jobs
`out/jobs/J###-<subject>-<kind>.json`, media
`{media}-{subject}-{action}[-{pack}]-{UTC}-{hash}.{ext}` — all from
`runtime/names.py`, `pipeline.gen_dir`, `jobs.job_dir`.

---

## Studio → API wiring (click → post → backend)

| you click | in | it posts | backend |
|---|---|---|---|
| Resize / Size stepper | `studio-core.js` `motionRow` | `/resize`, `/video_size` | `flow/pipeline.py` |
| Tile Size / X / Y sliders, Reset | `studio-core.js` `vsizeRow` | `/position` + `/video_size`; Reset clears position without reslice then clears scale with one reslice | `flow/pipeline.py` |
| Frame editor Apply | `studio-core.js` `vzCard` | `/position` + `/anim_preview` (one-frame test) | same |
| Download .zip | batch header | `/generations/{id}/export.zip` | `flow/batches.py` |
| Export to collection | pack / batch menu | `/export-collection` (queued) | `services/collection.py` |
| Send to Telegram | pack screen | Telegram routes | `services/telegram.py` |
| Use my own sheet | import dialog | `/api/import` (raw bytes) | `flow/imports.py` — duplicates offer Open existing / Import again as a new batch, with grid-mismatch consent |
| Use it anyway (any rejected picture) | tile / sheet cell / chat card | `/generations/{id}/allow` | `engine/verify.py` catalogue |

Every `data-act=<name>` in markup has an `ACT.<name>` handler posting a URL —
search the action name to trace any click end to end. Removed actions must be
listed under `renamed`/`retired` in `mirsal/tests/data/ui_baseline.json`
(tests enforce it).

---

## Exports

```
 batch/pack ──► export_zip ──┬──► manifest.json ──► assets[] (stickers)
                             │                      grey[]   ({stem}_grey.png)
                             │
                             ├──► Download .zip ──► you / Telegram
                             │
                             └──► Export to collection ──► CMS
                                      Media           = the files
                                      MediaThumbnails = PNG (sticker as-is,
                                                        .webm → grey)
                                      MediaMetadata   = [{emoji_utf, tags}]
```

| piece | file | what to change when backend says "update the export field" |
|---|---|---|
| Zip manifest rows | `flow/batches.py` `export_zip` (batch), `media/library.py` `export_zip` (pack) | per-sticker fields |
| Grey PNG | `media/grey.py` (`alpha_of` → first visible frame, `grey_png` → #BFBFBF) | silhouette logic |
| CMS emoji/tags | `services/collection.py` (`tags_of`, `items_from_zip`, `thumbnail`) | metadata + thumbnail bytes |
| CMS reference | `docs/api-integration.md` | field docs |
| Telegram send | `services/telegram.py` | delivery |
| Size/codec/duration rules | `engine/verify.py` (stage `telegram`) | limits |
| API shape | `api/schemas/` + `api/routers/` + `console/openapi.py` + `docs/api-integration.md` + label in `console/ui/` | contract end to end |

> Debugging rule: the CMS shows **our** thumbnail PNG at
> `user_media/Emoji_Assets/{emoji}.png` — a wrong picture there means our
> `thumbnail()` sent it, never a CMS bug. Sends are queued; state in
> `out/collection_exports/`, log in `out/collection_exports.jsonl`.

---

## Find anything fast

| question | do this |
|---|---|
| Where is feature X? | `rg <DistinctiveName>` from root (`vsizeRow`, `export_zip`, `spLibHtml`…) |
| What does this button do? | search `data-act=<name>` → `ACT.<name>` → its `post(...)` URL |
| Is this route real? | `GET /api/openapi.json`, then `api/app.py` |
| What should this screen do? | `docs/<area>.md` index → read only that section file |
| Which actions exist? | `console/inventory.py` + `tests/data/ui_baseline.json` |
| How is this tested? | `mirsal/tests/test_<area>.py`, `mirsal/tests/js/*.test.js` (browser-less UI) |

## Run it

- venv `mirsal/.venv` (Windows). Server: `python -m mirsal serve` — owner runs `:8770`, use your own `--port` with `MIRSAL_OUT=<a copy>`.
- Checks stay offline: `MIRSAL_NO_REAL_CLI=1`, `MIRSAL_LLM_PROVIDER=none` (tests never touch real providers; paid calls need a shown price + yes).
- Tests: narrowest only — `mirsal test fast` / `focused` / `area <module>`. Full `unittest discover` is retired.
- Health: `python -m mirsal doctor`.
