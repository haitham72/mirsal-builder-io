# UI/UX plan (branch ui/ux-review)

> **Concurrent implementation notice:** Another LLM changed and committed source while this review ran; checkout advanced from audited `170f26e` to at least `76952eb`. This catalog is a snapshot proposal. Read current `CLAUDE.md` and reconcile every task before execution; skip resolved issues and preserve newer preset/manifest/grid contracts. Grouped issue → proposed fix documents are indexed in [uiux_review/README.md](uiux_review/README.md); [concurrent-work.md](uiux_review/concurrent-work.md) records the drift.

Reviewed 2026-10-14 at source commit170f26e36893a194248eaf5d88449ecba9e9bcd7. This run reviews and plans; implementation belongs to the next executor. This file is self-contained: evidence reports are lookup aids, not required startup reading. It is a searchable task catalog; read summary/ground rules plus the assigned block and needed helper contract, not the whole catalog on every task.

## Summary

1. Core journeys have tiny targets: Studio35–37 and Trash28 below the probe threshold; reaction Close is12px wide.
2. Presentation is scattered:290 inline-style literals,610 literal-colour CSS declarations and264 lines over300characters.
3. Keep approved size is overwritten and applies/reslices immediately instead of offering Apply/Cancel.
4. Studio700ms async polling can overlap, and two1s clocks both replace the queue.
5. Current contracts disagree about reaction wall, sheet clicks, History retirement and built navigation.
6. Retime backdrop leaves a pending promise; cover badge blocks Timeline; local Account is dead.
7. Shared testCard, dialogFrame and groupedGrid remove most repeated markup; watchResource and semantic controls reduce lifecycle drift.
8. Preserve shell/rail/routes/actions and90% of information architecture; use8px spacing, five type roles, grouped inset cards,44px targets and one stage primary.
9. Bars/sheets alone may use translucent material; panels stay readable; icons share line weight;150–250ms ease-out motion explains changes and respects reduced motion.
10. 87 bounded tasks:50 for6.1-sol-medium and37 for luna-6-high;48 cited screenshots+11contact sheets=59images, under60. No source changes, tests or paid/external transfer during review.

## Ground rules

- Preserve all17screen keys, routes/ACT names and ui_baseline.json. Moved controls retain actions; retirement/rename requires an explicit authorized baseline entry. History/React removals stay held.
- Every soft-blocked/allowed picture keeps picture+plain reason+visible reversible override and honest bulk control. Technical Telegram/no-cut final blocks stay final. Human dropped/Bring back is distinct from Python blocked/Use it anyway.
- Engine/API decides eligibility, ownership, pricing and classification; presenters create no JS-only business logic or unread backend controls.
- Owner-only Telegram/collection/share/import stays owner-only; string ids, per-person Library and permission filtering stay intact.
- Refactors preserve request URLs/bodies and existing JSON values byte for byte. Only T-075 adds count fields while preserving old fields/values. Tests and acceptance never use paid/real providers.
- Each sol task≤2files/150totalchanged lines with zero design decisions; luna≤6files with bounded judgment; every task≤2explicit dependencies. File budgets include tests. Extra fixture work requires a separately specified bounded preparation task; never silently broaden scope.
- One narrow JS invocation per source change with real production helpers and faked APIs/timers; inventory when action/markup/script wiring changes. Passing evidence stays valid until files change. Docs-only0tests; no slow/full unittest discovery.
- Explicit-path commits, one per phase, with owning docs in the same phase; never git add-A or media/out/credentials/.env/opencode/telegram-id. Native hit-testing and mutation traces are acceptance; forced clicks are not.

### No-spend acceptance server

Create a new temp scratch directory outside the repo. Fetch/check out before starting; leave unrelated work alone. Copy mirsal/out excluding cache/trash/jobs and retaining library/files. Never use/kill8770. Choose a spare port (8795 here):

```powershell
$env:MIRSAL_OUT='<scratch>\outcopy'
$env:MIRSAL_DB_WRITE='0'
$env:MIRSAL_TRACE='none'
$env:MIRSAL_NO_REAL_CLI='1'
$env:MIRSAL_LLM_PROVIDER='none'
$env:MIRSAL_AGENT_PROVIDER='none'
$env:MIRSAL_VISION_PROVIDER='none'
# From mirsal/:
.venv\Scripts\python.exe -m mirsal serve --port 8795
```

macOS uses mirsal/venv and rsync in place of robocopy. Verify /api/health from the authenticated local browser if anonymous access is401; copied storage/provider flags must match. Close welcome with wlClose(), not only its CSS class. Wait for hydration/modal/slide transitions. Stale-code banner requires restart of your server and reload.

Never press Generate/Create sheet/Animate/regenerate/Create it/Allow vision/render/batch/all or sending acceptance. Free prompt planning, preview navigation and cancelling dialogs are allowed. Telegram's entry may auto-send when configured and no retime question is needed: intercept external mutation routes before reviewing that entry. Provider-none does not disable Telegram. Collection Send is never pressed. Stop only your server and delete only verified scratch outcopy at end.

```text
# JS: repository root; task-listed files only
node --test mirsal/tests/js/<listed>.test.js [...]
# Inventory: from mirsal/, only wiring/action/markup changes
python -m unittest tests.test_ui_inventory
# Backend counts: from mirsal/, fake/copy fixtures only
python -m unittest tests.test_trending tests.test_library tests.test_ui_inventory
# Reflow: vendored console_source.canonical(before)===canonical(after)
# Review/docs-only changes: zero tests
```

### Top15 by impact×reach/risk

| Rank | Finding | Impact/reach/risk | Priority | First task |
|---:|---|---|---:|---|
| 1 | F-22 Tap targets are too small across core journeys | 18/9/2 | 81.0 | T-066 |
| 2 | F-19 Presentation bypasses a shared token system | 9/11/2 | 49.5 | T-056 |
| 3 | F-01 Keep approved size bypasses preview | 22/2/1 | 44.0 | T-001 |
| 4 | F-05 Refresh loops can overlap and redraw twice | 10/8/2 | 40.0 | T-004 |
| 5 | F-33 Published screen contracts contradict each other | 6/5/1 | 30.0 | T-079 |
| 6 | F-30 Dark welcome text fades into pale artwork | 13/2/1 | 26.0 | T-074 |
| 7 | F-06 Backdrop hides retime without settling its promise | 8/3/1 | 24.0 | T-002 |
| 8 | F-34 Doc organization and tracker IDs raise reading cost | 4/6/1 | 24.0 | T-080 |
| 9 | F-36 Phone viewer header squeezes the title into a word column | 12/2/1 | 24.0 | T-086 |
| 10 | F-07 Segment builders disagree about semantics | 7/6/2 | 21.0 | T-017 |
| 11 | F-11 Long-line scripts make small changes expensive to review | 3/6/1 | 18.0 | T-059 |
| 12 | F-24 Cover badge intercepts Timeline click | 9/2/1 | 18.0 | T-065 |
| 13 | F-28 Help rows are click-only divs | 6/3/1 | 18.0 | T-073 |
| 14 | F-08 Download lifecycle is copied | 3/4/1 | 12.0 | T-026 |
| 15 | F-21 Inventory unique count omits the extra overwrite | 4/3/1 | 12.0 | T-064 |

Scores are prioritization judgments, not measured latency/contrast certifications. Repair Keep/retime/native hit areas before broad style work even if reach-weighted token work ranks higher. Findings.md gives formula and confidence.

## Phases

- **P1 mechanical cleanup and repairs:** T-001, T-002, T-003, T-004, T-056, T-059, T-060, T-061, T-062, T-065, T-085. Keep/retime/queue/tick first, token vocabulary and bounded reflow next. Pair with T-085 before commit.
- **P2 shared components:** T-005, T-006, T-007, T-008, T-009, T-010, T-011, T-012, T-013, T-014, T-015, T-016, T-017, T-018, T-019, T-020, T-021, T-022, T-023, T-024, T-025, T-026, T-027, T-028, T-029, T-030, T-031, T-032, T-033, T-034, T-035, T-036, T-037, T-038, T-039, T-040, T-041, T-042, T-043, T-044, T-045, T-046, T-047, T-048, T-049, T-050, T-051, T-052, T-053, T-054, T-055, T-057, T-058, T-084. Add each helper with real fixture coverage; migrate one consumer per task. No whole-screen merge. Pair with T-084 before commit.
- **P3 screen redesigns, worst first:** T-066, T-067, T-068, T-069, T-070, T-071, T-072, T-073, T-074, T-075, T-076, T-077, T-078, T-086, T-087, T-083. Targets→welcome/Studio→reaction/saved set→Settings/Help→counts/phone. Keep90%; pair with T-083 before commit.
- **P4 docs and inventory:** T-063, T-064, T-079, T-080, T-081, T-082. Contracts/gateway/tracker references and generated inventory after source work; human/paid/held items remain open.

Phase order is the default queue; listed dependencies are binding. Independent different-file tasks may run in parallel; one orchestrator owns shared CSS/index files and commits. No task has more than two dependencies. Review authorization does not authorize a production merge/provider call.

### Shared contracts and migration order

| Component/file | API | One-consumer migration tasks/order |
|---|---|---|
| ui-testcard.js | testCard({id,media:{kind,src,alt},caption,anchor,loading,busy,applyAct,cancelAct})→{update,close} | T-011, T-012, T-013; video then edge; repair staged Keep first |
| ui-grouped-grid.js | groupedGridHtml({groups,rootAttrs,groupAttrs,headerHtml,cellHtml})→string | T-014, T-015, T-016; Library then Pack; grouping stays in callers |
| ui-segment.js | segmentedHtml({label,mode:choice/tabs/navigation,items,selected,className})→string | T-017, T-018, T-019, T-020, T-021, T-022; reaction→composer→Studio→Pack→Settings |
| ui-range.js | rangeFieldHtml({label,min,max,step,value,attrs,formatValue,pairedInput,className,layout})→string | T-023, T-024, T-025; saved set then emoji; editor/prepare later one caller/task |
| ui-watch.js | watchResource({key,intervalMs,enabled,read,onValue,onError,isTerminal,signature,visibility})→{start,stop,refresh} | T-005, T-006, T-007, T-008, T-009, T-010; collection→reaction→FX→SP→live; preserve SSE |
| ui-download.js | downloadFile({url,blob,filename,revokeAfterMs=4000})→void | T-026, T-027, T-028, T-029, T-030, T-031; Timeline→prepare→editor→particles→reactions |
| ui-preview.js | previewSession({keyFor,request,commit,onError,maxEntries=64,debounceMs})→{schedule,refresh,clear,dispose} | T-032, T-033, T-034, T-035, T-036; VZ→emoji→preset cards→SP; endpoints unchanged |
| ui-dialog.js | dialogFrameHtml({title,bodyHtml,footerHtml,labelId}); dlg(html,{onDismiss}); closeDlg(reason) | T-037, T-038, T-039, T-040, T-041, T-042, T-043; ask→confirm→pack picker→retime→collection→Telegram |
| ui-menu.js | moreMenuHtml({label,itemsHtml,className,summaryAttrs,popClass,summaryHtml})→string | T-044, T-045, T-046, T-047; Pack→Studio→current reaction presets; map later |
| ui-feedback.js | statusMessageHtml({kind,text,bodyHtml,actionsHtml,live,className})→string; caller owns lifetime | T-048, T-049, T-050, T-051; collection→burst→Studio diagnostics |
| ui-decision.js | decisionStatusHtml({reason,eligible,allowed,actionAttrs,labels,context})→string | T-052, T-053, T-054, T-055; reason box→animation overlay→chat; no eligibility decision |

