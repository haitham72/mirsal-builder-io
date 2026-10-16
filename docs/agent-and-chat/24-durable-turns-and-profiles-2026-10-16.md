# Durable turns and profiles (2026-10-16)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

Implemented in `3f35dcd3`. The [review](../langgraph-memory-review.md) records five
open findings, including two P1 replay-safety issues. Cards and go-ahead buttons
remain the approval interface.

## Turn checkpoints (`SqliteSaver`, `out/checkpoints.sqlite`)

Every turn checkpoints under `thread_id = <session id>` using
`langgraph-checkpoint-sqlite`. The file is git-ignored under `mirsal/out/`, with
one saver per output directory. `Turn.__getstate__` drops the live trace and lock;
a node guard rebinds a restored turn's trace to its saved session and message.

Resume currently checks that the next node is in `SAFE_RESUME_NODES` and
`spent == 0`. This does not establish safety: resumed routing can enter spending
or decision nodes, and allowlisted `ask`/`names` can invoke vision providers
without updating `spent`. See review findings 1 and 2 before relying on replay.

`Agent.close()` / `Agent.close_all()` release saver connections. Test cleanup
must run after chat workers stop; the Telegram harness still leaves a connection
open and fails Windows temporary-directory cleanup (review finding 5).

When live focus has a generation but no stickers, `_ctx` uses `_last_focus` to
look for the newest earlier checkpoint with stickers for that generation,
scanning at most 40 checkpoints. A non-empty live selection takes precedence.

## Profiles (`out/profiles.sqlite`, `agent/profile.py`)

One row per person contains `user_id`, `name`, `tone`, and JSON columns for
`likes`, `dislikes`, `preferences`, and `edit_counts`. `Profile.set_facts` writes
name, likes, dislikes and extras to the table and JSON profile; tone and edit
counts also write both. First open imports the existing JSON facts. Existing
taste votes remain JSON-only, and Postgres fact synchronization remains in place.

- `detect_tone` runs inside `n_profile`. Explicit tone requests currently lack
  rule routing, and substring matching can mistake unrelated facts for tone
  instructions (review findings 3 and 4).
- Edit offers count `tweak`, `action`, `redesign`, or `editor`; `top_edit()` returns
  a kind only when it has a strict lead.
- A stored `brief` tone shortens the greeting. Unclear-edit replies can suggest
  phrasing for the person's most frequent edit kind.

Verification results and limitations are kept in the review. The six memory tests
pass, but the broader agent area is not green. Checks used disabled providers and
fakes; no paid-provider validation was performed.
