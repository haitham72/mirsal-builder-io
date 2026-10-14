# Code executor task catalog (provisional CT identifiers)

> **Concurrent implementation notice:** Evidence belongs to the audited snapshot, while another LLM advanced source during review. Reconcile current CLAUDE.md and [concurrent-work.md](concurrent-work.md) before treating a finding or task as current.

> Final handoff authority: ../uiux_plan.md and tasks.json select and reconcile 87 tasks (50 for 6.1-sol-medium, 37 for luna-6-high). CT identifiers below are a provisional task bank, not an additional execution queue.

Prepared from code_reader.md and duplication_map.md; no source changes, tests or provider calls were made while writing this catalog. The orchestrator selects/ranks these blocks and maps each C-id to the merged findings F-id. All original code line numbers are review-snapshot leads; use the named function/action anchors against current source. Preserve concurrent owner edits.

**Core: 35 blocks**, listed first. **Optional appendix: 53 blocks**, explicitly outside the core plan. Overall catalog:63 blocks for 6.1-sol-medium and 25 for luna-6-high. File lists are hard scope limits; sizes are estimated **total changed lines** including tests. Sol blocks have at most 2 files/150 changed lines and fully specified adapters; luna blocks have at most 6 files and bounded judgement. No block has more than 2 dependencies. A helper is introduced in its own task, then each consumer migrates separately. The optional appendix is a task bank, not committed execution scope; do not inflate the core plan by copying it wholesale.

Shared obligations for every source task:

- Preserve every route/ACT name, ui_baseline.json entry, owner gate, string id, recorded/reversible review, bulk override and rule10 picture/reason/action adjacency. No engine/API decisions move into JavaScript. Backend URL/body JSON is byte-identical except where a task explicitly changes *when* the same mutation occurs (CT-001).
- Browser/manual checks use only the copied-data no-spend server on8795, never8770. No Generate/Create sheet/Animate/regeneration/model execution, Send/collection export or batch job in manual acceptance. Unit tests stub APIs/timers and inspect attempted calls; they do not reach real providers.
- Run the task's listed narrow JS files in one invocation from repo root: node --test mirsal/tests/js/NAME.test.js [...]. Then from mirsal/ run python -m unittest tests.test_ui_inventory when source/markup/action/script loading changed. Docs-only tasks run **zero tests**. Never full discovery/slow tier. A pass remains valid until those files change.
- New helper tests must exercise the real exported production helper; consumer tests exercise the real named adapter with faked requests/DOM. Do not replace behavior coverage with tests of source formatting. Existing console_source.canonical is for reflow token equality only; vendored Acorn requires no installation.
- For a migration, capture current representative emitted HTML/payload before editing. Unless accessibility/interaction behavior is explicitly named, emitted text, attributes, ordering and JSON stay identical. Keep the existing CSS classes to avoid turning extraction into redesign.
- Helper foundations include a bounded console_vm integration so each module is loaded once in VM fixtures; one-consumer tests inject the real helper export into standalone statement-extraction fixtures. Do not silently broaden sol file scope: if additional fixture changes are discovered, split exact fixture prep into a separate ≤2-file mechanical block before migration, or assign a newly specified ≤6-file luna block.
- Shared CSS/script/action doc changes must be recorded in the owning area section and committed with that implementation phase. Complete phase documentation before its commit; avoid adding an unlisted documentation file to a two-file sol edit. The orchestrator supplies the matching phase-doc task. Nothing in this catalog authorizes deleting a candidate merely because a static scan missed its caller.

C-01/C-05/C-06 are repair priorities. C-02/C-03/C-07 are the three broad presentation extractions. C-04/C-08/C-09/C-10/C-12/C-13 follow without conflating distinct contracts. C-11/C-19 are bounded mechanical work. C-16/C-17 are evidence-only until retirement is proved and approved; C-18/C-14/C-15 are lower-payoff specification/deferred work; C-20/C-21 reconcile documentation with current active code.


## Core executor blocks —35

### CT-001 — Restore staged Keep approved size [model: 6.1-sol-medium] [risk: low] [depends: none]

Why: C-01 (code_reader.md).
Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/size_preview.test.js.
Do: Delete only the late ACT.gkeepsize assignment originally at901–911; retain the858 staged implementation and all other ACT names. Test with stubbed API/GM and the existing console_vm/source helpers: click changes VZ.keep and reads anim_preview; no keep_size/video_size POST until Apply. Cancel makes zero mutation calls; Apply sends the original {on,reslice} body once; technical failures retain the preview.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/size_preview.test.js mirsal/tests/js/anim_create.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-002 — Settle retime on every dialog cancellation [model: luna-6-high] [risk: medium] [depends: none]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/app.js, mirsal/mirsal/console/packs.js, mirsal/tests/js/dialog_cancel.test.js.
Do: Extend dlg(html,{onDismiss}={}) and closeDlg(reason='dismiss') with one active dismissal callback cleared before invocation. retimeAsk registers a callback that captures its own resolver and resolves null exactly once; ACT.rtans clears RTA/callback before closing and returns only true/false/null. Opening a replacement dialog cancels the prior request. Preserve dlg(html) callers; backdrop and ACT.dlgx use the same close path. Do not add Escape handling until dialog lifecycle task.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/dialog_cancel.test.js mirsal/tests/js/pack_delete.test.js; inventory check as specified above.
Size: ~160 total changed lines; hard cap 6 files.

### CT-003 — Coalesce duplicate queue clock redraws [model: 6.1-sol-medium] [risk: low] [depends: none]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/live.js, mirsal/tests/js/queue_clock.test.js.
Do: Remove only the second1000-ms interval at live.js:191. Retain the first interval at185 byte-for-byte, including data-lvt updates and its original active/run predicate. Add a stub-clock test proving one queue1000-ms interval registration and one drawLive call per clock tick for REQUESTED/CLAIMED work. Preserve qRefresh/qtoggle, all queue ACT names and saved QO; incremental DOM rendering is a separate design task.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/queue_clock.test.js mirsal/tests/js/job_recovery.test.js; inventory check as specified above.
Size: ~80 total changed lines; hard cap 150/2 files.

### CT-004 — Serialize Studio refreshes and retain force requests [model: luna-6-high] [risk: medium] [depends: none]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_poll.test.js.
Do: Add a tick in-flight flag and one pending-force flag. Concurrent tick(true) must queue one force refresh after the current read completes; intervals may not overlap. Release both flags on every failure via finally. Skip interval work while document.hidden, but explicit force requests and required open-modal refreshes retain current behavior. Read each original URL/body and preserve glast/typing guard/404 session cleanup. Use fake slow reads and hidden-state tests; do not change server polling cadence here.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/studio_poll.test.js mirsal/tests/js/prompt_tab.test.js; inventory check as specified above.
Size: ~170 total changed lines; hard cap 6 files.

### CT-005 — Introduce resource watcher lifecycle [model: luna-6-high] [risk: medium] [depends: CT-004]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/ui-watch.js, mirsal/mirsal/console/index.html, mirsal/tests/js/ui_watch.test.js, mirsal/tests/js/console_vm.js.
Do: Implement watchResource({key,intervalMs,enabled,read,onValue,onError,isTerminal,signature,visibility}) -> {start,stop,refresh}. Exactly one read at a time; refresh(true) retains one pending force; next timeout begins after settle. Terminal/stop disposes timers; failure calls onError then reschedules while enabled. visibility is explicit 'visible'|'always'; no default policy guessing. Export pure/testable helper with no DOM reads at module load. Include once after app.js and before consumers. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files. enabled=false skips reads and continues only cheap enabled checks until explicit stop/terminal; caller route transitions do not create parallel instances. Visibility policy skips read while hidden without marking a running job terminal. Cover disable/re-enable without manual new watcher.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~230 total changed lines; hard cap 6 files.