Already shared: FX/SP fxNew/fxX/spBurstHtml, global selection and .gseg CSS. Scoped escaping, relative-time policy, toast/field-error/notification lifetimes, Telegram launch and distinct preview endpoints remain distinct. Later editor-range/map-menu migration must also be one caller per task.

### Surface tokens/components

T-056 defines exact semantic names/values before adapters use them: spacing8/16/24/32, large-title/title/headline/body/footnote, card/group surfaces, bar/sheet material, border/focus/status and control44. Reuse palettes; diagnostics map deterministically to status tokens. Presentation values alone migrate; image colours/canvas coordinates/media formats remain data. No new inline UI colours. Icons share a line weight without changing art; motion150–250ms ease-out explains state/navigation and respects reduced motion. Group Settings/Trash as inset lists; choice/tabs/navigation semantics remain distinct.

The44CSSpx goal follows the requested direction and [W3C enhanced target guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html), not a blanket AA failure claim. Text contrast targets≥4.5:1normal/3:1large follow [W3C contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). Executors measure layered backgrounds; review has settled visual proof of welcome fading, not a ratio measurement.

### Common helper-fixture contract

Load each new helper once before its actual consumer in console_vm loadConsole, deduplicating resolved filenames. Standalone statement-extraction fixtures inject the actual exported helper. Preserve console_source canonicalization and unrelated fixture grouping. Foundations own this integration; consumer migrations do not broaden sol budgets.

## Tasks

F01–F21 merge C01–C21 one-to-one. Original CT/UX/DOC ids are traceability; schedule by T ids. File lists are hard caps. New helper/test files are marked(new).

### T-001 Restore staged Keep approved size [model:6.1-sol-medium] [risk:low] [depends:none]

Why: F-01 — Keep approved size bypasses preview. Trace: CT-001.

Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/size_preview.test.js (new or supplied by dependency).

Do:

1. Delete only the late ACT.gkeepsize assignment originally at901–911; retain the858 staged implementation and all other ACT names. Test with stubbed API/GM and the existing console_vm/source helpers: click changes VZ.keep and reads anim_preview; no keep_size/video_size POST until Apply. Cancel makes zero mutation calls; Apply sends the original {on,reslice} body once; technical failures retain the preview.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/size_preview.test.js mirsal/tests/js/anim_create.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~100 total changed lines including tests; hard cap150 changed lines/2files.

### T-002 Settle retime on every dialog cancellation [model:luna-6-high] [risk:medium] [depends:none]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-002.

Files: mirsal/mirsal/console/app.js, mirsal/mirsal/console/packs.js, mirsal/tests/js/dialog_cancel.test.js (new or supplied by dependency).

Do:

1. Extend dlg(html,{onDismiss}={}) and closeDlg(reason='dismiss') with one active dismissal callback cleared before invocation. retimeAsk registers a callback that captures its own resolver and resolves null exactly once; ACT.rtans clears RTA/callback before closing and returns only true/false/null. Opening a replacement dialog cancels the prior request. Preserve dlg(html) callers; backdrop and ACT.dlgx use the same close path. Do not add Escape handling until dialog lifecycle task.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/dialog_cancel.test.js mirsal/tests/js/pack_delete.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~160 total changed lines including tests; hard cap6files.

### T-003 Coalesce duplicate queue clock redraws [model:6.1-sol-medium] [risk:low] [depends:none]

Why: F-05 — Refresh loops can overlap and redraw twice. Trace: CT-003.

Files: mirsal/mirsal/console/live.js, mirsal/tests/js/queue_clock.test.js (new or supplied by dependency).

Do:

1. Remove only the second1000-ms interval at live.js:191. Retain the first interval at185 byte-for-byte, including data-lvt updates and its original active/run predicate. Add a stub-clock test proving one queue1000-ms interval registration and one drawLive call per clock tick for REQUESTED/CLAIMED work. Preserve qRefresh/qtoggle, all queue ACT names and saved QO; incremental DOM rendering is a separate design task.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/queue_clock.test.js mirsal/tests/js/job_recovery.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~80 total changed lines including tests; hard cap150 changed lines/2files.

### T-004 Serialize Studio refreshes and retain force requests [model:luna-6-high] [risk:medium] [depends:none]

Why: F-05 — Refresh loops can overlap and redraw twice. Trace: CT-004.

Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_poll.test.js (new or supplied by dependency).

Do:

1. Add a tick in-flight flag and one pending-force flag. Concurrent tick(true) must queue one force refresh after the current read completes; intervals may not overlap. Release both flags on every failure via finally. Skip interval work while document.hidden, but explicit force requests and required open-modal refreshes retain current behavior. Read each original URL/body and preserve glast/typing guard/404 session cleanup. Use fake slow reads and hidden-state tests; do not change server polling cadence here.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/studio_poll.test.js mirsal/tests/js/prompt_tab.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~170 total changed lines including tests; hard cap6files.

### T-005 Introduce resource watcher lifecycle [model:luna-6-high] [risk:medium] [depends:T-004]

Why: F-05 — Refresh loops can overlap and redraw twice. Trace: CT-005.

Files: mirsal/mirsal/console/ui-watch.js (new or supplied by dependency), mirsal/mirsal/console/index.html, mirsal/tests/js/ui_watch.test.js (new or supplied by dependency), mirsal/tests/js/console_vm.js.

Do:

1. Implement watchResource({key,intervalMs,enabled,read,onValue,onError,isTerminal,signature,visibility}) -> {start,stop,refresh}. Exactly one read at a time; refresh(true) retains one pending force; next timeout begins after settle. Terminal/stop disposes timers; failure calls onError then reschedules while enabled. visibility is explicit 'visible'|'always'; no default policy guessing. Export pure/testable helper with no DOM reads at module load. Include once after app.js and before consumers. Use the common helper-fixture contract below. enabled=false skips reads and continues only cheap enabled checks until explicit stop/terminal; caller route transitions do not create parallel instances. Visibility policy skips read while hidden without marking a running job terminal. Cover disable/re-enable without manual new watcher.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/ui_watch.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~230 total changed lines including tests; hard cap6files.

### T-006 Migrate collection export watcher [model:6.1-sol-medium] [risk:medium] [depends:T-005]

Why: F-05 — Refresh loops can overlap and redraw twice. Trace: CT-006.

Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/collection_watch.test.js (new or supplied by dependency).

Do:

1. Replace only colWatch scheduling with watchResource; keep its public colWatch(id,tries=0). Policy:2500ms, always visible/offscreen, stop on404, done, failed or tries>720; preserve done/failed toast wording and no duplicate terminal toast. read remains GET collection/exports/{encoded id}; never initiate an export in tests. Exact failed-read/retry-limit fixtures.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/collection_watch.test.js mirsal/tests/js/pack_delete.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~140 total changed lines including tests; hard cap150 changed lines/2files.

### T-007 Migrate reaction batch watcher [model:6.1-sol-medium] [risk:medium] [depends:T-005]

Why: F-05 — Refresh loops can overlap and redraw twice. Trace: CT-007.

Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.

Do:

1. Adapt rxWatch/rxRun's runT scheduling to watchResource at RXPOLL1500. Preserve original reaction batch id capture, running/terminal decisions, fresh-token progress, RXS.done reset and redraw points. Off-route background batches keep original continuation policy; no new batch request. Extend existing reactions tests with terminal-once, failure recovery and stopped watcher fixtures.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/ui_watch.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~140 total changed lines including tests; hard cap150 changed lines/2files.

### T-008 Migrate effect-run watcher [model:6.1-sol-medium] [risk:medium] [depends:T-005]

Why: F-05 — Refresh loops can overlap and redraw twice. Trace: CT-008.

Files: mirsal/mirsal/console/effects.js, mirsal/tests/js/effects_core.test.js.

Do:

1. Replace fxPoll's timeout with one watcher per X.who/eid at2200ms; enabled=original fxBusy(X)&&X.alive(). read uses fxLoad(X), which retains original state-token guard. Keep fxSig and X.last redraw check; stop/dispose on fxReset and eid switch. Do not share FX/SP state or merge their screens.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/effects_core.test.js mirsal/tests/js/ui_watch.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~140 total changed lines including tests; hard cap150 changed lines/2files.

### T-009 Migrate saved-set drawing watcher [model:6.1-sol-medium] [risk:medium] [depends:T-005]

Why: F-05 — Refresh loops can overlap and redraw twice. Trace: CT-009.

Files: mirsal/mirsal/console/particles.js, mirsal/tests/js/particle_editor.test.js.

Do:

1. Replace only spPoll with a2500-ms watcher. While original busy predicate is true, reproduce route-specific reads exactly: Library particles calls spLibSync(true); Pack calls ptCounts(PACK_ID) and conditional spLibSync(true); off-route wakes may continue without reads. Preserve SPL.busy, cached cells invalidation and terminal behavior. Do not migrate search/slider timers.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/particle_editor.test.js mirsal/tests/js/ui_watch.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~145 total changed lines including tests; hard cap150 changed lines/2files.

### T-010 Migrate background job reads [model:luna-6-high] [risk:medium] [depends:T-005]

Why: F-05 — Refresh loops can overlap and redraw twice. Trace: CT-010.

Files: mirsal/mirsal/console/live.js, mirsal/tests/js/live_watch.test.js (new or supplied by dependency).

Do:

1. Move liveTick2500-ms registration to watcher with visibility:'always'; preserve LTB, completion/session mutations, dismissal handling, lsave and qRefresh. read/commit split must reproduce existing call/order; a force tick during a read may coalesce but cannot lose completion. Fake all network operations and assert exact session/ANIM/LIVE outcomes for completed sheet/video and failed job.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/live_watch.test.js mirsal/tests/js/job_recovery.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~200 total changed lines including tests; hard cap6files.

### T-011 Introduce shared test-card presenter [model:luna-6-high] [risk:medium] [depends:T-001]

Why: F-02 — Two Apply/Cancel presenters drift. Trace: CT-019.

Files: mirsal/mirsal/console/ui-testcard.js (new or supplied by dependency), mirsal/mirsal/console/index.html, mirsal/tests/js/ui_testcard.test.js (new or supplied by dependency), mirsal/tests/js/console_vm.js.

Do:

1. Implement testCard({id,media:{kind,src,alt},caption,anchor,loading,busy,applyAct,cancelAct}) -> {update,close}. Reuse existing egcimg/egbadge/egccap/egcbtn classes and exact labels/ids; support image or autoplay loop muted playsinline video. Width min(300,innerWidth-24); same12px horizontal clamp and70px/min(innerHeight-width-110,anchor.bottom+8 or90) top clamp. Only owned DOM, no API/policy. Include once after app.js. Use the common helper-fixture contract below.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/ui_testcard.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~230 total changed lines including tests; hard cap6files.

### T-012 Migrate video-size test card [model:6.1-sol-medium] [risk:medium] [depends:T-011, T-001]

Why: F-02 — Two Apply/Cancel presenters drift. Trace: CT-020.

Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/size_preview.test.js (new or supplied by dependency).

Do:

1. Replace only vzCard DOM construction/update/position with testCard. Adapter computes existing target/caption, source/spinner, busy state and anchor expression; preserve #vzcard, gvsize/gkeepsize anchor choices and vzapply/vzcancel. Scroll/resize still update placement. Do not change VZ.n, endpoints or tick calls.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/size_preview.test.js mirsal/tests/js/ui_testcard.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~140 total changed lines including tests; hard cap150 changed lines/2files.

