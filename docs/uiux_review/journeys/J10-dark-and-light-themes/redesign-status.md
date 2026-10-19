# Redesign status — 2026-10-15

**Issue:** Different visual vocabularies across screens.

**Implemented fix:** Semantic type/spacing/status/elevation/focus/motion tokens and opaque content surfaces.

**Evidence:** Eight initial surfaces + Studio/frame/saved-set/Emoji states sampled at1440/390 in both themes.

**Remaining:** Not an exhaustive contrast/accessibility certification; legacy inline styles remain.

[Current status](../../current-status.md) · [Execution log](../../implementation-log.md) · [Images](../../redesign-shots/README.md). Historical issue/proposed-fix documents retain the original findings; they are not a claim that all catalog refactors shipped.

### Engineering acceptance — 2026-10-19

Slider/reaction matrices passed in both themes at 1440px/390px. Selected dark-tab hover contrast was fixed from 1.26:1 to 13.24:1 (light 5.17:1).

[2026-10-19 acceptance evidence](../../acceptance-2026-10-19.md).
