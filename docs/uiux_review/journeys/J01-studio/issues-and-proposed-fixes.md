# Create a sticker set in Studio — issues and proposed fixes

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Scores use impact × reach ÷ risk from [findings.md](../../findings.md). Candidate-only code findings and unverified surfaces stay explicitly qualified; they do not authorize deletions.

## F-22 — Tap targets are too small across core journeys

### Issue

Settled Studio batch66controls/35tiny; G00167/37; Trash37/28; current reaction editor Close12×28px, Reset43×24; welcome dots72×18; phone editor Close still12px wide. Tiny threshold in probe is width<32 OR height<28, smaller than44px goal.

**Confidence:** browser measured. **Impact / reach / risk:** 18 / 9 / 2. **Priority:** 81.0.

### Proposed fix

Use44px logical targets, consistent8px gaps and secondary/tinted controls; retain every action and per-picture recovery.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-22--tap-targets-are-too-small-across-core-journeys). [J1-03-batch-dark.jpg](../../shots/J1-03-batch-dark.jpg) · [J11-04-viewer-dark.jpg](../../shots/J11-04-viewer-dark.jpg) · [J11-06-editor-dark.jpg](../../shots/J11-06-editor-dark.jpg) · [J3-04-viewer-dark.jpg](../../shots/J3-04-viewer-dark.jpg) · [J3-05-timeline-dark.jpg](../../shots/J3-05-timeline-dark.jpg) · [J4-04-batch-dark.jpg](../../shots/J4-04-batch-dark.jpg) · [J6-02-rejected-still-dark.jpg](../../shots/J6-02-rejected-still-dark.jpg) · [J6-02-rejected-still-light.jpg](../../shots/J6-02-rejected-still-light.jpg) · [J6-03-chat-review-dark.jpg](../../shots/J6-03-chat-review-dark.jpg) · [J8-02-trash-dark.jpg](../../shots/J8-02-trash-dark.jpg) · [J8-02-trash-light.jpg](../../shots/J8-02-trash-light.jpg)

### Bounded implementation work

- [T-066](../../../uiux_plan.md) — Apply44px targets through semantic control tokens (luna-6-high); mirsal/mirsal/console/studio.css, mirsal/mirsal/console/agent.css, mirsal/mirsal/console/theme.css.
  Use the control44 token for .btn.sm, .gseg button, .set-nav button, .rx-h [data-act=rxclose], .rx-gh .link and non-inline icon actions; enlarge actual hit areas with padding/min-size, not a visual glyph. Separate repeated secondary/destructive controls by8px; keep inline sentence links and media-overlay cell geometry intentional. Bound changes to shared controls and J1/J3/J4/J5/J8/J11; retain rail width, sidebar geometry and all data-act. Decide bounded wrapping at390px while preserving all controls.
- [T-069](../../../uiux_plan.md) — Clarify Studio primary versus recovery actions (luna-6-high); mirsal/mirsal/console/studio-core.js, mirsal/mirsal/console/studio-tiles.js, mirsal/mirsal/console/studio.css, mirsal/tests/js/allow_tiles.test.js.
  Keep exactly one principal stage action visually primary in the batch view; make per-picture Use it anyway/Take it back and bulk recovery clear tinted/secondary actions without moving or hiding them. Preserve stage-specific disabled reasons and eligibility from API. Group batch tools separately from tile sizing/approval. Apply shared spacing/type/status tokens; do not reduce the scope/count of any bulk action.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-19 — Presentation bypasses a shared token system

### Issue

610 non-custom CSS declarations contain literal colours; studio/agent/theme7/1/0!important;290 JSstyle attributes;218 literal px occurrences. Existing six-size scale is studio.css:5. Tokens do not cover all status/material/spacing uses.

**Confidence:** measured structure + browser. **Impact / reach / risk:** 9 / 11 / 2. **Priority:** 49.5.

### Proposed fix

