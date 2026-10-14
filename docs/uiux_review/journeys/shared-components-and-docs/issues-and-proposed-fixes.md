# Shared code structure, inventory and documentation — issues and proposed fixes

**Snapshot notice:** These issues were recorded against source `170f26e`. Another LLM changed and committed implementation during the review. They are historical evidence and proposals, not a claim that every issue still exists. Before implementation, reconcile the named functions and current `CLAUDE.md`; skip already-resolved work. See [concurrent-work.md](../../concurrent-work.md).

Scores use impact × reach ÷ risk from [findings.md](../../findings.md). Candidate-only code findings and unverified surfaces stay explicitly qualified; they do not authorize deletions.

## F-33 — Published screen contracts contradict each other

### Issue

A1D01 reactiontwo rows/Yourreactions versus scrollingwall/presets; D03sheetclick opensdetails versus neveropens; D04–06builtmap/journey/tabspecs versus planned wording; D08startup rules differ. Both file:line sides in docs_reader.md.

**Confidence:** docs confirmed. **Impact / reach / risk:** 6 / 5 / 1. **Priority:** 30.0.

### Proposed fix

Choose dated current contracts and remove stale statements; UI gateway under1KB links owners instead of reprinting contracts.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-33--published-screen-contracts-contradict-each-other). Source/document evidence; no screenshot claimed.

### Bounded implementation work

- [T-079](../../../uiux_plan.md) — Reconcile current UI screen contracts (luna-6-high); docs/design/04-4-the-shell-rules-that-hold-on-every-screen.md, docs/design/11-ui-ux-pass-of-2026-10-03-what-a-click-means.md, docs/reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md, docs/redesign_plan.md.
  Replace stale two-row/Your reactions prose with current wall/Done/load-more/preset contract, marking historical proposals historical. Reconcile sheet-cell click semantics against the retained action map and rule10; keep current two pack tabs untilQ2 has an owner answer. State that project map/journey is built and which older proposal paragraphs are superseded. Put reaction behavior in its owner section and link from shell. Do not implement or decide Q1/Q2.
- [T-081](../../../uiux_plan.md) — Correct contradictory final-block and startup wording (6.1-sol-medium); docs/rules.md, docs/agent-and-chat.md.
  Replace the blanket Python BLOCK verdicts are final wording with the current CLAUDE rule10 distinction: only Telegram technical/no-cut failures final; every other check visibly recorded/reversible. Replace upfront read-every-tracker startup with current lean task-index/needed-section rule; trackers/devnotes/testing read only when touched. Keep historical notes explicitly historical, never change engine decision tables or user authorization.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-34 — Doc organization and tracker IDs raise reading cost

### Issue

architecture28356B; export176287B with generated bank; UIinventory~46KB searchable; designinteraction17445B spansfourtopics. FullCLAUDE7954B alone nearly8KB; waiting49 duplicated and headermax39.

**Confidence:** measured docs. **Impact / reach / risk:** 4 / 6 / 1. **Priority:** 24.0.

### Proposed fix

Split task-critical wiring/contracts from appendices; compact responsibility indexes; preserve tracker provenance when disambiguating duplicate49.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-34--doc-organization-and-tracker-ids-raise-reading-cost). Source/document evidence; no screenshot claimed.

### Bounded implementation work

- [T-080](../../../uiux_plan.md) — Create a cheap UI reading gateway and wiring appendix (luna-6-high); CLAUDE.md, README.md, docs/design.md, docs/architecture.md, docs/ui_gateway.md, docs/architecture-ui-wiring.md.
  Add docs/ui_gateway.md under1KB linking shell/tokens/recovery/currentscreen owners and test map. Extract UI wiring from architecture into a bounded appendix and link it; leave Python/module inventory out of the UI task path. Compress repeated startup/history/routing prose in CLAUDE to≤4KB while preserving all13constraints, tests/git/server authorization and scope links to full rules; do not weaken any rule. Design/README route UI tasks to the gateway. Total gateway+sharedshell/foundation+needed recovery passage must be≤8KB before code, counting inherited CLAUDE separately and reporting both totals.
