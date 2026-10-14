# J3 — Library, pack, viewer, Edit and Timeline

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Read [issues-and-proposed-fixes.md](issues-and-proposed-fixes.md) for the problem, evidence, proposed repair and constraints. Then use [implementation-checklist.md](implementation-checklist.md); the canonical task contracts remain in [uiux_plan.md](../../../uiux_plan.md).

| Finding | Issue | Proposed fix | Priority |
|---|---|---|---:|
| F-22 | Tap targets are too small across core journeys | Use44px logical targets, consistent8px gaps and secondary/tinted controls; retain every action and per-picture recovery. | 81.0 |
| F-19 | Presentation bypasses a shared token system | Introduce semantic spacing/type/status/material/control tokens; convert one bounded block per task; never tokenize art content values. | 49.5 |
| F-07 | Segment builders disagree about semantics | segmentedHtml has choice/tabs/navigation modes; do not turn navigation into a preference or change data-act. | 21.0 |
| F-24 | Cover badge intercepts Timeline click | Make decorative cover badge pointer-events:none or place it clear of controls; native click must work, no forced click workaround. | 18.0 |
| F-08 | Download lifecycle is copied | downloadFile owns only object URLs it creates; preserve filenames and each URL/body; migrate consumers separately. | 12.0 |
| F-29 | Library/public/Home totals count reactions as stickers | Define additive backend sticker_count/reaction_count, preserving existing fields and permissions; migrate Trending/Home presentation separately. | 12.0 |
| F-03 | Grouped grids repeat presentation | Extract only groupedGridHtml; Library keeps global carousel indices, Pack keeps source groups, ordering, cover and drag actions. | 10.5 |
| F-12 | Range label/output builders repeat in editors | rangeFieldHtml can host them later, one caller per task; user artwork colours/canvas coordinates remain data. | 6.0 |

## Screenshots and walkthrough

[Journey contact sheet](../../shots/contact-J3.jpg) · [Recorded states](../../screens.md) · [Raw probes](../../probes.jsonl)

- [J3-01-library-dark.jpg](../../shots/J3-01-library-dark.jpg)
- [J3-02-grouped-dark.jpg](../../shots/J3-02-grouped-dark.jpg)
- [J3-03-pack-dark.jpg](../../shots/J3-03-pack-dark.jpg)
- [J3-03-pack-light.jpg](../../shots/J3-03-pack-light.jpg)
- [J3-04-viewer-dark.jpg](../../shots/J3-04-viewer-dark.jpg)
- [J3-05-cover-hover-dark.jpg](../../shots/J3-05-cover-hover-dark.jpg)
- [J3-05-timeline-dark.jpg](../../shots/J3-05-timeline-dark.jpg)
- [J3-06-edit-project-light.jpg](../../shots/J3-06-edit-project-light.jpg)
