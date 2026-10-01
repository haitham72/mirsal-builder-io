# Phase_03 — supporting material for `../phase_03.md`

Phase 3 is **Postgres** (3A: stable IDs like `G004/S3`, lineage, immutable history, search, tracing) and then the pool, photo, text and depth features (3B-3E). It was Phase 2 until 2026-10-01 (the old Phase 3's second half now follows it). The spec is **`../phase_03.md`**. **3A started on Haitham's confirmation (2026-10-01, "proceed with the local postgres") and is built** (architecture in `README.md` in this folder); 3B-3E wait.

- **3A needs no inputs from Haitham** except one decision: LangSmith cloud or self-hosted (`LANGSMITH_API_KEY`). Not blocking: the trace seam ships with the `none` backend and a fake-server test.
- **Prerequisite:** the Phase 1 exits. Phase 2 (live generation) is what gives 3A most to import (`out/jobs/*.json`, `out/model_calls.jsonl`, VLM verdicts); the exact shapes are in `../phase_03.md`, "Notes from building 1F + 1G", and `../phase_02.md`, "Hands to Phase 3".
- **Port:** use 5434. 5433 is `temporal_note-db` and 5437 is the old Mirsal POC. `mirsal doctor` checks it with a Python socket (no `lsof`; the dev PC is Windows).
- **Read `../Phase_01/README.md` first** (Phase 1 as built), and keep the lean-dependency rules (CLAUDE.md rule 8). The PC has internet since 2026-10-01, so `docker pull` and `pip install` into `mirsal/.venv` are fine; `docker save/load` stays the fallback.
- **Later checkpoints and their inputs from Haitham:**
  - `search_queries.md` (pending): ~30 "{topic} doing {action}" queries (English, Arabic, Arabizi) with the sticker IDs he considers relevant, plus >=5 that should return nothing. It is the 3B eval.
  - `photos/` (pending; **gitignored**, never commit): 10+ real test photos (pets, people, food) for the 3C cutout and 3E parallax, including a few **iPhone Portrait-mode HEIC** photos, which carry embedded depth.
  - Templates (optional): extra 3D template art. Drop PNG frame folders into `mirsal/templates/<id>/` using the `template.json` format in `../phase_03.md` Part 7. The builder ships 30+ procedural starters, so nothing blocks on this.
- **Gates:** 3A -> 3B (semantic pool) -> 3C (photo cutout) -> 3D (text templates) -> 3E (parallax photos), each reviewed before the next. No Redis in this phase.
