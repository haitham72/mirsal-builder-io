# Redesign status — 2026-10-15

**Issue:** Counts call reactions stickers; pack tabs and previews compete with content.

**Implemented fix:** Backend semantic counts, always-visible sticker then reaction sections, Library Studio shortcut, bounded viewer/frame sheets.

**Evidence:** Library shortcut opens G002; phone viewer wraps; pack and frame controls accepted in sampled themes/widths.

**Remaining:** Broader grid/preview/download helper extraction and exhaustive editor states remain.

[Current status](../../current-status.md) · [Execution log](../../implementation-log.md) · [Images](../../redesign-shots/README.md). Historical issue/proposed-fix documents retain the original findings; they are not a claim that all catalog refactors shipped.

### Latest Library and Create acceptance — 2026-10-15

`1980c857` fixes Library Lottie highlighting and visible-player mounting. Browser checks followed multiple saved-file selections and confirmed playback after Library → Create return. Create now offers Sticker / Emojis from a photo and video-sheet import; image/video sheets open Studio with Auto / 2×2 / 3×3 controls. Temporary imports finished READY. Wider editor/theme/phone states remain pending.

### Engineering acceptance — 2026-10-19

All three reaction tabs passed on both Create and Library, with shared state, real server contents and keyboard activation in all four width/theme states.

[2026-10-19 acceptance evidence](../../acceptance-2026-10-19.md).
