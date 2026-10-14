# Reaction wall, emoji editor, presets and batch selection — issues and proposed fixes

> **Latest source validation:** Read [../../revalidation.md](../../revalidation.md). It classifies all 36 findings against the newer implementation; changed reaction scopes must be revised before coding.

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

## F-07 — Segment builders disagree about semantics

### Issue

composer.js:99, studio-core.js:613, packs.js:31 (role=tab with aria-pressed), reactions.js:99, settings.js:19. Already one .gseg CSS but five builders.

**Confidence:** confirmed duplicate. **Impact / reach / risk:** 7 / 6 / 2. **Priority:** 21.0.

### Proposed fix

segmentedHtml has choice/tabs/navigation modes; do not turn navigation into a preference or change data-act.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-07--segment-builders-disagree-about-semantics). [J3-03-pack-dark.jpg](../../shots/J3-03-pack-dark.jpg) · [J4-03-presets-light.jpg](../../shots/J4-03-presets-light.jpg) · [J8-01-settings-dark.jpg](../../shots/J8-01-settings-dark.jpg)

### Bounded implementation work

- [T-017](../../../uiux_plan.md) — Introduce semantic segmented presenter (luna-6-high); mirsal/mirsal/console/ui-segment.js, mirsal/mirsal/console/index.html, mirsal/tests/js/segmented.test.js, mirsal/tests/js/console_vm.js.
  Implement segmentedHtml({label,mode,items,selected,className}) -> string. choice: role=group plus button aria-pressed; tabs: role=tablist/buttons role=tab + aria-selected + roving tabindex; navigation: nav aria-label with aria-current=page on selected. Keep data attributes supplied in items.attrs and ACT names verbatim; no state/persistence logic. Escape labels and values. Include once after app.js. Provide delegated keyboard handling restricted to role=tab within helper-emitted tablists: Left/Right wrap focus and call the target button.click(), Home/End select first/last; do not intercept text inputs or choice/navigation groups. Export the handler for stub-DOM tests and install one guarded listener in browser mode. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
- [T-018](../../../uiux_plan.md) — Migrate reaction filter segment (6.1-sol-medium); mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
  Replace only rxPick's All/Done/Not done segment with mode:'choice'; preserve gseg rx-f, data-act=rxfilter/data-f all|done|todo and RXQ.f. Keep counts, wall, selection, batch actions untouched. Exact selected states for each of three values and unchanged action names.
- [T-019](../../../uiux_plan.md) — Migrate composer source segment (6.1-sol-medium); mirsal/mirsal/console/composer.js, mirsal/tests/js/prompt_step.test.js.
  Replace only cpDrawBar Creative/Predefined gseg cp-act with choice mode. Preserve cpactions/data-v creative|predefined, current Creative selection whenever actions!='predefined', both tooltips and model/prompt behavior. Assert both states and original ACT.cpactions persistence/body.
- [T-020](../../../uiux_plan.md) — Migrate Studio view segment (6.1-sol-medium); mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_menu.test.js.
  Replace only gview What to show segment with choice mode, using stickers|sheet|both, data-act=gvmode/data-v and exact tooltip strings. Preserve saved view fallback and emitted content for each state; never change tabs or routes. Extend exact marker-based VM fixture rather than test text line formatting.
- [T-021](../../../uiux_plan.md) — Migrate Pack tabs segment (6.1-sol-medium); mirsal/mirsal/console/packs.js, mirsal/tests/js/pack_delete.test.js.
  Replace only gseg pk-tabs with mode:'tabs', keys stickers|particles, ACT.pktab/data-t unchanged. Use aria-selected and roving tabindex rather than aria-pressed; wire Left/Right/Home/End to focus/select only these two tab buttons using shared helper callback (helper keyboard support must be pinned in foundation before this task). Preserve PKTAB and rendering.