### CT-006 — Migrate collection export watcher [model: 6.1-sol-medium] [risk: medium] [depends: CT-005]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/collection_watch.test.js.
Do: Replace only colWatch scheduling with watchResource; keep its public colWatch(id,tries=0). Policy:2500ms, always visible/offscreen, stop on404, done, failed or tries>720; preserve done/failed toast wording and no duplicate terminal toast. read remains GET collection/exports/{encoded id}; never initiate an export in tests. Exact failed-read/retry-limit fixtures.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/collection_watch.test.js mirsal/tests/js/pack_delete.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-007 — Migrate reaction batch watcher [model: 6.1-sol-medium] [risk: medium] [depends: CT-005]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
Do: Adapt rxWatch/rxRun's runT scheduling to watchResource at RXPOLL1500. Preserve original reaction batch id capture, running/terminal decisions, fresh-token progress, RXS.done reset and redraw points. Off-route background batches keep original continuation policy; no new batch request. Extend existing reactions tests with terminal-once, failure recovery and stopped watcher fixtures.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-008 — Migrate effect-run watcher [model: 6.1-sol-medium] [risk: medium] [depends: CT-005]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/effects.js, mirsal/tests/js/effects_core.test.js.
Do: Replace fxPoll's timeout with one watcher per X.who/eid at2200ms; enabled=original fxBusy(X)&&X.alive(). read uses fxLoad(X), which retains original state-token guard. Keep fxSig and X.last redraw check; stop/dispose on fxReset and eid switch. Do not share FX/SP state or merge their screens.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/effects_core.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-009 — Migrate saved-set drawing watcher [model: 6.1-sol-medium] [risk: medium] [depends: CT-005]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/particles.js, mirsal/tests/js/particle_editor.test.js.
Do: Replace only spPoll with a2500-ms watcher. While original busy predicate is true, reproduce route-specific reads exactly: Library particles calls spLibSync(true); Pack calls ptCounts(PACK_ID) and conditional spLibSync(true); off-route wakes may continue without reads. Preserve SPL.busy, cached cells invalidation and terminal behavior. Do not migrate search/slider timers.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/particle_editor.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-010 — Migrate background job reads [model: luna-6-high] [risk: medium] [depends: CT-005]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/live.js, mirsal/tests/js/live_watch.test.js.
Do: Move liveTick2500-ms registration to watcher with visibility:'always'; preserve LTB, completion/session mutations, dismissal handling, lsave and qRefresh. read/commit split must reproduce existing call/order; a force tick during a read may coalesce but cannot lose completion. Fake all network operations and assert exact session/ANIM/LIVE outcomes for completed sheet/video and failed job.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/live_watch.test.js mirsal/tests/js/job_recovery.test.js; inventory check as specified above.
Size: ~200 total changed lines; hard cap 6 files.

### CT-019 — Introduce shared test-card presenter [model: luna-6-high] [risk: medium] [depends: CT-001]

Why: C-02 (code_reader.md).
Files: mirsal/mirsal/console/ui-testcard.js, mirsal/mirsal/console/index.html, mirsal/tests/js/ui_testcard.test.js, mirsal/tests/js/console_vm.js.
Do: Implement testCard({id,media:{kind,src,alt},caption,anchor,loading,busy,applyAct,cancelAct}) -> {update,close}. Reuse existing egcimg/egbadge/egccap/egcbtn classes and exact labels/ids; support image or autoplay loop muted playsinline video. Width min(300,innerWidth-24); same 12px horizontal clamp and 70px/min(innerHeight-width-110,anchor.bottom+8 or90) top clamp. Only owned DOM, no API/policy. Include once after app.js. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/ui_testcard.test.js; inventory check as specified above.
Size: ~230 total changed lines; hard cap 6 files.

### CT-020 — Migrate video-size test card [model: 6.1-sol-medium] [risk: medium] [depends: CT-019, CT-001]

Why: C-02 (code_reader.md).
Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/size_preview.test.js.
Do: Replace only vzCard DOM construction/update/position with testCard. Adapter computes existing target/caption, source/spinner, busy state and anchor expression; preserve #vzcard, gvsize/gkeepsize anchor choices and vzapply/vzcancel. Scroll/resize still update placement. Do not change VZ.n, endpoints or tick calls.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/size_preview.test.js mirsal/tests/js/ui_testcard.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-021 — Migrate edge test card [model: 6.1-sol-medium] [risk: medium] [depends: CT-019]

Why: C-02 (code_reader.md).
Files: mirsal/mirsal/console/live.js, mirsal/tests/js/edge_preview.test.js.
Do: Replace only egCard DOM construction/update/position with testCard. Preserve #egcard image/caption and egapply/egundo. Keep modal-overlay route, egDirty/egClear, 40-ms debounce and stored-snapshot undo semantics. Set busy from EG.busy without changing eligibility; test dirty-cancel is zero POST while committed undo retains original body.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/edge_preview.test.js mirsal/tests/js/ui_testcard.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-022 — Introduce grouped-grid presentation helper [model: luna-6-high] [risk: medium] [depends: none]

Why: C-03 (code_reader.md).
Files: mirsal/mirsal/console/ui-grouped-grid.js, mirsal/mirsal/console/index.html, mirsal/tests/js/grouped_grid.test.js, mirsal/tests/js/console_vm.js.
Do: Implement groupedGridHtml({groups,rootAttrs,groupAttrs,headerHtml,cellHtml}) -> string. Emit one outer container and section+header+grid per group, preserving caller-provided attributes/markup; headerHtml(group), cellHtml(item,index,group) use original caller indices carried in items. No grouping/sorting/selection mutations inside helper. Include once after app.js; test flat index/order, labels and emitted root/group/cell attributes. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/grouped_grid.test.js; inventory check as specified above.
Size: ~160 total changed lines; hard cap 6 files.

### CT-023 — Migrate Library grouped grid [model: 6.1-sol-medium] [risk: medium] [depends: CT-022]

Why: C-03 (code_reader.md).
Files: mirsal/mirsal/console/library.js, mirsal/tests/js/grouped_grid.test.js.
Do: Use groupedGridHtml inside libByPackHtml only. Retain its Map-by-pack algorithm, [sticker,globalIndex] pairs, SEL/selKey checks, lcopen/lsel/openpack attributes, lib-bypack/lib-pk/lib-pkh classes and empty sentence. Snapshot representative two-pack HTML before extraction, assert byte equality after migration including cap escaping and global LCL index.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/grouped_grid.test.js mirsal/tests/js/packs_column.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-024 — Migrate Pack grouped grid [model: 6.1-sol-medium] [risk: medium] [depends: CT-022]

Why: C-03 (code_reader.md).
Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/grouped_grid.test.js.
Do: Replace only drawPack's pk-bybatch section/grid iteration. Keep pkGroups/pkGroupHead outputs, non-Studio last group, original sticker order, all drag/cover/reaction/hover/name/selection attributes and disabled owner actions. Snapshot exact representative HTML before extraction and compare unchanged output; no change to reaction tab markup.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/grouped_grid.test.js mirsal/tests/js/pack_delete.test.js mirsal/tests/js/manual_batch_action.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-025 — Introduce semantic segmented presenter [model: luna-6-high] [risk: medium] [depends: none]

Why: C-07 (code_reader.md).
Files: mirsal/mirsal/console/ui-segment.js, mirsal/mirsal/console/index.html, mirsal/tests/js/segmented.test.js, mirsal/tests/js/console_vm.js.
Do: Implement segmentedHtml({label,mode,items,selected,className}) -> string. choice: role=group plus button aria-pressed; tabs: role=tablist/buttons role=tab + aria-selected + roving tabindex; navigation: nav aria-label with aria-current=page on selected. Keep data attributes supplied in items.attrs and ACT names verbatim; no state/persistence logic. Escape labels and values. Include once after app.js. Provide delegated keyboard handling restricted to role=tab within helper-emitted tablists: Left/Right wrap focus and call the target button.click(), Home/End select first/last; do not intercept text inputs or choice/navigation groups. Export the handler for stub-DOM tests and install one guarded listener in browser mode. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/segmented.test.js; inventory check as specified above.
Size: ~200 total changed lines; hard cap 6 files.

