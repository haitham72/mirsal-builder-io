# Pack reactions, motion and standalone effects — implementation checklist

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
| T-017 Introduce semantic segmented presenter | luna-6-high | mirsal/mirsal/console/ui-segment.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/segmented.test.js<br>mirsal/tests/js/console_vm.js | 200 | — |
| T-018 Migrate reaction filter segment | 6.1-sol-medium | mirsal/mirsal/console/reactions.js<br>mirsal/tests/js/reactions.test.js | 100 | T-017 |
| T-019 Migrate composer source segment | 6.1-sol-medium | mirsal/mirsal/console/composer.js<br>mirsal/tests/js/prompt_step.test.js | 110 | T-017 |
| T-020 Migrate Studio view segment | 6.1-sol-medium | mirsal/mirsal/console/studio-core.js<br>mirsal/tests/js/studio_menu.test.js | 110 | T-017 |
| T-021 Migrate Pack tabs segment | 6.1-sol-medium | mirsal/mirsal/console/packs.js<br>mirsal/tests/js/pack_delete.test.js | 130 | T-017 |
| T-022 Migrate Settings section navigation | 6.1-sol-medium | mirsal/mirsal/console/settings.js<br>mirsal/tests/js/theme.test.js | 120 | T-017 |
| T-023 Introduce range-field presenter | luna-6-high | mirsal/mirsal/console/ui-range.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/range_field.test.js<br>mirsal/tests/js/console_vm.js | 200 | — |
| T-024 Migrate saved-set burst sliders | 6.1-sol-medium | mirsal/mirsal/console/particles.js<br>mirsal/tests/js/particle_editor.test.js | 110 | T-023 |
| T-025 Migrate emoji reaction sliders | 6.1-sol-medium | mirsal/mirsal/console/reactions.js<br>mirsal/tests/js/reactions.test.js | 120 | T-023 |
| T-032 Introduce latest-result preview session | luna-6-high | mirsal/mirsal/console/ui-preview.js<br>mirsal/mirsal/console/index.html<br>mirsal/tests/js/preview_session.test.js<br>mirsal/tests/js/console_vm.js | 240 | — |
| T-033 Migrate size preview request lifecycle | luna-6-high | mirsal/mirsal/console/studio-core.js<br>mirsal/tests/js/size_preview.test.js | 180 | T-032, T-012 |
| T-034 Migrate emoji editor and hover preview lifecycle | luna-6-high | mirsal/mirsal/console/reactions.js<br>mirsal/tests/js/reactions.test.js | 220 | T-032 |
| T-035 Migrate preset-card preview cache | 6.1-sol-medium | mirsal/mirsal/console/reactions.js<br>mirsal/tests/js/reactions.test.js | 145 | T-032, T-034 |
| T-036 Migrate saved-set burst preview lifecycle | luna-6-high | mirsal/mirsal/console/particles.js<br>mirsal/tests/js/pack_studio.test.js | 220 | T-032 |
| T-056 Define semantic UI spacing/type/status tokens | luna-6-high | mirsal/mirsal/console/studio.css<br>mirsal/mirsal/console/theme.css<br>mirsal/tests/js/theme.test.js | 130 | — |
| T-057 Tokenize diagnostic categories without recoloring | 6.1-sol-medium | mirsal/mirsal/console/studio-tiles.js<br>mirsal/tests/js/cell_op.test.js | 100 | T-056 |
| T-070 Disclose advanced emoji motion and group batch actions | luna-6-high | mirsal/mirsal/console/reactions.js<br>mirsal/mirsal/console/studio.css<br>mirsal/tests/js/reactions.test.js | 260 | T-025, T-066 |
| T-071 Apply the already-tracked saved-set disclosure cleanup | luna-6-high | mirsal/mirsal/console/particles.js<br>mirsal/mirsal/console/packs.js<br>mirsal/mirsal/console/studio.css<br>mirsal/tests/js/particle_editor.test.js | 300 | T-024, T-066 |
| T-083 Record P3 screen changes and API compatibility | luna-6-high | docs/design/03-3-foundations.md<br>docs/design/05-5-per-screen.md<br>docs/design/09-9-every-rejected-picture-carries-its-own-overrid.md<br>docs/reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md<br>docs/api.md<br>docs/api-parts/pack-counts.md | 280 | T-070, T-075 |
| T-085 Document P1 repairs and token ownership | luna-6-high | docs/design/03-3-foundations.md<br>docs/architecture.md<br>docs/engine-and-studio/13-12-ui-observer.md | 200 | T-004, T-056 |

Task details and acceptance: [uiux_plan.md](../../../uiux_plan.md). The catalog’s scopes were written for the review snapshot; reconcile before execution. Product choices remain in its Questions for Haitham section.
