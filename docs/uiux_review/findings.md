# UI/UX findings — 2026-10-14

> **Concurrent implementation notice:** Evidence belongs to the audited snapshot, while another LLM advanced source during review. Reconcile current CLAUDE.md and [concurrent-work.md](concurrent-work.md) before treating a finding or task as current.

Review of commit `170f26e36893a194248eaf5d88449ecba9e9bcd7` on `ui/ux-review`. No implementation, paid job, provider acceptance, Telegram transfer or collection Send was performed. Existing checkout media/data edits were left untouched. Source line numbers are original anchors; use named functions after reflow.

## Method and reproducible severity

Desktop1440×900/DPR0.5, phone390×844/DPR1; viewport JPEG quality60. `probes.jsonl` contains every recorded probe, including attempts/transients; `screens.md` identifies authoritative settled states. `probe.js` is the final reusable expression. It excludes closed details, transparent/hidden controls and elements clipped outside scroll containers; discovery emoji items are counted separately from non-item controls. Earlier raw probes remain marked superseded, not used to inflate severity. Styles count mounted DOM across inactive screens, so they are diagnostics, not a claim that all styles are visible. Modal probes may count occluded background controls; manual modal judgment overrides choice overload. The tiny-target threshold is width<32 OR height<28; rounding can show28 for27.6. It intentionally flags only a subset of the44px target goal.

State metric M = 2×floor(max(controls−15,0)/10) +2[tiny>5] +2[fontSizes>6] +2[textColours>8] +1[inlineStyles>20] +1[depth>25] +4[confirmed unintended text/page overflow]. Add5 for a reproduced broken interaction,3 for >2 competing primaries/no clear primary where a task requires one,3 for a rule10 picture/reason/action omission,2 for a documented promise violation and1 per verified extra journey click. No zero-primary penalty for browsing, settings, disabled provider states or required per-picture override actions. Raw overflow alone never adds4: translated tracks, intentionally clipped media and decoration are excluded. No generic console-error penalty: the12 accumulated errors include server restarts/disabled-provider setup and were not attributable new crashes.

Code/doc-only scores are a declared rubric:1 low-payoff candidate,3 confirmed repeated presentation,5 broken contract or broad duplicated lifecycle, +2 documented contradiction/broad reach, with multi-clause evidence yielding the stated impact. F01 = settled batch M15+broken5+promise2 =22. F22 = G001M15+competing primaries3 =18. F19 = reaction editorM9. F06 = retimeM3+broken5 =8. F05 = broken serialization5+duplicate scheduling3+promise2 =10. F33 = three contradictory current-screen promises×2 =6. F30=welcome rawM11+theme promise2=13; rawM includes background, so its rank is supported principally by settled paired visual/source evidence, not a measured contrast ratio. These are prioritization judgments, not an accessibility certification.

Priority=impact×reach/risk; risk low=1, medium=2, high=3. Reach counts affected journeys/screens from the inventory; all values are explicit below and owner choices are kept out of runnable tasks.

## Ranked findings

