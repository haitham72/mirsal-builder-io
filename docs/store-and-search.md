# Postgres, search, the pool, photos and tracing: how it is built

Durable state, identity, lineage, decisions and search. The file store (`out/G###/result.json`) stays the primary store and the app works without the database;
Postgres mirrors it, so history and search survive a restart and a conversation or a decision is a row you can query. Local `mirsal-db`
(`pgvector/pgvector:pg16`, host port **5434**; 5433, 5436 and 5437 belong to other projects and are never touched).

## Run it

```
cd mirsal
pip install -r requirements.txt            # psycopg[binary], redis, langgraph; the engine never imports them
python -m mirsal db up                     # starts mirsal-db (5434) and mirsal-redis (6380) by name when they exist (even made by hand: its data volume stays), docker compose creates only the missing ones; then migrate
python -m mirsal db migrate                # apply migrations/*.sql in order (every file is re-runnable); notes what it cleared (a vector dimension change empties the vectors: `pool reindex` refills them)
python -m mirsal db status                 # schema_migrations read back: declared / applied / pending / unknown files
python -m mirsal db check                  # does the LIVE schema match the files? builds every file in a throwaway schema inside a transaction it rolls back and diffs columns, constraints and indexes
python -m mirsal db import                 # backfill out/tasks, out/jobs, out/model_calls.jsonl and every out/G### (idempotent)
python -m mirsal list | show G092 | history G092/S1 | search "teddy book" [--approved --animated]
python -m mirsal task img-001-teddy_bear   # provider task id -> generations, files, decisions
python -m mirsal pool reindex              # index approved stickers and fill their vectors (local embeddings, free)
python -m mirsal pool search "falcon dancing" [--style flat_vector] [--count 9] [--json]
python -m mirsal pool status | pool hide G002/S5
python -m mirsal trace status | trace backfill [--since DATE]
```

`MIRSAL_DATABASE_URL` (or `mirsal/.env`, git-ignored) overrides `postgresql://mirsal:mirsal_local@localhost:5434/mirsal`. `MIRSAL_DB_WRITE=0` forces write-through off.
Only the real `out/` writes through (tests and `MIRSAL_OUT` copies never touch the shared database; use `db import` for a copy).

## Where things live

```
mirsal/migrations/
  001_init.sql      generations, stickers, assets, video_sheets, reviews, generation_events, tasks, search_log
  002_models.sql    model_calls (the ledger), tasks.job_id / model / cost_credits, stickers.judge / emoji_suggestion
  003_pool.sql      sticker_index (lexical columns, hidden, shared, topics) + pg_trgm
  004_sessions.sql  sessions, interactions, feedback, generation_references, stickers.annotation
  005_vectors.sql   sticker_index.subject_vec / action_vec as vector(768) + cosine HNSW (re-runnable: never wipes vectors)
  009_groups.sql    generations.group_id (the family root, flow/groups.py) and relation (joined | redo | edit), written by every save_generation
  011_user_profiles.sql  user_profiles (user_id, facts jsonb, updated_at): the copy of out/profile/<user>.json facts (agent/profile.py, sync.sync_profile; the file is the record)
  012_pack_claims.sql    pack_sessions, claims, claim_generations: the copy of out/pack_sessions/<slug>.json (generation/claims.py, sync.sync_pack_session; the file is the record)
mirsal/mirsal/store/
  db.py             connect (2 s timeout), cached available(), migrate(), reset(confirm='yes')
  repo.py           save_generation() in ONE transaction (idempotent re-import); import_tasks / save_job / import_jobs / save_model_call /
                    import_model_calls; save_session; save_pack_session / import_pack_sessions; list / show / history / search / find_task
  sync.py           best-effort write-through (generations, jobs, ledger lines, sessions); counts ok / failed / skipped and keeps the last error
                    (shown by `mirsal doctor` and GET /api/health: a failing mirror is never silent)
  assets.py         AssetStore / LocalAssetStore: object keys, append-only puts, HMAC signed expiring links
mirsal/mirsal/store/pool.py     the sticker pool (below)        mirsal/mirsal/services/embed.py   local embeddings (below)
mirsal/mirsal/flow/tickets.py  tickets (below); obs/scrub.py keeps file paths out of free text
```

## Data mapping (file store -> rows)