### T-013 Migrate edge test card [model:6.1-sol-medium] [risk:medium] [depends:T-011]

Why: F-02 — Two Apply/Cancel presenters drift. Trace: CT-021.

Files: mirsal/mirsal/console/live.js, mirsal/tests/js/edge_preview.test.js (new or supplied by dependency).

Do:

1. Replace only egCard DOM construction/update/position with testCard. Preserve #egcard image/caption and egapply/egundo. Keep modal-overlay route, egDirty/egClear, 40-ms debounce and stored-snapshot undo semantics. Set busy from EG.busy without changing eligibility; test dirty-cancel is zero POST while committed undo retains original body.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/edge_preview.test.js mirsal/tests/js/ui_testcard.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~140 total changed lines including tests; hard cap150 changed lines/2files.

### T-014 Introduce grouped-grid presentation helper [model:luna-6-high] [risk:medium] [depends:none]

Why: F-03 — Grouped grids repeat presentation. Trace: CT-022.

Files: mirsal/mirsal/console/ui-grouped-grid.js (new or supplied by dependency), mirsal/mirsal/console/index.html, mirsal/tests/js/grouped_grid.test.js (new or supplied by dependency), mirsal/tests/js/console_vm.js.

Do:

1. Implement groupedGridHtml({groups,rootAttrs,groupAttrs,headerHtml,cellHtml}) -> string. Emit one outer container and section+header+grid per group, preserving caller-provided attributes/markup; headerHtml(group), cellHtml(item,index,group) use original caller indices carried in items. No grouping/sorting/selection mutations inside helper. Include once after app.js; test flat index/order, labels and emitted root/group/cell attributes. Use the common helper-fixture contract below.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/grouped_grid.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~160 total changed lines including tests; hard cap6files.

### T-015 Migrate Library grouped grid [model:6.1-sol-medium] [risk:medium] [depends:T-014]

Why: F-03 — Grouped grids repeat presentation. Trace: CT-023.

Files: mirsal/mirsal/console/library.js, mirsal/tests/js/grouped_grid.test.js (new or supplied by dependency).

Do:

1. Use groupedGridHtml inside libByPackHtml only. Retain its Map-by-pack algorithm, [sticker,globalIndex] pairs, SEL/selKey checks, lcopen/lsel/openpack attributes, lib-bypack/lib-pk/lib-pkh classes and empty sentence. Snapshot representative two-pack HTML before extraction, assert byte equality after migration including cap escaping and global LCL index.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/grouped_grid.test.js mirsal/tests/js/packs_column.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~140 total changed lines including tests; hard cap150 changed lines/2files.

### T-016 Migrate Pack grouped grid [model:6.1-sol-medium] [risk:medium] [depends:T-014]

Why: F-03 — Grouped grids repeat presentation. Trace: CT-024.

Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/grouped_grid.test.js (new or supplied by dependency).

Do:

1. Replace only drawPack's pk-bybatch section/grid iteration. Keep pkGroups/pkGroupHead outputs, non-Studio last group, original sticker order, all drag/cover/reaction/hover/name/selection attributes and disabled owner actions. Snapshot exact representative HTML before extraction and compare unchanged output; no change to reaction tab markup.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/grouped_grid.test.js mirsal/tests/js/pack_delete.test.js mirsal/tests/js/manual_batch_action.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~145 total changed lines including tests; hard cap150 changed lines/2files.

### T-017 Introduce semantic segmented presenter [model:luna-6-high] [risk:medium] [depends:none]

Why: F-07 — Segment builders disagree about semantics. Trace: CT-025.

Files: mirsal/mirsal/console/ui-segment.js (new or supplied by dependency), mirsal/mirsal/console/index.html, mirsal/tests/js/segmented.test.js (new or supplied by dependency), mirsal/tests/js/console_vm.js.

Do:

1. Implement segmentedHtml({label,mode,items,selected,className}) -> string. choice: role=group plus button aria-pressed; tabs: role=tablist/buttons role=tab + aria-selected + roving tabindex; navigation: nav aria-label with aria-current=page on selected. Keep data attributes supplied in items.attrs and ACT names verbatim; no state/persistence logic. Escape labels and values. Include once after app.js. Provide delegated keyboard handling restricted to role=tab within helper-emitted tablists: Left/Right wrap focus and call the target button.click(), Home/End select first/last; do not intercept text inputs or choice/navigation groups. Export the handler for stub-DOM tests and install one guarded listener in browser mode. Use the common helper-fixture contract below.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/segmented.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~200 total changed lines including tests; hard cap6files.

### T-018 Migrate reaction filter segment [model:6.1-sol-medium] [risk:medium] [depends:T-017]

Why: F-07 — Segment builders disagree about semantics. Trace: CT-026.

Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.

Do:

1. Replace only rxPick's All/Done/Not done segment with mode:'choice'; preserve gseg rx-f, data-act=rxfilter/data-f all|done|todo and RXQ.f. Keep counts, wall, selection, batch actions untouched. Exact selected states for each of three values and unchanged action names.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/segmented.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~100 total changed lines including tests; hard cap150 changed lines/2files.

### T-019 Migrate composer source segment [model:6.1-sol-medium] [risk:medium] [depends:T-017]

Why: F-07 — Segment builders disagree about semantics. Trace: CT-027.

Files: mirsal/mirsal/console/composer.js, mirsal/tests/js/prompt_step.test.js.

Do:

1. Replace only cpDrawBar Creative/Predefined gseg cp-act with choice mode. Preserve cpactions/data-v creative|predefined, current Creative selection whenever actions!='predefined', both tooltips and model/prompt behavior. Assert both states and original ACT.cpactions persistence/body.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/prompt_step.test.js mirsal/tests/js/segmented.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~110 total changed lines including tests; hard cap150 changed lines/2files.

### T-020 Migrate Studio view segment [model:6.1-sol-medium] [risk:medium] [depends:T-017]

Why: F-07 — Segment builders disagree about semantics. Trace: CT-028.

Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_menu.test.js.

Do:

1. Replace only gview What to show segment with choice mode, using stickers|sheet|both, data-act=gvmode/data-v and exact tooltip strings. Preserve saved view fallback and emitted content for each state; never change tabs or routes. Extend exact marker-based VM fixture rather than test text line formatting.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/studio_menu.test.js mirsal/tests/js/segmented.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~110 total changed lines including tests; hard cap150 changed lines/2files.

### T-021 Migrate Pack tabs segment [model:6.1-sol-medium] [risk:medium] [depends:T-017]

Why: F-07 — Segment builders disagree about semantics. Trace: CT-029.

Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/pack_delete.test.js.

Do:

1. Replace only gseg pk-tabs with mode:'tabs', keys stickers|particles, ACT.pktab/data-t unchanged. Use aria-selected and roving tabindex rather than aria-pressed; wire Left/Right/Home/End to focus/select only these two tab buttons using shared helper callback (helper keyboard support must be pinned in foundation before this task). Preserve PKTAB and rendering.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/pack_delete.test.js mirsal/tests/js/segmented.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~130 total changed lines including tests; hard cap150 changed lines/2files.

### T-022 Migrate Settings section navigation [model:6.1-sol-medium] [risk:medium] [depends:T-017]

Why: F-07 — Segment builders disagree about semantics. Trace: CT-030.

Files: mirsal/mirsal/console/settings.js, mirsal/tests/js/theme.test.js.

Do:

1. Replace only Settings section nav using mode:'navigation'. Keep ordered IDs set-appear,au-me,set-health,staff set-prep,set-ai,set-tg,trx-box and existing setjump attributes/actions. This control scrolls to anchors, not a content tablist; preserve role/access and staff gating. Do not invent a selected pane if no state currently tracks it; navigation selected:null yields no aria-current.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/theme.test.js mirsal/tests/js/segmented.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~120 total changed lines including tests; hard cap150 changed lines/2files.

### T-023 Introduce range-field presenter [model:luna-6-high] [risk:medium] [depends:none]

Why: F-04 — Range controls repeat across distinct reaction contracts. Trace: CT-031.

Files: mirsal/mirsal/console/ui-range.js (new or supplied by dependency), mirsal/mirsal/console/index.html, mirsal/tests/js/range_field.test.js (new or supplied by dependency), mirsal/tests/js/console_vm.js.

Do:

1. Implement rangeFieldHtml({label,min,max,step,value,attrs,formatValue,pairedInput,className}). pairedInput='output'|'number'|'none'; emit supplied namespace attributes unchanged on range and number only; output formatting is caller-supplied; no default/range/rounding policy. Support fx-sl label/span/output wrapper and fld/srow wrapper via explicit layout:'label-output'|'field-pair'. Include once after app.js; pin output escaping and two-input value attributes. Use the common helper-fixture contract below.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/range_field.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~200 total changed lines including tests; hard cap6files.

### T-024 Migrate saved-set burst sliders [model:6.1-sol-medium] [risk:medium] [depends:T-023]

Why: F-04 — Range controls repeat across distinct reaction contracts. Trace: CT-032.

Files: mirsal/mirsal/console/particles.js, mirsal/tests/js/particle_editor.test.js.

Do:

1. Replace only spBSlider. Use original FXSL lookup, par override then shown fallback and blank-null behavior; label-output mode, class fx-sl, data-psbp and data-id exact. Do not move FXSL/default/clean parameter decisions into helper. Pin each six descriptors and focused-input handling remains outside helper.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/particle_editor.test.js mirsal/tests/js/pack_studio.test.js mirsal/tests/js/range_field.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~110 total changed lines including tests; hard cap150 changed lines/2files.

### T-025 Migrate emoji reaction sliders [model:6.1-sol-medium] [risk:medium] [depends:T-023]

Why: F-04 — Range controls repeat across distinct reaction contracts. Trace: CT-033.

Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.

Do:

1. Replace only rxSlider. Retain rxVal/rxFmt and each original RXSIM/RXO min/max/step/unit/label; attrs data-rxo, existing classes/label references and preview events unchanged. Preserve sim versus extra payload keys and percent display. Pin all descriptors, nullable fallback and byte-identical rxBody JSON.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/range_field.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~120 total changed lines including tests; hard cap150 changed lines/2files.

### T-026 Introduce URL/blob download utility [model:luna-6-high] [risk:low] [depends:none]

Why: F-08 — Download lifecycle is copied. Trace: CT-037.

Files: mirsal/mirsal/console/ui-download.js (new or supplied by dependency), mirsal/mirsal/console/index.html, mirsal/tests/js/ui_download.test.js (new or supplied by dependency), mirsal/tests/js/console_vm.js.

Do:

1. Implement downloadFile({url,blob,filename,revokeAfterMs=4000}) with exactly one source. Append anchor, assign href/download, click, remove in finally; create object URL only for blob and revoke only helper-owned URL after specified delay. Existing URL/data-URL must never be revoked. No fetch or Telegram launch in helper. Include once after app.js; stub document/URL/timers. Use the common helper-fixture contract below.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/ui_download.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~160 total changed lines including tests; hard cap6files.

### T-027 Migrate Timeline blob download [model:6.1-sol-medium] [risk:low] [depends:T-026]

Why: F-08 — Download lifecycle is copied. Trace: CT-038.

Files: mirsal/mirsal/console/animate.js, mirsal/tests/js/ui_download.test.js (new or supplied by dependency).