| Rank | ID | Finding | Impact | Reach | Risk | Priority |
|---:|---|---|---:|---:|---:|---:|
| 1 | F-22 | Tap targets are too small across core journeys | 18 | 9 | 2 | 81.0 |
| 2 | F-19 | Presentation bypasses a shared token system | 9 | 11 | 2 | 49.5 |
| 3 | F-01 | Keep approved size bypasses preview | 22 | 2 | 1 | 44.0 |
| 4 | F-05 | Refresh loops can overlap and redraw twice | 10 | 8 | 2 | 40.0 |
| 5 | F-33 | Published screen contracts contradict each other | 6 | 5 | 1 | 30.0 |
| 6 | F-30 | Dark welcome text fades into pale artwork | 13 | 2 | 1 | 26.0 |
| 7 | F-06 | Backdrop hides retime without settling its promise | 8 | 3 | 1 | 24.0 |
| 8 | F-34 | Doc organization and tracker IDs raise reading cost | 4 | 6 | 1 | 24.0 |
| 9 | F-36 | Phone viewer header squeezes the title into a word column | 12 | 2 | 1 | 24.0 |
| 10 | F-07 | Segment builders disagree about semantics | 7 | 6 | 2 | 21.0 |
| 11 | F-11 | Long-line scripts make small changes expensive to review | 3 | 6 | 1 | 18.0 |
| 12 | F-24 | Cover badge intercepts Timeline click | 9 | 2 | 1 | 18.0 |
| 13 | F-28 | Help rows are click-only divs | 6 | 3 | 1 | 18.0 |
| 14 | F-08 | Download lifecycle is copied | 3 | 4 | 1 | 12.0 |
| 15 | F-21 | Inventory unique count omits the extra overwrite | 4 | 3 | 1 | 12.0 |
| 16 | F-29 | Library/public/Home totals count reactions as stickers | 9 | 4 | 3 | 12.0 |
| 17 | F-35 | Phone Library tabs locally exceed their row | 6 | 2 | 1 | 12.0 |
| 18 | F-23 | Allowed animations lose the readable boundary reason | 11 | 3 | 3 | 11.0 |
| 19 | F-03 | Grouped grids repeat presentation | 7 | 3 | 2 | 10.5 |
| 20 | F-04 | Range controls repeat across distinct reaction contracts | 5 | 4 | 2 | 10.0 |
| 21 | F-10 | Feedback markup repeats with different lifetimes | 4 | 5 | 2 | 10.0 |
| 22 | F-26 | Local Account shortcut is a no-op | 10 | 1 | 1 | 10.0 |
| 23 | F-32 | Studio prompt view is dense and exposes an engine inspector | 9 | 2 | 2 | 9.0 |
| 24 | F-02 | Two Apply/Cancel presenters drift | 8 | 2 | 2 | 8.0 |
| 25 | F-09 | Preview request lifecycles repeat; endpoints are distinct | 6 | 4 | 3 | 8.0 |
| 26 | F-20 | History retirement prose contradicts active route | 4 | 2 | 1 | 8.0 |
| 27 | F-18 | Script-order wrappers form implicit extension contracts | 3 | 7 | 3 | 7.0 |
| 28 | F-25 | Reaction editor and batch controls compete for space | 7 | 2 | 2 | 7.0 |
| 29 | F-27 | Tickets have no section shortcut | 7 | 1 | 1 | 7.0 |
| 30 | F-31 | Same Reaction effects wording leads to different workflows | 7 | 3 | 3 | 7.0 |
| 31 | F-12 | Range label/output builders repeat in editors | 3 | 4 | 2 | 6.0 |
| 32 | F-13 | Decision reason boxes need one UI presentation adapter | 6 | 3 | 3 | 6.0 |
| 33 | F-16 | Missing literal buttons do not prove dead actions | 2 | 3 | 3 | 2.0 |
| 34 | F-15 | Relative-time helpers use distinct units/policies | 1 | 3 | 2 | 1.5 |
| 35 | F-14 | Escaping aliases are not unsafe global collisions | 1 | 2 | 2 | 1.0 |
| 36 | F-17 | Unmatched CSS scan is a candidate list | 1 | 3 | 3 | 1.0 |

## Evidence by finding

### F-01 — Keep approved size bypasses preview

Screen/state: J1. Severity **22**; reach2; risk1; priority44.0. Confidence: broken. Merged evidence: C-01.

Evidence: studio-core.js:858,901; loaded ACT.gkeepsize.toString() POSTs keep_size immediately. Video-size +/- opens #vzcard while Keep uses the overwritten handler.

Screenshots: J1-04-preview-dark.jpg.

Plan: Restore the staged handler before extracting testCard; zero mutations before Apply; Cancel writes nothing.

### F-02 — Two Apply/Cancel presenters drift

Screen/state: J1. Severity **8**; reach2; risk2; priority8.0. Confidence: confirmed duplicate. Merged evidence: C-02.

Evidence: live.js:237–243 egCard; studio-core.js:806–827 vzCard; studio-core.js:792 explicitly describes copying. Media type, busy states and viewport anchoring differ.

Screenshots: J1-04-preview-dark.jpg.

Plan: Introduce ui-testcard.js testCard; video then edge adapters; responsive sheet treatment after behavior is pinned.

### F-03 — Grouped grids repeat presentation

Screen/state: J3. Severity **7**; reach3; risk2; priority10.5. Confidence: confirmed duplicate. Merged evidence: C-03.

Evidence: library.js:361–372 libByPackHtml and packs.js:7–39,85–88 pkGroups/pkGroupHead; studio.css:781,783 duplicate group declarations. Existing selection is shared.

Screenshots: J3-02-grouped-dark.jpg, J3-03-pack-dark.jpg.

Plan: Extract only groupedGridHtml; Library keeps global carousel indices, Pack keeps source groups, ordering, cover and drag actions.

### F-04 — Range controls repeat across distinct reaction contracts

Screen/state: J5. Severity **5**; reach4; risk2; priority10.0. Confidence: partial duplicate. Merged evidence: C-04.

Evidence: effects.js:17–19, particles.js:365–366, reactions.js:16–18,124–126. Six descriptors/five preset labels overlap; FX/SP is already shared.

Screenshots: J5-03-motion-light.jpg, J4-02-editor-dark.jpg.

