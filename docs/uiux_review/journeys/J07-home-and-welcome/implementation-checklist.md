# Home and welcome — implementation checklist

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

1. Read current `CLAUDE.md`, then only the relevant area section. Check the shared checkout branch and uncommitted edits.
2. Revalidate the named current functions and contracts. Mark already-fixed findings resolved; do not overwrite the other LLM’s changes. Reaction work must preserve the current preset manifest and emoji-free/no-base64 contract.
3. Use the task dependency graph; shared tasks run once. File/line budgets include tests.
4. Run the narrow checks listed in the canonical task only after its source change. This review adds documents and runs zero code tests.
5. Recheck the affected UI with copied data/providers off; never touch owner port 8770 or paid/send acceptance.
6. Commit only explicit owned paths, after checking branch immediately before commit.

| Task | Model | Files | Line estimate | Depends on |
|---|---|---|---:|---|
| T-056 Define semantic UI spacing/type/status tokens | luna-6-high | mirsal/mirsal/console/studio.css<br>mirsal/mirsal/console/theme.css<br>mirsal/tests/js/theme.test.js | 130 | — |
| T-057 Tokenize diagnostic categories without recoloring | 6.1-sol-medium | mirsal/mirsal/console/studio-tiles.js<br>mirsal/tests/js/cell_op.test.js | 100 | T-056 |
| T-074 Give welcome slides their own readable surface palette | luna-6-high | mirsal/mirsal/console/studio.css<br>mirsal/mirsal/console/theme.css | 90 | T-056 |
| T-075 Expose additive public-pack sticker/reaction counts | luna-6-high | mirsal/mirsal/media/library.py<br>mirsal/mirsal/flow/trending.py<br>mirsal/mirsal/console/app.py<br>mirsal/tests/test_trending.py<br>mirsal/tests/test_library.py<br>docs/api-parts/pack-counts.md | 280 | — |
| T-076 Use public summary counts in Trending labels | 6.1-sol-medium | mirsal/mirsal/console/trending.js<br>mirsal/tests/js/imports_trending.test.js | 80 | T-075 |
| T-077 Keep Home totals consistent with the backend | 6.1-sol-medium | mirsal/mirsal/console/home.js<br>mirsal/tests/js/home.test.js | 100 | T-075 |
| T-083 Record P3 screen changes and API compatibility | luna-6-high | docs/design/03-3-foundations.md<br>docs/design/05-5-per-screen.md<br>docs/design/09-9-every-rejected-picture-carries-its-own-overrid.md<br>docs/reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md<br>docs/api.md<br>docs/api-parts/pack-counts.md | 280 | T-070, T-075 |
| T-085 Document P1 repairs and token ownership | luna-6-high | docs/design/03-3-foundations.md<br>docs/architecture.md<br>docs/engine-and-studio/13-12-ui-observer.md | 200 | T-004, T-056 |
| T-087 Label grouped Library counts without calling reactions stickers | 6.1-sol-medium | mirsal/mirsal/console/library.js<br>mirsal/tests/js/packs_column.test.js | 100 | T-075 |

Task details and acceptance: [uiux_plan.md](../../../uiux_plan.md). The catalog’s scopes were written for the review snapshot; reconcile before execution. Product choices remain in its Questions for Haitham section.
