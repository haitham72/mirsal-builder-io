# HANDOFF: the save point

This file holds only what a session was in the middle of when it stopped (it got stuck, the context ran out, something went wrong). Nothing else lives here: the next steps are `plan.md`, what exists is in `README.md` and `docs/`, what is open is in `docs/backlog.md` and `docs/waiting-for-haitham.md`.

When a session stops mid-step, write: the step being worked on, the files touched, what is half-done, how to resume. The session that resumes deletes it.

## In progress

Nothing: the chat's stage selector and batch follow-up (`plan.md` Steps 0–3) are built and `plan.md` is deleted. Haitham's browser look is item 1 of `docs/waiting-for-haitham.md`.

Still unknown: `tests.test_js` has 3 Studio failures + 1 error, and `mirsal test area agent/graph` 3 failures (video-prompt wording x2, history-card `KeyError: 'G002'`); all fail the same way without these changes, not chased.

Not mine, do not commit: the AddCollection URL change (`docs/Api/`, `mirsal/.env.example`, `services/collection.py`) and `mirsal/out/` runtime files.