Plan: Share rangeFieldHtml; retain namespaces, defaults, touched-only params, versioned emoji and pack ownership.

### F-05 — Refresh loops can overlap and redraw twice

Screen/state: source/documentation audit. Severity **10**; reach8; risk2; priority40.0. Confidence: source confirmed; latency not measured. Merged evidence: C-05.

Evidence: studio-core.js:913–973 async tick each700ms without in-flight guard; live.js:185,191 both1s queue redraw; :267 unconditional800ms egSync.61 timer call sites across38scripts.

Screenshots: code-only; J1-03-batch-dark.jpg is visual context, not latency proof.

Plan: Serialize tick, coalesce queue clock, then migrate one watcher per task. Preserve forced refresh and off-screen job completion.

### F-06 — Backdrop hides retime without settling its promise

Screen/state: J9. Severity **8**; reach3; risk1; priority24.0. Confidence: browser confirmed broken. Merged evidence: C-06.

Evidence: packs.js:47–53 retimeAsk/RTA; app.js:114–121 closeDlg/backdrop. Actual backdrop click leaves typeof RTA==function; explicit Cancel clears it. Applies to ZIP and Telegram retime callers.

Screenshots: J9-01-retime-dark.jpg, J9-03-telegram-dark.jpg.

Plan: Every dismissal/replacement settles null once; keep explicit answers true/false and all request payloads.

### F-07 — Segment builders disagree about semantics

Screen/state: J3. Severity **7**; reach6; risk2; priority21.0. Confidence: confirmed duplicate. Merged evidence: C-07.

Evidence: composer.js:99, studio-core.js:613, packs.js:31 (role=tab with aria-pressed), reactions.js:99, settings.js:19. Already one .gseg CSS but five builders.

Screenshots: J3-03-pack-dark.jpg, J4-03-presets-light.jpg, J8-01-settings-dark.jpg.

Plan: segmentedHtml has choice/tabs/navigation modes; do not turn navigation into a preference or change data-act.

### F-08 — Download lifecycle is copied

Screen/state: source/documentation audit. Severity **3**; reach4; risk1; priority12.0. Confidence: confirmed duplicate. Merged evidence: C-08.

Evidence: animate.js:68, prepare.js:198 blob/object URL/anchor/revoke; editor.js:224 data URL; particles.js:429 and reactions.js:317–346 server URLs. Telegram tg:// is not a download.

Screenshots: code-only.

Plan: downloadFile owns only object URLs it creates; preserve filenames and each URL/body; migrate consumers separately.

### F-09 — Preview request lifecycles repeat; endpoints are distinct

Screen/state: J1. Severity **6**; reach4; risk3; priority8.0. Confidence: partial duplicate. Merged evidence: C-09.

Evidence: studio-core.js:834–841 generation counter; reactions.js:206–239 RXS.pv/ppv caches without eviction; particles.js:395–406 busy/again/signature. Edge/sheet/anim/emoji endpoints perform different work.

Screenshots: J1-04-preview-dark.jpg, J4-02-editor-light.jpg.

Plan: Introduce bounded latest-result previewSession; never combine backend operations or move rendering decisions into JS.

### F-10 — Feedback markup repeats with different lifetimes

Screen/state: J9. Severity **4**; reach5; risk2; priority10.0. Confidence: partial duplicate. Merged evidence: C-10.

Evidence: app.js:24 toast; packs.js:60–74 persistent collection validation; particles.js spBurstHtml warning; notifications are durable outcomes.

Screenshots: J9-02-collection-dark.jpg.

Plan: Share inline status markup only; retain toast, field errors and durable notifications as different channels.

### F-11 — Long-line scripts make small changes expensive to review

Screen/state: source/documentation audit. Severity **3**; reach6; risk1; priority18.0. Confidence: measured structure. Merged evidence: C-11.

Evidence: 38JS files760119bytes/9256lines;264 lines >300chars; 290 literal style attributes. Packs/particles/reactions/live contain compressed helpers. Full per-file counts and AST-backed >80-line candidates: code_reader.md appendix.

Screenshots: code-only.

Plan: Reflow bounded named functions with vendored Acorn canonical token equality; do not blanket-format templates.

### F-12 — Range label/output builders repeat in editors

Screen/state: source/documentation audit. Severity **3**; reach4; risk2; priority6.0. Confidence: confirmed presentation overlap. Merged evidence: C-12.

Evidence: prepare.js/editor.js range rows versus particles.js spBSlider/reactions.js rxSlider; same label/range/output pattern, different user-art values.

Screenshots: code-only.

Plan: rangeFieldHtml can host them later, one caller per task; user artwork colours/canvas coordinates remain data.

