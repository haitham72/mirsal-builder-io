# J8 — Settings, Trash, Tickets, Help and Trending

> **Latest source validation:** Read [../../revalidation.md](../../revalidation.md). It classifies all 36 findings against the newer implementation; changed reaction scopes must be revised before coding.

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Read [issues-and-proposed-fixes.md](issues-and-proposed-fixes.md) for the problem, evidence, proposed repair and constraints. Then use [implementation-checklist.md](implementation-checklist.md); the canonical task contracts remain in [uiux_plan.md](../../../uiux_plan.md).

| Finding | Issue | Proposed fix | Priority |
|---|---|---|---:|
| F-22 | Tap targets are too small across core journeys | Use44px logical targets, consistent8px gaps and secondary/tinted controls; retain every action and per-picture recovery. | 81.0 |
| F-19 | Presentation bypasses a shared token system | Introduce semantic spacing/type/status/material/control tokens; convert one bounded block per task; never tokenize art content values. | 49.5 |
| F-07 | Segment builders disagree about semantics | segmentedHtml has choice/tabs/navigation modes; do not turn navigation into a preference or change data-act. | 21.0 |
| F-28 | Help rows are click-only divs | Use native focusable title controls with sibling secondary actions; preserve suopen/suq/sufaq, selected/scroll states and role visibility. | 18.0 |
| F-29 | Library/public/Home totals count reactions as stickers | Define additive backend sticker_count/reaction_count, preserving existing fields and permissions; migrate Trending/Home presentation separately. | 12.0 |
| F-26 | Local Account shortcut is a no-op | Derive section shortcuts from mounted cards after wrappers; retain LAN Account entry and backend behavior. | 10.0 |
| F-27 | Tickets have no section shortcut | Add role-aware Tickets section entry after mounted card detection; do not create another route. | 7.0 |

## Screenshots and walkthrough

[Journey contact sheet](../../shots/contact-J8.jpg) · [Recorded states](../../screens.md) · [Raw probes](../../probes.jsonl)

- [J8-01-settings-dark.jpg](../../shots/J8-01-settings-dark.jpg)
- [J8-01-settings-light.jpg](../../shots/J8-01-settings-light.jpg)
- [J8-02-trash-dark.jpg](../../shots/J8-02-trash-dark.jpg)
- [J8-02-trash-light.jpg](../../shots/J8-02-trash-light.jpg)
- [J8-04-faq-dark.jpg](../../shots/J8-04-faq-dark.jpg)
- [J8-05-trending-dark.jpg](../../shots/J8-05-trending-dark.jpg)
- [J8-06-tickets-bottom-dark.jpg](../../shots/J8-06-tickets-bottom-dark.jpg)
