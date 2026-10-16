# Review brief: durable LangGraph turns + SQLite profiles (uncommitted, 2026-10-16)

For a reviewing LLM. Scope is ONLY the uncommitted edits on branch `redesign-ui-ux`
on top of `6b3f297f` (already pushed). Goal of the change: the chat's LangGraph
router finally uses LangGraph powers — a checkpointer for durable turns, and a
per-user profile table it reads back. Approvals, cards, spending, and the engine
are intentionally untouched.

## Change inventory (355 insertions, 10 deletions + 2 new files)

| file | change |
|---|---|
| `mirsal/mirsal/agent/graph.py` | `SqliteSaver` checkpointer, `thread_id=sid`, safe resume, focus fallback, tone/edit hooks, `Agent.close/close_all` |
| `mirsal/mirsal/agent/profile.py` | `ProfileTable` (SQLite), `detect_tone`, dual-write into `Profile`, `tone/set_tone/count_edit/top_edit` |
| `mirsal/tests/test_agent_memory.py` | NEW: 6 tests (checkpoints, resume, focus, table, tone, edit counting) |
| `mirsal/tests/test_agent.py`, `test_llm_local.py`, `test_profile.py` | close saver connections in tearDown/cleanup (Windows file-lock fix) |
| `mirsal/requirements.txt` | `langgraph-checkpoint-sqlite>=3.1` |
| `.gitignore` | ignore `checkpoints.sqlite*`, `profiles.sqlite*` |
| `docs/agent-and-chat/24-*.md` + index row | design record |

Environment (not in git): venv gained `langgraph-checkpoint 4.3.0`,
`langgraph-checkpoint-sqlite 3.1.2` (+ transitive `aiosqlite`, `sqlite-vec`, unused).

## Design decisions to verify

1. **Checkpoints:** `out/checkpoints.sqlite`, one per `out/` (a `MIRSAL_OUT` copy gets
   its own), shared process-wide via `_saver_for` (refcounted). `Turn` pickles with
   `__getstate__` dropping the live trace/lock; a node guard rebinds a restored
   turn's trace. Serde is `JsonPlusSerializer(pickle_fallback=True)` — v4's default
   msgpack serde rejects the `Turn` dataclass outright (observed:
   `TypeError: Type is not msgpack serializable: Turn`).
2. **Resume rule (conservative):** a dead turn replays only if the pending node is in
   `SAFE_RESUME_NODES` (8 spend-free, decision-free nodes) AND `spent == 0`.
   Anything else keeps the legacy interrupted message. No double-spend path by
   construction — confirm no listed node creates jobs or writes reviews.
3. **Focus fallback:** `_last_focus` scans checkpoint history (cap 40) for the newest
   earlier turn with stickers for the same batch; used in `_ctx` only when the live
   focus is empty. Never overrides a non-empty focus.
4. **Profiles:** `profiles(user_id PK, name, tone, likes/dislikes/preferences/edit_counts
   JSON, updated_at)`. Every table write mirrors into the JSON export (readable,
   existing readers untouched); first open imports the JSON. `top_edit()` requires a
   strict lead. Tone is detected from fixed word lists, confirmed in the reply.
   Visible reads: brief-tone greeting, most-used-phrasing hint on unclear edits.
5. **Lifecycle:** server never closes (one conn per `out/`, intended); tests must
   close (`Agent.close` / `close_all`), or Windows tempdir cleanup fails.

## Verification evidence (run 2026-10-16, this PC, providers off)

- `tests.test_agent_memory`: 6/6 pass.
- `mirsal test area agent`: 304 tests, 5 failures + 54 errors — same counts and same
  5 named failures as the untouched base (verified via `git stash` + rerun). The 5 failures
  (`test_a_second_message...`, 2× `test_llm_catalog`, `test_chat_interaction`,
  `test_chat_multi` cases) and the 54 errors (sandbox socket blocks WinError 10013,
  DB-skips) pre-exist and are out of scope.

## Review checklist

- [ ] `SAFE_RESUME_NODES` audit: prove each listed node spends nothing and writes no
  decisions (a spend node in that set breaks the no-double-spend argument).
- [ ] Pickle surface: `Turn.__getstate__` drops exactly `trace`/`_lock`; confirm no
  other field can hold a lock/client (Brain/tools are NOT on Turn — confirm).
- [ ] Resume race: `prepare` resumes while holding the session lock; confirm the
  resumed invoke cannot interleave with `drive_creator` on the same sid.
- [ ] `_last_focus` cost: history scan per `_ctx` call when focus is empty — confirm
  the cap bounds it and failures fall back to `[]` (never break a turn).
