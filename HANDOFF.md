# HANDOFF: the save point

This file holds only what a session was in the middle of when it stopped (it got stuck, the context ran out, something went wrong). Nothing else lives here: the next steps are `plan.md`, what exists is in `README.md` and `docs/`, what is open is in `docs/backlog.md` and `docs/waiting-for-haitham.md`.

When a session stops mid-step, write: the step being worked on, the files touched, what is half-done, how to resume. The session that resumes deletes it.

## In progress

Session of 2026-10-08 (second), all work committed and pushed. Nothing half-written.

**Just finished:** plan Phase 1, the claim ledger core — `generation/claims.py`, `migrations/012_pack_claims.sql` (applied to the local database, `db check` clean),
`store/repo.save_pack_session` / `import_pack_sessions`, `store/sync.sync_pack_session`, `db import` hookup, `tests/test_claims.py` (11 green; `test_store` + `test_migrations` green).
Proven once on the real local Postgres in a rolled-back transaction. Nothing calls the ledger yet.

**Still open (unchanged from the previous session unless noted):**
1. `tests.test_batches.RemoveRoutes` Windows file-lock flake in teardown (pre-existing, not from this work).
2. Next: plan Phase 2 (resolver + chat wiring). Per-owner vs shared pack sessions: Haitham said ignore it for now (2026-10-08); sessions stay keyed by slug.
3. Paid proof (plan Phase 6) needs Haitham's explicit yes (~2 credits).
4. Particles ordering (Studio step 5) investigated, not implemented; `mirsal/mirsal/console/particles.js` and `mirsal/tests/js/particles.test.js` have uncommitted edits in the working tree that predate this session (not mine; left untouched).
5. Import-pack browser check never happened (restart `serve --lan` first); `batch_import_inputs.py` at repo root does not run; Haitham's questions (original-emojis mapping, copying sheets into `inputs/`) unanswered.

**Resume:** `plan.md` Phase 2, with `docs/export to team/mirsal-export-architecture.md` §10.7. Windows checkout, venv `mirsal/.venv`, branch `main`.
