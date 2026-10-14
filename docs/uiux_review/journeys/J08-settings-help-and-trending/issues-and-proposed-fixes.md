# Settings, Trash, Tickets, Help and Trending — issues and proposed fixes

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

## F-28 — Help rows are click-only divs

**Implemented 2026-10-14 (branch `uiux-fixes`, T-073):** conversation/queue/FAQ title rows are native `button.crow` (same `suopen`/`suq`/`sufaq` + ids, no nested buttons; full-width 44px + existing focus-visible). Extended `support.test.js` (6 pass).

### Issue

support.js:14,46,55 emit conversation/queue/FAQ data-act rows without native button roles/focus. FAQ titles appear as text in accessibility snapshot.

**Confidence:** source + accessibility snapshot. **Impact / reach / risk:** 6 / 3 / 1. **Priority:** 18.0.

### Proposed fix

Use native focusable title controls with sibling secondary actions; preserve suopen/suq/sufaq, selected/scroll states and role visibility.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-28--help-rows-are-click-only-divs). [J8-04-faq-dark.jpg](../../shots/J8-04-faq-dark.jpg)

### Bounded implementation work

- [T-073](../../../uiux_plan.md) — Make Help list titles native keyboard controls (luna-6-high); mirsal/mirsal/console/support.js, mirsal/mirsal/console/studio.css, mirsal/tests/js/support.test.js.
  Replace click-only conversation/queue/FAQ title regions with native button elements retaining suopen/suq/sufaq and data ids. Keep sibling delete/menu actions outside buttons to avoid invalid nested buttons. Add visible focus and full-width44px hit areas using current row classes. Preserve selected/scroll/filter state, source chips, owner/staff visibility and existing conversations/FAQ backend behavior.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-29 — Library/public/Home totals count reactions as stickers

### Issue

Trending Angel10 versus9stickers+1reaction sidebar; Batman19 versus17+2. trending.js:11 and home.js:44 count total while app.js:430/library.js:400 exclude particle_set. Contradicts docs/reaction/12-11-added-bursts-are-reactions-not-stickers-2026.md:5. My Stickers grouped grid also labels Batman Lego19 stickers while the pack is17stickers+2reactions (J3-02 snapshot/library.js:372). Keep those accessible items; fix the count wording, do not silently discard them.

**Confidence:** browser/source; API follow-up needed. **Impact / reach / risk:** 9 / 4 / 3. **Priority:** 12.0.

### Proposed fix

Define additive backend sticker_count/reaction_count, preserving existing fields and permissions; migrate Trending/Home presentation separately.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-29--librarypublichome-totals-count-reactions-as-stickers). [J3-02-grouped-dark.jpg](../../shots/J3-02-grouped-dark.jpg) · [J7-01-home-dark.jpg](../../shots/J7-01-home-dark.jpg) · [J8-05-trending-dark.jpg](../../shots/J8-05-trending-dark.jpg)

**Concurrent-edit reconciliation:** Reaction preset/library/storage/count contracts changed during this run. The newest `CLAUDE.md` defines Reaction effects as an emoji-free, no-base64 animation preset library and a Unicode-to-preset manifest. Recheck this issue against that implementation before extracting components or altering labels.

### Bounded implementation work

- [T-075](../../../uiux_plan.md) — Expose additive public-pack sticker/reaction counts (luna-6-high); mirsal/mirsal/media/library.py, mirsal/mirsal/flow/trending.py, mirsal/mirsal/console/app.py, mirsal/tests/test_trending.py, mirsal/tests/test_library.py, docs/api-parts/pack-counts.md.
  Inspect the existing Library serialization and public Trending summary builders and native/legacy adapter first. Introduce one backend pack_counts helper under media/library.py using the documented source.particle_set distinction after existing visibility filtering; expose additive sticker_count/reaction_count on both personal library and public summaries. Public summary delegates to the same count owner. Retain every existing JSON field/value, route, total and permission filter. If app.py delegates transparently, avoid duplicate logic there. No count decision moves into JS. Test static-only/mixed/reaction-only and owner/member visibility; document additive fields/absent-field compatibility.
