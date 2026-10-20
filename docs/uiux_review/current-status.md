# Redesign — remaining work

Source audited: `64d8b8a4`, `redesign-ui-ux`, 2026-10-19 — a docs-only audit, no product fixes.
Two later, separate phases on the same branch did land product fixes: the
[neutral/cyan dark theme and always-open New request](dark-rework-2026-10-19.md)
(fixes UX-02 primary-hover contrast; folds in always-open New request), and a
2026-10-20 pass fixing UX-03/04/05 (keyboard tiles, editor names, frame card
focus/Escape), UX-06 (workspace identity), UX-08 (owner-aware heading) and
UX-11 (owner names/thumbnails) — see [audit fixes](../design/16-app-audit-fixes-2026-10-20.md). The defect list below is this audit's, minus what those phases
already fixed. Use [plan.md](../../plan.md) as the execution queue and the
[user review guide](../../user%20app%20review%20guide.md) for Haitham's later review.

- **Confirmed defects:** phone populated editor/animation/Save layout. Watch-folder phone layout depends on W34 retention. IDs and reproduction: [current audit](app-audit-2026-10-19.md).
- **Design decisions:** review the proposed Studio left creation panel; earlier-work recovery, phone Chat density, F-31 wording, cloud pricing and visual verdicts.
- **Engineering:** API routers/schemas, graph/lifecycle boundaries, watcher/presenter/cache/style extractions T-024/025/031/034/035; runtime/parked React decisions W29/W33.
- **Unverified states:** route-wide keyboard/menu/destructive combinations, loaded Prepare video, LAN roles, all Settings/Help states and every opened/hover state. Paid quality and sends remain owner-only.
- **Test debt:** inherited agent baseline 322 / 4 failures / 9 errors. No tests rerun for this docs-only audit.
- **Merge/deployment:** remain unapproved. Preserve duplicate-choice imports, Resize semantics, engine decisions, reversible picture overrides and distinct Emoji/Lottie exports.

Evidence, not an open-work queue: [audit measurements/screenshots](app-audit-2026-10-19.json), [earlier acceptance](acceptance-2026-10-19.md), [implementation log](implementation-log.md). The audit covers 96 sampled screen states and additional populated controls; it is not exhaustive acceptance.