- [T-082](../../../uiux_plan.md) — Merge tracked work and disambiguate tracker IDs (luna-6-high); docs/backlog.md, docs/waiting-for-haitham.md, plan.md.
  Map implemented UXtasks to existing W1/W4/W16/W18/W19/W20/W22/W23/W33/W34/Help items before adding any tracker row. Remove only actually completed machine items from plan/backlog and write their area contract; retain pending human verdicts, paid work, Spending and held retirements. Assign the two W49 entries unique stable ids only after classifying every reference in both trackers, preserving their original dates/history and routing ambiguous references explicitly. Refresh max-id/branch metadata. Keep plan.md pack no-tabs/newsave/erosion open unless independently implemented and authorized.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-11 — Long-line scripts make small changes expensive to review

### Issue

38JS files760119bytes/9256lines;264 lines >300chars; 290 literal style attributes. Packs/particles/reactions/live contain compressed helpers. Full per-file counts and AST-backed >80-line candidates: code_reader.md appendix.

**Confidence:** measured structure. **Impact / reach / risk:** 3 / 6 / 1. **Priority:** 18.0.

### Proposed fix

Reflow bounded named functions with vendored Acorn canonical token equality; do not blanket-format templates.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-11--long-line-scripts-make-small-changes-expensive-to-review). Source/document evidence; no screenshot claimed.

### Bounded implementation work

- [T-059](../../../uiux_plan.md) — Reflow packs.js bounded helpers (6.1-sol-medium); mirsal/mirsal/console/packs.js.
  Reflow only named helper bodies pkGroups and pkGroupHead; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
- [T-060](../../../uiux_plan.md) — Reflow live.js bounded helpers (6.1-sol-medium); mirsal/mirsal/console/live.js.
  Reflow only named helper bodies egCard and egCommitted; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
- [T-061](../../../uiux_plan.md) — Reflow particles.js bounded helpers (6.1-sol-medium); mirsal/mirsal/console/particles.js.
  Reflow only named helper bodies spBurstState and spBSlider; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.
- [T-062](../../../uiux_plan.md) — Reflow reactions.js bounded helpers (6.1-sol-medium); mirsal/mirsal/console/reactions.js.
  Reflow only named helper bodies rxBody and rxFields; split statements/indent blocks outside template/string/regex literals. Preserve every literal token, template text, comment wording, ACT name and payload. At most150 changed lines; do not format the whole file or any other function. Capture file bytes before edit and compare canonical(before)===canonical(after) with existing tests/js/console_source.js (vendored Acorn); literal/template tokens must be byte-identical. This is formatting only.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-21 — Inventory unique count omits the extra overwrite

### Issue

Current table483 definitions/481 unique ACT names; current heading482/483. Both ggo and gkeepsize are defined twice; only ggo is documented as intentional.17screen keys/22render assignments.

**Confidence:** measured source/docs. **Impact / reach / risk:** 4 / 3 / 1. **Priority:** 12.0.

### Proposed fix

After the Keep repair regenerate inventory and verify unique counts; no baseline action drops.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-21--inventory-unique-count-omits-the-extra-overwrite). Source/document evidence; no screenshot claimed.

### Bounded implementation work

- [T-064](../../../uiux_plan.md) — Refresh generated inventory counts after repairs (6.1-sol-medium); docs/ui_inventory.md.
  Regenerate/read console inventory using python -m mirsal.console.inventory from mirsal/ in measure-only mode; update this doc's heading/table from current actual definitions and unique ACT names. Confirm ggo remains intentional override and gkeepsize has one definition. Preserve baseline data/routes; current review snapshot was481 unique/483 definitions, after CT-001 expected481/482 unless an authorized concurrent change exists. Record current measured values, never hard-code the stale482 unique.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-20 — History retirement prose contradicts active route

### Issue

index.html:47 loads history.js; app.js:203 includes history and :266 Watch folders; history.js:8,35 render/poll. backlog:112/waiting:78 call it retired. React web/ remains parked.

**Confidence:** source and docs confirmed. **Impact / reach / risk:** 4 / 2 / 1. **Priority:** 8.0.