Do:

1. Replace only anCall's response blob/createObjectURL/anchor/remove/revoke sequence with downloadFile({blob,filename: original sanitized A.st.name+'.'+A.fmt}). Preserve fetch/body, busy state, original4000ms cleanup timing and save branch. Extend fixture proving filename/source ownership and zero new network requests.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/ui_download.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~110 total changed lines including tests; hard cap150 changed lines/2files.

### T-028 Migrate video-editor blob download [model:6.1-sol-medium] [risk:low] [depends:T-026]

Why: F-08 — Download lifecycle is copied. Trace: CT-039.

Files: mirsal/mirsal/console/prepare.js, mirsal/tests/js/ui_download.test.js (new or supplied by dependency).

Do:

1. Replace only prCall's response-blob download sequence with downloadFile; preserve (e.name||P.p.name).replace(/[^\w-]+/g,'_')+'.'+e.format exactly, original4000ms cleanup, encoding request/body and save branches. No change to project persistence/timing/canvas.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/ui_download.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~110 total changed lines including tests; hard cap150 changed lines/2files.

### T-029 Migrate still-editor PNG download [model:6.1-sol-medium] [risk:low] [depends:T-026]

Why: F-08 — Download lifecycle is copied. Trace: CT-040.

Files: mirsal/mirsal/console/editor.js, mirsal/tests/js/ui_download.test.js (new or supplied by dependency).

Do:

1. Replace only ACT.xdl anchor construction with downloadFile({url:E.dataUrl,filename: original sanitized (E.name||'sticker')+'.png'}). Keep action name and data URL; do not fetch/revoke it. Pin fallback/special-character filenames.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/ui_download.test.js mirsal/tests/js/ai_editor.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~80 total changed lines including tests; hard cap150 changed lines/2files.

### T-030 Migrate particle Lottie download [model:6.1-sol-medium] [risk:low] [depends:T-026]

Why: F-08 — Download lifecycle is copied. Trace: CT-041.

Files: mirsal/mirsal/console/particles.js, mirsal/tests/js/particle_editor.test.js.

Do:

1. Replace only ACT.psblottie success-path anchor download with downloadFile({url: original server URL,filename: original name}). Preserve original export-lottie POST, touched-only params/scale, busy button recovery and filename wording. Test fake response, never render or call a model.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/particle_editor.test.js mirsal/tests/js/ui_download.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~100 total changed lines including tests; hard cap150 changed lines/2files.

### T-031 Migrate reaction ZIP and Lottie downloads [model:6.1-sol-medium] [risk:low] [depends:T-026]

Why: F-08 — Download lifecycle is copied. Trace: CT-042.

Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.

Do:

1. Replace only rxzip and rxdl anchor creation with downloadFile; preserve zip URL query for selected tokens, encoded join order, filename reactions.zip and individual token/id .lottie.json filename. Keep all download controls/data attributes, no fetch added. Test selected/full and individual versions.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/ui_download.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~130 total changed lines including tests; hard cap150 changed lines/2files.

### T-032 Introduce latest-result preview session [model:luna-6-high] [risk:high] [depends:none]

Why: F-09 — Preview request lifecycles repeat; endpoints are distinct. Trace: CT-043.

Files: mirsal/mirsal/console/ui-preview.js (new or supplied by dependency), mirsal/mirsal/console/index.html, mirsal/tests/js/preview_session.test.js (new or supplied by dependency), mirsal/tests/js/console_vm.js.

Do:

1. Implement previewSession({keyFor,request,commit,onError,maxEntries=64,debounceMs}) -> {schedule,refresh,clear,dispose}. Unique monotonic generation per request; stale responses never commit; allow one in-flight read and retain only latest queued key. Cache response metadata by exact caller key with64-entry LRU; no media blobs/artwork generated or URL rewriting. Clear/dispose cancels scheduled work and invalidates late replies. Errors release busy state. Include once after app.js. Use the common helper-fixture contract below.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/preview_session.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~240 total changed lines including tests; hard cap6files.

### T-033 Migrate size preview request lifecycle [model:luna-6-high] [risk:high] [depends:T-032, T-012]

Why: F-09 — Preview request lifecycles repeat; endpoints are distinct. Trace: CT-044.

Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/size_preview.test.js (new or supplied by dependency).

Do:

1. Replace only VZ.t/VZ.n orchestration in vzPreview with previewSession debounce250/cache policy exact query key. Keep generation/index/scale/keep query serialization, initial clear/spinner, api anim_preview GET, metadata/caption and error toast/vzClear. VZ change/clear must invalidate prior requests; no automatic Apply. Preserve currently selected generation and test delayed old responses after target switch/Cancel.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/size_preview.test.js mirsal/tests/js/preview_session.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~180 total changed lines including tests; hard cap6files.

### T-034 Migrate emoji editor and hover preview lifecycle [model:luna-6-high] [risk:high] [depends:T-032]

Why: F-09 — Preview request lifecycles repeat; endpoints are distinct. Trace: CT-045.

Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.

Do:

1. Move only rxPlay/rxHovPreview request ownership and RXS.pv response cache into previewSession adapters. Exact existing rxKey(rxBody(k)) and hover '|fit' keys; editor and hover channels remain separate so hovering cannot cancel editor work. Preserve size256, fit behavior, sim/extras payload, displayed ghost and error wording. Existing300/220ms debounce semantics remain. Test stale editor/hover replies and64-entry eviction with fakes.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/preview_session.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~220 total changed lines including tests; hard cap6files.

### T-035 Migrate preset-card preview cache [model:6.1-sol-medium] [risk:medium] [depends:T-032, T-034]

Why: F-09 — Preview request lifecycles repeat; endpoints are distinct. Trace: CT-046.

Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.

Do:

1. Adapt only rxPresetPreviews/RXS.ppv using separate preview channel, key preset id+token+exact JSON settings, size RXPX and fit:true. Preserve ordering/throttled serial iteration and redraw behavior; do not replace editor/hover cache or batch watcher. Invalidated preset changes may not reuse old metadata;64-entry cap is explicit.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/preview_session.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~145 total changed lines including tests; hard cap150 changed lines/2files.

### T-036 Migrate saved-set burst preview lifecycle [model:luna-6-high] [risk:high] [depends:T-032]

Why: F-09 — Preview request lifecycles repeat; endpoints are distinct. Trace: CT-047.

Files: mirsal/mirsal/console/particles.js, mirsal/tests/js/pack_studio.test.js.

Do:

1. Replace only spBurstPreview busy/again/request signature/debounce lifecycle with previewSession keyed by existing spBurstPreviewKey. Preserve pack_id omission, optional preset, fxClean touched-only params + spBurstSize, size256, server shown params and never overwrite focused input. A slider during a request queues latest key; target/preset changes cannot apply stale response. No mutation/render endpoints.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/pack_studio.test.js mirsal/tests/js/particle_editor.test.js mirsal/tests/js/preview_session.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~220 total changed lines including tests; hard cap6files.

### T-037 Introduce dialog frame and focus lifecycle [model:luna-6-high] [risk:medium] [depends:T-002]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-048.

Files: mirsal/mirsal/console/ui-dialog.js (new or supplied by dependency), mirsal/mirsal/console/app.js, mirsal/mirsal/console/index.html, mirsal/tests/js/dialog_frame.test.js (new or supplied by dependency), mirsal/tests/js/console_vm.js.

Do:

1. Implement dialogFrameHtml({title,bodyHtml,footerHtml,labelId}) -> string using shared escaped title/body/footer slots. Keep dlg(html,{onDismiss})/closeDlg adapters; add role=dialog/aria-modal/title association on dbox, save initiating focus, focus first input/button and trap Tab within active box; Escape/outside/ACT.dlgx settle dismissal once and return focus when initiating element still exists. Preserve ASK/PK callbacks and explicit rtans response. Include once after app.js; no endpoint changes. Use the common helper-fixture contract below.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/dialog_frame.test.js mirsal/tests/js/dialog_cancel.test.js mirsal/tests/js/avatar.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~260 total changed lines including tests; hard cap6files.

### T-038 Migrate text prompt dialog frame [model:6.1-sol-medium] [risk:medium] [depends:T-037]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-049.

Files: mirsal/mirsal/console/app.js, mirsal/tests/js/dialog_frame.test.js (new or supplied by dependency).

Do:

1. Use dialogFrameHtml only inside askText, preserving #askv/title/value, Cancel data-act=dlgx, Save askok, selection/focus and Enter behavior. Keep ASK result callback and ignored empty text exactly. Do not migrate confirmDlg/pickPack here.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/dialog_frame.test.js mirsal/tests/js/avatar.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~100 total changed lines including tests; hard cap150 changed lines/2files.

### T-039 Migrate confirmation dialog frame [model:6.1-sol-medium] [risk:medium] [depends:T-037]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-050.

Files: mirsal/mirsal/console/app.js, mirsal/tests/js/dialog_frame.test.js (new or supplied by dependency).

Do:

1. Use dialogFrameHtml only in confirmDlg; title stays escaped exactly once, Cancel data-act=dlgx and confirm data-act=cfok with original ok label. Preserve ASK callback/owner callers and no invocation on outside/Escape. Extend exact malicious-text/callback fixtures.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/dialog_frame.test.js mirsal/tests/js/pack_delete.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~90 total changed lines including tests; hard cap150 changed lines/2files.

### T-040 Migrate pack-picker dialog frame [model:6.1-sol-medium] [risk:medium] [depends:T-037]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-051.

Files: mirsal/mirsal/console/app.js, mirsal/tests/js/dialog_frame.test.js (new or supplied by dependency).

Do:

1. Use dialogFrameHtml only in pickPack. Preserve await loadLib, PK callback, pl rows, coverMedia, data-act=pk/data-id, #npn, pknew Create and Cancel. Keep original pack ordering and new-pack POST body outside presenter. Preserve empty sentence and string ids.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/dialog_frame.test.js mirsal/tests/js/manual_batch_action.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~140 total changed lines including tests; hard cap150 changed lines/2files.

### T-041 Migrate retime dialog frame [model:6.1-sol-medium] [risk:medium] [depends:T-037, T-002]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-052.

Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/dialog_cancel.test.js (new or supplied by dependency).

Do:

1. Use dialogFrameHtml only in retimeAsk; keep one Promise/result true|false|null,3 actions/data-v x|0|1 and explanatory sentences. Preserve12-item short-list cap, Telegram-only warning and default choice. Do not change backend retime flags or downloaded file URL. Cancellation tests cover replacement/backdrop/Escape/button.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/dialog_cancel.test.js mirsal/tests/js/dialog_frame.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~145 total changed lines including tests; hard cap150 changed lines/2files.

### T-042 Migrate collection dialog frame [model:6.1-sol-medium] [risk:medium] [depends:T-037]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-053.

Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/collection_dialog.test.js (new or supplied by dependency).

Do:

1. Use dialogFrameHtml only in ACT.colopen. Preserve #col-name maxlength40; #col-desc maxlength160 and required; optional #col-retime values1|0; #col-light Full0 selected/Light1; #col-res; Close data-act=dlgx and colsend kind/id/config-disabled. Preserve owner gate, configured notice and read-only status/short reads. No Send in test/browser acceptance.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/collection_dialog.test.js mirsal/tests/js/dialog_frame.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~145 total changed lines including tests; hard cap150 changed lines/2files.

### T-043 Migrate Telegram connection/status frames [model:luna-6-high] [risk:medium] [depends:T-037]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-054.

