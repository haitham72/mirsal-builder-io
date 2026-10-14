# J9 — ZIP, collection and Telegram dialogs

> **Latest source validation:** Read [../../revalidation.md](../../revalidation.md). It classifies all 36 findings against the newer implementation; changed reaction scopes must be revised before coding.

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Read [issues-and-proposed-fixes.md](issues-and-proposed-fixes.md) for the problem, evidence, proposed repair and constraints. Then use [implementation-checklist.md](implementation-checklist.md); the canonical task contracts remain in [uiux_plan.md](../../../uiux_plan.md).

| Finding | Issue | Proposed fix | Priority |
|---|---|---|---:|
| F-22 | Tap targets are too small across core journeys | Use44px logical targets, consistent8px gaps and secondary/tinted controls; retain every action and per-picture recovery. | 81.0 |
| F-06 | Backdrop hides retime without settling its promise | Every dismissal/replacement settles null once; keep explicit answers true/false and all request payloads. | 24.0 |
| F-08 | Download lifecycle is copied | downloadFile owns only object URLs it creates; preserve filenames and each URL/body; migrate consumers separately. | 12.0 |
| F-10 | Feedback markup repeats with different lifetimes | Share inline status markup only; retain toast, field errors and durable notifications as different channels. | 10.0 |

## Screenshots and walkthrough

[Journey contact sheet](../../shots/contact-J9.jpg) · [Recorded states](../../screens.md) · [Raw probes](../../probes.jsonl)

- [J9-01-retime-dark.jpg](../../shots/J9-01-retime-dark.jpg)
- [J9-02-collection-dark.jpg](../../shots/J9-02-collection-dark.jpg)
- [J9-03-telegram-dark.jpg](../../shots/J9-03-telegram-dark.jpg)
