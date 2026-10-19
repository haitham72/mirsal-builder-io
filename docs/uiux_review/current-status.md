# Redesign — remaining work

Source audited: `64d8b8a4`, `redesign-ui-ux`, 2026-10-19. No product fixes were made in this audit.
Use [plan.md](../../plan.md) as the execution queue and the [user review guide](../../user%20app%20review%20guide.md) for Haitham's later review.

- **Confirmed defects:** phone populated editor/animation/Save layout; dark primary hover; keyboard sticker actions; editor accessible names; frame preview focus/Escape; incorrect saved-set ownership heading. Watch-folder phone layout depends on W34 retention. IDs and reproduction: [current audit](app-audit-2026-10-19.md).
- **Design decisions:** workspace identity, earlier-work recovery, phone Chat density, recognizable reaction owners, F-31 wording, cloud pricing and visual verdicts.
- **Engineering:** API routers/schemas, graph/lifecycle boundaries, watcher/presenter/cache/style extractions T-024/025/031/034/035; runtime/parked React decisions W29/W33.
- **Unverified states:** route-wide keyboard/menu/destructive combinations, loaded Prepare video, LAN roles, all Settings/Help states and every opened/hover state. Paid quality and sends remain owner-only.
- **Test debt:** inherited agent baseline 322 / 4 failures / 9 errors. No tests rerun for this docs-only audit.
- **Merge/deployment:** remain unapproved. Preserve duplicate-choice imports, Resize semantics, engine decisions, reversible picture overrides and distinct Emoji/Lottie exports.

Evidence, not an open-work queue: [audit measurements/screenshots](app-audit-2026-10-19.json), [earlier acceptance](acceptance-2026-10-19.md), [implementation log](implementation-log.md). The audit covers 96 sampled screen states and additional populated controls; it is not exhaustive acceptance.