- `result.json` -> `generations` (`parent` int `8` -> `G008`, `grid`, `slots`, `template_id/version`, `outline/erode_px`, `prompts.json` -> `plan`); the status
  READY / PARTIAL / FAILED is derived from the stickers.
- Stickers -> `stickers` (`tags=[key]` when missing, `emoji` -> `text[]`, `review{}` mirrored to `still_review` / `anim_review`); PNG / WEBM / plain twin / sheet / keyed / prompts ->
  `assets` (bytes hashed, never opened as media); `video_sheets[]` short ids (`A1`) qualified to `G032/A1`.
- `history[]` -> one `reviews` row each (actor `python | human | vlm`; the vision judge's verdicts arrive here); generation-level decisions -> rows with `sticker_id NULL`;
  `events.jsonl` -> `generation_events` (with `trace_run_id` when tracing is on).
- **`tasks`** is the join with the provider: `UNIQUE (provider, external_task_id)`. `out/tasks/*.json` (the typed task, mirrored with the Higgsfield job id at claim) and
  `out/jobs/J###.json` (from CLAIMED on) land in the **same row** (the job updates it: status, result, cost in credits, links to the generation and the video sheet); one `prepared`
  row per generation stands in for the provider when none ran.
- `out/pack_sessions/<slug>.json` (the pack claim ledger, `docs/export to team/mirsal-export-architecture.md` §10.7) -> `pack_sessions` + `claims` (one per preset grid, `C###`) + `claim_generations` (append-only revisions) + one `tasks` row per claim (provider `mirsal-pack`, `external_task_id` = the claim id, kind `sheet`).
- `out/model_calls.jsonl` -> `model_calls`, keyed by the sha256 of the line (re-import adds nothing); `cost_credits` is Higgsfield credits, never dollars.
- `out/sessions/S###.json` -> `sessions`, `interactions`, `feedback` (one row per sticker), `generation_references`.
- `Idempotency-Key` answers (no file): `idempotency_keys` (`store/idem.py`, migration 008): `scope`, the key's sha256, the first answer as `jsonb`; kept 24 h, pruned on write, only for the real `out/`.

## Search

- `GET /api/search?q=` and `mirsal search`: full-text on prompt, key and tags with a tag boost, then a word-level trigram fallback (every query word must resemble a stored
  word; "tedy bok" finds the book sticker, "penguin skiing" finds nothing). Postgres only for the real `out/` with the database up, else files.
- **The pool** (`store/pool.py`, `mirsal pool ...`, the chat's search): every **approved** sticker has a `sticker_index` row (subject, action, topics, `shared`, `hidden`).
  A request "falcon dancing" first fetches matching stickers (free), and only the missing count would go to paid generation, after the price is shown.
  Two scorers behind one query path: **vectors** (`0.5*cos(subject) + 0.4*cos(action) + 0.1*lexical`, quality gate `cos(subject) >= 0.50` and `cos(action) >= 0.40`, so a
  pool without penguins returns nothing for "penguin skiing") and **lexical** for rows without vectors or when no embedding backend runs; `hybrid` mixes them.
  At most 2 hits per generation (`per_gen` lifts it), near-duplicates collapse, `--style` filters. Stickers from an uploaded reference image are `shared = false` forever.
  Thresholds are provisional until Haitham's eval set exists (`docs/measurements.md` has the first real run: related 0.55-0.97, unrelated 0.20-0.35).
- **Embeddings** (`services/embed.py`): `text-embedding-nomic-embed-text-v1.5` on the local LM Studio, 768-d, hardcoded; OpenAI `text-embedding-3-small` with `dimensions = 768` when the
  local server is down and a key exists. Documents are `search_document: ...`, queries `search_query: ...`; vectors are cached in Redis.

## Photo cutout (`mirsal photo`)

A photo becomes a validated 512 sticker in `out/photo/` (private, `shared: false`): `library.cutout` (existing alpha, then the engine's chroma key for green and blue screens, then the
AI matte `media/matte.py` (U2-Net / IS-Net through onnxruntime, weights in `mirsal/mirsal/models/`), then OpenCV GrabCut as the no-weights fallback) followed by the engine's edge finish and
the verifier (`single_subject`, `foreground`, `static_file`, size and format). On-device by default: the photo never leaves the machine and the default mode makes no network call.

## Tickets (`flow/tickets.py`, `migrations/010_tickets.sql`)

Problems are tickets, not traces: LangSmith was retired on 2026-10-04 (it sent data off the machine and could not hold what a person meant). A ticket is `out/tickets/T###.json` (the record) and a row of `tickets` in Postgres (the searchable copy, `store/repo.py` `save_ticket`, best effort like every write-through): what happened and when, the person's words, the issue, a summary, a proposed fix, 2-4 questions with the answers, a status (open / answered / fixed / won't fix) and the commit that fixed it. Automatic tickets (a server error, a FAILED job, a refused Telegram send) fold by a fingerprint that blanks numbers, ids and quoted values. The local model drafts the issue, summary, fix and questions (`flow/ticket_models.py` `TicketDraft`, validated; a bad or missing draft keeps the preset questions). Free text is scrubbed of absolute paths (`obs/scrub.py`). Routes: `docs/api.md` (Tickets); the screen: Settings > Tickets (the owner: the caught failures) and **Report** on a batch, a particle row and a chat reply. A **support** ticket (source `support`, `tickets.open_support`) belongs to one Help conversation (`conversation`). It has a `thread` of admin and user replies (`tickets.add_message`, idempotent by `client_id`), the status `replied` (an admin answered, it stays open), `pinged` (one Telegram ping per event, retried when it failed) and `faq` (its FAQ proposal). Other fields are set by `tickets.patch`. When the local model's draft replaces the preset questions, the replaced ones are kept in `superseded_questions` and an answer records its `question_text`, so a click on a question the page still showed is never refused (Haitham's live T001, 2026-10-05).