Introduce semantic spacing/type/status/material/control tokens; convert one bounded block per task; never tokenize art content values.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-19--presentation-bypasses-a-shared-token-system). [J1-01-studio-dark.jpg](../../shots/J1-01-studio-dark.jpg) · [J1-03-batch-light.jpg](../../shots/J1-03-batch-light.jpg) · [J11-03-pack-dark.jpg](../../shots/J11-03-pack-dark.jpg) · [J11-05-wall-dark.jpg](../../shots/J11-05-wall-dark.jpg) · [J11-06-editor-light.jpg](../../shots/J11-06-editor-light.jpg) · [J2-01-chat-dark.jpg](../../shots/J2-01-chat-dark.jpg) · [J3-01-library-dark.jpg](../../shots/J3-01-library-dark.jpg) · [J3-03-pack-light.jpg](../../shots/J3-03-pack-light.jpg) · [J5-01-pack-reactions-light.jpg](../../shots/J5-01-pack-reactions-light.jpg) · [J3-06-edit-project-light.jpg](../../shots/J3-06-edit-project-light.jpg)

### Bounded implementation work

- [T-056](../../../uiux_plan.md) — Define semantic UI spacing/type/status tokens (luna-6-high); mirsal/mirsal/console/studio.css, mirsal/mirsal/console/theme.css, mirsal/tests/js/theme.test.js.
  Add spacing tokens --space-1..6 as8/16/24/32/40/48px; type tokens --type-large-title32px,--type-title24px,--type-headline18px,--type-body16px,--type-footnote13px. Add status tokens --status-bounds #f97316,--status-key #a855f7,--status-loop #eab308,--status-look #ec4899,--status-spec #3b82f6,--status-bad #ef4444,--status-on-accent #fff,--status-on-loop #422006 with same light/dark values initially. Keep existing --fs-* aliases unchanged and all current selectors using them until each surface task. Add .ui-footnote font-size:var(--type-footnote). Pin dark/light token availability and old token values; no palette redesign here. Also define --surface-card:var(--sf), --surface-group:var(--fill), --material-bar:var(--glass), --material-sheet:var(--glass), --border-ui:var(--bd), --focus-ui:var(--pri), --control-min-size:44px, --control-gap:8px, --icon-stroke:1.6, --motion-duration:200ms and --motion-easing:cubic-bezier(0.2,0,0,1). These are semantic aliases/units, not new palette decisions; existing selectors remain unchanged until their surface task.
- [T-057](../../../uiux_plan.md) — Tokenize diagnostic categories without recoloring (6.1-sol-medium); mirsal/mirsal/console/studio-tiles.js, mirsal/tests/js/cell_op.test.js.
  Replace only CAT color tuple literals at file start with CSS var strings for the exact status tokens, keeping category order/labels. White foreground -> --status-on-accent, loop #422006 -> --status-on-loop. Ensure all consumers are CSS/SVG presentation and never canvas before substitution; if a canvas use is found, leave that literal and record it for bounded follow-up. Pin issue markup vars and compare computed colors in light/dark screenshot fixtures.
- [T-083](../../../uiux_plan.md) — Record P3 screen changes and API compatibility (luna-6-high); docs/design/03-3-foundations.md, docs/design/05-5-per-screen.md, docs/design/09-9-every-rejected-picture-carries-its-own-overrid.md, docs/reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md, docs/api.md, docs/api-parts/pack-counts.md.
  After P3 implementations, update the matching screen owner paragraphs with actual grouped-controls/sheet behavior and the additive count contract. Link pack-counts from the API index; preserve old payload semantics. Record fixture-backed picture/reason/action parity and remaining phone/paid/LAN limits; never claim unexecuted acceptance. Keep held product alternatives and advance human trackers only on an actual verdict. Commit these area changes in the same P3 phase as the source.
- [T-085](../../../uiux_plan.md) — Document P1 repairs and token ownership (luna-6-high); docs/design/03-3-foundations.md, docs/architecture.md, docs/engine-and-studio/13-12-ui-observer.md.
  Before the P1 commit, record the exact new spacing/type/status/control token names and staged-preview/cancellation invariants in the existing UI foundations and wiring owner paragraphs. Locate the Studio observer owner section through its index; use its existing section file if the listed observer filename has moved, with an exact-path preparation task before editing rather than silently broadening scope. Record non-overlapping refresh/forced-read behavior, not measured latency claims. Reflow changes require only a note that emitted markup/JSON/token streams remain identical. No new engine behavior, models or approval semantics.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-01 — Keep approved size bypasses preview

### Issue

