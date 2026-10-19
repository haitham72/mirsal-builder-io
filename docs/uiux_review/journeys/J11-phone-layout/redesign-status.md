# Redesign status — 2026-10-15

**Issue:** Small controls, overflowing headers and unreachable Apply/Cancel.

**Implemented fix:** 44px floors, wrapping headers and bounded bottom sheets; preview placement measures real height.

**Evidence:** 390px phone: four frame-session variants remain in viewport, all frame buttons44px, Cancel0POST; saved-set and Emoji editor no overflow.

**Remaining:** Populated multi-owner saved-set/pack dialogs and route-wide keyboard/menu combinations remain in the exhaustive-state follow-up.

[Current status](../../current-status.md) · [Execution log](../../implementation-log.md) · [Images](../../redesign-shots/README.md). Historical issue/proposed-fix documents retain the original findings; they are not a claim that all catalog refactors shipped.

### Engineering acceptance — 2026-10-19

390px slider/reaction matrices passed in both themes; frame editor remained within viewport and Cancel made zero position/video-size POSTs. Route-wide keyboard/menu combinations remain a bounded follow-up.

[2026-10-19 acceptance evidence](../../acceptance-2026-10-19.md).
