# HANDOFF — 2026-10-15 (save point; Claude stopped at Haitham's request: weekly budget at 99%)

Branch `handpicked-lottie`, everything below committed and pushed. No uncommitted source of mine. Other sessions' uncommitted data in `mirsal/out/` and `Custom_emojis/` is untouched.

## Done this session (commits)

| commit | what |
|---|---|
| 826cf70f | Repaired another session's broken import fix (JS syntax error in imports.js killed the import buttons; nonexistent ffmpeg call; `cut_sheet` VIDEO_RETURNED reverted). Grid-mismatch question: "Cut it as R×C anyway" (`grid_ok=1`). reslice/preview/reloop work on imported 3x3 videos. |
| a9f16b93 | Proposal doc `docs/size-position-lottie-proposal.md`. |
| f3b9ef52 | **Size/Position**: `[✓] Resize` + Size on the batch row; hot spot (pixels opaque in ≥50% of frames) sizing; per-sticker frame editor (Position drag/arrows/Centre, guide grid, frame scrubber); every test = ONE frame PNG (`engine/video.preview_frame`, `size_window`); native routes `POST /api/generations/{id}/resize`, `/position`. |
| 7f1e4d17 | **Lottie style à la Trapcode Particular**: Emitter / Particle / Physics / Aux groups, presets, seed re-roll, time sampling (`tm`). Byte-identical for old bursts (second RNG; 9 cases compared). Fix: fresh preset library lacked `handpicked`. |
| ec16244a | Import the same file again on purpose: "Again into G###" / "As a new batch" (`again=1`). |

Tests run (narrow): gates area 40, engine/video area 56, imports 14, live slicing test, lottie_reactions 22, emoji_lottie 12, ui_inventory 4 — all pass. Particle area: 2 pre-existing failures in `test_particle_set` (see plan.md).

## Not done / next (see plan.md)

1. **No browser check of anything above** — restart the server from `mirsal/.venv` and look before judging.
2. UI/UX plan review (`docs/uiux_review/plan-review.md`) not written. Facts already established:
   - The uiux repair batch (T-001..T-004, T-065, T-086, T-074, T-072, T-073) IS in HEAD (`uiux-fixes` is an ancestor); every source marker present. T-001 is superseded by the Resize/frame editor. Browser acceptance outstanding for all.
   - `docs/uiux_review/revalidation.md` (2026-10-14) predates the repairs and the Size/Position + Lottie work: its "still present" for F-01/F-05/F-06/F-24/F-26..F-28/F-30/F-36 is stale.
   - plan.md items 1–9 (reaction/pack cleanup) were not checked this session: keep them.
3. Proposal decisions 1–3 approved by Haitham 2026-10-15 (as built). UI/UX plan review done: docs/uiux_review/plan-review.md. Still open: "Use 2×2" for a mismatched grid was deliberately not offered (a 3×3 batch's stickers are its cells).

## Merged into main (2026-10-15)
Branch handpicked-lottie merged to main as fast-forward (main was its ancestor) and deleted, local and remote.
Commits carried: no-dup import removal + grey everywhere (5ad67e2d), tile sliders (9194bfc5 + docs 47817ab6),
reactions bridge + 3-tab merge + Library tabs (2743bd7f, d78d6605, 15da937d, docs 09d62c8c).
Open work stays in plan.md; redesign continues on redesign-ui-ux.
