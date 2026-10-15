# Prompt: implement the UI/UX redesign on branch `redesign-ui-ux`

> Current 2026-10-15 steering: retain the duplicate **choice router** (Open existing / Import again as a new batch), per Haitham after reviewing 5ad67e2d. Do not enforce a fresh cut for every upload. Import the grey-thumbnail implementation from that commit; preserve the redesign structure. See implementation-log.md for current acceptance.

You produced the UI/UX review of Mirsal Builder (`docs/uiux_review/`, `docs/uiux_plan.md`, `tasks.json`). Now implement it. Work **only** on a new branch `redesign-ui-ux`. Since your review, the app gained a lot of functionality, so build on what exists today, not on your old screenshots.

## Set up

1. `git fetch`, then create `redesign-ui-ux` from `origin/handpicked-lottie` (HEAD at the time of writing: `01364004` plus a docs commit). Only `main` and `handpicked-lottie` exist; all other branches were deleted after a containment check.
2. Work in **your own worktree** (`git worktree add <dir> -b redesign-ui-ux origin/handpicked-lottie`). Another session may use the shared checkout `G:/Haitham/VsCode/Mirsal-Builder`: never switch, stash or reset it, and never commit to `handpicked-lottie` or `main`. Run `git branch --show-current` before every commit.
3. Push `redesign-ui-ux` to origin after every phase. No merges, no deployment.

## Read first (lean)

