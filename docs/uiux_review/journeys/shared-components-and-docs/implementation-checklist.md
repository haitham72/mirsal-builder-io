# Shared code structure, inventory and documentation — implementation checklist

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

1. Read current `CLAUDE.md`, then only the relevant area section. Check the shared checkout branch and uncommitted edits.
2. Revalidate the named current functions and contracts. Mark already-fixed findings resolved; do not overwrite the other LLM’s changes. Reaction work must preserve the current preset manifest and emoji-free/no-base64 contract.
3. Use the task dependency graph; shared tasks run once. File/line budgets include tests.
4. Run the narrow checks listed in the canonical task only after its source change. This review adds documents and runs zero code tests.
5. Recheck the affected UI with copied data/providers off; never touch owner port 8770 or paid/send acceptance.
6. Commit only explicit owned paths, after checking branch immediately before commit.

| Task | Model | Files | Line estimate | Depends on |
|---|---|---|---:|---|
| T-059 Reflow packs.js bounded helpers | 6.1-sol-medium | mirsal/mirsal/console/packs.js | 145 | — |
| T-060 Reflow live.js bounded helpers | 6.1-sol-medium | mirsal/mirsal/console/live.js | 145 | — |
| T-061 Reflow particles.js bounded helpers | 6.1-sol-medium | mirsal/mirsal/console/particles.js | 145 | — |
| T-062 Reflow reactions.js bounded helpers | 6.1-sol-medium | mirsal/mirsal/console/reactions.js | 145 | — |
| T-063 Correct retired-History wording | 6.1-sol-medium | docs/waiting-for-haitham.md | 40 | — |
| T-064 Refresh generated inventory counts after repairs | 6.1-sol-medium | docs/ui_inventory.md | 100 | T-001 |
| T-079 Reconcile current UI screen contracts | luna-6-high | docs/design/04-4-the-shell-rules-that-hold-on-every-screen.md<br>docs/design/11-ui-ux-pass-of-2026-10-03-what-a-click-means.md<br>docs/reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md<br>docs/redesign_plan.md | 300 | — |
| T-080 Create a cheap UI reading gateway and wiring appendix | luna-6-high | CLAUDE.md<br>README.md<br>docs/design.md<br>docs/architecture.md<br>docs/ui_gateway.md<br>docs/architecture-ui-wiring.md | 360 | T-079 |
| T-081 Correct contradictory final-block and startup wording | 6.1-sol-medium | docs/rules.md<br>docs/agent-and-chat.md | 90 | T-079 |
| T-082 Merge tracked work and disambiguate tracker IDs | luna-6-high | docs/backlog.md<br>docs/waiting-for-haitham.md<br>plan.md | 200 | T-071, T-079 |

Task details and acceptance: [uiux_plan.md](../../../uiux_plan.md). The catalog’s scopes were written for the review snapshot; reconcile before execution. Product choices remain in its Questions for Haitham section.
