# J5 — Pack reactions, motion and standalone effects

> [Current redesign status and evidence](redesign-status.md) override historical implementation status below.

> **Latest source validation:** Read [../../revalidation.md](../../revalidation.md). It classifies all 36 findings against the newer implementation; changed reaction scopes must be revised before coding.

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Read [issues-and-proposed-fixes.md](issues-and-proposed-fixes.md) for the problem, evidence, proposed repair and constraints. Then use [implementation-checklist.md](implementation-checklist.md); the canonical task contracts remain in [uiux_plan.md](../../../uiux_plan.md).

| Finding | Issue | Proposed fix | Priority |
|---|---|---|---:|
| F-19 | Presentation bypasses a shared token system | Introduce semantic spacing/type/status/material/control tokens; convert one bounded block per task; never tokenize art content values. | 49.5 |
| F-07 | Segment builders disagree about semantics | segmentedHtml has choice/tabs/navigation modes; do not turn navigation into a preference or change data-act. | 21.0 |
| F-04 | Range controls repeat across distinct reaction contracts | Share rangeFieldHtml; retain namespaces, defaults, touched-only params, versioned emoji and pack ownership. | 10.0 |
| F-09 | Preview request lifecycles repeat; endpoints are distinct | Introduce bounded latest-result previewSession; never combine backend operations or move rendering decisions into JS. | 8.0 |
| F-25 | Reaction editor and batch controls compete for space | Group basic motion/shape and one Advanced; sticky phone action footer; keep complete bank/preset/batch actions and values. Merge existing plan items rather than call them new. | 7.0 |
| F-31 | Same Reaction effects wording leads to different workflows | Ask owner which door Home should present; recommend distinct pack-reaction/emoji-reaction labels while preserving both routes. | 7.0 |
| F-12 | Range label/output builders repeat in editors | rangeFieldHtml can host them later, one caller per task; user artwork colours/canvas coordinates remain data. | 6.0 |

## Screenshots and walkthrough

[Journey contact sheet](../../shots/contact-J5.jpg) · [Recorded states](../../screens.md) · [Raw probes](../../probes.jsonl)

- [J5-01-pack-reactions-light.jpg](../../shots/J5-01-pack-reactions-light.jpg)
- [J5-02-set-card-light.jpg](../../shots/J5-02-set-card-light.jpg)
- [J5-03-motion-light.jpg](../../shots/J5-03-motion-light.jpg)
- [J5-04-effects-light.jpg](../../shots/J5-04-effects-light.jpg)
