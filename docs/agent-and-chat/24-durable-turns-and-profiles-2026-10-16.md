# Durable turns and profiles (2026-10-16)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

The graph finally uses two LangGraph powers: a checkpointer for durable turns, and per-user memory it reads back. Approvals are unchanged (cards and go-ahead buttons, not `interrupt()`).

## Turn checkpoints (`SqliteSaver`, `out/checkpoints.sqlite`)

Every turn checkpoints under `thread_id = <session id>` (`langgraph-checkpoint-sqlite`, in `requirements.txt`). The file is disposable and git-ignored, one per `out/` (a `MIRSAL_OUT` copy gets its own). `Turn` pickles with only JSON-native fields: `__getstate__` drops the live trace and lock; a node guard rebinds a restored turn's trace to its own sess/msg.

A restart resumes the dead turn only when it is provably safe: the pending node is in `SAFE_RESUME_NODES` (understand, resolve, clarify, ask, smalltalk, profile, search, names, finish — none of them spends or writes decisions) **and** the turn spent nothing (`spent == 0`). Anything else keeps the old interrupted message. `Agent.close()` / `Agent.close_all()` release the process-wide saver connections (tests must close, or temp dirs cannot be deleted on Windows).

The last turn's stickers repair an emptied focus: when the session focus names a batch but no stickers (a paid batch just reset it), `_ctx` falls back to `_last_focus` — the newest earlier checkpoint with stickers for that batch — so "number 3" hits the new batch, not the old one.

## Profiles (`out/profiles.sqlite`, `agent/profile.py`)

One row per person: predefined columns for the stable core (`user_id`, `name`, `tone`), JSON columns for what grows (`likes`, `dislikes`, `preferences`, `edit_counts`). The JSON file stays the human-readable export (every table write mirrors into it; the first open imports it), the Postgres copy stays the mirror. Never committed, like the JSON.

- Name, likes, dislikes, extras flow in through `set_facts` (validated as before); tone through `detect_tone` ("be brief" → `brief`) in `n_profile`, confirmed in the reply.
- Every decided edit is counted in `n_editroute` (`tweak` / `action` / `redesign` / `editor`); `top_edit()` only names a kind when it is strictly ahead.
- Reads with a visible effect: the greeting shortens for `brief` tone, and the unclear-edit reply nudges the phrasing the person uses most (`You usually ask for tweak — say it like '...'`).

Tests: `tests/test_agent_memory.py` (checkpoint per turn, safe resume, focus fallback, table growth/ranking, tone greeting, edit counting). Nothing here spends: providers stay `none` under tests.
