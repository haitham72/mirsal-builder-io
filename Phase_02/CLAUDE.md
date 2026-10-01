# Phase_02 — supporting material for `../phase_02.md`

Phase 2 adds Postgres: stable IDs (`G004/S3`), lineage and immutable history, with the same behaviour as Phase 1. The spec is **`../phase_02.md`**. Prerequisite: the Phase 1 exits (1A + 1B).

- **Prerequisite added 2026-10-01:** Phase 1 checkpoint **1F** (golden path with review gates, `../phase_01.md`). Phase 2 persists its contracts (`tags`, `reviews`, `history`, `video_sheets`) and makes everything searchable in Postgres.
- **No inputs from Haitham.** Don't wait for any. LangSmith is **not** in this phase (moved to Phase 3 on 2026-10-01); this phase is seamless Postgres integration.
- **Port:** use 5434. 5433 is `temporal_note-db` and 5437 is the old Mirsal POC. `mirsal doctor` checks it with a Python socket (no `lsof`; the dev PC is Windows).
- **Read `../README.md` first** (Phase 1 as built), and keep the restricted-network rules: image via `docker load`, wheels vendored.
