# Video quality, the gap, Loop and the edge (measured on G002, 2026-10-01)

<sub>Part of [generation.md](../generation.md).</sub>

- **Pixels.** The first Kling clip was `std`: 960x960 for the whole sheet, 320 px per slot, the sticker filled 55% of its slot, so about 176 px of picture were scaled 2x to 512:
  that is the pixelation. Kling is now always `pro` (1440 px, 480 px per slot; `std` is not offered) and both Groks always 1080p. A 2x2 sheet would give each sticker 2.25x the pixels of a 3x3
  one (open question).
- **The gap is the user's to slide.** The server fills each slot to `slot_fill` (0.74, so the free space per slot went 45% -> 34% -> 26%) and the animation box shows a **Gap** slider
  (8-50%) with a small preview of the exact sheet that would be sent (`GET /api/generations/<id>/sheet_preview?fill=`, built on the fly, never stored). `POST /api/live/video {slot_fill}` builds the
  sheet at that fill; if the user moved the slider after a sheet was built, the old sheet is **rejected (never deleted)** and a new one is built. The fill is stored on the sheet (`slot_fill`).
  A fuller slot leaves less room for expressive motion, so more cells can fail the out-of-bounds checks (those are warnings the user can include anyway).
- **Loop is a choice, off by default** (like the stroke): the saved plan has `slots.loop`, the composer has a Loop chip, the animation box a Loop checkbox. Off: `video_v2` contains no loop
  wording at all and the Kling job gets only a start image; on: "seamless loop", "End on the starting pose so the clip loops" and start = end image. The engine closes loops itself
  (`close_loop` eases the last frames of a clip whose end does not match its start into frame 0, so the clip starts on its own first pose and the thumbnail is never a dissolve; it used to start on the tail's pose and cross-fade into the head, which showed as a ghost on the first frames), so the model never needs the word. `loop_seam` stays a technical block.
- **The edge is a preview until it is applied, and it never loses a video.** Stroke and trim are sliders in the edge bar (and in the open thumbnail's view). Dragging one changes **one
  thumbnail only**: the open one, else the last one picked, else the first. Outside the open view that is a **floating card** under the sliders (the test sticker, large, on the checkerboard,
  with **Apply** and **Cancel**); in the open view the big sticker pane is the preview. The grid is never touched, nothing is stored and nothing is re-rendered while a slider moves
  (`GET /api/generations/<id>/edge_preview?index=&outline=&erode=`, one PNG rendered from the stroke-free twin by the same `apply_edge` the real render uses).
  **Apply** (`POST /api/generations/<id>/edge {outline, erode}`) saves **one snapshot** (`result.json edge_history`, seeded with how the batch started) and applies the edge to the whole batch:
  the stills are re-rendered (about 0.2 s) and the animations are re-cut from the stored video (`gates.reslice`, no credits; the animation cache keys on the edge, so a setting used before comes
  back in about 2 s and a new one takes about 13 s for 9 stickers). **Undo** steps back one real snapshot (the log is replayed as a stack: an `undo` entry pops, so two Undos never flip between two
  values) and is itself recorded; **Cancel** only drops the test. The same edge twice changes nothing and adds no snapshot. Besides Apply, a pending edge is applied automatically in exactly
  two moments: when the **video is generated from the image** (`POST /api/live/video {outline, erode}`) and when the **stickers go into a pack** (the add endpoint); both go through
  `Console.commit_edge`, which refuses while another job holds the pipeline. The video sheet is built from the stroke-free stickers on purpose, so changing the stroke never needs a new Kling video.
- **The returned video stays visible.** The Animation view shows the Kling video with the slot lines (a light 720 px `preview.mp4` is made when the video is attached, or on demand for older
  ones), and a batch with a Kling video counts as having a video everywhere in the UI.
- **Warnings in plain words.** A kept-with-a-check sticker says what Python noticed and what to do (for example "looks almost the same as S1: the same pose drawn twice? Kept: drop one with the
  x"), not a check name.
- **Independent local sequences for new plans (2026-10-19).** New slots persist
  `video_independent_v1`: fixed spatial cell, stated emotion, Action 1 then Action 2
  inside that cell, concurrent independent paces across cells. New sheets default
  to 2×2. The expressive line, fixed camera/background/design, empty slots and
  face-only restrictions stay. Loop closure is requested only when Loop is on.
  Older plans without video-template metadata retain `video_short_v1`; old
  template files and custom text are unchanged. This supersedes the 2026-10-09
  short-numbered-lines default. See [contract and limits](19-independent-cell-video-and-2x2.md).
