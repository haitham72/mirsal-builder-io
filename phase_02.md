# Phase 2 — Generation: what is still open

> **A tracker, not a log** (`CLAUDE.md` rule 7). Phase 2 was Phase 3 until 2026-10-01 (Haitham reordered: generation first, Postgres second). **The live half is built and in use** and is described as architecture in [`Phase_02/README.md`](Phase_02/README.md): template-locked prompts (v1–v3), the emotion bank and styles, the AI slot filler with its code lint and small reviewer, references, jobs fulfilled through the Higgsfield CLI (ticket first, retry, daily cap), the model catalog, the usage ledger, the Generate menu, the Kling animation from the normalised video sheet (gap, Loop, edge preview with Apply / Undo, allow anyway, blue-screen keying) and the named export folders. This file keeps only what is **not** built or not yet measured. Supporting inputs: `Phase_02/CLAUDE.md`, `Phase_02/prompt_samples.md`, `Phase_02/higgsfield.md`.

**Not in this phase:** Postgres, LangSmith, vectors / pool, photo / text / depth stickers (Phase 3), Redis, LangGraph, a frontend rewrite (Phases 4-5).

> The LLM writes the creative content. Code writes the constraints. Python judges what is *correct*; the VLM judges what is *good*.

## Rules for whoever runs jobs
The server fulfils jobs itself (`jobs.fulfil` through the Higgsfield CLI); an operator session can run `mirsal hf run J###` or the claim / done / fail commands. Ticket first (create without waiting, claim, then wait); one paid call at a time; never retry a paid call by hand (`Retry` waits for the same job); `generate cost` before every call; **Nano Banana 2 at 2k and Kling v3.0 `pro`, never Kling 4k**; never open or judge media (Python and the human judge); never write inside `Phase_01/Images_gen|videos_gen`; tests never reach the real CLI (`MIRSAL_NO_REAL_CLI`). Nothing raw goes to the video model: the video is made from the normalised video sheet.

## Open steps (each ends with something Haitham can see; stop at each gate)

| Step | What is left | Done when |
|---|---|---|
| **S4** | **Measure the normalised video.** The Kling path is built and has run for real (G002 and later). Left: re-run G002 with `pro` and the current gap (its first clip, J004, was `std`), write `python -m mirsal measure-cells` (the share of cells flagged by `inside_slot` / `cross_slot` / `inside_frame`, the cross-cell interaction rate, `subject_px_in_video`), record it, then tune `slot_fill` (0.74 now, the user slides it per batch) or choose a 2x2 sheet / one sticker per video. Target: nothing flagged. | The flagged share is measured and recorded in `docs/phase2_measurements.md`; the default gap is chosen. |
| **S5** | **AI lab rating.** The slot filler and reviewer are built. Left: `mirsal prompt lab --ai` (20 prompts) and Haitham's rating. | The 20 pass lint; Haitham rates them. |
| **S6** | **Vision judge** (below) and the bounded regeneration rules. Needs Haitham's 30 labelled stickers and one decision: the judge on `OPENAI_API_KEY` or an agent judge in the operator session. | The judge agrees with Haitham on at least 80% of the 30. |
| **S7** | **Quality work** (below): sheet vs single, model outline vs the engine's. | Exit below. |

### Leftovers of the original planner design (ask Haitham whether each is still wanted before building)
- **UAE content rules** as a lint (`prompts/content_rules.md`, ported from the old POC `proposals/Mirsal-chat-emojis/api/planner.py`): no flags, emblems or text; no real people, rulers or religious figures; the falcon is always "a young brown saker falcon chick"; Emirati dress rules; Commemoration Day is solemn. Not built; the lint only has banned words.
- **English + Arabic search keywords per cell** for Telegram (0-20 keywords, 64 characters total, English first). Not built.
- **4x4 grid** (the generic-emoji layout) and 16:9 sheets: `split_grid` handles 2x2 and 3x3 only.
- **No trademarks in published metadata** (Genmoji, Apple, Pixar, Disney may appear in prompts, never in a Telegram title or tag): check that the pack name and tags are guarded.
- **A 2x2 sheet gives each sticker 2.25x the pixels of a 3x3** (open question: offer 2x2 for the animation sheet by default?).

## Part 2 — Vision quality check (S6)

**Python first** (deterministic; its facts are final, and live in `engine/verify.py`): `background_flat`, `chroma_risk`, `holes`, `layout_match`, `inside_slot` / `cross_slot` and the rest. Phase 2 adds no second checker; it *acts* on their verdicts (`chroma_risk` / `holes` above threshold -> the other key colour; `cut_clean` / `grid_detected` failures -> a new sheet).

