# Decisions that shaped the build (as planned vs as built)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

| Was planned | As built | Why |
|---|---|---|
| Inputs in `mirsal/sets/<subject>/NN/{sheet.png,manifest.json,video.mp4}` + `set.json` (and, later in the build, image/video pairing by take number) | Inputs read in place from `inputs/Images_gen/img-NNN-<subject>/` and `Phase_01/videos_gen/vid-NNN-<subject>/`: **one folder per variant, image and video paired by the same folder number NNN**. Pre-sliced clips in `vid-NNN/slices/{quicktime,webm}/<name> (n).<ext>` (n = grid cell) replace slicing the 3x3 mp4 (`.mov` preferred). Names in the watch folders are final and never renamed by the app; a positional guess (`pairing: order`, flagged by `doctor`) exists only as a last resort. `flow/sources.py` (`PhaseDirSource`) replaces `FixtureSource`/`StickerSource` | Matches how Haitham actually generates; no copying, no hand-written JSON |
| `manifest.json` per variant (names, emoji, prompts) | The **prompter stub** (`generation/prompter.py`) expands the task into `prompts.json`: 9 x `{index, id, prompt, key, emoji}` + `sheet_prompt`, `video_prompt`, modular `guidelines`. Plain JSON, no pydantic/LLM | Each sticker gets its own name from the prompter output; same shape a Phase 2 planner must return |
| `S1.png`..`S9.png` | `<media>-<NNN>-<task_slug>-<key>.<ext>`, e.g. `img-001-teddy_bear_school-teddy_bear_with_a_book.png`, `vid-...webm`, together in `out/G00N/slices/` | Searchable names; Phase 3B pool keys off `key` |
| Pydantic `models.py`, `ChromaSpec`, `PackManifest` | Dataclasses + dicts (`engine/config.py`, `Report`, `StickerResult`, `AnimationResult`); `mirsal/engine/models.py` left untouched and unused | "No pydantic/langgraph yet" |
| `preview.html`, `chain.html`, `out/last.json`, `python -m mirsal create` opens a page | The Lifecycle Console (`python -m mirsal serve`) is the review surface; `more [G001]` derives state from `result.json`; results carry `parent` | One live UI instead of two static pages |
| macOS python path, pinned versions, pytest | Windows/macOS/Linux, Python >= 3.10, `>=` version floors, stdlib `unittest`, ffmpeg from PATH or `imageio-ffmpeg`, no ffprobe (probing parses `ffmpeg -i`) | Restricted-network PC; see README "library policy" |
| `LOOP_SEAM_MAX` absolute | Seam limit = `max(12, 1.0 x the clip's own median frame-to-frame change)` | Real clips: normal motion between consecutive frames already scored 15-40 on the absolute scale, so a fixed 12 failed clips that loop fine; 1.5 x (until 2026-10-12) passed wraps that snap visibly on lively clips (G146: 🤣 jumped 66.8 on a limit of 75.2), so a wrap may now be no bigger than one ordinary step |
| CRF ladder 30/38/46/54 | 30/38/46/54/60 | Real cell 3 was 264 KB at CRF 54 |
| Bicubic upscale | Linear upscale + a second edge-band despill after resize | Bicubic ringing produced green fringe pixels on thin outlines (found by the tests) |