- [T-022](../../../uiux_plan.md) — Migrate Settings section navigation (6.1-sol-medium); mirsal/mirsal/console/settings.js, mirsal/tests/js/theme.test.js.
  Replace only Settings section nav using mode:'navigation'. Keep ordered IDs set-appear,au-me,set-health,staff set-prep,set-ai,set-tg,trx-box and existing setjump attributes/actions. This control scrolls to anchors, not a content tablist; preserve role/access and staff gating. Do not invent a selected pane if no state currently tracks it; navigation selected:null yields no aria-current.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-04 — Range controls repeat across distinct reaction contracts

### Issue

effects.js:17–19, particles.js:365–366, reactions.js:16–18,124–126. Six descriptors/five preset labels overlap; FX/SP is already shared.

**Confidence:** partial duplicate. **Impact / reach / risk:** 5 / 4 / 2. **Priority:** 10.0.

### Proposed fix

Share rangeFieldHtml; retain namespaces, defaults, touched-only params, versioned emoji and pack ownership.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-04--range-controls-repeat-across-distinct-reaction-contracts). [J4-02-editor-dark.jpg](../../shots/J4-02-editor-dark.jpg) · [J5-03-motion-light.jpg](../../shots/J5-03-motion-light.jpg)

**Concurrent-edit reconciliation:** Reaction preset/library/storage/count contracts changed during this run. The newest `CLAUDE.md` defines Reaction effects as an emoji-free, no-base64 animation preset library and a Unicode-to-preset manifest. Recheck this issue against that implementation before extracting components or altering labels.

### Bounded implementation work

- [T-023](../../../uiux_plan.md) — Introduce range-field presenter (luna-6-high); mirsal/mirsal/console/ui-range.js, mirsal/mirsal/console/index.html, mirsal/tests/js/range_field.test.js, mirsal/tests/js/console_vm.js.
  Implement rangeFieldHtml({label,min,max,step,value,attrs,formatValue,pairedInput,className}). pairedInput='output'|'number'|'none'; emit supplied namespace attributes unchanged on range and number only; output formatting is caller-supplied; no default/range/rounding policy. Support fx-sl label/span/output wrapper and fld/srow wrapper via explicit layout:'label-output'|'field-pair'. Include once after app.js; pin output escaping and two-input value attributes. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
- [T-024](../../../uiux_plan.md) — Migrate saved-set burst sliders (6.1-sol-medium); mirsal/mirsal/console/particles.js, mirsal/tests/js/particle_editor.test.js.
  Replace only spBSlider. Use original FXSL lookup, par override then shown fallback and blank-null behavior; label-output mode, class fx-sl, data-psbp and data-id exact. Do not move FXSL/default/clean parameter decisions into helper. Pin each six descriptors and focused-input handling remains outside helper.
- [T-025](../../../uiux_plan.md) — Migrate emoji reaction sliders (6.1-sol-medium); mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
  Replace only rxSlider. Retain rxVal/rxFmt and each original RXSIM/RXO min/max/step/unit/label; attrs data-rxo, existing classes/label references and preview events unchanged. Preserve sim versus extra payload keys and percent display. Pin all descriptors, nullable fallback and byte-identical rxBody JSON.

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

## F-25 — Reaction editor and batch controls compete for space

### Issue

Current wall initially loads120items; actual bank1898 with4done.27–30non-item controls; editor has11sliders, tinyReset/Close and below-wall actions. Shift happy→love correctly selects5. Pack set shows raw ids/unlink rows and two Advanced sections. plan.md UIcleanup1–4 already requests disclosure.

**Confidence:** browser + existing tracked work. **Impact / reach / risk:** 7 / 2 / 2. **Priority:** 7.0.

### Proposed fix

Group basic motion/shape and one Advanced; sticky phone action footer; keep complete bank/preset/batch actions and values. Merge existing plan items rather than call them new.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-25--reaction-editor-and-batch-controls-compete-for-space). [J4-01-wall-light.jpg](../../shots/J4-01-wall-light.jpg) · [J4-02-editor-dark.jpg](../../shots/J4-02-editor-dark.jpg) · [J4-03-presets-light.jpg](../../shots/J4-03-presets-light.jpg) · [J4-04-batch-dark.jpg](../../shots/J4-04-batch-dark.jpg) · [J5-02-set-card-light.jpg](../../shots/J5-02-set-card-light.jpg) · [J5-03-motion-light.jpg](../../shots/J5-03-motion-light.jpg)

