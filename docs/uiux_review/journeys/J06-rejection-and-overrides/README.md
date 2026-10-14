# J6 — Rejected pictures, reasons and reversible overrides

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Read [issues-and-proposed-fixes.md](issues-and-proposed-fixes.md) for the problem, evidence, proposed repair and constraints. Then use [implementation-checklist.md](implementation-checklist.md); the canonical task contracts remain in [uiux_plan.md](../../../uiux_plan.md).

| Finding | Issue | Proposed fix | Priority |
|---|---|---|---:|
| F-22 | Tap targets are too small across core journeys | Use44px logical targets, consistent8px gaps and secondary/tinted controls; retain every action and per-picture recovery. | 81.0 |
| F-23 | Allowed animations lose the readable boundary reason | Keep a one-sentence reason next to the allowed preview and a visible selected-sheet-cell status row. Preserve backend eligibility, technical final blocks and bulk recovery. | 11.0 |
| F-13 | Decision reason boxes need one UI presentation adapter | Build decisionStatusHtml from existing backend eligibility and reason data; keep allow/include/drop distinctions and bulk controls. | 6.0 |

## Screenshots and walkthrough

[Journey contact sheet](../../shots/contact-J6.jpg) · [Recorded states](../../screens.md) · [Raw probes](../../probes.jsonl)

- [J6-01-blocked-animation-dark.jpg](../../shots/J6-01-blocked-animation-dark.jpg)
- [J6-02-rejected-still-dark.jpg](../../shots/J6-02-rejected-still-dark.jpg)
- [J6-02-rejected-still-detail-dark.jpg](../../shots/J6-02-rejected-still-detail-dark.jpg)
- [J6-02-rejected-still-light.jpg](../../shots/J6-02-rejected-still-light.jpg)
- [J6-03-chat-review-dark.jpg](../../shots/J6-03-chat-review-dark.jpg)