## Help & Support records (`migrations/011_support.sql`; `docs/agent-and-chat.md` "Support")

The files are the record; Postgres mirrors them best effort (`store/sync.py` `sync_support`, `store/repo.py`) and holds the vectors:
- `faq`: `out/faq/F###.json`. The status, the published text, `vec vector(768)` of the published text only (cleared when it is not published), and `body` (pending proposal, revisions, provenance, seed). Search answers only from `status = 'published'`, and the file is checked again, so a stale row never answers.
- `support_chunks`: `out/support/index.json`. One row per section of `docs/` (`kind doc`) or block of code (`kind code`), with its file's sha256 and the vector. A changed file's rows are replaced in one transaction (`repo.replace_chunks`).
- `support_conversations`: `out/support/C###.json`.
- `notifications`: `out/notifications/<user>.json`, one row per person and event key.

## Verified

- 2026-10-01: 92 generations, 828 stickers in Postgres, re-import adds zero rows, `docker restart mirsal-db` keeps everything.
- 2026-10-02 on the real `out/` of this PC: `db import` = 8 generations, 11 task files, 14 jobs, 43 model calls, again = 0 new; 45 approved stickers indexed and embedded; the pool searches
- Tests that need the database (`test_store.py`, `test_pool.py`) **skip as whole classes when `mirsal-db` is down**; run `python -m mirsal db up` first.

## Principles that held (the rules the code follows)

1. **Postgres is the state; the disk is the media.** Rows hold paths, hashes and metadata, never image bytes.
2. **Append-only where it counts.** History lines (`result.json` `history`, `reviews` rows) are only ever appended; a `more` or a 1x1 regen is a new generation with `parent_id` / `regen_of`; `AssetStore.put` refuses
   different bytes under an existing key. Inside one `out/G###`, re-running a stage replaces its artefacts in place (`result.json`, `slices/*`, a returned video the user replaced), and the old values live on in the history.
3. **Natural language is never an identifier.** IDs are `G###` and `G###/S#`; the provider's task id is the join key (`tasks.external_task_id`), `name_key` is the human-readable key.
4. **The engine does not change.** Persistence is an adapter over `result.json`; the engine never imports `psycopg` or `redis` (a test enforces it).
5. **Decisions are rows.** Every Python PASS / BLOCK, human approve / reject / edit and vision-judge verdict is one `reviews` row; `still_review` / `anim_review` mirror the latest.
6. **The gate rules stay in Python** (`flow/gates.py`, `flow/pipeline.py`). The repository stores decisions, it does not decide; the agent only *waits* at a gate.
7. **Postgres is the search surface** for everything the console shows; the pool extends the one query path with vectors, it does not fork it.
