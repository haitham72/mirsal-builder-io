# Phase_02 — supporting material for `../phase_02.md`

Phase 2 adds Postgres: stable IDs (`G004/S3`), lineage and immutable history, with the same behaviour as Phase 1. The spec is **`../phase_02.md`**. Prerequisite: the Phase 1 exits (1A, 1B, 1D, 1F, 1G).

- **Prerequisite added 2026-10-01:** Phase 1 checkpoint **1F** (golden path with review gates, `../phase_01.md`). Phase 2 persists its contracts (`tags`, `reviews`, `history`, `video_sheets`, 1G's `out/tasks/*.json` as `tasks` rows) and makes everything searchable in Postgres.
- **1F and 1G are built (2026-10-01):** the exact shapes to import are in `../phase_02.md`, "Notes from building 1F + 1G".
- **No inputs from Haitham.** Don't wait for any. LangSmith is **not** in this phase (moved to Phase 3 on 2026-10-01); this phase is seamless Postgres integration.
- **Port:** use 5434. 5433 is `temporal_note-db` and 5437 is the old Mirsal POC. `mirsal doctor` checks it with a Python socket (no `lsof`; the dev PC is Windows).
- **Read `../README.md` first** (Phase 1 as built), and keep the lean-dependency rules (CLAUDE.md rule 8). The PC has internet since 2026-10-01, so `docker pull` and `pip install` into `mirsal/.venv` are fine; `docker save/load` stays the fallback.