Files: mirsal/mirsal/console/telegram.js, mirsal/tests/js/telegram_dialog.test.js (new or supplied by dependency).

Do:

1. Migrate only tgFlow's final send/confirmation dlg to dialogFrameHtml, retaining every existing branch/form field/action, owner restriction and short-animation retime handling. Do not change tgConnectForm/tgSettingsCard/tgDone or launch tg://. Test local fixtures for configured/unconfigured/status/error flows; assert no external send on open/cancel.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/telegram_dialog.test.js mirsal/tests/js/dialog_frame.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~180 total changed lines including tests; hard cap6files.

### T-044 Introduce details-menu presenter [model:luna-6-high] [risk:medium] [depends:none]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-055.

Files: mirsal/mirsal/console/ui-menu.js (new or supplied by dependency), mirsal/mirsal/console/index.html, mirsal/tests/js/more_menu.test.js (new or supplied by dependency), mirsal/tests/js/console_vm.js.

Do:

1. Implement moreMenuHtml({label,itemsHtml,className,summaryAttrs,popClass,summaryHtml}) -> string. Emit details + summary + role=menu popover, exact caller classes and trusted prebuilt items; escape label attrs. Support gh-more/gh-pop and pm-menu existing wrapper variants; keep native details behavior and app.js outside/pick closing. Include once after app.js; test classes/menu labels and unchanged action markup. Use the common helper-fixture contract below.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/more_menu.test.js mirsal/tests/js/avatar.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~180 total changed lines including tests; hard cap6files.

### T-045 Migrate Pack more menu [model:6.1-sol-medium] [risk:medium] [depends:T-044]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-056.

Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/pack_delete.test.js.

Do:

1. Replace only drawPack's gh-more menu wrapper with moreMenuHtml; reuse identical items string in same order Rename/Public/Collection/Preview/full ZIP/chat/add/delete. Preserve conditional owner/export and disabled flags, summary btn class/title and label More for this pack. No menu action disappears.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/pack_delete.test.js mirsal/tests/js/more_menu.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~140 total changed lines including tests; hard cap150 changed lines/2files.

### T-046 Migrate Studio toolbar more menu [model:6.1-sol-medium] [risk:medium] [depends:T-044]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-057.

Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_menu.test.js.

Do:

1. Replace only gview gh-more toolbar wrapper; retain identical item expressions/order and summary btn sm/title More for this batch. Do not migrate project-map menus or any action body. Canonical emitted menu HTML is byte-identical except intentional accessibility label normalization from foundation.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/studio_menu.test.js mirsal/tests/js/more_menu.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~140 total changed lines including tests; hard cap150 changed lines/2files.

### T-047 Migrate reaction preset menu [model:6.1-sol-medium] [risk:medium] [depends:T-044]

Why: F-06 — Backdrop hides retime without settling its promise. Trace: CT-058.

Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.

Do:

1. Replace only rxPresetMenu(k) details/summary/pop wrapper using gh-more rx-pmenu and gh-pop. Preserve current Save as new, picked-preset Update/Remove actions, empty sentence Pick a preset to update or remove it, data-id and rxpdel dng style. Keep rxPresetChips outside this menu unchanged: chips own loading and motion-first ordering. Never recreate the old Load/Remove submenu from stale assets.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/more_menu.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~130 total changed lines including tests; hard cap150 changed lines/2files.

### T-048 Introduce durable inline status presenter [model:luna-6-high] [risk:medium] [depends:none]

Why: F-10 — Feedback markup repeats with different lifetimes. Trace: CT-060.

Files: mirsal/mirsal/console/ui-feedback.js (new or supplied by dependency), mirsal/mirsal/console/index.html, mirsal/tests/js/feedback_message.test.js (new or supplied by dependency), mirsal/tests/js/console_vm.js.

Do:

1. Implement statusMessageHtml({kind,text,bodyHtml,actionsHtml,live='off',className}) -> string with exactly one of escaped text or explicitly trusted prebuilt bodyHtml, plus supplied trusted action markup. Use existing warn/mut/bad classes to preserve visuals; warning/error can use explicit role/status/live mode without altering persistence. Keep toast() transient and /api/notifications persistent; no new transport or eligibility logic. Include once after app.js. Use the common helper-fixture contract below.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/feedback_message.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~180 total changed lines including tests; hard cap6files.

### T-049 Migrate collection inline validation [model:6.1-sol-medium] [risk:medium] [depends:T-048, T-042]

Why: F-10 — Feedback markup repeats with different lifetimes. Trace: CT-061.

Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/collection_dialog.test.js (new or supplied by dependency).

Do:

1. Use statusMessageHtml only for empty-description and failed-post #col-res warnings in ACT.colsend. Keep exact sentences, busy/reset behavior and original input/body fields; kind error, live polite. Preserve background terminal toast and notifications; no popup/toast substitute for validation.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/collection_dialog.test.js mirsal/tests/js/feedback_message.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~100 total changed lines including tests; hard cap150 changed lines/2files.

### T-050 Migrate burst warning presentation [model:6.1-sol-medium] [risk:medium] [depends:T-048]

Why: F-10 — Feedback markup repeats with different lifetimes. Trace: CT-062.

Files: mirsal/mirsal/console/particles.js, mirsal/tests/js/pack_studio.test.js.

Do:

1. Use statusMessageHtml for spBurstCard blocks/warnings only. Keep fxWords mapping, original block/warning order, file/no-file media, disabled/add eligibility, Use it anyway label and backend-written statuses. Preserve original fx-w/bad class variants through className adapter; no technical block becomes overridable.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/pack_studio.test.js mirsal/tests/js/feedback_message.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~130 total changed lines including tests; hard cap150 changed lines/2files.

### T-051 Migrate Studio inline stale/health warnings [model:6.1-sol-medium] [risk:medium] [depends:T-048, T-004]

Why: F-10 — Feedback markup repeats with different lifetimes. Trace: CT-063.

Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_poll.test.js (new or supplied by dependency).

Do:

1. Use statusMessageHtml only in tick's #ghealth stale-server and no-VP9 notices, with exact existing trusted code fragments as caller body/action slots; use text escape for dynamic errors. Preserve condition/order, system-health diagnostics and current message refresh behavior. Do not convert rejected-picture warnings or generic say() here.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/studio_poll.test.js mirsal/tests/js/feedback_message.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~145 total changed lines including tests; hard cap150 changed lines/2files.

### T-052 Introduce decision-status presentation adapter [model:luna-6-high] [risk:high] [depends:none]

Why: F-13 — Decision reason boxes need one UI presentation adapter. Trace: CT-064.

Files: mirsal/mirsal/console/ui-decision.js (new or supplied by dependency), mirsal/mirsal/console/index.html, mirsal/tests/js/decision_status.test.js (new or supplied by dependency), mirsal/tests/js/console_vm.js.

Do:

1. Implement decisionStatusHtml({reason,eligible,allowed,actionAttrs,labels,context}) -> string. reason is escaped; eligible/allowed are supplied from current server-backed adapters, never inferred here. Preserve variants context='studio-box'|'studio-overlay'|'chat-tile' and caller's button class/data-* strings, label and technical-block explanation. Helper returns status/action markup only; picture/bulk control remain owned by callers. Pin identical representative allowed/blocked/technical fragments and one-time VM helper loading.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/decision_status.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~230 total changed lines including tests; hard cap6files.

### T-053 Migrate blocked still/animation reason box [model:6.1-sol-medium] [risk:high] [depends:T-052]

Why: F-13 — Decision reason boxes need one UI presentation adapter. Trace: CT-065.

Files: mirsal/mirsal/console/studio-tiles.js, mirsal/tests/js/allow_tiles.test.js.

Do:

1. Replace only blockedBox's status/action construction with decisionStatusHtml; retain A=ALW result, reason fallback and A.can eligibility, still/anim labels and exact cellAct attributes. Preserve gBad/gbadmsg wrappers, adjacent picture and title. Extend existing fixtures for blocked overridable, blocked technical, already allowed and missing allow data; no new decision code.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/allow_tiles.test.js mirsal/tests/js/cell_op.test.js mirsal/tests/js/decision_status.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~140 total changed lines including tests; hard cap150 changed lines/2files.

### T-054 Migrate blocked animation overlay [model:6.1-sol-medium] [risk:high] [depends:T-052]

Why: F-13 — Decision reason boxes need one UI presentation adapter. Trace: CT-066.

Files: mirsal/mirsal/console/studio-tiles.js, mirsal/tests/js/allow_tiles.test.js.

Do:

1. Replace only blockedAnimOverlay reason/button construction; retain gblockover wrapper, A.why/ANIMWHY fallback, original cellAct animation attributes and technical no-button case. Do not hide/replace the blocked picture. Pin byte-identical representative fragment plus reason/override adjacency.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/allow_tiles.test.js mirsal/tests/js/cell_op.test.js mirsal/tests/js/decision_status.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~140 total changed lines including tests; hard cap150 changed lines/2files.

### T-055 Migrate chat rejected tile status [model:luna-6-high] [risk:high] [depends:T-052]

Why: F-13 — Decision reason boxes need one UI presentation adapter. Trace: CT-067.

Files: mirsal/mirsal/console/chat-cards.js, mirsal/tests/js/chat_allow.test.js.

Do:

1. Replace only tileHTML's rejected/allowed status/action markup with decisionStatusHtml; chat allow object and its current can/undo/reason values remain authoritative. Preserve picture, red marks, agallow attrs/data-kind/data-i/data-g/data-allow, unchanged key/id/title handling and carousel links. No Studio GM dependency in Chat. Pin rule10 blocked technical/override/take-back snapshots.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/chat_allow.test.js mirsal/tests/js/sticker_id.test.js mirsal/tests/js/decision_status.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~200 total changed lines including tests; hard cap6files.

### T-056 Define semantic UI spacing/type/status tokens [model:luna-6-high] [risk:medium] [depends:none]

Why: F-19 — Presentation bypasses a shared token system. Trace: CT-068.

Files: mirsal/mirsal/console/studio.css, mirsal/mirsal/console/theme.css, mirsal/tests/js/theme.test.js.

Do:

1. Add spacing tokens --space-1..6 as8/16/24/32/40/48px; type tokens --type-large-title32px,--type-title24px,--type-headline18px,--type-body16px,--type-footnote13px. Add status tokens --status-bounds #f97316,--status-key #a855f7,--status-loop #eab308,--status-look #ec4899,--status-spec #3b82f6,--status-bad #ef4444,--status-on-accent #fff,--status-on-loop #422006 with same light/dark values initially. Keep existing --fs-* aliases unchanged and all current selectors using them until each surface task. Add .ui-footnote font-size:var(--type-footnote). Pin dark/light token availability and old token values; no palette redesign here. Also define --surface-card:var(--sf), --surface-group:var(--fill), --material-bar:var(--glass), --material-sheet:var(--glass), --border-ui:var(--bd), --focus-ui:var(--pri), --control-min-size:44px, --control-gap:8px, --icon-stroke:1.6, --motion-duration:200ms and --motion-easing:cubic-bezier(0.2,0,0,1). These are semantic aliases/units, not new palette decisions; existing selectors remain unchanged until their surface task.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/theme.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~130 total changed lines including tests; hard cap6files.

### T-057 Tokenize diagnostic categories without recoloring [model:6.1-sol-medium] [risk:medium] [depends:T-056]

Why: F-19 — Presentation bypasses a shared token system. Trace: CT-069.

