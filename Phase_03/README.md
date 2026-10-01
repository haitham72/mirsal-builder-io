# Phase 3A — Postgres: the architecture as built

Durable state, identity, lineage, decisions and search. The behaviour is unchanged from Phase 1;
3A adds memory, not features: the console and CLI work exactly as before, now backed by Postgres.

**This README is the architecture of what 3A built** (repo convention: each built phase documents itself
here; the plan `phase_03.md` keeps the remaining checkpoints 3B–3E). Built 2026-10-01, on local
`mirsal-db` (`pgvector/pgvector:pg16`, host port **5434** — 5433/5436/5437 belong to other projects
and are never touched).

## Run it

```
cd mirsal
pip install -r requirements.txt            # adds psycopg[binary]; the engine never imports it
python -m mirsal db up                     # docker compose up -d (mirsal-db), then migrate
python -m mirsal db migrate                # apply migrations/*.sql in order (re-runnable)
python -m mirsal db import                 # backfill out/tasks/*.json + all out/G### (idempotent)
python -m mirsal list | show G092 | history G092/S1 | search "teddy book" [--approved --animated]
python -m mirsal task img-001-teddy_bear   # provider task id -> generations, files, decisions
docker restart mirsal-db && python -m mirsal show G092   # still there
```

`MIRSAL_DATABASE_URL` (or `mirsal/.env`, git-ignored) overrides the default
`postgresql://mirsal:mirsal_local@localhost:5434/mirsal`. `MIRSAL_DB_WRITE=0` forces write-through off.

## Where things live

```
mirsal/
  docker-compose.yml          # db only (mirsal-db, 5434, volume mirsal_pgdata). Redis arrives in Phase 4.
  .env.example                # DATABASE_URL, MIRSAL_DB_WRITE, OPENAI_API_KEY, MIRSAL_TRACE (commit; real .env never)
  migrations/001_init.sql     # generations, stickers, assets, video_sheets, reviews, generation_events,
                              # tasks, search_log (+ schema_migrations). Re-runnable; deviations from phase_03.md
                              # are noted at its top (trace_run_id folded in, reviews EDIT, PLAIN_STICKER).
  mirsal/store/
    db.py                     # connect (2 s timeout), cached available(), migrate(), reset(confirm='yes')
    repo.py                   # save_generation() in ONE transaction (upsert generation/stickers,
                              # DO-NOTHING reviews/events/assets -> idempotent re-import); list/show/history;
                              # search: full-text + tag boost, word-level trigram fallback (every query word
                              # must resemble a key/prompt word; "tedy bok" finds the book sticker, "penguin
                              # skiing" finds nothing); find_task by external id or name_key prefix
    sync.py                   # best-effort write-through from pipeline.write_result(); only the real out/
                              # (is_default_out: tests and MIRSAL_OUT copies never touch the shared DB), never raises
  mirsal/obs/trace.py         # span()/feedback(), backends none (default, zero network calls) | langsmith
                              # (urllib, batched background thread, failures dropped, never media bytes)
```

## Data mapping (file store -> rows)

- `result.json` -> `generations` (+ `parent` int `8` -> `G008`, `grid`, `slots`, `template_id/version`,
  `outline/erode_px`, `prompts.json` -> `plan`); status READY/PARTIAL/FAILED derived from the stickers.
- Stickers -> `stickers` (`tags=[key]` when missing, `emoji` string -> `text[]`, `review{}` mirrored to
  `still_review/anim_review`, `NONE` -> `PENDING`); PNG/WEBM/`source/plain/S#.png`/sheet/keyed/prompts ->
  `assets` (bytes hashed, never opened as media); `video_sheets[]` short ids (`A1`) qualified to `G032/A1`.
- `history[]` -> one `reviews` row each (stage->gate map; unknown actor/decision coerced, never dropped
  silently); generation `reviews{plan,video_sheet{A1},pack}` -> `sticker_id NULL` rows (deduped by hand:
  the UNIQUE key never fires on NULLs); `events.jsonl` -> `generation_events`.
- `out/tasks/*.json` (1G manual, `higgsfield-manual`) -> `tasks`; one `prepared` task row per generation
  (`external_task_id` = the watch-folder name, e.g. `img-001-teddy_bear`).
- Pre-1F results (no tags/history, e.g. G001): import as python PASS/BLOCK rows from status/reason,
  human gates stay PENDING.

## Console + CLI

- `GET /api/search?q=` uses Postgres only when serving the real `out/` with the DB up (same row shape as
  the file search plus `"via"`); temp dirs (tests) and `MIRSAL_OUT` copies always use files.
- `python -m mirsal doctor` reports Postgres (reachable + write-through on/off) and the trace backend.

## Verified (2026-10-01)

- 92/92 generations in Postgres (91 prepared + G092 written live through `more`, no import needed),
  828 stickers, reviews + events + assets; re-import adds zero rows.
- `search "teddy book"` (book first), `"tedy bok"` (book at rank 0), `"penguin skiing"` (nothing),
  `--approved --animated` filters; `task img-001-teddy_bear` lists its generations.
- `docker restart mirsal-db && show` returns everything.
- 152 tests green (`tests/test_store.py`: 10 — round trip, pre-1F, idempotency, history order, search,
  task prefix, tmp-out isolation, engine boundary incl. `redis`, trace none + langsmith fake-server).

## Deliberately not in 3A (stays in phase_03.md)

- `out/jobs/*.json` + `out/model_calls.jsonl` + VLM verdicts: no Phase 2 outputs exist yet; `import_tasks`
  covers `out/tasks/*.json` only. The `model_calls` table and `002` migration land with Phase 2's outputs.
- `mirsal trace backfill`: the seam + gate-feedback keys exist; the replay command waits for real runs.
- One `prepared` task row per generation (sheet); separate per-video task rows deferred.
- 3B vectors (the image already ships pgvector; no container swap later), 3C–3E, Redis, LangGraph.