**VLM second** (a pre-reviewer, never the gate):
- `VisionJudge.judge_sticker(png, cell, pack_ctx) -> Judgement`; `pack_ctx` holds the subject description, the style and a reference sticker (the first approved one).
- Output: `{decision: APPROVE|REJECT, confidence, concept_match, emoji_fit, character_match, style_match, reasons[]}`; reasons from a fixed list: DUPLICATE, WEAK_CONCEPT, AMBIGUOUS_ACTION, STYLE_DRIFT, IDENTITY_DRIFT, SEVERE_ARTIFACT, POOR_COMPOSITION, ANIMATION_RISK, CHROMA_RISK, MISSING_REQUIRED_ELEMENT, ANATOMY_ERROR, OBJECT_DEFORMATION, EMOJI_MISMATCH, UNWANTED_TEXT. A better emoji may be suggested and is stored; it is applied only if the config allows it.
- A sheet check: one call per sheet (count, isolated cells, none missing or duplicated).
- The division of labour is strict: the VLM never overrides Python on dimensions, alpha or bounds; Python never judges funny, cute or expressive.
- **Where it sits:** its verdict is a history line with `actor = 'vlm'` at the same gate (`still` before G2, `anim` before G4; a `reviews` row once Phase 3 imports it, LangSmith feedback `vlm_still` / `vlm_anim`). The Studio shows it next to the tile; the human still decides. `auto_approve_vlm` (off by default) would also set the review and skip the human gate, recorded as such.
- **Implementation:** one OpenAI-compatible vision client (`VISION_BASE_URL`, `VISION_MODEL`, `VISION_TIMEOUT`, `VISION_MAX_TOKENS`, `VISION_CONCURRENCY`); the same interface can sit on vLLM (needs an NVIDIA GPU), LM Studio, a hosted endpoint or Claude vision. **Never trust `response_format` from a local model**: parse, validate, one repair, log the raw output when that fails. Policy when the VLM is down: `FAIL_CLOSED` (default; stickers stay READY, flagged "unjudged") or `DETERMINISTIC_ONLY`.
- **Bounded recovery** (acts on VLM rejections only; a human REJECT regenerates only when the human asks): more than 2 of 9 rejected or the sheet check fails -> a new sheet, at most 3 attempts (keep the best as PARTIAL, FAILED if none approved); 1-2 rejected -> only those cells as 1x1 through the same engine, the first approved sticker as a reference when the model takes references, at most 2 attempts per cell, approved stickers never touched; `CHROMA_RISK` -> one sheet with the other key colour, recorded.
- **Tests (offline, fake VLM):** 1 rejection -> single-cell regeneration only; 3 -> sheet regeneration; `CHROMA_RISK` -> the other key; VLM down under both policies; invalid JSON -> repair, then fail with the raw output logged. Every VLM call is a line in `out/model_calls.jsonl`.

## Part 4 — Quality work (S7, "measured, not guessed")
1. **Sheet vs single:** the same 5 requests in both modes; compare character consistency (VLM `character_match` plus Haitham's eye), pass rate and cost; pick the default.
2. **Outline A/B:** the engine's outline (default, `Edge`) vs a model-drawn die-cut outline with `outline_px: 0` on 5 requests. Never both.
3. **Judge calibration:** Haitham labels 30 stickers; the VLM must agree on >= 80%, or the judge prompt is tuned. Record agreement per reason.
4. Everything in `docs/phase2_measurements.md`: pass rate, rating, cost, latency, judge agreement, decisions.

## Exit (Phase 2)
- [ ] `prompt` gives English, Arabic and Arabizi plans that Haitham approves against `prompt_samples.md` (gate S1).
- [ ] Measured: >= 80% of live runs end with >= 7/9 **approved**; Haitham's average rating >= 4/5 (live runs so far: G001-G008; G006 failed on the blue-key bug, now fixed, G007 on a 3x4 layout the model drew).
- [ ] The judge agrees with Haitham on >= 80% of 30 stickers (S6).
- [ ] The sheet-vs-single and outline decisions are made and recorded (S7).
- [ ] A real video from the normalised sheet is sliced and the flagged share (`measure-cells`) is recorded; `slot_fill` chosen (S4).
- [ ] Haitham ran one full request live, end to end into a Telegram pack.
- [ ] Every LLM, image, video **and VLM** call is a line in `out/model_calls.jsonl` with latency and cost (all but the VLM already are).

## Hands to Phase 3
`out/jobs/*.json`, `out/tasks/*.json` and `out/model_calls.jsonl` are already imported by 3A. Still to hand over: the VLM verdicts as `actor = 'vlm'` history lines (-> `reviews` rows), the judge version on every generation, and `docs/phase2_measurements.md`.
