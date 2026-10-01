# Phase 2 — Generation: prompt engine, vision check, live generation through Higgsfield (CLI)

> **Order changed 2026-10-01 (Haitham): this phase was Phase 3.** Live generation now comes **before** Postgres (which is Phase 3). It removes the manual Higgsfield loop and the cause of the out-of-bounds animations, and nothing in it needs a database: it runs on the file store Phase 1 already has (`out/tasks/*.json`, `out/G00N/result.json`, `out/library/`). Phase 3 imports what this phase writes.

**Prerequisite:** the Phase 1 exits (1A, 1B, 1D, 1F golden path + verifier, 1G the simple flow, 1H Send to Telegram, proven live). **No database.**

**Supporting material:** `Phase_02/prompt_samples.md` (Haitham's golden prompts: a generic 4×4 sheet and the teddy-bear meta-prompt) and `Phase_02/CLAUDE.md`. Written in this phase: `Phase_02/higgsfield.md` (what the Higgsfield CLI offers, step S0, done) and `docs/operator.md` (how the operator runs jobs).

**Phase 1 contract to build on:** `mirsal/prompter.py` already defines the plan JSON (`task`, `task_slug`, `guidelines`, `sheet_prompt`, `video_prompt`, `stickers[{index,id,prompt,key,emoji}]`). The Part 1 planner **extends** that shape (it adds `extraction`, locks, keywords) and must keep `task_slug` and each cell's `key`, because every output file is named `<media>-<NNN>-<task_slug>-<key>` and the pool (3B) indexes by `key`. Phase 1's `prompter.expand` stays as the `--no-llm` path and as the offline test double.

**Goal:** great prompts in, verified stickers out, generated live. The parts:
1. **Prompt engine.** A short request is extracted, a character + style lock is built, and the saved template is filled (never rewritten).
2. **Vision quality check.** A VLM pre-reviews every sticker; Python checks the pixels. The human still decides.
3. **Generation.** The image sheet and then the video are made live by Higgsfield, driven through its CLI (the server fulfils the jobs itself; an operator session can run the same commands), and fed into the unchanged Phase 1 engine. The video always comes from the **normalised** video sheet.
4. **Quality work.** Measured, not guessed.

**Not in this phase:** Postgres, LangSmith, vectors/pool, photo/text/depth features (all Phase 3), Redis, LangGraph, a frontend rewrite (Phases 4-5).

> The LLM writes the creative content. Code writes the constraints. Python judges what is *correct*; the VLM judges what is *good*.

---

## Ready to go (start here)

### Decisions (Haitham, 2026-10-01)
1. **Order:** generation (this phase) before Postgres (Phase 3).
2. **Live provider: Higgsfield through its CLI** (`higgsfield`, measured in `Phase_02/higgsfield.md`; Claude Code does not use Higgsfield's MCP connector). Mirsal never holds Higgsfield credentials: the CLI keeps its own OAuth login. The CLI is a scriptable subprocess that prints JSON (`generate create ... --wait --json`, job ids usable as media inputs), so the same **jobs** interface can be fulfilled by an **operator** session running those commands or by a fulfiller inside Mirsal; decide at S3. Models fixed by Haitham: **Nano Banana 2 (`nano_banana_flash`) at 2k** for sheets, **Kling v3.0 (`kling3_0`)** for animation, **never its `4k` mode**. A plain HTTP provider stays possible behind the same interface.
3. **Nothing raw goes to the video model.** The video is made from the normalised video sheet (Part 3). The prepared Higgsfield samples in `Phase_01` stay as they are.
4. Telegram needs no change here (images and video are proven).

### What exists already (do not rebuild)
Everything in `Phase_01/README.md` and `Phase_02/README.md`: the engine and verifier, the gates, the prompt lab and v2 templates, jobs and their CLI fulfiller, the model catalog, the usage log, the Generate menu with the AI enhancer, references and live Kling animation.

### Build order (each step ends with something Haitham can see; stop at each gate)
| Step | What | Done when |
|---|---|---|
| **S4** | **Normalised video: the Kling job from an approved video sheet is built** (attach + slice, `pro` = 480 px per sticker). Left: run it on real sheets and **measure** — `python -m mirsal measure-cells` (not built) reports the share of cells flagged by `inside_slot` / `cross_slot` / `inside_frame`; tune `slot_fill`, or fall back to one sticker per video / 2x2. First real run: G002 (J004, in flight when this was written). | The flagged share is measured and recorded; `slot_fill` is tuned until it is near zero or the per-sticker fallback is chosen. |
| **S5** | **LLM slot filler** (built: `expander.py`, `llm.py`, the reviewer; architecture in `Phase_02/README.md`). Left: the 20-prompt AI lab (`mirsal prompt lab --ai`) and Haitham's rating. | 20 prompts from the prompt lab pass lint; Haitham rates them. |
| **S6** | **Vision judge** (Part 2) + the bounded regeneration rules; every call appended to `out/model_calls.jsonl`. | The judge agrees with Haitham on at least 80% of 30 labelled stickers. |
| **S7** | **Quality work** (Part 4): sheet vs single, outline A/B, measurements in `docs/phase2_measurements.md`. | Exit below. |

### What Haitham provides
- Keeps the Higgsfield connector authorised in the operator session; a daily credit budget for tests (the operator stops at it).
- S5 decision made: the slot filler and reviewer use `OPENAI_API_KEY` (`llm.py`). Still open for S6: the judge on the same key, or an agent judge in the operator session.
- 30 sticker labels for S6, a rating for the first live sheets.

### Rules for whoever runs jobs
The server fulfils jobs itself (`jobs.fulfil` through the Higgsfield CLI); an operator session can run `mirsal hf run J###` or the claim/done/fail commands. Ticket first (create without waiting, claim, then wait); one paid call at a time; never retry a paid call; `generate cost` before every call; Nano Banana 2 at 2k and Kling v3.0, never Kling 4k; never open or judge media (Python and the human judge); never write inside `Phase_01/Images_gen|videos_gen`; tests never reach the real CLI (`MIRSAL_NO_REAL_CLI`).

---

## Part 1 — Prompt engine

### Template-locked prompts (Haitham, 2026-10-01: this overrides "the planner writes the prompt" below)

**The master prompt is a saved file, picked by grid, never rewritten.** The LLM only fills a **small JSON** whose fields plug into named slots. Prompt quality is iterated later by editing and versioning the templates and the slot rules, not by letting a model rewrite the whole prompt each time.

```
request ─► SLOT FILLER (LLM, tiny JSON) ─► SLOT REVIEWER (small model + code lint) ─► template[grid] + slots (code) ─► final prompt
```

**Templates** live in `mirsal/prompts/templates/`, are versioned, and are chosen by grid:
- `sheet_3x3_v1.txt` and `sheet_2x2_v1.txt` (the user's choice; 3×3 is the default);
- `single_1x1_v1.txt`, used to regenerate **one** sticker: the user picks a sticker and asks for a regen, and only that sticker is handled, as a 1×1 sheet through the same engine;
- `video_v1.txt`.

The stored prompt record is `{template_id, template_version, slots}`, never a free-text blob. "Update the prompt" therefore means swapping slot values. The final string is always rebuilt from the template, so two generations differ exactly by their slot diff.

**Template shape** (sheet; `{…}` are slots, everything else is fixed text):

```
Create a sticker sheet pack of {subject_description}.
STYLE: {style}
LAYOUT: {cols}×{rows} grid, {n} separate stickers of the same character, wide even gaps between cells, generous outer margin,
every character fully inside its own cell with empty space on every side, no character touching or crossing its cell edge, no interaction between cells.
CELLS:
{cells}                         ← one line each: "1.1: happy", "1.2: laughing", "1.3: envy", "2.1: thumbs up", …
BACKGROUND: solid flat pure chroma-key {key_colour} (#00FF00 | #0000FF), no texture, no gradient, no floor, no shadow on the background.
RULES: same character, proportions, materials and lighting in every cell; full body, centred; no text, no logos, no borders, no dividers.
```

**Slot JSON** (the only thing the LLM writes; strict schema):

```json
{ "subject_description": "a cute yellow teddy bear with a round head, small rounded ears and a button nose",
  "style_id": "ios3d_backlit", "style_extra": "",
  "mode": "subject | subject_action",
  "cells": [ {"pos": "1.1", "label": "happy", "tags": ["teddy_bear_happy", "happy", "smile"], "emoji": ["😄"]} ],
  "action_guidance": null,
  "key_colour": "green" }
```

**Two request shapes:**
- **Specific subject** ("teddy bear"), `mode: subject`: each cell gets a **high-level label only** (`1.1: happy, 1.2: laughing, 1.3: envy, 1.4: thumbs up …`). The image model fills in the pose.
- **Subject doing something** ("teddy bear playing football"), `mode: subject_action`: the labels become short action lines ("1.1: kicking the ball, ball fully inside the cell"). `action_guidance` adds one shared sentence that guides the image model a little more (props, framing). Labels stay short; this is guidance, not a rewritten prompt.

**Slot reviewer:**
- **Code lint first:**
  - schema;
  - exactly `rows×cols` cells, with positions `r.c` in order;
  - unique labels;
  - 1–5 tags with `tags[0]` the key, and ≥1 emoji;
  - the green-word rule → `key_colour`;
  - banned words.
- **Then a small model** (`claude-haiku-4-5-20251001`, configurable) answers `{ok, problems[]}`: are the labels distinct and animatable? Does `subject_description` match the request without adding to it? Does `style_id` fit the words the user gave?
- One repair round is allowed, then the result fails cleanly.
- The reviewer never edits the template and never writes prose into it.

**Style presets** (`mirsal/prompts/styles.yaml`; the `{style}` slot is the preset text, plus `style_extra` when the user adds words; enhanced 2026-10-01):

| id | text dropped into `{style}` |
|---|---|
| `ios3d_backlit` (default) | premium iOS-style 3D emoji pack, soft rim backlight and gentle glow around the silhouette, cute oversized features, rounded edges everywhere, glossy vinyl material with subtle subsurface warmth, smooth gradients, soft studio key light, clean readable shapes at small size |
| `genmoji` | Apple-Genmoji-like glossy 3D, chubby rounded proportions, big expressive eyes, polished plastic-candy finish, soft ambient occlusion, bright friendly colours |
| `toon_cel` | flat toon cel shading, bold clean vector outlines, two-tone shadows, saturated flat colours, crisp graphic shapes, no texture noise |
| `pixar_cinematic` | cinematic 3D character render, creamy key light, warm rim glow, soft depth, appealing squash-and-stretch proportions, film-quality materials |
| `chibi_kawaii` | kawaii chibi, big head small body, marshmallow-soft shapes, pastel candy gloss, sparkle highlights in the eyes, blush cheeks |
| `clay_3d` | smooth matte clay / plasticine 3D, rounded chunky forms, soft warm shadows, slightly imperfect handmade toy feel |
| `sticker_flat` | classic flat vector sticker, thick uniform outline, solid fills, minimal shading, high contrast, instantly readable |
| `yellow_face` | premium glossy round yellow emoji face, identical face construction in every cell, polished 3D finish, soft studio lighting |

- Style names never appear in published metadata (the trademark rule in Lint).
- New styles are rows in this file, A/B tested in the prompt lab. Code never changes for a new style.

**What the rest of Part 1 becomes:**
- The planner below is the **slot filler**. `character_lock` → `subject_description`, `style_lock` → `style_id` + `style_extra`, and `cells[].action` → `cells[].label`.
- The "Assemble" templates below are the first versions of the template files.
- The Lint section is the slot reviewer's code half.
- `extraction`, the content rules and the few-shot examples stay as they are.

**Phase 1 adopts the shape now** (checkpoint 1F): `prompter.expand` fills the same slot JSON deterministically and renders the same template files, so Phase 2 swaps only the filler. **Built 2026-10-01:** `mirsal/prompts/templates/{sheet_3x3,sheet_2x2,single_1x1,video}_v1.txt`, `prompter.render_plan(slots, template_id, version)` (the one function that turns slots into prompts) and `validate_plan`, which rebuilds the sheet and video prompts from `{template_id, template_version, slots}`. Per-cell `tags` (1-5, `tags[0]` = key) and the margin clause are in place; the Phase 2 lint checks the assembled text for the clause. The Inbox (`tasks.py`) already stores `request = {template_id, template_version, slots, grid}` on `out/tasks/NNN.json`.

### Original design (kept until the gate; superseded where the template note above differs)

```
request ─► PLANNER (one LLM call, strict JSON) ─► lint (code) ─► ASSEMBLE (code) ─► sheet prompt  (mode: sheet, default)
                                                                              └─► 9 single prompts (mode: single)
```

### Planner output (the structured plan)

```json
{
  "task": "yellow teddy bear in toon cel shade + iOS 3D genmoji", "task_slug": "teddy_bear_toon",
  "extraction": { "subject": "yellow teddy bear", "attributes": [], "style_words": "toon cel shade + iOS 3D genmoji",
                  "occasion": null, "tone": "playful", "constraints": [] },
  "character_lock": "a cute yellow teddy bear: round head, small rounded ears, button nose, big glossy dark eyes, soft plush fur texture, chubby short limbs",
  "style_lock": "premium iOS-3D Genmoji-style sticker with toon cel shading: rounded forms, bold clean outlines, two-tone cel shading, glossy subtle highlights, soft cinematic key light, appealing proportions, readable at small size",
  "cells": [
    { "index": 1, "name": "Big Hug", "key": "teddy_bear_big_hug", "tags": ["teddy_bear_big_hug", "hug", "love"],
      "concept": "HUG", "emoji": ["🤗"],
      "action": "arms wide open going in for a huge hug, eyes squeezed shut with joy",
      "motion": "arms open and close in a squeeze", "key_color_risk": false,
      "keywords": { "en": ["hug", "love", "teddy"], "ar": ["حضن", "حب"] } }
  ],
  "key_color": "green"
}
```

**Planner system prompt (`mirsal/prompts/planner_v1.md`)** is built from Haitham's teddy-bear meta-prompt (`Phase_02/prompt_samples.md`), with these changes:
- **Output** is the JSON above, not markdown. Pixel and background wording is removed from the planner's job.
- **Character lock:** one identical character across all cells: proportions, head, face, eyes, colours, materials, accessories, lighting, camera.
- **Style lock:** translate *whatever* style words the user gives into concrete visual properties (rendering, materials, finish, lighting, proportions, colour, shape language, polish). **Blends are allowed**, e.g. "toon cel shade + iOS 3D genmoji". With no style words, the planner copies the default preset text verbatim.
- **Variety:** nine completely different actions or reactions, mixing comedy, extreme reactions, emotions, physical actions, celebrations, failures, surprises, cute moments, dramatic poses, absurd situations and useful chat reactions. No two cells share a pose; a slightly changed mouth is not a new pose.
- **Sticker composition:** one character, full body, centered, clear silhouette, readable at emoji size, props only when they strengthen the concept. Prefer actions that animate clearly (bounce, wave, dance, jump, spin, laugh).
- **Clean output:** no text, captions, speech bubbles, logos, watermarks, borders, frames, extra characters or scenery.
- **Boundary:** creative inside the request and never changes it. `constraints` ("no dancing") are obeyed.
- **UAE content rules** are ported from `proposals/Mirsal-chat-emojis/api/planner.py` into `mirsal/prompts/content_rules.md`:
  - no flags, emblems or text;
  - no real people, rulers, royals or religious figures;
  - the falcon is always "a young brown saker falcon chick…";
  - Emirati dress: kandura + ghutra + black agal, or abaya + shayla; never a red-and-white shemagh; no shoe soles;
  - Commemoration Day is solemn: no confetti, candles or doves.
- Input can be English, Arabic, Gulf dialect, Arabizi or mixed. The output is always English.
- **Few-shot:** the 2–3 golden examples closest to the input, taken from `mirsal/prompts/examples/`, which is seeded from `Phase_02/prompt_samples.md`.

**Model:** `claude-sonnet-5`, configurable. It uses a strict JSON schema, gets one repair attempt, and then fails cleanly.

**`--no-llm`:** a fixed 9-concept list (Happy 😄, Laughing 😂, In love 😍, Surprised 😮, Sad 😢, Angry 😠, Sleeping 😴, Thumbs up 👍, Dancing 💃) plus the default preset, so the pipeline runs offline and in CI. This is Phase 1's `prompter.expand`, which already has context action sets (school, birthday, default); extend those sets rather than writing a second offline planner.

### Style presets (`mirsal/prompts/styles.yaml`)

These are anchors, used verbatim when the user names no style and as reference text when the planner translates style words. Seeds:
- `genmoji` (the default): glossy Apple-Genmoji-style 3D, cute rounded proportions;
- `ios3d`: iOS-Pixar glossy, vinyl sheen, subsurface warmth;
- `toon`: flat toon cel-shaded, bold vector lines, two-tone shading;
- `pixar`: cinematic 3D, creamy key light, warm rim glow;
- `chibi`: kawaii chibi, marshmallow shapes, candy gloss;
- `yellow_face`: the premium glossy yellow face character from the generic sample.

A `--style <id>` flag forces a preset.

### Lint (code; blocks a bad plan before any money is spent)

- It has exactly `rows×cols` cells, unique `concept` and `name` values, and every cell has an action, a name and ≥1 emoji. Emoji are Telegram's required tags, max 20, and the **first one** drives Telegram's suggestions.
- **Keywords:** each cell has English **and Arabic** search keywords. The Telegram limit is 0–20 keywords with ≤64 characters total, so trim to fit, English first.
- `character_lock` and `style_lock` are non-empty.
- `task_slug` and every `key` match `[a-z0-9_]+`, keys are unique, start with the subject slug and stay under 60 characters (they become file names on Windows too: no reserved names, path length checked).
- **Tags (the 1F contract):** every cell has 1–5 `tags`, each `[a-z0-9_]+`, and `tags[0] == key`. Tags describe the *sliced output* (what the single sticker shows), not the sheet. They are English slugs and are separate from `keywords` (en + ar, Telegram search).
- **Margin:** every single-mode prompt and the sheet prompt contain the margin clause. The lint checks the assembled text, so a template edit cannot silently drop it.
- Banned words are absent: text, caption, logo, watermark, flag, "transparent background", "contact shadow", "drop shadow", and names from a real-person list.
- **No trademarks in public metadata:** names and keywords may not contain Genmoji, Apple, Pixar, Disney or similar. They may appear inside generation prompts as style words, never in anything published to Telegram.
- `key_color` follows the chroma rule: **blue** if the subject, a lock or any action matches the green-word list (green, leaf, plant, grass, palm, mint, lime, olive, emerald, cactus, tree, frog, watermelon, avocado…), or if any `key_color_risk` is set. Otherwise **green**.
- The assembled prompt is under the model's length limit.

### Assemble (code, deterministic templates, versioned)

**Sheet mode** (the default; one image, from Haitham's generic-sheet structure):

```
Create a clean, high-quality sticker sheet of {N} different stickers of the same character, arranged in a perfectly aligned {cols}×{rows} grid.
ASPECT RATIO: 1:1 square.
CHARACTER (identical in every cell): {character_lock}
STYLE: {style_lock}. All {N} stickers share the EXACT same character, visual style, proportions, lighting, material and size.
GRID LAYOUT: {cols} columns × {rows} rows, evenly spaced, wide gaps between cells, generous outer margins, no overlapping; every character fully inside its own cell; no interaction between cells.
BACKGROUND: solid pure {chroma-key green (#00FF00) | chroma-key blue (#0000FF)}, flat, no texture, no gradient, no floor, no shadow cast onto the background, no extra elements.
{N} UNIQUE STICKERS:
1. {name} — {action}
…
COMPOSITION: one character per cell, full body, centered, immediately recognizable and visually distinct, readable at small emoji size.
No duplicate poses, no distorted faces, no missing or extra stickers, no text, no watermark, no border, no dividers.
```

**Single mode** (9 images, from Haitham's teddy-bear per-cell structure; also used to regenerate one rejected cell):

```
{character_lock}. {action}. {style_lock}. One character, full body, centered, clear silhouette, generous empty margin on every side (at least 20% of the frame), nothing touching or crossing the frame edge.
Flat solid pure {key colour} chroma-key background, no floor, no shadow on the background, no text, no border.
```

**Video prompt:** `{per-cell motion}. Static camera, each character stays centered in its own cell, the background stays flat solid {key colour} with no shadows, glow or colour change, smooth looping motion that ends exactly where it starts, no text.`
- When the provider supports a last frame (as the old POC's `ltx2.5-loop` did), pass **last frame = first frame** for a true seamless loop.
- Phase 1's `loop_seam` crossfade stays as the safety net.

**Outline:** the prompt does **not** ask for a die-cut outline by default; Python draws it (Phase 1). The A/B in Part 4 decides whether to switch to a model-drawn outline with `outline_px: 0`. Never both.

**Grid:** 3×3 is the default. 4×4 is supported (the generic-emoji layout). Aspect ratio is 1:1 by default; 16:9 is allowed.

---

---

## Part 2 — Vision quality check

**Python first** (deterministic; its facts are final):
- **These live in Phase 1's verifier now** (`engine/verify.py`, 1F catalogue): `background_flat`, `chroma_risk` (interior key colour, WARN at 3%), `holes`, `layout_match`, `inside_slot` / `cross_slot` and the rest. Phase 2 adds no second checker. It *acts* on their verdicts: `chroma_risk` / `holes` above threshold → blue re-key; `cut_clean` / `grid_detected` failures → sheet regeneration. The original text follows.
- The Phase 1 validators, plus two new checks:
  - `background_flat`: the key-colour variance across the gutters is low, i.e. the model really drew a flat key background.
  - `chroma_risk`: the share of subject pixels whose hue is near the key colour but below the key threshold. These are subject colours the key could eat. Above ~3%, flag the sticker `CHROMA_RISK`.
- **Grid detection: built in Phase 1 (1F) as `split_grid()`**, needed for 2×2 and for real sheets whose gutters are off-thirds. Phase 2 extends it to 16:9 and 4×4 if those return. Original note: `split_grid()` projects the background mask onto the x and y axes and cuts at the widest background bands near each expected line. Generated sheets have outer padding and uneven gaps (the generic sample is 16:9 with padding), so equal thirds would cut characters. Fixed equal division stays as the fallback, and for prepared sheets.

**VLM second:**
- `VisionJudge.judge_sticker(png, cell, pack_ctx) -> Judgement`, where `pack_ctx` holds `character_lock`, `style_lock` and a reference sticker (the first approved one) for consistency.
- **Output:**

  ```json
  { "decision": "APPROVE|REJECT", "confidence": 0.0,
    "concept_match": true, "emoji_fit": true, "character_match": true, "style_match": true,
    "reasons": [] }
  ```
- **Reasons** come from a fixed list: DUPLICATE, WEAK_CONCEPT, AMBIGUOUS_ACTION, STYLE_DRIFT, IDENTITY_DRIFT, SEVERE_ARTIFACT, POOR_COMPOSITION, ANIMATION_RISK, CHROMA_RISK, MISSING_REQUIRED_ELEMENT, ANATOMY_ERROR, OBJECT_DEFORMATION, EMOJI_MISMATCH, UNWANTED_TEXT.
- `emoji_fit` asks whether the assigned emoji describes the visible expression or action. If not, the VLM may suggest a better emoji. The suggestion is stored, and applied only if Haitham's config allows automatic emoji correction.
- **Sheet check:** one call per sheet asks whether the count is right, whether the cells are isolated (no cross-cell interaction or touching), and whether any cell is missing or duplicated.

**The division of labour is strict.** The VLM never overrides Python on dimensions, alpha or bounds, and Python never judges funny, cute or expressive.

**Implementation:** use one OpenAI-compatible vision client (`VISION_BASE_URL`, `VISION_MODEL`, `VISION_TIMEOUT`, `VISION_MAX_TOKENS`, `VISION_CONCURRENCY`).
- It targets **vLLM** serving a Qwen-VL model. The same client works against LM Studio or a hosted endpoint. A Claude-vision implementation sits behind the same `VisionJudge` interface.
- **Hardware note:** vLLM needs an NVIDIA GPU; on a machine without one use LM Studio or Claude until a GPU box is available.
- **Never trust `response_format` from a local model.** LM Studio was measured not enforcing JSON schemas on qwen3-4b in this workspace. Always parse, validate against the Pydantic schema, attempt one repair, and log the raw output when that fails.
- **Policy if the VLM is down:** `FAIL_CLOSED` (the default: stickers stay `READY`, flagged "unjudged") or `DETERMINISTIC_ONLY`.

**Where the VLM sits in the golden path (`Phase_01/README.md`, 1F):**
- The VLM is a **pre-reviewer**, not the gate. Its verdict is a history line with `actor = 'vlm'` (a `reviews` row once Phase 3 imports it) at the same gate (`still` before G2, `anim` before G4).
- The console shows it next to the tile ("VLM: REJECT · STYLE_DRIFT"), and the human still decides.
- With `auto_approve_vlm = true` (off by default), a VLM APPROVE also sets `still_review`/`anim_review` and the human gate is skipped; it is recorded as such.
- From Phase 3 every VLM verdict is also LangSmith feedback (key `vlm_still` / `vlm_anim`), so the judge calibration can compare VLM and human feedback on the same runs.

**Decisions and recovery (all bounded):**
- **Statuses:** `READY` (Python ok) → `JUDGING` → `APPROVED | REJECTED` (VLM), then the human G2. The automatic regenerations below act on VLM rejections only. A human REJECT at G2 regenerates only when the human asks ("Regenerate" on the tile), never on its own.
- **More than 2 of 9 rejected, or the sheet check fails:** regenerate the whole sheet with a new seed, at most 3 sheet attempts. Keep the best as `PARTIAL`, or `FAILED` if 0 stickers are approved.
- **1–2 rejected:** regenerate only those cells in **single mode**, passing the first approved sticker as a reference image when the provider supports it (for character consistency). At most 2 attempts per cell. Approved stickers are never touched.
- **`CHROMA_RISK` on any cell:** regenerate the sheet once with the **other** key colour, and record `chroma_reason: "vision/pixel chroma risk"`.

---

## Part 3 — Generation (live, through Higgsfield)

### Sizes and margins are normalised before anything goes to the video model (Haitham, 2026-10-01)

The prepared Higgsfield sheets and videos in `Phase_01` are pre-rendered and **not** normalised, and it shows: the border check finds characters leaving their cell in 3 of 9 teddy animations and 8 of 9 generic-emoji animations (G069), and 60 of the 88 generic-emoji animations made so far touch their cell edge. So the video job never takes the raw generated sheet. Its `input_image` is the output of `build_video_sheet()` (built in Phase 1): ONE scale for the whole sheet (the stickers keep their relative sizes), each subject centred and at most `slot_fill` of its slot (55% today), margin on every side, flat chroma, no outline, plus `layout.json`.
- **`slot_fill` is the dial, tuned by measurement per provider.** `python -m mirsal measure-cells` reports, for a set of generations: the share of cells flagged by `inside_slot` / `inside_frame`, the cross-cell interaction rate (`cross_slot` blocks / slots) and `subject_px_in_video`. Target: nothing flagged. If tuning fails, the fallback is per-sticker animation (a 1×1 sheet and one call per sticker), chosen per provider.
- The image prompt keeps its margin clause so the stills pass `inside_cell` first.
- Slicing uses the layout's rectangles and the same Phase 1 gates.

### Engine changes allowed in this phase
The two new Python checks of Part 2 if still missing, `split_grid()` extensions (16:9, 4×4), and the `slot_fill` setting. Existing engine functions stay unchanged, including `build_video_sheet()` and layout slicing.

---

## Part 4 — Quality work (the heart of the phase)

1. **Prompt lab:** run `prompt` on 20 inputs, including Haitham's own ("yellow teddy bear in Pixar 3D iOS style", "yellow teddy bear in toon cel shade with ios 3d genmoji style", the generic 4×4 yellow faces), Arabic and Arabizi requests, a UAE occasion, a green subject, and a constraint. Haitham reviews them against `prompt_samples.md`, and the planner prompt is iterated (`planner_v2`, …), with every version kept.
2. **Sheet vs single:** the same 5 requests in both modes. Compare character consistency (the VLM `character_match` rate plus Haitham's eye), pass rate and cost, and pick the default.
3. **Outline A/B:** Python outline vs model die-cut outline, on 5 requests.
4. **Judge calibration:** Haitham labels 30 stickers approve/reject. The VLM must agree on ≥80%, or `judge_v1` is tuned. Record agreement per reason.
5. Everything is recorded in `docs/phase2_measurements.md`: pass rate, rating, cost, latency, judge agreement and decisions.

## Tests (offline, no network)
- **Fake planner:** the lint catches injected faults (8 cells, a duplicate concept, "transparent background", "contact shadow", a green subject on a green key, an empty style lock).
- **Style handling:** a `--style` flag wins; no style words → the default preset verbatim; a blend passes through to `style_lock`.
- **Golden assembly:** 5 fixed plans → exact sheet and single prompt strings, in 3×3 and 4×4.
- **`split_grid()`:** golden tests on synthetic sheets with outer padding, uneven gutters, and 16:9 4×4.
- **Fake VLM:** 1 rejection → single-cell regeneration only; 3 rejections → sheet regeneration; `CHROMA_RISK` → a blue-key rerun; VLM down → both policies; invalid JSON → repair, then fail with the raw output logged.
- **Fake image/video generators** reuse the synthetic sheets and MP4; retry limits and timeouts hold.

## Exit (Phase 2)
- [ ] `prompt` produces locks + 9 concepts + sheet and single prompts for English, Arabic and Arabizi, and Haitham approves them against `prompt_samples.md`.
- [ ] Measured: ≥80% of live `create` runs end with ≥7/9 **approved**; Haitham's average rating is ≥4/5.
- [ ] The judge agrees with Haitham on ≥80% of 30 stickers.
- [ ] The sheet-vs-single and outline decisions are made and recorded.
- [ ] A real video made from the **normalised** video sheet is sliced; the flagged share (`measure-cells`) is recorded and `slot_fill` is chosen.
- [ ] Haitham ran at least one full request live: type -> job -> Higgsfield sheet -> stills -> video job -> animations -> pack -> Telegram.
- [ ] Every LLM, image, video and VLM call is a line in `out/model_calls.jsonl` with latency and cost.


## Hands to Phase 3
- `out/jobs/*.json` and `out/tasks/*.json` with `external_task_id` / `provider = 'higgsfield-cli'`: imported as `tasks` rows.
- `out/model_calls.jsonl` (one line per LLM / image / video / VLM call with latency and cost): imported as `model_calls`.
- `plan` with `{template_id, template_version, slots}` and the planner / judge versions on every generation; the VLM verdicts in `result.json` as `actor = 'vlm'` history lines, imported as `reviews` rows.
- The normalised video sheet and its `layout.json`, and the measurements in `docs/phase2_measurements.md`.
- A `ModelSource` behind the unchanged source interface.