Files: mirsal/mirsal/console/studio-tiles.js, mirsal/tests/js/cell_op.test.js.

Do:

1. Replace only CAT color tuple literals at file start with CSS var strings for the exact status tokens, keeping category order/labels. White foreground -> --status-on-accent, loop #422006 -> --status-on-loop. Ensure all consumers are CSS/SVG presentation and never canvas before substitution; if a canvas use is found, leave that literal and record it for bounded follow-up. Pin issue markup vars and compare computed colors in light/dark screenshot fixtures.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/cell_op.test.js mirsal/tests/js/allow_tiles.test.js mirsal/tests/js/theme.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~100 total changed lines including tests; hard cap150 changed lines/2files.

### T-058 Replace unconditional edge synchronization clock [model:luna-6-high] [risk:medium] [depends:T-013, T-004]

Why: F-05 — Refresh loops can overlap and redraw twice. Trace: CT-072.

Files: mirsal/mirsal/console/live.js, mirsal/mirsal/console/studio-core.js, mirsal/tests/js/edge_preview.test.js (new or supplied by dependency).

Do:

1. Remove only live.js800-ms egSync/applyEdgePreview interval. At tick's existing successful generation-key-change/force redraw point, call egSync before existing applyEdgePreview; retain showPanel/input/change/pointerup/scroll/resize calls. No synchronization when no relevant view exists. Pin updated committed outline/trim and active slider preservation after fake generation refresh; preview cancel/apply unchanged. Do not treat this DOM synchronization as server polling.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/edge_preview.test.js mirsal/tests/js/studio_poll.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~190 total changed lines including tests; hard cap6files.

### T-059 Reflow packs.js bounded helpers [model:6.1-sol-medium] [risk:low] [depends:none]

Why: F-11 — Long-line scripts make small changes expensive to review. Trace: CT-077.

Files: mirsal/mirsal/console/packs.js.

Do:

1. Reflow only named helper bodies pkGroups and pkGroupHead; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/pack_delete.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~145 total changed lines including tests; hard cap150 changed lines/2files.

### T-060 Reflow live.js bounded helpers [model:6.1-sol-medium] [risk:low] [depends:none]

Why: F-11 — Long-line scripts make small changes expensive to review. Trace: CT-078.

Files: mirsal/mirsal/console/live.js.

Do:

1. Reflow only named helper bodies egCard and egCommitted; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/history_card.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~145 total changed lines including tests; hard cap150 changed lines/2files.

### T-061 Reflow particles.js bounded helpers [model:6.1-sol-medium] [risk:low] [depends:none]

Why: F-11 — Long-line scripts make small changes expensive to review. Trace: CT-079.

Files: mirsal/mirsal/console/particles.js.

Do:

1. Reflow only named helper bodies spBurstState and spBSlider; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/particle_editor.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~145 total changed lines including tests; hard cap150 changed lines/2files.

### T-062 Reflow reactions.js bounded helpers [model:6.1-sol-medium] [risk:low] [depends:none]

Why: F-11 — Long-line scripts make small changes expensive to review. Trace: CT-080.

Files: mirsal/mirsal/console/reactions.js.

Do:

1. Reflow only named helper bodies rxBody and rxFields; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/reactions.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it.

Size: ~145 total changed lines including tests; hard cap150 changed lines/2files.

### T-063 Correct retired-History wording [model:6.1-sol-medium] [risk:low] [depends:none]

Why: F-20 — History retirement prose contradicts active route. Trace: CT-085.

Files: docs/waiting-for-haitham.md.

Do:

1. In item34 only, replace fact 'nothing in rail opens it'/'retired' with current owner-avatar Watch folders route #/history, loaded history.js and active /api/watch refresh. Retain the owner's keep/delete decision as unanswered; recommendation may say keep until the active owner workflow has an approved replacement and recorded baseline retirement. Do not delete code or decide W33 React removal.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: Docs-only: zero tests; verify exact anchors/links/byte limits and the stated acceptance.

Size: ~40 total changed lines including tests; hard cap150 changed lines/2files.

### T-064 Refresh generated inventory counts after repairs [model:6.1-sol-medium] [risk:low] [depends:T-001]

Why: F-21 — Inventory unique count omits the extra overwrite. Trace: CT-086.

Files: docs/ui_inventory.md.

Do:

1. Regenerate/read console inventory using python -m mirsal.console.inventory from mirsal/ in measure-only mode; update this doc's heading/table from current actual definitions and unique ACT names. Confirm ggo remains intentional override and gkeepsize has one definition. Preserve baseline data/routes; current review snapshot was481 unique/483 definitions, after CT-001 expected481/482 unless an authorized concurrent change exists. Record current measured values, never hard-code the stale482 unique.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: Docs-only: zero tests; verify exact anchors/links/byte limits and the stated acceptance.

Size: ~100 total changed lines including tests; hard cap150 changed lines/2files.

### T-065 Clear the cover badge hit area [model:6.1-sol-medium] [risk:low] [depends:none]

Why: F-24 — Cover badge intercepts Timeline click. Trace: UX-01.

Files: mirsal/mirsal/console/studio.css.

Do:

1. Add pointer-events:none only to the decorative .badge2 cover overlay inside #pkgrid .cell. Keep badge position, text, z-order and every hover button. Do not use force clicks or disable the cell dispatcher.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/pack_delete.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. J3 first cover-card Timeline native pointer click opens #/animate for that same id; Preview/Edit/Cover/Delete remain hit-testable, keyboard and selection unchanged.

Size: ~25 total changed lines including tests; hard cap150 changed lines/2files.

### T-066 Apply44px targets through semantic control tokens [model:luna-6-high] [risk:medium] [depends:T-056]

Why: F-22 — Tap targets are too small across core journeys. Trace: UX-02.

Files: mirsal/mirsal/console/studio.css, mirsal/mirsal/console/agent.css, mirsal/mirsal/console/theme.css.

Do:

1. Use the control44 token for .btn.sm, .gseg button, .set-nav button, .rx-h [data-act=rxclose], .rx-gh .link and non-inline icon actions; enlarge actual hit areas with padding/min-size, not a visual glyph. Separate repeated secondary/destructive controls by8px; keep inline sentence links and media-overlay cell geometry intentional. Bound changes to shared controls and J1/J3/J4/J5/J8/J11; retain rail width, sidebar geometry and all data-act. Decide bounded wrapping at390px while preserving all controls.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/theme.test.js mirsal/tests/js/studio_menu.test.js mirsal/tests/js/reactions.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. Compare1440 and390px: named controls have≥44×44px clickable rects, no overlapping targets/page horizontal scroll; all overrides stay beside their pictures.

Size: ~180 total changed lines including tests; hard cap6files.

### T-067 Present Apply/Cancel tests as responsive sheets [model:luna-6-high] [risk:medium] [depends:T-012, T-013]

Why: F-02 — Two Apply/Cancel presenters drift. Trace: UX-03.

Files: mirsal/mirsal/console/ui-testcard.js (new or supplied by dependency), mirsal/mirsal/console/studio.css, mirsal/tests/js/ui_testcard.test.js (new or supplied by dependency).

Do:

1. Keep testCard media/loading/busy/action API. Atdesktop use a centred bounded panel; below760px use a bottom sheet with safe-area padding,44px actions and max-height allowing content scroll. Apply/Cancel remain visible while preview loads; focus returns to the exact opener on Cancel. Preserve request eligibility and deferred mutation semantics. Use material only for this sheet and bars.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/ui_testcard.test.js mirsal/tests/js/size_preview.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. J1 size preview:≤1 enabled primary in the sheet; Cancel makes zero mutation requests; both themes and390px fit; no screenshot of a spinner counted as a failed preview.

Size: ~220 total changed lines including tests; hard cap6files.

### T-068 Group Studio composer and prompt metadata [model:luna-6-high] [risk:medium] [depends:T-056, T-066]

Why: F-32 — Studio prompt view is dense and exposes an engine inspector. Trace: UX-04.

Files: mirsal/mirsal/console/composer.js, mirsal/mirsal/console/studio-prompt.js, mirsal/mirsal/console/studio-core.js, mirsal/mirsal/console/studio.css, mirsal/tests/js/prompt_step.test.js.

Do:

1. Keep request/model/style/stroke and free Generate prompt discoverable. Put backend Auto/Local/Cloud diagnostics under a clearly labelled Connection details section, preserving every existing control. In the draft keep editable sheet prompt, plan status and price/unavailable explanation together; place long per-sticker metadata and later video prompt in collapsed sections. Existing exact API/control values remain read by their backends. Preserve Prompt draft/Discard and journey navigation. Use the five-type scale and8px spacing, no new inline colours.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/prompt_step.test.js mirsal/tests/js/prompt_tab.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. J1 request→free draft remains3ordinary clicks from rail/tab/prompt; disabled Generate sheet explains provider unavailability; no field/action disappears; no paid call.

Size: ~280 total changed lines including tests; hard cap6files.

### T-069 Clarify Studio primary versus recovery actions [model:luna-6-high] [risk:medium] [depends:T-053, T-066]

Why: F-22 — Tap targets are too small across core journeys. Trace: UX-05.

Files: mirsal/mirsal/console/studio-core.js, mirsal/mirsal/console/studio-tiles.js, mirsal/mirsal/console/studio.css, mirsal/tests/js/allow_tiles.test.js.

Do:

1. Keep exactly one principal stage action visually primary in the batch view; make per-picture Use it anyway/Take it back and bulk recovery clear tinted/secondary actions without moving or hiding them. Preserve stage-specific disabled reasons and eligibility from API. Group batch tools separately from tile sizing/approval. Apply shared spacing/type/status tokens; do not reduce the scope/count of any bulk action.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/allow_tiles.test.js mirsal/tests/js/cell_op.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. J6 G001 retains picture+plain reason+override forS2/S9 and Take it back forS1/S7; J1 batch hasone stage primary while every recovery remains visible/reversible.

Size: ~220 total changed lines including tests; hard cap6files.

### T-070 Disclose advanced emoji motion and group batch actions [model:luna-6-high] [risk:medium] [depends:T-025, T-066]

Why: F-25 — Reaction editor and batch controls compete for space. Trace: UX-06.

Files: mirsal/mirsal/console/reactions.js, mirsal/mirsal/console/studio.css, mirsal/tests/js/reactions.test.js.

Do:

1. Keep the current scrolling/load-more wall, search and Done/Not done filters. Group basic motion/speed/gravity and size as named inset sections; move rotation/spread/variation/hue into one collapsed Advanced summary that includes current values. Keep selected preset chips and current Presets Update/Remove ownership. Put selection count/look/Create selected together, separate from random-motion All/Not done actions; preserve Select all over the full filtered1898-bank, Shift range, exports and run Cancel. Onphone keep preview and44px primary footer visible without hiding the remaining sliders.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/reactions.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. Current happy→love Shift selects5; every descriptor/default/touched override and body JSON is identical; Reset/preset/version controls work; desktop/390px no overflow; no batch/render pressed.

Size: ~260 total changed lines including tests; hard cap6files.

### T-071 Apply the already-tracked saved-set disclosure cleanup [model:luna-6-high] [risk:medium] [depends:T-024, T-066]

Why: F-25 — Reaction editor and batch controls compete for space. Trace: UX-07.

Files: mirsal/mirsal/console/particles.js, mirsal/mirsal/console/packs.js, mirsal/mirsal/console/studio.css, mirsal/tests/js/particle_editor.test.js.