### F-13 — Decision reason boxes need one UI presentation adapter

Screen/state: J6. Severity **6**; reach3; risk3; priority6.0. Confidence: confirmed shared invariant. Merged evidence: C-13.

Evidence: studio-tiles.js:135–147 reason boxes/blocked overlay; chat-cards.js rejected tile builders; decision authority is verify/gates API, not JS.

Screenshots: J6-01-blocked-animation-dark.jpg, J6-02-rejected-still-detail-dark.jpg.

Plan: Build decisionStatusHtml from existing backend eligibility and reason data; keep allow/include/drop distinctions and bulk controls.

### F-14 — Escaping aliases are not unsafe global collisions

Screen/state: source/documentation audit. Severity **1**; reach2; risk2; priority1.0. Confidence: low-payoff candidate. Merged evidence: C-14.

Evidence: Scoped escape helpers in TRX/tickets/auth and esc at app.js:6; no same-name top-level declaration collisions in828 lexical definitions. Standalone bundle tests intentionally avoid shell dependencies.

Screenshots: code-only.

Plan: Retain scoped aliases and standalone fixtures; document boundary instead of a forced shared-global rewrite.

### F-15 — Relative-time helpers use distinct units/policies

Screen/state: source/documentation audit. Severity **1**; reach3; risk2; priority1.5. Confidence: partial; defer. Merged evidence: C-15.

Evidence: Live history, chat and Trash format seconds/milliseconds and differing granularity/local time. Code_reader.md lists ownership.

Screenshots: code-only.

Plan: Pin units first if revisited; no mechanical merge of policy into one global helper.

### F-16 — Missing literal buttons do not prove dead actions

Screen/state: source/documentation audit. Severity **2**; reach3; risk3; priority2.0. Confidence: candidate scan only. Merged evidence: C-16.

Evidence: 26 ACT candidates from literal inventory include dynamic shell/JR names, Enter-driven ggo and compatibility qretry. Stronger candidates listed in code_reader.md.

Screenshots: code-only.

Plan: Keep every candidate until callers/dynamic markup/baseline are checked and owner authorizes any retirement.

### F-17 — Unmatched CSS scan is a candidate list

Screen/state: source/documentation audit. Severity **1**; reach3; risk3; priority1.0. Confidence: static best effort. Merged evidence: C-17.

Evidence: 37 studio.css absent-class candidates after conservative filtering; dynamic class concatenation and third-party/legacy markup can invalidate lexical absence.

Screenshots: code-only.

Plan: No CSS deletion from this scan alone. Require emitted-markup evidence and scoped acceptance before future cleanup.

### F-18 — Script-order wrappers form implicit extension contracts

Screen/state: source/documentation audit. Severity **3**; reach7; risk3; priority7.0. Confidence: source confirmed architecture. Merged evidence: C-18.

Evidence: live/composer replace RENDER.generate/ACT.ggo; Settings wraps across settings→trash→tickets→auth; particles wraps RENDER.effects; projmap wraps hist/view functions.18-file regex SCC is not runtime recursion proof.

Screenshots: code-only.

Plan: Preserve loading order; extract small presenters first. Defer universal extension bus.

### F-19 — Presentation bypasses a shared token system

Screen/state: J1. Severity **9**; reach11; risk2; priority49.5. Confidence: measured structure + browser. Merged evidence: C-19.

Evidence: 610 non-custom CSS declarations contain literal colours; studio/agent/theme7/1/0!important;290 JSstyle attributes;218 literal px occurrences. Existing six-size scale is studio.css:5. Tokens do not cover all status/material/spacing uses.

Screenshots: J1-01-studio-dark.jpg, J1-03-batch-light.jpg, J3-03-pack-light.jpg, J11-06-editor-light.jpg.

Plan: Introduce semantic spacing/type/status/material/control tokens; convert one bounded block per task; never tokenize art content values.

### F-20 — History retirement prose contradicts active route

Screen/state: source/documentation audit. Severity **4**; reach2; risk1; priority8.0. Confidence: source and docs confirmed. Merged evidence: C-20.

Evidence: index.html:47 loads history.js; app.js:203 includes history and :266 Watch folders; history.js:8,35 render/poll. backlog:112/waiting:78 call it retired. React web/ remains parked.

Screenshots: code-only.

Plan: Correct the prose; keep route/actions/owner gate and parked React.

### F-21 — Inventory unique count omits the extra overwrite

Screen/state: source/documentation audit. Severity **4**; reach3; risk1; priority12.0. Confidence: measured source/docs. Merged evidence: C-21.

Evidence: Current table483 definitions/481 unique ACT names; current heading482/483. Both ggo and gkeepsize are defined twice; only ggo is documented as intentional.17screen keys/22render assignments.