studio-core.js:858,901; loaded ACT.gkeepsize.toString() POSTs keep_size immediately. Video-size +/- opens #vzcard while Keep uses the overwritten handler.

**Confidence:** broken. **Impact / reach / risk:** 22 / 2 / 1. **Priority:** 44.0.

### Proposed fix

Restore the staged handler before extracting testCard; zero mutations before Apply; Cancel writes nothing.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-01--keep-approved-size-bypasses-preview). [J1-04-preview-dark.jpg](../../shots/J1-04-preview-dark.jpg)

### Bounded implementation work

- [T-001](../../../uiux_plan.md) — Restore staged Keep approved size (6.1-sol-medium); mirsal/mirsal/console/studio-core.js, mirsal/tests/js/size_preview.test.js.
  Delete only the late ACT.gkeepsize assignment originally at901–911; retain the858 staged implementation and all other ACT names. Test with stubbed API/GM and the existing console_vm/source helpers: click changes VZ.keep and reads anim_preview; no keep_size/video_size POST until Apply. Cancel makes zero mutation calls; Apply sends the original {on,reslice} body once; technical failures retain the preview.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-05 — Refresh loops can overlap and redraw twice

### Issue

studio-core.js:913–973 async tick each700ms without in-flight guard; live.js:185,191 both1s queue redraw; :267 unconditional800ms egSync.61 timer call sites across38scripts.

**Confidence:** source confirmed; latency not measured. **Impact / reach / risk:** 10 / 8 / 2. **Priority:** 40.0.

### Proposed fix

Serialize tick, coalesce queue clock, then migrate one watcher per task. Preserve forced refresh and off-screen job completion.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-05--refresh-loops-can-overlap-and-redraw-twice). [J1-03-batch-dark.jpg](../../shots/J1-03-batch-dark.jpg)

### Bounded implementation work

- [T-003](../../../uiux_plan.md) — Coalesce duplicate queue clock redraws (6.1-sol-medium); mirsal/mirsal/console/live.js, mirsal/tests/js/queue_clock.test.js.
  Remove only the second1000-ms interval at live.js:191. Retain the first interval at185 byte-for-byte, including data-lvt updates and its original active/run predicate. Add a stub-clock test proving one queue1000-ms interval registration and one drawLive call per clock tick for REQUESTED/CLAIMED work. Preserve qRefresh/qtoggle, all queue ACT names and saved QO; incremental DOM rendering is a separate design task.
- [T-004](../../../uiux_plan.md) — Serialize Studio refreshes and retain force requests (luna-6-high); mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_poll.test.js.
  Add a tick in-flight flag and one pending-force flag. Concurrent tick(true) must queue one force refresh after the current read completes; intervals may not overlap. Release both flags on every failure via finally. Skip interval work while document.hidden, but explicit force requests and required open-modal refreshes retain current behavior. Read each original URL/body and preserve glast/typing guard/404 session cleanup. Use fake slow reads and hidden-state tests; do not change server polling cadence here.
- [T-005](../../../uiux_plan.md) — Introduce resource watcher lifecycle (luna-6-high); mirsal/mirsal/console/ui-watch.js, mirsal/mirsal/console/index.html, mirsal/tests/js/ui_watch.test.js, mirsal/tests/js/console_vm.js.
  Implement watchResource({key,intervalMs,enabled,read,onValue,onError,isTerminal,signature,visibility}) -> {start,stop,refresh}. Exactly one read at a time; refresh(true) retains one pending force; next timeout begins after settle. Terminal/stop disposes timers; failure calls onError then reschedules while enabled. visibility is explicit 'visible'|'always'; no default policy guessing. Export pure/testable helper with no DOM reads at module load. Include once after app.js and before consumers. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files. enabled=false skips reads and continues only cheap enabled checks until explicit stop/terminal; caller route transitions do not create parallel instances. Visibility policy skips read while hidden without marking a running job terminal. Cover disable/re-enable without manual new watcher.
- [T-006](../../../uiux_plan.md) — Migrate collection export watcher (6.1-sol-medium); mirsal/mirsal/console/packs.js, mirsal/tests/js/collection_watch.test.js.
  Replace only colWatch scheduling with watchResource; keep its public colWatch(id,tries=0). Policy:2500ms, always visible/offscreen, stop on404, done, failed or tries>720; preserve done/failed toast wording and no duplicate terminal toast. read remains GET collection/exports/{encoded id}; never initiate an export in tests. Exact failed-read/retry-limit fixtures.
