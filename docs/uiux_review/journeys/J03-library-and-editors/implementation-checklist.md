# Library, pack, viewer, Edit and Timeline — implementation checklist

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

1. Read current `CLAUDE.md`, then only the relevant area section. Check the shared checkout branch and uncommitted edits.
2. Revalidate the named current functions and contracts. Mark already-fixed findings resolved; do not overwrite the other LLM’s changes. Reaction work must preserve the current preset manifest and emoji-free/no-base64 contract.
3. Use the task dependency graph; shared tasks run once. File/line budgets include tests.
4. Run the narrow checks listed in the canonical task only after its source change. This review adds documents and runs zero code tests.
5. Recheck the affected UI with copied data/providers off; never touch owner port 8770 or paid/send acceptance.
6. Commit only explicit owned paths, after checking branch immediately before commit.

| Task | Model | Files | Line estimate | Depends on |
|---|---|---|---:|---|
| T-014 Introduce grouped-grid presentation helper | luna-6-high | mirsal/mirsal/console/ui-grouped-grid.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/grouped_grid.test.js<br>mirsal/tests/js/console_vm.js | 160 | — |
| T-015 Migrate Library grouped grid | 6.1-sol-medium | mirsal/mirsal/console/library.js<br>mirsal/tests/js/grouped_grid.test.js | 140 | T-014 |
| T-016 Migrate Pack grouped grid | 6.1-sol-medium | mirsal/mirsal/console/packs.js<br>mirsal/tests/js/grouped_grid.test.js | 145 | T-014 |
| T-017 Introduce semantic segmented presenter | luna-6-high | mirsal/mirsal/console/ui-segment.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/segmented.test.js<br>mirsal/tests/js/console_vm.js | 200 | — |
| T-018 Migrate reaction filter segment | 6.1-sol-medium | mirsal/mirsal/console/reactions.js<br>mirsal/tests/js/reactions.test.js | 100 | T-017 |
| T-019 Migrate composer source segment | 6.1-sol-medium | mirsal/mirsal/console/composer.js<br>mirsal/tests/js/prompt_step.test.js | 110 | T-017 |
| T-020 Migrate Studio view segment | 6.1-sol-medium | mirsal/mirsal/console/studio-core.js<br>mirsal/tests/js/studio_menu.test.js | 110 | T-017 |
| T-021 Migrate Pack tabs segment | 6.1-sol-medium | mirsal/mirsal/console/packs.js<br>mirsal/tests/js/pack_delete.test.js | 130 | T-017 |
| T-022 Migrate Settings section navigation | 6.1-sol-medium | mirsal/mirsal/console/settings.js<br>mirsal/tests/js/theme.test.js | 120 | T-017 |
| T-026 Introduce URL/blob download utility | luna-6-high | mirsal/mirsal/console/ui-download.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/ui_download.test.js<br>mirsal/tests/js/console_vm.js | 160 | — |
| T-027 Migrate Timeline blob download | 6.1-sol-medium | mirsal/mirsal/console/animate.js<br>mirsal/tests/js/ui_download.test.js | 110 | T-026 |
| T-028 Migrate video-editor blob download | 6.1-sol-medium | mirsal/mirsal/console/prepare.js<br>mirsal/tests/js/ui_download.test.js | 110 | T-026 |
| T-029 Migrate still-editor PNG download | 6.1-sol-medium | mirsal/mirsal/console/editor.js<br>mirsal/tests/js/ui_download.test.js | 80 | T-026 |
| T-030 Migrate particle Lottie download | 6.1-sol-medium | mirsal/mirsal/console/particles.js<br>mirsal/tests/js/particle_editor.test.js | 100 | T-026 |
| T-031 Migrate reaction ZIP and Lottie downloads | 6.1-sol-medium | mirsal/mirsal/console/reactions.js<br>mirsal/tests/js/reactions.test.js | 130 | T-026 |
| T-056 Define semantic UI spacing/type/status tokens | luna-6-high | mirsal/mirsal/console/studio.css<br>mirsal/mirsal/console/theme.css<br>mirsal/tests/js/theme.test.js | 130 | — |
| T-057 Tokenize diagnostic categories without recoloring | 6.1-sol-medium | mirsal/mirsal/console/studio-tiles.js<br>mirsal/tests/js/cell_op.test.js | 100 | T-056 |
| T-065 Clear the cover badge hit area | 6.1-sol-medium | mirsal/mirsal/console/studio.css | 25 | — |
| T-066 Apply44px targets through semantic control tokens | luna-6-high | mirsal/mirsal/console/studio.css<br>mirsal/mirsal/console/agent.css<br>mirsal/mirsal/console/theme.css | 180 | T-056 |
| T-069 Clarify Studio primary versus recovery actions | luna-6-high | mirsal/mirsal/console/studio-core.js<br>mirsal/mirsal/console/studio-tiles.js<br>mirsal/mirsal/console/studio.css<br>mirsal/tests/js/allow_tiles.test.js | 220 | T-053, T-066 |
| T-075 Expose additive public-pack sticker/reaction counts | luna-6-high | mirsal/mirsal/media/library.py<br>mirsal/mirsal/flow/trending.py<br>mirsal/mirsal/console/app.py<br>mirsal/tests/test_trending.py<br>mirsal/tests/test_library.py<br>docs/api-parts/pack-counts.md | 280 | — |
| T-076 Use public summary counts in Trending labels | 6.1-sol-medium | mirsal/mirsal/console/trending.js<br>mirsal/tests/js/imports_trending.test.js | 80 | T-075 |
| T-077 Keep Home totals consistent with the backend | 6.1-sol-medium | mirsal/mirsal/console/home.js<br>mirsal/tests/js/home.test.js | 100 | T-075 |
| T-083 Record P3 screen changes and API compatibility | luna-6-high | docs/design/03-3-foundations.md<br>docs/design/05-5-per-screen.md<br>docs/design/09-9-every-rejected-picture-carries-its-own-overrid.md<br>docs/reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md<br>docs/api.md<br>docs/api-parts/pack-counts.md | 280 | T-070, T-075 |
| T-084 Document P2 component APIs and caller order | luna-6-high | docs/architecture.md<br>docs/design/03-3-foundations.md<br>docs/design/09-9-every-rejected-picture-carries-its-own-overrid.md | 180 | T-055, T-058 |
| T-085 Document P1 repairs and token ownership | luna-6-high | docs/design/03-3-foundations.md<br>docs/architecture.md<br>docs/engine-and-studio/13-12-ui-observer.md | 200 | T-004, T-056 |
| T-087 Label grouped Library counts without calling reactions stickers | 6.1-sol-medium | mirsal/mirsal/console/library.js<br>mirsal/tests/js/packs_column.test.js | 100 | T-075 |

Task details and acceptance: [uiux_plan.md](../../../uiux_plan.md). The catalog’s scopes were written for the review snapshot; reconcile before execution. Product choices remain in its Questions for Haitham section.
