# HANDOFF: the save point

This file holds only what a session was in the middle of when it stopped (it got stuck, the context ran out, something went wrong). Nothing else lives here: the next steps are `plan.md`, what exists is in `README.md` and `docs/`, what is open is in `docs/backlog.md` and `docs/waiting-for-haitham.md`.

When a session stops mid-step, write: the step being worked on, the files touched, what is half-done, how to resume. The session that resumes deletes it.

## In progress

`plan.md` Steps 1–3 (chat stages + batch follow-up). Step 0 is built and committed (`c7835b6`, 2026-10-09, plus its area-doc lines in `docs/agent-and-chat.md`).

Step 1 (next): `settings.stage` + `agent/stages.py` + creator `end`. Reads done, no Step 1 code written yet. Resume: create `mirsal/mirsal/agent/stages.py` (`of`, `run_spec`, pure); `memory.py` `DEFAULT_SETTINGS` + `summary_structured`; `console/server.py` settings route validates `stage`; `graph.py` `n_new` branches (prompt = plan-only pending, animation/export = `_creator_plan` with `end`), `_creator_plan(end)` reply/chips, `_start_creator` passes `end`, `_creator_say` done-text for the animation end; `creator.py` `new_run(end)` + pack-step intercept when `end == "animation"`; `tg_chat.py` `session_of` defaults `stage: emojis`, `_run_part` done-label; `openapi.py` Settings; new `mirsal/tests/test_chat_stage.py` + stage cases in `mirsal/tests/test_agent_server.py`.

Still unknown: none on Step 0 (its 6 new tests + resolver tests + 146 agent-area tests green). `mirsal test area agent/graph` has 3 failures, all unrelated and 2 verified pre-existing via stash (video-prompt wording x2, history-card `KeyError: 'G002'` x1).

Not mine, do not commit: the AddCollection URL change (`docs/Api/`, `mirsal/.env.example`, `services/collection.py`) and `mirsal/out/` runtime files (library, jobs, model_calls, collection_exports).
