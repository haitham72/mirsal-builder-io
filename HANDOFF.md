# HANDOFF: the save point

This file holds only what a session was in the middle of when it stopped (it got stuck, the context ran out, something went wrong). Nothing else lives here: the next steps are `plan.md`, what exists is in `README.md` and `docs/`, what is open is in `docs/backlog.md` and `docs/waiting-for-haitham.md`.

When a session stops mid-step, write: the step being worked on, the files touched, what is half-done, how to resume. The session that resumes deletes it.

## In progress

Session of 2026-10-08 (second), all work committed and pushed. Nothing half-written in the files; the next UI step is planned, not started.

**Built this session:** claim ledger core (`generation/claims.py`, `012_pack_claims.sql`, applied locally); Grok Imagine 1.5 Lite in the video models;
regenerate video inside a generation (`gates.redo_video`, `SUPERSEDED`, `cut_sheet`, `pick_video`, `remove_video`); regenerate sheet = a new generation of the
batch (family) with `groups.family` / `groups.pick`; Next batch (`tasks.next_batch`, `POST /api/plan/next`, `actions.BODY_SENTENCES`); `sheet_model` and
`video_sheets[].model` recorded; the Studio's footers are one Regenerate with the model folded as {current} -> {next}; "Create more" is "Next batch";
the Prepared-sheets chip row is gone. An in-place sheet resheet was built and then removed the same day (Haitham chose generations in a row instead).

**Also built (last commit):** the Studio's Batch k header with the generations row (★ main, Make main / Delete / Report; Delete keeps the batch one family), the one frame (Raw · Keyed · To send · Video) with one control row (model drop-down, settings, Loop, Generate/Regenerate, Prompt toggle, Gap only on To send). Not yet looked at in a browser by Haitham.

**Next:** `plan.md` "Next" step 2 (the animations row in the Video view: pick / remove / report; the routes exist), then step 3 (Import inside a batch).

**Still open:**
1. `tests.test_batches.RemoveRoutes` Windows file-lock flake in teardown (pre-existing).
2. Nothing was tried against real Higgsfield; the first real regenerate costs the price on its button. Restart `serve --lan` before looking.
3. `mirsal/mirsal/console/particles.js` and `mirsal/tests/js/particles.test.js` have uncommitted edits from before this session (not mine; left untouched).
4. Paid proof (plan Phase 6) needs Haitham's yes; Import-pack browser check never happened; `batch_import_inputs.py` at repo root does not run.

**Resume:** `plan.md` "Next" step 1. Windows checkout, venv `mirsal/.venv`, branch `main`. Tests that cover this: `tests.test_live` (the regenerate, family,
next-batch and animation-row tests), `tests/js/prompt_tab.test.js`.
