# HANDOFF — 2026-10-15 (final; pushed and clean)

## Branch map

```
origin/main @ 0167761b  (stable base — merged implementation)
origin/redesign-ui-ux @ 95d4b4a4  (checkout: G:/Haitham/VsCode/Mirsal-Builder-redesign)
```

Main has 44 uncommitted runtime files (`mirsal/out/*`, `Custom_emojis/*`) — never commit these.
Redesign is fully clean. Dead `.worktrees/redesign-ui-ux` folder deleted.

## What main carries (all session work)

| commit | what |
|---|---|
| 5ad67e2d | No duplicate check for manual uploads (same file = fresh batch; only retry finishes an old batch). Grey silhouette from the animation's first visible frame — in Download .zip AND Export-to-collection thumbnails. |
| 9194bfc5 + 47817ab6 | Per-tile Size/X/Y sliders (readout on input, one `/position` POST 500ms after release, Reset clears). |
| 2743bd7f → 09d62c8c | Reaction bridge → 3-tab merge (`#/reactions`: Emoji Style \| Lottie Style \| Packs) → same tabs in Library › Reactions. One tab state (`rx.tab`). |
| cdeae419 | 409-busy retry (`postBusy`, 12×1s) — slider/frame-editor sends survive a running cut. |
| 94bfb645 | All stale js tests repaired (372 pass, 0 fail); two `test_particle_set` test bugs fixed (gen_dir path, pack-nested history lookup). |
| dc8c0c6b | `GUIDE.md` visual interview guide. |

Tests on main: js 372/0, python narrow (imports + collection + library + ui_inventory + particle_cut) green.
Redesign: js 388/0, same python gates green.

## What redesign carries (beyond main)

- Imports: duplicate-choice dialogs kept (`again`, "Again into / As a new batch") — deliberate divergence from main per Haitham. Never reconcile without Haitham.
- Slider WIP committed (57c8850b), Adjust toggle (699a49a1), busy-retry (825f4dcc), stale-test repairs (eb0c4f83).
- Reaction tabs ported (42a93282), plan/handoff/brief all record completion.
- Grey .zip thumbnails already there (a439eec4).

## Still open (see plan.md for the full list)

1. **Interactive browser acceptance** — tabs on both screens, sliders, frame editor, dark/light, ≤760 px. Needs a human or browser agent.
2. **UI/UX redesign backlog** — `plan.md` items 1–9 (reaction/pack cleanup), T-056 tokens → T-066 44px targets → J1 Studio visual reference, journeys J2–J11. The visual redesign has not started.
3. **Optional Lottie fields** — Pre-run, Time scale, sticker-silhouette emitter, blend modes (need a go-ahead).

## How to pick up

- Read `plan.md` (main) for the ordered remaining work. Read `docs/uiux_review/main-agent-brief-2026-10-15.md` (redesign) for the redesign lane status.
- Tests: narrowest only (`mirsal test fast|focused|area <module>`). Full `unittest discover` retired.
- Server: `python -m mirsal serve` from `mirsal/.venv`. Owner runs :8770; use your own `--port` with `MIRSAL_OUT=<copy>`.
- Providers off for checks: `MIRSAL_NO_REAL_CLI=1`, `MIRSAL_LLM_PROVIDER=none`.
