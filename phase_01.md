# Phase 1 — Sticker Engine (prepared sheets → stickers → animation)

**Goal:** prove the Python.
- Haitham types `banana with big eyes`.
- The app picks a sheet he prepared, keys out the green, cuts it into 9 cells, and scales each one into a clean 512×512 transparent sticker.
- It shows the stickers on a preview page.
- Part B does the same for a prepared 3×3 video, producing transparent looping WEBMs.

**Not in this phase:** a database, generation APIs, LLMs, LangGraph, or the production web app. Those are Phases 2–5.

**In this phase (Part C):** a minimal local **Lifecycle Console**: one page, stdlib server, no framework. It shows each generation moving through its real steps: pick sheet → key → slice → pick video → key → slice.

**In this phase (Part D):** the console grows into the **desktop Sticker Builder** (Library, Chat echo, Create, Editor, Pack manager, animated editor, export) following `ref/Mirsal-Builder.jpg`. Phase 1 is one phase: there is no separate "1B phase" any more.

> The quality of the keying and scaling **is** the demo. Most of the effort goes there.

The phase has checkpoints 1A (static), 1B (animation), 1D (desktop builder, Part D), 1E (video/GIF projects) and **1F (the golden path with review gates, added 2026-10-01; the prerequisite for Phase 2)**. Haitham reviews **1A** before **1B** starts. The console (Part C) is built incrementally: its still-image stages ship with 1A and its video stages with 1B, so it is the review surface for both.

---

## As built (read first)

> **How this file works:** this plan is the hand-off. What is built and proven is recorded in `README.md` (architecture). Items here are ticked when done and only removed after Haitham approves the gate, so nothing is lost before review. Keep enhancing this file; never shrink it to make it look finished.

### Decisions that override the text below

| Was planned | As built | Why |
|---|---|---|
| Inputs in `mirsal/sets/<subject>/NN/{sheet.png,manifest.json,video.mp4}` + `set.json` (and, later in the build, image/video pairing by take number) | Inputs read in place from `Phase_01/Images_gen/img-NNN-<subject>/` and `Phase_01/videos_gen/vid-NNN-<subject>/`: **one folder per variant, image and video paired by the same folder number NNN**. Pre-sliced clips in `vid-NNN/slices/{quicktime,webm}/<name> (n).<ext>` (n = grid cell) replace slicing the 3x3 mp4 (`.mov` preferred). Names in the watch folders are final and never renamed by the app; a positional guess (`pairing: order`, flagged by `doctor`) exists only as a last resort. `sources.py` (`PhaseDirSource`) replaces `FixtureSource`/`StickerSource` | Matches how Haitham actually generates; no copying, no hand-written JSON |
| `manifest.json` per variant (names, emoji, prompts) | The **prompter stub** (`prompter.py`) expands the task into `prompts.json`: 9 x `{index, id, prompt, key, emoji}` + `sheet_prompt`, `video_prompt`, modular `guidelines`. Plain JSON, no pydantic/LLM | Each sticker gets its own name from the prompter output; same shape a Phase 3 planner must return |
| `S1.png`..`S9.png` | `<media>-<NNN>-<task_slug>-<key>.<ext>`, e.g. `img-001-teddy_bear_school-teddy_bear_with_a_book.png`, `vid-...webm`, together in `out/G00N/slices/` | Searchable names; Phase 3B pool keys off `key` |
| Pydantic `models.py`, `ChromaSpec`, `PackManifest` | Dataclasses + dicts (`engine/config.py`, `Report`, `StickerResult`, `AnimationResult`); `mirsal/engine/models.py` left untouched and unused | "No pydantic/langgraph yet" |
| `preview.html`, `chain.html`, `out/last.json`, `python -m mirsal create` opens a page | The Lifecycle Console (`python -m mirsal serve`) is the review surface; `more [G001]` derives state from `result.json`; results carry `parent` | One live UI instead of two static pages |
| macOS python path, pinned versions, pytest | Windows/macOS/Linux, Python >= 3.10, `>=` version floors, stdlib `unittest`, ffmpeg from PATH or `imageio-ffmpeg`, no ffprobe (probing parses `ffmpeg -i`) | Restricted-network PC; see README "library policy" |
| `LOOP_SEAM_MAX` absolute | Seam limit = `max(12, 1.5 x the clip's own median frame-to-frame change)` | Real clips: normal motion between consecutive frames already scored 15-40 on the absolute scale, so a fixed 12 failed clips that loop fine |
| CRF ladder 30/38/46/54 | 30/38/46/54/60 | Real cell 3 was 264 KB at CRF 54 |
| Bicubic upscale | Linear upscale + a second edge-band despill after resize | Bicubic ringing produced green fringe pixels on thin outlines (found by the tests) |

### Status

| Checkpoint | State |
|---|---|
| 1A engine + stills + console stills | **Built, 11 tests green.** Real `teddy_bear` sheet: 8/9 READY in 0.4 s; slice 4 flagged `no_spill`. **Waiting on Haitham: 100% zoom fringe review of the slices.** |
| 1B video + console video (pre-sliced clips) | **Built and tested on synthetic clips** (2 of 9 cells in the unit test, loop close proven). **Real video not yet passing end to end:** the first real run (before the seam-ratio and CRF-60 fixes) gave 1 READY, 6 `loop_seam`, 1 `size_budget`. **Waiting on Haitham's run** (frame processing is done on his PC while the VPS network block is sorted). |
| 1C console | **Built**; see Part C. |
| 1D desktop Sticker Builder | **Built, 25 tests green, headless-browser walk-through on synthetic data; waiting on Haitham's gate** (Part D). |
| 1F golden path + review gates | **Not built. Added 2026-10-01 after Haitham's review; it is the spine of the product and the prerequisite for Phase 2.** See "Golden path" below. |

### Next steps (ordered)

