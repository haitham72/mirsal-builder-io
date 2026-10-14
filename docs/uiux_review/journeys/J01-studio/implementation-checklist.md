# Create a sticker set in Studio — implementation checklist

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

1. Read current `CLAUDE.md`, then only the relevant area section. Check the shared checkout branch and uncommitted edits.
2. Revalidate the named current functions and contracts. Mark already-fixed findings resolved; do not overwrite the other LLM’s changes. Reaction work must preserve the current preset manifest and emoji-free/no-base64 contract.
3. Use the task dependency graph; shared tasks run once. File/line budgets include tests.
4. Run the narrow checks listed in the canonical task only after its source change. This review adds documents and runs zero code tests.
5. Recheck the affected UI with copied data/providers off; never touch owner port 8770 or paid/send acceptance.
6. Commit only explicit owned paths, after checking branch immediately before commit.

| Task | Model | Files | Line estimate | Depends on |
|---|---|---|---:|---|
| T-001 Restore staged Keep approved size | 6.1-sol-medium | mirsal/mirsal/console/studio-core.js<br>mirsal/tests/js/size_preview.test.js | 100 | — |
| T-003 Coalesce duplicate queue clock redraws | 6.1-sol-medium | mirsal/mirsal/console/live.js<br>mirsal/tests/js/queue_clock.test.js | 80 | — |
| T-004 Serialize Studio refreshes and retain force requests | luna-6-high | mirsal/mirsal/console/studio-core.js<br>mirsal/tests/js/studio_poll.test.js | 170 | — |
| T-005 Introduce resource watcher lifecycle | luna-6-high | mirsal/mirsal/console/ui-watch.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/ui_watch.test.js<br>mirsal/tests/js/console_vm.js | 230 | T-004 |
| T-006 Migrate collection export watcher | 6.1-sol-medium | mirsal/mirsal/console/packs.js<br>mirsal/tests/js/collection_watch.test.js | 140 | T-005 |
| T-007 Migrate reaction batch watcher | 6.1-sol-medium | mirsal/mirsal/console/reactions.js<br>mirsal/tests/js/reactions.test.js | 140 | T-005 |
| T-008 Migrate effect-run watcher | 6.1-sol-medium | mirsal/mirsal/console/effects.js<br>mirsal/tests/js/effects_core.test.js | 140 | T-005 |
| T-009 Migrate saved-set drawing watcher | 6.1-sol-medium | mirsal/mirsal/console/particles.js<br>mirsal/tests/js/particle_editor.test.js | 145 | T-005 |
| T-010 Migrate background job reads | luna-6-high | mirsal/mirsal/console/live.js<br>mirsal/tests/js/live_watch.test.js | 200 | T-005 |
| T-011 Introduce shared test-card presenter | luna-6-high | mirsal/mirsal/console/ui-testcard.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/ui_testcard.test.js<br>mirsal/tests/js/console_vm.js | 230 | T-001 |
| T-012 Migrate video-size test card | 6.1-sol-medium | mirsal/mirsal/console/studio-core.js<br>mirsal/tests/js/size_preview.test.js | 140 | T-011, T-001 |
| T-013 Migrate edge test card | 6.1-sol-medium | mirsal/mirsal/console/live.js<br>mirsal/tests/js/edge_preview.test.js | 140 | T-011 |
| T-032 Introduce latest-result preview session | luna-6-high | mirsal/mirsal/console/ui-preview.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/preview_session.test.js<br>mirsal/tests/js/console_vm.js | 240 | — |
| T-033 Migrate size preview request lifecycle | luna-6-high | mirsal/mirsal/console/studio-core.js<br>mirsal/tests/js/size_preview.test.js | 180 | T-032, T-012 |
| T-034 Migrate emoji editor and hover preview lifecycle | luna-6-high | mirsal/mirsal/console/reactions.js<br>mirsal/tests/js/reactions.test.js | 220 | T-032 |
| T-035 Migrate preset-card preview cache | 6.1-sol-medium | mirsal/mirsal/console/reactions.js<br>mirsal/tests/js/reactions.test.js | 145 | T-032, T-034 |
| T-036 Migrate saved-set burst preview lifecycle | luna-6-high | mirsal/mirsal/console/particles.js<br>mirsal/tests/js/pack_studio.test.js | 220 | T-032 |
| T-056 Define semantic UI spacing/type/status tokens | luna-6-high | mirsal/mirsal/console/studio.css<br>mirsal/mirsal/console/theme.css<br>mirsal/tests/js/theme.test.js | 130 | — |
| T-057 Tokenize diagnostic categories without recoloring | 6.1-sol-medium | mirsal/mirsal/console/studio-tiles.js<br>mirsal/tests/js/cell_op.test.js | 100 | T-056 |
| T-058 Replace unconditional edge synchronization clock | luna-6-high | mirsal/mirsal/console/live.js<br>mirsal/mirsal/console/studio-core.js<br>mirsal/tests/js/edge_preview.test.js | 190 | T-013, T-004 |
| T-066 Apply44px targets through semantic control tokens | luna-6-high | mirsal/mirsal/console/studio.css<br>mirsal/mirsal/console/agent.css<br>mirsal/mirsal/console/theme.css | 180 | T-056 |
| T-067 Present Apply/Cancel tests as responsive sheets | luna-6-high | mirsal/mirsal/console/ui-testcard.js<br>mirsal/mirsal/console/studio.css<br>mirsal/tests/js/ui_testcard.test.js | 220 | T-012, T-013 |
| T-068 Group Studio composer and prompt metadata | luna-6-high | mirsal/mirsal/console/composer.js<br>mirsal/mirsal/console/studio-prompt.js<br>mirsal/mirsal/console/studio-core.js<br>mirsal/mirsal/console/studio.css<br>mirsal/tests/js/prompt_step.test.js | 280 | T-056, T-066 |
| T-069 Clarify Studio primary versus recovery actions | luna-6-high | mirsal/mirsal/console/studio-core.js<br>mirsal/mirsal/console/studio-tiles.js<br>mirsal/mirsal/console/studio.css<br>mirsal/tests/js/allow_tiles.test.js | 220 | T-053, T-066 |
| T-083 Record P3 screen changes and API compatibility | luna-6-high | docs/design/03-3-foundations.md<br>docs/design/05-5-per-screen.md<br>docs/design/09-9-every-rejected-picture-carries-its-own-overrid.md<br>docs/reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md<br>docs/api.md<br>docs/api-parts/pack-counts.md | 280 | T-070, T-075 |
| T-085 Document P1 repairs and token ownership | luna-6-high | docs/design/03-3-foundations.md<br>docs/architecture.md<br>docs/engine-and-studio/13-12-ui-observer.md | 200 | T-004, T-056 |

Task details and acceptance: [uiux_plan.md](../../../uiux_plan.md). The catalog’s scopes were written for the review snapshot; reconcile before execution. Product choices remain in its Questions for Haitham section.
