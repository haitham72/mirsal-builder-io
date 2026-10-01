# Phase 3 — Prompt Engine, Vision Quality Check, Generation APIs

**Prerequisite:** Phase 2 exit is met.

**Supporting material:** `Phase_03/prompt_samples.md` holds Haitham's golden prompts (a generic 4×4 sheet and the teddy-bear meta-prompt). `Phase_03/CLAUDE.md` routes the folder.

**Phase 1 contract to build on:** `mirsal/prompter.py` already defines the plan JSON (`task`, `task_slug`, `guidelines`, `sheet_prompt`, `video_prompt`, `stickers[{index,id,prompt,key,emoji}]`). The Part 1 planner **extends** that shape (it adds `extraction`, locks, keywords) and must keep `task_slug` and each cell's `key`, because every output file is named `<media>-<NNN>-<task_slug>-<key>` and Phase 3B indexes by `key`. Phase 1's `prompter.expand` stays as the `--no-llm` path and as the offline test double.

**Five checkpoints**, each reviewed before the next:
- **3A** = Parts 1–4 (prompts, vision check, APIs, quality);
- **3B** = Part 5 (the semantic sticker pool);
- **3C** = Part 6 (photo cutout stickers);
- **3D** = Part 7 (text template stickers, CapCut-style);
- **3E** = Part 8 (3D parallax photos: depth + gyroscope).

**Goal:** great prompts in, verified stickers out, and reuse of what already exists. The parts:
1. **Prompt engine.** A short request ("yellow teddy bear in toon cel shade with iOS 3D genmoji style") is extracted, then a character + style lock is built. From that come 9 distinct concepts, assembled into a sheet prompt, or into 9 single prompts.
2. **Vision quality check.** A vision model (VLM) checks every sticker: does it match its prompt and its emoji, is it the same character, is the style consistent? Python checks the pixels, including whether the green key should have been blue.
3. **Generation APIs.** A real image model (and a video model for `animate`) feed the unchanged Phase 1 engine.

**Not in this phase:** LangGraph, chat or follow-up references, memory, **Redis/caching**, a web server, or a frontend.

> The LLM writes the creative content. Code writes the constraints. Python judges what is *correct*; the VLM judges what is *good*.

---

## What Haitham sees at the end

```
python -m mirsal prompt "yellow teddy bear in Pixar 3D iOS style"          # FREE: extraction → locks → 9 concepts → final prompt(s)
python -m mirsal prompt "..." --mode single                                 # 9 standalone prompts instead of one sheet prompt
python -m mirsal create "yellow teddy bear in toon cel shade with ios 3d genmoji style"
python -m mirsal create "..." --grid 4x4                                    # the generic-emoji layout
python -m mirsal create "..." --offline                                     # prepared set (Phase 1)
python -m mirsal judge G012                                                 # re-run the vision check on an existing generation
python -m mirsal animate | styles | doctor
```

- `prompt` is the free **prompt lab**. Only `create` and `animate` spend money, and they print the estimated cost first.
- Each `create` writes `out/G00N/prompt_report.html`. It shows the request → locks → concepts → final prompt → each sticker with its Python checks, its VLM verdict and its emoji, so Haitham reviews everything in one place.

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

**Phase 1 adopts the shape now** (checkpoint 1F): `prompter.expand` fills the same slot JSON deterministically and renders the same template files, so Phase 3 swaps only the filler. **Built 2026-10-01:** `mirsal/prompts/templates/{sheet_3x3,sheet_2x2,single_1x1,video}_v1.txt`, `prompter.render_plan(slots, template_id, version)` (the one function that turns slots into prompts) and `validate_plan`, which rebuilds the sheet and video prompts from `{template_id, template_version, slots}`. Per-cell `tags` (1-5, `tags[0]` = key) and the margin clause are in place; the Phase 3 lint checks the assembled text for the clause. The Inbox (`tasks.py`) already stores `request = {template_id, template_version, slots, grid}` on `out/tasks/NNN.json`.

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

**Planner system prompt (`mirsal/prompts/planner_v1.md`)** is built from Haitham's teddy-bear meta-prompt (`Phase_03/prompt_samples.md`), with these changes:
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
- **Few-shot:** the 2–3 golden examples closest to the input, taken from `mirsal/prompts/examples/`, which is seeded from `Phase_03/prompt_samples.md`.

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

## Part 2 — Vision quality check

**Python first** (deterministic; its facts are final):
- **These live in Phase 1's verifier now** (`engine/verify.py`, 1F catalogue): `background_flat`, `chroma_risk` (interior key colour, WARN at 3%), `holes`, `layout_match`, `inside_slot` / `cross_slot` and the rest. Phase 3 adds no second checker. It *acts* on their verdicts: `chroma_risk` / `holes` above threshold → blue re-key; `cut_clean` / `grid_detected` failures → sheet regeneration. The original text follows.
- The Phase 1 validators, plus two new checks:
  - `background_flat`: the key-colour variance across the gutters is low, i.e. the model really drew a flat key background.
  - `chroma_risk`: the share of subject pixels whose hue is near the key colour but below the key threshold. These are subject colours the key could eat. Above ~3%, flag the sticker `CHROMA_RISK`.
