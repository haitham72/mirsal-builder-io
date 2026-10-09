# plan.md — after the chat's stages and batch follow-up (2026-10-09)

What an LLM does next. The stages (Prompt · Emojis · Animation · Export) and the batch follow-up are built (`1e28524`, `2dba73f`, `4239bff`, `d66c647`);
the architecture is in `docs/agent-and-chat.md` "Stages and the batch follow-up". Read `CLAUDE.md` first; test budget: `docs/testing.md` (one narrowest
run per change, no paid call, `MIRSAL_LLM_PROVIDER=none`). Delete each step when it is built; delete this file when the plan is done.

## Step 0 — Haitham does not see the selector (2026-10-09, FIRST)

Haitham: "I still don't see a slider from 'prompt' all the way to 'export to API' at all." Three gaps between what he expects and what was built:

1. **Nothing visible yet.** The pill lives only on the AI screen (`#/agent`), inside the chat box, left of Send (`agent.js` `drawStage`, `#ag-stage`). A server
   started before `2dba73f` serves the old `agent.js`: restart `python -m mirsal serve` from `mirsal/.venv` (Windows) and hard-reload (Ctrl+F5). Check it is
   there first; if it still is not, debug `drawStage` (is `#ag-stage` in the markup, is `drawBar` reached on the AI screen) before anything else.
2. **A pill is not a slider.** The plan said "a picker like Claude / ChatGPT's reasoning level", and a dropdown pill was built. Haitham expects a **visible
   slider / stepper**: Prompt -> Emojis -> Animation -> Export, every stage on screen at once, the current one marked, one click (or drag, or arrow keys)
   to move. Rebuild the control as a 4-stop (5 with the API, below) segmented slider in the chat bar, same route (`settings.stage`), no turn, tokens from
   `docs/design.md`; keep `AIU.stageOf`; update `tests/js/chat_stage.test.js` and `docs/design.md` "The stage pill".
3. **"Export to API" does not exist in the chat.** D1 made Export = Library pack + Telegram and the AddCollection API "a second button on the final card";
   that button was NOT built (`graph.py` / `agent.js` never call `services/collection.py`). Either (a) build the button on the Export run's done message
   (the pack's existing AddCollection export route, never automatic, its credentials and live proof stay W49), or (b) if Haitham wants it as the slider's last
   stop, add a fifth stage `api` (Export + the AddCollection send) to `agent/stages.py`, the creator's `end`, the settings route, OpenAPI, Telegram `/stage`.
   Ask Haitham (a) or (b) once, with (a) as the recommendation while W49 is open.

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
