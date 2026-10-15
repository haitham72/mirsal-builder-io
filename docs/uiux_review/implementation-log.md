# UI/UX fixes — execution record (branch `uiux-fixes`, from `ui/ux-review` @ `7f7f930d`)

Worktree `…/Temp/opencode/uiux-fixes`; the shared checkout was never switched, stashed, or reset.
Scope rule: current `CLAUDE.md` + `revalidation.md` take precedence over historical
screenshot scores/line numbers; reaction/grid contracts preserved; no paid calls.

## Implemented

| ID | Finding | Change | Tests |
|---|---|---|---|
| T-001 | F-01 staged Keep approved size | `studio-core.js`: deleted the late immediate `ACT.gkeepsize` POST; staged handler is the single definition | `size_preview.test.js` 2 pass; `test_an_action_is_not_silently_replaced_by_a_later_script` FAIL→PASS |
| T-002 | F-06 retime promise | `app.js`: `dlg(html,{onDismiss})`, `closeDlg(reason)`, `dlgForget()`; `packs.js`: settle-once `retimeAsk`, `rtans` clears dismissal then closes `'answer'` | `dialog_cancel.test.js` 4 pass (behavioral) |
| T-003 | F-05 queue clocks | `live.js`: removed duplicate bare 1000-ms redraw; retained `data-lvt` interval byte for byte | `queue_clock.test.js` 1 pass |
| T-004 | F-05 Studio refresh | `studio-core.js`: `tickBusy`/`tickForce`, hidden-tab interval skip, `finally` release + one queued force; cadence unchanged | `studio_poll.test.js` 2 pass |
| T-065 | F-24 badge hit area | `studio.css`: `#pkgrid .cell .badge2{pointer-events:none}` | `surface_fixes.test.js` |
| T-086 | F-36 phone viewer | `studio.css`: ≤760px viewer grid, metadata row 1 cols 1–2, controls row 2, `max-height:calc(100dvh - 24px)` | `surface_fixes.test.js` |
| T-074 | F-30 welcome contrast | `studio.css`+`theme.css`: `--wl-ink:#123546`/`--wl-ink2:#345969` both themes, slide-only use; `.wl-d` 44px targets, 5px glyph | `surface_fixes.test.js` (3 pass total) |
| T-072 | F-26/F-27 settings bar | `settings.js`: `SET_SECTIONS` registry + `setNavHtml`/`setNavSync`; `auth/tickets/trash.js` rebuild after mounting | `settings_nav.test.js` 3 pass |
| T-073 | F-28 Help semantics | `support.js`: conv/queue/FAQ title rows are native `button.crow`; `studio.css`: `button.crow` 44px rule | `support.test.js` 6 pass |

Docs in the same step: `design/05` (Pack/Settings/Help), `design/10` (welcome),
10 `Implemented` markers across J01/J03/J07/J08/J09/J10/J11 journey files.

## Test evidence

- New/affected node suites: 51/51 pass (`auth, tickets, trash, support, welcome,
  pack_delete, theme, settings_nav, surface_fixes, size_preview, dialog_cancel,
  queue_clock, studio_poll`).
- `python -m unittest tests.test_ui_inventory`: 4 tests OK (no action/screen/route lost).
- Full node suite: 341 pass / 9 fail — the 9 failures are byte-identical on the
  pristine checkout (pre-existing: `cpGrid` stub gap in `prompt_step`, stale
  markup expectations in `cell_op`/`home`, etc.); my 9 new tests all pass.
- `python -m tests.test_js`: 14 errors are a pre-existing harness encoding issue
  (`UnicodeDecodeError` cp1252 in `console_sources()`), identical on pristine.
- `node --check`: all 9 changed console scripts parse.

## Risks / still unknown

- No real-browser pass yet in this environment (no browser driver here): native
  hit-testing, dark/light paint, and ≤760px layout verified by source + unit
  level only; needs Haitham's browser look or a Playwright session.
- T-066 (44px via tokens) deferred: needs T-056 token vocabulary first; the
  per-fix 44px floors above do not replace it.
- T-005+ watcher migration, T-056+ token work, remaining journey redesigns:
  intentionally out of scope for this batch.

## Remaining owner decisions (unchanged)

Reaction labels, pack tabs, cloud pricing (`docs/uiux_plan.md` Questions for Haitham).

## Redesign phase 1 — current contracts and unfinished code

Branch `redesign-ui-ux`, isolated under `.worktrees/redesign-ui-ux` from `2fb92c3e`. Replaced the obsolete Keep test with four behavioral Resize/Size/Position/Cancel tests using production controllers and fake I/O. Corrected particle fixtures to resolve generation paths and inspect nested history batches. TESTCARD now shares edge/frame presentation without merging controllers. window_box receives cfg.size. General duplicate file import offers Open existing or Import again as a new batch, using again=1/as_new=1 without a destination; batch-specific impagain remains intact.

