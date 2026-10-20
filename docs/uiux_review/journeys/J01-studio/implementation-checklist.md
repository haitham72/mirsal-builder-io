# Studio — remaining checklist

- [ ] Left creation panel is built ([plan](../../../design/15-studio-creation-sidebar-plan.md)): fix the empty Creative/Predefined pill, pin Generate at the panel bottom, add its regression test, screenshot pass; then Haitham's review. New request must stay open. (UX-05 is built: [audit fixes](../../../design/16-app-audit-fixes-2026-10-20.md).)
- [ ] Watcher/edge synchronization and shared preview/cache ownership (separate from slider tasks T-024/025).
- [ ] Remaining route-wide states and owner visual verdict; preserve fresh Create and existing slider/frame semantics.

Before implementation: reproduce against current source, preserve all contracts,
use one narrow failing→passing check per fix and copied data/providers off.
Check `redesign-ui-ux` before committing explicit paths. No owner verdict is inferred.

[Current findings/acceptance gates](../../app-audit-2026-10-19.md) · [Status](redesign-status.md) · [Root plan](../../../../plan.md)
