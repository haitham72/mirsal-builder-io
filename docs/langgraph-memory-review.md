# Durable turns and SQLite profiles: review (2026-10-16)

Reviewed implementation: `3f35dcd3` on `redesign-ui-ux`, against base
`6b3f297f`. The original findings below are retained as history. All five were
fixed on 2026-10-19; the evidence and limits below supersede the original status.

## Findings

1. **[P1] Resume can enter spending and decision nodes.**
   **Fixed:** `dd8ee1bd` advances one node at a time and rechecks every checkpoint.
   Fake resolve → review/confirm regressions failed before and passed after;
   the old confirmation never runs ahead of the new cancel.
   `mirsal/mirsal/agent/graph.py:320` checks only the pending `snap.next`, then
   resumes the unrestricted graph. An allowlisted `resolve` can route to `review`
   or `confirm`. Fake-only reproductions observed both paths, including the old
   confirmation executing before a newly submitted `cancel` message was handled.
   Enforce the safety boundary throughout resumed execution, rather than checking
   only its first node.

2. **[P1] Allowlisted nodes can repeat paid vision calls.**
   **Fixed:** ask/names and other provider-capable nodes are excluded from replay;
   resolve's ask/edit fallback is excluded too. A fake invocation that records
   then raises was called twice before and once after. A follow-up fake found
   finish's optional model summarizer; replay now uses the deterministic reducer.
   `mirsal/mirsal/agent/graph.py:52` includes `ask` and `names`. The former can
   call `_describe`; the latter calls `_run_names`. Both can reach vision
   providers without updating `Turn.spent`. A fake `name_proposals` call that
   raised after recording its invocation left `next=('names',)` and `spent=0`;
   the next message invoked it again (two calls total). These nodes are not
   spend-free and cannot safely replay on that predicate.

3. **[P2] Ordinary tone requests do not reach profile handling.**
   **Fixed:** `afc0f3f6` routes explicit requests to PROFILE by rules. End-to-end
   fake turns for be brief / keep it short / stay formal / be warm persist tone
   and create no sticker plan (failing then passing).
   `mirsal/mirsal/agent/graph.py:2463` detects tone only inside `n_profile`, but
   the rule router does not recognize explicit tone requests. In fake-only turns,
   `be brief` and `keep it short` each produced a sticker plan and left tone
   unset. Add explicit routing for tone requests; the existing greeting test
   sets tone directly and does not cover this input path.

4. **[P2] Unrelated profile facts silently change reply tone.**
   **Fixed:** `afc0f3f6` requires a request verb and a whole style phrase, rejecting
   negations. Shorty, warm colours, negations and partial words failed before
   and pass after, including persisted profile checks.
   `mirsal/mirsal/agent/profile.py:245` uses substring matching without requiring
   a request about reply style. Reproductions: `my name is Shorty` saved `brief`,
   and `I like warm colours` saved `warm`. Match explicit tone instructions,
   with word boundaries and negation handling, rather than arbitrary facts.

5. **[P2] Saver cleanup is incomplete in the Telegram test harness.**
   **Fixed:** `afc0f3f6` closes all savers after workers stop and before temporary
   cleanup. The real fake-Telegram turn test reproduced WinError 32 then passed.
   The saver acquired by `Agent.__init__` at
   `mirsal/mirsal/agent/graph.py:169` remains open for agents created through
   the Telegram test server. The agent-area run errors in
   `tests.test_tg_chat.TelegramChatTests.tearDownClass` with Windows error 32
   while deleting `out/checkpoints.sqlite`. Close these saver connections after
   chat workers stop and before temporary-directory cleanup.

## Historical verification and limits (2026-10-16)

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
  in the superseded review brief; the isolated archive does not reproduce the checkout's
  local configuration, so this difference is not attributed to the memory edits.
- `git diff --check` passed. `git check-ignore` confirmed that
  `mirsal/out/checkpoints.sqlite` and `mirsal/out/profiles.sqlite` are ignored.
  Arbitrary `MIRSAL_OUT` copy locations were not independently verified.

Other inspected properties: `Turn.__getstate__` removes `trace` and `_lock`;
Brain/tools are held on Agent rather than Turn. Resume runs inside the same
session-lock scope used by `drive_creator`. `_last_focus` requests at most 40
checkpoints and returns an empty list if history retrieval fails. These checks
were supplemented by the fixes above. A complete dual-write audit remains
open; existing taste votes still use the JSON profile.

## Final engineering verification — 2026-10-19

Seven targeted checkpoint/profile tests passed across their narrow runs; the
fake Telegram turn/cleanup passed after reproducing WinError 32. The final
`mirsal test area agent` run: **322 tests, 4 failures, 9 errors**, matching the
isolated base (previous checkout: 5/10). The model-preference assertion now
isolates both saved preference and dotenv sources and passes by itself.

Remaining baseline failures/errors concern concurrent session refusal, historical
pack wording, model validation/catalog fallback mocks and source-location UI
assertions. They are not silently treated as green. No provider was called.
Node JS: **389/389**; Python console wrapper: **18/18**. The stale `rxedit`
expectation was replaced with current preset/tab wiring.
