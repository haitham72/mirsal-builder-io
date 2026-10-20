# Next steps

1. **Finish the Studio left panel** (built 2026-10-20, [plan + what is built](docs/design/15-studio-creation-sidebar-plan.md)): fix the empty Creative/Predefined pill in the narrow panel's Options, keep Generate reachable at the panel bottom while settings scroll, add a regression test for `studioCol`/`cpStash` and the Batches drawer, then a light/dark screenshot pass at 1440/1024/760/390. Haitham's visual review follows. New request must never fold; Create stays a fresh start.
2. **UX-10 phone Chat density:** one compact configuration disclosure and a readable conversation title on phone ([audit](docs/uiux_review/app-audit-2026-10-19.md) UX-10). Preserve status visibility, polling/scroll stability and every option.
3. **Unverified states:** route-wide keyboard/menu/destructive combinations, loaded Prepare video, LAN roles, all Settings/Help substates and every opened/hover state. Paid quality and sends remain separate. Do not rerun the completed 36-state theme and 24-case view checks without a relevant source change.
4. **Shared code / structure:** watchers and edge synchronization; range/segment/download/preview/cache presenters; API routers/schemas, graph lifecycle and explicit UI state ownership before cosmetic moves. T-024/025 are saved-set/Emoji sliders; T-031/034/035 are download/preview/cache adapters. Reconcile legacy task scopes and remaining reading paths.
5. **Owner decisions (never implement without Haitham):** F-31 Effects/Reactions wording, the Generate-prompt enhancer's pricing gate (W18), final dark/light visual verdict, merge timing. Use [user app review guide.md](user%20app%20review%20guide.md).
6. **Optional / baseline:** Lottie Pre-run, Time scale, silhouette feasibility and blend modes need a go-ahead and unchanged-default proof. Triage agent's 4 failures / 9 errors with fakes. W29 runtime retention/backup, W33 parked frontend and W34 History remain owner decisions.

All confirmed audit defects (UX-01..09, UX-11) are fixed: [audit fixes](docs/design/16-app-audit-fixes-2026-10-20.md).

Work only here on `redesign-ui-ux`; verify branch before each explicit-path commit. Preserve duplicate-choice imports/grid consent, new-plan 2x2 defaults with explicit/existing grids retained, Resize, engine authority, reversible picture decisions and separate Emoji/Lottie exports. No merge, deployment, paid calls or sends.

Browser checks use sanitized copied output, disabled providers and a task-owned port. Never automate/restart/repoint real-data :8770. Area docs and dated evidence record what is implemented; HANDOFF.md records where the session stopped.
