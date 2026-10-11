# plan.md — after the redesign (2026-10-11)

What an LLM does next. The stages (Prompt · Stickers · Animation · Telegram · Export) and the batch follow-up are built (`1e28524`, `2dba73f`, `4239bff`, `d66c647`);
the architecture is in `docs/agent-and-chat.md` "Stages and the batch follow-up". Read `CLAUDE.md` first; test budget: `docs/testing.md` (one narrowest
run per change, no paid call, `MIRSAL_LLM_PROVIDER=none`). Delete each step when it is built; delete this file when the plan is done.

## The redesign (branch `edit-design`) — built 2026-10-11, waits for Haitham

Every phase of `docs/redesign_plan.md` §5 is built. Next: Haitham looks at it in the browser (restart with `serve --reload`, hard reload); the outside
review against §9; then D3 / D4 (§5 "Open"). Merge into `main` only when Haitham says so.

## Step 1 — prove the follow-up through the real server (fakes only)

The follow-up is tested on `FakeTools` only. Add ONE test in the style of `tests/test_creator_live.py` (the real console, the fake Higgsfield CLI, the
fake Bot API): a request at the Emojis stage -> Create -> the sheet is cut -> polling `GET /api/chat/sessions/{id}` posts exactly one follow-up message
with Regenerate · Batch 02 · 03 · 04 -> `{type: "batch_more", to: 3}` -> one go-ahead starts two sheets. Assert the counts of `tasks.session_state`
(`existing`) match the chat's own rows. If the poll hook (`console/server.py`, `_agent.batch_followup`) is slow on a chat with many batches, cache the
"said" check before loading cards.

## Step 2 — the Animation / Export queue through the real creator driver

`sess["creator_queue"]` (batches 02+ at the Animation / Export stages) is tested only by its start and Stop. Add ONE `Console.drive_creator(block=True)`
test on the fake CLI with bypass on: two queued batches run one after the other, each ends at its `end`, the last done message carries the follow-up.

## Step 3 — the failures that were left as notes (separate commit, only if Haitham asks or a step above touches them)

They fail the same way without the stages work (checked by stash): `tests.test_js` StudioActionTests x3 + 1 error (Earlier batches title / list,
green-screen panel in `batchHtml`, action registration, a click on a batch) and `mirsal test area agent/graph` x3 (`test_live`: video-prompt wording x2,
history card `KeyError: 'G002'`). Read each assertion against the current Studio code; fix the test when the code's behaviour is the documented one,
the code when it is not. Never a loop: one run per fix.

## Not an LLM's (stays in `docs/waiting-for-haitham.md`)

The browser look of the pill, the popover, the follow-up card and Telegram `/stage` (item 1); a real paid run of a stage (item 6).