### CT-026 — Migrate reaction filter segment [model: 6.1-sol-medium] [risk: medium] [depends: CT-025]

Why: C-07 (code_reader.md).
Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
Do: Replace only rxPick's All/Done/Not done segment with mode:'choice'; preserve gseg rx-f, data-act=rxfilter/data-f all|done|todo and RXQ.f. Keep counts, wall, selection, batch actions untouched. Exact selected states for each of three values and unchanged action names.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/segmented.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-027 — Migrate composer source segment [model: 6.1-sol-medium] [risk: medium] [depends: CT-025]

Why: C-07 (code_reader.md).
Files: mirsal/mirsal/console/composer.js, mirsal/tests/js/prompt_step.test.js.
Do: Replace only cpDrawBar Creative/Predefined gseg cp-act with choice mode. Preserve cpactions/data-v creative|predefined, current Creative selection whenever actions!='predefined', both tooltips and model/prompt behavior. Assert both states and original ACT.cpactions persistence/body.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/prompt_step.test.js mirsal/tests/js/segmented.test.js; inventory check as specified above.
Size: ~110 total changed lines; hard cap 150/2 files.

### CT-028 — Migrate Studio view segment [model: 6.1-sol-medium] [risk: medium] [depends: CT-025]

Why: C-07 (code_reader.md).
Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_menu.test.js.
Do: Replace only gview What to show segment with choice mode, using stickers|sheet|both, data-act=gvmode/data-v and exact tooltip strings. Preserve saved view fallback and emitted content for each state; never change tabs or routes. Extend exact marker-based VM fixture rather than test text line formatting.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/studio_menu.test.js mirsal/tests/js/segmented.test.js; inventory check as specified above.
Size: ~110 total changed lines; hard cap 150/2 files.

### CT-029 — Migrate Pack tabs segment [model: 6.1-sol-medium] [risk: medium] [depends: CT-025]

Why: C-07 (code_reader.md).
Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/pack_delete.test.js.
Do: Replace only gseg pk-tabs with mode:'tabs', keys stickers|particles, ACT.pktab/data-t unchanged. Use aria-selected and roving tabindex rather than aria-pressed; wire Left/Right/Home/End to focus/select only these two tab buttons using shared helper callback (helper keyboard support must be pinned in foundation before this task). Preserve PKTAB and rendering.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/pack_delete.test.js mirsal/tests/js/segmented.test.js; inventory check as specified above.
Size: ~130 total changed lines; hard cap 150/2 files.

### CT-030 — Migrate Settings section navigation [model: 6.1-sol-medium] [risk: medium] [depends: CT-025]

Why: C-07 (code_reader.md).
Files: mirsal/mirsal/console/settings.js, mirsal/tests/js/theme.test.js.
Do: Replace only Settings section nav using mode:'navigation'. Keep ordered IDs set-appear,au-me,set-health,staff set-prep,set-ai,set-tg,trx-box and existing setjump attributes/actions. This control scrolls to anchors, not a content tablist; preserve role/access and staff gating. Do not invent a selected pane if no state currently tracks it; navigation selected:null yields no aria-current.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/theme.test.js mirsal/tests/js/segmented.test.js; inventory check as specified above.
Size: ~120 total changed lines; hard cap 150/2 files.

### CT-048 — Introduce dialog frame and focus lifecycle [model: luna-6-high] [risk: medium] [depends: CT-002]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/ui-dialog.js, mirsal/mirsal/console/app.js, mirsal/mirsal/console/index.html, mirsal/tests/js/dialog_frame.test.js, mirsal/tests/js/console_vm.js.
Do: Implement dialogFrameHtml({title,bodyHtml,footerHtml,labelId}) -> string using shared escaped title/body/footer slots. Keep dlg(html,{onDismiss})/closeDlg adapters; add role=dialog/aria-modal/title association on dbox, save initiating focus, focus first input/button and trap Tab within active box; Escape/outside/ACT.dlgx settle dismissal once and return focus when initiating element still exists. Preserve ASK/PK callbacks and explicit rtans response. Include once after app.js; no endpoint changes. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/dialog_frame.test.js mirsal/tests/js/dialog_cancel.test.js mirsal/tests/js/avatar.test.js; inventory check as specified above.
Size: ~260 total changed lines; hard cap 6 files.

### CT-049 — Migrate text prompt dialog frame [model: 6.1-sol-medium] [risk: medium] [depends: CT-048]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/app.js, mirsal/tests/js/dialog_frame.test.js.
Do: Use dialogFrameHtml only inside askText, preserving #askv/title/value, Cancel data-act=dlgx, Save askok, selection/focus and Enter behavior. Keep ASK result callback and ignored empty text exactly. Do not migrate confirmDlg/pickPack here.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/dialog_frame.test.js mirsal/tests/js/avatar.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-050 — Migrate confirmation dialog frame [model: 6.1-sol-medium] [risk: medium] [depends: CT-048]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/app.js, mirsal/tests/js/dialog_frame.test.js.
Do: Use dialogFrameHtml only in confirmDlg; title stays escaped exactly once, Cancel data-act=dlgx and confirm data-act=cfok with original ok label. Preserve ASK callback/owner callers and no invocation on outside/Escape. Extend exact malicious-text/callback fixtures.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/dialog_frame.test.js mirsal/tests/js/pack_delete.test.js; inventory check as specified above.
Size: ~90 total changed lines; hard cap 150/2 files.

### CT-051 — Migrate pack-picker dialog frame [model: 6.1-sol-medium] [risk: medium] [depends: CT-048]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/app.js, mirsal/tests/js/dialog_frame.test.js.
Do: Use dialogFrameHtml only in pickPack. Preserve await loadLib, PK callback, pl rows, coverMedia, data-act=pk/data-id, #npn, pknew Create and Cancel. Keep original pack ordering and new-pack POST body outside presenter. Preserve empty sentence and string ids.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/dialog_frame.test.js mirsal/tests/js/manual_batch_action.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-052 — Migrate retime dialog frame [model: 6.1-sol-medium] [risk: medium] [depends: CT-048, CT-002]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/dialog_cancel.test.js.
Do: Use dialogFrameHtml only in retimeAsk; keep one Promise/result true|false|null,3 actions/data-v x|0|1 and explanatory sentences. Preserve12-item short-list cap, Telegram-only warning and default choice. Do not change backend retime flags or downloaded file URL. Cancellation tests cover replacement/backdrop/Escape/button.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/dialog_cancel.test.js mirsal/tests/js/dialog_frame.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-053 — Migrate collection dialog frame [model: 6.1-sol-medium] [risk: medium] [depends: CT-048]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/collection_dialog.test.js.
Do: Use dialogFrameHtml only in ACT.colopen. Preserve #col-name maxlength=40; #col-desc maxlength=160 and required; optional #col-retime values1|0; #col-light Full0 selected/Light1; #col-res; Close data-act=dlgx and colsend kind/id/config-disabled. Preserve owner gate, configured notice and read-only status/short reads. No Send in test/browser acceptance.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/collection_dialog.test.js mirsal/tests/js/dialog_frame.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-054 — Migrate Telegram confirmation frame [model: luna-6-high] [risk: medium] [depends: CT-048]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/telegram.js, mirsal/tests/js/telegram_dialog.test.js.
Do: Migrate only tgFlow's final send/confirmation dlg to dialogFrameHtml, retaining every existing branch/form field/action, owner restriction and short-animation retime handling. Do not change tgConnectForm/tgSettingsCard/tgDone or launch tg://. Test local fixtures for configured/unconfigured/status/error flows; assert no external send on open/cancel.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/telegram_dialog.test.js mirsal/tests/js/dialog_frame.test.js; inventory check as specified above.
Size: ~180 total changed lines; hard cap 6 files.