**Concurrent-edit reconciliation:** Reaction preset/library/storage/count contracts changed during this run. The newest `CLAUDE.md` defines Reaction effects as an emoji-free, no-base64 animation preset library and a Unicode-to-preset manifest. Recheck this issue against that implementation before extracting components or altering labels.

### Bounded implementation work

- [T-070](../../../uiux_plan.md) — Disclose advanced emoji motion and group batch actions (luna-6-high); mirsal/mirsal/console/reactions.js, mirsal/mirsal/console/studio.css, mirsal/tests/js/reactions.test.js.
  Keep the current scrolling/load-more wall, search and Done/Not done filters. Group basic motion/speed/gravity and size as named inset sections; move rotation/spread/variation/hue into one collapsed Advanced summary that includes current values. Keep selected preset chips and current Presets Update/Remove ownership. Put selection count/look/Create selected together, separate from random-motion All/Not done actions; preserve Select all over the full filtered1898-bank, Shift range, exports and run Cancel. Onphone keep preview and44px primary footer visible without hiding the remaining sliders.
- [T-071](../../../uiux_plan.md) — Apply the already-tracked saved-set disclosure cleanup (luna-6-high); mirsal/mirsal/console/particles.js, mirsal/mirsal/console/packs.js, mirsal/mirsal/console/studio.css, mirsal/tests/js/particle_editor.test.js.
  Implement plan.md UIcleanup1–4: set-card cell/picked/made-for metadata onhover/focus, cost only when spent; Duplicate/Rename/Delete in the existing more-menu pattern; unlink list behind Manage stickers with Attached toN summary; show selected motion preset and Change; one Advanced summary for reaction count/spin/resolution. Preserve preview/name/open/attach/add, exact ids, assign/unlink eligibility and every parameter/backend action. Keep burst downloads and pack reaction/sticker separation. Do not implement plan.md no-tabs, new save workflow or erosion feature.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-31 — Same Reaction effects wording leads to different workflows

### Issue

home.js:55 Try reaction effects→#/effects; actual click confirmed. app.js:295 +New Reaction effects→#/reactions. Standalone effects shows giant sticker-source chooser; emoji wall is a distinct screen.

**Confidence:** browser/source confirmed product choice. **Impact / reach / risk:** 7 / 3 / 3. **Priority:** 7.0.

### Proposed fix

Ask owner which door Home should present; recommend distinct pack-reaction/emoji-reaction labels while preserving both routes.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-31--same-reaction-effects-wording-leads-to-different-workflows). [J5-04-effects-light.jpg](../../shots/J5-04-effects-light.jpg) · [J7-01-home-dark.jpg](../../shots/J7-01-home-dark.jpg)

**Concurrent-edit reconciliation:** Reaction preset/library/storage/count contracts changed during this run. The newest `CLAUDE.md` defines Reaction effects as an emoji-free, no-base64 animation preset library and a Unicode-to-preset manifest. Recheck this issue against that implementation before extracting components or altering labels.

### Bounded implementation work

No standalone repair assigned; preserve the qualified finding and reconcile it during the related shared cleanup.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-12 — Range label/output builders repeat in editors

### Issue

prepare.js/editor.js range rows versus particles.js spBSlider/reactions.js rxSlider; same label/range/output pattern, different user-art values.

**Confidence:** confirmed presentation overlap. **Impact / reach / risk:** 3 / 4 / 2. **Priority:** 6.0.

### Proposed fix

rangeFieldHtml can host them later, one caller per task; user artwork colours/canvas coordinates remain data.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-12--range-labeloutput-builders-repeat-in-editors). [J3-06-edit-project-light.jpg](../../shots/J3-06-edit-project-light.jpg)

### Bounded implementation work

No standalone repair assigned; preserve the qualified finding and reconcile it during the related shared cleanup.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.