- **Grid detection: built in Phase 1 (1F) as `split_grid()`**, needed for 2×2 and for real sheets whose gutters are off-thirds. Phase 3 extends it to 16:9 and 4×4 if those return. Original note: `split_grid()` projects the background mask onto the x and y axes and cuts at the widest background bands near each expected line. Generated sheets have outer padding and uneven gaps (the generic sample is 16:9 with padding), so equal thirds would cut characters. Fixed equal division stays as the fallback, and for prepared sheets.

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
- **Hardware note:** vLLM needs an NVIDIA GPU, so on this Mac use LM Studio or Claude until a GPU box is available.
- **Never trust `response_format` from a local model.** LM Studio was measured not enforcing JSON schemas on qwen3-4b in this workspace. Always parse, validate against the Pydantic schema, attempt one repair, and log the raw output when that fails.
- **Policy if the VLM is down:** `FAIL_CLOSED` (the default: stickers stay `READY`, flagged "unjudged") or `DETERMINISTIC_ONLY`.

**Where the VLM sits in the golden path (`phase_01.md`, 1F):**
- The VLM is a **pre-reviewer**, not the gate. Its verdict is a `reviews` row with `actor = 'vlm'` at the same gate (`still` before G2, `anim` before G4).
- The console shows it next to the tile ("VLM: REJECT · STYLE_DRIFT"), and the human still decides.
- With `auto_approve_vlm = true` (off by default), a VLM APPROVE also sets `still_review`/`anim_review` and the human gate is skipped; it is recorded as such.
- Every VLM verdict is also LangSmith feedback (key `vlm_still` / `vlm_anim`) through the Part 3b trace seam. So Haitham's judge calibration (Part 4) can compare VLM and human feedback on the same runs.

**Decisions and recovery (all bounded):**
- **Statuses:** `READY` (Python ok) → `JUDGING` → `APPROVED | REJECTED` (VLM), then the human G2. The automatic regenerations below act on VLM rejections only. A human REJECT at G2 regenerates only when the human asks ("Regenerate" on the tile), never on its own.
- **More than 2 of 9 rejected, or the sheet check fails:** regenerate the whole sheet with a new seed, at most 3 sheet attempts. Keep the best as `PARTIAL`, or `FAILED` if 0 stickers are approved.
- **1–2 rejected:** regenerate only those cells in **single mode**, passing the first approved sticker as a reference image when the provider supports it (for character consistency). At most 2 attempts per cell. Approved stickers are never touched.
- **`CHROMA_RISK` on any cell:** regenerate the sheet once with the **other** key colour, and record `chroma_reason: "vision/pixel chroma risk"`.

---

## Part 3 — Generation APIs

```python
class ImageGenerator(Protocol):
    def generate(self, prompt: str, aspect: str, seed: int | None, reference: bytes | None = None) -> GenOutput: ...
class VideoGenerator(Protocol):
    def animate(self, image_png: bytes, prompt: str, duration_s: float, seed: int | None) -> GenOutput: ...
# GenOutput: bytes, provider, model, seed_used, latency_ms, cost_usd | None, raw_meta
```

- **Vendor:** WaveSpeed first. Port the working client and price table from `proposals/Mirsal-chat-emojis/api/wavespeed.py` and `spike/genmoji.py`.
- Build one image and one video provider. Keys go in `.env` only.
- `ModelSource` implements the Phase 1 source interface in `sources.py` (`find(prompt, variant) -> Pick`: sheet, optional video, subject, variant), so the engine and the store can't tell generated input from prepared input. **Changed 2026-10-01:** the `Phase_01` watch folders are mock samples and are **removed in Phase 3**, together with 1G's `higgsfield-manual` provider and the folder-number pairing. Generated sheets and videos are stored as assets under `out/` (object keys per generation) and linked by `tasks.external_task_id` (the Phase 2 "hard truth"), never by folder names. 1G's Inbox keeps working: it lists API tasks instead of watch folders.
- **Restricted network:** every provider client sits behind the Protocols above with recorded fixtures for tests; `mirsal doctor` checks keys and reachability; `--offline` stays first class.
- **Animation sheet: built in Phase 1** as `build_video_sheet()` (checkpoint 1F; it was planned here as `build_animation_sheet`).
  - It recomposes the stickers approved at G2 onto a flat-chroma canvas: same slots, rejected slots blank, subject at most 55% of the slot, no outline. It writes `layout.json`.
  - Phase 3 only sends that sheet to image-to-video **after G3** and stores the provider's task id in `video_sheets.ticket`. The returned video is attached by ticket, which replaces 1F's manual upload.
  - Slicing uses the layout's rectangles, and the `inside_slot` / `cross_slot` gate is the same Phase 1 code.
  - Measure the cross-cell interaction rate (`cross_slot` blocks / slots) and `subject_px_in_video` per provider. The fallback is per-sticker animation (a 1×1 sheet, one call per sticker), chosen per provider when either measure fails.