### CT-055 — Introduce details-menu presenter [model: luna-6-high] [risk: medium] [depends: none]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/ui-menu.js, mirsal/mirsal/console/index.html, mirsal/tests/js/more_menu.test.js, mirsal/tests/js/console_vm.js.
Do: Implement moreMenuHtml({label,itemsHtml,className,summaryAttrs,popClass,summaryHtml}) -> string. Emit details + summary + role=menu popover, exact caller classes and trusted prebuilt items; escape label attrs. Support gh-more/gh-pop and pm-menu existing wrapper variants; keep native details behavior and app.js outside/pick closing. Include once after app.js; test classes/menu labels and unchanged action markup. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/more_menu.test.js mirsal/tests/js/avatar.test.js; inventory check as specified above.
Size: ~180 total changed lines; hard cap 6 files.

### CT-056 — Migrate Pack more menu [model: 6.1-sol-medium] [risk: medium] [depends: CT-055]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/pack_delete.test.js.
Do: Replace only drawPack's gh-more menu wrapper with moreMenuHtml; reuse identical items string in same order Rename/Public/Collection/Preview/full ZIP/chat/add/delete. Preserve conditional owner/export and disabled flags, summary btn class/title and label More for this pack. No menu action disappears.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/pack_delete.test.js mirsal/tests/js/more_menu.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-057 — Migrate Studio toolbar more menu [model: 6.1-sol-medium] [risk: medium] [depends: CT-055]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_menu.test.js.
Do: Replace only gview gh-more toolbar wrapper; retain identical item expressions/order and summary btn sm/title More for this batch. Do not migrate project-map menus or any action body. Canonical emitted menu HTML is byte-identical except intentional accessibility label normalization from foundation.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/studio_menu.test.js mirsal/tests/js/more_menu.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-058 — Migrate reaction preset menu [model: 6.1-sol-medium] [risk: medium] [depends: CT-055]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
Do: Replace only rxPresetMenu(k) details/summary/pop wrapper using gh-more rx-pmenu and gh-pop. Preserve current Save as new, picked-preset Update/Remove actions, empty sentence Pick a preset to update or remove it, data-id and rxpdel dng style. Keep rxPresetChips outside this menu unchanged: chips own loading and motion-first ordering. Never recreate the old Load/Remove submenu from stale assets.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/more_menu.test.js; inventory check as specified above.
Size: ~130 total changed lines; hard cap 150/2 files.

### CT-068 — Define semantic UI spacing/type/status tokens [model: luna-6-high] [risk: medium] [depends: none]

Why: C-19 (code_reader.md).
Files: mirsal/mirsal/console/studio.css, mirsal/mirsal/console/theme.css, mirsal/tests/js/theme.test.js.
Do: Add spacing tokens --space-1..6 as8/16/24/32/40/48px; type tokens --type-large-title32px,--type-title24px,--type-headline18px,--type-body16px,--type-footnote13px. Add status tokens --status-bounds #f97316,--status-key #a855f7,--status-loop #eab308,--status-look #ec4899,--status-spec #3b82f6,--status-bad #ef4444,--status-on-accent #fff,--status-on-loop #422006 with same light/dark values initially. Keep existing --fs-* aliases unchanged and all current selectors using them until each surface task. Add .ui-footnote font-size:var(--type-footnote). Pin dark/light token availability and old token values; no palette redesign here.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/theme.test.js; inventory check as specified above.
Size: ~130 total changed lines; hard cap 6 files.

### CT-072 — Replace unconditional edge synchronization clock [model: luna-6-high] [risk: medium] [depends: CT-021, CT-004]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/live.js, mirsal/mirsal/console/studio-core.js, mirsal/tests/js/edge_preview.test.js.
Do: Remove only live.js800-ms egSync/applyEdgePreview interval. At tick's existing successful generation-key-change/force redraw point, call egSync before existing applyEdgePreview; retain showPanel/input/change/pointerup/scroll/resize calls. No synchronization when no relevant view exists. Pin updated committed outline/trim and active slider preservation after fake generation refresh; preview cancel/apply unchanged. Do not treat this DOM synchronization as server polling.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/edge_preview.test.js mirsal/tests/js/studio_poll.test.js; inventory check as specified above.
Size: ~190 total changed lines; hard cap 6 files.


## Optional task bank — outside core scope

These53 blocks are fully sized for later selection. They are not required dependencies of the35 core blocks. Evidence-only retirement/specification tasks belong in P4 or an optional follow-up; no candidate deletion is authorized.

### CT-011 — Migrate visible batch-history refresh [model: 6.1-sol-medium] [risk: medium] [depends: CT-005]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/live.js, mirsal/tests/js/history_card.test.js.
Do: Replace only the10000-ms Earlier-batches interval. enabled is !document.hidden && ['generate','create'].includes(route_); read is histLoad(false,true). Preserve HB.sig and conditional redraw. The owner Watch folders history.js interval is a separate task. Test no read while hidden/off-route and same hist rows/order.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/history_card.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~90 total changed lines; hard cap 150/2 files.

### CT-012 — Migrate provider-status refresh [model: 6.1-sol-medium] [risk: medium] [depends: CT-005, CT-010]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/live.js, mirsal/tests/js/live_watch.test.js.
Do: Replace only refreshHf20000-ms interval with watcher visibility:'always' to preserve current policy. Keep /api/higgsfield status read and composer redraw only when availability changes. Keep liveInit's initial parallel model/status reads. Tests use local stubs, never a provider.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/live_watch.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~80 total changed lines; hard cap 150/2 files.

### CT-013 — Migrate Studio reaction-section refresh [model: 6.1-sol-medium] [risk: medium] [depends: CT-005]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/particles.js, mirsal/tests/js/particle_scope.test.js.
Do: Replace spSecSync2500-ms interval using visible/generate enabled predicate. Keep SPS.busy, gpart existence, same generation-particles reads, signatures and per-batch links; no request while hidden. No change to spPoll or action ownership.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/particle_scope.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-014 — Migrate active Watch folders refresh [model: 6.1-sol-medium] [risk: medium] [depends: CT-005]

Why: C-05, C-20 (code_reader.md).
Files: mirsal/mirsal/console/history.js, mirsal/tests/js/imports_trending.test.js.
Do: Replace only history.js4000-ms interval with watcher enabled=route_==='history', visibility:'always'. Preserve hLoad and error toast. Keep the currently reachable owner-only route and script; do not implement W34 retirement. Extend existing source/VM fixture to assert /api/watch read and stop on route exit.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/imports_trending.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-015 — Add explicit terminal-await adapter [model: 6.1-sol-medium] [risk: medium] [depends: CT-005]

Why: C-12 (code_reader.md).
Files: mirsal/mirsal/console/ui-watch.js, mirsal/tests/js/ui_watch.test.js.
Do: Add awaitTerminal({read,isTerminal,intervalMs,timeoutMs,onProgress}) -> Promise<{state,value}> over the existing watcher. timeoutMs:null means no deadline; terminal result/error/timeout stops scheduling. Define state='terminal'|'timeout'|'read-error'; value retains last successful response. Never decide backend eligibility or purge policy. Cover each exit exactly once with fake timers.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-016 — Migrate removed-batch purge waiting [model: 6.1-sol-medium] [risk: medium] [depends: CT-015]

Why: C-12 (code_reader.md).
Files: mirsal/mirsal/console/live.js, mirsal/tests/js/remove_batch.test.js.
Do: In remPurge only, replace the wait loop with awaitTerminal:500ms,240 scheduled-read cap, GET trash/purges/{id}; preserve original initial response and final failed/done/refused messaging. Encode cap as an explicit local counter, not a new shared default. Preserve original refusal handling and returned outcome.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/remove_batch.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-017 — Migrate removed-batch removal waiting [model: 6.1-sol-medium] [risk: medium] [depends: CT-015]

