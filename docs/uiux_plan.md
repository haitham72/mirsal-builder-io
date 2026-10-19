# UI/UX — remaining work

Current branch: `redesign-ui-ux`. The old 87-task plan is a historical specification,
not the current execution queue. Its original contents remain in git and
`uiux_review/tasks.json`; unclassified legacy tasks are not silently declared fixed.
Reproduce their current need before scheduling them.

1. Fix [current audit](uiux_review/app-audit-2026-10-19.md) UX-01/02/03/04/05/08: phone editing/saving, primary hover, keyboard actions/names, frame-card dismissal and ownership text.
2. If W34 retains Watch folders, fix UX-09 phone rows. Do not retire a route without the owner's decision and baseline entry.
3. Complete remaining route-wide menu/keyboard/destructive states, loaded Prepare video, LAN roles and Settings/Help substates. Paid quality/sends are separate.
4. Resolve design proposals UX-06/07/10/11 with concrete review; F-31 wording, pricing and visual/merge verdicts remain Haitham's.
5. Extract API routers/schemas, graph lifecycle and shared UI state/watchers/presenters/styles. Existing T-024/025/031/034/035 are re-scoped below; do not recreate obsolete reaction workflows.
6. Triage inherited agent failures/errors; resolve W29 runtime retention and W33 parked frontend before deleting/untracking anything.

[Root plan](../plan.md) owns the queue. [Current status](uiux_review/current-status.md),
[remaining code tasks](uiux_review/code_tasks.md), and
[minimal user review guide](../user%20app%20review%20guide.md) provide entry points.
Implementation proof belongs in area docs and the execution log; no done steps remain here.