- [T-007](../../../uiux_plan.md) — Migrate reaction batch watcher (6.1-sol-medium); mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
  Adapt rxWatch/rxRun's runT scheduling to watchResource at RXPOLL1500. Preserve original reaction batch id capture, running/terminal decisions, fresh-token progress, RXS.done reset and redraw points. Off-route background batches keep original continuation policy; no new batch request. Extend existing reactions tests with terminal-once, failure recovery and stopped watcher fixtures.
- [T-008](../../../uiux_plan.md) — Migrate effect-run watcher (6.1-sol-medium); mirsal/mirsal/console/effects.js, mirsal/tests/js/effects_core.test.js.
  Replace fxPoll's timeout with one watcher per X.who/eid at2200ms; enabled=original fxBusy(X)&&X.alive(). read uses fxLoad(X), which retains original state-token guard. Keep fxSig and X.last redraw check; stop/dispose on fxReset and eid switch. Do not share FX/SP state or merge their screens.
- [T-009](../../../uiux_plan.md) — Migrate saved-set drawing watcher (6.1-sol-medium); mirsal/mirsal/console/particles.js, mirsal/tests/js/particle_editor.test.js.
  Replace only spPoll with a2500-ms watcher. While original busy predicate is true, reproduce route-specific reads exactly: Library particles calls spLibSync(true); Pack calls ptCounts(PACK_ID) and conditional spLibSync(true); off-route wakes may continue without reads. Preserve SPL.busy, cached cells invalidation and terminal behavior. Do not migrate search/slider timers.
- [T-010](../../../uiux_plan.md) — Migrate background job reads (luna-6-high); mirsal/mirsal/console/live.js, mirsal/tests/js/live_watch.test.js.
  Move liveTick2500-ms registration to watcher with visibility:'always'; preserve LTB, completion/session mutations, dismissal handling, lsave and qRefresh. read/commit split must reproduce existing call/order; a force tick during a read may coalesce but cannot lose completion. Fake all network operations and assert exact session/ANIM/LIVE outcomes for completed sheet/video and failed job.
- [T-058](../../../uiux_plan.md) — Replace unconditional edge synchronization clock (luna-6-high); mirsal/mirsal/console/live.js, mirsal/mirsal/console/studio-core.js, mirsal/tests/js/edge_preview.test.js.
  Remove only live.js800-ms egSync/applyEdgePreview interval. At tick's existing successful generation-key-change/force redraw point, call egSync before existing applyEdgePreview; retain showPanel/input/change/pointerup/scroll/resize calls. No synchronization when no relevant view exists. Pin updated committed outline/trim and active slider preservation after fake generation refresh; preview cancel/apply unchanged. Do not treat this DOM synchronization as server polling.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-23 — Allowed animations lose the readable boundary reason

### Issue

G146S2/S6 and G001S1/S7 show allowed by you + Take it back in tile captions. Full boundary reason is in sheet cell title; studio-tiles.js:276 constructs short allowed caption, sheet cell titles in studio-sheet.js. Blocked G001S2/S9 do show picture/reason/Use it anyway; human-rejected G012S5 is a different drop/Bring back state.

**Confidence:** source + browser confirmed; bounded sample. **Impact / reach / risk:** 11 / 3 / 3. **Priority:** 11.0.

### Proposed fix

Keep a one-sentence reason next to the allowed preview and a visible selected-sheet-cell status row. Preserve backend eligibility, technical final blocks and bulk recovery.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-23--allowed-animations-lose-the-readable-boundary-reason). [J1-03-batch-dark.jpg](../../shots/J1-03-batch-dark.jpg) · [J6-01-blocked-animation-dark.jpg](../../shots/J6-01-blocked-animation-dark.jpg)

### Bounded implementation work

No standalone repair assigned; preserve the qualified finding and reconcile it during the related shared cleanup.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-32 — Studio prompt view is dense and exposes an engine inspector

### Issue

Prompt contains long sheet/video text + per-sticker metadata, while composer adds model/style/stroke/loop/reaction switches and Auto/Local/Cloud/no-model inspector. Current plan reached free built-in draft; paid Generate sheet stayed disabled.