Why: C-12 (code_reader.md).
Files: mirsal/mirsal/console/live.js, mirsal/tests/js/remove_batch.test.js.
Do: In remRemove only, adapt its500ms/240-read loop with the same explicit capped policy. Preserve original endpoint/body, local cache removal and success/refusal semantics. Cover zero-read already-terminal response and original partial/refused outcomes; no deletion against real data.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/remove_batch.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-018 — Migrate Settings trash waiting [model: 6.1-sol-medium] [risk: medium] [depends: CT-015]

Why: C-12 (code_reader.md).
Files: mirsal/mirsal/console/trash.js, mirsal/tests/js/trash.test.js.
Do: Replace trxWait loop only with awaitTerminal at1200ms and timeoutMs:null. Retain last t on failed GET and existing status handling; do not silently impose a deadline or change shared-item confirmation. Fake responses; owner-only Restore/Delete/Purge controls remain unchanged.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/trash.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-031 — Introduce range-field presenter [model: luna-6-high] [risk: medium] [depends: none]

Why: C-04 (code_reader.md).
Files: mirsal/mirsal/console/ui-range.js, mirsal/mirsal/console/index.html, mirsal/tests/js/range_field.test.js, mirsal/tests/js/console_vm.js.
Do: Implement rangeFieldHtml({label,min,max,step,value,attrs,formatValue,pairedInput,className}). pairedInput='output'|'number'|'none'; emit supplied namespace attributes unchanged on range and number only; output formatting is caller-supplied; no default/range/rounding policy. Support fx-sl label/span/output wrapper and fld/srow wrapper via explicit layout:'label-output'|'field-pair'. Include once after app.js; pin output escaping and two-input value attributes. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/range_field.test.js; inventory check as specified above.
Size: ~200 total changed lines; hard cap 6 files.

### CT-032 — Migrate saved-set burst sliders [model: 6.1-sol-medium] [risk: medium] [depends: CT-031]

Why: C-04 (code_reader.md).
Files: mirsal/mirsal/console/particles.js, mirsal/tests/js/particle_editor.test.js.
Do: Replace only spBSlider. Use original FXSL lookup, par override then shown fallback and blank-null behavior; label-output mode, class fx-sl, data-psbp and data-id exact. Do not move FXSL/default/clean parameter decisions into helper. Pin each six descriptors and focused-input handling remains outside helper.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/particle_editor.test.js mirsal/tests/js/pack_studio.test.js mirsal/tests/js/range_field.test.js; inventory check as specified above.
Size: ~110 total changed lines; hard cap 150/2 files.

### CT-033 — Migrate emoji reaction sliders [model: 6.1-sol-medium] [risk: medium] [depends: CT-031]

Why: C-04 (code_reader.md).
Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
Do: Replace only rxSlider. Retain rxVal/rxFmt and each original RXSIM/RXO min/max/step/unit/label; attrs data-rxo, existing classes/label references and preview events unchanged. Preserve sim versus extra payload keys and percent display. Pin all descriptors, nullable fallback and byte-identical rxBody JSON.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/range_field.test.js; inventory check as specified above.
Size: ~120 total changed lines; hard cap 150/2 files.

### CT-034 — Migrate edge ranges [model: 6.1-sol-medium] [risk: medium] [depends: CT-031, CT-021]

Why: C-04 (code_reader.md).
Files: mirsal/mirsal/console/live.js, mirsal/tests/js/edge_preview.test.js.
Do: Replace only edgeControlsHtml Stroke/Trim markup with label-output rangeFieldHtml. Preserve data-edge=outline|erode, outline min=0/max=24; erode min=0/max=6; both step=1/default=0 and px display. Pin exact fields before substitution; no egApply/undo semantics change.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/edge_preview.test.js mirsal/tests/js/range_field.test.js; inventory check as specified above.
Size: ~110 total changed lines; hard cap 150/2 files.

### CT-035 — Migrate still-editor range pairs [model: 6.1-sol-medium] [risk: medium] [depends: CT-031]

Why: C-04 (code_reader.md).
Files: mirsal/mirsal/console/editor.js, mirsal/tests/js/editor_ranges.test.js.
Do: Replace only sl(lbl,inp,val,min,max) implementation using field-pair layout, pairedInput:'number'; preserve data-inp on both controls and original min/max/value propagation. No transforms, canvas, content colors or range caps change. Capture all production sl callers and assert rendered attributes/number-range equality.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/editor_ranges.test.js mirsal/tests/js/ai_editor.test.js mirsal/tests/js/range_field.test.js; inventory check as specified above.
Size: ~120 total changed lines; hard cap 150/2 files.

### CT-036 — Migrate video-editor range fields [model: 6.1-sol-medium] [risk: medium] [depends: CT-031]

Why: C-04 (code_reader.md).
Files: mirsal/mirsal/console/prepare.js, mirsal/tests/js/prepare_ranges.test.js.
Do: Replace only fld/rng-composed range fields used by pinsp scale/rotation/opacity at109–111. mode field-pair/pairedInput:none retains existing DOM; preserve data-pk, min/max/step/current numeric values and payload behavior. Keep timing-number pairs, fit radios, custom canvas code and every other inspector block unchanged.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/prepare_ranges.test.js mirsal/tests/js/range_field.test.js; inventory check as specified above.
Size: ~130 total changed lines; hard cap 150/2 files.

### CT-037 — Introduce URL/blob download utility [model: luna-6-high] [risk: low] [depends: none]

Why: C-08 (code_reader.md).
Files: mirsal/mirsal/console/ui-download.js, mirsal/mirsal/console/index.html, mirsal/tests/js/ui_download.test.js, mirsal/tests/js/console_vm.js.
Do: Implement downloadFile({url,blob,filename,revokeAfterMs=4000}) with exactly one source. Append anchor, assign href/download, click, remove in finally; create object URL only for blob and revoke only helper-owned URL after specified delay. Existing URL/data-URL must never be revoked. No fetch or Telegram launch in helper. Include once after app.js; stub document/URL/timers. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/ui_download.test.js; inventory check as specified above.
Size: ~160 total changed lines; hard cap 6 files.

### CT-038 — Migrate Timeline blob download [model: 6.1-sol-medium] [risk: low] [depends: CT-037]

Why: C-08 (code_reader.md).
Files: mirsal/mirsal/console/animate.js, mirsal/tests/js/ui_download.test.js.
Do: Replace only anCall's response blob/createObjectURL/anchor/remove/revoke sequence with downloadFile({blob,filename: original sanitized A.st.name+'.'+A.fmt}). Preserve fetch/body, busy state, original 4000ms cleanup timing and save branch. Extend fixture proving filename/source ownership and zero new network requests.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/ui_download.test.js; inventory check as specified above.
Size: ~110 total changed lines; hard cap 150/2 files.

### CT-039 — Migrate video-editor blob download [model: 6.1-sol-medium] [risk: low] [depends: CT-037]

Why: C-08 (code_reader.md).
Files: mirsal/mirsal/console/prepare.js, mirsal/tests/js/ui_download.test.js.
Do: Replace only prCall's response-blob download sequence with downloadFile; preserve (e.name||P.p.name).replace(/[^\w-]+/g,'_')+'.'+e.format exactly, original 4000ms cleanup, encoding request/body and save branches. No change to project persistence/timing/canvas.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/ui_download.test.js; inventory check as specified above.
Size: ~110 total changed lines; hard cap 150/2 files.

### CT-040 — Migrate still-editor PNG download [model: 6.1-sol-medium] [risk: low] [depends: CT-037]

Why: C-08 (code_reader.md).
Files: mirsal/mirsal/console/editor.js, mirsal/tests/js/ui_download.test.js.
Do: Replace only ACT.xdl anchor construction with downloadFile({url:E.dataUrl,filename: original sanitized (E.name||'sticker')+'.png'}). Keep action name and data URL; do not fetch/revoke it. Pin fallback/special-character filenames.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/ui_download.test.js mirsal/tests/js/ai_editor.test.js; inventory check as specified above.
Size: ~80 total changed lines; hard cap 150/2 files.