- [T-076](../../../uiux_plan.md) — Use public summary counts in Trending labels (6.1-sol-medium); mirsal/mirsal/console/trending.js, mirsal/tests/js/imports_trending.test.js.
  Render sticker_count with the word stickers and an optional separate reaction_count label. When additive fields are absent, keep the previous label exactly; never infer by subtracting unknown arrays. Preserve likes/comments/use/delete/share controls and ids, request URLs and role checks.
- [T-077](../../../uiux_plan.md) — Keep Home totals consistent with the backend (6.1-sol-medium); mirsal/mirsal/console/home.js, mirsal/tests/js/home.test.js.
  Use additive backend sticker/reaction totals for Home summary only when present; retain old field fallback and current showcase filtering. Preserve gallery media nodes onsearch/resize, routes, all shortcuts and per-person/owner rules. Do not change the ambiguous reaction shortcut destination withoutQ1.
- [T-087](../../../uiux_plan.md) — Label grouped Library counts without calling reactions stickers (6.1-sol-medium); mirsal/mirsal/console/library.js, mirsal/tests/js/packs_column.test.js.
  In libByPackHtml group-header wording only, when LIBQ is empty and the matching backend pack summary supplies sticker_count/reaction_count, render the two explicit labels. With a filtered subset or absent additive fields, label xs.length as items rather than stickers. Preserve all items, global carousel indices, cell HTML, Open pack, selection handlers and request payloads. Do not infer classification/counts in JS or silently hide reaction thumbnails.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-26 — Local Account shortcut is a no-op

**Implemented 2026-10-14 (branch `uiux-fixes`, T-072):** the bar is built from `SET_SECTIONS` and rebuilt by the auth/tickets/trash wrappers after mounting (`setNavSync`), so it only offers mounted cards: no Account off the LAN, Tickets only where `tk-box` mounted. `ACT.setgo`, ids and routes unchanged. Test `settings_nav.test.js` (3 pass).

### Issue

settings.js:19 emits Account→au-me; :41 ignores missing target; auth.js:82 only adds Account for LAN. Non-LAN DOM #au-me count0 while button remains.

**Confidence:** browser confirmed broken. **Impact / reach / risk:** 10 / 1 / 1. **Priority:** 10.0.

### Proposed fix

Derive section shortcuts from mounted cards after wrappers; retain LAN Account entry and backend behavior.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-26--local-account-shortcut-is-a-no-op). [J8-01-settings-dark.jpg](../../shots/J8-01-settings-dark.jpg) · [J8-01-settings-light.jpg](../../shots/J8-01-settings-light.jpg)

### Bounded implementation work

- [T-072](../../../uiux_plan.md) — Build Settings shortcuts from mounted cards (luna-6-high); mirsal/mirsal/console/settings.js, mirsal/mirsal/console/auth.js, mirsal/mirsal/console/tickets.js, mirsal/tests/js/auth.test.js, mirsal/tests/js/tickets.test.js.
  Add a settings-section registry containing existing ids/labels including Tickets, then filter by actually mounted cards only after the current render wrappers finish. Rebuild the bar when auth/tickets cards mount; avoid recursion and preserve existing wrapper order. Non-LAN must not emit Account when au-me is absent; LAN keeps Account. Add Tickets only for roles that mount its card; keep all section ids/ACT.setgo and current backend routes. Do not invent Spending controls.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-27 — Tickets have no section shortcut

**Implemented 2026-10-14 (branch `uiux-fixes`, T-072):** `tk-box`/`Tickets` is in the registry; presence-filtered like Account (non-owner cards carry no `tk-box`, so no shortcut there). Same tests as F-26.

### Issue

settings.js:19 lacks Tickets; tickets.js:50–53 appends owner card after Trash wrapper. Reaching Tickets requires scrolling past nine trash items.

**Confidence:** browser confirmed. **Impact / reach / risk:** 7 / 1 / 1. **Priority:** 7.0.

### Proposed fix

Add role-aware Tickets section entry after mounted card detection; do not create another route.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-27--tickets-have-no-section-shortcut). [J8-06-tickets-bottom-dark.jpg](../../shots/J8-06-tickets-bottom-dark.jpg)

### Bounded implementation work

No standalone repair assigned; preserve the qualified finding and reconcile it during the related shared cleanup.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.
