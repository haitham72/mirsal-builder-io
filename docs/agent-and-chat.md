# The agent and the chat: how it is built

The chat is an **interface**; structured state is the system of record. A language model orchestrates the deterministic pipeline and never
generates media or judges pixels. Every reference a user makes ends as an id like `G012/S3`; every change is a new generation with a parent;
the gate rules stay Python's (a human approves, the vision model only pre-reviews, Python's blocks are final).

The chat's backend **is the Studio**: the agent calls the same functions the Studio's buttons call (`Console.live`, `pipeline`, `gates`, search),
through `agent/tools.py`. Nothing is re-implemented.

```
 browser (console/agent.js)            server (console/server.py)                 engine
 ─────────────────────────             ──────────────────────────                 ──────
 What will you create today?  ──POST /api/chat/sessions/{id}/messages──►  Agent.prepare (session lock, user + "working" message)
 poll GET /api/chat/sessions/{id}      thread: Agent.execute ─► LangGraph:  understand → resolve → intent nodes → finish
 (steps appear as they are written)               │   tools: plan · estimate · create · animate · review · search · generation
 plan card · carousel · chips                     └──────────────► Console.live / pipeline / gates  (jobs, Higgsfield, verifier, gates)
```

## Files

Paths are relative to the Python package `mirsal/mirsal/`.

| file | job |
|---|---|
| `mirsal/agent/memory.py` | `SessionStore`: sessions in `out/sessions/S###.json` (files first, mirrored to Postgres, hot copy in Redis), the per-subject summary, feedback, traits, the reducer, `context(level)` |
| `mirsal/agent/resolver.py` | **deterministic first**: numbers, `#3`, ordinals, lists, ranges, exclusions, `G012/S3`, "it / that one", "previous" (the parent in this branch), a semantic word match, "make 5 like 2", role references; the intent rules (`classify`) and `settings_from` |
| `mirsal/agent/brain.py` | the small model: classify what the rules are unsure of, pick a sticker the words do not name, answer a question from the structured state, write the narrative summary. Schema-checked, one repair round, every call in `out/model_calls.jsonl`; failure = the deterministic answer |
| `mirsal/agent/tools.py` | `ConsoleTools` (the real engine) and `FakeTools` (tests): `plan` (Redis planner cache), `estimate`, `create`, `more`, `animate`, `review`, `search`, `generation`, `reference_from_sticker` |
| `mirsal/agent/graph.py` | the LangGraph state machine, the step trace, `Agent.prepare / execute / run_turn`, `hydrate` (the session as the page shows it) |
| `mirsal/console/agent.js`, `agent.css` | the screen (see below). The pure helpers are tested under node (`tests/js/agent.test.js`) |
| `mirsal/cache.py`, `mirsal/events.py` | Redis (see below) |
| `mirsal/vision/` | the vision judge |

## One turn

1. `understand`: rules first (`classify`); a model only when confidence is under 0.6. Intents: `NEW, ANOTHER, EDIT_STICKERS, ANIMATE, FEEDBACK, REVIEW,
   ASK, CHANGE_SETTINGS, SEARCH, CONFIRM, CANCEL, SMALLTALK, AMBIGUOUS`. A message can carry two ("I like 2 but make 5 happier" = feedback, then edit).
2. `resolve`: sticker ids from the text, the UI selection or the focus. Two equally plausible candidates ask **one short question** with chips; a clear
   mapping ("make number 3 happier") never asks.
