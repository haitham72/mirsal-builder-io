# HANDOFF: the save point

This file holds only what a session was in the middle of when it stopped (it got stuck, the context ran out, something went wrong). Nothing else lives here: the next steps are `plan.md`, what exists is in `README.md` and `docs/`, what is open is in `docs/backlog.md` and `docs/waiting-for-haitham.md`.

When a session stops mid-step, write: the step being worked on, the files touched, what is half-done, how to resume. The session that resumes deletes it.

## In progress

Session of 2026-10-09, all work committed and pushed. Nothing half-written in the files.

**Built this session:** the animations row in the Video view (pick / remove / Report on `G###/A#`); Import inside a batch (picture = the batch's next
generation, video = the main generation's next animation, the sheet it came from read from its first frame); Export to collection (the AddCollection API,
`services/collection.py`). Not yet looked at in a browser by Haitham. Restart `serve --lan` before looking.

**Next:** `plan.md` "Next" (Phase 2: the claim ledger behind Next batch).

**Still open:**
1. The AddCollection credential that was pasted in `docs/Api/AddCollection-API .md` is in git history (commit dd17f61, pushed): rotate that password,
   then put the new one in `mirsal/.env` as `MIRSAL_COLLECTION_API_CREDENTIALS`. Export to collection was never tried against the real CMS.
2. `tests.test_batches.RemoveRoutes` Windows file-lock flake in teardown (pre-existing).
3. Nothing was tried against real Higgsfield; the first real regenerate costs the price on its button.
4. Paid proof (plan Phase 6) needs Haitham's yes; Import-pack browser check never happened.
5. `batch_import_inputs.py` at repo root does not run (calls `pl.Config.default()` / `pl.Pace.default()`, which do not exist, prints characters cp1252
   cannot encode, ignores its arguments and would import a folder twice). Do not run it against the real `out/` until it is fixed.

**Resume:** `plan.md`. Windows checkout, venv `mirsal/.venv`, branch `main`. Tests that cover this session: `tests.test_imports`, `tests.test_collection`,
`tests/js/anim_row.test.js`.