`CLAUDE.md` (the rules are binding, especially 6, 10, 11 and 12, and the test budget), `HANDOFF.md`, `plan.md`, **`docs/uiux_review/plan-review.md`** (the reconciliation of your review with today's code; it overrides `revalidation.md` and the old task statuses), then `docs/design.md` and the section files you need before any CSS or markup change. For reactions read `docs/reaction/15-*.md`, `16-*.md` and `17-*.md` (the two styles: Emoji style's preset library, and Lottie style's Particular-style groups). For the Studio size controls read `docs/engine-and-studio/09-engine.md` ("Resize") and `docs/size-position-lottie-proposal.md`. Use `docs/uiux_plan.md` and `tasks.json` as a searchable catalog; don't load them whole.

## What is already true (do not redo, do not undo)

- The repair batch T-002–T-004, T-065, T-072–T-074 and T-086 is in the code; only browser acceptance is outstanding. **T-001 is superseded**: Keep approved size is retired. The Studio's Motion row is now `[✓] Resize · Size − 100% +`. Resize off = one uniform scale; Resize on = hot spot matched to the approved still (Haitham approved this on 2026-10-15). Each animated tile has a **frame editor** (`vzCard`: one frame as a PNG, drag/arrows/Centre for Position, Grid on/off, frame scrubber, Apply/Cancel), backed by `GET /anim_preview` (one frame) and the native routes `POST /api/generations/{id}/resize` and `/position`. Keep these contracts and behaviours.
- Lottie style's editor already uses `<details>` groups (Emitter, Particle, Physics, Morph, Aux system) with a closed-group summary, a preset row and a seed re-roll. Keep that structure; style it, don't flatten it.
- The two reaction export contracts differ, so never merge their rules. Emoji style exports emoji-free preset Lottie (`{motion}_{NN}.json`, one external `emoji` asset, no base64). Lottie style exports a self-contained composition that embeds every source.
- Import into a batch: the grid-mismatch dialog ("Cut it as R×C anyway", `grid_ok=1`) and the duplicate dialog ("Again into G###" / "As a new batch", `again=1`) exist.

## Do, in this order (one commit per phase, area docs in the same commit)

1. **Unfinished code Claude left you (do these first):**
   a. Rewrite `mirsal/tests/js/size_preview.test.js` for the Resize box and frame editor (it still tests the removed `gkeepsize`/`keepSizeBtn`): staged Resize toggle → preview with `resize=0|1`; batch Size → `video_size` on Apply only; sticker editor → one `position` POST on Apply with `offset` + `scale`; Cancel sends nothing.
   b. Fix the two stale tests in `mirsal/tests/test_particle_set.py`. `test_a_sparse_sheet_…` builds `out / f"G{gid:03d}"` by hand; use `pl.gen_dir`. `test_the_kind_is_only_written_…` looks the batch up in `pl.history` and finds nothing; find out why and fix the test, or fix the code if the code is wrong.
   c. Share one presentation between `egCard` (edge test) and `vzCard` (frame editor) (T-012/T-033 re-scoped). Keep their endpoints and units distinct.
   d. `engine/video.window_box` hard-codes 512; pass `cfg.size`.
   e. The general import dialog (`imports.js` `result()`) still only "Opens the existing batch" on a duplicate; offer "Import again as a new batch" (`again=1&as_new=1`) there too.
2. **Browser acceptance** of plan-review.md checks 1–4, on your own server (`serve --port <not 8770>`), a **copy** of `out/` (`MIRSAL_OUT`), `MIRSAL_NO_REAL_CLI=1`, `MIRSAL_LLM_PROVIDER=none`. Reopen a repair only for a failure you reproduce. Record the evidence in `docs/uiux_review/implementation-log.md`.
3. **T-056 semantic tokens** (8 px spacing grid, five type roles, status colour pairs, radii, elevation, focus ring, motion durations 150–250 ms with `prefers-reduced-motion`), reusing the existing tokens in `theme.css`/`studio.css`. Then **T-066**: 44 px targets everywhere, including the frame editor's buttons, `.rx-x`/`.rx-vsel` and phone.
4. **J1 Studio as the visual reference** (T-068/T-069): grouped batch header, one clear primary action per stage, recovery and secondary actions in a menu, consistent segments and sheets, and the Motion row on tokens. Check desktop and phone, dark and light. A before/after must show a real improvement in hierarchy, grouping and density, not just new colours.
5. **plan.md items 1, 2 and 4 together with T-071** (saved-set card: counts on hover, cost only when spent, Duplicate/Rename/Delete in a ⋯ menu, "Manage stickers" disclosure, one Advanced section that summarises its values). Then **item 5** (burst row without the preset name), **item 6** (pack view without tabs: stickers grid first, then reactions; retire `PKTAB`/`pktab` with `retired` entries in `mirsal/tests/data/ui_baseline.json`), and **item 7** (Open in Studio on Library pack cards). Then **item 8** (Open and save) and **item 9** (`erosion_px` on `ParticleParams`, default 0, a morphological erosion on each sprite's alpha after keying and before despill, plus a slider; rule 6: the backend reads it).
6. **The other journeys** through the same system: J2 Chat, J3 Library/pack/viewer/editors, J6 rejection/override states (every rejected picture keeps its visible, reversible "Use it anyway"; rule 10), J7 Home/welcome, J8 Settings/Help/Trending, J9 export dialogs; J10 theme and J11 phone acceptance for each. Reaction tasks (J4/J5: T-007, T-018, T-024, T-025, T-031, T-034, T-035, T-047, T-070) only after you re-scope them against today's two-style screen.
7. **Optional, Lottie style (Haitham allowed it on this branch only):** the parts of proposal D that were not built. Pre-run (start mid-burst), Time scale, a sticker-silhouette emitter (born on the origin Lottie's alpha edge, if it can be measured without rasterizing at runtime; otherwise skip and say why), and blend modes (`bm`) only where lottie-web's SVG renderer supports them. Every new field must be off by default and draw from the second generator (`default_rng([seed, 0x15])`), so existing bursts keep their bytes. Prove that with a before/after trajectory comparison, as `tests/test_lottie_reactions.ParticularTests` does.

## Boundaries

- About 90% of the information architecture stays: shell, rail, routes, JSON contracts, action names (a removed action needs a `retired` entry, `tests/test_ui_inventory.py` stays green), owner-only operations, the engine as the authority (rule 11: no logic only in the browser).
- No paid calls, no Telegram sends, no CDN. Use your own port and copied data, never 8770.
- Tests: run one narrowest suite per change (`mirsal test focused` / `area <module>`, the node test for the touched script); no tests for docs; never the full discovery.
- Docs are part of every change: the area section file, `docs/design/*`, the implementation log, task statuses in `tasks.json`, and the matching `plan.md` step removed once it is implemented **and** accepted.
- Commit explicit paths only; never `git add -A`; never `.env`, tokens, `opencode.json` or `mirsal/telegram-id.md`.

## Finish with

What you implemented (per phase, with commit ids and test evidence), what was accepted in the browser, what remains in priority order, and the decisions that only Haitham can make (still open: pack tabs vs item 6 if you find a reason to doubt it, the "Reaction effects" wording used for two workflows (F-31), and the cloud pricing copy).