### Proposed fix

Correct the prose; keep route/actions/owner gate and parked React.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-20--history-retirement-prose-contradicts-active-route). Source/document evidence; no screenshot claimed.

### Bounded implementation work

- [T-063](../../../uiux_plan.md) — Correct retired-History wording (6.1-sol-medium); docs/waiting-for-haitham.md.
  In item34 only, replace fact 'nothing in rail opens it'/'retired' with current owner-avatar Watch folders route #/history, loaded history.js and active /api/watch refresh. Retain the owner's keep/delete decision as unanswered; recommendation may say keep until the active owner workflow has an approved replacement and recorded baseline retirement. Do not delete code or decide W33 React removal.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-18 — Script-order wrappers form implicit extension contracts

### Issue

live/composer replace RENDER.generate/ACT.ggo; Settings wraps across settings→trash→tickets→auth; particles wraps RENDER.effects; projmap wraps hist/view functions.18-file regex SCC is not runtime recursion proof.

**Confidence:** source confirmed architecture. **Impact / reach / risk:** 3 / 7 / 3. **Priority:** 7.0.

### Proposed fix

Preserve loading order; extract small presenters first. Defer universal extension bus.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-18--script-order-wrappers-form-implicit-extension-contracts). Source/document evidence; no screenshot claimed.

### Bounded implementation work

No standalone repair assigned; preserve the qualified finding and reconcile it during the related shared cleanup.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-16 — Missing literal buttons do not prove dead actions

### Issue

26 ACT candidates from literal inventory include dynamic shell/JR names, Enter-driven ggo and compatibility qretry. Stronger candidates listed in code_reader.md.

**Confidence:** candidate scan only. **Impact / reach / risk:** 2 / 3 / 3. **Priority:** 2.0.

### Proposed fix

Keep every candidate until callers/dynamic markup/baseline are checked and owner authorizes any retirement.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-16--missing-literal-buttons-do-not-prove-dead-actions). Source/document evidence; no screenshot claimed.

### Bounded implementation work

No standalone repair assigned; preserve the qualified finding and reconcile it during the related shared cleanup.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-15 — Relative-time helpers use distinct units/policies

### Issue

Live history, chat and Trash format seconds/milliseconds and differing granularity/local time. Code_reader.md lists ownership.

**Confidence:** partial; defer. **Impact / reach / risk:** 1 / 3 / 2. **Priority:** 1.5.

### Proposed fix

Pin units first if revisited; no mechanical merge of policy into one global helper.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-15--relative-time-helpers-use-distinct-unitspolicies). Source/document evidence; no screenshot claimed.

### Bounded implementation work

No standalone repair assigned; preserve the qualified finding and reconcile it during the related shared cleanup.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-14 — Escaping aliases are not unsafe global collisions

### Issue

Scoped escape helpers in TRX/tickets/auth and esc at app.js:6; no same-name top-level declaration collisions in828 lexical definitions. Standalone bundle tests intentionally avoid shell dependencies.

**Confidence:** low-payoff candidate. **Impact / reach / risk:** 1 / 2 / 2. **Priority:** 1.0.

### Proposed fix

Retain scoped aliases and standalone fixtures; document boundary instead of a forced shared-global rewrite.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-14--escaping-aliases-are-not-unsafe-global-collisions). Source/document evidence; no screenshot claimed.

### Bounded implementation work

No standalone repair assigned; preserve the qualified finding and reconcile it during the related shared cleanup.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-17 — Unmatched CSS scan is a candidate list

### Issue

37 studio.css absent-class candidates after conservative filtering; dynamic class concatenation and third-party/legacy markup can invalidate lexical absence.

**Confidence:** static best effort. **Impact / reach / risk:** 1 / 3 / 3. **Priority:** 1.0.

### Proposed fix

No CSS deletion from this scan alone. Require emitted-markup evidence and scoped acceptance before future cleanup.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-17--unmatched-css-scan-is-a-candidate-list). Source/document evidence; no screenshot claimed.

### Bounded implementation work

No standalone repair assigned; preserve the qualified finding and reconcile it during the related shared cleanup.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.