Screenshots: code-only.

Plan: After the Keep repair regenerate inventory and verify unique counts; no baseline action drops.

### F-22 — Tap targets are too small across core journeys

Screen/state: J1. Severity **18**; reach9; risk2; priority81.0. Confidence: browser measured. Merged evidence: browser.

Evidence: Settled Studio batch66controls/35tiny; G00167/37; Trash37/28; current reaction editor Close12×28px, Reset43×24; welcome dots72×18; phone editor Close still12px wide. Tiny threshold in probe is width<32 OR height<28, smaller than44px goal.

Screenshots: J1-03-batch-dark.jpg, J3-04-viewer-dark.jpg, J3-05-timeline-dark.jpg, J4-04-batch-dark.jpg, J8-02-trash-dark.jpg, J11-04-viewer-dark.jpg, J11-06-editor-dark.jpg.

Plan: Use44px logical targets, consistent8px gaps and secondary/tinted controls; retain every action and per-picture recovery.

### F-23 — Allowed animations lose the readable boundary reason

Screen/state: J1. Severity **11**; reach3; risk3; priority11.0. Confidence: source + browser confirmed; bounded sample. Merged evidence: browser + C-13.

Evidence: G146S2/S6 and G001S1/S7 show allowed by you + Take it back in tile captions. Full boundary reason is in sheet cell title; studio-tiles.js:276 constructs short allowed caption, sheet cell titles in studio-sheet.js. Blocked G001S2/S9 do show picture/reason/Use it anyway; human-rejected G012S5 is a different drop/Bring back state.

Screenshots: J1-03-batch-dark.jpg, J6-01-blocked-animation-dark.jpg.

Plan: Keep a one-sentence reason next to the allowed preview and a visible selected-sheet-cell status row. Preserve backend eligibility, technical final blocks and bulk recovery.

### F-24 — Cover badge intercepts Timeline click

Screen/state: J3. Severity **9**; reach2; risk1; priority18.0. Confidence: native hit-test confirmed broken. Merged evidence: browser.

Evidence: packs.js:33 badge2 cover overlay and :34 hover buttons; native click on first card stanim fails with span.badge2 intercepting pointer events. The next sticker Timeline button opens #/animate/9ebb180c/fc6b6fcf.

Screenshots: J3-05-cover-hover-dark.jpg.

Plan: Make decorative cover badge pointer-events:none or place it clear of controls; native click must work, no forced click workaround.

### F-25 — Reaction editor and batch controls compete for space

Screen/state: J4. Severity **7**; reach2; risk2; priority7.0. Confidence: browser + existing tracked work. Merged evidence: browser.

Evidence: Current wall initially loads120items; actual bank1898 with4done.27–30non-item controls; editor has11sliders, tinyReset/Close and below-wall actions. Shift happy→love correctly selects5. Pack set shows raw ids/unlink rows and two Advanced sections. plan.md UIcleanup1–4 already requests disclosure.

Screenshots: J4-01-wall-light.jpg, J4-02-editor-dark.jpg, J4-03-presets-light.jpg, J4-04-batch-dark.jpg, J5-02-set-card-light.jpg, J5-03-motion-light.jpg.

Plan: Group basic motion/shape and one Advanced; sticky phone action footer; keep complete bank/preset/batch actions and values. Merge existing plan items rather than call them new.

### F-26 — Local Account shortcut is a no-op

Screen/state: J8. Severity **10**; reach1; risk1; priority10.0. Confidence: browser confirmed broken. Merged evidence: J8-F01.

Evidence: settings.js:19 emits Account→au-me; :41 ignores missing target; auth.js:82 only adds Account for LAN. Non-LAN DOM #au-me count0 while button remains.

Screenshots: J8-01-settings-dark.jpg, J8-01-settings-light.jpg.

Plan: Derive section shortcuts from mounted cards after wrappers; retain LAN Account entry and backend behavior.

### F-27 — Tickets have no section shortcut

Screen/state: J8. Severity **7**; reach1; risk1; priority7.0. Confidence: browser confirmed. Merged evidence: J8-F02.

Evidence: settings.js:19 lacks Tickets; tickets.js:50–53 appends owner card after Trash wrapper. Reaching Tickets requires scrolling past nine trash items.

Screenshots: J8-06-tickets-bottom-dark.jpg.

Plan: Add role-aware Tickets section entry after mounted card detection; do not create another route.

### F-28 — Help rows are click-only divs

Screen/state: J8. Severity **6**; reach3; risk1; priority18.0. Confidence: source + accessibility snapshot. Merged evidence: J8-F04.

