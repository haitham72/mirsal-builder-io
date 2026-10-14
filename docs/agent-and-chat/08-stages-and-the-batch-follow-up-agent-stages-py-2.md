# Stages and the batch follow-up (`agent/stages.py`, 2026-10-09)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

**The slider is one per person and a boundary both ways (Haitham, 2026-10-11).** Six stops: **Auto** (the default) · Prompt · Stickers · Animation · Telegram · Export. The person's stop lives in `out/sessions/_prefs.json` (`SessionStore.person_stage`), every chat of theirs follows it on load, and the Studio reads and writes it through `GET/POST /api/prefs`. **Auto**: the message decides (`stages.resolve` / `need_of`: "animate" needs Animation, "Telegram" Telegram, "to the API" Export, "just the prompt" Prompt; nothing named = Stickers). **A fixed stop**: a message that needs a step past it ("animate it with grok lite" at Stickers), or that says "only" an earlier step ("new stickers only" at Animation), gets a question in words with buttons that set the slider and go (`_stage_ask`, chip action `stage_go {stage, text, force?}`: "Set to Animation and go", "Set to Auto and go", "Not now" / "Keep Animation and go"); explicit Animate and Send-to-Telegram requests check it too (`stages.at_least`). A plain request at a fixed stop just runs to it. Moving the slider to a step the open batch already passed posts one line, no turn ("Stickers is already done for G128; new requests now stop at Stickers."). "Make X and animate them" with nothing made yet is a new request that runs to the animation.

**The chat loads the person's preference before drawing the new-chat pill.** Picking a stage before the first message writes `/api/prefs` without creating an empty chat. With a session open it uses that session's settings route, which also updates the person's preference. Popup outside-click detection uses the original event path because drawing the slider replaces the clicked button; delayed composer focus does not close an open popup. Node tests and a headless Chromium check cover opening, dismissal, keyboard selection, persistence and desktop/mobile bounds.

How far a NEW request goes is the chat's **stage**, `settings.stage`, one of five (Haitham, 2026-10-09; the fifth, `api`, 2026-10-11). The slider names them Prompt · Stickers · Animation · Telegram · Export; the ids stay as below so saved chats keep their meaning. `agent/stages.py` is the one pure table (`of`, `run_spec`, `batch_label`):

| stage | a new request | spends |
|---|---|---|
| `prompt` | the plan card only (cells, tags, the sheet prompt) and **Generate** / **Edit**; a pending `create` with `stage: prompt` that never starts by itself, even with "Ask before spending" off | nothing until Generate (which makes the sheet) |
| `emojis` (default, web and Telegram) | today's turn: the plan, the go-ahead, the sheet, the cut stickers; stops at G2 for the person | the sheet |
| `animation` | the agentic creator with `scope: video` and `end: animation`: the run ends after "Approve the animations" (G4), no pack, no Telegram; its done message says "export" packs and sends | sheet + animation, both on the plan card |
| `export` ("Telegram") | the full creator run with `end: export`: animation, then the Library pack and the Telegram send (D1) | sheet + animation |
| `api` ("Export") | the creator run with `end: api`: everything `export` does, then the pack's Download .zip is sent to the AddCollection API as one collection (`tools.collection_export`, the pack's own "Export to collection" call; owner only). A refusal or a missing setup is a stop with **Try again** / **Stop**: the pack is already in the library and in Telegram | sheet + animation |

- **It maps onto the creator, never forks it.** `n_new` reads `stages.run_spec(stages.of(settings), bypass)`: `plan_only` -> `_prompt_plan`; `creator` -> `_creator_plan(end=…)`,
  which shows the whole price (`card.creator = {sheet, video, end}`) and `Create and animate` / `Create and send to Telegram`. `creator.new_run(end)` stores `end` on the run;
  `creator.steps_of(run)` drops the pack and Telegram steps for `end: animation`, and the `pack` step ends such a run as `done` without packing.
- **D2:** Animation and Export stop at G2 and G4 for one click unless the creator's bypass ("Approve everything for me", `settings.creator.bypass`) is on, as the creator always did.
- **Old sessions:** `stages.of` reads a missing stage from the old switches (`creator.on` + `scope: video` -> `export`, anything else -> `emojis`); the settings route does the same when an old
  client posts `creator` without `stage`. `summary_structured` carries `stage`.
