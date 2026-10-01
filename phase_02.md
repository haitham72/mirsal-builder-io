# Phase 2 — Postgres (durable state, identity, lineage)

**Prerequisite:** Phase 1 exits (1A, 1B, 1D and **1F, the golden path with review gates**) are met.

**Read `README.md` first.** It documents Phase 1 as built: the `<media>-<NNN>-<task_slug>-<key>` naming, `result.json`, `events.jsonl`, the prompter contract and the input pairing. Then read `phase_01.md`, "Golden path", for the gates (G1 plan, G2 stills, G3 video sheet, G4 animation, G5 pack), `tags`, `history` and `video_sheets`. This phase persists exactly that; it invents no new shapes.

**Goal:** every generation, sticker, asset and **decision** gets a stable ID, survives restarts and can be **searched in Postgres**.
- `G004/S3` is addressable forever, with its prompt, name, tags, emoji, validation report, files, parent generation, and every approve/reject it received (who, at which gate, why).
- Nothing is ever overwritten.

The behaviour stays the same as in Phase 1. This phase adds memory and search, not features: it is about **seamless integration**, so the console and CLI behave exactly as before, now backed by Postgres.

**Not in this phase:** generation APIs, LLMs, LangGraph, **LangSmith (moved to Phase 3, decided 2026-10-01)**, Redis, or vector search. There is no new web server or frontend: the Phase 1 console stays, writes through the repo, and its existing Library search box switches to Postgres.

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
5. **Store versions for reproducibility:** `engine_version` and the manifest as used. Phase 3 adds model and seed.
6. **Decisions are append-only rows.** Every Python block or pass, human approve or reject, and (from Phase 3) VLM verdict is one `reviews` row. The sticker's `still_review` / `anim_review` columns only mirror the latest row; they are status columns in the sense of principle 2. A sticker's history is a query, never a stored blob.
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

## Schema (`001_init.sql`)