- **Ticket-based pairing (the Phase 2 "hard truth"):** every provider call inserts a `tasks` row (`provider`, `external_task_id`, `kind`, `name_key`, `request`) **before** waiting, and fills `result_ref` and `status` when it returns. The provider call returns a ticket (task id); store it on the generation, and when the image and video arrive, attach them to that generation by ticket, not by filename or take number. The Phase 1 number-matching (and its `pairing: order` guess) then only serves manual sandbox files.
- **Reliability:**
  - every call has a timeout and a max attempt count;
  - transient errors are retried up to 2 times; invalid input is never retried;
  - there is never a "while not good" loop;
  - if the video provider is down, stickers still work.
- **Engine changes allowed in this phase:** the two new Python checks, and `split_grid()` extensions (16:9, 4×4). Existing engine functions stay unchanged, including Phase 1's `build_video_sheet()` and layout slicing.

---

## Part 3b — Tracing (LangSmith; moved here from Phase 2 on 2026-10-01)

Phase 3 is where model calls start, so it is where tracing starts.

**Goal:** every stage and every gate decision of the golden path (`phase_01.md`, 1F) is visible in LangSmith.
- Postgres stays the record (`reviews`, `generation_events`, `model_calls`).
- LangSmith is the view, and the place where VLM verdicts are compared with human ones.

**`mirsal/obs/trace.py`** exposes `span(name, inputs, outputs, parent)` and `feedback(run_id, key, score, comment)`.
- It is wired into `pipeline.Stage`, the review route, and every provider / LLM / VLM call.
- **Backend `none`** is the default and records nothing outside Postgres.
- **Backend `langsmith`** uses the `langsmith` SDK. Its posts are batched on a background thread; a failed post is logged and dropped. **Tracing never blocks or fails the pipeline.**

**Mapping:**
- One root run per generation.
- One child run per stage and per model call.
- **Each gate decision is feedback** on the run it judges:
  - keys `gate_plan | gate_still | gate_video_sheet | gate_anim | gate_pack` for humans, and `vlm_still | vlm_anim` for the judge;
  - score 1 for APPROVE/PASS and 0 for REJECT/BLOCK;
  - comment = the reason.

**What leaves the machine:** ids, slot JSON, prompts, metrics and decisions. **Never image or video bytes;** files are referred to by object key. This is fixed in code (Mirsal is positioned as a secure chat).

**Config:** `MIRSAL_TRACE=none|langsmith`, `LANGSMITH_API_KEY`, `LANGSMITH_ENDPOINT` (cloud or self-hosted), `LANGSMITH_PROJECT=mirsal`. `doctor` reports the backend and whether it is reachable.

**`mirsal trace backfill [--since]`** replays the Phase 2 rows that have no `trace_run_id`, including all of Phase 2's history. It is idempotent.

**Tests:**
- `none` makes zero network calls (socket guard);
- against a local fake server, `langsmith` gets one root run per generation, one child run per stage, and one feedback per decision, with no media bytes in any payload;
- a 500 or a timeout from the server does not slow the pipeline.

**Open decision for Haitham:** LangSmith cloud or self-hosted. Phase 4 keeps the same keys when LangGraph adds its own native runs to the same project.

---

## Schema (`002_models.sql`)

```sql
ALTER TABLE generations
  ADD COLUMN seed bigint, ADD COLUMN attempts int NOT NULL DEFAULT 1,
  ADD COLUMN key_color text, ADD COLUMN chroma_reason text,
  ADD COLUMN style_id text, ADD COLUMN mode text,          -- 'sheet' | 'single'
  -- `plan jsonb` exists since Phase 2 (same shape, extended by the planner): do not add it again
  ADD COLUMN planner_version text, ADD COLUMN prompt_template_version text,  -- assembly template, not Phase 4 transformations
  ADD COLUMN final_prompt text, ADD COLUMN final_video_prompt text,
  ADD COLUMN sheet_check jsonb;
ALTER TABLE stickers
  ADD COLUMN judge jsonb,                                   -- VLM Judgement
  ADD COLUMN keywords jsonb,                                -- {"en": [...], "ar": [...]}
  ADD COLUMN emoji_suggestion text[];
ALTER TABLE generations ADD COLUMN prompt_slots jsonb, ADD COLUMN template_id text;   -- template-locked prompts (Part 1)
ALTER TABLE generation_events ADD COLUMN trace_run_id uuid;                          -- Part 3b
ALTER TABLE reviews           ADD COLUMN trace_run_id uuid;
CREATE TABLE model_calls (
  id bigserial PRIMARY KEY,
  generation_id text REFERENCES generations(id), sticker_id text REFERENCES stickers(id),
  kind text NOT NULL,            -- LLM_PLAN | IMAGE_SHEET | IMAGE_SINGLE | VIDEO | VLM_STICKER | VLM_SHEET
  provider text NOT NULL, model text NOT NULL, prompt_version text,
  attempt int NOT NULL, seed bigint,
  status text NOT NULL,          -- OK | TIMEOUT | ERROR | INVALID_OUTPUT | REJECTED_BY_GATE
  latency_ms int, tokens_in int, tokens_out int, cost_usd numeric(10,4), error text, raw_output text,
  created_at timestamptz NOT NULL DEFAULT now()
);
```