- The stage governs creation; explicit animation and export requests also check its boundary. Viewing or describing existing stickers does not change the stage.
- **Tests:** `tests/test_chat_stage.py` (each stage on `FakeTools`: the plan card, the price, Prompt never starts, an Animation run ends with no pack and no Telegram, Export reaches Telegram,
  waiting at G2 without bypass, the migration, `batch_label`) and `tests/test_agent_server.py` (the route: validated, 400 on an unknown stage, no turn, the old switches).

### Batch 01 first, then ONE follow-up card

A new request plans **batch 01 only** (Haitham, 2026-10-09): for an emoji pack the first preset grid (core-v1, actions 1-9), else the first 9 bank actions. When its plan
has `batches_max > 1` (`tasks.preview`, capped at `stages.MAX_BATCHES` = 4) the plan card says "Batch 01 of 04 · core" (`card.batch`); a transformation (one character changed) or a 1x1 has one batch.

- **The pack** (`sess["pack"]`): `{request, subject, grid, style_id, ai, plan (batch 01's, compact), max, transformation, made: [{no, label, generation, job, plan, creator, ts}], said}`.
  It opens when batch 01 starts (`_track_batch` from `_start_create` / `_start_items`; the Prompt stage opens it with the plan, nothing made); a later batch or a regenerated one takes its
  number's row (the newest take is the batch). How many exist is `max(rows, tools.batch_state(gens))`: `tasks.session_state`, the Studio picker's own count (an emoji pack counts its grids
  wherever they were made).
- **The follow-up card** (`_followup`): one message with the chips **Regenerate · N credits** and **Batch 02 · 03 · 04** (only the ones still possible; the price is the stage's per batch, so
  "Batch 03" with one made states two batches). It comes when the batch reaches the stage's end: for Emojis when every batch just started is cut (`Agent.batch_followup`, called on every
  poll of the chat, web `GET /api/chat/sessions/{id}` and Telegram `render`; once per set of batches, `pack.said`); for Animation / Export in the creator's done message (`_creator_say`);
  for Prompt right after the plan (its Batch chips plan 01..k together). A transformation shows Regenerate only; with all four made, Regenerate only.
- **`{type: "batch_more", to: k}`** (`n_batches`): the batches after the ones made up to `k`, planned by `tools.more_batches` (an emoji pack's next preset grids, else the next unused bank
  actions; the chat's batches and, through their generations, the Studio's batches of the same pack are skipped; never a repeat, never past batch 04), on ONE `multi` card with ONE total and
  ONE go-ahead (pending `batch_more`). Nothing made yet (the Prompt stage): batch 01 goes with them. Each new batch runs to the chat's stage (`_run_batch_items`): Emojis as sheets side by
  side (`_start_items`); Animation / Export through the creator, one run after the other (`sess["creator_queue"]`, started by `creator_tick` when a run is done, priced and approved
  with the first; Stop clears it). Each export run creates its own library pack; later batches use `Batch NN <subject>` as the pack title, so their Telegram names stay distinct even when a long subject is truncated. At the Prompt stage the card is a plan and Generate is the go-ahead.
- **`{type: "regenerate", generation}`** (`n_regenerate`): a new generation of that batch from its own saved plan, the Studio's Regenerate (`parent` + `regen_of`, so it joins the batch's
  family in Earlier batches), priced on the button, one go-ahead, to the chat's stage; the old one stays.
- **Typed words work too** (`resolver.batch_intent`, in `classify` and, at the Prompt stage with no batch made, in `n_understand`): "next batch", "batch 3", "make the rest of the pack",
  "regenerate it" ("regenerate 2" stays an edit of sticker 2).
- The chat's batches share the pack in Earlier batches on their own (`pipeline._packs`: same request, same person, within 6 h); the chat's generation cards say "Batch 02 · social" (`card.batch`).
- **Telegram:** the follow-up card is a chip row, so it arrives as inline buttons (`_chip_rows` carries `to`); a plan's "Batch 01 of 04" is a line of its text.
- **Tests:** `tests/test_chat_batches.py` (batch 01 first, an emoji pack's grid names, the follow-up once when cut, Batch 03 = two sheets after one go-ahead, never a fifth batch,
  Regenerate's parent and regen_of, a transformation gets Regenerate only, the typed forms, the Prompt stage, the Animation stage's queue and Stop), `tests/test_tg_chat.py` (the buttons). `tests/test_creator_live.py` also proves the real console path with a fake CLI/Bot API: polling posts exactly one cut-batch follow-up, one confirmation starts two more sheets, and the blocking creator driver completes two batches sequentially at Animation and Telegram export. Both checks agree with `tasks.session_state`; Animation makes no pack/send, Telegram export delivers two distinct nine-sticker sets.
