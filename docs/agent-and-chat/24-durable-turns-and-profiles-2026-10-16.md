# Durable turns and profiles (2026-10-16)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

Implemented in `3f35dcd3`, with replay and profile fixes in `dd8ee1bd` / `afc0f3f6`.
The [review](../langgraph-memory-review.md) records fixes and evidence for all five
findings. Cards and go-ahead buttons
remain the approval interface.

## Turn checkpoints (`SqliteSaver`, `out/checkpoints.sqlite`)

Code ownership is now split under `agent/lifecycle/`: `checkpoints.py` owns the
connection pool, `runner.py` owns locks/replay, `turn.py` owns serialized state,
and `builder.py` owns topology. `agent/graph.py` preserves the public entry points
and old checkpoint class imports. See [code boundaries](25-agent-code-boundaries.md).

Every turn checkpoints under `thread_id = <session id>` using
`langgraph-checkpoint-sqlite`. The file is git-ignored under `mirsal/out/`, with
one saver per output directory. `Turn.__getstate__` drops the live trace and lock;
a node guard rebinds a restored turn's trace to its saved session and message.

Resume advances one node per invocation (`interrupt_after="*"`), checking every
checkpoint against `SAFE_RESUME_NODES` and `spent == 0`. It stops before spending
or decision nodes. Provider-capable understand/profile/search/ask/names nodes
are excluded; resolve with an ask/edit queue is excluded because it can use a
model fallback. Interrupted provider calls require a fresh request, never replay.
Fake checkpoint regressions prove resolve cannot enter review/confirm ahead of
a new cancel and a failed names invocation is called only once.
Resumed `finish` uses the deterministic reducer: a thread-local replay flag
disables its optional model summarizer, including when a long history reaches
the reduction window. A fake summary-provider regression failed then passed.

`Agent.close()` / `Agent.close_all()` release saver connections. Test cleanup
must run after chat workers stop; the Telegram harness now calls `close_all()`
before temporary-directory cleanup (Windows lock regression reproduced and fixed).

When live focus has a generation but no stickers, `_ctx` uses `_last_focus` to
look for the newest earlier checkpoint with stickers for that generation,
scanning at most 40 checkpoints. A non-empty live selection takes precedence.

## Profiles (`out/profiles.sqlite`, `agent/profile.py`)

One row per person contains `user_id`, `name`, `tone`, and JSON columns for
`likes`, `dislikes`, `preferences`, and `edit_counts`. `Profile.set_facts` writes
name, likes, dislikes and extras to the table and JSON profile; tone and edit
counts also write both. First open imports the existing JSON facts. Existing
taste votes remain JSON-only.

Postgres copy: after the JSON write, `store/sync.sync_profile` upserts the whole
`facts` dict into `user_profiles` (migration `011_user_profiles.sql`, keyed by
`user_id`, `facts` JSONB). It is best effort: when Postgres is unreachable it is
skipped silently and the file stays the record. Chat reads still come from the
JSON file and `profiles.sqlite`; nothing reads `user_profiles` back. `db.available()`
caches the first failure per process, so a chat server started before Postgres
was up keeps skipping the copy until it restarts.

- Explicit tone requests route to `n_profile` by rules. `detect_tone` requires
  a be/keep/stay/respond/reply/answer request with a whole style phrase and rejects
  negations. Names such as Shorty and preferences such as warm colours do not
  set reply tone. Fake regressions cover the full routing and stored profile.
- Edit offers count `tweak`, `action`, `redesign`, or `editor`; `top_edit()` returns
  a kind only when it has a strict lead.
- A stored `brief` tone shortens the greeting. Unclear-edit replies can suggest
  phrasing for the person's most frequent edit kind.

Verification results and limitations are kept in the review. Targeted memory tests
pass, but the broader agent area retains baseline failures. Checks used disabled providers and
fakes; no paid-provider validation was performed.

The vision configuration regression test isolates both dotenv loading and the
persisted cloud-model preference. Clearing environment variables alone does not
isolate this checkout from its saved model; this is test isolation, not a change
to the precedence of user settings. It failed with the saved model, then passed
with both configuration sources mocked out.