- [ ] Dual-write gaps: every `Profile` mutation path writes table AND JSON, or say
  which one is intentionally single-sided.
- [ ] `profiles.sqlite`/`checkpoints.sqlite` under a `MIRSAL_OUT` copy and the real
  `out/`: correct files, ignored ones stay untracked (`git status` clean of them).
- [ ] Re-run: `python -m unittest tests.test_agent_memory` and
  `python -m mirsal test area agent`, then diff the failure set against the base list above.

## Explicit non-goals (do not ask for them in this review)

`interrupt()`-based spend approvals, Postgres/Redis savers, engine changes, server
route changes, UI redesign. Paid-provider runs (need Haitham's go-ahead first).

## Review results (2026-10-16)

Review only: the findings below were reproduced or traced in the uncommitted
changes against `6b3f297f`. No fixes were applied. The safe-resume claim is not
established; the two P1 findings must be resolved before relying on it.

### Findings

1. **[P1] Resume can enter spending and decision nodes.**
   `mirsal/mirsal/agent/graph.py:320` checks only the pending `snap.next`, then
   resumes the unrestricted graph. An allowlisted `resolve` can route to `review`
   or `confirm`. Fake-only reproductions observed both paths, including the old
   confirmation executing before a newly submitted `cancel` message was handled.
   Enforce the safety boundary throughout resumed execution, rather than checking
   only its first node.

2. **[P1] Allowlisted nodes can repeat paid vision calls.**
   `mirsal/mirsal/agent/graph.py:52` includes `ask` and `names`. The former can
   call `_describe`; the latter calls `_run_names`. Both can reach vision
   providers without updating `Turn.spent`. A fake `name_proposals` call that
   raised after recording its invocation left `next=('names',)` and `spent=0`;
   the next message invoked it again (two calls total). These nodes are not
   spend-free and cannot safely replay on that predicate.

3. **[P2] Ordinary tone requests do not reach profile handling.**
   `mirsal/mirsal/agent/graph.py:2463` detects tone only inside `n_profile`, but
   the rule router does not recognize explicit tone requests. In fake-only turns,
   `be brief` and `keep it short` each produced a sticker plan and left tone
   unset. Add explicit routing for tone requests; the existing greeting test
   sets tone directly and does not cover this input path.

4. **[P2] Unrelated profile facts silently change reply tone.**
   `mirsal/mirsal/agent/profile.py:245` uses substring matching without requiring
   a request about reply style. Reproductions: `my name is Shorty` saved `brief`,
   and `I like warm colours` saved `warm`. Match explicit tone instructions,
   with word boundaries and negation handling, rather than arbitrary facts.

5. **[P2] Saver cleanup is incomplete in the Telegram test harness.**
   The saver acquired by `Agent.__init__` at
   `mirsal/mirsal/agent/graph.py:169` remains open for agents created through
   the Telegram test server. The agent-area run errors in
   `tests.test_tg_chat.TelegramChatTests.tearDownClass` with Windows error 32
   while deleting `out/checkpoints.sqlite`. Close these saver connections after
   chat workers stop and before temporary-directory cleanup.

### Verification and limits

Providers were disabled (`MIRSAL_NO_REAL_CLI=1`, `MIRSAL_LLM_PROVIDER=none`);
the targeted reproductions used fakes/mocks. No paid provider was called.

- `python -m unittest tests.test_agent_memory`: **6 tests passed**.
- `python -m mirsal test area agent`: **322 tests, 5 failures, 10 errors**.
- An isolated archive of base `6b3f297f`, using the same Python environment:
  **322 tests, 4 failures, 9 errors**. The working checkout was not stashed or
  modified for this comparison.
- The additional error is the Telegram checkpoint file lock above. The other
  differing result is
  `test_cloud_vision_inherits_the_configured_model_unless_explicitly_overridden`
  (`openai:gpt-6-luna` versus `router-vision`). That test is listed as pre-existing
  in the original brief; the isolated archive does not reproduce the checkout's
  local configuration, so this difference is not attributed to the memory edits.
- `git diff --check` passed. `git check-ignore` confirmed that
  `mirsal/out/checkpoints.sqlite` and `mirsal/out/profiles.sqlite` are ignored.
  Arbitrary `MIRSAL_OUT` copy locations were not independently verified.

Other inspected properties: `Turn.__getstate__` removes `trace` and `_lock`;
Brain/tools are held on Agent rather than Turn. Resume runs inside the same
session-lock scope used by `drive_creator`. `_last_focus` requests at most 40
checkpoints and returns an empty list if history retrieval fails. These checks
do not resolve the replay-safety findings. A complete dual-write audit remains
open; existing taste votes still use the JSON profile.