### CT-041 — Migrate particle Lottie download [model: 6.1-sol-medium] [risk: low] [depends: CT-037]

Why: C-08 (code_reader.md).
Files: mirsal/mirsal/console/particles.js, mirsal/tests/js/particle_editor.test.js.
Do: Replace only ACT.psblottie success-path anchor download with downloadFile({url: original server URL,filename: original name}). Preserve original export-lottie POST, touched-only params/scale, busy button recovery and filename wording. Test fake response, never render or call a model.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/particle_editor.test.js mirsal/tests/js/ui_download.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-042 — Migrate reaction ZIP and Lottie downloads [model: 6.1-sol-medium] [risk: low] [depends: CT-037]

Why: C-08 (code_reader.md).
Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
Do: Replace only rxzip and rxdl anchor creation with downloadFile; preserve zip URL query for selected tokens, encoded join order, filename reactions.zip and individual token/id .lottie.json filename. Keep all download controls/data attributes, no fetch added. Test selected/full and individual versions.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/ui_download.test.js; inventory check as specified above.
Size: ~130 total changed lines; hard cap 150/2 files.

### CT-043 — Introduce latest-result preview session [model: luna-6-high] [risk: high] [depends: none]

Why: C-09 (code_reader.md).
Files: mirsal/mirsal/console/ui-preview.js, mirsal/mirsal/console/index.html, mirsal/tests/js/preview_session.test.js, mirsal/tests/js/console_vm.js.
Do: Implement previewSession({keyFor,request,commit,onError,maxEntries=64,debounceMs}) -> {schedule,refresh,clear,dispose}. Unique monotonic generation per request; stale responses never commit; allow one in-flight read and retain only latest queued key. Cache response metadata by exact caller key with64-entry LRU; no media blobs/artwork generated or URL rewriting. Clear/dispose cancels scheduled work and invalidates late replies. Errors release busy state. Include once after app.js. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/preview_session.test.js; inventory check as specified above.
Size: ~240 total changed lines; hard cap 6 files.

### CT-044 — Migrate size preview request lifecycle [model: luna-6-high] [risk: high] [depends: CT-043, CT-020]

Why: C-09 (code_reader.md).
Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/size_preview.test.js.
Do: Replace only VZ.t/VZ.n orchestration in vzPreview with previewSession debounce250/cache policy exact query key. Keep generation/index/scale/keep query serialization, initial clear/spinner, api anim_preview GET, metadata/caption and error toast/vzClear. VZ change/clear must invalidate prior requests; no automatic Apply. Preserve currently selected generation and test delayed old responses after target switch/Cancel.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/size_preview.test.js mirsal/tests/js/preview_session.test.js; inventory check as specified above.
Size: ~180 total changed lines; hard cap 6 files.

### CT-045 — Migrate emoji editor and hover preview lifecycle [model: luna-6-high] [risk: high] [depends: CT-043]

Why: C-09 (code_reader.md).
Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
Do: Move only rxPlay/rxHovPreview request ownership and RXS.pv response cache into previewSession adapters. Exact existing rxKey(rxBody(k)) and hover '|fit' keys; editor and hover channels remain separate so hovering cannot cancel editor work. Preserve size256, fit behavior, sim/extras payload, displayed ghost and error wording. Existing300/220ms debounce semantics remain. Test stale editor/hover replies and 64-entry eviction with fakes.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/preview_session.test.js; inventory check as specified above.
Size: ~220 total changed lines; hard cap 6 files.

### CT-046 — Migrate preset-card preview cache [model: 6.1-sol-medium] [risk: medium] [depends: CT-043, CT-045]

Why: C-09 (code_reader.md).
Files: mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
Do: Adapt only rxPresetPreviews/RXS.ppv using separate preview channel, key preset id+token+exact JSON settings, size RXPX and fit:true. Preserve ordering/throttled serial iteration and redraw behavior; do not replace editor/hover cache or batch watcher. Invalidated preset changes may not reuse old metadata;64-entry cap is explicit.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/reactions.test.js mirsal/tests/js/preview_session.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-047 — Migrate saved-set burst preview lifecycle [model: luna-6-high] [risk: high] [depends: CT-043]

Why: C-09 (code_reader.md).
Files: mirsal/mirsal/console/particles.js, mirsal/tests/js/pack_studio.test.js.
Do: Replace only spBurstPreview busy/again/request signature/debounce lifecycle with previewSession keyed by existing spBurstPreviewKey. Preserve pack_id omission, optional preset, fxClean touched-only params + spBurstSize, size256, server shown params and never overwrite focused input. A slider during a request queues latest key; target/preset changes cannot apply stale response. No mutation/render endpoints.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/pack_studio.test.js mirsal/tests/js/particle_editor.test.js mirsal/tests/js/preview_session.test.js; inventory check as specified above.
Size: ~220 total changed lines; hard cap 6 files.

### CT-059 — Migrate project-map sheet menus [model: 6.1-sol-medium] [risk: medium] [depends: CT-055]

Why: C-06 (code_reader.md).
Files: mirsal/mirsal/console/projmap.js, mirsal/tests/js/project_map.test.js.
Do: Replace only pmSheet details.pm-menu wrapper with moreMenuHtml configured to existing summary/pop classes. Preserve current/other-sheet choices, exact ggen/pmopen/data-* routing, video/branch options and app.js outside closing. Keep map hierarchy/crumbs and captured wrapper hooks untouched.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/project_map.test.js mirsal/tests/js/more_menu.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-060 — Introduce durable inline status presenter [model: luna-6-high] [risk: medium] [depends: none]

Why: C-10 (code_reader.md).
Files: mirsal/mirsal/console/ui-feedback.js, mirsal/mirsal/console/index.html, mirsal/tests/js/feedback_message.test.js, mirsal/tests/js/console_vm.js.
Do: Implement statusMessageHtml({kind,text,bodyHtml,actionsHtml,live='off',className}) -> string with exactly one of escaped text or explicitly trusted prebuilt bodyHtml, plus supplied trusted action markup. Use existing warn/mut/bad classes to preserve visuals; warning/error can use explicit role/status/live mode without altering persistence. Keep toast() transient and /api/notifications persistent; no new transport or eligibility logic. Include once after app.js. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/feedback_message.test.js; inventory check as specified above.
Size: ~180 total changed lines; hard cap 6 files.

### CT-061 — Migrate collection inline validation [model: 6.1-sol-medium] [risk: medium] [depends: CT-060, CT-053]

Why: C-10 (code_reader.md).
Files: mirsal/mirsal/console/packs.js, mirsal/tests/js/collection_dialog.test.js.
Do: Use statusMessageHtml only for empty-description and failed-post #col-res warnings in ACT.colsend. Keep exact sentences, busy/reset behavior and original input/body fields; kind error, live polite. Preserve background terminal toast and notifications; no popup/toast substitute for validation.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/collection_dialog.test.js mirsal/tests/js/feedback_message.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-062 — Migrate burst warning presentation [model: 6.1-sol-medium] [risk: medium] [depends: CT-060]

Why: C-10 (code_reader.md).
Files: mirsal/mirsal/console/particles.js, mirsal/tests/js/pack_studio.test.js.
Do: Use statusMessageHtml for spBurstCard blocks/warnings only. Keep fxWords mapping, original block/warning order, file/no-file media, disabled/add eligibility, Use it anyway label and backend-written statuses. Preserve original fx-w/bad class variants through className adapter; no technical block becomes overridable.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/pack_studio.test.js mirsal/tests/js/feedback_message.test.js; inventory check as specified above.
Size: ~130 total changed lines; hard cap 150/2 files.

### CT-063 — Migrate Studio inline stale/health warnings [model: 6.1-sol-medium] [risk: medium] [depends: CT-060, CT-004]

