# Home and welcome — issues and proposed fixes

> **Latest source validation:** Read [../../revalidation.md](../../revalidation.md). It classifies all 36 findings against the newer implementation; changed reaction scopes must be revised before coding.

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Scores use impact × reach ÷ risk from [findings.md](../../findings.md). Candidate-only code findings and unverified surfaces stay explicitly qualified; they do not authorize deletions.

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

## F-30 — Dark welcome text fades into pale artwork

### Issue

studio.css:583–584 use general --ink/--ink2 over fixed pale slide art; theme.css:7 dark ink is pale. Settled One idea slide title/body almost disappear in dark and are legible in light. Welcome dots18px remain small.

**Confidence:** settled paired screenshots; contrast ratio not measured. **Impact / reach / risk:** 13 / 2 / 1. **Priority:** 26.0.

### Proposed fix

Give slide text a fixed light-surface semantic palette or guaranteed contrasting text backing; preserve artwork/film; make dot hit regions44px.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-30--dark-welcome-text-fades-into-pale-artwork). [J7-03-welcome-settled-dark.jpg](../../shots/J7-03-welcome-settled-dark.jpg) · [J7-03-welcome-settled-light.jpg](../../shots/J7-03-welcome-settled-light.jpg)

### Bounded implementation work

- [T-074](../../../uiux_plan.md) — Give welcome slides their own readable surface palette (luna-6-high); mirsal/mirsal/console/studio.css, mirsal/mirsal/console/theme.css.
  Define --wl-ink:#123546 and --wl-ink2:#345969 for the existing pale slide text region in both themes, with a solid/light backing only if artwork pixel contrast still fails. Replace only .wl-meta title/body general ink uses; keep artwork, film, cards and media pixels unchanged. Expand .wl-d hit regions to44px while leaving dot glyphs small; preserve selected tabs/Skip/opt-out and animation behavior.

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