**Confidence:** browser measured; no model-off error score. **Impact / reach / risk:** 9 / 2 / 2. **Priority:** 9.0.

### Proposed fix

Keep editable prompt, price/unavailable explanation and primary; group supporting metadata under Advanced. Move backend connection detail into expandable inspector.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-32--studio-prompt-view-is-dense-and-exposes-an-engine-inspector). [J1-01-studio-dark.jpg](../../shots/J1-01-studio-dark.jpg) · [J1-02-plan-dark.jpg](../../shots/J1-02-plan-dark.jpg) · [J2-03-plan-dark.jpg](../../shots/J2-03-plan-dark.jpg)

### Bounded implementation work

- [T-068](../../../uiux_plan.md) — Group Studio composer and prompt metadata (luna-6-high); mirsal/mirsal/console/composer.js, mirsal/mirsal/console/studio-prompt.js, mirsal/mirsal/console/studio-core.js, mirsal/mirsal/console/studio.css, mirsal/tests/js/prompt_step.test.js.
  Keep request/model/style/stroke and free Generate prompt discoverable. Put backend Auto/Local/Cloud diagnostics under a clearly labelled Connection details section, preserving every existing control. In the draft keep editable sheet prompt, plan status and price/unavailable explanation together; place long per-sticker metadata and later video prompt in collapsed sections. Existing exact API/control values remain read by their backends. Preserve Prompt draft/Discard and journey navigation. Use the five-type scale and8px spacing, no new inline colours.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-02 — Two Apply/Cancel presenters drift

### Issue

live.js:237–243 egCard; studio-core.js:806–827 vzCard; studio-core.js:792 explicitly describes copying. Media type, busy states and viewport anchoring differ.

**Confidence:** confirmed duplicate. **Impact / reach / risk:** 8 / 2 / 2. **Priority:** 8.0.

### Proposed fix

Introduce ui-testcard.js testCard; video then edge adapters; responsive sheet treatment after behavior is pinned.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-02--two-applycancel-presenters-drift). [J1-04-preview-dark.jpg](../../shots/J1-04-preview-dark.jpg)

### Bounded implementation work

- [T-011](../../../uiux_plan.md) — Introduce shared test-card presenter (luna-6-high); mirsal/mirsal/console/ui-testcard.js, mirsal/mirsal/console/index.html, mirsal/tests/js/ui_testcard.test.js, mirsal/tests/js/console_vm.js.
  Implement testCard({id,media:{kind,src,alt},caption,anchor,loading,busy,applyAct,cancelAct}) -> {update,close}. Reuse existing egcimg/egbadge/egccap/egcbtn classes and exact labels/ids; support image or autoplay loop muted playsinline video. Width min(300,innerWidth-24); same12px horizontal clamp and70px/min(innerHeight-width-110,anchor.bottom+8 or90) top clamp. Only owned DOM, no API/policy. Include once after app.js. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
- [T-012](../../../uiux_plan.md) — Migrate video-size test card (6.1-sol-medium); mirsal/mirsal/console/studio-core.js, mirsal/tests/js/size_preview.test.js.
  Replace only vzCard DOM construction/update/position with testCard. Adapter computes existing target/caption, source/spinner, busy state and anchor expression; preserve #vzcard, gvsize/gkeepsize anchor choices and vzapply/vzcancel. Scroll/resize still update placement. Do not change VZ.n, endpoints or tick calls.
- [T-013](../../../uiux_plan.md) — Migrate edge test card (6.1-sol-medium); mirsal/mirsal/console/live.js, mirsal/tests/js/edge_preview.test.js.
  Replace only egCard DOM construction/update/position with testCard. Preserve #egcard image/caption and egapply/egundo. Keep modal-overlay route, egDirty/egClear, 40-ms debounce and stored-snapshot undo semantics. Set busy from EG.busy without changing eligibility; test dirty-cancel is zero POST while committed undo retains original body.