---

## Part 4 — Quality work (the heart of the phase)

1. **Prompt lab:** run `prompt` on 20 inputs, including Haitham's own ("yellow teddy bear in Pixar 3D iOS style", "yellow teddy bear in toon cel shade with ios 3d genmoji style", the generic 4×4 yellow faces), Arabic and Arabizi requests, a UAE occasion, a green subject, and a constraint. Haitham reviews them against `prompt_samples.md`, and the planner prompt is iterated (`planner_v2`, …), with every version kept.
2. **Sheet vs single:** the same 5 requests in both modes. Compare character consistency (the VLM `character_match` rate plus Haitham's eye), pass rate and cost, and pick the default.
3. **Outline A/B:** Python outline vs model die-cut outline, on 5 requests.
4. **Judge calibration:** Haitham labels 30 stickers approve/reject. The VLM must agree on ≥80%, or `judge_v1` is tuned. Record agreement per reason.
5. Everything is recorded in `docs/phase3_measurements.md`: pass rate, rating, cost, latency, judge agreement and decisions.

## Tests (offline, no network)
- **Fake planner:** the lint catches injected faults (8 cells, a duplicate concept, "transparent background", "contact shadow", a green subject on a green key, an empty style lock).
- **Style handling:** a `--style` flag wins; no style words → the default preset verbatim; a blend passes through to `style_lock`.
- **Golden assembly:** 5 fixed plans → exact sheet and single prompt strings, in 3×3 and 4×4.
- **`split_grid()`:** golden tests on synthetic sheets with outer padding, uneven gutters, and 16:9 4×4.
- **Fake VLM:** 1 rejection → single-cell regeneration only; 3 rejections → sheet regeneration; `CHROMA_RISK` → a blue-key rerun; VLM down → both policies; invalid JSON → repair, then fail with the raw output logged.
- **Fake image/video generators** reuse the synthetic sheets and MP4; retry limits and timeouts hold.

## Exit (checkpoint 3A)
- [ ] `prompt` produces locks + 9 concepts + sheet and single prompts for English, Arabic and Arabizi, and Haitham approves them against `prompt_samples.md`.
- [ ] Measured: ≥80% of live `create` runs end with ≥7/9 **approved**; Haitham's average rating is ≥4/5.
- [ ] The judge agrees with Haitham on ≥80% of 30 stickers.
- [ ] The sheet-vs-single and outline decisions are made and recorded.
- [ ] `animate` works from the animation sheet, and the cross-cell rate is measured.
- [ ] Every LLM, image, video and VLM call is in `model_calls` with latency and cost.

## Part 5 — Semantic sticker pool (checkpoint 3B: search → reuse → generate only the gaps)

**Idea (ported from the old build's `/api/pool`, with its defects fixed):**
- Every approved sticker joins a searchable pool.
- A request like **"{topic} doing {action}"** ("falcon dancing", "banana shocked", "صقر يرقص") first fetches matching existing stickers: **free and instant**.
- Only the missing count goes to paid generation, and only after the price is shown.
- New stickers join the pool, so it grows with use.
- **No Redis here:** Postgres + pgvector only. Phase 4 adds a cache on top later.

**Write path (index):**
- Each `APPROVED` sticker gets a row in `sticker_index`. Hidden stickers and inherited edit copies (from Phase 4) are skipped.
- **`subject`**: `plan.extraction.subject`. For prepared sets, the set name.
- **`action`**: the cell's `action`, falling back to `name` + `concept`.
- **`search_text`**: `subject — action — name — emoji — style_id`. Phase 4C appends `annotation.visual_summary` and reindexes.
- **`topics`**: normalized tags, using the old build's `normalize_topic()`: lower-case, apostrophes folded, punctuation dropped, Arabic letters kept. So "Mother's Day!" becomes `mothers day`.
- **Two vectors per sticker:**
  - `subject_vec` = embed(subject);
  - `action_vec` = embed(action + name).
  - The model is `EMBED_MODEL` (default `text-embedding-3-small`, 1536-d, as in the old build). The model name is stored per row for reindexing.
- **Commands:** `mirsal pool reindex` backfills every earlier generation, including Phase 1–2 prepared-set runs. `mirsal pool hide <sticker_id>` removes a sticker from search without deleting it.

**Read path: `mirsal search "falcon dancing" [--count 9] [--style …]`**
1. **Parse the query** into `{subject, action, emotion?, style?, topics[]}`.
   - Deterministic patterns come first: "X doing Y", "X Y-ing", "Y X", "X that is Y".
   - Arabic, Arabizi and anything unmatched go to `claude-haiku-4-5-20251001` with a strict schema. The output is English.
2. **Hybrid score:**
   - The parts: `0.5·cos(subject) + 0.4·cos(action) + 0.1·lexical`. The lexical part is a trigram match on name/emoji/topics.
   - Filter out hidden stickers, missing images, a mismatched `style_id` when a style was asked for, and anything outside the viewer's scope (below).
3. **Quality gate** (the old build had none; it returned nearest neighbours even when irrelevant): a hit counts only if `cos(subject) ≥ SUBJECT_MIN` **and** `cos(action) ≥ ACTION_MIN`, with both calibrated on the eval set. "Penguin skiing" in a pool with no penguins returns **zero**, never the closest junk.
4. **Diversity:** at most 2 hits per generation. Near-duplicates (`search_text` cosine > 0.97) collapse to the best-judged one.
5. **Gaps:**
   - If fewer than `--count` match, the reply is: "Found 4 · generate 5 more? (~$X)".
   - On confirmation, the gap is generated through Part 3 with the parsed subject + action as the request, varying that action.
   - `create` always generates (it's what the Part 4 measurements use). `search` is the pool-first command. Phase 5 merges both into one search box.

**Sharing scope:**
- Until Phase 5 there is one local user.
- The rule is fixed now for 5C: stickers from **text-only** requests are `shared = true`. Anything from an **uploaded reference image** is `shared = false` forever, visible to its owner only.

**Migration `003_pool.sql`:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;            -- image is pgvector/pgvector:pg16 since Phase 2
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE TABLE sticker_index (
  sticker_id  text PRIMARY KEY REFERENCES stickers(id),
  subject     text NOT NULL, action text NOT NULL, search_text text NOT NULL,
  topics      text[] NOT NULL DEFAULT '{}',
  subject_vec vector(1536) NOT NULL, action_vec vector(1536) NOT NULL,
  embed_model text NOT NULL,
  shared      boolean NOT NULL DEFAULT true, hidden boolean NOT NULL DEFAULT false,
  indexed_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON sticker_index USING hnsw (subject_vec vector_cosine_ops);
CREATE INDEX ON sticker_index USING hnsw (action_vec vector_cosine_ops);
CREATE INDEX ON sticker_index USING gin (topics);
CREATE INDEX ON sticker_index USING gin (search_text gin_trgm_ops);
-- search_log exists since Phase 2 (id, query, filters, hit_ids, latency_ms, created_at); extend it, never re-create it
ALTER TABLE search_log ADD COLUMN parsed jsonb, ADD COLUMN gap_generated int NOT NULL DEFAULT 0;
```

**Phase 2 already has `mirsal search`** (full-text on prompt, key and tags, plus a trigram fallback, with gate filters) and the console's Library search. 3B upgrades the same command and route to the hybrid score below. It keeps Phase 2's filters (`--approved`, `--animated`) and `tags` as part of `topics`. A sticker is "approved" for the pool when its human gate says so (`still_review = 'APPROVED'`, see 1F). A VLM approval alone counts only when `auto_approve_vlm` is on.

**Eval set:** `Phase_03/search_queries.md` holds ~30 queries (English, Arabic, Arabizi), each with the sticker IDs Haitham considers relevant, plus ≥5 that should return nothing.

**3B exit:**
- [ ] `search "falcon dancing"` returns only dancing falcons, not a dancing banana or a sleeping falcon. It is free, with no image calls in `model_calls`.
- [ ] Measured on the eval set: precision@5 ≥ 0.8, and **0 results** on every should-return-nothing query. The thresholds are recorded in `docs/phase3_measurements.md`.
- [ ] The gap flow: "found N, generate M more?", with the price shown. The generated stickers are indexed and findable on the very next search.
- [ ] `pool reindex` covers every earlier generation. A hidden sticker never appears.
- [ ] Search latency is measured with no cache; this is the baseline Phase 4's Redis cache must beat.

---

## Part 6 — Photo cutout stickers (checkpoint 3C)

**What the user does:** takes a photo of their dog, brother or food. The subject comes back **cut out** with clean alpha and an outline, as a 512 sticker. That's the whole feature. Text on stickers is the separate Part 7.

```
python -m mirsal photo dog.jpg [--outline white|color|dieCut|none] [--subject N]
```

It needs the Phase 1 engine (scale, outline, validators) and Phase 2 storage; no prompts, no generation API, no Redis.

**Use an existing library, do not write one** (options and licence cautions are tabulated in `README.md`, "Keyers": rembg with U2-Net/ISNet/BiRefNet first, transparent-background, SAM 2 for click-to-select, OpenCV `grabCut` as a zero-download fallback). Wire it as the last rung of Phase 1's key-failure ladder as well, so a failed green-screen cell gets one matting attempt before it is ruled out.

**Update (Phase 1, Part E):** the seam now exists as `mirsal/matte.py` (U2-Net / IS-Net through onnxruntime, models in `mirsal/models/`), called by `library.cutout` (auto -> matte -> GrabCut) and by the video background-removal provider; 3C's remaining work is a stronger model (BiRefNet), click-to-refine (SAM 2) and video propagation behind the same functions. **Earlier state (Part D):** `library.cutout()` (used by the desktop builder's "Create from photo") keeps existing alpha, chroma-keys green/blue screens with the Phase 1 engine, and otherwise runs OpenCV GrabCut with an inset rectangle. It is the seam for this part: implement `engine/matte.py`, call it from `library.cutout` for the non-green branch, keep GrabCut only as the no-weights fallback, and keep the `method`/`foreground`/`warning` info the editor shows. GrabCut is known to fail on busy backgrounds and similar colours, so 3C's exit should compare both on Haitham's own photos. The editor's Erase/Restore brush is the human fallback and needs no change.

**Matting keyer (new, same contract as Phase 1's chroma key):** photos have no green screen, so add `engine/matte.py` exposing the same `key_image(rgb, cfg) -> Keyed(rgba, ...)` shape, with backends `rembg` (u2net / isnet-general-use / birefnet). Everything after the key (specks, trim, pack scale, outline, validators) is Phase 1 code, untouched. Model weights are downloaded once on a connected machine and loaded by path (`MIRSAL_MATTE_MODEL`); `doctor` checks them. Video matting (RVM) stays opt-in and out of the default path: per-frame matting flickers, which is why Phase 1 keeps chroma for video.

- **Matting, not chroma key:** `Matting.segment(photo) -> alpha`. The default is **local**: BiRefNet (MIT licence) via onnxruntime, at full resolution for fur and hair edges.
- **Fallback:** port `proposals/Mirsal-chat-emojis/api/cutout.py` (`silueta.onnx` U2-Net 320 px + GrabCut). It is too coarse for fur, which is why it's only the fallback.
- **On-device by default:** the photo never leaves the machine (Mirsal is a secure chat). A hosted matting API sits behind the same interface, opt-in only.
- **Subject choice:** the largest connected subject ≥2% of the frame; `--subject N` picks another.
- **Then the Phase 1 steps:** speck removal, trim, scale (occupancy 0.775), premultiplied resize, and the outline: None / White / Color / Die-cut, the old POC's set.
- **Checks:**
  - `single_subject` and `foreground`;
  - `edge_quality`: a soft alpha gradient along the contour, not a hard binary edge;
  - `static_file`.
- **Optional paid AI motion** (opt-in, price shown first): the cutout on flat chroma goes to the Part 3 video model, then through the Phase 1 keying and loop close.
- **Privacy:** the photo (`SOURCE_PHOTO` asset) and its stickers are `shared = false`: never in the shared pool. Haitham's test photos live in `Phase_03/photos/`, which is **gitignored**.

**Tests:**
- Composite our own keyed stickers onto cluttered photo backgrounds (the old POC's method) and require IoU ≥ 0.92.
- A synthetic fur-edge shape keeps a soft gradient.
- Default mode makes **zero network calls** (sockets blocked in the test).

**3C exit:**
- [ ] `photo dog.jpg` gives a clean subject sticker in ≤3 s, on the chain page.
- [ ] On Haitham's 10+ real photos (pets, people, food), he judges the edges clean. IoU ≥ 0.92 on composites.
- [ ] No network calls in default mode.

---

## Part 7 — Text template stickers (checkpoint 3D, CapCut-style)

**What the user gets:** a big library of ready-made **templates**, each a flashy sticker design with a text slot. The animation is only **1–2 frames flashing on repeat**, like an old "Happy Holiday" web banner: colours swap, sparkles jump, a neon sign flickers.
- The user's words drop into the slot.
- When the user's **last chat message is ≤ `N` words** (default 4, ≤24 characters), the app auto-fills it and suggests the best-matching templates.
- It is Snapchat's "comment on a sticker", and WhatsApp's newer auto-text sticker done properly: many templates instead of a couple of fixed images, matched to the message, and working in Arabic.

```
python -m mirsal text "happy eid"                   # "last message" → top 6 matching templates, filled, on the chain page
python -m mirsal text "صباح الخير" --template neon_flicker
python -m mirsal templates [--tag eid]              # browse the library
python -m mirsal template check <id>                # validate a new template
```

**Template = files, versioned in the repo** (`mirsal/templates/<id>/`):
- `template.json` holds:
  - `id`, `version`;
  - `tags` {en[], ar[]}, `occasion` (UAE events), `mood`;
  - `frames`: 1–4 entries, each `{art: "f1.png" | null, duration_ms, text_style}`. `text_style` sets the fill, stroke, glow and offset **per frame**, which is what makes it flash.
  - `slot`: the text box `{x, y, w, h, rotation, align, max_chars, font_id}`.
  - an optional `subject_slot`, so a 3C cutout can sit in the template.
- **Frame art** is 512×512 RGBA. It is either procedural (drawn by code from `template.json`: starbursts, sparkles, neon tubes, badges), so the starter set needs no artwork and no licences, or PNGs from Haitham or designers.
- The art may also be generated once through Part 3's image model, **without text** (models garble text), then turned into a template.
- **Starter library:** 30+ procedural templates across greetings, reactions, love, birthday and the UAE occasions (National Day, Eid, Ramadan). More are added by dropping folders in.

**Render (deterministic, instant, free):**
- For each frame: the frame art, plus the text auto-fitted into the slot with that frame's style.
- **Text is rendered by code**, with bundled open-licence display fonts (Latin + Arabic, licence files committed).
- **Arabic** uses Pillow + libraqm for shaping and right-to-left layout, falling back to `arabic-reshaper` + `python-bidi`. A word is never split, because splitting breaks the letter joins.
- Frames loop, so the loop is **seamless by construction**.
- **Encoding:**
  - **WEBM VP9 + alpha** at the template's frame timing, repeated to fill ≤3 s, through the Phase 1 encoder and validators (Telegram);
  - plus **animated WEBP** (WhatsApp-style, 512×512, ≤500 KB).
  - **Not GIF:** its 1-bit transparency makes the text edges jagged.
- **Editable:** text is data. `text_layer = {template_id, template_version, text, overrides}` is stored, and editing re-renders in under a second as a new generation with a parent.

**Matching the message to templates:**
1. An exact `occasion`/`tags` hit ("eid", "عيد", "good morning") in English or Arabic.
2. Otherwise, embedding similarity between the message and each template's tags, reusing the 3B `EMBED_MODEL`.
3. Otherwise, generic templates.

The top K results are diversified, so the six suggestions aren't six near-identical neon designs. Messages over `N` words get no auto-fill; the user types the text instead.

**Tests:**
- Every template passes `template check`: the text fits the slot at `max_chars` in both scripts; every frame is 512 RGBA; the timing is valid.
- "صباح الخير" renders joined, with a golden hash against the raqm reference.
- Outputs pass the Telegram video validator and the animated-WEBP size limit.
- "happy eid" ranks Eid templates first; a 6-word message gets no auto-fill.
- An edit makes no network calls and finishes in under 1 s.

**3D exit:**
- [ ] `text "happy eid"` gives 6 filled, flashing, Telegram-valid stickers in ≤2 s.
- [ ] Arabic works in every template.
- [ ] Haitham rates the starter library as good enough to demo, and a new template folder dropped in shows up with no code change.

**Migration `004_photo_text_depth.sql`** (also covers 3C and 3E):
```sql
ALTER TABLE assets DROP CONSTRAINT assets_kind_check;
ALTER TABLE assets ADD CONSTRAINT assets_kind_check
  CHECK (kind IN ('SOURCE_SHEET','SOURCE_VIDEO','SOURCE_PHOTO','PNG','WEBP','WEBM','WEBP_ANIM','DEPTH','LAYER'));
ALTER TABLE stickers
  ADD COLUMN kind text NOT NULL DEFAULT 'SHEET'
    CHECK (kind IN ('SHEET','PHOTO_SUBJECT','TEXT_TEMPLATE','TEXT_TEMPLATE_WITH_PHOTO')),
  ADD COLUMN text_layer jsonb;
-- generations.source gains 'photo', 'template' and 'depth'
```

---

## Part 8 — 3D parallax photos (checkpoint 3E)

**What the user sees:** any photo, whether taken or received in chat, gets depth and **moves in 3D as the phone tilts**. The subject stays anchored while the background shifts behind it. It's like a Live Photo, but with parallax instead of motion. Apple ships the same effect as Spatial Scenes in iOS 26 Photos; Mirsal brings it to chat images.

It is not a sticker feature: it's a photo viewing effect. It sits in Phase 3 because it reuses the 3C matting and needs no Redis. Phase 5 puts the viewer into the app.

```
python -m mirsal depth photo.jpg [--strength 0.02] [--layers 1|2|3] [--bake]
```

This writes `out/G00N/`:
- `depth.png` (16-bit), plus layer PNGs when `--layers ≥2`;
- `parallax.html`: a self-contained WebGL viewer that follows the mouse on a laptop and the **gyroscope** on a phone;
- with `--bake`, a looping tilt-sweep video for places without WebGL or a gyro.

**1. Depth (on-device by default, like 3C):**
1. **Embedded depth first.** iPhone Portrait photos (HEIC) carry Apple's own depth/disparity map. Read it with `pillow-heif` when present, since it beats any estimate.
2. **Otherwise estimate** with **Depth Anything V2 Small** (Apache-2.0) via onnxruntime at ~1024 px on the long side.
   - Its Base, Large and Giant sizes are **CC-BY-NC (non-commercial)**, so don't use them.
   - Check the licence of any other model (e.g. Apple Depth Pro) before adopting it.
3. **Edge-aware smoothing:** a guided filter on the depth, with the photo as the guide, so depth edges snap to object edges. Smeared edges cause the rubbery stretching.

**2. Focal anchor:** run the 3C matting to find the subject and put the focal plane at its median depth. The subject stays still and the background moves around it; without a subject, focus on the nearest large region.

**3. Rendering, in two quality levels (the start is the first):**
- **Displacement shader (default):** sample the image at `uv + tilt × (depth − focal) × strength`, with `strength` subtle (≈1–3% of the width).
  - Use a slightly dilated foreground depth so edges tear inward instead of smearing.
  - It's cheap, and works on any phone.
- **Layered (`--layers 2|3`, only if the default's halos look bad):**
  - split at the big depth jumps into foreground/background planes;
  - **inpaint the background hidden behind the subject** (OpenCV Telea as the baseline; LaMa, Apache-2.0, as the quality option);
  - render them as stacked planes.

**4. Motion input (web viewer):**
- The gyroscope comes through `DeviceOrientationEvent`. **iOS requires a tap-to-allow permission and HTTPS.**
- Low-pass filter the readings, recenter on the first one, and clamp the tilt.
- Fall back to mouse or touch drag.
- Respect `prefers-reduced-motion` by showing the image static.

**5. Chat contract (for Mirsal's own app):**
- An image message carries `{depth_asset_id, focal_depth, strength, layers[]}`, and the client renders parallax instead of a flat image (with a toggle).
- The web viewer is the **reference implementation**. The native iOS client would do the same with Metal and CoreMotion from the same data.
- A depth map can't reproduce the photo on its own, but it is still derived from a private image, so it gets the same access rules as the photo.

**Privacy and storage:** the photo and depth are private (`shared = false`). A `depth` generation stores `SOURCE_PHOTO`, `DEPTH` and `LAYER` assets (no stickers rows). Haitham's test photos go in `Phase_03/photos/` (gitignored).

**Tests (offline):**
- **Synthetic scene with known depth** (three textured planes at different distances): the estimated depth ordering matches, and the focal anchor lands on the subject plane.
- **Embedded depth:** a Portrait HEIC sample yields a depth map, and the pipeline prefers it over estimation.
- **Viewer:** a headless browser checks that `parallax.html` loads, the shader compiles, and the mouse and simulated orientation events change the uniforms. DOM and uniform values only, no screenshots.
- **Privacy:** default mode makes zero network calls.

**3E exit:**
- [ ] `depth photo.jpg` finishes in ≤3 s on this Mac for a 12 MP photo.
- [ ] `parallax.html` works with the mouse on desktop and with **tilt on Haitham's iPhone** (served over HTTPS, e.g. a local tunnel).
- [ ] The subject stays anchored. On 10 real photos, Haitham judges the edge halos acceptable, and switches to `--layers 2` if not.
- [ ] Portrait HEIC photos use their embedded depth.
- [ ] `--bake` produces a valid looping video. No network calls in default mode.

---

## Explicitly deferred
- **Photo filters (TODO; not planned in any phase yet):**
  - **Blur background.** *Easy*, about a day after 3C: the 3C cutout over a blurred copy of the original. The output is a photo, not a sticker, so build it only if Mirsal wants photo effects.
  - **Beautify** (skin smoothing, retouch). *Medium*: MediaPipe face landmarks (Apache-2.0), a skin mask and edge-preserving smoothing. People only. Needs a product and ethics decision first.
  - **Parallax stickers** (idea): 3E depth applied to generated stickers, so they tilt in 3D inside Mirsal. Telegram can't render gyroscope effects, so this is Mirsal-only.
  - **Snapchat Lens Studio import.** *Not engineering*: lenses only run inside Snap's runtime and can't be exported. The only route is Snap's Camera Kit SDK, which needs Snap's approval and commercial terms and sends data to Snap, conflicting with Mirsal's secure-chat positioning. Alternatives we own: 2D photo frames via 3D templates (`subject_slot`), or MediaPipe face effects.
- Follow-ups ("make number 3 happier"), references, feedback, transformation templates (dog as banana), annotation and memory → Phase 4.
- Caching (planner output, VLM verdicts, search results) → Phase 4, in Redis.
- 60 FPS: dropped (the Telegram cap is 30).

## Hands to Phase 4
- A structured plan per generation (extraction, locks, cells), assembled in two modes.
- A calibrated vision judge.
- Python pixel checks and grid detection.
- A `StickerSource` that really generates.
- Per-call accounting.