Validation: four Resize controller tests; four import/trending tests; two corrected particle cases plus two HotSpot tests (4total); UIinventory4 pass. No provider calls. Browser acceptance of shared presentation is next; these test passes do not claim visual acceptance.

## Redesign phase 2 — native browser acceptance and reproduced gaps

Chrome at1440×900/DPR0.5 and390×844, own server8796, scratch outcopy, DB writes off and LLM/agent/vision providers none. External/paid mutation routes guarded. Shared-card asset initially404: registered ui-testcard.js in UI_FILES and added an inventory regression checking every shell script is served (5tests pass). Native retime Escape exposed a real gap: added dlgEscape with welcome priority and propagation stop; dialog_cancel5 pass. After reload TESTCARD is an object.

Accepted: G154 imported2×2 video frame preview (72frames), Position and Size changes, Grid toggle, frame scrubber; Cancel produced zero POSTs. Apply returned200 for one position request {index:1,offset:[0.01,0],reslice:true} on copied data. Escape and backdrop each settled retime to null with RTA cleared. Lottie Burn calories played the export through lottie-web, preserved5groups, and seed re-roll rebuilt7layers without errors. Settings omitted the dead local Account link and exposed tk-box; Help FAQ rows were native buttons and Enter opened F001. Native cover Timeline opened animate route. Phone viewer metadata is286px wide, grid-based, with no page overflow. Dark welcome ink is rgb(18,53,70), dots44px.

Remaining acceptance: exact imported3×3 fixture, native duplicate-upload retry, active-job clock trace, Lottie loop/random-still variants and post-redesign dark/light/phone checks. G154 was2×2, not claimed3×3. Browser startup errors from the fixed missing asset and deliberate server restarts are separated from accepted runs. Screenshots are temporary output/playwright artifacts. No paid or external send occurred.

## Redesign phase 3 — semantic foundations and targets

Added shared8px spacing tokens, five type roles with legacy aliases, status foreground/background pairs, focus/elevation/motion tokens and reduced-motion durations. Preserved locked issue colours and existing theme/route contracts. Shared controls have44px floors; checkbox/radio labels carry the hit target. Preview cards are bounded phone bottom sheets, retaining their frame controls.

Checks: theme/surface7 pass. Fresh-server browser: Studio desktop93 controls with zero targets below44; phone no page overflow, frame sheet x12..378/y184..832 and every frame button at least44px. Three engine-selector controls measured43px during the immediate resize/press transition and need settled-state confirmation in the Studio reference pass. Original old-styles measurement is excluded; the server static asset cache requires restart before CSS acceptance.

## Redesign phase 4 — Studio reference

Regrouped the batch header into identity, tools and Motion; generation and batch secondary actions use labelled details menus. Existing-project New request and Edge fold behind summaries, while an empty session/draft opens the composer. Composer Options and Prompt engine disclose advanced choices without flattening or removing controls. APIs, Grid/Resize/Position and recovery remain intact.

Validation: Studio menu/prompt9 pass before final disclosure; final menu/queue4 pass. Browser1440desktop and390phone in both themes: no page overflow, New request/Edge closed for G154, exactly one enabled stage primary (gadd). Reference desktop/phone screenshots in output/playwright; compare with the phase2 before screenshot. Broader cross-journey acceptance remains in the next phase.

## Redesign phase 5 — original reaction/pack requirements

Implemented original items1–9: native saved-set open button, hover/focus/expanded metadata, paid-only cost, Set options menu; Manage stickers; selected Motion/Change disclosure; one Advanced summary; burst rows without repeated preset plus download; no pack tabs (pktab retirement in baseline); Library Open in Studio; Open and save as an explicit independent row; default-off erosion_px0–6 read by engine and both raster/sprite-Lottie outputs. Current Emoji/Lottie-style contracts remain distinct.

Validation: saved-set/editor18 pass; particle UI42 pass after updating intentionally obsolete cost/markup expectations; pack/Studio/particle35 passed before final small label/download changes; pack-generation3 pass; UI inventory5 pass. Erosion3 tests and existing preview/strict-param2 tests pass. Baseline vs modified default hashes identical: frames56c9438feb3858d90f3489fb78a28155d143d0687e1a2c5545238f6662bf0746; Lottied4b5261b7da81f78dc27e961abe9c6775e5d2c9674bc7c758ad741a6f23ebe45.