```sql
CREATE SEQUENCE generation_seq;

-- IMMUTABLE helpers for the stickers.search_doc generated column
CREATE FUNCTION array_to_text(text[]) RETURNS text LANGUAGE sql IMMUTABLE AS $$ SELECT array_to_string($1, ' ') $$;
CREATE FUNCTION mirsal_words(text)    RETURNS text LANGUAGE sql IMMUTABLE AS $$ SELECT replace($1, '_', ' ') $$;

CREATE TABLE generations (
  id            text PRIMARY KEY,                 -- 'G004' (from generation_seq, zero-padded ≥3)
  parent_id     text REFERENCES generations(id),  -- 'another' / later edits
  prompt        text NOT NULL,                    -- exactly what the user typed
  subject       text NOT NULL,
  source        text NOT NULL,                    -- 'prepared' now (was 'fixture'); 'model' in Phase 3
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
  idx              int  NOT NULL,                 -- 1..9, row-major
  name             text NOT NULL,                 -- file stem: 'img-004-teddy_bear_school-teddy_bear_with_a_book'
  key              text NOT NULL,                 -- searchable action name: 'teddy_bear_with_a_book' (Phase 3B pool key)
  tags             text[] NOT NULL,               -- 1..5 from the plan (1F); tags[1] = key
  concept          text,                          -- filled by the Phase 3 planner; NULL for Phase 1 prompts
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
  ticket        text,                             -- Phase 3: provider task id; NULL for a manual upload
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
  actor          text NOT NULL CHECK (actor IN ('python','human','vlm')),   -- 'vlm' from Phase 3
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

**Why `'simple'` and not `'english'`:** keys and tags are already normalized slugs, and the `english` stemmer would merge words Phase 3B must keep apart. Arabic keywords arrive in Phase 3 (`keywords` jsonb); they get their own `simple` vector then.

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

   Phase 3B `ALTER`s it (adds `parsed`, `gap_generated`). It does not create it again. The Phase 2 lexical search is the latency baseline that 3B's hybrid search reports against.

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

**Status rule:** a generation is `READY` if all its stickers are READY (9 for a sheet; 1 or more for Phase 3C/3D photo and text stickers), `PARTIAL` if some are, and `FAILED` if none. A partial pack is a valid pack. The gate result is separate from this status: the **final pack** is the stickers with `still_review = 'APPROVED'` and, if animated, `anim_review = 'APPROVED'`.

---


## Build steps

1. Write `docker-compose.yml` and `.env.example` (`DATABASE_URL`, `ASSET_ROOT`).
2. Add `mirsal db up | migrate | reset` (reset is dev only and asks for confirmation).
3. Write `repo.py`. `save_generation(result)` is **one transaction**: the generation row, 9 sticker rows and all asset rows. The run's status becomes visible only after the commit.
4. `create` / `another` / `animate` **and the 1F gate routes** (`review`, `video_sheet`, the returned-video upload) write through the repo. A gate decision is one transaction: the `reviews` row, the mirrored `still_review`/`anim_review` and the event. Keep writing `result.json` too, as a portable export.
5. Add `list`, `show <id>`, `history <G###/S#>` and `search "<text>" [filters]`. Switch the console's Library search box to `GET /api/search` when the database is up, and keep the `library.json` search when it is not (doctor says which one is active).
6. `mirsal db import out/` backfills Phase 1 runs from `result.json` (including `parent`, `tags`, per-sticker `history` → `reviews` rows, and `video_sheets` with their `layout.json`), `prompts.json` and `events.jsonl`. It is idempotent: re-running it skips generations, events and reviews already present. Results written before 1F have no `tags` (use `[key]`) and no `history`: import their Python verdicts as `actor = 'python'` PASS/BLOCK rows from `status`/`reason`, and leave the human gates `PENDING`.
7. **Ingest (moved here from Phase 1):** `mirsal ingest <file> --task <subject> [--kind img|vid]` copies a raw download into `Images_gen/`/`videos_gen/` as the next `{task}-##`, records it as a `SOURCE_SHEET`/`SOURCE_VIDEO` asset with its sha256, and keeps image and video linked by the same `##`. Manual sandbox files stay valid; the app never renames anything in a watch folder without this explicit command.

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

## Exit
- [ ] Every command above works; the tests pass.
- [ ] `import out/` brings in every Phase 1 run, including 1F reviews and video sheets.
- [ ] Haitham runs `list` / `show` / `history` / `search` after a restart and sees his history, with every approve/reject he made in the console.

## Explicitly deferred
- Sessions, interactions, feedback, preferences → Phase 4. Chat feedback ("I like 2 but not 3") is different from a gate decision: when Phase 4 receives it at an open gate, it writes `reviews` rows too.
- LangSmith tracing → Phase 3. LangGraph `interrupt()` at the gates → Phase 4. The gate rules and the `reviews` table do not change.
- Model-call logging, seeds → Phase 3.
- Pack curation tables (pack vs generation) → Phase 5.
- **Redis → Phase 4** (event streams, job progress, locks, hot caches). Postgres stays the only durable store.
- Vector search → Phase 3, checkpoint 3B (semantic sticker pool). The image already ships pgvector, so there is no container swap later.

## Hands to Phase 3
- Stable IDs.
- A transactional repo.
- An `AssetStore` interface.
- `generations.source` / `source_ref`, ready for `model`.
- `generations.plan` has the prompter contract's shape, so the Phase 3 planner output drops in unchanged.
- `generation_events`, which Phase 4 mirrors into Redis streams and Phase 5 replays over SSE.
- `reviews`: the Phase 3 VLM writes its verdicts here as `actor = 'vlm'`, before the human gates.
- `video_sheets` with a `ticket` column: Phase 3's video API attaches its task id there instead of the manual upload.
- `search` + `search_log`: Phase 3B adds vectors and Arabic keywords to the same query path instead of creating a second one.
- Clean seams for Phase 3's LangSmith tracing: `pipeline.Stage` (one span per stage) and the review route (one feedback per decision). Phase 3 adds `trace_run_id` to `generation_events` and `reviews`.