Do:

1. Implement plan.md UIcleanup1–4: set-card cell/picked/made-for metadata onhover/focus, cost only when spent; Duplicate/Rename/Delete in the existing more-menu pattern; unlink list behind Manage stickers with Attached toN summary; show selected motion preset and Change; one Advanced summary for reaction count/spin/resolution. Preserve preview/name/open/attach/add, exact ids, assign/unlink eligibility and every parameter/backend action. Keep burst downloads and pack reaction/sticker separation. Do not implement plan.md no-tabs, new save workflow or erosion feature.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/particle_editor.test.js mirsal/tests/js/particle_scope.test.js mirsal/tests/js/pack_particles.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. J5 openedP010 remains fully manageable; no raw-id unlink wall by default; keyboard exposes the same metadata/menu;48+controls are disclosed without losing any action.

Size: ~300 total changed lines including tests; hard cap6files.

### T-072 Build Settings shortcuts from mounted cards [model:luna-6-high] [risk:medium] [depends:T-022]

Why: F-26 — Local Account shortcut is a no-op. Trace: UX-08.

Files: mirsal/mirsal/console/settings.js, mirsal/mirsal/console/auth.js, mirsal/mirsal/console/tickets.js, mirsal/tests/js/auth.test.js, mirsal/tests/js/tickets.test.js.

Do:

1. Add a settings-section registry containing existing ids/labels including Tickets, then filter by actually mounted cards only after the current render wrappers finish. Rebuild the bar when auth/tickets cards mount; avoid recursion and preserve existing wrapper order. Non-LAN must not emit Account when au-me is absent; LAN keeps Account. Add Tickets only for roles that mount its card; keep all section ids/ACT.setgo and current backend routes. Do not invent Spending controls.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/auth.test.js mirsal/tests/js/tickets.test.js mirsal/tests/js/theme.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. J8 every visible shortcut scrolls to a real card; Tickets reachable without traversing allTrash; non-LAN0dead Account; fake-LAN/member/admin fixtures preserve privacy.

Size: ~200 total changed lines including tests; hard cap6files.

### T-073 Make Help list titles native keyboard controls [model:luna-6-high] [risk:medium] [depends:T-066]

Why: F-28 — Help rows are click-only divs. Trace: UX-09.

Files: mirsal/mirsal/console/support.js, mirsal/mirsal/console/studio.css, mirsal/tests/js/support.test.js.

Do:

1. Replace click-only conversation/queue/FAQ title regions with native button elements retaining suopen/suq/sufaq and data ids. Keep sibling delete/menu actions outside buttons to avoid invalid nested buttons. Add visible focus and full-width44px hit areas using current row classes. Preserve selected/scroll/filter state, source chips, owner/staff visibility and existing conversations/FAQ backend behavior.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/support.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. Tab reaches issue/queue/FAQ titles and Enter/Space opens the same record; mouse selection unchanged; no support submission/FAQ publish during acceptance.

Size: ~190 total changed lines including tests; hard cap6files.

### T-074 Give welcome slides their own readable surface palette [model:luna-6-high] [risk:low] [depends:T-056]

Why: F-30 — Dark welcome text fades into pale artwork. Trace: UX-10.

Files: mirsal/mirsal/console/studio.css, mirsal/mirsal/console/theme.css.

Do:

1. Define --wl-ink:#123546 and --wl-ink2:#345969 for the existing pale slide text region in both themes, with a solid/light backing only if artwork pixel contrast still fails. Replace only .wl-meta title/body general ink uses; keep artwork, film, cards and media pixels unchanged. Expand .wl-d hit regions to44px while leaving dot glyphs small; preserve selected tabs/Skip/opt-out and animation behavior.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/welcome.test.js mirsal/tests/js/theme.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. Settled One idea slide is readable inboth themes, measured4.5:1 normal/3:1large text; dot hit rect≥44px and no overlap; reduced-motion and Escape still work.

Size: ~90 total changed lines including tests; hard cap6files.

### T-075 Expose additive public-pack sticker/reaction counts [model:luna-6-high] [risk:high] [depends:none]

Why: F-29 — Public/Home totals count reactions as stickers. Trace: UX-11.

Files: mirsal/mirsal/media/library.py, mirsal/mirsal/flow/trending.py, mirsal/mirsal/console/app.py, mirsal/tests/test_trending.py, mirsal/tests/test_library.py, docs/api-parts/pack-counts.md (new or supplied by dependency).

Do:

1. Inspect the existing Library serialization and public Trending summary builders and native/legacy adapter first. Introduce one backend pack_counts helper under media/library.py using the documented source.particle_set distinction after existing visibility filtering; expose additive sticker_count/reaction_count on both personal library and public summaries. Public summary delegates to the same count owner. Retain every existing JSON field/value, route, total and permission filter. If app.py delegates transparently, avoid duplicate logic there. No count decision moves into JS. Test static-only/mixed/reaction-only and owner/member visibility; document additive fields/absent-field compatibility.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers. Only the two named additive count fields are permitted.

Accept: From mirsal/: python -m unittest tests.test_trending tests.test_library tests.test_ui_inventory Angel summary9stickers/1reaction; Batman17/2; old clients still receive byte-identical old fields; no real public share or external call.

Size: ~280 total changed lines including tests; hard cap6files.

### T-076 Use public summary counts in Trending labels [model:6.1-sol-medium] [risk:low] [depends:T-075]

Why: F-29 — Public/Home totals count reactions as stickers. Trace: UX-12.

Files: mirsal/mirsal/console/trending.js, mirsal/tests/js/imports_trending.test.js.

Do:

1. Render sticker_count with the word stickers and an optional separate reaction_count label. When additive fields are absent, keep the previous label exactly; never infer by subtracting unknown arrays. Preserve likes/comments/use/delete/share controls and ids, request URLs and role checks.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/imports_trending.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. J8 cards agree with their sidebar forAngel9+1 andBatman17+2; nothing is shared/liked/commented by acceptance.

Size: ~80 total changed lines including tests; hard cap150 changed lines/2files.

### T-077 Keep Home totals consistent with the backend [model:6.1-sol-medium] [risk:low] [depends:T-075]

Why: F-29 — Public/Home totals count reactions as stickers. Trace: UX-13.

Files: mirsal/mirsal/console/home.js, mirsal/tests/js/home.test.js.

Do:

1. Use additive backend sticker/reaction totals for Home summary only when present; retain old field fallback and current showcase filtering. Preserve gallery media nodes onsearch/resize, routes, all shortcuts and per-person/owner rules. Do not change the ambiguous reaction shortcut destination withoutQ1.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/home.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. Home headline count matches the same classification asTrending/Library; films are not replaced by search/resize; no horizontal page scroll.

Size: ~100 total changed lines including tests; hard cap150 changed lines/2files.

### T-078 Expose all four Library choices at phone width [model:6.1-sol-medium] [risk:low] [depends:T-066]

Why: F-35 — Phone Library tabs locally exceed their row. Trace: UX-14.

Files: mirsal/mirsal/console/studio.css.

Do:

1. At≤760px only, make #s-library .tabs a two-column equal-widthgrid with min-width:0 and8px gaps. Preserve Recent/My Stickers/Reactions/Trending order, text/actions and pressed state. Keep desktop layout unchanged; use inherited44px targets. Do not widen the document or hide a tab.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: From repo root: node --test mirsal/tests/js/theme.test.js Inventory from mirsal/ when actions/markup/script wiring change; otherwise final phase inventory covers it. At390×844 every tab is pointer/keyboard accessible, .tabs has no unintended text overflow, document has no horizontal scroll, selected content and rail remain visible.

Size: ~45 total changed lines including tests; hard cap150 changed lines/2files.

### T-079 Reconcile current UI screen contracts [model:luna-6-high] [risk:low] [depends:none]

Why: F-33 — Published screen contracts contradict each other. Trace: DOC-01.

Files: docs/design/04-4-the-shell-rules-that-hold-on-every-screen.md, docs/design/11-ui-ux-pass-of-2026-10-03-what-a-click-means.md, docs/reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md, docs/redesign_plan.md.

Do:

1. Replace stale two-row/Your reactions prose with current wall/Done/load-more/preset contract, marking historical proposals historical. Reconcile sheet-cell click semantics against the retained action map and rule10; keep current two pack tabs untilQ2 has an owner answer. State that project map/journey is built and which older proposal paragraphs are superseded. Put reaction behavior in its owner section and link from shell. Do not implement or decide Q1/Q2.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: Docs-only: zero tests; verify exact anchors/links/byte limits and the stated acceptance. Both sides of A1D01–D06 resolve to one current dated owner contract; no routes/actions/human verdicts disappear; docs-only0tests.

Size: ~300 total changed lines including tests; hard cap6files.

### T-080 Create a cheap UI reading gateway and wiring appendix [model:luna-6-high] [risk:low] [depends:T-079]

Why: F-34 — Doc organization and tracker IDs raise reading cost. Trace: DOC-02.

Files: CLAUDE.md, README.md, docs/design.md, docs/architecture.md, docs/ui_gateway.md (new or supplied by dependency), docs/architecture-ui-wiring.md (new or supplied by dependency).

Do:

1. Add docs/ui_gateway.md under1KB linking shell/tokens/recovery/currentscreen owners and test map. Extract UI wiring from architecture into a bounded appendix and link it; leave Python/module inventory out of the UI task path. Compress repeated startup/history/routing prose in CLAUDE to≤4KB while preserving all13constraints, tests/git/server authorization and scope links to full rules; do not weaken any rule. Design/README route UI tasks to the gateway. Total gateway+sharedshell/foundation+needed recovery passage must be≤8KB before code, counting inherited CLAUDE separately and reporting both totals.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: Docs-only: zero tests; verify exact anchors/links/byte limits and the stated acceptance. All links resolve; gateway≤1KB; explicit bytes for coldstart vs incremental task path; docs-only0tests.

Size: ~360 total changed lines including tests; hard cap6files.

### T-081 Correct contradictory final-block and startup wording [model:6.1-sol-medium] [risk:low] [depends:T-079]

Why: F-33 — Published screen contracts contradict each other. Trace: DOC-03.

Files: docs/rules.md, docs/agent-and-chat.md.

Do:

1. Replace the blanket Python BLOCK verdicts are final wording with the current CLAUDE rule10 distinction: only Telegram technical/no-cut failures final; every other check visibly recorded/reversible. Replace upfront read-every-tracker startup with current lean task-index/needed-section rule; trackers/devnotes/testing read only when touched. Keep historical notes explicitly historical, never change engine decision tables or user authorization.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: Docs-only: zero tests; verify exact anchors/links/byte limits and the stated acceptance. Exact rule meaning matches CLAUDE.md and verify OVERRIDABLE/TECHNICAL references;≤100changed lines/2files; docs-only0tests.

Size: ~90 total changed lines including tests; hard cap150 changed lines/2files.

### T-082 Merge tracked work and disambiguate tracker IDs [model:luna-6-high] [risk:low] [depends:T-071, T-079]

Why: F-34 — Doc organization and tracker IDs raise reading cost. Trace: DOC-04.

Files: docs/backlog.md, docs/waiting-for-haitham.md, plan.md.

Do:

1. Map implemented UXtasks to existing W1/W4/W16/W18/W19/W20/W22/W23/W33/W34/Help items before adding any tracker row. Remove only actually completed machine items from plan/backlog and write their area contract; retain pending human verdicts, paid work, Spending and held retirements. Assign the two W49 entries unique stable ids only after classifying every reference in both trackers, preserving their original dates/history and routing ambiguous references explicitly. Refresh max-id/branch metadata. Keep plan.md pack no-tabs/newsave/erosion open unless independently implemented and authorized.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: Docs-only: zero tests; verify exact anchors/links/byte limits and the stated acceptance. No duplicate ids; every moved implementation has an owning contract; no human approval item silently closed; docs-only0tests.

Size: ~200 total changed lines including tests; hard cap6files.

### T-083 Record P3 screen changes and API compatibility [model:luna-6-high] [risk:low] [depends:T-070, T-075]

Why: F-19 — Presentation bypasses a shared token system. Trace: DOC-07.

Files: docs/design/03-3-foundations.md, docs/design/05-5-per-screen.md, docs/design/09-9-every-rejected-picture-carries-its-own-overrid.md, docs/reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md, docs/api.md, docs/api-parts/pack-counts.md (new or supplied by dependency).

Do:

1. After P3 implementations, update the matching screen owner paragraphs with actual grouped-controls/sheet behavior and the additive count contract. Link pack-counts from the API index; preserve old payload semantics. Record fixture-backed picture/reason/action parity and remaining phone/paid/LAN limits; never claim unexecuted acceptance. Keep held product alternatives and advance human trackers only on an actual verdict. Commit these area changes in the same P3 phase as the source.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: Docs-only: zero tests; verify exact anchors/links/byte limits and the stated acceptance. Area docs, API index and phase commits describe exactly the implemented state; no stale before/after instructions; docs-only0tests.

Size: ~280 total changed lines including tests; hard cap6files.

### T-084 Document P2 component APIs and caller order [model:luna-6-high] [risk:low] [depends:T-055, T-058]

Why: F-03 — Grouped grids repeat presentation. Trace: DOC-06.

Files: docs/architecture.md, docs/design/03-3-foundations.md, docs/design/09-9-every-rejected-picture-carries-its-own-overrid.md.

Do:

1. Before the P2 commit, document the actual ui-* helper file names, presenter/watch/preview signatures, script load order and one-consumer migration adapters. Keep all API/backend semantics in their existing owners; state that shared UI components only present server decisions. Record bounded cache/no-overlap/cancel/focus contracts proven by narrow tests; no blanket claim that all timers or endpoints were unified. Remove superseded duplicate explanations and link one owner.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: Docs-only: zero tests; verify exact anchors/links/byte limits and the stated acceptance. P2 source and area docs land together; current screen/action/route inventory unchanged;0docs tests.

Size: ~180 total changed lines including tests; hard cap6files.

### T-085 Document P1 repairs and token ownership [model:luna-6-high] [risk:low] [depends:T-004, T-056]

Why: F-19 — Presentation bypasses a shared token system. Trace: DOC-05.

Files: docs/design/03-3-foundations.md, docs/architecture.md, docs/engine-and-studio/13-12-ui-observer.md (new or supplied by dependency).

Do:

1. Before the P1 commit, record the exact new spacing/type/status/control token names and staged-preview/cancellation invariants in the existing UI foundations and wiring owner paragraphs. Locate the Studio observer owner section through its index; use its existing section file if the listed observer filename has moved, with an exact-path preparation task before editing rather than silently broadening scope. Record non-overlapping refresh/forced-read behavior, not measured latency claims. Reflow changes require only a note that emitted markup/JSON/token streams remain identical. No new engine behavior, models or approval semantics.
2. Capture representative current markup/payload before editing; verify the named acceptance against real production code and fake/copy fixtures. Include owning phase documentation before committing.

Do not: change routes/ACT names, drop picture/reason/override or bulk recovery, change existing JSON values, move engine decisions into JS, relax owner gates, touch working media or call providers.

Accept: Docs-only: zero tests; verify exact anchors/links/byte limits and the stated acceptance. P1 source and owning docs land together; all described states have the task acceptance evidence;0docs tests.

Size: ~200 total changed lines including tests; hard cap6files.

### T-086 Give the phone viewer metadata a full-width row [model:6.1-sol-medium] [risk:low] [depends:T-066]

Why: F-36 — Phone viewer header squeezes the title into a word column. Trace: UX-15.

Files: mirsal/mirsal/console/studio.css.

Do:

1. Only at≤760px: set #modal .mbox>.mrow to grid columns44px minmax(0,1fr)44px with8px gaps. Its div:nth-child(2) metadata spans columns1–2 on row1; [data-act=lcclose] is column3,row1. [data-act=lcprev] is column1,row2; .toggles is column2,row2 with a two-column equal-widthgrid and8px gaps; [data-act=lcnext] is column3,row2. Metadata uses normal wrapping/min-width:0. Keep .mbox max-height:calc(100dvh - 24px) and overflow-y:auto so existing actions remain reachable. Desktop layout, media pixels, labels, ordering/data-act and requests remain unchanged.
2. Check the exact native phone layout and retain every action; include P3 owning documentation before committing.

Do not: change routes/ACT names/JSON, media pixels, owner gates or any backend behavior; no forced clicks.

Accept: At390×844 the metadata title area is≥240px wide instead of a word column; all4background choices/browse/Close are native hit targets; viewer/footer can scroll; no page horizontal scroll. Zero new unit tests for this CSS-only layout change.

Size:~65 total changed lines; hard cap150changedlines/2files.

### T-087 Label grouped Library counts without calling reactions stickers [model:6.1-sol-medium] [risk:low] [depends:T-075]

Why: F-29 — Library/public/Home totals count reactions as stickers. Trace: UX-16.

Files: mirsal/mirsal/console/library.js, mirsal/tests/js/packs_column.test.js.

Do:

1. In libByPackHtml group-header wording only, when LIBQ is empty and the matching backend pack summary supplies sticker_count/reaction_count, render the two explicit labels. With a filtered subset or absent additive fields, label xs.length as items rather than stickers. Preserve all items, global carousel indices, cell HTML, Open pack, selection handlers and request payloads. Do not infer classification/counts in JS or silently hide reaction thumbnails.
2. Check grouped labels/order and preserve P3 owning documentation before commit.

Do not: change routes/ACT names/JSON, item availability/carousel indices or backend decisions.

Accept: node --test mirsal/tests/js/packs_column.test.js; inventory when markup changes. Unfiltered Batman group says17stickers/2reactions; filtered3results say3items; every existing item/action remains reachable; current grouped index/order fixtures green.

Size:~100 total changed lines; hard cap150changedlines/2files.

## Questions for Haitham

1. **Which reaction door should Home present?** Keep the pack workflow with distinct labels (Home: Try pack reactions; +New: Emoji reaction effects), or route Home to the emoji wall and keep pack reactions in the pack. **Recommendation: distinct labels preserving both workflows.** Current Home→#/effects and +New→#/reactions; no task changes its destination before your verdict.
2. **Keep the two pack tabs or implement plan.md no-tabs?** **Recommendation: keep Stickers/Reactions tabs for this90%-surface pass and fix density first.** No-tabs needs an explicit authorized pktab retirement/rename baseline entry plus preserved reaction management. It remains an open proposal; no task silently deletes it.
3. **How should cloud prompt/intent expansion be priced?** W18 already tracks this. **Recommendation: free only for the built-in/local-free path; backend estimate and explicit price acceptance for a cloud call.** Decide accepted budget/wording separately. Provider-off review cannot certify cloud prices; Spending remains backend-first open work.

## Not doing

- Merging FX/SP/emoji screens: shared pieces already exist and ownership/JSON differ.
- Collapsing edge/sheet/anim/emoji endpoints or replacing all polling with SSE.
- Retiring History, parked React, literal-missing ACT/CSS candidates without evidence and owner/baseline authorization.
- Changing Telegram one-click behavior or adding a product approval flow during presentation extraction.
- Blanket reflow of scripts/templates; only bounded AST-equivalent helpers.
- Altering artwork/media/export pixels; real generation/provider/public-sharing/export completion.
- Claiming first-session media/LAN privacy/theme-focus/rejected-chat parity passed without fixtures.
- Treating loading placeholders, translated/decorative overflow, disabled-provider states or old copied ticket errors as new crashes.
- Implementing Spending, erosion, new save workflow or paid W items in this review.
- Moving all giant generated docs now; the gateway bounds UI startup, appendix maintenance is later work.

## Five before/after sketches

Conceptual boundaries, not implementation. All controls/values remain.

### 1. Studio / rejected-picture decisions (F01/F22/F23/F32)

Before: J1-03-batch-dark and J6-01-blocked-animation-dark.

```text
BEFORE                                 AFTER
composer + engine diagnostics           Request card [Model][Style][Stroke]
view modes / background / sizing        [Generate prompt]  [Advanced ▾]
journey + batch tools + video controls  Idea > Prompt > Stickers > Motion > Pack
sheet + tiles + tiny actions           Batch tools [More ▾]   [Preview size]
[Allowed by you][Take it back]          [picture] Short boundary reason
                                        [Take it back]  [Use it anyway]
                                        [Add to pack]   one stage primary
```

Every per-picture and bulk action survives; technical eligibility remains backend-owned.

### 2. Emoji reaction editor (F04/F25)

Before: J4-02-editor-dark/light and J4-04-batch-dark.

```text
BEFORE                                 AFTER
wall / filters / export / select        Search [All|Done|Not done]  [Select]
preview + eleven sliders               scrolling/load-more wall
preset chips + Presets + batches        [selected emoji preview] [Saved version]
                                        Motion [preset] [Change]   Size
                                        [Advanced: values ▾]
                                        5 selected [Look ▾] [Create selected]
                                        Batch options / Animation presets
PHONE: all editor below the wall       preview + scrollable grouped controls
                                        sticky footer [Create] [Presets ▾]
```

Full-bank Select all, Shift range, exports, preset updates/removal and run Cancel remain present.

### 3. Settings / Trash / Tickets (F26/F27/F28)

Before: J8-01-settings-dark and J8-06-tickets-bottom-dark.

```text
BEFORE                                 AFTER
Appearance|Account(no card)|...|Trash    mounted-card section navigation only
health and backend details             Appearance [Dark|Light]
nine Restore/Delete pairs              grouped cards / expandable diagnostics
Tickets after the whole Trash list     Tickets shortcut [Open queue]
                                        Trash inset list
                                        item   [Restore] [More ▾]
```

Destructive actions retain confirmation. Account appears only when its real card mounts; no unbuilt Spending control. Help titles become native buttons, secondary actions remain siblings.

### 4. Welcome contrast (F30)

Before: J7-03-welcome-settled-dark/light.

```text
BEFORE dark                            AFTER both themes
pale text over unchanged pale art      same art / film pixels
small18px tab hit regions              fixed readable slide text palette/backing
                                        small dot glyphs inside44px hit regions
                                        [Skip] / opt-out / keyboard unchanged
```

Executor measures contrast on all real slides; no recolouring media or removing motion opt-out.

### 5. Phone Library / viewer (F22/F35)

Before: J11-01-library-dark and J11-04-viewer-dark.

```text
BEFORE                                 AFTER
four choices exceed narrow row         Recent      My Stickers
small preview background switches      Reactions   Trending
dense action footer                    selected media in bounded sheet
                                        [Checker|Light|Dark|Wall]44px choices
                                        [Edit in Studio] primary
                                        Open / Move / Chat as secondary actions
                                        visible Close / browse controls
```

Keep bottom rail, packs drawer, routes, selection and every action; no global page-width increase.
