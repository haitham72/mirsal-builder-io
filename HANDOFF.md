# HANDOFF — 2026-10-15

## Latest user fixes (2026-10-15)

Implementation checkpoint: `1980c857` on `redesign-ui-ux`, pushed. Documentation follow-up synchronizes the area docs, README, plan and review status.

- Lottie selection redraws the active screen; the player and thumbnails mount within that screen. Browser verified saved-file switching and advancing playback in Library and Create, including returning to Create.
- Create > + New > From a photo asks Sticker / Emojis; Sticker keeps the cutout/editor, Emojis imports an image sheet into Studio. From a video imports a video sheet into Studio.
- All sheet import dialogs offer Auto detect / 2×2 / 3×3. Manual grids override detection; a different destination grid starts a separate batch. In-batch video mismatches can also start a batch using the detected grid. Duplicate dialogs stay.
- Focused imports pass (automatic/manual image grid, separate batch preservation, standalone video, existing in-batch image/video). Node suite passes (389 checks). Broader Python console checks have one existing stale assertion for removed `data-act=rxedit`; do not describe that suite as green.
- Browser imports on temporary storage finished READY: automatic 2×2 image and a 3×3 video manually cut as 2×2. User server: http://127.0.0.1:8796/.

## Branch map

```
origin/main @ 0167761b  (stable base — merged implementation)
redesign-ui-ux: implementation checkpoint 1980c857
active checkout: G:/Haitham/VsCode/Mirsal-Builder
```

The earlier main-checkout handoff recorded 44 runtime files (`mirsal/out/*`, `Custom_emojis/*`); do not commit runtime files. This session's active checkout is on `redesign-ui-ux`. Dead `.worktrees/redesign-ui-ux` folder was deleted previously.

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
Redesign's latest results are recorded above; historical Python gates do not supersede the current stale console assertion.

## What redesign carries (beyond main)

- Imports: duplicate-choice dialogs kept (`again`, "Again into / As a new batch") — deliberate divergence from main per Haitham. Never reconcile without Haitham.
- Slider WIP committed (57c8850b), Adjust toggle (699a49a1), busy-retry (825f4dcc), stale-test repairs (eb0c4f83).
- Reaction tabs ported (42a93282), plan/handoff/brief all record completion.
- Grey .zip thumbnails already there (a439eec4).

## Still open (see plan.md for the full list)

1. **Remaining browser acceptance** — full slider/frame-editor sweep, Emoji/Packs tab transitions on both screens, theme/phone matrix and extended states. Lottie selection/playback and Create sheet imports passed targeted browser checks.
2. **Engineering follow-ups and visual review** — see `plan.md` and `docs/uiux_review/current-status.md`. The visual redesign and original reaction/pack requirements are implemented; broader shared-code extraction and owner visual review remain open.
3. **Optional Lottie fields** — Pre-run, Time scale, sticker-silhouette emitter, blend modes (need a go-ahead).

## How to pick up

- Read `plan.md` in the active checkout for remaining work, then `docs/uiux_review/main-agent-brief-2026-10-15.md` for the redesign lane status. Check the branch before edits or commits.
- Tests: narrowest only (`mirsal test fast|focused|area <module>`). Full `unittest discover` retired.
- Server: `python -m mirsal serve` from `mirsal/.venv`. Owner runs :8770; use your own `--port` with `MIRSAL_OUT=<copy>`.
- Providers off for checks: `MIRSAL_NO_REAL_CLI=1`, `MIRSAL_LLM_PROVIDER=none`.