Browser: pack9ebb180c has grid plus Reaction studio, zero pktab controls, no page overflow; P010 exposes one Advanced and Manage stickers. Active Open and save mode says Save as a new row. Erosion1 preview returned200 with params.erosion_px=1; Save returned201 P012 while original P010 remained200. All mutations were in scratch outcopy. Library shortcut opened G002 in Studio. Remaining: phone/theme/keyboard saved-set polish and cross-journey checks, so the nine original plan descriptions remain until those are accepted.

## Redesign phase 6a — authoritative cross-journey counts

Library snapshots and public Trending summaries now add sticker_count/reaction_count using one backend classifier, after existing owner/public filtering. Legacy totals and arrays remain intact. Home, grouped Library and Trending cards consume the additive fields; filtered subsets use neutral item wording. No client-only ownership or classification rule was added.

Validation: two narrow Python cases cover empty/static/reaction/mixed packs, owner filtering and public-only visibility. Imports/Trending + Packs column8 node tests pass; five relevant Home cases pass. Browser initial surfaces at1440/390 in both themes have no page overflow or below44px fully visible sampled controls. This geometry sample does not claim every off-screen, opened or hover state.

## Redesign phase 6b — reproduced integration gaps

A real duplicate MP4 upload exposed FastAPI's ImportOptions rejecting again/grid_ok although the existing engine and legacy handler support them. Added those booleans and their OpenAPI descriptions; an unknown-option rejection remains. Native general duplicate retry now returns202 with again=1/as_new=1 and creates G156. The batch duplicate choices are present; running a second import while the first cut holds the writer lock correctly returns409, so that overlap is not treated as a UI regression.

The 44px target pass made wrapped frame controls taller than the old placement reserve. Native Cancel reproduced an off-screen desktop action row. TESTCARD now measures rendered height. Real imported3×3 G155 has nine READY animations/36frames; Grid, End scrub, arrows, Centre, drag and native Cancel pass at1440/390 in both themes. Card bottom832 and Cancel bottom821 in844px viewport; no button below44; zero mutation POSTs during all four cancelled sessions.

Narrow regressions: import schema/OpenAPI1 pass, preview placement2 pass, UIinventory5 pass. Baseline JSON formatting restored without changing semantics; pktab retirement retained. No full suite or provider call.

## Redesign phase 6c — cross-journey surface and accessibility

Applied shared opaque cards to Chat/Library/Trending/Settings/Help and bounded desktop/phone dialogs. Shared dialogs now carry a labelled modal role, trap Tab/Shift+Tab and restore focus. Native Rename showed that its action menu closes before dismissal; focus restoration now targets the visible Set options summary rather than a hidden button. Dialog6 regression cases pass; native wrapping and focus return pass. Studio allowed pictures keep their available diagnostic reasons and visible reversible Take it back actions (G146: four controls, two with retained detailed reasons).

Browser sampled eight initial surfaces at1440/390 in both themes: no horizontal page overflow or below44px fully visible sampled controls; no pageerror in that matrix. Saved P010: all four theme/width combinations show metadata on focus, closed Manage stickers then visible unlink after expansion, one Advanced and Save as a new row, without page overflow. Lottie loop/random-still both return200 and mount SVG. Active queue fixture advanced0:04 to0:08 in4.2s; eight total DOM replacements include the2.5s network refresh/startup hooks, so this is not claimed as an isolated one-second draw count. Source/narrow queue test still guards the single1s registration.

2026-10-15 concurrent-work steering: Haitham supplied pushed handpicked-lottie commit5ad67e2d. The previously accepted duplicate-dialog behavior above is now superseded: manual uploads must always create a fresh batch, no again flag/dialog, explicit retry alone resumes old work. Grey animation thumbnails must come from that commit. Next: cherry-pick it, resolve structure/behavior overlaps and run the exact requested verification suites before clearing the plan.

### Concurrent change reviewed; final user choice

Reviewed5ad67e2d before finalizing its no-commit cherry-pick. Haitham then explicitly chose the redesign's choice router, not enforced fresh cuts. Retained imports.js, flow/imports.py, server parsing and their duplicate/retry tests from the redesign checkpoint. The general duplicate dialog and both deliberate batch choices remain; again/grid_ok schema support stays. The conflicting import-policy/doc portions of5ad67e2d are excluded.

Imported unchanged from5ad67e2d: media/grey.py, services/collection.py, the batches comment, collection tests and grey/export documentation. Animation alpha is taken from its first visible frame (within the supplied scan window), still fallback; collection WebM thumbnails and ZIP grey PNGs use the same grey encoder. No Lottie export or visual structure changed. Requested verification is run against this selected combination, not against forced-fresh-cut behavior. No runtime data was ported.

Integration verification: exact requested unittest command (test_imports, test_collection, library.NamingTests, ui_inventory) passed32 tests in46s. Retained import/Trending UI suite passed5. Grey source/tests/batches comment compare byte-for-byte to5ad67e2d; no data directories in the staged paths.
