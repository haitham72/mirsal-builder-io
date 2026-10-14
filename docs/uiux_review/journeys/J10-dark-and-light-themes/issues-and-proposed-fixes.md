# Dark and light comparisons — issues and proposed fixes

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

**Theme limitation:** The Studio dark/light captures differ in media tab after async redraw; use them for context, not a same-state contrast measurement. Welcome uses settled paired evidence.

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

**Theme limitation:** The Studio dark/light captures differ in media tab after async redraw; use them for context, not a same-state contrast measurement. Welcome uses settled paired evidence.

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

**Theme limitation:** The Studio dark/light captures differ in media tab after async redraw; use them for context, not a same-state contrast measurement. Welcome uses settled paired evidence.

### Bounded implementation work

- [T-074](../../../uiux_plan.md) — Give welcome slides their own readable surface palette (luna-6-high); mirsal/mirsal/console/studio.css, mirsal/mirsal/console/theme.css.
  Define --wl-ink:#123546 and --wl-ink2:#345969 for the existing pale slide text region in both themes, with a solid/light backing only if artwork pixel contrast still fails. Replace only .wl-meta title/body general ink uses; keep artwork, film, cards and media pixels unchanged. Expand .wl-d hit regions to44px while leaving dot glyphs small; preserve selected tabs/Skip/opt-out and animation behavior.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.