Evidence: support.js:14,46,55 emit conversation/queue/FAQ data-act rows without native button roles/focus. FAQ titles appear as text in accessibility snapshot.

Screenshots: J8-04-faq-dark.jpg.

Plan: Use native focusable title controls with sibling secondary actions; preserve suopen/suq/sufaq, selected/scroll states and role visibility.

### F-29 — Public/Home totals count reactions as stickers

Screen/state: J8. Severity **9**; reach3; risk3; priority9.0. Confidence: browser/source; API follow-up needed. Merged evidence: J8-F05.

Evidence: Trending Angel10 versus9stickers+1reaction sidebar; Batman19 versus17+2. trending.js:11/home.js:44 and My Stickers library.js:372 count total while sidebar app.js:430 and pack row library.js:400 exclude particle_set. Grouped My Stickers also shows Batman19 rather than17+2. Contradicts docs/reaction/12-11-added-bursts-are-reactions-not-stickers-2026.md:5.

Screenshots: J8-05-trending-dark.jpg, J7-01-home-dark.jpg.

Plan: Define additive backend sticker_count/reaction_count, preserving existing fields and permissions; migrate Trending/Home presentation separately.

### F-30 — Dark welcome text fades into pale artwork

Screen/state: J7. Severity **13**; reach2; risk1; priority26.0. Confidence: settled paired screenshots; contrast ratio not measured. Merged evidence: J7-F02.

Evidence: studio.css:583–584 use general --ink/--ink2 over fixed pale slide art; theme.css:7 dark ink is pale. Settled One idea slide title/body almost disappear in dark and are legible in light. Welcome dots18px remain small.

Screenshots: J7-03-welcome-settled-dark.jpg, J7-03-welcome-settled-light.jpg.

Plan: Give slide text a fixed light-surface semantic palette or guaranteed contrasting text backing; preserve artwork/film; make dot hit regions44px.

### F-31 — Same Reaction effects wording leads to different workflows

Screen/state: J5. Severity **7**; reach3; risk3; priority7.0. Confidence: browser/source confirmed product choice. Merged evidence: browser.

Evidence: home.js:55 Try reaction effects→#/effects; actual click confirmed. app.js:295 +New Reaction effects→#/reactions. Standalone effects shows giant sticker-source chooser; emoji wall is a distinct screen.

Screenshots: J5-04-effects-light.jpg, J7-01-home-dark.jpg.

Plan: Ask owner which door Home should present; recommend distinct pack-reaction/emoji-reaction labels while preserving both routes.

### F-32 — Studio prompt view is dense and exposes an engine inspector

Screen/state: J1. Severity **9**; reach2; risk2; priority9.0. Confidence: browser measured; no model-off error score. Merged evidence: browser.

Evidence: Prompt contains long sheet/video text + per-sticker metadata, while composer adds model/style/stroke/loop/reaction switches and Auto/Local/Cloud/no-model inspector. Current plan reached free built-in draft; paid Generate sheet stayed disabled.

Screenshots: J1-01-studio-dark.jpg, J1-02-plan-dark.jpg, J2-03-plan-dark.jpg.

Plan: Keep editable prompt, price/unavailable explanation and primary; group supporting metadata under Advanced. Move backend connection detail into expandable inspector.

### F-33 — Published screen contracts contradict each other

Screen/state: source/documentation audit. Severity **6**; reach5; risk1; priority30.0. Confidence: docs confirmed. Merged evidence: A1D-01..D-10.

Evidence: A1D01 reactiontwo rows/Yourreactions versus scrollingwall/presets; D03sheetclick opensdetails versus neveropens; D04–06builtmap/journey/tabspecs versus planned wording; D08startup rules differ. Both file:line sides in docs_reader.md.

Screenshots: code-only.

Plan: Choose dated current contracts and remove stale statements; UI gateway under1KB links owners instead of reprinting contracts.

### F-34 — Doc organization and tracker IDs raise reading cost

Screen/state: source/documentation audit. Severity **4**; reach6; risk1; priority24.0. Confidence: measured docs. Merged evidence: A1 structure.

Evidence: architecture28356B; export176287B with generated bank; UIinventory~46KB searchable; designinteraction17445B spansfourtopics. FullCLAUDE7954B alone nearly8KB; waiting49 duplicated and headermax39.

Screenshots: code-only.

Plan: Split task-critical wiring/contracts from appendices; compact responsibility indexes; preserve tracker provenance when disambiguating duplicate49.

### F-35 — Phone Library tabs locally exceed their row

Screen/state: J11. Severity **6**; reach2; risk1; priority12.0. Confidence: DOM local overflow; no page horizontal scroll. Merged evidence: browser.

