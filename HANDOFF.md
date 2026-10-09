# HANDOFF: the save point

This file holds only what a session was in the middle of when it stopped (it got stuck, the context ran out, something went wrong). Nothing else lives here: the next steps are `plan.md`, what exists is in `README.md` and `docs/`, what is open is in `docs/backlog.md` and `docs/waiting-for-haitham.md`.

When a session stops mid-step, write: the step being worked on, the files touched, what is half-done, how to resume. The session that resumes deletes it.

## In progress

Session of 2026-10-09, all work committed and pushed. Nothing half-written in the files.

**Built this session:** the animations row in the Video view (pick / remove / Report on `G###/A#`); Import inside a batch; Export to collection (the
AddCollection API at `emojicms.devinprocess.com`, `services/collection.py`; refusals show the CMS's reason); the terminal's activity lines
(`runtime/activity.py`: generating / received / cut / exported / ERROR, `MIRSAL_ACTIVITY`); **the AI chat in Telegram** (`services/tg_chat.py`, on the admin
bot: open to everyone with 0-credit member accounts, native buttons, `/model`, real stickers; docs/agent-and-chat.md "The chat in Telegram").
Fixes found in use: the animation in use follows the pick (`cutOf`), Generate sheet no longer stays grey after a second Generate prompt, a model picked in
the control row is really used (`data-lvvid`), an expired job can be dismissed (it was retried on every poll).

**Next:** `plan.md` "Next" (Phase 2: the claim ledger behind Next batch).

**Still open:**
1. The AddCollection credential pasted earlier is in git history (commit dd17f61, pushed): rotate it; the new one lives in `mirsal/.env` only.
2. Never tried for real: the Telegram chat (sendSticker with our .webm, albums, the creator message edits), Export to collection after the description
   fix. Haitham's `mirsal/.env` still has `MIRSAL_ACCESS_LOG=1` (the per-request flood): remove it and restart `serve --lan`.
3. Telegram chat gaps: a picture sent to the bot is not read; single sheet cells, the editor and the gap slider stay in the browser.
4. `tests.test_batches.RemoveRoutes` Windows file-lock flake in teardown (pre-existing).
5. Paid proof (plan Phase 6) needs Haitham's yes; Import-pack browser check never happened.
6. `batch_import_inputs.py` at repo root does not run (calls `pl.Config.default()` / `pl.Pace.default()`, which do not exist, prints characters cp1252
   cannot encode, ignores its arguments and would import a folder twice). Do not run it against the real `out/` until it is fixed.

**Resume:** `plan.md`. Windows checkout, venv `mirsal/.venv`, branch `main`. Tests that cover this session: `tests.test_imports`, `tests.test_collection`,
`tests.test_tg_chat`, `tests.test_jobs`, `tests/js/anim_row.test.js`, `tests/js/model_pick.test.js`, `tests/js/prompt_step.test.js`.
