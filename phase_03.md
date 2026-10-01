# Phase 3 — Postgres (durable state, identity, lineage), tracing, the sticker pool, photo / text / depth stickers

> **Order changed 2026-10-01 (Haitham): the old Phase 2 and the old Phase 3 swapped.** Live generation is **Phase 2** and runs on the file store. This phase starts only when Haitham confirms. It first gives everything Phase 2 wrote a database (**3A**), then builds on it (**3B-3E**, which were the old Phase 3's second half).

**Checkpoints, each reviewed before the next:**
- **3A** = Postgres, identity, history, search, **and tracing (LangSmith)** — the old Phase 2 plus the old Part 3b;
- **3B** = the semantic sticker pool (Part 5);
- **3C** = photo cutout stickers (Part 6);
- **3D** = text template stickers, CapCut-style (Part 7);
- **3E** = 3D parallax photos (Part 8).

**Prerequisite:** the Phase 1 exits, and Phase 2 has produced live generations. (Haitham can start 3A earlier; nothing in it needs Phase 2, it simply has less to import.)

**Read `Phase_01/README.md` first.** It documents Phase 1 as built: the `<media>-<NNN>-<task_slug>-<key>` naming, `result.json`, `events.jsonl`, the prompter contract and the input pairing. Then read `Phase_01/README.md`, "Golden path", for the gates (G1 plan, G2 stills, G3 video sheet, G4 animation, G5 pack), `tags`, `history` and `video_sheets`, and `phase_02.md` for the jobs, `out/model_calls.jsonl` and the judge verdicts. This phase persists exactly those; it invents no new shapes.

**Goal of 3A:** every generation, sticker, asset and **decision** gets a stable ID, survives restarts and can be **searched in Postgres**.
- `G004/S3` is addressable forever, with its prompt, name, tags, emoji, validation report, files, parent generation, and every approve/reject it received (who, at which gate, why).
- Nothing is ever overwritten.
- A 1x1 regen of one sticker is a new generation (`regen_of`, `parent_id`); its other stickers are `inherited_from` the parent's rows. No files are copied.

The behaviour stays the same as in Phase 1 and 2. 3A adds memory and search, not features: it is about **seamless integration**, so the console and CLI behave exactly as before, now backed by Postgres.

**Not in 3A:** vectors (3B), Redis, LangGraph, a new web server or frontend. The Phase 1 console stays, writes through the repo, and its existing Library search box switches to Postgres.

---

## What Haitham sees at the end

```
python -m mirsal create "banana with big eyes"   # same as Phase 1, now also written to Postgres
python -m mirsal another                          # G002, parent = G001
python -m mirsal list                             # G001 banana 01 9/9 ✓ · G002 banana 02 8/9 ✓ …
python -m mirsal show G002                        # stickers, names, tags, emoji, status, reasons, files, parent, gate decisions
python -m mirsal history G002/S5                  # sliced PASS (python) → G2 REJECT (human, "too dark") …
python -m mirsal search "teddy book"              # G002/S1 teddy_bear_with_a_book 📚 · still APPROVED · anim APPROVED …
python -m mirsal search "teddy" --approved --animated
docker restart mirsal-db && python -m mirsal show G002   # still there
```

`show` prints each sticker's files and the console URL. `preview.html` no longer exists: the Phase 1 Lifecycle Console replaced it, and Phase 5 supersedes the console.

---

## Principles

1. **Postgres is the state; the disk is the media.** Rows hold paths + hashes + metadata, never image bytes.
2. **Immutable history.** Generations and assets are append-only.
   - A re-run, "another", or later an edit creates a **new** generation with `parent_id` set.
   - Files are never overwritten: paths include the generation id.
   - Only status columns may be updated, e.g. `animation_status` when `animate` runs later.
3. **Natural language is never an identifier.** IDs are `G###` and `G###/S#`, allocated by Postgres.
4. **The engine doesn't change.** Persistence is an adapter that consumes `StickerResult` / `result.json`. The boundary test gains `psycopg`: the engine must not import it.
5. **Store versions for reproducibility:** `engine_version` and the manifest as used. Phase 2 adds model and seed.
6. **Decisions are append-only rows.** Every Python block or pass, human approve or reject, and (from Phase 2) VLM verdict is one `reviews` row. The sticker's `still_review` / `anim_review` columns only mirror the latest row; they are status columns in the sense of principle 2. A sticker's history is a query, never a stored blob.
7. **Postgres is the search surface.** Anything Haitham can see in the console can be found with `mirsal search` or the Library search box: prompt, task, key, tags, emoji, status, gate decision, generation, date.
8. **The gate rules stay in Python** (Phase 1's `pipeline.py`). The repo stores decisions; it does not decide. This is what lets Phase 4's LangGraph `interrupt()` take over the *waiting* without moving the rules.

---

## Where things live

```
mirsal/
  docker-compose.yml          # pgvector/pgvector:pg16 (plain Postgres 16 + pgvector, used from Phase 3B), container mirsal-db, host port 5434
  migrations/001_init.sql     # plain SQL, applied in order by `mirsal db migrate`
  mirsal/store/
    db.py                     # psycopg 3 connection (DATABASE_URL from .env)
    repo.py                   # save_generation(), get_generation(), list_generations(), add_asset(), set_animation_status(),
                              # add_review(), history(sticker_id), save_video_sheet(), search(query, filters)
    assets.py                 # AssetStore interface + LocalAssetStore (disk). S3-compatible store is a later swap.
```

**Port 5434:** 5433 is already taken by the workspace's `temporal_note-db`. `mirsal doctor` (introduced in Phase 1, extended here) checks the port with a Python socket, which works on Windows, macOS and Linux (no `lsof`).

**Restricted network:** the dev PC has poor internet. Load the `pgvector/pgvector:pg16` image from a tarball (`docker save` on a connected machine, `docker load` here), and vendor the `psycopg[binary]` wheel next to the Phase 1 wheels (see README "library policy"). If Docker itself is unavailable, the repo layer must stay behind `repo.py` so a plain local Postgres install works with the same `DATABASE_URL`.

---

## The Phase 1 library migrates here

Phase 1 (Part D) stores packs in `out/library/library.json` (`packs[] -> stickers[]`: id, name, slug, cover, next counter, sticker file/type/emoji/kb/w/h/source, created). Model it as `packs` and `pack_stickers` (ordered by position, `emoji text[]` for Telegram's multi-tag rule, `source jsonb` = `{generation, index}` or `{editor: true}`), keep the same file naming `<img|vid>-<NNN>-<pack_slug>-<sticker_slug>`, and import the JSON once. The `Library` class becomes a repository with the same method names so the console keeps working unchanged.

## The hard truth: request → external task id → database → search (Haitham, 2026-10-01)

This is the one flow every phase must keep true:

```
user asks ("teddy bear")  ─►  external API returns a task id  ─►  Postgres stores {id, name_key}  ─►  dev lookup + key / semantic search
```

- **The external task id is the join key** between Mirsal and the provider. It is never derived from a filename. Phase 2's provider returns it (the Higgsfield job id, written at `claim` into `out/jobs/*.json` and `out/tasks/*.json` with `provider = 'higgsfield-mcp'`). Where no provider ran, the **prepared** inputs stand in for it: `provider = 'prepared'`, `external_task_id = 'img-001-teddy_bear'` (the watch-folder name, which is final and never renamed).
- **`name_key`** is the human-readable, searchable key:
  - for a task it is the plan's `task_slug` (`teddy_bear_school`);
  - for a sticker it is its `key` (`teddy_bear_with_a_book`, = `tags[0]`).
  Every file stem is built from them (`<media>-<NNN>-<task_slug>-<key>`), so a filename, a DB row and a search hit all say the same thing.
- **Dev use:** `mirsal task <external_task_id>` and `mirsal task --key teddy_bear_school` print the task, its generation(s), the stickers, their files, and every verifier/human decision. The question "what happened to provider task X?" is answered in one command.
- **Search use:** `search` matches `name_key`, key and tags exactly or by prefix first (fast, for dev and the UI), then full-text and trigram (3A). 3B adds vectors over the same rows (semantic). There is one query path; 3B extends it, it does not fork it.

```sql
CREATE TABLE tasks (
  id               bigserial PRIMARY KEY,
  provider         text NOT NULL,                  -- 'prepared' (Phases 1-2) | 'wavespeed' | 'openai' … (Phase 2)
  external_task_id text NOT NULL,                  -- the provider's task id; for prepared inputs the watch-folder name
  kind             text NOT NULL CHECK (kind IN ('sheet','video','single')),   -- single = 1x1 regen of one sticker
  name_key         text NOT NULL,                  -- task_slug, e.g. 'teddy_bear_school'
  generation_id    text REFERENCES generations(id),
  video_sheet_id   text REFERENCES video_sheets(id),   -- set for kind = 'video'
  status           text NOT NULL,                  -- REQUESTED | RUNNING | DONE | FAILED | TIMEOUT
  request          jsonb NOT NULL,                 -- what was sent: template id + slot JSON, grid, model, seed
  result_ref       jsonb,                          -- what came back: object key(s), sha256, provider metadata
  created_at       timestamptz NOT NULL DEFAULT now(),
  completed_at     timestamptz,
  UNIQUE (provider, external_task_id)              -- one row per provider task; re-delivery is idempotent
);
CREATE INDEX ON tasks (name_key);
CREATE INDEX ON stickers (key text_pattern_ops);   -- prefix search on name keys ('teddy_bear_%')
```

- `video_sheets.ticket` (below) becomes a reference to `tasks.external_task_id` (kind `video`). There is one place for provider ids.
- **Migration order:** `tasks` references `generations` and `video_sheets`, so `001_init.sql` creates it after both.
- **1G's manual tasks** (`out/tasks/<NNN>.json`, `provider = 'higgsfield-manual'`, `external_task_id` = the reserved folder name) import as `tasks` rows unchanged.
- `db import` creates one `prepared` task row per imported generation (sheet) and one per video used.
- **Tests:**
  - importing the same prepared folder twice gives one task row;
  - `mirsal task img-001-teddy_bear` lists every generation made from it;
  - `search teddy_bear_with` (prefix) returns that sticker before any full-text hit.

## Schema (`001_init.sql`)

```sql
CREATE SEQUENCE generation_seq;

-- IMMUTABLE helpers for the stickers.search_doc generated column
CREATE FUNCTION array_to_text(text[]) RETURNS text LANGUAGE sql IMMUTABLE AS $$ SELECT array_to_string($1, ' ') $$;
CREATE FUNCTION mirsal_words(text)    RETURNS text LANGUAGE sql IMMUTABLE AS $$ SELECT replace($1, '_', ' ') $$;

CREATE TABLE generations (
  id            text PRIMARY KEY,                 -- 'G004' (from generation_seq, zero-padded ≥3)
  parent_id     text REFERENCES generations(id),  -- 'another' / later edits / a 1x1 regen
  grid          int[] NOT NULL DEFAULT '{3,3}',   -- {rows,cols}: {3,3} | {2,2} | {1,1} (1F)
  regen_of      text,                             -- 'G004/S5' when this generation is a single-sticker 1x1 regen
  verify_version text NOT NULL,                   -- the verifier rule set that judged it (1F VERIFY_VERSION)
  prompt        text NOT NULL,                    -- exactly what the user typed
  subject       text NOT NULL,
  source        text NOT NULL,                    -- 'prepared' now (was 'fixture'); 'model' in Phase 2
  source_ref    jsonb NOT NULL,                   -- {"subject":"teddy_bear","subject_id":"001","variant":2,"sheet":"img-001-teddy_bear (5).jpg","video":"vid-001-teddy_bear (2).mp4"}
  task          text NOT NULL,                    -- prompter output: 'teddy yellow bear for school'
  task_slug     text NOT NULL,                    -- 'teddy_bear_school' (file-name middle)
  sheet_prompt  text,
  video_prompt  text,
  plan          jsonb NOT NULL,                   -- prompts.json as used (guidelines + 9 stickers). Replaces the old manifest column.
  engine_version text NOT NULL,
  status        text NOT NULL,                    -- READY | PARTIAL | FAILED
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE stickers (
  id               text PRIMARY KEY,              -- 'G004/S3'
  generation_id    text NOT NULL REFERENCES generations(id),
  idx              int  NOT NULL,                 -- 1..rows*cols, row-major
  name             text NOT NULL,                 -- file stem: 'img-004-teddy_bear_school-teddy_bear_with_a_book'
  key              text NOT NULL,                 -- searchable action name: 'teddy_bear_with_a_book' (Phase 3B pool key)
  inherited_from   text REFERENCES stickers(id),  -- moved here from Phase 4: a 1x1 regen generation inherits its other stickers
  tags             text[] NOT NULL,               -- 1..5 from the plan (1F); tags[1] = key
  concept          text,                          -- filled by the Phase 2 planner; NULL for Phase 1 prompts
  prompt           text NOT NULL,
  emoji            text[] NOT NULL,
  status           text NOT NULL,                 -- READY | FAILED (superset enum in models.py)
  reason           text,
  report           jsonb NOT NULL,                -- validator checks
  metrics          jsonb NOT NULL,                -- bbox, scale, spill count, timings
  animation_status text NOT NULL DEFAULT 'NOT_REQUESTED',
  animation_reason text,
  still_review     text NOT NULL DEFAULT 'PENDING',  -- mirror of the latest G2 row in reviews: PENDING | APPROVED | REJECTED | BLOCKED
  anim_review      text NOT NULL DEFAULT 'PENDING',  -- mirror of the latest G4 row (BLOCKED = Python, e.g. inside_slot)
  video_sheet_id   text,                          -- the A<n> it was animated from (FK added below)
  search_doc       tsvector GENERATED ALWAYS AS (  -- mirsal_words() must exist first: array_to_string is only STABLE,
                     to_tsvector('simple',        -- and Postgres refuses non-IMMUTABLE generated columns
                       coalesce(prompt,'') || ' ' || mirsal_words(key) || ' ' || mirsal_words(array_to_text(tags)))) STORED,
  UNIQUE (generation_id, idx)
);

CREATE TABLE assets (
  id            bigserial PRIMARY KEY,
  generation_id text NOT NULL REFERENCES generations(id),
  sticker_id    text REFERENCES stickers(id),     -- NULL for SOURCE_SHEET / SOURCE_VIDEO
  kind          text NOT NULL CHECK (kind IN ('SOURCE_SHEET','SOURCE_VIDEO','KEYED_SHEET','PROMPTS','PNG','WEBP','WEBM',
                                              'VIDEO_SHEET','VIDEO_LAYOUT','RETURNED_VIDEO')),
  video_sheet_id text,                            -- set for VIDEO_SHEET / VIDEO_LAYOUT / RETURNED_VIDEO
  object_key    text NOT NULL,                    -- relative key under the asset root
  sha256        text NOT NULL,
  mime          text NOT NULL,
  bytes         int  NOT NULL,
  width         int, height int, fps real, duration real,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ON stickers (concept);
CREATE INDEX ON generations (parent_id);

-- 1F: the video sheet built from the approved stills (G3), and the video that came back for it
CREATE TABLE video_sheets (
  id            text PRIMARY KEY,                 -- 'G004/A1'
  generation_id text NOT NULL REFERENCES generations(id),
  attempt       int  NOT NULL,                    -- A1, A2 … (a new sheet after a changed G2 decision is a new attempt)
  slots         int[] NOT NULL,                   -- sticker idx placed on the sheet, e.g. {1,2,3,4,7,8,9}
  layout        jsonb NOT NULL,                   -- layout.json as written (canvas, key_rgb, grid, slot rects, scale)
  status        text NOT NULL,                    -- BUILT | APPROVED | REJECTED | VIDEO_RETURNED | SLICED
  ticket        text,                             -- Phase 2: provider task id; NULL for a manual upload
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (generation_id, attempt)
);
ALTER TABLE stickers ADD FOREIGN KEY (video_sheet_id) REFERENCES video_sheets(id);
ALTER TABLE assets   ADD FOREIGN KEY (video_sheet_id) REFERENCES video_sheets(id);

-- every decision at every gate, by every actor; append-only
CREATE TABLE reviews (
  id             bigserial PRIMARY KEY,
  generation_id  text NOT NULL REFERENCES generations(id),
  sticker_id     text REFERENCES stickers(id),      -- NULL for whole-generation gates (plan, video_sheet, pack)
  video_sheet_id text REFERENCES video_sheets(id),  -- set for G3 and for G4 rows
  gate           text NOT NULL CHECK (gate IN ('plan','still','video_sheet','anim','pack')),
  actor          text NOT NULL CHECK (actor IN ('python','human','vlm')),   -- 'vlm' from Phase 2
  decision       text NOT NULL CHECK (decision IN ('PASS','BLOCK','APPROVE','REJECT')),
  reason         text,                              -- python: the check name (no_spill, inside_slot …); human: free note
  detail         jsonb,                             -- e.g. {"frame": 41, "over_px": 6}
  user_id        text NOT NULL DEFAULT 'local',     -- Phase 5 adds real users
  ts             timestamptz NOT NULL,
  UNIQUE (generation_id, sticker_id, gate, actor, ts)  -- makes `db import` idempotent
);
CREATE INDEX ON reviews (sticker_id, ts);

-- search (principle 7). pg_trgm ships in the pgvector image's contrib.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX ON stickers USING gin (search_doc);
CREATE INDEX ON stickers USING gin (tags);
CREATE INDEX ON stickers USING gin (key gin_trgm_ops);    -- typo-tolerant fallback ("tedy bok")
CREATE INDEX ON generations USING gin (prompt gin_trgm_ops);
```

**Why `'simple'` and not `'english'`:** keys and tags are already normalized slugs, and the `english` stemmer would merge words 3B must keep apart. Arabic keywords arrive from the Phase 2 planner (`keywords` jsonb); they get their own `simple` vector then.

**Search (`repo.search`, `mirsal search`, `GET /api/search?q=` for the console's Library box):**
1. Full-text match on `search_doc` (prompt, key and tags), ranked with `ts_rank`.
2. Exact tag match boosts the rank.
3. If nothing is found, fall back to trigram similarity on `key` and `generations.prompt`.
4. Filters: `--approved` (`still_review = 'APPROVED'`), `--animated` (`anim_review = 'APPROVED'`), `--gate-rejected`, `--generation G004`, `--since`.
5. Every hit shows its id, key, emoji, both review states and its file.
6. The query and the hit ids are written to `search_log`:

   ```sql
   CREATE TABLE search_log (id bigserial PRIMARY KEY, query text NOT NULL, filters jsonb NOT NULL DEFAULT '{}',
                            hit_ids text[] NOT NULL, latency_ms int, created_at timestamptz NOT NULL DEFAULT now());
   ```

   Phase 3B `ALTER`s it (adds `parsed`, `gap_generated`). It does not create it again. The 3A lexical search is the latency baseline that 3B's hybrid search reports against.

**History (`repo.history(sticker_id)`, `mirsal history G004/S5`):**
- Returns the `reviews` rows plus the `generation_events` rows for that sticker, in time order.
- This is exactly the path shown in the console's carousel.

**Lifecycle events** (Phase 1 writes them; persist them, they are the audit trail and what Phase 5's SSE replays):

```sql
CREATE TABLE generation_events (
  id            bigserial PRIMARY KEY,
  generation_id text NOT NULL REFERENCES generations(id),
  ts            timestamptz NOT NULL,
  stage         text NOT NULL,     -- requested | plan_reviewed | sheet_picked | keyed | sliced | stills_reviewed | video_sheet_built
                                   -- | video_sheet_reviewed | video_requested | video_returned | video_picked | video_sliced | video_cell
                                   -- | anim_reviewed | pack_final   (1F added the review and video-sheet stages)
  status        text NOT NULL,     -- start | done | error
  ms            int,
  detail        jsonb,
  actor         text,              -- python | human | vlm (1F); NULL for plain engine steps
  UNIQUE (generation_id, ts, stage, status)      -- makes `db import` idempotent
);
```

**Object keys** follow `G004/slices/img-004-teddy_bear_school-teddy_bear_with_a_book.png` (or `.webp` if the PNG exceeded 512 KB), `G004/slices/vid-004-teddy_bear_school-teddy_bear_with_a_book.webm`, `G004/source/sheet.jpg`, `G004/source/keyed.png` and `G004/prompts.json`. They are relative to `ASSET_ROOT` (default `mirsal/out/`), so the resolved paths are exactly Phase 1's `out/G004/...`. `generations.parent_id` comes from `result.json`'s `parent`.

**Status rule:** a generation is `READY` if all its stickers are READY (9 for a sheet; 1 or more for 3C/3D photo and text stickers), `PARTIAL` if some are, and `FAILED` if none. A partial pack is a valid pack. The gate result is separate from this status: the **final pack** is the stickers with `still_review = 'APPROVED'` and, if animated, `anim_review = 'APPROVED'`.

---


## Build steps

1. Write `docker-compose.yml` and `.env.example` (`DATABASE_URL`, `ASSET_ROOT`).
2. Add `mirsal db up | migrate | reset` (reset is dev only and asks for confirmation).
3. Write `repo.py`. `save_generation(result)` is **one transaction**: the generation row, 9 sticker rows and all asset rows. The run's status becomes visible only after the commit.
4. `create` / `another` / `animate` **and the 1F gate routes** (`review`, `video_sheet`, the returned-video upload) write through the repo. A gate decision is one transaction: the `reviews` row, the mirrored `still_review`/`anim_review` and the event. Keep writing `result.json` too, as a portable export.
5. Add `list`, `show <id>`, `history <G###/S#>` and `search "<text>" [filters]`. Switch the console's Library search box to `GET /api/search` when the database is up, and keep the `library.json` search when it is not (doctor says which one is active).
6. `mirsal db import out/` backfills `out/tasks/*.json` (1G) as `tasks` rows, then Phase 1 runs from `result.json` (including `parent`, `tags`, per-sticker `history` → `reviews` rows, and `video_sheets` with their `layout.json`), `prompts.json` and `events.jsonl`. It is idempotent: re-running it skips generations, events and reviews already present. Results written before 1F have no `tags` (use `[key]`) and no `history`: import their Python verdicts as `actor = 'python'` PASS/BLOCK rows from `status`/`reason`, and leave the human gates `PENDING`.
7. **What Phase 2 wrote is imported too:** `out/jobs/*.json` become `tasks` rows (`provider = 'higgsfield-mcp'`, `external_task_id` = the Higgsfield job id, `video_sheet_id` for video jobs), `out/model_calls.jsonl` becomes `model_calls` (see `002_models.sql` below), and the `actor = 'vlm'` history lines become `reviews` rows. Generated files are already stored by job; `mirsal ingest <file> --task <subject> [--kind img|vid]` stays for raw manual downloads (it records a `SOURCE_SHEET`/`SOURCE_VIDEO` asset with its sha256 and never renames anything in a watch folder without that explicit command).

---

## Tests
- Use a throwaway database per test session (create/drop a temp DB on the same container).
- Round trip: save → load a generation, and every field matches.
- Immutability: `another` creates a new generation, and G001's rows and files are byte-identical before and after.
- Lineage: G1 → G2 → G3 through `another`; walking `parent_id` from G3 returns G2, then G1.
- Partial pack: the blank-cell synthetic sheet stores `PARTIAL` with S4 `FAILED(empty_subject)`.
- Hash integrity: every asset's `sha256` matches its file.
- Restart: `docker restart mirsal-db`, and `show` still returns everything.
- Boundary: the engine does not import `psycopg`.
- Events: importing the same `events.jsonl` twice adds no rows; event order per generation matches the file.
- Names: `stickers.name` is unique per generation and matches the file on disk; `key` matches `prompts.json`.
- Parent: `more` in Phase 1 wrote `parent`; import sets `parent_id` from it (G002 -> G001).
- **Golden path round trip:** the 1F synthetic scenario (G2 rejects 5 and 6; `inside_slot` blocks 1 and 2; G4 approves the rest) stored, then reloaded:
  - `history G00N/S5` ends with `still REJECT human`;
  - `history G00N/S1` ends with `anim BLOCK python inside_slot`;
  - the final-pack query returns exactly 3, 4, 7, 8, 9;
  - `video_sheets.slots = {1,2,3,4,7,8,9}`.
- **Append-only reviews:** changing a decision adds a row and never updates one; the mirror column follows the latest row; approving a `BLOCK`ed sticker is refused by the repo as well as by the pipeline.
- **Search:**
  - `search "teddy book"` finds the sticker whose tags hold `book`;
  - `search "tedy bok"` finds it through the trigram fallback;
  - `--approved` hides gate-rejected stickers;
  - a key-only Phase 1 import is still findable.

## Exit (3A built 2026-10-01; architecture in `Phase_03/README.md`)
- [x] Every command works (`db/list/show/history/search/task`); 152 tests pass (`tests/test_store.py`: 10).
- [x] `db import` brings in every Phase 1 run (92/92 incl. 1F reviews and video sheets; re-import adds zero rows),
  with one `prepared` task row per generation (sheet; separate per-video rows deferred).
- [x] `mirsal task <external_task_id>` and prefix search work for prepared folders (Higgsfield job ids: no Phase 2
  outputs exist yet).
- [ ] `import out/` also brings in `out/jobs/*.json`, `out/model_calls.jsonl` and the VLM verdicts — waits for
  Phase 2 to produce them (`import_tasks` covers `out/tasks/*.json` only; `model_calls` table + `002` land then).
- [~] Tracing seam done (`obs/trace.py`: `none` zero network calls, `langsmith` batched + droppable, gate-feedback
  keys; fake-server tested). `mirsal trace backfill` waits for real runs.
- [x] Restart proof done by the builder (`docker restart mirsal-db && show` returns everything); Haitham's own
  `list/show/history/search` run still pending.

## Explicitly deferred (3A)
- Sessions, interactions, feedback, preferences → Phase 4. Chat feedback ("I like 2 but not 3") is different from a gate decision: when Phase 4 receives it at an open gate, it writes `reviews` rows too.
- LangGraph `interrupt()` at the gates → Phase 4. The gate rules and the `reviews` table do not change.
- Vector search → 3B (semantic sticker pool). The image already ships pgvector, so there is no container swap later.
- Pack curation tables (pack vs generation) → Phase 5.
- **Redis → Phase 4** (event streams, job progress, locks, hot caches). Postgres stays the only durable store.

## Hands to 3B and the later phases
- Stable IDs, a transactional repo, an `AssetStore` interface.
- `generations.source` / `source_ref` (`prepared` or `model`) and `tasks` with the provider ticket.
- `generations.plan` in the prompter contract's shape, so the Phase 2 planner output is stored unchanged.
- `generation_events`, which Phase 4 mirrors into Redis streams and Phase 5 replays over SSE.
- `reviews`: Python, human and (imported from Phase 2) VLM verdicts, one row each.
- `video_sheets.ticket` = the Higgsfield job id of the video job.
- `search` + `search_log`: 3B adds vectors and Arabic keywords to the same query path instead of creating a second one.
- The tracing seams (`pipeline.Stage`, the review route) are wired in the second half of this checkpoint, with `trace_run_id` on `generation_events` and `reviews`.

## Notes from building 1F + 1G (2026-10-01): exact shapes to import


**Added later on 2026-10-01 (import these too, nothing else changes):**
- `stickers` gains `file_name` (the generator's `img-NNN-<task_slug>-<key>`; the library sticker's `name` is now the readable `{subject} {action}`), `edited` + `edited_at` (a human edit in the sticker editor; the original is kept in `source/orig/S#.png`; `history[]` gets decision `EDIT` at stage `still`, actor `human`).
- `reviews` can now hold, for an animation that leaves its cell, a `BLOCK` row with reason `inside_frame` while `anim_status` stays `READY` (the video exists but `review.anim = BLOCKED`); the WARN check `inside_frame` is in the `anim_report`.
- `anim_metrics.ms` (per-stage timings) and `anim_metrics.cache = "hit"` are metrics only. `out/cache/anim/` is a derived cache (safe to delete), not a source of truth: do not import it.
- The library packs (`library.json`) are not in Postgres yet in this plan's tables: `source = {generation, index}` on a library sticker is the link back to `G00N/S#`.
Written after the Phase 1 build so the migration matches what is on disk (README, "The golden path" and "The Inbox"):
- **`history[]` per sticker** is `{ts, stage, actor, decision, reason, ref, detail}` with `stage` in `sheet | sliced | still | video_sheet | video | anim | pack`, `actor` in `python | human` (`vlm` from Phase 2), `decision` in `PASS | BLOCK | APPROVE | REJECT`, `ref` = the video sheet id (`A1`) where one applies, and `detail` = the failing check as `{check, value, limit, note, data}` (for `inside_slot`: `data.frame`, `data.over_px`). One entry becomes one `reviews` row; `detail` goes to `reviews.detail jsonb`. Generation-level decisions are in `result.reviews` (`plan`, `video_sheet{A1}`, `pack` with its `stickers[]`), each `{decision, by, ts, note}`: they become `reviews` rows with `sticker_id` NULL.
- **Checks are stored on the result too:** `stickers[].report[]` and `anim_report[]` (`{name, ok, detail, severity, stage, value, limit, data}`), `verify.sheet[]`, `video_sheets[].verify[]` and `.video_checks[]`. `verify_version` is on the result. A `WARN` is a failing row with `severity: "WARN"`.
- **`video_sheets[]`** holds `{id, slots, grid, file, layout, video, video_name, status, blocked, block, video_flags, video_info, canvas, video_prompt}`; status `VIDEO_BLOCKED` is new (the returned video failed `layout_match`/`video_specs`/`video_decodes` and nothing was sliced; the upload can be repeated). `layout.json` is `{canvas, key_rgb, grid, slots[{slot, sticker, rect, subject_rect, scale, subject_px}], verify_version}`.
- **Files:** every still has an outline-free twin at `source/plain/S#.png` (the video sheet is built from it): store it as an `assets` row of kind `PLAIN_STICKER` next to the still.
- **`tasks`:** `out/tasks/NNN.json` is `{id, number, provider, external_task_id, name_key, status, created, prompt, grid, style_id, folders{img,vid}, paths, request{template_id, template_version, slots, grid}, plan, plan_review, generations[]}`. Results carry `task_id`, `name_key`, `regen_of`, `template_id`, `template_version`, `slots`.
- **Events** carry optional `actor` and `decision`; new stages: `plan_reviewed, stills_reviewed, video_sheet_built, video_sheet_reviewed, video_returned, video_flag, anim_reviewed, pack_final` and a per-decision `review` event with `detail {gate, index, note}`.
- **`GET /api/search?q=`** exists as a file search; the Postgres search replaces its body, not the route or the row shape (`{generation, id, index, key, tags, name, task_slug, status, reason, review, anim_status, png, webm, emoji, final}`).


---

## 3A, second half — Tracing (LangSmith)

Phase 2 is where model calls start (their log is `out/model_calls.jsonl`); tracing starts here, once Postgres holds the record.

**Goal:** every stage and every gate decision of the golden path (`Phase_01/README.md`, 1F) is visible in LangSmith.
- Postgres stays the record (`reviews`, `generation_events`, `model_calls`).
- LangSmith is the view, and the place where VLM verdicts are compared with human ones.

**`mirsal/obs/trace.py`** exposes `span(name, inputs, outputs, parent)` and `feedback(run_id, key, score, comment)`.
- It is wired into `pipeline.Stage`, the review route, and every provider / LLM / VLM call.
- **Backend `none`** is the default and records nothing outside Postgres.
- **Backend `langsmith`** uses the `langsmith` SDK. Its posts are batched on a background thread; a failed post is logged and dropped. **Tracing never blocks or fails the pipeline.**

**Mapping:**
- One root run per generation.
- One child run per stage and per model call.
- **Each gate decision is feedback** on the run it judges:
  - keys `gate_plan | gate_still | gate_video_sheet | gate_anim | gate_pack` for humans, and `vlm_still | vlm_anim` for the judge;
  - score 1 for APPROVE/PASS and 0 for REJECT/BLOCK;
  - comment = the reason.

**What leaves the machine:** ids, slot JSON, prompts, metrics and decisions. **Never image or video bytes;** files are referred to by object key. This is fixed in code (Mirsal is positioned as a secure chat).

**Config:** `MIRSAL_TRACE=none|langsmith`, `LANGSMITH_API_KEY`, `LANGSMITH_ENDPOINT` (cloud or self-hosted), `LANGSMITH_PROJECT=mirsal`. `doctor` reports the backend and whether it is reachable.

**`mirsal trace backfill [--since]`** replays the Phase 3 rows that have no `trace_run_id`, including all of Phase 3's history. It is idempotent.

**Tests:**
- `none` makes zero network calls (socket guard);
- against a local fake server, `langsmith` gets one root run per generation, one child run per stage, and one feedback per decision, with no media bytes in any payload;
- a 500 or a timeout from the server does not slow the pipeline.

**Open decision for Haitham:** LangSmith cloud or self-hosted. Phase 4 keeps the same keys when LangGraph adds its own native runs to the same project.

---

## Schema (`002_models.sql`: what Phase 2 produced, imported)

```sql
ALTER TABLE generations
  ADD COLUMN seed bigint, ADD COLUMN attempts int NOT NULL DEFAULT 1,
  ADD COLUMN key_color text, ADD COLUMN chroma_reason text,
  ADD COLUMN style_id text, ADD COLUMN mode text,          -- 'sheet' | 'single'
  -- `plan jsonb` exists since Phase 3 (same shape, extended by the planner): do not add it again
  ADD COLUMN planner_version text, ADD COLUMN prompt_template_version text,  -- assembly template, not Phase 4 transformations
  ADD COLUMN final_prompt text, ADD COLUMN final_video_prompt text,
  ADD COLUMN sheet_check jsonb;
ALTER TABLE stickers
  ADD COLUMN judge jsonb,                                   -- VLM Judgement
  ADD COLUMN keywords jsonb,                                -- {"en": [...], "ar": [...]}
  ADD COLUMN emoji_suggestion text[];
ALTER TABLE generations ADD COLUMN prompt_slots jsonb, ADD COLUMN template_id text;   -- template-locked prompts (Part 1)
ALTER TABLE generation_events ADD COLUMN trace_run_id uuid;                          -- Part 3b
ALTER TABLE reviews           ADD COLUMN trace_run_id uuid;
-- model_calls: one row per line of out/model_calls.jsonl (Phase 2), plus every new call
CREATE TABLE model_calls (
  id bigserial PRIMARY KEY,
  generation_id text REFERENCES generations(id), sticker_id text REFERENCES stickers(id),
  kind text NOT NULL,            -- LLM_PLAN | IMAGE_SHEET | IMAGE_SINGLE | VIDEO | VLM_STICKER | VLM_SHEET
  provider text NOT NULL, model text NOT NULL, prompt_version text,
  attempt int NOT NULL, seed bigint,
  status text NOT NULL,          -- OK | TIMEOUT | ERROR | INVALID_OUTPUT | REJECTED_BY_GATE
  latency_ms int, tokens_in int, tokens_out int, cost_usd numeric(10,4), error text, raw_output text,
  created_at timestamptz NOT NULL DEFAULT now()
);
```

---

## Part 5 — Semantic sticker pool (checkpoint 3B: search → reuse → generate only the gaps)

**Idea (ported from the old build's `/api/pool`, with its defects fixed):**
- Every approved sticker joins a searchable pool.
- A request like **"{topic} doing {action}"** ("falcon dancing", "banana shocked", "صقر يرقص") first fetches matching existing stickers: **free and instant**.
- Only the missing count goes to paid generation, and only after the price is shown.
- New stickers join the pool, so it grows with use.
- **No Redis here:** Postgres + pgvector only. Phase 4 adds a cache on top later.

**Write path (index):**
- Each `APPROVED` sticker gets a row in `sticker_index`. Hidden stickers and inherited edit copies (from Phase 4) are skipped.
- **`subject`**: `plan.extraction.subject`. For prepared sets, the set name.
- **`action`**: the cell's `action`, falling back to `name` + `concept`.
- **`search_text`**: `subject — action — name — emoji — style_id`. Phase 4C appends `annotation.visual_summary` and reindexes.
- **`topics`**: normalized tags, using the old build's `normalize_topic()`: lower-case, apostrophes folded, punctuation dropped, Arabic letters kept. So "Mother's Day!" becomes `mothers day`.
- **Two vectors per sticker:**
  - `subject_vec` = embed(subject);
  - `action_vec` = embed(action + name).
  - The model is `EMBED_MODEL` (default `text-embedding-3-small`, 1536-d, as in the old build). The model name is stored per row for reindexing.
- **Commands:** `mirsal pool reindex` backfills every earlier generation, including Phase 1–2 prepared-set runs. `mirsal pool hide <sticker_id>` removes a sticker from search without deleting it.

**Read path: `mirsal search "falcon dancing" [--count 9] [--style …]`**
1. **Parse the query** into `{subject, action, emotion?, style?, topics[]}`.
   - Deterministic patterns come first: "X doing Y", "X Y-ing", "Y X", "X that is Y".
   - Arabic, Arabizi and anything unmatched go to `claude-haiku-4-5-20251001` with a strict schema. The output is English.
2. **Hybrid score:**
   - The parts: `0.5·cos(subject) + 0.4·cos(action) + 0.1·lexical`. The lexical part is a trigram match on name/emoji/topics.
   - Filter out hidden stickers, missing images, a mismatched `style_id` when a style was asked for, and anything outside the viewer's scope (below).
3. **Quality gate** (the old build had none; it returned nearest neighbours even when irrelevant): a hit counts only if `cos(subject) ≥ SUBJECT_MIN` **and** `cos(action) ≥ ACTION_MIN`, with both calibrated on the eval set. "Penguin skiing" in a pool with no penguins returns **zero**, never the closest junk.
4. **Diversity:** at most 2 hits per generation. Near-duplicates (`search_text` cosine > 0.97) collapse to the best-judged one.
5. **Gaps:**
   - If fewer than `--count` match, the reply is: "Found 4 · generate 5 more? (~$X)".
   - On confirmation, the gap is generated through Part 3 with the parsed subject + action as the request, varying that action.
   - `create` always generates (it's what the Part 4 measurements use). `search` is the pool-first command. Phase 5 merges both into one search box.

**Sharing scope:**
- Until Phase 5 there is one local user.
- The rule is fixed now for 5C: stickers from **text-only** requests are `shared = true`. Anything from an **uploaded reference image** is `shared = false` forever, visible to its owner only.

**Migration `003_pool.sql`:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;            -- image is pgvector/pgvector:pg16 since Phase 3
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE TABLE sticker_index (
  sticker_id  text PRIMARY KEY REFERENCES stickers(id),
  subject     text NOT NULL, action text NOT NULL, search_text text NOT NULL,
  topics      text[] NOT NULL DEFAULT '{}',
  subject_vec vector(1536) NOT NULL, action_vec vector(1536) NOT NULL,
  embed_model text NOT NULL,
  shared      boolean NOT NULL DEFAULT true, hidden boolean NOT NULL DEFAULT false,
  indexed_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON sticker_index USING hnsw (subject_vec vector_cosine_ops);
CREATE INDEX ON sticker_index USING hnsw (action_vec vector_cosine_ops);
CREATE INDEX ON sticker_index USING gin (topics);
CREATE INDEX ON sticker_index USING gin (search_text gin_trgm_ops);
-- search_log exists since Phase 3 (id, query, filters, hit_ids, latency_ms, created_at); extend it, never re-create it
ALTER TABLE search_log ADD COLUMN parsed jsonb, ADD COLUMN gap_generated int NOT NULL DEFAULT 0;
```

**Phase 3 already has `mirsal search`** (full-text on prompt, key and tags, plus a trigram fallback, with gate filters) and the console's Library search. 3B upgrades the same command and route to the hybrid score below. It keeps 3A's filters (`--approved`, `--animated`) and `tags` as part of `topics`. A sticker is "approved" for the pool when its human gate says so (`still_review = 'APPROVED'`, see 1F). A VLM approval alone counts only when `auto_approve_vlm` is on.

**Eval set:** `Phase_02/search_queries.md` holds ~30 queries (English, Arabic, Arabizi), each with the sticker IDs Haitham considers relevant, plus ≥5 that should return nothing.

**3B exit (lexical pass built 2026-10-01; vectors deferred):**
- [x] `pool search "teddy waving"` returns only waving teddies (ranked); `"falcon dancing"` / `"teddy dancing"` return **zero** (no such stickers; never the closest junk). Free, no model calls. (`mirsal/pool.py`, `tests/test_pool.py`: 4.)
- [ ] Measured on the eval set (`Phase_03/search_queries.md`, pending from Haitham): precision@5 ≥ 0.8. Recorded in `docs/phase3_measurements.md` when the eval lands.
- [~] Gap flow: "Found N · generate M more?" (confirmation required; the price is not shown yet — no provider pricing without live calls; generation stays manual).
- [x] `pool reindex` covers every earlier generation (140 approved indexed); `pool hide` removes from search without deleting.
- [ ] Search latency baseline for Phase 4's Redis cache (measure when the eval lands).
- Deferred to the embedding pass: `EMBED_MODEL` vectors + HNSW (`subject_vec/action_vec` NULLABLE until then), Arabic LLM query parser (deterministic patterns now), `pool_version` cache key (no Redis yet).

---

## Part 6 — Photo cutout stickers (checkpoint 3C)

**What the user does:** takes a photo of their dog, brother or food. The subject comes back **cut out** with clean alpha and an outline, as a 512 sticker. That's the whole feature. Text on stickers is the separate Part 7.

```
python -m mirsal photo dog.jpg [--outline white|color|dieCut|none] [--subject N]
```

It needs the Phase 1 engine (scale, outline, validators) and Phase 3 storage; no prompts, no generation API, no Redis.

**Use an existing library, do not write one** (options and licence cautions are tabulated in `Phase_01/README.md`, "Keyers": rembg with U2-Net/ISNet/BiRefNet first, transparent-background, SAM 2 for click-to-select, OpenCV `grabCut` as a zero-download fallback). Wire it as the last rung of Phase 1's key-failure ladder as well, so a failed green-screen cell gets one matting attempt before it is ruled out.

**Update (Phase 1, Part E):** the seam now exists as `mirsal/matte.py` (U2-Net / IS-Net through onnxruntime, models in `mirsal/models/`), called by `library.cutout` (auto -> matte -> GrabCut) and by the video background-removal provider; 3C's remaining work is a stronger model (BiRefNet), click-to-refine (SAM 2) and video propagation behind the same functions. **Earlier state (Part D):** `library.cutout()` (used by the desktop builder's "Create from photo") keeps existing alpha, chroma-keys green/blue screens with the Phase 1 engine, and otherwise runs OpenCV GrabCut with an inset rectangle. It is the seam for this part: implement `engine/matte.py`, call it from `library.cutout` for the non-green branch, keep GrabCut only as the no-weights fallback, and keep the `method`/`foreground`/`warning` info the editor shows. GrabCut is known to fail on busy backgrounds and similar colours, so 3C's exit should compare both on Haitham's own photos. The editor's Erase/Restore brush is the human fallback and needs no change.

**Matting keyer (new, same contract as Phase 1's chroma key):** photos have no green screen, so add `engine/matte.py` exposing the same `key_image(rgb, cfg) -> Keyed(rgba, ...)` shape, with backends `rembg` (u2net / isnet-general-use / birefnet). Everything after the key (specks, trim, pack scale, outline, validators) is Phase 1 code, untouched. Model weights are downloaded once on a connected machine and loaded by path (`MIRSAL_MATTE_MODEL`); `doctor` checks them. Video matting (RVM) stays opt-in and out of the default path: per-frame matting flickers, which is why Phase 1 keeps chroma for video.

- **Matting, not chroma key:** `Matting.segment(photo) -> alpha`. The default is **local**: BiRefNet (MIT licence) via onnxruntime, at full resolution for fur and hair edges.
- **Fallback:** port `proposals/Mirsal-chat-emojis/api/cutout.py` (`silueta.onnx` U2-Net 320 px + GrabCut). It is too coarse for fur, which is why it's only the fallback.
- **On-device by default:** the photo never leaves the machine (Mirsal is a secure chat). A hosted matting API sits behind the same interface, opt-in only.
- **Subject choice:** the largest connected subject ≥2% of the frame; `--subject N` picks another.
- **Then the Phase 1 steps:** speck removal, trim, scale (occupancy 0.775), premultiplied resize, and the outline: None / White / Color / Die-cut, the old POC's set.
- **Checks:**
  - `single_subject` and `foreground`;
  - `edge_quality`: a soft alpha gradient along the contour, not a hard binary edge;
  - `static_file`.
- **Optional paid AI motion** (opt-in, price shown first): the cutout on flat chroma goes to the Part 3 video model, then through the Phase 1 keying and loop close.
- **Privacy:** the photo (`SOURCE_PHOTO` asset) and its stickers are `shared = false`: never in the shared pool. Haitham's test photos live in `Phase_02/photos/`, which is **gitignored**.

**Tests:**
- Composite our own keyed stickers onto cluttered photo backgrounds (the old POC's method) and require IoU ≥ 0.92.
- A synthetic fur-edge shape keeps a soft gradient.
- Default mode makes **zero network calls** (sockets blocked in the test).

**3C exit (offline core built 2026-10-01; `tests/test_photo.py`: 2):**
- [x] `photo dog.jpg` gives a clean subject sticker in ≤3 s (synthetic green-screen: chroma path, 512 PNG, validated).
- [ ] On Haitham's 10+ real photos (`Phase_03/photos/`, still pending), he judges the edges clean. IoU ≥ 0.92 on composites.
- [x] No network calls in default mode (chroma/GrabCut; AI matte only when installed).
- Deferred: BiRefNet upgrade, SAM 2 click-to-refine, `--subject N`, paid AI motion, `SOURCE_PHOTO` asset rows, HEIC/iPhone Portrait input (Pillow reads browser-common formats today).

---

## Part 7 — Text template stickers (checkpoint 3D, CapCut-style)

**What the user gets:** a big library of ready-made **templates**, each a flashy sticker design with a text slot. The animation is only **1–2 frames flashing on repeat**, like an old "Happy Holiday" web banner: colours swap, sparkles jump, a neon sign flickers.
- The user's words drop into the slot.
- When the user's **last chat message is ≤ `N` words** (default 4, ≤24 characters), the app auto-fills it and suggests the best-matching templates.
- It is Snapchat's "comment on a sticker", and WhatsApp's newer auto-text sticker done properly: many templates instead of a couple of fixed images, matched to the message, and working in Arabic.

```
python -m mirsal text "happy eid"                   # "last message" → top 6 matching templates, filled, on the chain page
python -m mirsal text "صباح الخير" --template neon_flicker
python -m mirsal templates [--tag eid]              # browse the library
python -m mirsal template check <id>                # validate a new template
```

**Template = files, versioned in the repo** (`mirsal/templates/<id>/`):
- `template.json` holds:
  - `id`, `version`;
  - `tags` {en[], ar[]}, `occasion` (UAE events), `mood`;
  - `frames`: 1–4 entries, each `{art: "f1.png" | null, duration_ms, text_style}`. `text_style` sets the fill, stroke, glow and offset **per frame**, which is what makes it flash.
  - `slot`: the text box `{x, y, w, h, rotation, align, max_chars, font_id}`.
  - an optional `subject_slot`, so a 3C cutout can sit in the template.
- **Frame art** is 512×512 RGBA. It is either procedural (drawn by code from `template.json`: starbursts, sparkles, neon tubes, badges), so the starter set needs no artwork and no licences, or PNGs from Haitham or designers.
- The art may also be generated once through Part 3's image model, **without text** (models garble text), then turned into a template.
- **Starter library:** 30+ procedural templates across greetings, reactions, love, birthday and the UAE occasions (National Day, Eid, Ramadan). More are added by dropping folders in.

**Render (deterministic, instant, free):**
- For each frame: the frame art, plus the text auto-fitted into the slot with that frame's style.
- **Text is rendered by code**, with bundled open-licence display fonts (Latin + Arabic, licence files committed).
- **Arabic** uses Pillow + libraqm for shaping and right-to-left layout, falling back to `arabic-reshaper` + `python-bidi`. A word is never split, because splitting breaks the letter joins.
- Frames loop, so the loop is **seamless by construction**.
- **Encoding:**
  - **WEBM VP9 + alpha** at the template's frame timing, repeated to fill ≤3 s, through the Phase 1 encoder and validators (Telegram);
  - plus **animated WEBP** (WhatsApp-style, 512×512, ≤500 KB).
  - **Not GIF:** its 1-bit transparency makes the text edges jagged.
- **Editable:** text is data. `text_layer = {template_id, template_version, text, overrides}` is stored, and editing re-renders in under a second as a new generation with a parent.

**Matching the message to templates:**
1. An exact `occasion`/`tags` hit ("eid", "عيد", "good morning") in English or Arabic.
2. Otherwise, embedding similarity between the message and each template's tags, reusing the 3B `EMBED_MODEL`.
3. Otherwise, generic templates.

The top K results are diversified, so the six suggestions aren't six near-identical neon designs. Messages over `N` words get no auto-fill; the user types the text instead.

**Tests:**
- Every template passes `template check`: the text fits the slot at `max_chars` in both scripts; every frame is 512 RGBA; the timing is valid.
- "صباح الخير" renders joined, with a golden hash against the raqm reference.
- Outputs pass the Telegram video validator and the animated-WEBP size limit.
- "happy eid" ranks Eid templates first; a 6-word message gets no auto-fill.
- An edit makes no network calls and finishes in under 1 s.

**3D exit:**
- [ ] `text "happy eid"` gives 6 filled, flashing, Telegram-valid stickers in ≤2 s.
- [ ] Arabic works in every template.
- [ ] Haitham rates the starter library as good enough to demo, and a new template folder dropped in shows up with no code change.

**Migration `004_photo_text_depth.sql`** (also covers 3C and 3E):
```sql
ALTER TABLE assets DROP CONSTRAINT assets_kind_check;
ALTER TABLE assets ADD CONSTRAINT assets_kind_check
  CHECK (kind IN ('SOURCE_SHEET','SOURCE_VIDEO','SOURCE_PHOTO','PNG','WEBP','WEBM','WEBP_ANIM','DEPTH','LAYER'));
ALTER TABLE stickers
  ADD COLUMN kind text NOT NULL DEFAULT 'SHEET'
    CHECK (kind IN ('SHEET','PHOTO_SUBJECT','TEXT_TEMPLATE','TEXT_TEMPLATE_WITH_PHOTO')),
  ADD COLUMN text_layer jsonb;
-- generations.source gains 'photo', 'template' and 'depth'
```

---

## Part 8 — 3D parallax photos (checkpoint 3E)

**What the user sees:** any photo, whether taken or received in chat, gets depth and **moves in 3D as the phone tilts**. The subject stays anchored while the background shifts behind it. It's like a Live Photo, but with parallax instead of motion. Apple ships the same effect as Spatial Scenes in iOS 26 Photos; Mirsal brings it to chat images.

It is not a sticker feature: it's a photo viewing effect. It sits in Phase 3 because it reuses the 3C matting and needs no Redis. Phase 5 puts the viewer into the app.

```
python -m mirsal depth photo.jpg [--strength 0.02] [--layers 1|2|3] [--bake]
```

This writes `out/G00N/`:
- `depth.png` (16-bit), plus layer PNGs when `--layers ≥2`;
- `parallax.html`: a self-contained WebGL viewer that follows the mouse on a laptop and the **gyroscope** on a phone;
- with `--bake`, a looping tilt-sweep video for places without WebGL or a gyro.

**1. Depth (on-device by default, like 3C):**
1. **Embedded depth first.** iPhone Portrait photos (HEIC) carry Apple's own depth/disparity map. Read it with `pillow-heif` when present, since it beats any estimate.
2. **Otherwise estimate** with **Depth Anything V2 Small** (Apache-2.0) via onnxruntime at ~1024 px on the long side.
   - Its Base, Large and Giant sizes are **CC-BY-NC (non-commercial)**, so don't use them.
   - Check the licence of any other model (e.g. Apple Depth Pro) before adopting it.
3. **Edge-aware smoothing:** a guided filter on the depth, with the photo as the guide, so depth edges snap to object edges. Smeared edges cause the rubbery stretching.

**2. Focal anchor:** run the 3C matting to find the subject and put the focal plane at its median depth. The subject stays still and the background moves around it; without a subject, focus on the nearest large region.

**3. Rendering, in two quality levels (the start is the first):**
- **Displacement shader (default):** sample the image at `uv + tilt × (depth − focal) × strength`, with `strength` subtle (≈1–3% of the width).
  - Use a slightly dilated foreground depth so edges tear inward instead of smearing.
  - It's cheap, and works on any phone.
- **Layered (`--layers 2|3`, only if the default's halos look bad):**
  - split at the big depth jumps into foreground/background planes;
  - **inpaint the background hidden behind the subject** (OpenCV Telea as the baseline; LaMa, Apache-2.0, as the quality option);
  - render them as stacked planes.

**4. Motion input (web viewer):**
- The gyroscope comes through `DeviceOrientationEvent`. **iOS requires a tap-to-allow permission and HTTPS.**
- Low-pass filter the readings, recenter on the first one, and clamp the tilt.
- Fall back to mouse or touch drag.
- Respect `prefers-reduced-motion` by showing the image static.

**5. Chat contract (for Mirsal's own app):**
- An image message carries `{depth_asset_id, focal_depth, strength, layers[]}`, and the client renders parallax instead of a flat image (with a toggle).
- The web viewer is the **reference implementation**. The native iOS client would do the same with Metal and CoreMotion from the same data.
- A depth map can't reproduce the photo on its own, but it is still derived from a private image, so it gets the same access rules as the photo.

**Privacy and storage:** the photo and depth are private (`shared = false`). A `depth` generation stores `SOURCE_PHOTO`, `DEPTH` and `LAYER` assets (no stickers rows). Haitham's test photos go in `Phase_02/photos/` (gitignored).

**Tests (offline):**
- **Synthetic scene with known depth** (three textured planes at different distances): the estimated depth ordering matches, and the focal anchor lands on the subject plane.
- **Embedded depth:** a Portrait HEIC sample yields a depth map, and the pipeline prefers it over estimation.
- **Viewer:** a headless browser checks that `parallax.html` loads, the shader compiles, and the mouse and simulated orientation events change the uniforms. DOM and uniform values only, no screenshots.
- **Privacy:** default mode makes zero network calls.

**3E exit:**
- [ ] `depth photo.jpg` finishes in ≤3 s on the dev PC for a 12 MP photo.
- [ ] `parallax.html` works with the mouse on desktop and with **tilt on Haitham's iPhone** (served over HTTPS, e.g. a local tunnel).
- [ ] The subject stays anchored. On 10 real photos, Haitham judges the edge halos acceptable, and switches to `--layers 2` if not.
- [ ] Portrait HEIC photos use their embedded depth.
- [ ] `--bake` produces a valid looping video. No network calls in default mode.

---

## Explicitly deferred
- **Photo filters (TODO; not planned in any phase yet):**
  - **Blur background.** *Easy*, about a day after 3C: the 3C cutout over a blurred copy of the original. The output is a photo, not a sticker, so build it only if Mirsal wants photo effects.
  - **Beautify** (skin smoothing, retouch). *Medium*: MediaPipe face landmarks (Apache-2.0), a skin mask and edge-preserving smoothing. People only. Needs a product and ethics decision first.
  - **Parallax stickers** (idea): 3E depth applied to generated stickers, so they tilt in 3D inside Mirsal. Telegram can't render gyroscope effects, so this is Mirsal-only.
  - **Snapchat Lens Studio import.** *Not engineering*: lenses only run inside Snap's runtime and can't be exported. The only route is Snap's Camera Kit SDK, which needs Snap's approval and commercial terms and sends data to Snap, conflicting with Mirsal's secure-chat positioning. Alternatives we own: 2D photo frames via 3D templates (`subject_slot`), or MediaPipe face effects.
- Follow-ups ("make number 3 happier"), references, feedback, transformation templates (dog as banana), annotation and memory → Phase 4.
- Caching (planner output, VLM verdicts, search results) → Phase 4, in Redis.
- 60 FPS: dropped (the Telegram cap is 30).

## Hands to Phase 4 (from all of Phase 2 and 3)
- A structured plan per generation (extraction, locks, cells), assembled in two modes.
- A calibrated vision judge.
- Python pixel checks and grid detection.
- A `StickerSource` that really generates.
- Per-call accounting.