Evidence: 390×844 Library probe marks .page/.tabs overflow visible; Trending row consumes extra width. No document horizontal scroll on any sampled phone state.

Screenshots: J11-01-library-dark.jpg.

Plan: Keep all four choices and expose them through wrapping/grid or accessible scrolling; acceptance is real pointer/keyboard access to Trending, no global width increase.

### F-36 — Phone viewer header squeezes the title into a word column

Screen: J11 settled viewer. Severity12; reach2; risk1; priority24. Confidence:settled phone screenshot and exact source; no page horizontal scroll.

Evidence:packs.js:177–179 lcDraw puts previous, metadata, four background choices, next and Close in one flex .mrow. At390px metadata shrinks to a few words per line and consumes most of the header height. The settled viewer screenshot proves the legibility/layout failure even though overflowing=0. Pending preview media is not scored as missing.

Screenshot: [J11-04-viewer-dark.jpg](shots/J11-04-viewer-dark.jpg).

Plan:At phone width give metadata a full header row with Close; put previous/background choices/next in a second row; preserve all labels/actions and a scrollable bounded viewer.

## Cited screenshot ledger

Only these files are committed; each has a finding citation. Loading placeholders/context shots are not media-quality or missing-picture proof. Screenshots carry UI presentation evidence; static correctness uses exact source/handler evidence.

| Screenshot | Finding(s) |
|---|---|
| [J1-01-studio-dark.jpg](shots/J1-01-studio-dark.jpg) | F-19, F-32 |
| [J1-02-plan-dark.jpg](shots/J1-02-plan-dark.jpg) | F-32 |
| [J1-03-batch-dark.jpg](shots/J1-03-batch-dark.jpg) | F-05, F-22, F-23 |
| [J1-03-batch-light.jpg](shots/J1-03-batch-light.jpg) | F-19 |
| [J1-04-preview-dark.jpg](shots/J1-04-preview-dark.jpg) | F-01, F-02, F-09 |
| [J11-01-library-dark.jpg](shots/J11-01-library-dark.jpg) | F-35 |
| [J11-03-pack-dark.jpg](shots/J11-03-pack-dark.jpg) | F-19 |
| [J11-04-viewer-dark.jpg](shots/J11-04-viewer-dark.jpg) | F-22, F-36 |
| [J11-05-wall-dark.jpg](shots/J11-05-wall-dark.jpg) | F-19 |
| [J11-06-editor-dark.jpg](shots/J11-06-editor-dark.jpg) | F-22 |
| [J11-06-editor-light.jpg](shots/J11-06-editor-light.jpg) | F-19 |
| [J2-01-chat-dark.jpg](shots/J2-01-chat-dark.jpg) | F-19 |
| [J2-03-plan-dark.jpg](shots/J2-03-plan-dark.jpg) | F-32 |
| [J3-01-library-dark.jpg](shots/J3-01-library-dark.jpg) | F-19 |
| [J3-02-grouped-dark.jpg](shots/J3-02-grouped-dark.jpg) | F-03, F-29 |
| [J3-03-pack-dark.jpg](shots/J3-03-pack-dark.jpg) | F-03, F-07 |
| [J3-03-pack-light.jpg](shots/J3-03-pack-light.jpg) | F-19 |
| [J3-04-viewer-dark.jpg](shots/J3-04-viewer-dark.jpg) | F-22 |
| [J3-05-cover-hover-dark.jpg](shots/J3-05-cover-hover-dark.jpg) | F-24 |
| [J3-05-timeline-dark.jpg](shots/J3-05-timeline-dark.jpg) | F-22 |
| [J4-01-wall-light.jpg](shots/J4-01-wall-light.jpg) | F-25 |
| [J4-02-editor-dark.jpg](shots/J4-02-editor-dark.jpg) | F-04, F-25 |
| [J4-02-editor-light.jpg](shots/J4-02-editor-light.jpg) | F-09 |
| [J4-03-presets-light.jpg](shots/J4-03-presets-light.jpg) | F-07, F-25 |
| [J4-04-batch-dark.jpg](shots/J4-04-batch-dark.jpg) | F-22, F-25 |
| [J5-01-pack-reactions-light.jpg](shots/J5-01-pack-reactions-light.jpg) | F-19 |
| [J5-02-set-card-light.jpg](shots/J5-02-set-card-light.jpg) | F-25 |
| [J5-03-motion-light.jpg](shots/J5-03-motion-light.jpg) | F-04, F-25 |
| [J5-04-effects-light.jpg](shots/J5-04-effects-light.jpg) | F-31 |
| [J6-01-blocked-animation-dark.jpg](shots/J6-01-blocked-animation-dark.jpg) | F-13, F-23 |
| [J6-02-rejected-still-dark.jpg](shots/J6-02-rejected-still-dark.jpg) | F-22 |
| [J6-02-rejected-still-detail-dark.jpg](shots/J6-02-rejected-still-detail-dark.jpg) | F-13 |
| [J6-02-rejected-still-light.jpg](shots/J6-02-rejected-still-light.jpg) | F-22 |
| [J6-03-chat-review-dark.jpg](shots/J6-03-chat-review-dark.jpg) | F-22 |
| [J7-01-home-dark.jpg](shots/J7-01-home-dark.jpg) | F-29, F-31 |
| [J7-03-welcome-settled-dark.jpg](shots/J7-03-welcome-settled-dark.jpg) | F-30 |
| [J7-03-welcome-settled-light.jpg](shots/J7-03-welcome-settled-light.jpg) | F-30 |
| [J8-01-settings-dark.jpg](shots/J8-01-settings-dark.jpg) | F-07, F-26 |
| [J8-01-settings-light.jpg](shots/J8-01-settings-light.jpg) | F-26 |
| [J8-02-trash-dark.jpg](shots/J8-02-trash-dark.jpg) | F-22 |
| [J8-02-trash-light.jpg](shots/J8-02-trash-light.jpg) | F-22 |
| [J8-04-faq-dark.jpg](shots/J8-04-faq-dark.jpg) | F-28 |
| [J8-05-trending-dark.jpg](shots/J8-05-trending-dark.jpg) | F-29 |
| [J8-06-tickets-bottom-dark.jpg](shots/J8-06-tickets-bottom-dark.jpg) | F-27 |
| [J9-01-retime-dark.jpg](shots/J9-01-retime-dark.jpg) | F-06 |
| [J9-02-collection-dark.jpg](shots/J9-02-collection-dark.jpg) | F-10 |
| [J9-03-telegram-dark.jpg](shots/J9-03-telegram-dark.jpg) | F-06 |
| [J3-06-edit-project-light.jpg](shots/J3-06-edit-project-light.jpg) | F-12, F-19 |

