# ZIP, collection and Telegram dialogs — implementation checklist

> **Latest source validation:** Read [../../revalidation.md](../../revalidation.md). It classifies all 36 findings against the newer implementation; changed reaction scopes must be revised before coding.

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

1. Read current `CLAUDE.md`, then only the relevant area section. Check the shared checkout branch and uncommitted edits.
2. Revalidate the named current functions and contracts. Mark already-fixed findings resolved; do not overwrite the other LLM’s changes. Reaction work must preserve the current preset manifest and emoji-free/no-base64 contract.
3. Use the task dependency graph; shared tasks run once. File/line budgets include tests.
4. Run the narrow checks listed in the canonical task only after its source change. This review adds documents and runs zero code tests.
5. Recheck the affected UI with copied data/providers off; never touch owner port 8770 or paid/send acceptance.
6. Commit only explicit owned paths, after checking branch immediately before commit.

| Task | Model | Files | Line estimate | Depends on |
|---|---|---|---:|---|
| T-002 Settle retime on every dialog cancellation | luna-6-high | mirsal/mirsal/console/app.js<br>mirsal/mirsal/console/packs.js<br>mirsal/tests/js/dialog_cancel.test.js | 160 | — |
| T-026 Introduce URL/blob download utility | luna-6-high | mirsal/mirsal/console/ui-download.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/ui_download.test.js<br>mirsal/tests/js/console_vm.js | 160 | — |
| T-027 Migrate Timeline blob download | 6.1-sol-medium | mirsal/mirsal/console/animate.js<br>mirsal/tests/js/ui_download.test.js | 110 | T-026 |
| T-028 Migrate video-editor blob download | 6.1-sol-medium | mirsal/mirsal/console/prepare.js<br>mirsal/tests/js/ui_download.test.js | 110 | T-026 |
| T-029 Migrate still-editor PNG download | 6.1-sol-medium | mirsal/mirsal/console/editor.js<br>mirsal/tests/js/ui_download.test.js | 80 | T-026 |
| T-030 Migrate particle Lottie download | 6.1-sol-medium | mirsal/mirsal/console/particles.js<br>mirsal/tests/js/particle_editor.test.js | 100 | T-026 |
| T-031 Migrate reaction ZIP and Lottie downloads | 6.1-sol-medium | mirsal/mirsal/console/reactions.js<br>mirsal/tests/js/reactions.test.js | 130 | T-026 |
| T-037 Introduce dialog frame and focus lifecycle | luna-6-high | mirsal/mirsal/console/ui-dialog.js<br>mirsal/mirsal/console/app.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/dialog_frame.test.js<br>mirsal/tests/js/console_vm.js | 260 | T-002 |
| T-038 Migrate text prompt dialog frame | 6.1-sol-medium | mirsal/mirsal/console/app.js<br>mirsal/tests/js/dialog_frame.test.js | 100 | T-037 |
| T-039 Migrate confirmation dialog frame | 6.1-sol-medium | mirsal/mirsal/console/app.js<br>mirsal/tests/js/dialog_frame.test.js | 90 | T-037 |
| T-040 Migrate pack-picker dialog frame | 6.1-sol-medium | mirsal/mirsal/console/app.js<br>mirsal/tests/js/dialog_frame.test.js | 140 | T-037 |
| T-041 Migrate retime dialog frame | 6.1-sol-medium | mirsal/mirsal/console/packs.js<br>mirsal/tests/js/dialog_cancel.test.js | 145 | T-037, T-002 |
| T-042 Migrate collection dialog frame | 6.1-sol-medium | mirsal/mirsal/console/packs.js<br>mirsal/tests/js/collection_dialog.test.js | 145 | T-037 |
| T-043 Migrate Telegram connection/status frames | luna-6-high | mirsal/mirsal/console/telegram.js<br>mirsal/tests/js/telegram_dialog.test.js | 180 | T-037 |
| T-044 Introduce details-menu presenter | luna-6-high | mirsal/mirsal/console/ui-menu.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/more_menu.test.js<br>mirsal/tests/js/console_vm.js | 180 | — |
| T-045 Migrate Pack more menu | 6.1-sol-medium | mirsal/mirsal/console/packs.js<br>mirsal/tests/js/pack_delete.test.js | 140 | T-044 |
| T-046 Migrate Studio toolbar more menu | 6.1-sol-medium | mirsal/mirsal/console/studio-core.js<br>mirsal/tests/js/studio_menu.test.js | 140 | T-044 |
| T-047 Migrate reaction preset menu | 6.1-sol-medium | mirsal/mirsal/console/reactions.js<br>mirsal/tests/js/reactions.test.js | 130 | T-044 |
| T-048 Introduce durable inline status presenter | luna-6-high | mirsal/mirsal/console/ui-feedback.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/feedback_message.test.js<br>mirsal/tests/js/console_vm.js | 180 | — |
| T-049 Migrate collection inline validation | 6.1-sol-medium | mirsal/mirsal/console/packs.js<br>mirsal/tests/js/collection_dialog.test.js | 100 | T-048, T-042 |
| T-050 Migrate burst warning presentation | 6.1-sol-medium | mirsal/mirsal/console/particles.js<br>mirsal/tests/js/pack_studio.test.js | 130 | T-048 |
| T-051 Migrate Studio inline stale/health warnings | 6.1-sol-medium | mirsal/mirsal/console/studio-core.js<br>mirsal/tests/js/studio_poll.test.js | 145 | T-048, T-004 |
| T-066 Apply44px targets through semantic control tokens | luna-6-high | mirsal/mirsal/console/studio.css<br>mirsal/mirsal/console/agent.css<br>mirsal/mirsal/console/theme.css | 180 | T-056 |
| T-069 Clarify Studio primary versus recovery actions | luna-6-high | mirsal/mirsal/console/studio-core.js<br>mirsal/mirsal/console/studio-tiles.js<br>mirsal/mirsal/console/studio.css<br>mirsal/tests/js/allow_tiles.test.js | 220 | T-053, T-066 |

Task details and acceptance: [uiux_plan.md](../../../uiux_plan.md). The catalog’s scopes were written for the review snapshot; reconcile before execution. Product choices remain in its Questions for Haitham section.
