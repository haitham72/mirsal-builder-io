# Memory

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

A session is `{id, title, settings, focus, subjects[], preferences, feedback[], interactions[], summary, pending, messages[]}`.

- **`subjects`**: for every subject asked for, the metadata of its **passes** (generations): ids, prompt, grid, style, parent, counts (ready / approved /
  rejected), what the user liked and disliked. `summary_text()` renders it ("Subject 'banana': G012: 9 ready, 2 approved; liked S2, S7; disliked S3, S4 |
  G013 (from G012): ...") and **every turn starts from that summary, never from the history**.
- **`feedback`** is `TEMPORARY` (shapes the *next* generation only, then it is marked used; a disliked sticker's pose goes into that plan as "Avoid the poses of banana flat, banana squashed", not only into a note) or `PERSISTENT` (only when the user says so: "I never want
  dark outlines"). Nothing is inferred about feelings: "I hate 4" is a negative on S4 and nothing more.
- **traits**: the fixed regex table recognizes requests for a wider emotional range, bolder expressions, no dark outlines, an anime-inspired look, and a less cartoony look. A matching request must appear in at least two interactions before becoming a note in the next plan. This is a small deterministic vocabulary, not general model-based preference extraction.
- **reducer**: every 15 interactions the older ones become a short narrative (a model call, or a deterministic digest); the structured summary is rebuilt from
  data each turn, so no id can be lost by a summariser.
- **outside batches**: `summary_text()` also names the five newest batches the Studio or the command line made (generations this chat never recorded as a pass, only those the caller may see), so "what did you just create" has an answer. The chat can talk about them, and naming one adopts it ("Studio batches" above).
- **bounded**: a session keeps its newest 400 messages, 300 interactions (only already-summarised ones are dropped, `summary.upto` follows) and 200 feedback entries (`memory.MAX_*`); subjects, passes and likes are never trimmed. Message and interaction ids come from the last id, not from the length, so they stay unique.
- **a turn that died with its server** leaves a message with `status: working`. Once its session lock is free, `hydrate` or the next `prepare` marks it `error`, preserves the saved trace, and appends one interruption note directing the person to check the Queue before retrying. It makes no promise that nothing was spent: a job may already exist. With real Redis, a dead server's lock can remain until its TTL expires.
- Postgres mirror (`migrations/004_sessions.sql`): `sessions`, `interactions`, `feedback` (one row per sticker), `generation_references` ("make 5 like 2").

**Structured access and routing.** `summary_structured()` returns a detached dictionary of subjects/passes, focus, preferences, repeated traits and the latest completed generation. `focus_context()` reads focus id, selected sticker ids, grid/style and sticker keys. On a low-confidence turn, `Brain.classify` receives a separate focus fence before the chat summary: at most three selected sticker ids and three keys, capped at 1,000 characters. It carries no images or full sticker prompts. The chat summary is rendered from structured state; `llm.fence('CHAT', ...)` still caps that prose at 2,000 characters. `_route_context` already includes the profile, last question and held plan. There is no LangGraph checkpointer or automatic replay of a crashed turn.
