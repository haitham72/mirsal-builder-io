# HANDOFF: the save point

This file holds only what a session was in the middle of when it stopped (it got stuck, the context ran out, something went wrong). Nothing else lives here: the next steps are `plan.md`, what exists is in `README.md` and `docs/`, what is open is in `docs/backlog.md` and `docs/waiting-for-haitham.md`.

When a session stops mid-step, write: the step being worked on, the files touched, what is half-done, how to resume. The session that resumes deletes it.

## In progress

Nothing half-done. The chat's stages and batch follow-up are built and pushed (`1e28524` Step 1, `2dba73f` Step 2, `4239bff` Step 3, `d66c647` docs). Next: `plan.md` Step 1 (prove the follow-up through the real server on fakes).

What was verified: `tests/test_chat_stage.py` (9), `tests/test_chat_batches.py` (12), `tests/js/chat_stage.test.js` (3), the stage route and follow-up buttons in `tests/test_agent_server.py` / `tests/test_tg_chat.py`, `mirsal test area agent/creator` (29), `tests.test_openapi` (10), the node suite. All green.

Still unknown:
- Nothing ran on a live server or real Higgsfield: the follow-up's timing on a real poll, the creator queue under `drive_creator`, the real `tasks.session_state` count beside the chat's own rows (an emoji pack also counts Studio batches of the same request and person, as the Studio picker does).
- The browser look of the pill, popover and follow-up card is Haitham's (`docs/waiting-for-haitham.md` item 1).
- Pre-existing failures, not chased (they fail the same way without this work): `tests.test_js` 3 Studio failures + 1 error; `mirsal test area agent/graph` 3 (video-prompt wording x2, history card `KeyError: 'G002'`). `plan.md` Step 3.
- One existing test was changed on purpose: `test_agent_server.test_a_full_conversation` now finds the generation card's message, because the follow-up message comes after it.

Not mine, do not commit: the AddCollection URL change (`docs/Api/`, `mirsal/.env.example`, `services/collection.py`) and `mirsal/out/` runtime files.
