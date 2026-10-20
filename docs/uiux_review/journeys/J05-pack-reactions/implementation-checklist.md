# Pack reactions — remaining checklist

- [x] UX-08 owner-aware heading (2026-10-20): the set heading's ownership tag is derived from `SP.set.owner`, never hard-coded "on their own" (`console/particles.js` `spBody`). `tests/js/particle_editor.test.js`.
- [x] UX-11 recognizable owner names/thumbnails (2026-10-20): Manage stickers resolves each `owner[].sticker_id` to its name/thumbnail/pack through the library (`spStickerRef`), falling back to the id only when it is no longer in any pack. `tests/js/particles.test.js`.
- [ ] Optional Lottie fields and shared adapters; remaining route-wide/destructive combinations.

Before implementation: reproduce against current source, preserve all contracts,
use one narrow failing→passing check per fix and copied data/providers off.
Check `redesign-ui-ux` before committing explicit paths. No owner verdict is inferred.

[Current findings/acceptance gates](../../app-audit-2026-10-19.md) · [Status](redesign-status.md) · [Root plan](../../../../plan.md)
