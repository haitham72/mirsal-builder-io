# J7 — Home and welcome

> **Latest source validation:** Read [../../revalidation.md](../../revalidation.md). It classifies all 36 findings against the newer implementation; changed reaction scopes must be revised before coding.

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Read [issues-and-proposed-fixes.md](issues-and-proposed-fixes.md) for the problem, evidence, proposed repair and constraints. Then use [implementation-checklist.md](implementation-checklist.md); the canonical task contracts remain in [uiux_plan.md](../../../uiux_plan.md).

| Finding | Issue | Proposed fix | Priority |
|---|---|---|---:|
| F-19 | Presentation bypasses a shared token system | Introduce semantic spacing/type/status/material/control tokens; convert one bounded block per task; never tokenize art content values. | 49.5 |
| F-30 | Dark welcome text fades into pale artwork | Give slide text a fixed light-surface semantic palette or guaranteed contrasting text backing; preserve artwork/film; make dot hit regions44px. | 26.0 |
| F-29 | Library/public/Home totals count reactions as stickers | Define additive backend sticker_count/reaction_count, preserving existing fields and permissions; migrate Trending/Home presentation separately. | 12.0 |
| F-31 | Same Reaction effects wording leads to different workflows | Ask owner which door Home should present; recommend distinct pack-reaction/emoji-reaction labels while preserving both routes. | 7.0 |

## Screenshots and walkthrough

[Journey contact sheet](../../shots/contact-J7.jpg) · [Recorded states](../../screens.md) · [Raw probes](../../probes.jsonl)

- [J7-01-home-dark.jpg](../../shots/J7-01-home-dark.jpg)
- [J7-03-welcome-settled-dark.jpg](../../shots/J7-03-welcome-settled-dark.jpg)
- [J7-03-welcome-settled-light.jpg](../../shots/J7-03-welcome-settled-light.jpg)