3. an intent node: `new` (plan with the user's memory added, a priced plan card), `another`, `edit` (one 1x1 child generation per sticker, the rest stay),
   `animate`, `feedback`, `review` ("approve all but 5 and 6" = human decisions through `gates.review`), `ask` (answered from metadata, no generation),
   `search` (the pool), `settings`, `confirm` / `cancel`.
4. `finish`: focus, the interaction log, the reducer, the final step, the saved session.

**Spending.** Nothing costs credits until the user says so: a plan card shows the price with **Create / Not yet**, a typed "yes" works too. With
"Ask before spending" off (the settings popover, or "don't ask me") the agent creates at once. Without a provider (no Higgsfield CLI) generation is free and
starts immediately. A second message while a turn runs gets **409** (one turn per session, a Redis `SET NX` lock).

## Memory

A session is `{id, title, settings, focus, subjects[], preferences, feedback[], interactions[], summary, pending, messages[]}`.

- **`subjects`**: for every subject asked for, the metadata of its **passes** (generations): ids, prompt, grid, style, parent, counts (ready / approved /
  rejected), what the user liked and disliked. `summary_text()` renders it ("Subject 'banana': G012: 9 ready, 2 approved; liked S2, S7; disliked S3, S4 |
  G013 (from G012): ...") and **every turn starts from that summary, never from the history**.
- **`feedback`** is `TEMPORARY` (shapes the *next* generation only, then it is marked used) or `PERSISTENT` (only when the user says so: "I never want
  dark outlines"). Nothing is inferred about feelings: "I hate 4" is a negative on S4 and nothing more.
- **traits**: something asked for twice in the user's own words ("a wider range of emotions") becomes a note in the step trace and part of the next plan.
- **reducer**: every 15 interactions the older ones become a short narrative (a model call, or a deterministic digest); the structured summary is rebuilt from
  data each turn, so no id can be lost by a summariser.
- Postgres mirror (`migrations/004_sessions.sql`): `sessions`, `interactions`, `feedback` (one row per sticker), `generation_references` ("make 5 like 2").

## The step trace

The small queue the chat shows while the agent works (`message.steps[]`, `{kind, label, detail, status}` with kind `task | step | note | final`):

```
┌ generating teddy bear
│
●  expand prompt  >          (opens the nine names)
│
●  added your preferences  >
│
◇  you consistently asked for a wider range of emotions     (what the memory contributed)
│
└  plan ready · about 2 credits
```

While the agent works the last row reads "Thinking"; when it is done the trace collapses to one line ("5 steps · plan ready") that opens it again. The page polls the
session while anything still moves: only the **newest** assistant message holds the live plan card (the pending Create), and a read or paint that fails is retried
instead of ending the polling (a frame that throws must never freeze the chat on "Thinking").

## The screen (`#/agent`, the landing page of the Studio shell)

- **Hero**: "What will you create today?" over a cyan aurora that follows the pointer (a dot grid appears under it; reduced motion switches the ambient motion off).
- **Chats** in the second column (a drawer on phones); a bottom bar replaces the rail on phones.
- **Cards**: a plan card (subject, grid, style, names, price, Create / Not yet), a generation card with a **carousel** (swipe on touch, drag or arrows with a mouse,
  keyboard arrows, scroll-snap, dots; stickers appear as the engine finishes them; animated stickers play), a stickers card (search results and answers).
  Tap a sticker to select it: the selection travels with the next message ("make these more energetic"). "Open in Studio" opens the batch in the Studio.
- **Settings are two controls**: the grid (3x3 / 2x2) and "Ask before spending". The model pill shows what runs the assistant (local or cloud).

## Models (all hardcoded; `llm.py`)

| use | model | where |
|---|---|---|
| agent, judge, plan expansion | `qwen3.5-4b:2` (LM Studio, local, free, multimodal, a thinking model: calls send `reasoning_effort: "none"`) | `MIRSAL_LOCAL_MODEL` overrides |
| embeddings (pool search) | `text-embedding-nomic-embed-text-v1.5` (768-d) | `MIRSAL_EMBED_MODEL` overrides |
| fallback | OpenAI `gpt-4.1-mini` / `text-embedding-3-small` (dimensions 768) when LM Studio is down and `OPENAI_API_KEY` is set | |

Nothing asks LM Studio which models it has; reachability is a TCP connect cached for 60 s. `MIRSAL_LLM_PROVIDER`, `MIRSAL_AGENT_PROVIDER`, `MIRSAL_VISION_PROVIDER`
(`local | openai | auto`) pick the backend per use.

## The vision judge (`mirsal/vision/`)

A pre-reviewer, never the gate. `python -m mirsal judge G002 [--anim] [--force]` (or `POST /api/generations/{id}/judge`): each READY sticker is shown on a grey
background with what it was meant to be (the first approved sticker is the reference); the answer is JSON `{decision, confidence, scores, reasons[], suggested_emoji,
notes}` with reasons from a fixed list (DUPLICATE, WEAK_CONCEPT, AMBIGUOUS_ACTION, STYLE_DRIFT, IDENTITY_DRIFT, SEVERE_ARTIFACT, POOR_COMPOSITION, ANIMATION_RISK,
CHROMA_RISK, MISSING_REQUIRED_ELEMENT, ANATOMY_ERROR, OBJECT_DEFORMATION, EMOJI_MISMATCH, UNWANTED_TEXT). An animation is judged as four frames side by side.
The verdict is a history line with `actor = 'vlm'` at the same gate (it shows in the sticker detail) and `sticker.judge`; it never changes `review.*`. The answer is
parsed tolerantly, validated, repaired once, and on failure the sticker is **unjudged** (`FAIL_CLOSED`, the default; `DETERMINISTIC_ONLY` says nothing). Verdicts are cached in
Redis by image hash + model + judge version + context; calls are limited by `VISION_CONCURRENCY` (2). `recovery.plan_recovery` turns the rejections into a
**recommendation** (regenerate 1-2 cells as 1x1, or a new sheet after more than 2 rejected, at most 3 sheets and 2 attempts per cell; one sheet with the other key colour
on a colour problem) and spends nothing. **Uncalibrated** until Haitham labels 30 stickers (`docs/measurements.md`).

## Redis (disposable; `mirsal-redis`, port 6380)

Everything here can be rebuilt; nothing is written only to Redis; `FLUSHALL` costs cache misses. With Redis down, `mirsal/cache.py` runs the same calls in memory.
`REDIS_URL` is deliberately **not** read (the shared `.env` may hold another project's); use `MIRSAL_REDIS_URL`. Keys are `mirsal:u:{user}:...` with `user = local`.

| use | key | TTL |
|---|---|---|
| event stream per generation | `events:G###` (stream; the entry id is the SSE event id) | 24 h, capped at 1000 |
| session lock (one turn at a time) | `lock:session:S###` | 5 min |
| session hot copy | `session:S###` | 1 h |
| planner cache | `plan:{sha(normalised request, grid, style, ai, template versions, model)}` | 7 d |
| vision verdicts | `vlm:judge:{asset sha}:{model}:{judge version}:{context}` | 30 d |
| embeddings | `pool:vec:{sha(kind, text)}:{model}` | 30 d |
| idempotency | `idem:{scope}:{sha(key)}` | 24 h |

The planner key never merges a semantic difference ("dog as banana" and "dog with bananas" are different keys; a plan the AI failed to expand is not cached).
`mirsal doctor` shows the Redis engine; `GET /api/health` reports every dependency.

## Events and SSE

`pipeline.emit` writes `events.jsonl` (the record) and publishes the same event under the Phase 5 names: `generation_started, sheet_generated, sticker_processing,
sticker_ready / sticker_failed (one per sticker as it is cut, with `asset_url`), animation_started, animation_ready, video_sheet_ready, review_decided, pack_complete,
generation_failed`. `GET /api/generations/{id}/events` streams them (`text/event-stream`, replay from `Last-Event-ID` or `?after=`, a ping every few seconds, ends at a terminal
event or after 10 minutes). The generation continues when the browser goes away.

## Tests

`tests/test_agent.py` (27: plan, confirm, cancel, instant mode, memory, reducer, edits, ask, review, settings, search, errors, lock), `test_agent_resolver.py` (19), `test_agent_server.py`
(4: the whole chat through the real server on prepared sheets), `test_vision.py` (19), `test_cache.py` (20, memory and real Redis), `tests/js/agent.test.js` (8, node).