Why: C-10 (code_reader.md).
Files: mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_poll.test.js.
Do: Use statusMessageHtml only in tick's #ghealth stale-server and no-VP9 notices, with exact existing trusted code fragments as caller body/action slots; use text escape for dynamic errors. Preserve condition/order, system-health diagnostics and current message refresh behavior. Do not convert rejected-picture warnings or generic say() here.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/studio_poll.test.js mirsal/tests/js/feedback_message.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-064 — Introduce decision-status presentation adapter [model: luna-6-high] [risk: high] [depends: none]

Why: C-13 (code_reader.md).
Files: mirsal/mirsal/console/ui-decision.js, mirsal/mirsal/console/index.html, mirsal/tests/js/decision_status.test.js, mirsal/tests/js/console_vm.js.
Do: Implement decisionStatusHtml({reason,eligible,allowed,actionAttrs,labels,context}) -> string. reason is escaped; eligible/allowed are supplied from current server-backed adapters, never inferred here. Preserve variants context='studio-box'|'studio-overlay'|'chat-tile' and caller's button class/data-* strings, label and technical-block explanation. Helper returns status/action markup only; picture/bulk control remain owned by callers. Pin identical representative allowed/blocked/technical fragments and one-time VM helper loading.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/decision_status.test.js; inventory check as specified above.
Size: ~230 total changed lines; hard cap 6 files.

### CT-065 — Migrate blocked still/animation reason box [model: 6.1-sol-medium] [risk: high] [depends: CT-064]

Why: C-13 (code_reader.md).
Files: mirsal/mirsal/console/studio-tiles.js, mirsal/tests/js/allow_tiles.test.js.
Do: Replace only blockedBox's status/action construction with decisionStatusHtml; retain A=ALW result, reason fallback and A.can eligibility, still/anim labels and exact cellAct attributes. Preserve gBad/gbadmsg wrappers, adjacent picture and title. Extend existing fixtures for blocked overridable, blocked technical, already allowed and missing allow data; no new decision code.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/allow_tiles.test.js mirsal/tests/js/cell_op.test.js mirsal/tests/js/decision_status.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-066 — Migrate blocked animation overlay [model: 6.1-sol-medium] [risk: high] [depends: CT-064]

Why: C-13 (code_reader.md).
Files: mirsal/mirsal/console/studio-tiles.js, mirsal/tests/js/allow_tiles.test.js.
Do: Replace only blockedAnimOverlay reason/button construction; retain gblockover wrapper, A.why/ANIMWHY fallback, original cellAct animation attributes and technical no-button case. Do not hide/replace the blocked picture. Pin byte-identical representative fragment plus reason/override adjacency.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/allow_tiles.test.js mirsal/tests/js/cell_op.test.js mirsal/tests/js/decision_status.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-067 — Migrate chat rejected tile status [model: luna-6-high] [risk: high] [depends: CT-064]

Why: C-13 (code_reader.md).
Files: mirsal/mirsal/console/chat-cards.js, mirsal/tests/js/chat_allow.test.js.
Do: Replace only tileHTML's rejected/allowed status/action markup with decisionStatusHtml; chat allow object and its current can/undo/reason values remain authoritative. Preserve picture, red marks, agallow attrs/data-kind/data-i/data-g/data-allow, unchanged key/id/title handling and carousel links. No Studio GM dependency in Chat. Pin rule10 blocked technical/override/take-back snapshots.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/chat_allow.test.js mirsal/tests/js/sticker_id.test.js mirsal/tests/js/decision_status.test.js; inventory check as specified above.
Size: ~200 total changed lines; hard cap 6 files.

### CT-069 — Tokenize diagnostic categories without recoloring [model: 6.1-sol-medium] [risk: medium] [depends: CT-068]

Why: C-19 (code_reader.md).
Files: mirsal/mirsal/console/studio-tiles.js, mirsal/tests/js/cell_op.test.js.
Do: Replace only CAT color tuple literals at file start with CSS var strings for the exact status tokens, keeping category order/labels. White foreground -> --status-on-accent, loop #422006 -> --status-on-loop. Ensure all consumers are CSS/SVG presentation and never canvas before substitution; if a canvas use is found, leave that literal and record it for bounded follow-up. Pin issue markup vars and compare computed colors in light/dark screenshot fixtures.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/cell_op.test.js mirsal/tests/js/allow_tiles.test.js mirsal/tests/js/theme.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-070 — Tokenize video-editor small explanatory text [model: 6.1-sol-medium] [risk: medium] [depends: CT-068, CT-036]

Why: C-19 (code_reader.md).
Files: mirsal/mirsal/console/prepare.js, mirsal/tests/js/prepare_ranges.test.js.
Do: Replace only exact font-size:12px declarations in explanatory div/span with ui-footnote class. Preserve every other inline style declaration, existing class, text, input and data-* attr; do not touch canvas text/font or artwork payloads. No13px/14px/34px substitution in this task. Assert count of exact12px presentation literals reaches0, class remains on each original text block, and project payload is byte-identical.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/prepare_ranges.test.js mirsal/tests/js/theme.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-071 — Tokenize still-editor small explanatory text [model: 6.1-sol-medium] [risk: medium] [depends: CT-068, CT-035]

Why: C-19 (code_reader.md).
Files: mirsal/mirsal/console/editor.js, mirsal/tests/js/editor_ranges.test.js.
Do: Replace only exact font-size:12px declarations on inspector explanatory blocks with ui-footnote class; retain all unrelated inline styles/classes and labels. Preserve actual artwork size/fonts/colors and layer JSON. Other15/14/34px literals are outside this bounded task. Assert targeted literals0 and unchanged canonical engine request payload fixtures.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/editor_ranges.test.js mirsal/tests/js/ai_editor.test.js mirsal/tests/js/theme.test.js; inventory check as specified above.
Size: ~120 total changed lines; hard cap 150/2 files.

### CT-073 — Migrate support conversation watch [model: 6.1-sol-medium] [risk: medium] [depends: CT-005]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/support.js, mirsal/tests/js/support.test.js.
Do: Replace suWatch timeout only using15000ms watcher; original route/help/conversation status guard, hidden read skip, message-length/status redraw and notification/list refresh retained. Preserve awaiting_admin/admin_replied states; do not create conversations or send support messages. Fake update/unchanged/hidden fixtures.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/support.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-074 — Migrate persistent notification refresh [model: 6.1-sol-medium] [risk: medium] [depends: CT-005]

Why: C-05, C-10 (code_reader.md).
Files: mirsal/mirsal/console/support.js, mirsal/tests/js/support.test.js.
Do: Retain1500ms initial suNotes deferral; replace only 30000-ms notification interval with watcher enabled=!document.hidden, read=suNotes. Persistent notes/unread/redraw and staff filtering remain separate from toast/inline feedback. Assert hidden read0 and unchanged notification identities/click actions.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/support.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-075 — Migrate operator-job status watch [model: 6.1-sol-medium] [risk: medium] [depends: CT-005]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/studio-prompt.js, mirsal/tests/js/job_recovery.test.js.
Do: Replace only ACT.hgenop's5000-ms interval with watchResource. Same job GET and elapsed text; stop on failed GET, missing hjela DOM or DONE/FAILED/TIMEOUT; success reports stored result file/bytes, failure draws JR.controls. Initial job POST/body stays unchanged and must be stubbed in tests. No paid provider call.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/job_recovery.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~140 total changed lines; hard cap 150/2 files.

### CT-076 — Adapt chat fallback polling without changing SSE [model: luna-6-high] [risk: medium] [depends: CT-005]

Why: C-05 (code_reader.md).
Files: mirsal/mirsal/console/chat-core.js, mirsal/tests/js/chat_poll.test.js, mirsal/tests/js/ui_watch.test.js, mirsal/mirsal/console/ui-watch.js.
Do: Replace only startPoll's scheduled callback with watcher lifecycle; preserve500ms first read,2500ms failed-read retry,700ms working and 1600/4000ms idle escalation after120s. Extend watcher intervalMs to accept function returning caller delay, with fake-clock tests in the listed ui_watch.test.js. Keep startStream/EventSource preferred and working/pending/session404/visibilitychange semantics. Every fallback read settles before next scheduling; SSE must cancel fallback timers. Do not unify chat transport with collection events.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/chat_poll.test.js mirsal/tests/js/agent.test.js mirsal/tests/js/ui_watch.test.js; inventory check as specified above.
Size: ~220 total changed lines; hard cap 6 files.

