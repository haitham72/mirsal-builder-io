# plan.md — the chat: a continuation fix, a stage selector (Prompt · Emojis · Animation · Export) and the batch follow-up

What an LLM builds next. Step 0 goes first (it fixes a live mis-route); Steps 1–3 are the feature. Nothing here is built yet (2026-10-09). Read `CLAUDE.md` first (the rules, especially 10, 11, 12, 13), then
`docs/agent-and-chat.md` (One turn, the agentic creator, "The chat in Telegram"), `docs/engine-and-studio.md` ("Batches, generations, regenerate", the
multi-batch Generate and "Packs in Earlier batches") and `docs/design.md` (one shell, one token set; read it before touching CSS). Test budget:
`docs/testing.md` (one narrowest run per change). No paid call in any test (`MIRSAL_NO_REAL_CLI`, `FakeTools` / the fake CLI). Delete each step when it is built;
delete this file when the plan is done; record what was built in `docs/agent-and-chat.md` (and `docs/api.md` for any route) in the same commit.

## Why

Haitham, 2026-10-09: (1) in the chat the person should choose **how far a request goes**, with a clean, minimal selector like the "thinking" level
picker of Claude / ChatGPT, but with four stages instead of low...max: **Prompt · Emojis · Animation · Export**. (2) A pack request assumes **batch 01**
(the first 9 actions), then offers, after the generation, **Regenerate | Batch 02 | Batch 03 | Batch 04**. (3) A transcript the same day ("girl emirati"):
"create video and export" planned a NEW subject called "video and export" instead of animating G127, and a names/describe turn reported "no finished
stickers to look at yet" on a batch with nothing cut. Step 0 fixes both before the feature lands on top.

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
  (`models_card`). Pack / export of an existing batch does not exist in chat today outside the creator.

## Step 0 — the continuation fix (first: the transcript bug)

- **Order in `classify`:** with `has_generation`, continuation verbs beat `NEW_VERBS` — put the match BEFORE the `NEW_VERBS` branch (~line 533), because
  "create video" contains "create". Pattern: `\b(video|videos|animate|animated|animation|export|send|pack|telegram)\b` with an optional
  it/them/these/those/this/that: video-words → ANIMATE (the existing node, on the focus batch); export-words → a new EXPORT intent. "create video and
  export" with G127 in focus ends as a pending animate of G127 — the reply says in one line that pack + send follow after the animation — never a plan
  for a subject called "video and export". "animate G001"-by-name adoption stays as it is (`tests/test_agent.py:554`).
- **New `n_export`:** no READY animations on the focus batch → pending animate first ("I'll animate G127 first, then pack and send it"); animated →
  pending `{type: "pack_send", generation}` → "Pack G127 (N stickers) and send it to Telegram?" with chips `Pack and send: confirm` / `Not yet: cancel` →
  confirm runs `tools.pack_add` + `tools.telegram_send` (both free; the confirm is for the outward step). Typed forms that must work: "export",
  "export it", "send to telegram", "pack it and send", "create video", "make a video", "video it".
- **Names/describe guard** (pending names/describe, `n_confirm` ~603–610): zero `ready_indexes` → no vision call, one calm sentence ("<Name> has no finished
  stickers yet — I'll look at them once they're cut"), pending dropped, nothing spent. Same guard shape as `n_animate` 1426–1429.
- Tests: resolver intent cases in `tests/test_agent_resolver.py`; new `tests/test_chat_continue.py` on `FakeTools` (video-words → pending animate of the
  focus batch with no `create` call; export on an animated batch → `pack_add` + `telegram_send` after confirm; export on an unanimated batch → animate
  first; names with zero ready → no vision call and the calm sentence).

## Step 1 — the stage, as state and contract (engine first, rule 11)

- `settings.stage` in the chat session: `prompt | emojis | animation | export`, default **`emojis`** (today's behaviour). Validate it in the settings
  route (`POST /api/chat/sessions/{id}/settings {stage}`), add it to `DEFAULT_SETTINGS`, to the session's `summary_structured`, to OpenAPI (`Settings`,
  chat actions) and `docs/api.md`.
- Meaning (one place, e.g. `agent/stages.py`, pure, tested):
  - **prompt** — plan only: the plan card (cells, tags, the sheet prompt) and an "Edit / Generate" follow-up; nothing is spent, no job.
  - **emojis** — the sheet and the cut stickers (today's default turn); stops at G2 for the person.
  - **animation** — emojis + the video: the creator path with `scope: video` that ENDS after the animations (G4), no pack, no Telegram.
  - **export** — the full creator run: animation, pack (Library), then send (D1).
- Map onto the creator, do not fork it: `stage` animation/export = `creator.on` with `scope: video` and an end step (`animation` stops after
  "approve the animations", `export` runs to the end); `stage` emojis = creator off (or `scope: images` stopping at G2); `stage` prompt = no
  `_start_create`. Keep `settings.creator` readable for old sessions (migrate on load: `creator.on` + `scope: video` -> `export`).
- The stage governs NEW requests; Step 0 continuation keeps working on the open batch; follow-up batches (Step 3) run to the chat's stage.
- The plan card shows the whole price of the chosen stage before the go-ahead (sheet, + animation when the stage animates), as the creator card
  does today (rule 13: nothing spends before the click; a price rise > 25% stops and asks, as now).
- Tests: `tests/test_chat_stage.py` (stage -> what the turn does, on `FakeTools`; migration of old `creator` settings; the settings route
  validates; the price on the card per stage).

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

- `docs/agent-and-chat.md`: a section "Stages and the batch follow-up" (Step 0 continuation, state, the mapping onto the creator, the card, Telegram);
  `docs/api.md` (`settings.stage`, the new actions); `docs/design.md` (the pill and popover); `README.md` only if the index changes.
- One browser look at the end (Haitham's eyes, W1-style): the pill, the popover, the follow-up card.