**Findings from the 2026-10-01 pass** (fixed and recorded in README; kept here until Haitham approves):
- **Every earlier WEBM failure had one cause.** The Anaconda ffmpeg on PATH has no libvpx-vp9 and rejects `-deadline`, so each cell died as `exception`. Now `imageio-ffmpeg` is installed in the project venv, and cells fail fast with `no_vp9_encoder` when that happens. Result: 36/36 READY.
- **Variants 2-4 were animated with variant 1's teddies.** Their `slices/*.mov` are byte copies of vid-001's. The copies are now detected and ignored, and each variant uses its own mp4. *Haitham:* re-slice vid-002..004 or delete their `slices/` folders.
- **Gutter cuts** replace equal thirds (stills 78/90 -> 90/90). `inside_cell` now means a real crossing, not a bad cut.
- **`no_spill` misfired on subject colour**: 0 edge pixels, all interior. Interior key colour is now the `chroma_risk` warning. Follow-up: a saturated green part of a subject is keyed out completely and leaves an **enclosed transparent hole**, which `chroma_risk` cannot see. Add a `holes` metric (transparent regions enclosed by the subject's outer contour) before Phase 3's blue re-key relies on it.
- The **Anaconda base env** has a mixed numpy 1.26/2.0 install that crashes onnxruntime. Always use `mirsal/.venv`.

0. **Build checkpoint 1F (the golden path with review gates) before Phase 2.** Phase 2 persists exactly the contracts 1F defines (tags, reviews, history, video sheets); building Postgres first would mean a second schema migration for the core flow.
0. **Rotation + inputs panel:** every Generate for a subject takes the next prepared variant (001..004, wrapping), img-NNN with vid-NNN; the console lists all prepared inputs with a Use button. Results written by older versions still render (the page used to go blank on them).
0. **Done since the last review:** pre-sliced clip input (mov preferred), folder-per-variant pairing, key-failure branch (dissect -> key again -> rule out), click-to-enlarge carousel in the console. Measured: one real `.mov` cell -> READY 512x512 WEBM in ~17 s.
1. **Haitham runs the real video pack** (`python -m mirsal serve` -> "Video -> full pack", or `python -m mirsal animate G001`) and reports per-cell `anim_reason`, `kb`, `loop_seam`, `loop_limit` from `result.json`. If cells still fail `loop_seam`, the answer is more crossfade frames (`loop_fade_frames`), not a looser limit.
2. **Speed.** Now ~5 s per cell and ~50 s per 9-cell pack with ffmpeg 7.1 (imageio-ffmpeg), which meets the 60 s target; it was ~18 s per cell. Remaining levers if needed: Levers, in order: process cells in a `multiprocessing` pool (cells are independent); start the CRF ladder from an estimate instead of always at 30; `-cpu-used 5`; keying at native 320 px then upscaling is already cheap, encode dominates.
3. **Real-sheet robustness.** Gutter cuts are done (`engine/grid.py`, 2026-10-01). Original note: real AI grids are rarely exactly on thirds. Add `grid_inset`/per-sheet cell offsets (or connected-component grouping as a fallback when `inside_cell` fails for 3+ cells). Add a per-cell `spill_ok` override in `prompts.json` for legitimately green props (slice 4).
4. **Tracker -> pipeline.** `Phase_01/tracker/tracker.json` already records chosen image/video takes per subject. Let `sources.py` use `chosen_img`/`chosen_vid` when set instead of order pairing, so Haitham's picks drive variant selection.
5. **`doctor` grows per phase** (Phase 2 adds Postgres; Phase 4 Redis; Phase 3 API keys/model weights). Port checks use Python sockets, not `lsof`.
6. **H.264 vs PNG spill comparison** (1B exit item): print spill counts for the PNG and WEBM paths of the same cell.
7. **Findings to act on from the real clips:** (a) the `.mov` clips have opaque pixels on the slice border in 51/97 frames (`edge_touch_frames` is reported; check whether the slicer clips the character or the character truly fills the cell); (b) the `.webm` clips carry alpha haze (values 1-3), handled by `clip_alpha_floor`; (c) both are 320 px and 4 s, so they are upscaled to 512 and trimmed to 3 s; a 512 px re-slice would sharpen the result; (d) encode dominates the 17 s/clip: try `-cpu-used 5`, a single CRF pass, or a process pool.
8. **Keyers for non-green input:** see README "Keyers"; add a `matte` backend and make it the last rung of the key-failure ladder (Phase 3C).
9. **Labels vs. real sheet.** The prompter stub invents labels by cell position; it cannot know what a hand-made sheet contains. Manual sandbox sheets should carry their real prompts in `<sheet name>.json` (implemented, tested). Phase 3 removes the gap because the sheet is generated *from* the plan, and its VLM check (Part 2) verifies each cell against its prompt.
10. **Deferred to Phase 2/3 (decided):** ingest (raw downloads like `123123.jpg` / `higgsfield-wavespeed23844.mp4` -> `{task}-##`) and grid number in slice names. Phase 1 is a manual sandbox: `Phase_01/Images_gen` and `videos_gen` are Haitham's hand-edited watch folders. The app only reads them (filenames + decoded sheet/video), never writes or renames inside them (the empty `slices/` folders there are unused); all outputs go to `mirsal/out/`.
11. **Optional**: an offline `preview.html` writer if a static, shareable page is wanted; not needed for the demo.

---

## Golden path: the core flow with review gates (checkpoint 1F)

**Why this section exists.** On 2026-10-01 Haitham named the flow below as *the* product. Parts A–E built its pieces: keying, slicing, video slicing and the console. They did not build the spine that joins them:
- approve/reject at every stage;
- a re-composed **video sheet** built only from the approved stickers;
- a link from the returned video back to those stickers;
- a boundary gate on the video.

1F builds that spine with no database and no LLM. Later phases each take one piece of it:
- Phase 2 persists it in Postgres, makes it searchable and traces it to LangSmith;
- Phase 3 replaces the stub planner, the prepared sheet and the manual video upload with APIs, and adds the VLM as a pre-reviewer;
- Phase 4 makes LangGraph `interrupt()` wait at the same gates.

**The gate rules stay in Python in every phase.**

### The flow (example: `teddy bear`)

| # | Step | Actor | Gate | Today | 1F builds |
|---|---|---|---|---|---|
| 1 | The user types `teddy bear`. | human | | built | |
| 2 | **Plan:** one cell prompt per cell of the chosen grid (9 for 3×3, 4 for 2×2), filled into a saved template (Phase 3 Part 1: template + slot JSON). Each prompt has 1–5 **tags** describing the sliced output and an explicit **margin** clause; the sheet prompt is included too. | prompter (stub; LLM in Phase 3) | **G1 plan:** approve / reject | 1 `key` per cell; margin wording only in the sheet guideline; no gate | `tags`, per-cell margin clause, G1 |
| 3 | The sheet arrives (Phase 1: prepared; Phase 3: the image API). | source | | built | |
| 4 | Python keys, slices and validates, and blocks bad cells (for example 5 and 6) with a named reason. One pack-wide scale; each sticker is shown on its own. | engine | Python's block is final | built (`FAILED` + reason) | record each block as a `history` entry, `actor: python` |
| 5 | The human reviews the stills. | human | **G2 stills:** approve / reject per sticker, plus "Approve all READY" | no approve/reject | G2 |
| 6 | Build the **video sheet** from the approved stickers only: same slot positions, rejected slots left empty, extra margin, flat key colour, no outline. Save it with its `layout.json`. | engine (pure) | **G3 video sheet:** approve → "Send to video" | not built (it was Phase 3's `build_animation_sheet`) | `build_video_sheet()` |
| 7 | The video comes back and is attached to **that video sheet** (`A1`), not matched by filename. Phase 1: Haitham uploads the mp4 he made from the sheet. Phase 3: an API ticket. | human / API | | pairing by folder `NNN` only | upload linked to `A1` |
| 8 | ffmpeg decodes each **approved slot** using the layout's exact rectangles. Python re-keys every frame and checks **boundaries on every frame** (`inside_slot`, `cross_slot`), plus loop seam and size, and blocks failures (for example 1 and 2). | engine | Python's block is final | split into thirds; `edge_touch_frames` is a warning only | layout slicing + boundary gate |
| 9 | The human reviews the animated stickers. | human | **G4 animation:** approve / reject per sticker | none | G4 |
| 10 | The final pack shows only stickers approved at **both** G2 and G4, each with its full history. | console | **G5 pack:** approve → add to a Library pack | "Add all to pack", not gated | final view gated by G2 + G4 |

**Example outcome:**
1. G2 rejects 5 and 6.
2. Video sheet `A1` has slots 1–4 and 7–9 filled; 5 and 6 are blank key colour.
3. Python blocks 1 and 2 at step 8 with `inside_slot`.
4. G4 approves 3, 4, 7, 8 and 9.
5. The pack holds those 5 animated stickers.

The history stays readable afterwards:
- `G00N/S5` still reads "rejected at G2 by human";
- `G00N/S1` reads "blocked at video by python: inside_slot (frame 41, 6 px over)".

### Rules

- **Python's block is final.** A human can reject a READY sticker; nobody can approve a FAILED one. This is the same split as Phase 3: Python judges what is *correct*, a human (and from Phase 3 the VLM) judges what is *good*.
- **The VLM never replaces the human gate.** From Phase 3 it is a third actor that pre-reviews before G2 and G4. It replaces the human only if Haitham's config says so.
- **Rejection never deletes.** Files stay, and the sticker carries its `review` and `history`. A decision can be changed at the same gate until the next stage has started from it (for example, until `A1` is built).
- **Identity is the original cell index.** A sticker stays `S5` through every stage. The video sheet's `layout.json` maps slot → `S#`, so a 7-sticker video sheet still reports in the original numbering.
- **One outline, applied last.** The video sheet uses the keyed, scaled, despilled sticker **without** the white outline (render with `outline_px: 0`). The outline is added once, after the returned video is keyed. Otherwise the video model animates the outline and Python adds a second one; Part A says never both.
- **Logic first, not resolution (Haitham, 2026-10-01).** Production sheets are 2K from Nano Banana 2 / GPT Image 2, so pixels per subject are not the concern; the test inputs are only samples. Default: the subject's longest side is at most 55% of its slot, which leaves at least 22% margin per side. `subject_px_in_video` is recorded per slot as a metric only: no warning, no gate.
- **Grid is the user's choice: 3×3 (default) or 2×2.** The grid is part of the plan and of `layout.json`. Every stage handles `rows×cols` cells; nothing assumes 9. **Regenerating one sticker** (pick one, regen) is a **1×1** run through the same engine. It produces a new still for that `S#` only, records `regen_of: "G00N/S#"`, and the sticker then goes through G2 → video → G4 alone. Phase 2 stores it as a new generation whose other stickers are inherited from the parent, so history is never modified.
- **Cut at the gutters, not at equal fractions.** Real sheets do not put their gutters on exact thirds; measured on the 10 prepared sheets, gutters sit up to ~90 px off. `split_grid()` finds the background bands and cuts in their middle, falling back to equal division when it finds none. It moved here from Phase 3 because the 2×2 grid needs it anyway.
- **The background is exact.** The video sheet is drawn on the pure key colour (`#00FF00`, or blue when the stills were keyed on blue), with no noise or gradient. A flat background keys more reliably after video compression than the original sheet's background did.
- **Every gate decision is an event and a history entry.** Nothing is decided only in the browser.

### Contracts (plain JSON; Phase 2 persists them unchanged)

**`prompts.json`, per cell:**
- New fields `template_id`, `template_version` and `slots` (the slot JSON of Phase 3 Part 1: `subject_description`, `style_id`, `mode`, `cells[{pos, label, tags, emoji}]`, `action_guidance`, `key_colour`). The final prompts are rebuilt from the template and never stored as free text only.
- New field `tags`: 1–5 entries, each `[a-z0-9_]+`, unique within the cell. The first tag is the `key` (the file-name tail); the rest are search terms.
- The per-cell `prompt` ends with the margin clause: *"full body, centred, generous empty margin on every side (at least 20% of the cell), nothing touching or crossing the cell edge"*.
- `validate_plan` treats a missing `tags` as `[key]`, so hand-written prompts files stay valid.

```json
{"index": 1, "id": "prompt01", "key": "teddy_bear_with_a_book",
 "tags": ["teddy_bear_with_a_book", "reading", "book", "school"],
 "prompt": "teddy bear holding a book, full body, centred, generous empty margin on every side ...", "emoji": "📚"}
```

**`result.json` gains:**

```json
"reviews": {"plan": {"decision": "APPROVE", "by": "human", "ts": 0, "note": null},
            "video_sheet": {"A1": {"decision": "APPROVE", "by": "human", "ts": 0}}, "pack": null},
"video_sheets": [{"id": "A1", "slots": [1, 2, 3, 4, 7, 8, 9], "file": "video_sheet/A1/sheet.png",
                  "layout": "video_sheet/A1/layout.json", "video": "video_sheet/A1/video.mp4",
                  "status": "BUILT | APPROVED | VIDEO_RETURNED | SLICED"}],
"stickers[i]": {"tags": [], "review": {"still": "PENDING | APPROVED | REJECTED | BLOCKED", "anim": "..."},
                "history": [{"ts": 0, "stage": "sliced", "actor": "python | human", "decision": "PASS | BLOCK | APPROVE | REJECT",
                             "reason": null, "ref": "A1"}]}
```

**`layout.json`:**

```json
{"canvas": [2048, 2048], "key_rgb": [0, 255, 0], "grid": [3, 3],
 "slots": [{"slot": 1, "sticker": "S1", "rect": [0, 0, 682, 682], "subject_rect": [0, 0, 0, 0], "scale": 0.0}]}
```

`build_video_sheet(stickers_rgba, approved, cfg) -> (sheet_rgb, layout)` is **pure** and deterministic, with a golden-hash test. It lives in `engine/`, so the boundary test covers it.

**New lifecycle stages**, appended to `STAGES`; old results still render:
- `plan_reviewed`, `stills_reviewed`, `video_sheet_built`, `video_sheet_reviewed`, `video_returned`;
- the existing `video_sliced`;
- `anim_reviewed`, `pack_final`.

The event payload gains `actor` and `decision`.

**Engine changes:**
- `process_video` takes an optional `layout` (exact slot rectangles instead of thirds).
- The new checks are `inside_slot` (every frame's subject stays inside its slot, minus `edge_touch_px`), `cross_slot` (no foreground in the gutter between slots) and `subject_px_in_video` (metric plus warning).
- For pre-sliced clips, `edge_touch_frames` stays a warning: their slice rectangle is not ours.

### API (console; seeds Phase 5)

| Route | Purpose |
|---|---|
| `POST /api/generations/<id>/review {gate: plan\|still\|video_sheet\|anim\|pack, decision: APPROVE\|REJECT, index?, note?}` | Records one decision. Per-sticker gates take `index`; `index: "ready"` approves every READY sticker. |
| `POST /api/generations/<id>/video_sheet` | Builds `A<n>` from the currently approved stills. |
| `POST /api/generations/<id>/video_sheet/<A>/video` (raw body) | Attaches the returned video to that sheet, then slices its approved slots. |

- A gate out of order returns 409: for example, a video sheet before any still is approved, or an animation review before slicing.
- The existing `animate` route stays for the prepared-video sandbox path (folder pairing).

### UI (Generate screen)

- **Per tile:** Approve and Reject buttons with a state badge. The history shows in the carousel.
- **Above the grid:** the active gate, and "Approve all READY".
- **After G2:** "Build video sheet" shows the sheet with slot numbers overlaid, then "Approve & download" and "Upload returned video".
- **After slicing:** Approve and Reject per tile for the animation.
- **A "Final" tab** shows the pack (approved at G2 and G4) with "Add to pack".

### Checkpoint 1F — exit

- [ ] A synthetic end-to-end test reproduces the example exactly:
  - G2 rejects 5 and 6, and the video sheet has 7 filled slots with 5 and 6 blank;
  - in a synthetic returned video, slots 1 and 2 drift over their slot edge, so 1 and 2 get an `inside_slot` BLOCK;
  - G4 approves the rest, and the final pack is 3, 4, 7, 8, 9;
  - every sticker's `history` tells its path.
- [ ] `build_video_sheet` passes a golden-hash test. Blank slots are pure key colour, the sheet has no white outline, and the final WEBMs have the outline exactly once (alpha-ring test).
- [ ] Prompter: every cell has 1–5 tags, the first one is the key, and the prompt contains the margin clause. Old prompts files without `tags` still load.
- [ ] Gate order is enforced (409s). FAILED stickers cannot be approved. A decision can be changed until the next stage starts.
- [ ] Console: every gate can be driven from the page (headless walk-through), with no dead buttons.
- [ ] `subject_px_in_video` is recorded per slot (metric only).
- [ ] A 2×2 synthetic sheet and a 1×1 single-sticker regen go through every gate; a sheet with off-third gutters is cut at the gutters (no `inside_cell` from the cut).
- [ ] Prompter: `prompts.json` holds `{template_id, template_version, slots}` and the final prompt is rebuilt from the template file (`mirsal/prompts/templates/sheet_3x3_v1.txt`, `sheet_2x2_v1.txt`, `single_1x1_v1.txt`). The stub fills the slots deterministically; Phase 3 swaps only the filler.
- [ ] **Haitham** runs it on a real teddy sheet:
  1. approve some stickers and reject some;
  2. build the video sheet;
  3. make the video from it in his own tool;
  4. upload it, review the animations, and get the final pack.

---

## What Haitham sees at the end

```
python -m mirsal create "banana with big eyes"
```

This opens `out/G001/preview.html`, a 3×3 grid on a checkerboard (so transparency is obvious):
- each sticker's name and emoji underneath;
- a **Before/After** toggle that shows the raw cell next to the clean sticker, so the Python's work is visible;
- a **background toggle**: light chat, dark chat, and a busy wallpaper. A white outline vanishes on light and pops on dark, so check all three;
- in 1B, each tile loops its WEBM animation.

The file is self-contained HTML: no server, no build step.

For the live version, `python -m mirsal serve` opens the **Lifecycle Console** at `http://127.0.0.1:8770` (see Part C). It is the supervisor demo for this phase; `preview.html` stays as the offline fallback.

---

## Where things live

```
proposals/Mirsal-Builder/mirsal/
  sets/                               # Haitham's prepared inputs
    banana/
      set.json                        # {"name": "Banana", "keywords": ["banana"]}
      01/ sheet.png  manifest.json  video.mp4
      02/ sheet.png  manifest.json    # video optional per variant
    puppy/ ...
  mirsal/
    engine/                           # PURE: numpy / OpenCV / Pillow / ffmpeg subprocess only
      models.py                       # contracts (already exists — see "Contract changes")
      chroma.py  normalize.py  outline.py  sheet.py  video.py  validate.py
    sources/
      base.py                         # StickerSource interface
      fixture.py                      # FixtureSource: prompt → set/variant → paths + manifest
    preview.py                        # writes preview.html
    cli.py  __main__.py               # create / more (alias: another) / animate / serve
    console/                          # Part C: server.py (stdlib http.server) + index.html (vanilla JS)
  scripts/make_test_sheet.py          # synthetic fixtures
  tests/
  out/                                # results (gitignored)
```

| Builder asks | Answer |
|---|---|
| Where are the sheets? | `sets/<subject>/NN/sheet.png`: a 3×3 grid on a green background. |
| Where are the videos? | `sets/<subject>/NN/video.mp4`. Video NN animates sheet NN, in the same cell order. |
| Where are the prompts that made them? | `sets/<subject>/NN/manifest.json`: `sheet_prompt`, `video_prompt`, and `stickers[i].prompt` per cell. |
| Where are the sticker names? | Same manifest: `stickers[i].name` + `emoji` + `concept`. |
| Cell order? | Row-major: `1 2 3 / 4 5 6 / 7 8 9`, starting top-left. |

Until Haitham's real sets arrive, build against synthetic sets from `scripts/make_test_sheet.py`, which use the same layout.

---

## Contract changes (make these first in `engine/models.py`)

1. `ChromaSpec.threshold: int | None = None`. `None` means auto-calibrate from the sheet (step 3 below); a number is a manual override.
2. `PackManifest.tags: list[str] = []` holds variant words such as `["big eyes"]` (see Matching).
3. Add `outline_px: int = 12` to `EngineConfig` (0 turns the outline off), and an optional `outline_px: int | None` to `PackManifest` that overrides it per set.
4. **`generation_id` is allocated per run** (the next free `G###` under `out/`), not read from the manifest. Keep `PackInfo.generation_id` only as the runtime slot.

---

## Flow (fully deterministic)

```
prompt → FixtureSource.find(prompt) → (sheet.png, manifest, video.mp4?) → engine.process_sheet() → out/G00N/ → preview.html
```

**Matching:**
- Lowercase the prompt. The first set with a keyword present as a whole word wins.
- Within that set, pick the variant whose `tags` appear in the prompt; otherwise use variant `01`. So "banana with big eyes" can land on the big-eyes sheet.
- No match shows `No prepared set for that. Try: banana, puppy`.

**Commands:**
- `create "<prompt>"`: a new generation.
- `more` (alias `another`): the same set, the **next prepared variant**, as a new generation.
  - Variants are served in folder order `01, 02, 03…`, starting after whichever variant `create` picked.
  - After the last one, the reply is `That's all N prepared variations of <set>.` It does **not** wrap back, because a repeated sheet looks broken in a demo.
  - `create` starts a fresh chain.
- `animate [G00N]`: runs Part B on the latest generation, or on the one named. It uses **that variant's own** `video.mp4`. If a variant has no video, the reply is `No animation prepared for this variation.`

The CLI keeps a tiny `out/last.json`: the current set, the variants already served, and the chain of generation ids since the last `create`.

**Chain preview:** besides each generation's own `preview.html`, the CLI rewrites `out/chain.html` on every `create`, `more` and `animate`.
- The newest 3×3 grid is on top and earlier ones below, each labelled `G00N · variant NN`, with its names and emoji.
- Animated generations show looping WEBMs.
- "Generate more" feels like the page grows. This page is the one Haitham shows.

**Swap point:** `StickerSource` has one method, `find(prompt) -> SourceResult(sheet_path, manifest, video_path | None)`. Phase 3 adds `ModelSource` behind this same interface, and nothing downstream changes.

---

## Part A — static engine (checkpoint 1A)

`process_sheet(sheet: np.ndarray, manifest: PackManifest, cfg: EngineConfig) -> list[StickerResult]` is **pure**: no file paths, no web, no database. Per cell:

1. **Split** into `w//3 × h//3` cells. No computer-vision grid detection yet (Phase 3 may add it if needed).
2. **Sample the real background** from the cell's outer border ring (the median of the outer ~4 px). AI tools almost never give a true `#00FF00`; calibrate to what is actually there.
3. **Key** with a colour-difference key: `d = K − max(other two)`, where K is G for green chroma or B for blue.
   - `d ≥ t` is transparent; `d ≤ t/2` is opaque; the alpha is linear between.
   - `t` is the manual threshold if set, otherwise `0.5 × median d of the border ring`.
4. **Remove specks:** drop connected components under `min_component_px` (~64). **No erosion**: it eats thin outlines, lashes and highlights.
5. **Despill the edge band only** (~3 px around transparency) by clamping K to `max(other two)`. Global despill turns yellow orange, and banana is yellow. That makes banana the right first test.
6. **Trim** to the subject's bounding box and **scale with one pack-wide scale.** Fitting each sticker on its own makes the character's size jump: a lying-down "sleeping" pose gets blown up next to a standing one. Instead:
   - compute every sticker's fit scale (longest side = 0.775 × 512);
   - use the **median** of the 9 for all of them;
   - clamp per sticker so nothing exceeds 0.85 × 512.

   Record `scale_mode` (`pack` or `clamped`) in the metrics. Centre on a 512×512 transparent canvas and never stretch.
   - **Premultiply → resize → un-premultiply.** Without this, the green left under transparent pixels bleeds back in as a fringe.
7. **White outline:** dilate the alpha by `outline_px`, fill it white, and composite it under the subject. This gives the sticker look and hides small keying flaws. If a prepared sheet already has white die-cut outlines drawn in, set `outline_px: 0` for that set in its manifest. Never apply both outlines.
8. **Validate** (each check is named in a `Report`):
   - `dimensions`: 512×512 RGBA.
   - `transparent_corners`.
   - `foreground`: at least `min_foreground_px`.
   - `inside_cell`: the subject did not touch its cell border, which would mean it was cut off or crossed into a neighbour.
   - `no_spill`: about 0 opaque pixels with `d` above `t`.
   - `static_file`: decodes and is ≤512 KB. If a detailed PNG is over the limit, re-save it as **lossless WEBP**, which Telegram also accepts, and record the format.

   A failure is a `StickerResult(status=FAILED, reason=...)`. **Never raise.** The other 8 still show.

The CLI writes the stickers to **`out/G00N/slices/img-NNN-<task_slug>-<key>.png`**, plus `out/G00N/source/sheet.png` (a copy), `out/G00N/result.json`, `out/G00N/events.jsonl` (see Part C) and `preview.html`.

**`result.json` is the contract Phase 2 persists.** It holds the generation id, the prompt, set/variant, the manifest, and per sticker the `index, name, concept, prompt, emoji, status, reason, report, metrics` plus relative file paths.

### Checkpoint 1A — exit
- [x] The synthetic sheet generator is deterministic. Its background is noisy and gradient green, not flat, and its cells cover:
  - a yellow shape;
  - a 2 px thin outline;
  - a soft drop shadow;
  - a small detached detail (a sweat drop), which must survive;
  - a blank cell, which must fail as `empty_subject`;
  - a border-touching shape, which must fail as `inside_cell`.
- [x] A blue-chroma synthetic variant keeps a green subject intact.
- [x] **Pack-consistent scale:** a synthetic sheet with one tall and one wide pose renders the same shape at the same size in both cells (within 2%).
- [x] **WEBP fallback:** a deliberately detailed sticker over 512 KB comes out as a valid lossless WEBP under 512 KB.
- [x] Golden test: the same input gives the same PNG pixel hash across two runs.
- [x] Boundary test: importing `mirsal.engine` in a fresh subprocess does **not** load `fastapi`, `psycopg`, `langgraph` or `anthropic`.
- [x] `create "banana with big eyes"` opens the preview in under ~2 s. Measure and print the timing.
- [ ] Every real prepared sheet passes the validators, and **Haitham** eyeballs the preview at 100% zoom: no green fringe. *(8/9 READY; slice 4 `no_spill`; awaiting Haitham's eyeball)*
- [x] **Console, stills (stages 1–4):** `python -m mirsal serve`; typing a prompt walks the stepper through `requested → sheet_picked → keyed → sliced`, and the 9 slices appear in `out/G00N/slices/`. The console tests for POST/poll, event order and path traversal pass.
- [x] **More chain:** with 3 synthetic variants, `create` → `more` → `more` gives G001–G003 from variants 01–03, all on `chain.html` (newest first). A 4th `more` replies "That's all 3 prepared variations" and creates nothing. *(tested with 2 variants through the console; `chain.html` replaced by the console list)*

---

## Part B — animation (checkpoint 1B)

`process_video(mp4: Path, manifest, cfg, workdir: Path, cells: list[int] | None = None) -> list[AnimationResult]`, using **the same `chroma.py`** as Part A. `cells=None` means all 9; `[i]` processes only that cell (the decode is already per cell, so this is cheap).

1. `ffprobe` the file: width, height, fps, duration, codec.
2. **Decode one cell at a time** with `ffmpeg -vf crop=w:h:x:y` straight to raw RGB. A 2K grid × 90 frames in one array is about 1 GB; per cell it is about 125 MB.
3. Keep the native fps if it is ≤30; reduce it only if it is above. Never duplicate frames upward. Cap the frames at `floor(3.0 × fps)`.
4. Key every frame with the Part A keyer. Sample the background once per cell from the first frame's border ring.
5. **Normalize with one transform per clip:** take the union bounding box across all frames, then apply one scale and offset to every frame. Per-frame fitting makes the subject jitter and pump in size.
6. Add the same white outline per frame. Then **close the loop**: Telegram plays video stickers on repeat, so a clip that doesn't end where it starts visibly jumps every cycle.
   - Measure `loop_seam`, the alpha-weighted mean absolute difference between the last and first frames.
   - If it is above `LOOP_SEAM_MAX`, crossfade the last ~6 frames (0.2 s) into the first ones, and re-measure.
   - Record the before and after values in the metrics.
7. Encode with `ffmpeg -f rawvideo -pix_fmt rgba … -c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 -b:v 0 -crf N -an`. libvpx doesn't support alt-ref frames with alpha. The CRF ladder is `[30, 38, 46, 54]`: stop at the first result ≤256 KB, and after 4 attempts fail with `size_budget`.
8. **Validate:**
   - codec vp9, 512×512, fps ≤30, duration ≤3.0 s, ≤256 KB, no audio;
   - the `ALPHA_MODE=1` tag;
   - then **decode with `-c:v libvpx-vp9`** and confirm the alpha plane has both transparent and opaque pixels. ffprobe's default vp9 decoder hides alpha, so a probe-only check passes files with no real alpha.

`animate` writes `out/G00N/slices/vid-NNN-<task_slug>-<key>.webm` (same name tail as the PNG, same folder, so each slice has a still and an animation side by side), updates `result.json` (`animation_status`, `animation_reason` per sticker) and rewrites `preview.html` with looping `<video>` tiles. The preview needs Chrome or Firefox; Safari's WEBM alpha support isn't reliable.

**An animation failure never marks the sticker's PNG as failed.**

### Checkpoint 1B — exit
- [ ] A synthetic 3 s 30 fps grid MP4 (shapes bouncing on noisy green) gives 9 WEBMs that pass every check. *(unit test covers cells 1 and 9 only; extend to all 9)*
- [x] A real prepared video: each cell passes, or fails with a named reason. No crashes. *(2026-10-01: 36/36 READY over 4 teddy variants; Haitham still judges the look)*
- [ ] H.264's colour subsampling smears green at edges, so compare spill counts between the PNG and WEBM paths. Widen the video despill band only if the numbers say so. *(not done; Next steps 6)*
- [x] The whole 9-cell run finishes in a measured time (target under 60 s). *(2026-10-01: 43-56 s per pack on the 4 real teddy packs)*
- [x] **Loops:** a synthetic clip whose end differs from its start gets crossfaded, and its `loop_seam` after the fix is below `LOOP_SEAM_MAX`. Every output WEBM reports its seam value.
- [x] **Console, video (stages 5–7):** **Generate video → this slice** creates exactly one WEBM in `slices/` next to its PNG, and the tile starts looping. **→ full pack** fills the remaining eight. A variant without a video returns the clear message. *(single-slice path tested on synthetic; pack path awaits the real-video run)*
- [x] `animate G002` animates variant 02 with **its own** video. A variant without `video.mp4` gets the clear message, and nothing fails. *(covered by the console test)*

---

## Part C — Lifecycle Console (minimal local UI)

**Purpose:** a real frontend that shows the fake-but-deterministic generation lifecycle. Nothing in the UI is mocked: every stage it shows is a real engine step whose output exists on disk. "Fake" means only that the *picking* steps (sheet, video) are lookups over Haitham's prepared files instead of a model call.

**Limits:**
- `mirsal/console/`: stdlib `http.server` plus one `index.html`, vanilla JS. No framework, no build step, no database. Binds to `127.0.0.1` only.
- Dependency direction: the console imports the engine and `sources`; never the reverse. The boundary test from 1A still holds.
- The JSON API below is the seed of Phase 5's API. Do not add anything beyond it.

### Lifecycle

Each generation `G00N` is a small state machine. Every transition appends a line to `out/G00N/events.jsonl` (`{ts, stage, status, ms, detail}`) and updates `result.json`.

| # | Stage | What happens | What the UI shows |
|---|---|---|---|
| 1 | `requested` | The user types a prompt, or presses **More**. | The new entry appears in the list at once. |
| 2 | `sheet_picked` | `FixtureSource` matches a set and variant (a lookup). | Set, variant and tags, plus the raw sheet with the 3×3 grid overlaid. |
| 3 | `keyed` | The background is sampled and the threshold auto-calibrated (Part A steps 2–5). | Sampled background RGB, threshold `t`, and the keyed sheet on the checkerboard. |
| 4 | `sliced` | Split, one pack-wide scale, outline, validate (Part A steps 1, 6–8). | Per cell: the raw cell with its bounding box, then the 512×512 slice. Slices land in `out/G00N/slices/img-NNN-<task_slug>-<key>.png`. Failed cells show their named reason. |
| 5 | `video_requested` | The user clicks **Generate video** on one slice, or on the full pack. Offered only if the variant has a `video.mp4`. | A scope chip: `slice S4` or `pack`. |
| 6 | `video_picked` | The variant's own `video.mp4` is picked (a lookup: "generated from the frame sheet"). | ffprobe info: size, fps, duration, codec. |
| 7 | `video_sliced` | The **same settings** as stage 3–4 (same `ChromaSpec`, same threshold rule, same outline), then per-clip normalise, loop close and VP9 encode (Part B). WEBMs land in the same `slices/` folder as `vid-NNN-<task_slug>-<key>.webm`. | Each slice tile upgrades from a still to a looping video, with `loop_seam`, size, CRF and status. |

**Scope rules:**
- `slice` scope calls `process_video(..., cells=[i])`.
- `pack` scope calls it with all 9 cells and skips cells that already have a WEBM.
- Clicking the same slice twice does nothing, and the UI says so.
- An animation failure never marks the still as failed (as in Part B).

**Determinism:** the same input gives the same outputs and the same event order (timestamps aside). `--pace SECONDS` (default 0) inserts a fixed sleep between stages so the stepper is watchable in a live demo. It never changes any output.

### UI (single page)

- **Left column:** the prompt box, a **More** button, and the generation list (newest first, each showing its stage badge).
- **Main pane:**
  - a stepper of the seven stages with per-stage timing;
  - a before/after panel for the selected stage, with the light / dark / wallpaper / checker background toggle from Part A;
  - the 3×3 slice grid;
  - clicking a slice opens its detail: metrics, the named `Report` checks, and the PNG and WEBM.
- **Buttons:** **▶ Animate this** and **▶ Animate all 9**. A click starts an instant in-browser live preview of the paired 3x3 video (canvas keying, same framing as the stills) while the real WEBM encodes in the background and replaces it when READY. A banner warns when ffmpeg lacks VP9.
- Every control calls a real endpoint, so there are no dead stubs.

### API

| Route | Purpose |
|---|---|
| `GET /` | The page. |
| `GET /out/<path>` | Static files from `out/` only; path traversal is rejected with 400. |
| `GET /src/<id>/video` , `/src/<id>/clip/<n>` | Read-only, Range-capable view of the paired watch-folder video for the live preview. |
| `GET /api/generations` | The list, newest first, plus `health` (ffmpeg path, `vp9` bool). |
| `GET /api/generations/<id>` | `result.json` plus the events. |
| `POST /api/generations` `{prompt}` | Starts a new generation. |
| `POST /api/generations/<id>/more` | The next prepared variant, as a new generation. |
| `POST /api/generations/<id>/animate` `{scope: "pack"\|"slice", index?}` | Starts stages 5–7. |

- Long stages run on one background worker thread, and the UI polls `GET /api/generations/<id>` every 500 ms.
- Only one job runs at a time. A second request returns `409 busy`.
- A variant with no video returns `409` with the message `No animation prepared for this variation.`

### Console tests

Run through `http.client` against an ephemeral port, using synthetic sets:
- `POST` → poll → all 9 slices exist on disk;
- `animate slice` produces exactly one WEBM, and repeating it is a no-op;
- `animate pack` fills the remaining eight;
- a variant without video returns the 409 message;
- path traversal is blocked;
- the event order is identical across two runs.

---

### Next for the live preview (kept until Haitham approves)

- Add the 12 px white outline and loop closing to the canvas preview so it matches the final WEBM.
- Play the pre-sliced `.webm` clips per tile when there is no mp4 (fallback exists, untested on real clips).
- Decide on a `ref/` hand-off: `ref/mirsal_sticker_builder_architecture_design.md` is the in-app Sticker Builder UI/architecture spec (photo -> cutout -> editor -> pack -> chat); Phase 1's engine is its "export layer" and cutout backend. Not yet mapped to a phase.

## Part D — Desktop Sticker Builder (checkpoint 1D)

**Status:** built and verified on synthetic fixtures (25 unit tests + headless-Chromium walk-through, restyled against `ref/Mirsal-Builder.jpg` panel by panel: layout, colours, spacing and Inter type match; the mockup's illustrated sticker art, Windows title bar and chat list do not exist in the app). **Waiting for Haitham's review gate** (see "Gate" below). Architecture of what exists: `README.md`, "Desktop Sticker Builder".

**Goal:** turn the Lifecycle Console into the desktop app shell in `ref/Mirsal-Builder.jpg` and `ref/mirsal_sticker_builder_architecture_design.md`, so the same window covers Generate, Library, Create/Edit, Pack manager and Save. **Desktop only.** Phase 5C makes the same model expandable to mobile (the spec's MOBILE_01-07 screens); nothing here is thrown away for that: the project model, library API and export layer are UI-independent.

**Scope mapping (spec screen -> Part D):**

| Spec | Part D | State |
|---|---|---|
| DESKTOP_01 Library | Library: search, Recent / My Stickers, pack rows, `+ Create` | built |
| DESKTOP_02 Import | Create: drop zone, Photo/Files, Text sticker, recent stickers to re-edit | built (photo, still GIF frame); video import not built |
| DESKTOP_03 Editor | 3 panels, layers, inspector, zoom, preview backgrounds, undo/redo | built (see tools below) |
| DESKTOP_04 Animated editor | built: thumbnail timeline with trim handles, playhead and frame step, loop, frame rate, export WebM / WebP / GIF, save trimmed clip back to the pack | built (no per-frame editing, reorder or add-frame) |
| DESKTOP_05 Pack manager | drag reorder, cover, rename, preview, delete, export | built |
| DESKTOP_06 Export/Send | Save to Mirsal, Download PNG; `.wastickers` export from the pack | built; Send to Chat and direct WhatsApp import intentionally absent (need the Mirsal chat / a host app) |

Editor tools that exist (rule 6, no dead stubs): Sticker (move/scale/rotate handles), Text (fonts, outline, RTL detection), Emoji, Border (+ shadow), Adjust (brightness/contrast/saturation), Erase, Restore, auto cutout (chroma key or GrabCut), layers (visibility, lock, order, duplicate, delete), zoom 50-200 %, undo/redo (60 steps). **Crop and Draw are not built** and are not shown.

### Next steps for Part D (kept until Haitham approves the gate)

1. **Animated editor, part 2 (video/GIF import is done, see Part E):** per-frame edit (delete/reorder/duplicate frames, the mockup's "Add Frame"), speed/ping-pong, and video/GIF import (frame extraction via ffmpeg, per-frame matte from Phase 3C). Today the timeline trims and resamples only.
2. **Crop + Draw tools** and a real **project persistence** layer (`StickerProject` with layers, autosave, "My Projects"). Today a session lives in the page; only the rendered sticker is saved. Save the project JSON beside the sticker (`library/projects/<id>.json`) so re-editing keeps layers, not just pixels.
3. **Matte backend (Phase 3C; the ONNX U2-Net/IS-Net provider is done, see Part E):** next is BiRefNet; earlier note: swap GrabCut for rembg/BiRefNet behind `library.cutout()`; GrabCut fails on busy backgrounds (hair, similar colours). Add click-to-refine (SAM 2) on the Erase/Restore tools.
4. **Live preview polish:** outline and loop closing on the canvas preview so it matches the WEBM; per-tile play of pre-sliced webm clips when there is no mp4.
5. **Emoji tags:** Telegram wants at least one emoji per sticker; the UI asks for one but only edits one. Support several tags per sticker.
6. **Mirsal integration:** "Send to Chat" and "Save to Mirsal" writing into the real app (needs the Mirsal chat API; Phase 5A). Official WhatsApp import needs a host app (Android intent), not a file.
7. **Design pass against the mockup, remaining:** real chat-list column, Public Packs tab and Windows title bar (need the Mirsal shell and Phase 5A), Draw tool and the mockup's Background layer, Arabic/RTL UI mirroring, keyboard shortcut sheet, drag-to-import onto the canvas. The Packs column sits where the chat list is; swap it when the Mirsal shell hosts this.
8. **Open decisions for Haitham:** whether Library should also list the raw generations (G001...) that were never added to a pack; whether packs should be limited to WhatsApp's 30-sticker cap in the UI (today export takes the first 30).

### Gate for Part D (Haitham)

Try: Create -> drop a real photo -> Auto cutout -> add text/emoji -> Border -> Save to a new pack; Generate -> `Add all to pack`; Pack -> drag to reorder -> Export `.wastickers`. Report: cutout quality on your photos, anything that feels wrong versus `ref/Mirsal-Builder.jpg`, and which next step comes first.

---

## Part E — Video / GIF creation (checkpoint 1E)

**Status:** built and verified on synthetic clips (mp4 with a green screen, mp4 with a noisy background, GIF), 6 project unit tests + a console API test + headless-Chromium walk-throughs (import, text with timing, emoji, drag, key, GIF export, save to pack, undo, project list). **Waiting for Haitham's review gate.** Architecture: `README.md`, "Video / GIF projects".

**Goal:** implement section 21 of `ref/mirsal_sticker_builder_architecture.md` (the "Version 2" video/GIF extension) on the desktop: photo path unchanged, video/GIF path = import -> Prepare (preview, trim) -> optional GIF conversion -> optional background removal -> animated composition (text, emoji, sticker layers with timing) -> Save to pack / export. Desktop only; the mobile expansion (MOBILE_08, the scrollable control area under a fixed preview and timeline) is Phase 5C.

**Plan followed (in this order, each step testable alone):**
1. **Project model + storage** (`video_project.py`): one `StickerProject` for static and animated (no separate video project), source kept untouched, autosave with server-side clamping, layers carry `timing`, heavy media referenced not copied. Tests: import mp4/GIF/garbage, clamps, list/delete.
2. **Preview frames** via ffmpeg (any container, rotation applied, alpha kept as PNG) so the browser needs no codec support and GIFs behave like video.
3. **Render pipeline:** decode trimmed range at fps -> fit/fill -> optional key -> composite layer PNGs by timing -> shared encoders (`library.encode_frames`, extracted from `anim_export` so trimming and projects share the size ladders). Tests: per-frame timing (layer visible on exactly the right frames), letterbox alpha, fill has no alpha, key removes the screen and keeps the subject, sticker 3 s cap vs GIF 10 s, source untouched after failure.
4. **Capability-gated background removal** behind providers (chroma, AI matte, none) with the five states from the spec and a recovery path that never touches the project.
5. **Prepare UI:** tools left (Trim, GIF, Background, Text, Emoji, Sticker) with a layer list, canvas centre with move/scale handles, contextual properties right, timeline bottom with trim handles, playhead and a bar for the selected layer's visible range; undo/redo; autosave indicator; export panel. No route per tool: all contextual panels.
6. **Entry points and glue:** Create accepts video/GIF, My video projects strip, "Add text / effects..." from the animated editor, Send to chat works on the saved sticker.
7. **AI cutout (also fixes photos):** `matte.py` (U2-Net / IS-Net via onnxruntime), used by `library.cutout` and the video provider; Create has an Auto / AI matte / GrabCut selector; `doctor` reports it. GrabCut assumed the subject fills the frame, which is why photo cutouts looked like a fixed blob.

**Decisions taken (change on request):** GIF conversion is an output mode of the same project (GIF has loop + colours options), not a separate screen; packs accept WebM only (the same limit as the animated editor, because the library re-decodes stored animations); text is baked in the browser and composited on the server, so RTL/Arabic shaping is the browser's; stickers are clipped to 3 s (the existing WebM/WebP limits), GIFs to 10 s; video matte uses the small model for speed (~0.3 s/frame on CPU) and light temporal smoothing.

### Next steps for Part E (kept until Haitham approves the gate)

1. **Draw layer and Crop** (spec 21.9 lists them; the tool architecture already takes new tools without new routes).
2. **Layer motion:** keyframes (position/scale/opacity over time) instead of one transform per layer; text animations (pop, fade, slide).
3. **Per-frame editing** for the animated editor and projects (delete/duplicate/reorder frames, speed, ping-pong).
4. **Border / shadow on keyed video** (dilate the per-frame alpha, same outline code as the static editor).
5. **Better video matte (Phase 3C):** BiRefNet or SAM 2 video propagation behind the same `matte`/provider seam; temporal matting instead of smoothing.
6. **Autosaved projects for photos too** (today only the rendered static sticker is saved; the layer stack is not), then "My Projects" lists both.
7. **Mobile (Phase 5C):** MOBILE_08 with the scrollable control area (preview and timeline pinned, controls scroll beneath, progressive disclosure per spec 21.13).

### Gate for Part E (Haitham)

Try: Create -> drop a short mp4 -> Trim -> Text (type, move, set "visible from/to" with the bar under the timeline) -> Emoji -> Background (green screen clip, then a normal clip with the AI matte) -> GIF -> Download; then Save to pack (needs libvpx-vp9: `python -m mirsal doctor`) and Send to chat. Also drop a photo with a busy background and compare Auto vs GrabCut. Report: cutout quality on your photos and clips, anything in the Prepare layout that feels wrong versus section 21, and which next step comes first.

---

## What Haitham prepares

- [ ] As many sheets per subject as you have (`01`, `02`, … `NN`); each one is one "generate more":
  - square, ≥1536 px;
  - prompt the tool for a "flat pure green background, no shadows, no floor, wide gaps between the 9 characters";
  - no character touches its cell edge.
- [ ] Videos: generate **image-to-video with the sheet as the start frame**, which keeps the cells aligned with the sheet. Prompt for "each character moves in place, no interaction between cells, static camera". Keep them ≥3 s.
- [ ] One `manifest.json` per variant: `pack.name`, `sheet_prompt`, `video_prompt`, optional `tags`, and 9 × `{index, name, concept, prompt, emoji}`.
- [ ] One `set.json` per subject: `name` and `keywords`.

---

## Builder rules
- Build only this phase. If something belongs to Phase 2+, write it down; don't build it.
- **Don't open image or video files to judge quality** (the builder never views media; tests use synthetic fixtures and printed metrics). Use the validators and printed metrics; Haitham judges the look from `preview.html`.
- Python >= 3.10 on Windows/macOS/Linux (`pathlib` only, no shell-specific commands). Dependencies: see README "library policy": the network is restricted, so stdlib first, minimal wheels, `doctor` for checks.
- Version floors are in `mirsal/requirements.txt`; ffmpeg needs `libvpx-vp9`.

## Hands to Phase 2
- The sticker library (`library.py`, `out/library/library.json`, saved-sticker naming, `.wastickers` export) and the desktop shell in `mirsal/console/`.
- A pure engine with a stable `StickerResult` / `AnimationResult` contract.
- `result.json` per generation, including 1F's `tags`, `reviews`, per-sticker `review` and `history`, and `video_sheets`.
- A file layout under `out/G00N/` (`slices/`, `source/`, `video_sheet/A<n>/{sheet.png,layout.json,video.*}`, `result.json`, `events.jsonl`).
- The five gates (G1 plan, G2 stills, G3 video sheet, G4 animation, G5 pack) and their rules, enforced in Python.
- The console's JSON API shape, which Phase 5 grows into the real API.
- The `StickerSource` interface.
