# J2 — Create through AI chat

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Read [issues-and-proposed-fixes.md](issues-and-proposed-fixes.md) for the problem, evidence, proposed repair and constraints. Then use [implementation-checklist.md](implementation-checklist.md); the canonical task contracts remain in [uiux_plan.md](../../../uiux_plan.md).

| Finding | Issue | Proposed fix | Priority |
|---|---|---|---:|
| F-22 | Tap targets are too small across core journeys | Use44px logical targets, consistent8px gaps and secondary/tinted controls; retain every action and per-picture recovery. | 81.0 |
| F-19 | Presentation bypasses a shared token system | Introduce semantic spacing/type/status/material/control tokens; convert one bounded block per task; never tokenize art content values. | 49.5 |
| F-32 | Studio prompt view is dense and exposes an engine inspector | Keep editable prompt, price/unavailable explanation and primary; group supporting metadata under Advanced. Move backend connection detail into expandable inspector. | 9.0 |
| F-13 | Decision reason boxes need one UI presentation adapter | Build decisionStatusHtml from existing backend eligibility and reason data; keep allow/include/drop distinctions and bulk controls. | 6.0 |

## Screenshots and walkthrough

[Journey contact sheet](../../shots/contact-J2.jpg) · [Recorded states](../../screens.md) · [Raw probes](../../probes.jsonl)

- [J2-01-chat-dark.jpg](../../shots/J2-01-chat-dark.jpg)
- [J2-03-plan-dark.jpg](../../shots/J2-03-plan-dark.jpg)
