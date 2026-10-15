# Shared code structure, inventory and documentation

> [Current redesign status and evidence](redesign-status.md) override historical implementation status below.

> **Latest source validation:** Read [../../revalidation.md](../../revalidation.md). It classifies all 36 findings against the newer implementation; changed reaction scopes must be revised before coding.

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Read [issues-and-proposed-fixes.md](issues-and-proposed-fixes.md) for the problem, evidence, proposed repair and constraints. Then use [implementation-checklist.md](implementation-checklist.md); the canonical task contracts remain in [uiux_plan.md](../../../uiux_plan.md).

| Finding | Issue | Proposed fix | Priority |
|---|---|---|---:|
| F-33 | Published screen contracts contradict each other | Choose dated current contracts and remove stale statements; UI gateway under1KB links owners instead of reprinting contracts. | 30.0 |
| F-34 | Doc organization and tracker IDs raise reading cost | Split task-critical wiring/contracts from appendices; compact responsibility indexes; preserve tracker provenance when disambiguating duplicate49. | 24.0 |
| F-11 | Long-line scripts make small changes expensive to review | Reflow bounded named functions with vendored Acorn canonical token equality; do not blanket-format templates. | 18.0 |
| F-21 | Inventory unique count omits the extra overwrite | After the Keep repair regenerate inventory and verify unique counts; no baseline action drops. | 12.0 |
| F-20 | History retirement prose contradicts active route | Correct the prose; keep route/actions/owner gate and parked React. | 8.0 |
| F-18 | Script-order wrappers form implicit extension contracts | Preserve loading order; extract small presenters first. Defer universal extension bus. | 7.0 |
| F-16 | Missing literal buttons do not prove dead actions | Keep every candidate until callers/dynamic markup/baseline are checked and owner authorizes any retirement. | 2.0 |
| F-15 | Relative-time helpers use distinct units/policies | Pin units first if revisited; no mechanical merge of policy into one global helper. | 1.5 |
| F-14 | Escaping aliases are not unsafe global collisions | Retain scoped aliases and standalone fixtures; document boundary instead of a forced shared-global rewrite. | 1.0 |
| F-17 | Unmatched CSS scan is a candidate list | No CSS deletion from this scan alone. Require emitted-markup evidence and scoped acceptance before future cleanup. | 1.0 |

## Screenshots and walkthrough

[Recorded states](../../screens.md) · [Raw probes](../../probes.jsonl)

Use cited source evidence and the cross-journey links in the issue document.
