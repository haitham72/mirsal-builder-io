# J10 — Dark and light comparisons

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Read [issues-and-proposed-fixes.md](issues-and-proposed-fixes.md) for the problem, evidence, proposed repair and constraints. Then use [implementation-checklist.md](implementation-checklist.md); the canonical task contracts remain in [uiux_plan.md](../../../uiux_plan.md).

| Finding | Issue | Proposed fix | Priority |
|---|---|---|---:|
| F-22 | Tap targets are too small across core journeys | Use44px logical targets, consistent8px gaps and secondary/tinted controls; retain every action and per-picture recovery. | 81.0 |
| F-19 | Presentation bypasses a shared token system | Introduce semantic spacing/type/status/material/control tokens; convert one bounded block per task; never tokenize art content values. | 49.5 |
| F-30 | Dark welcome text fades into pale artwork | Give slide text a fixed light-surface semantic palette or guaranteed contrasting text backing; preserve artwork/film; make dot hit regions44px. | 26.0 |

## Screenshots and walkthrough

[Journey contact sheet](../../shots/contact-J10.jpg) · [Recorded states](../../screens.md) · [Raw probes](../../probes.jsonl)

Use cited source evidence and the cross-journey links in the issue document.
