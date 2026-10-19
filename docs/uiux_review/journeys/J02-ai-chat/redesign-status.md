# Redesign status — 2026-10-15

**Issue:** Dense or translucent content surfaces and inconsistent control sizing.

**Implemented fix:** Shared opaque card/composer surfaces and44px controls, preserving the aurora and routes.

**Evidence:** Initial Chat at1440/390 in both themes, no horizontal overflow; no new paid turn.

**Remaining:** Live model turns and exhaustive route-wide keyboard states remain outside this free acceptance; saved synthetic long-history polling passed.

[Current status](../../current-status.md) · [Execution log](../../implementation-log.md) · [Images](../../redesign-shots/README.md). Historical issue/proposed-fix documents retain the original findings; they are not a claim that all catalog refactors shipped.

### Engineering acceptance — 2026-10-19

A saved synthetic history was bounded to 400 messages and retained scroll position/count under polling in all four width/theme states. All five memory findings are fixed; agent area matches base (322 / 4 failures / 9 errors).

[2026-10-19 acceptance evidence](../../acceptance-2026-10-19.md).