Five theme-comparison surfaces: Studio batch, emoji editor, Settings top/Trash, rejected-still Studio overview, settled welcome slide. Studio dark/light captures show the same batch in different media tabs after async redraw, so they support shared-target/style findings but not an exact same-state contrast claim. Pack and phone editor also have pairs. Contact sheets are navigation aids derived from the cited shots, one per journey and a J10 theme comparison. Total image budget is checked in manifest.json.

Editor comparison context: [J3-06-edit-project-light.jpg](shots/J3-06-edit-project-light.jpg) is cited by F-12/F-19 for the existing range/control structure; it is a passing editor state, not a new crash or media-quality finding. Opening Edit in Studio reached the existing prepare project; no Save/Export was submitted.

## Limits and preserved decisions

- Provider-off planning reached a free built-in draft; live cloud prices/real generation quality were not tested. No job acceptance/Create it/Allow vision/render/batch/Send/collection Send was pressed.
- J9 Telegram entry reached a retime question and was cancelled. `telegram.js:1–3,22–33` can auto-send when configured, new media exist and retime is unnecessary; provider-none flags do not disable Telegram. Future reviews intercept external mutation routes before opening that entry. No transfer occurred here.
- Welcome CSS-only dismissal from the supplied prompt leaves WL.open set, intercepting the first Escape. Corrected with wlClose(); this is a harness artifact, not a viewer Escape bug. Initial checkout/server/script drift was resolved by reloading assets and restarting only8795; current reaction captures replace old ones.
- G001 has blocked animationsS2/S9 and allowedS1/S7. G012S5 is human-rejected, not Python-blocked: Bring back remains a separate action. Saved chatS010 was inspected but did not expose the rejectedG012tile; its card parity is not declared passed. Technical-only final blocks were reviewed in source contracts, not deliberately generated.
- No LAN Users/privacy cross-account exercise, real support submission, export completion, persistent theme cross-tab/focus regression test or editor render/export was run. Spending is tracked unbuilt backend-first work, not a broken route.
- Static graph/unused CSS/ACT counts are conservative lexical/regex candidates; the18-file SCC does not prove recursion. Existing tests were inspected, not run, because this change is docs-only.
- W18pricing, W33parkedReact, W34heldHistory, old-batch/editor/mobile/Help acceptance and plan.md reaction cleanup are existing items to merge, not new product scope.

The44CSS-pixel design target follows the requested direction and [W3C target-size enhanced guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html); it is not a claim that every24–43px control fails WCAG AA. Proposed normal-text contrast≥4.5:1 (large text≥3:1) uses [W3C contrast minimum guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). Ratios over welcome artwork still need executor measurement.
