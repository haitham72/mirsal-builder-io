# Durable turns and SQLite profiles: review (2026-10-16)

Reviewed implementation: `3f35dcd3` on `redesign-ui-ux`, against base
`6b3f297f`. The findings below remain open; no fixes were applied. The safe-resume claim is not
established; the two P1 findings must be resolved before relying on it.

## Findings

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

## Verification and limits

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
do not resolve the replay-safety findings. A complete dual-write audit remains
open; existing taste votes still use the JSON profile.
