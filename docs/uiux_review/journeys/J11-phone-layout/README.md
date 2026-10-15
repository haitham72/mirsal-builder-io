# J11 — Phone Library, pack, viewer and reaction editor

> [Current redesign status and evidence](redesign-status.md) override historical implementation status below.

> **Latest source validation:** Read [../../revalidation.md](../../revalidation.md). It classifies all 36 findings against the newer implementation; changed reaction scopes must be revised before coding.

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Read [issues-and-proposed-fixes.md](issues-and-proposed-fixes.md) for the problem, evidence, proposed repair and constraints. Then use [implementation-checklist.md](implementation-checklist.md); the canonical task contracts remain in [uiux_plan.md](../../../uiux_plan.md).

| Finding | Issue | Proposed fix | Priority |
|---|---|---|---:|
| F-22 | Tap targets are too small across core journeys | Use44px logical targets, consistent8px gaps and secondary/tinted controls; retain every action and per-picture recovery. | 81.0 |
| F-19 | Presentation bypasses a shared token system | Introduce semantic spacing/type/status/material/control tokens; convert one bounded block per task; never tokenize art content values. | 49.5 |
| F-36 | Phone viewer header squeezes the title into a word column | At phone width give metadata a full header row with Close; put previous/background choices/next in a second row; preserve all labels/actions and a scrollable bounded viewer. | 24.0 |
| F-35 | Phone Library tabs locally exceed their row | Keep all four choices and expose them through wrapping/grid or accessible scrolling; acceptance is real pointer/keyboard access to Trending, no global width increase. | 12.0 |

## Screenshots and walkthrough

[Journey contact sheet](../../shots/contact-J11.jpg) · [Recorded states](../../screens.md) · [Raw probes](../../probes.jsonl)

- [J11-01-library-dark.jpg](../../shots/J11-01-library-dark.jpg)
- [J11-03-pack-dark.jpg](../../shots/J11-03-pack-dark.jpg)
- [J11-04-viewer-dark.jpg](../../shots/J11-04-viewer-dark.jpg)
- [J11-05-wall-dark.jpg](../../shots/J11-05-wall-dark.jpg)
- [J11-06-editor-dark.jpg](../../shots/J11-06-editor-dark.jpg)
- [J11-06-editor-light.jpg](../../shots/J11-06-editor-light.jpg)
