# Rejected pictures, reasons and reversible overrides — implementation checklist

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

1. Read current `CLAUDE.md`, then only the relevant area section. Check the shared checkout branch and uncommitted edits.
2. Revalidate the named current functions and contracts. Mark already-fixed findings resolved; do not overwrite the other LLM’s changes. Reaction work must preserve the current preset manifest and emoji-free/no-base64 contract.
3. Use the task dependency graph; shared tasks run once. File/line budgets include tests.
4. Run the narrow checks listed in the canonical task only after its source change. This review adds documents and runs zero code tests.
5. Recheck the affected UI with copied data/providers off; never touch owner port 8770 or paid/send acceptance.
6. Commit only explicit owned paths, after checking branch immediately before commit.

| Task | Model | Files | Line estimate | Depends on |
|---|---|---|---:|---|
| T-052 Introduce decision-status presentation adapter | luna-6-high | mirsal/mirsal/console/ui-decision.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/decision_status.test.js<br>mirsal/tests/js/console_vm.js | 230 | — |
| T-053 Migrate blocked still/animation reason box | 6.1-sol-medium | mirsal/mirsal/console/studio-tiles.js<br>mirsal/tests/js/allow_tiles.test.js | 140 | T-052 |
| T-054 Migrate blocked animation overlay | 6.1-sol-medium | mirsal/mirsal/console/studio-tiles.js<br>mirsal/tests/js/allow_tiles.test.js | 140 | T-052 |
| T-055 Migrate chat rejected tile status | luna-6-high | mirsal/mirsal/console/chat-cards.js<br>mirsal/tests/js/chat_allow.test.js | 200 | T-052 |
| T-066 Apply44px targets through semantic control tokens | luna-6-high | mirsal/mirsal/console/studio.css<br>mirsal/mirsal/console/agent.css<br>mirsal/mirsal/console/theme.css | 180 | T-056 |
| T-069 Clarify Studio primary versus recovery actions | luna-6-high | mirsal/mirsal/console/studio-core.js<br>mirsal/mirsal/console/studio-tiles.js<br>mirsal/mirsal/console/studio.css<br>mirsal/tests/js/allow_tiles.test.js | 220 | T-053, T-066 |

Task details and acceptance: [uiux_plan.md](../../../uiux_plan.md). The catalog’s scopes were written for the review snapshot; reconcile before execution. Product choices remain in its Questions for Haitham section.