- [T-067](../../../uiux_plan.md) — Present Apply/Cancel tests as responsive sheets (luna-6-high); mirsal/mirsal/console/ui-testcard.js, mirsal/mirsal/console/studio.css, mirsal/tests/js/ui_testcard.test.js.
  Keep testCard media/loading/busy/action API. Atdesktop use a centred bounded panel; below760px use a bottom sheet with safe-area padding,44px actions and max-height allowing content scroll. Apply/Cancel remain visible while preview loads; focus returns to the exact opener on Cancel. Preserve request eligibility and deferred mutation semantics. Use material only for this sheet and bars.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-09 — Preview request lifecycles repeat; endpoints are distinct

### Issue

studio-core.js:834–841 generation counter; reactions.js:206–239 RXS.pv/ppv caches without eviction; particles.js:395–406 busy/again/signature. Edge/sheet/anim/emoji endpoints perform different work.

**Confidence:** partial duplicate. **Impact / reach / risk:** 6 / 4 / 3. **Priority:** 8.0.

### Proposed fix

Introduce bounded latest-result previewSession; never combine backend operations or move rendering decisions into JS.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-09--preview-request-lifecycles-repeat-endpoints-are-distinct). [J1-04-preview-dark.jpg](../../shots/J1-04-preview-dark.jpg) · [J4-02-editor-light.jpg](../../shots/J4-02-editor-light.jpg)

**Concurrent-edit reconciliation:** Reaction preset/library/storage/count contracts changed during this run. The newest `CLAUDE.md` defines Reaction effects as an emoji-free, no-base64 animation preset library and a Unicode-to-preset manifest. Recheck this issue against that implementation before extracting components or altering labels.

### Bounded implementation work

- [T-032](../../../uiux_plan.md) — Introduce latest-result preview session (luna-6-high); mirsal/mirsal/console/ui-preview.js, mirsal/mirsal/console/index.html, mirsal/tests/js/preview_session.test.js, mirsal/tests/js/console_vm.js.
  Implement previewSession({keyFor,request,commit,onError,maxEntries=64,debounceMs}) -> {schedule,refresh,clear,dispose}. Unique monotonic generation per request; stale responses never commit; allow one in-flight read and retain only latest queued key. Cache response metadata by exact caller key with64-entry LRU; no media blobs/artwork generated or URL rewriting. Clear/dispose cancels scheduled work and invalidates late replies. Errors release busy state. Include once after app.js. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
- [T-033](../../../uiux_plan.md) — Migrate size preview request lifecycle (luna-6-high); mirsal/mirsal/console/studio-core.js, mirsal/tests/js/size_preview.test.js.
  Replace only VZ.t/VZ.n orchestration in vzPreview with previewSession debounce250/cache policy exact query key. Keep generation/index/scale/keep query serialization, initial clear/spinner, api anim_preview GET, metadata/caption and error toast/vzClear. VZ change/clear must invalidate prior requests; no automatic Apply. Preserve currently selected generation and test delayed old responses after target switch/Cancel.
- [T-034](../../../uiux_plan.md) — Migrate emoji editor and hover preview lifecycle (luna-6-high); mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
  Move only rxPlay/rxHovPreview request ownership and RXS.pv response cache into previewSession adapters. Exact existing rxKey(rxBody(k)) and hover '|fit' keys; editor and hover channels remain separate so hovering cannot cancel editor work. Preserve size256, fit behavior, sim/extras payload, displayed ghost and error wording. Existing300/220ms debounce semantics remain. Test stale editor/hover replies and64-entry eviction with fakes.
- [T-035](../../../uiux_plan.md) — Migrate preset-card preview cache (6.1-sol-medium); mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
  Adapt only rxPresetPreviews/RXS.ppv using separate preview channel, key preset id+token+exact JSON settings, size RXPX and fit:true. Preserve ordering/throttled serial iteration and redraw behavior; do not replace editor/hover cache or batch watcher. Invalidated preset changes may not reuse old metadata;64-entry cap is explicit.
- [T-036](../../../uiux_plan.md) — Migrate saved-set burst preview lifecycle (luna-6-high); mirsal/mirsal/console/particles.js, mirsal/tests/js/pack_studio.test.js.
  Replace only spBurstPreview busy/again/request signature/debounce lifecycle with previewSession keyed by existing spBurstPreviewKey. Preserve pack_id omission, optional preset, fxClean touched-only params + spBurstSize, size256, server shown params and never overwrite focused input. A slider during a request queues latest key; target/preset changes cannot apply stale response. No mutation/render endpoints.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.