### CT-077 — Reflow packs.js bounded helpers [model: 6.1-sol-medium] [risk: low] [depends: none]

Why: C-11 (code_reader.md).
Files: mirsal/mirsal/console/packs.js.
Do: Reflow only named helper bodies pkGroups and pkGroupHead; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/pack_delete.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-078 — Reflow live.js bounded helpers [model: 6.1-sol-medium] [risk: low] [depends: none]

Why: C-11 (code_reader.md).
Files: mirsal/mirsal/console/live.js.
Do: Reflow only named helper bodies egCard and egCommitted; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/history_card.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-079 — Reflow particles.js bounded helpers [model: 6.1-sol-medium] [risk: low] [depends: none]

Why: C-11 (code_reader.md).
Files: mirsal/mirsal/console/particles.js.
Do: Reflow only named helper bodies spBurstState and spBSlider; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/particle_editor.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-080 — Reflow reactions.js bounded helpers [model: 6.1-sol-medium] [risk: low] [depends: none]

Why: C-11 (code_reader.md).
Files: mirsal/mirsal/console/reactions.js.
Do: Reflow only named helper bodies rxBody and rxFields; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/reactions.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-081 — Reflow prepare.js bounded helpers [model: 6.1-sol-medium] [risk: low] [depends: none]

Why: C-11 (code_reader.md).
Files: mirsal/mirsal/console/prepare.js.
Do: Reflow only named helper bodies saveSoon and pcommit; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: node --test mirsal/tests/js/ai_editor.test.js; inventory check as specified above.
Size: ~145 total changed lines; hard cap 150/2 files.

### CT-082 — Document action retirement candidates against baseline [model: 6.1-sol-medium] [risk: low] [depends: none]

Why: C-16, C-21 (code_reader.md).
Files: docs/uiux_review/retirement_candidates.md.
Do: Write candidate rows for agsetgrid,psusesave,vlmyes,sppack,spall,spnovlm,spmake,psmorechip,psmoreadd,pspackassign: definition anchor, current literal/dynamic/call references, ui_baseline.json action entry and compatibility evidence. Classify each unresolved unless full reference proof plus explicit owner retirement is present. Keep qretry compatibility, jr*/shell/dynamic actions and History out of removal list. No JS or baseline edits; existing overwritten gkeepsize removal is CT-001 and keeps its action.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: Docs-only: no tests. Verify cited named anchors/rows and no source/baseline diff.
Size: ~110 total changed lines; hard cap 150/2 files.

### CT-083 — Document conservative CSS retirement evidence [model: luna-6-high] [risk: low] [depends: none]

Why: C-17 (code_reader.md).
Files: docs/uiux_review/css_candidates.md.
Do: For only 37 studio/6 theme/1 agent absent-class candidates in code_reader, write selector/source family, static reference/dynamic exclusion and which safe browser fixtures actually match it. Dynamic bg/vbg/hm/gv/st/k/no_cells patterns remain excluded. Mark absence from one walk insufficient; do not delete styles. Candidate removal gets a later owner-approved component-scoped task only after proving all required states and rules retain behavior.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: Docs-only: no tests. Verify cited named anchors/rows and no source/baseline diff.
Size: ~140 total changed lines; hard cap 6 files.

### CT-084 — Specify explicit view-extension seam [model: luna-6-high] [risk: medium] [depends: none]

Why: C-18 (code_reader.md).
Files: docs/uiux_review/extension_seam.md.
Do: Document current wrappers and exact call order: generate core→live; settings base→trash→tickets→auth; effects argument/no-argument dispatch; projmap histCol/histLoad/gview wrappers; intentional composer ggo override. Propose registerViewExtension(view,{afterRender,onLeave}) in ui-view-hooks.js as future single seam, mapping every current wrapper without changing router/private state. Provide byte-identical adapter obligations and exact focused-test matrix; do not implement it or silently retire routes.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: Docs-only: no tests. Verify cited named anchors/rows and no source/baseline diff.
Size: ~130 total changed lines; hard cap 6 files.

### CT-085 — Correct retired-History wording [model: 6.1-sol-medium] [risk: low] [depends: none]

Why: C-20 (code_reader.md).
Files: docs/waiting-for-haitham.md.
Do: In item34 only, replace fact 'nothing in rail opens it'/'retired' with current owner-avatar Watch folders route #/history, loaded history.js and active /api/watch refresh. Retain the owner's keep/delete decision as unanswered; recommendation may say keep until the active owner workflow has an approved replacement and recorded baseline retirement. Do not delete code or decide W33 React removal.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: Docs-only: no tests. Verify cited named anchors/rows and no source/baseline diff.
Size: ~40 total changed lines; hard cap 150/2 files.

### CT-086 — Refresh generated inventory counts after repairs [model: 6.1-sol-medium] [risk: low] [depends: CT-001]

Why: C-21 (code_reader.md).
Files: docs/ui_inventory.md.
Do: Regenerate/read console inventory using python -m mirsal.console.inventory from mirsal/ in measure-only mode; update this doc's heading/table from current actual definitions and unique ACT names. Confirm ggo remains intentional override and gkeepsize has one definition. Preserve baseline data/routes; current review snapshot was481 unique/483 definitions, after CT-001 expected481/482 unless an authorized concurrent change exists. Record current measured values, never hard-code the stale482 unique.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: Docs-only: no tests. Verify cited named anchors/rows and no source/baseline diff.
Size: ~100 total changed lines; hard cap 150/2 files.

### CT-087 — Record escaping aliases and standalone fixture contract [model: luna-6-high] [risk: low] [depends: none]

Why: C-14 (code_reader.md).
Files: docs/uiux_review/escape_aliases.md.
Do: List each current HTML escape implementation/export alias in app,AIU,AUV,SUV,tickets,trash,trending,users,welcome, with exact null/string coercion and malicious-input fixture coverage. Specify future ui-html.js escapeHtml(value)->string with unchanged existing .esc aliases and CommonJS/browser entrypoints; map one consumer per future migration. Preserve self-contained pure bundle tests. This task is specification only; extraction is deferred until a shared helper needs the utility.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: Docs-only: no tests. Verify cited named anchors/rows and no source/baseline diff.
Size: ~100 total changed lines; hard cap 6 files.

### CT-088 — Pin relative-time policies before future consolidation [model: 6.1-sol-medium] [risk: low] [depends: none]

Why: C-15 (code_reader.md).
Files: docs/uiux_review/relative_time_policies.md.
Do: Copy the current live.js ago and reactions.js rxAgo thresholds/rounding/date fallback into a comparison table with exact boundary examples from source. Specify future relativeTime(epochSeconds,{policy,now}) -> string with two explicit policies; no shared defaults selected and no current wording changed. One live consumer then one reaction consumer would migrate later. Documentation-only; no tests or code changes.
Do not: change routes/actions, backend payloads, owner gates, baseline eligibility or rejected-picture recovery; scope is limited to the named functions/region.
Accept: Docs-only: no tests. Verify cited named anchors/rows and no source/baseline diff.
Size: ~80 total changed lines; hard cap 150/2 files.


## Deferred decisions and rejected blanket merges

History/React/ACT/CSS removals remain owner decisions with baseline proof; CT-085 corrects active-History facts only. No three-screen effect consolidation or endpoint merger. Toasts/inline warnings/notifications retain their distinct lifetimes. Artwork colors/canvas coordinates are content. Reflow remains bounded to named helper regions. View hooks/escaping aliases/relative-time utility are lower-payoff specifications until their cost is justified.
