# HANDOFF - session save point, 2026-10-20 (afternoon)

Checkout `G:/Haitham/VsCode/Mirsal-Builder`, branch `redesign-ui-ux` (main stays
`0167761b`, never merge without Haitham asking). Haitham said "do not stop until
all planned are implemented", then asked to stop here and hand over to another
LLM. Everything below is committed and pushed unless it says otherwise.

## Latest continuation

- `e544a906` committed and pushed: Studio scrolling settings/action footer,
  composer preservation and Batches regression tests (4 pass).
- UX-10 phone Chat completed: Style and options disclosure, wrapping title,
  visible model status. Chat stage tests: 8 pass. Synthetic 30-message browser
  check at 390×720 in light/dark preserved draft and scroll; desktop controls
  remained visible. Fixture-specific agent lookup returned 404; fallback status
  remained visible. No live-job polling verification.
- Task-owned server :8796 (exec session 3670) uses isolated
  `output/playwright/studio-out`, providers disabled and DB writes off.
  Local screenshots/check scripts are untracked in `output/playwright/` and
  `.playwright-cli/`; browser session `studio-finish`.
- Next: loaded-state/keyboard/roles sweep and scoped structural work in plan.md.
  Owner decisions and baseline agent failures remain open.

## Done this session (commits on origin/redesign-ui-ux)

- `0e1571d7` UX-06 Test-workspace badge, UX-08 reaction ownership heading, UX-11 owner names.
- `b677af07` UX-03 keyboard tiles, UX-04 editor control names, UX-05 frame card focus/Escape.
- `83b2e9ea` UX-01 phone editors and Save sticker, UX-09 watch-folder rows.
- **Save-point commit (this one)**: Studio left creation panel + Batches drawer
  (plan item 1, also UX-07's recovery entry). See "Studio left panel" below.

What each fix does, where, and its test: `docs/design/16-app-audit-fixes-2026-10-20.md`.
All confirmed audit defects (UX-01..UX-09, UX-11) are now fixed.

## Studio left panel (implemented, needs Haitham's visual review)

Plan: `docs/design/15-studio-creation-sidebar-plan.md` (its "Implemented" section).
- On `#/studio` the second column is the creation panel (352px, 320px <1180px):
  the ONE New request composer (`#cpwrap`) is moved there (`composer.js`
  `studioCol`, `cpHost`, `cpStash`/`CPKEEP` keeps the node, so the draft
  survives leaving and returning). `body.studio-split`. No second form, one `#prompt`.
- `studio-core.js` RENDER.generate draws a top bar: **Creation settings** (only
  <=900px, opens the existing col2 drawer) and **Batches**; it skips the legacy
  prompt row when the composer exists.
- Earlier batches and the open project's map (projmap.js) moved into the
  **Batches drawer** `#bdrawer` (`live.js` `bdEl`/`ACT.bdopen`/`bdClose`,
  `histHost()`); non-modal, focus to first control, Escape/Close returns focus,
  opening a batch (`hopen`/`pmopen`) closes it; the breadcrumb project link opens it.
- `app.js`: clicks inside the composer no longer close the narrow col2 drawer
  (except Generate); `#c2tog` is labelled "Creation settings" on the Studio.
- Verified on a copied workspace (port 8795, providers off): regions at
  1440/1024/760/390, draft kept across Library and back, drawer Escape/focus.
  Screenshots are only in the scratchpad (not committed).
- **Known gaps to pick up**:
  1. In Options (narrow panel) the Creative/Predefined segment (`.gseg.cp-act`)
     renders as an empty pill with `innerText` "" — investigate (maybe pre-existing).
  2. Follow-up completed: Generate prompt and existing draft/import actions now sit
     in a footer below independently scrolling settings.
  3. Added `studio_panel.test.js`: composer node/draft preservation, drawer visibility,
     focus restoration and history host routing. Together with composer_visibility: 4 pass.
  4. Empty-workspace light/dark checks passed at 1440/1024/760/390, 720px high,
     on isolated :8796 with providers off. Creative/Predefined worked in all eight
     layouts with Options open; the empty pill was not reproduced. Screenshots in
     `output/playwright/studio-*.png` (local only). Loaded artwork and busy/error
     acceptance remain; final visual verdict is Haitham's.

## Remaining plan (see plan.md)

F-31 wording and W18 enhancer price gate (owner
calls, never implemented); unverified states sweep; shared-code/router
refactors (AR-01..04, T-024/025/031/034/035); optional Lottie items; agent
baseline 4 failures / 9 errors.

## Running tools / paths

- A task test server may still be running on **http://127.0.0.1:8795/** with
  `MIRSAL_OUT` = scratch copy (providers off). Safe to kill. Never touch the
  real-data server **:8770**.
- Playwright MCP writes `.playwright-mcp/` in the repo root; it is git-ignored.
- Hash-only `goto` does not reload the page: call `page.reload()` after edits.
- `mirsal-db` Postgres on 5434; if it exits, writes stop until `serve` restarts.

## Unowned edits - leave untouched and unstaged

- Deletions: `Recovered particles L002.lottie (2).json`, `smiling_face.json`.
- Runtime writes: `mirsal/out/G154-generic_test-20261015T054257/preview/anim-S1.png`,
  `mirsal/out/higgsfield_models.json`, `mirsal/out/model_calls.jsonl`,
  `mirsal/out/sessions/S020.json`.
- Explicit-path commits only, check `git branch --show-current` first. No merge,
  deployment, paid call, Telegram or collection send.

## Tests last run

`node --test mirsal/tests/js/*.test.js` 416/416 pass; `python -m unittest
tests.test_ui_inventory` OK (run from `mirsal/` with `.venv`). Full Python
discovery is retired; not run.
