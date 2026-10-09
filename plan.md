# plan.md — the chat: a stage selector (Prompt · Emojis · Animation · Export) and the batch follow-up

What an LLM builds next. Step 0 (the continuation fix) and Step 1 (the stage as state: `settings.stage`, `agent/stages.py`, creator `end`) are built; Steps 2–3 are left. Read `CLAUDE.md` first (the rules, especially 10, 11, 12, 13), then
`docs/agent-and-chat.md` (One turn, the agentic creator, "The chat in Telegram"), `docs/engine-and-studio.md` ("Batches, generations, regenerate", the
multi-batch Generate and "Packs in Earlier batches") and `docs/design.md` (one shell, one token set; read it before touching CSS). Test budget:
`docs/testing.md` (one narrowest run per change). No paid call in any test (`MIRSAL_NO_REAL_CLI`, `FakeTools` / the fake CLI). Delete each step when it is built;
delete this file when the plan is done; record what was built in `docs/agent-and-chat.md` (and `docs/api.md` for any route) in the same commit.

## Why

Haitham, 2026-10-09: (1) in the chat the person should choose **how far a request goes**, with a clean, minimal selector like the "thinking" level
picker of Claude / ChatGPT, but with four stages instead of low...max: **Prompt · Emojis · Animation · Export**. (2) A pack request assumes **batch 01**
(the first 9 actions), then offers, after the generation, **Regenerate | Batch 02 | Batch 03 | Batch 04**.

## Decided (Haitham; these were the plan's Q1–Q3, build with them)

- **D1. Export = the Library pack + Telegram**, automatic at the end of the run (the creator's existing end). The AddCollection API is a second button on
  the final card, never automatic (its credential rotation and live proof are W49).
- **D2. Animation / Export stop at G2 and G4 for one click**, unless the chat's "Approve everything for me" (the creator's bypass) is on (rule 10, as today).
- **D3. Default stage Emojis** (today's behaviour), web and Telegram.

## What exists to build on (do not rebuild)

- Turns: `agent/graph.py` (`prepare` / `execute`, `n_new` + pending create + confirm, `n_multi` + `_start_items` = several jobs under ONE card and ONE
  price, `n_confirm`, `n_animate` 1419–1442, pending names/describe 603–610, `_ask_vision_early` / `VISION_ASK` 1836–1861), `agent/tools.py`
  (`ConsoleTools.create` / `animate` / `pack_add` 396–402 / `telegram_send` 579 — the last two used only by the creator today; `FakeTools` 622–912),
  `agent/memory.py` (`settings`, `DEFAULT_SETTINGS`), `agent/resolver.py` (`classify` 464–550, `NEW_VERBS` 308, ANIMATE 512–513, ANOTHER 522–523),
  the web chat `console/agent.js` (cards, chips, `agSend(text, action)`).
- The agentic creator (`agent/creator.py`): `sheet > cut > look > approve > [video > approve_anim] > pack > telegram`, settings
  `settings.creator = {on, scope: images|video, bypass}`, driven by `Console.drive_creator`. It already stops and waits at G2 / G4 without bypass.
- Batches of a pack: `generation/tasks.py` `preview` (answers `batches_max`), `next_batch`, `session_state(out, gens)` (an emoji pack counts GRIDS:
  batch k is grid k = `actions.PRESETS` core 1-9, social 10-18, reactions 19-27, daily 28-36), `more_batches` (the next grids / bank actions, never a
  repeat, never past `MAX_BATCHES` 4). Routes `POST /api/plan/next`, `POST /api/plan/more`.
- Regenerate = a new generation of the same batch: `POST /api/live/sheet {from_generation, parent, regen_of}` (`flow/groups.py` family/pick).
- The Telegram chat (`services/tg_chat.py`): every chip of a reply is an inline button (`_chip_rows`), `/model` is a minimal button card
  (`models_card`). Pack / export of an existing batch works in chat through `n_export` (pending `pack_send`; built in Step 0).

## Step 2 — the selector in the web chat (screen second)

- One compact pill in the chat box's bar (left of Send), like the reasoning-level picker of Claude / ChatGPT: it shows the current stage
  ("Emojis ▾"); a click opens a small popover with the four stages, each one line: the name, a few words ("plan only, free" / "sheet and
  stickers" / "+ animation" / "+ pack and send"), the selected one checked. Keyboard: Tab to it, Enter opens, arrows move, Enter picks, Esc closes.
  It writes `settings.stage` (the same route as the other chat settings) and makes no chat turn. It replaces the creator's on/scope switches in the
  chat's settings (bypass stays where it is).
- Tokens and shell from `docs/design.md`; no new colours. Node test in `tests/js/` for the builder (four rows, the checked one, the label).
- Telegram: a fifth row on the `/model` card ("🧭 Emojis") opening the same four choices (`tg_chat.models_card`), and a `/stage` command that sends
  the same card. A new Telegram chat starts on `emojis`.

## Step 3 — a pack request starts at batch 01 and the follow-up card

- A pack request ("generic emojis", "a teddy bear pack", any request whose plan has `batches_max > 1`) plans **batch 01** only: for an emoji pack
  the first grid (core-v1, actions 1-9), else the first 9 bank actions. The plan card says "Batch 01 of 04" and which grid.
- After the batch reaches the stage's end (stickers cut for `emojis`, animations for `animation`, sent for `export`; for `prompt`, right after the
  plan), the chat posts ONE follow-up card: **Regenerate** · **Batch 02** · **Batch 03** · **Batch 04**. Numbers are batch numbers of THIS pack,
  as in the Studio's picker: only the ones still possible are shown (`session_state(out, the chat's batches)` -> `existing`, `batches_max`); "Batch 03"
  with one batch made makes batches 02 and 03 (two sheets, one card, one total price, one go-ahead, `_start_items`-style); a transformation
  (one character changed) shows Regenerate only. Each new batch runs to the same stage as the chat's stage.
- Regenerate = a new generation of the batch (the Studio's Regenerate: `from_generation`, `parent`, `regen_of`), priced on the button.
- New chat action types, handled in `agent/graph.py` like the other buttons: `{type: "batch_more", to: k}` (plans via `tasks.more_batches` with the
  session's used grids/actions, then the same go-ahead card) and `{type: "regenerate", generation}`. Typed words must also work: "next batch",
  "batch 3", "make the rest of the pack", "regenerate it".
- The batches the chat makes share the pack in Earlier batches automatically (`pipeline._packs`: same request without grid names, same person,
  within 6 h); the chat's generation cards should say "Batch 02 · social" etc.
- Telegram gets the follow-up card as inline buttons for free once it is a chip row on a message (`tg_chat._chip_rows`); check it renders.
- Tests: resolver tests for the typed forms; `tests/test_chat_batches.py` on `FakeTools` (batch 01 first, the follow-up card's buttons from the
  session state, "Batch 03" starts two sheets after one go-ahead, Regenerate, a transformation gets Regenerate only, never a fifth batch);
  `tests/test_tg_chat.py` extended (the follow-up card is buttons).

## Step 4 — docs and the look

- `docs/agent-and-chat.md`: a section "Stages and the batch follow-up" (state, the mapping onto the creator, the card, Telegram);
  `docs/api.md` (`settings.stage`, the new actions); `docs/design.md` (the pill and popover); `README.md` only if the index changes.
- One browser look at the end (Haitham's eyes, W1-style): the pill, the popover, the follow-up card.
