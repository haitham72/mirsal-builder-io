# Main-agent brief for the redesign branch — 2026-10-15

Implementation checkpoint: `1980c857`, pushed on `redesign-ui-ux`. Active checkout: `G:/Haitham/VsCode/Mirsal-Builder`. The user server runs at http://127.0.0.1:8796/. Check the current branch before committing. [Current status](current-status.md), [execution log](implementation-log.md) and the root `plan.md` describe delivered work and remaining acceptance.

## Locked decisions

1. Imports retain duplicate lookup, Open existing / Import again, in-batch Again into / As a new batch and explicit recovery. Main's forced-fresh-cut policy must not replace these dialogs during a future merge.
2. Tile Size/X/Y sliders stay behind Adjust; the frame editor remains available. Scheduling, Reset and busy-retry fixes are implemented.
3. Create and Library share Emoji style / Lottie style / Packs tab state (`rx.tab`). Keep both entry points and their existing management actions.
4. Emoji and Lottie exports remain distinct. Lottie selection, thumbnails and main-player updates target the active screen; older preview responses cannot replace a newer selection.
5. From a photo asks Sticker / Emojis. Sticker keeps the existing cutout/editor; Emojis imports an image sheet into Studio. From a video imports a video sheet into Studio. Imports offer Auto detect / 2×2 / 3×3; an explicitly different destination grid starts a separate batch.

## Latest evidence

- Node suite: 389 checks passed. Focused imports passed for automatic/manual image grids, preserving the original batch, standalone video and existing in-batch image/video behavior.
- Python console checks retain one stale assertion expecting removed `data-act=rxedit`; the Python wrapper suite is not green. Windows runs need UTF-8 (`PYTHONUTF8=1`) to read console source reliably.
- Browser, temporary storage and copied Lottie settings: saved-file highlight follows selection; SVG playback advances in Create and Library; returning to Create mounts its visible player.
- Browser imports completed READY: automatic 2×2 image sheet and a 3×3 video manually cut as 2×2, both opening Studio. No provider calls or external sends were used.

## Remaining work

The visual redesign and original reaction/pack requirements are implemented; owner visual review remains. Finish the slider/frame-editor and reaction-tab theme/phone matrices, extended browser states and shared-code extractions listed in `plan.md`. Optional Pre-run, Time scale, silhouette emitters and blend modes remain unimplemented and need a go-ahead. No main merge or deployment is authorized by this handoff.
