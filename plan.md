# plan.md — after the redesign (2026-10-11)

What an LLM does next. The stages (Prompt · Stickers · Animation · Telegram · Export) and the batch follow-up are built (`1e28524`, `2dba73f`, `4239bff`, `d66c647`);
the architecture is in `docs/agent-and-chat.md` "Stages and the batch follow-up". Read `CLAUDE.md` first; test budget: `docs/testing.md` (one narrowest
run per change, no paid call, `MIRSAL_LLM_PROVIDER=none`). Delete each step when it is built; delete this file when the plan is done.

## Step A — refactor the screen scripts, no behaviour change (FIRST; a fresh session, Opus on medium)

Why: `mirsal/mirsal/console/generate.js` (~850 lines), `agent.js`, `app.js`, `live.js`, `packs.js` put a whole function on one line (300-900 characters),
so every read and edit costs a lot of tokens. Goal: the same behaviour, readable files of ~150-300 normal-width lines, one feature per file.

1. **Test helpers first.** Several node tests read code by "one statement per line" (`statement(marker)` in `tests/js/cell_op.test.js`,
   `sheet_cells.test.js`, `remove_batch.test.js`, `history_card.test.js`, `console_vm.js`; `block()` in `tests/test_js.py`). Change them to load whole
   files (`loadConsole([...files])`, as `project_map.test.js` does) or to find a statement by its marker and its matching closing brace. Run the node
   suite once: 302 pass is the baseline (one Python failure is old: `test_agent.test_a_second_message_while_one_is_running...`, leave it).
2. **Split `generate.js`** by feature, loaded in this order in `index.html` and listed in `UI_FILES` (`console/server.py`): `studio-core.js` (state GS /
   SES / GM, tick, gview, the toolbar), `studio-tiles.js` (tileHtml, cellOp, the allow queue ALQ, issues/marks), `studio-sheet.js` (sheetPanel,
   videoPanel, cutSvg, the Full-analysis dialog), `studio-prompt.js` (Prompt tab, pre-batch draft GD, pd*), `studio-animate.js` (animate, Add-to-pack
   wizard PW), `studio-panel.js` (gmodal, the sticker panel). Same for `agent.js` (`chat-core.js`, `chat-cards.js`, `chat-stage.js` with the pure
   `AIU` part kept exported for node) and `app.js` (shell/rail/router, library, settings). Format each statement over several lines (2-space indent,
   lines <= 140 chars); keep every name, every `ACT.<name>` and every `data-act` exactly.
3. **The guard:** `python -m unittest tests.test_ui_inventory` must pass with NO `renamed`/`retired` entry (nothing moved but files); regenerate
   `docs/ui_inventory.md` (`python -m mirsal.console.inventory`, splice the tables). Run `tests.test_js` + the node suite once at the end.
4. **Docs:** `docs/architecture.md` §6 (the script list and load order). One commit: "Refactor: split and format the console scripts (no behaviour change)".
5. Then (separate commits, optional): halve `CLAUDE.md` (keep the rules, move dated history into the area docs); shorten `docs/design.md` and
   `docs/agent-and-chat.md` entries to one paragraph per feature, rewritten in place.

## Step B — unified model selection and Luna (after Step A)

Today: `services/llm.py` talks to ONE OpenAI-compatible endpoint (`MIRSAL_CLOUD_URL`, `.env` = Nararouter) with `MIRSAL_LLM_MODEL` and
`MIRSAL_LLM_FALLBACK`; the chat's model pick (`settings.models.ai`) only lists LM Studio's local models.

1. **Providers as data** (`services/llm.py`, `.env`): `nararouter` (`MIRSAL_CLOUD_URL` + `OPENAI_API_KEY`) and `openai` (`MIRSAL_OPENAI_KEY`,
   `https://api.openai.com/v1`, optional). A model id is `provider:model` (e.g. `nararouter:mimo-v2.6-flash-free`); a bare id keeps today's meaning.
2. **Only vision models from Nararouter** (Haitham, 2026-10-11): the app sends pictures (the vision judge, names, the chat), so the list is an
   allow-list in code, `NARAROUTER_VISION`: `agnes-2.5-flash`, `exo-stealh`, `agnes-3-flash`, `mimo-v2.6-flash-free`,
   `muse-spark-1.3-contributor-free`, `step-5-preview`, `stepfun-3.7-flash` (the router page tags them "Vision"; free or free above a balance).
   Never offer the text-only ones (`jev`, `laguna-s-2.1`, `nemotron-3-ultra-free`, `nemotron-3.5-lightning-free`). Intersect with `GET /v1/models`
   so a model the router drops disappears. Add to this list only a model whose router page says Vision.
3. **Defaults:** replace every `gpt-4o` / `gpt-4o-mini` / `gpt-4.1-mini` default with **Luna**: `DEFAULT_MODEL` in `services/llm.py`,
   `DEFAULTS["ai"]` in `services/tg_chat.py`, the `.env.example` comments. Use `gpt-5.6-luna` on Nararouter (check its router page: if it is NOT
   tagged Vision, use it for text-only calls and keep `mimo-v2.6-flash-free` for calls with images; the fallback stays `agnes-2.5-flash`).
   Use the same provider/model resolution for chat, still descriptions, captions, naming and the vision judge; preserve explicit vision overrides.
   Never fall back to an unrelated hardcoded model id that the configured endpoint does not offer. Validate image support before sending a still.
   Haitham's `.env` today: `MIRSAL_LLM_MODEL=mimo-v2.6-flash`, `MIRSAL_LLM_FALLBACK=agnes-2.5-flash` (do not edit `.env` yourself; tell him the lines).
4. **One model list route:** `GET /api/llm/models` returns `{local: [...], nararouter: [...vision allow-list ∩ router], openai: [...]}` with
   `{id, label, vision, free}`. Put the grouped Local / Nararouter / OpenAI LLM list in the **top-right model control only**,
   opening beside that control (`ag-engine` / `setEngine`), and reuse it in Settings > AI and Telegram `/model`.
   A pick is `settings.models.ai = "provider:model"` (`services/llm.FORCE`); display the actual selected provider and model.
   Keep the **left composer selector** for image/video models, Creative / Predefined (**Predefined by default**) and Ask before spending.
   Sheet size stays in its existing outside chip. Keep the **right task-stage popover** limited to the stage slider; no models or options inside it.
   Reuse the existing shared catalogs/selectors, and retain saved choices when opening and closing any popover.
5. **Tests on fakes only** (`tests/test_llm_backend.py` style: patch `_post`; never call the router): the allow-list filters text-only models,
   `provider:model` routes to the right URL and key, Luna is the default, vision respects image capability and explicit overrides, the fallback still works.
   Cover the reported unavailable-model 404, top-right popup anchoring, saved selections and absence of duplicated selectors. Docs: `docs/agent-and-chat.md` "Models".

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
