# J1 — Create a sticker set in Studio

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Read [issues-and-proposed-fixes.md](issues-and-proposed-fixes.md) for the problem, evidence, proposed repair and constraints. Then use [implementation-checklist.md](implementation-checklist.md); the canonical task contracts remain in [uiux_plan.md](../../../uiux_plan.md).

| Finding | Issue | Proposed fix | Priority |
|---|---|---|---:|
| F-22 | Tap targets are too small across core journeys | Use44px logical targets, consistent8px gaps and secondary/tinted controls; retain every action and per-picture recovery. | 81.0 |
| F-19 | Presentation bypasses a shared token system | Introduce semantic spacing/type/status/material/control tokens; convert one bounded block per task; never tokenize art content values. | 49.5 |
| F-01 | Keep approved size bypasses preview | Restore the staged handler before extracting testCard; zero mutations before Apply; Cancel writes nothing. | 44.0 |
| F-05 | Refresh loops can overlap and redraw twice | Serialize tick, coalesce queue clock, then migrate one watcher per task. Preserve forced refresh and off-screen job completion. | 40.0 |
| F-23 | Allowed animations lose the readable boundary reason | Keep a one-sentence reason next to the allowed preview and a visible selected-sheet-cell status row. Preserve backend eligibility, technical final blocks and bulk recovery. | 11.0 |
| F-32 | Studio prompt view is dense and exposes an engine inspector | Keep editable prompt, price/unavailable explanation and primary; group supporting metadata under Advanced. Move backend connection detail into expandable inspector. | 9.0 |
| F-02 | Two Apply/Cancel presenters drift | Introduce ui-testcard.js testCard; video then edge adapters; responsive sheet treatment after behavior is pinned. | 8.0 |
| F-09 | Preview request lifecycles repeat; endpoints are distinct | Introduce bounded latest-result previewSession; never combine backend operations or move rendering decisions into JS. | 8.0 |

## Screenshots and walkthrough

[Journey contact sheet](../../shots/contact-J1.jpg) · [Recorded states](../../screens.md) · [Raw probes](../../probes.jsonl)

- [J1-01-studio-dark.jpg](../../shots/J1-01-studio-dark.jpg)
- [J1-02-plan-dark.jpg](../../shots/J1-02-plan-dark.jpg)
- [J1-03-batch-dark.jpg](../../shots/J1-03-batch-dark.jpg)
- [J1-03-batch-light.jpg](../../shots/J1-03-batch-light.jpg)
- [J1-04-preview-dark.jpg](../../shots/J1-04-preview-dark.jpg)
