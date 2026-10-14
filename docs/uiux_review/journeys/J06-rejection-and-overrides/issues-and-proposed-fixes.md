# Rejected pictures, reasons and reversible overrides — issues and proposed fixes

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

## F-13 — Decision reason boxes need one UI presentation adapter

### Issue

studio-tiles.js:135–147 reason boxes/blocked overlay; chat-cards.js rejected tile builders; decision authority is verify/gates API, not JS.

**Confidence:** confirmed shared invariant. **Impact / reach / risk:** 6 / 3 / 3. **Priority:** 6.0.

### Proposed fix

Build decisionStatusHtml from existing backend eligibility and reason data; keep allow/include/drop distinctions and bulk controls.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-13--decision-reason-boxes-need-one-ui-presentation-adapter). [J6-01-blocked-animation-dark.jpg](../../shots/J6-01-blocked-animation-dark.jpg) · [J6-02-rejected-still-detail-dark.jpg](../../shots/J6-02-rejected-still-detail-dark.jpg)

### Bounded implementation work

- [T-052](../../../uiux_plan.md) — Introduce decision-status presentation adapter (luna-6-high); mirsal/mirsal/console/ui-decision.js, mirsal/mirsal/console/index.html, mirsal/tests/js/decision_status.test.js, mirsal/tests/js/console_vm.js.
  Implement decisionStatusHtml({reason,eligible,allowed,actionAttrs,labels,context}) -> string. reason is escaped; eligible/allowed are supplied from current server-backed adapters, never inferred here. Preserve variants context='studio-box'|'studio-overlay'|'chat-tile' and caller's button class/data-* strings, label and technical-block explanation. Helper returns status/action markup only; picture/bulk control remain owned by callers. Pin identical representative allowed/blocked/technical fragments and one-time VM helper loading.
- [T-053](../../../uiux_plan.md) — Migrate blocked still/animation reason box (6.1-sol-medium); mirsal/mirsal/console/studio-tiles.js, mirsal/tests/js/allow_tiles.test.js.
  Replace only blockedBox's status/action construction with decisionStatusHtml; retain A=ALW result, reason fallback and A.can eligibility, still/anim labels and exact cellAct attributes. Preserve gBad/gbadmsg wrappers, adjacent picture and title. Extend existing fixtures for blocked overridable, blocked technical, already allowed and missing allow data; no new decision code.
- [T-054](../../../uiux_plan.md) — Migrate blocked animation overlay (6.1-sol-medium); mirsal/mirsal/console/studio-tiles.js, mirsal/tests/js/allow_tiles.test.js.
  Replace only blockedAnimOverlay reason/button construction; retain gblockover wrapper, A.why/ANIMWHY fallback, original cellAct animation attributes and technical no-button case. Do not hide/replace the blocked picture. Pin byte-identical representative fragment plus reason/override adjacency.
- [T-055](../../../uiux_plan.md) — Migrate chat rejected tile status (luna-6-high); mirsal/mirsal/console/chat-cards.js, mirsal/tests/js/chat_allow.test.js.
  Replace only tileHTML's rejected/allowed status/action markup with decisionStatusHtml; chat allow object and its current can/undo/reason values remain authoritative. Preserve picture, red marks, agallow attrs/data-kind/data-i/data-g/data-allow, unchanged key/id/title handling and carousel links. No Studio GM dependency in Chat. Pin rule10 blocked technical/override/take-back snapshots.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.
