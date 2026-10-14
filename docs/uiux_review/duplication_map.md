# UI duplication map — measured 2026-10-14

> **Concurrent implementation notice:** Evidence belongs to the audited snapshot, while another LLM advanced source during review. Reconcile current CLAUDE.md and [concurrent-work.md](concurrent-work.md) before treating a finding or task as current.

Scope: console JavaScript, studio.css, agent.css, theme.css, index.html and docs/ui_inventory.md; no engine files. Paths below are relative to mirsal/mirsal/console/ unless stated. **Confirmed** means repeated implementation; **partial** means common presentation with different contracts; a whole-screen merge is not implied. One migration means one consumer, with the narrow named checks green before moving to the next. Run JS checks from the repository root as node --test mirsal/tests/js/NAME.test.js; run the inventory check from mirsal/ as python -m unittest tests.test_ui_inventory. Preserve every ACT name, route, owner gate, string id, server JSON payload, recorded/reversible override and baseline entry.

## Known suspects: all ten adjudicated

### D-01 / C-01, C-02 — Apply / Cancel test card: confirmed

Copies: live.js:237–243 (egCard, #egcard), studio-core.js:806–827 (vzCard, #vzcard); the comment at studio-core.js:792 explicitly says copied. Same checkerboard, test badge, caption, two buttons, 300 px width and viewport-clamped positioning. Edge uses an image and its egundo button also supports snapshot undo; video uses a looping video, loading spinner and disables buttons while busy. Video has a monotonically increasing request token; edge addresses an image URL. Keep approved size has a more urgent defect: ACT.gkeepsize at :901 overwrites its preview implementation at :858, so the Keep switch commits immediately. Fix that before extracting anything.

ONE component: **testCard** in **ui-testcard.js**, API testCard({id, media:{kind,src,alt}, caption, anchor, loading, busy, applyAct, cancelAct}) -> {update, close}. Existing ids and ACT names are adapters; engine requests stay in callers. Migration: (1) pin staged keep-size behavior and fix the overwrite; (2) introduce component and migrate vzCard; (3) migrate egCard, preserving egundo's preview-cancel versus stored-undo distinction. Check each: new ui_testcard.test.js (image/video, busy, empty/loading, placement, close), new size_preview.test.js (zero mutation before Apply; Cancel zero writes; stale reply ignored), anim_create.test.js; final theme.test.js plus inventory. Payoff high, risk medium; bounded extraction luna-6-high, the duplicate-definition fix 6.1-sol-medium with exact tests.

### D-02 / C-03 — Grouped sticker grids: confirmed presentation duplicate

Copies: library.js:361–372 (libByPackHtml, .lib-bypack/.lib-pk) and packs.js:7–39, :85–88 (pkGroups/pkGroupHead, .pk-bybatch/.pk-grp). Both group items, show title/count, render selectable cells and nested grids. Library groups by pack and preserves a global LCL carousel index across groups. Pack groups by generation, puts non-Studio items last, preserves original order, has draggable cells/cover/reaction badge and five hover actions. Selection state/handlers are already shared (library.js:48–85); do not reimplement them.

ONE component: **groupedGridHtml** in **ui-grouped-grid.js**, API groupedGridHtml({groups, rootAttrs, groupAttrs, headerHtml, cellHtml}) -> string. Callers keep grouping algorithms, item indices and all actions. Migration: Library then Pack, one consumer per task. Tests each: new grouped_grid.test.js with ordering, global index, escaped labels and selection attributes; packs_column.test.js for Library, pack_delete.test.js and manual_batch_action.test.js for Pack, inventory each. Payoff high, risk medium, luna-6-high; no generic reorder logic in the helper.

### D-03 / C-04 — Three reaction/particle screens: partial; reject three-screen consolidation

Copies of six parameter descriptors: effects.js:17–19 (FXSL/FXPRESETS), reactions.js:16–18 (RXPRESETS/RXSIM/RXO), with sliders at particles.js:365–366 and reactions.js:124–126. Five motion preset names overlap, but Reaction effects additionally offers spread/hue/size-in/out, versioned emoji presets and batch selection; the set editor targets pack-owned sprites with resolution/scale and Render/Add. Labels differ (Energy/Float/Spin versus Speed/Gravity/Rotation), and the JSON is different (params versus sim + extras).

Already shared: effects.js:13 fxNew, :16 fxX, :187–190 fxMotion delegate to particles.js:380 spBurstHtml; Studio, Library and Pack already reuse spSetCard/spBurstHtml (particles.js:173, :380; packs.js:274). The wizard has its own state SP registered in FXS at particles.js:11–13. Hover in Pack already calls rxFxOn/rxFxOff (packs.js:144–146). These are shared implementations, not three independent copies.

ONE new presentation component: **rangeFieldHtml** in **ui-range.js**, API rangeFieldHtml({label,min,max,step,value,attrs,formatValue}) -> string. Preserve every descriptor, default, touched-only parameter and namespace in caller adapters. Migration: spBSlider first, rxSlider second; then editor/prepare fields under D-12. Tests each: particle_editor.test.js + pack_studio.test.js, then reactions.test.js; add range_field.test.js for labels/ranges/attributes without choosing defaults. Inventory each. Payoff medium, risk medium, luna-6-high. Keep effects/SP common code and distinct backend contracts.

### D-04 / C-05 — Background watching: confirmed duplicated lifecycle, distinct streams

Copies: studio-core.js:913–973 tick (700 ms), live.js:168–195 liveTick + two 1 s queue redraws + 20 s provider status; :267 edge redraw (800 ms), :285 history (10 s); packs.js:76–79 colWatch; reactions.js:243–256 rxWatch; effects.js:64–65 fxPoll; particles.js:161–164 spSecSync and :268–274 spPoll; history.js:35 watch folders; chat-core.js:743–777 fallback polling, support.js:91–93 suWatch. Full timer inventory is in code_reader.md. Studio has no in-flight guard; its request sequence can outlast 700 ms. liveTick does have LTB guard. Signature checks limit some redraws but do not eliminate requests.

ONE component: **watchResource** in **ui-watch.js**, API watchResource({key,intervalMs,enabled,read,onValue,onError,isTerminal,signature,visibility}) -> {start,stop,refresh}; schedule next read only after previous read settles, with explicit exception recovery. Callers retain endpoint, terminal statuses, persistence, owner behavior and whether work continues off-screen. Existing SSE is specific: chat-core.js startStream at :685 and job-recovery.js:24 generation events. Do not assume collection/reaction APIs emit a universal stream.

Migration: (1) tick + race contract; (2) colWatch; (3) rxWatch; (4) fxPoll; (5) spPoll; (6) liveTick; (7) history/provider status; (8) UI-only queue clock coalescing as separate task. Do not move debounce/seek/object-URL timers into polling. Tests each: new ui_watch.test.js (no overlap, terminal, error recovery, stop, visibility, manual force), existing prompt_tab/anim_create, pack_delete, reactions, effects_core, particle_editor, job_recovery, history_card respectively, plus inventory. Payoff very high, risk high; design/helper luna-6-high, individually specified timer migrations 6.1-sol-medium only when two files/150 lines fit.

### D-05 / C-06 — Dialogs and more menus: partial

Common dialog foundation already exists: app.js:109 dlg, :114 closeDlg, :127 askText, :158 confirmDlg, :172 pickPack. They are wrappers, not five competing implementations. Repeated frame/footer markup is confirmed in those callers plus packs.js:47 retimeAsk, :60 colopen, telegram.js:22 tgFlow, and many dlg(...) bodies. More menus repeat details/summary/.gh-pop in packs.js:24, studio-core.js:619, reactions.js:144 and projmap.js:19; app.js:360–364 supplies shared outside/pick closing. Content and action semantics differ.

ONE dialog component: **dialogFrameHtml** in **ui-dialog.js**, API dialogFrameHtml({title,bodyHtml,footerHtml,labelId}) -> string; keep dlg/closeDlg as compatibility entrypoints and add explicit focus/return-focus lifecycle there. ONE menu component for the separate repeated feature: **moreMenuHtml** in **ui-menu.js**, API moreMenuHtml({label,itemsHtml,className}) -> string. No automatic mutation or backend choice.

Migrate askText then confirmDlg then pickPack then retimeAsk then collection/Telegram, each separately; migrate pack menu then Studio then reaction presets then map. Tests: new dialog_frame.test.js for Escape/outside/focus and canceled Promise settlement; existing pack_delete, reactions, project_map, avatar, theme; inventory each. Retime currently stores RTA and generic closeDlg does not settle it (packs.js:46–53): pin/repair cancellation before normalizing. Payoff high, risk medium, luna-6-high.

### D-06 / C-07 — Segmented controls: confirmed

Copies: composer.js:99 Creative/Predefined, studio-core.js:613 What to show, packs.js:31 Stickers/Reactions, reactions.js:99 All/Done/Not done, settings.js:19 section navigation. Shared .gseg CSS already exists at studio.css:988–990. Semantics disagree: packs.js uses role=tab with aria-pressed; actual tabs should expose selection; settings is navigation, not a binary toggle.

ONE component: **segmentedHtml** in **ui-segment.js**, API segmentedHtml({label,mode:'choice'|'tabs'|'navigation',items:[{label,value,act,attrs}],selected}) -> string. Migration: reactions (choice), composer (choice), Studio view (choice), Pack (tabs), settings (navigation). Retain all data-act/data-* values; no preference/engine decisions. Tests each: reactions, prompt_step, studio_menu, pack_delete, theme respectively; new segmented.test.js asserts each semantic mode. Inventory each. Payoff high/reach broad, risk medium; helper/semantic decision luna-6-high, later one-consumer replacements 6.1-sol-medium.

### D-07 / C-08 — Download helpers: confirmed

Copies: animate.js:68 and prepare.js:198 are almost identical response-blob/object-URL/anchor/revoke-after-4-s sequences. editor.js:224 downloads a data URL; particles.js:429 and reactions.js:317–321, :346 download server URLs. telegram.js:10 launches tg:// via an anchor, which is not a download.

ONE component: **downloadFile** in **ui-download.js**, API downloadFile({url,blob,filename,revokeAfterMs=4000}) -> void; exactly one of url/blob; revoke only helper-owned object URLs. Migration: animate then prepare then editor then particles then reactions, one per task. Keep filename sanitization in each caller first; no backend request changes. Tests: new ui_download.test.js (append/click/remove, revoke ownership/timing), relevant anim/timeline acceptance for animate/prepare (no focused blob-download test currently), particle_editor then reactions; inventory each. Payoff medium, risk low; helper luna-6-high, migrations 6.1-sol-medium. Do not alter Telegram launch or location.href ZIP behavior.

### D-08 / C-09 — Preview endpoints/caches: partial; reject collapsing endpoints

edge_preview (live.js:244–245) produces a still edge image, sheet_preview (live.js:109) a composed sheet, anim_preview (studio-core.js:838) a re-cut animation, emoji-preview (reactions.js:210, :217, :238) a generated reaction preview; particles/{id}/preview (particles.js:399) previews a saved set. Those operations are not duplicates. Repeated request/cache/debounce/stale-result machinery is real: VZ.n at studio-core.js:834–841, RXS.pv/ppv at reactions.js:32 and :206–239, SPB busy/again/signature at particles.js:395–406. RXS caches have no eviction or byte cap.

ONE component: **previewSession** in **ui-preview.js**, API previewSession({keyFor,request,commit,maxEntries=64,debounceMs}) -> {schedule,refresh,clear,dispose}; generation counter and bounded response metadata cache. Endpoint-specific request bodies and displayed image/video types stay outside it. Migration: VZ first, emoji editor/hover second, preset cards third, saved-set burst fourth; edge/sheet only when changing their request lifecycle is useful. Tests each: new preview_session.test.js (latest wins, pending update, error recovery, bounded eviction), new size_preview, reactions, then pack_studio/particle_editor; inventory each. Payoff high, risk high, luna-6-high; keep the existing SPB touched-only/again behavior pinned.

### D-09 / C-10 — Toasts, inline warnings, notifications: partial; retain their roles

app.js:24 toast is transient feedback; app.js:32 say writes an inline message; packs.js:70–78 has inline collection validation plus background result toast; support.js:70–71 reads persistent notifications; particles.js:367–373 draws durable preview blocks/warnings. Different lifetimes and audiences are intentional. Duplicate severity/markup/copy styling merits normalization, not merging all feedback into a toast.

ONE presentation component: **statusMessageHtml** in **ui-feedback.js**, API statusMessageHtml({kind:'info'|'warning'|'error'|'success',text,actionsHtml,live:'off'|'polite'|'assertive'}) -> string. Existing toast and notification transport stay; component controls only inline frame/tokens and accessible announcements. Migration: collection result then particle burst warnings then Studio inline message, one at a time. Tests: pack_delete (header/actions) plus new feedback_message.test.js; pack_studio; allow_tiles (never hide blocking reason); inventory each. Payoff medium, risk medium, luna-6-high.

### D-10 / C-11 — Long one-line functions: confirmed smell, not a UI component

38 JS files contain 264 physical lines over 300 characters. Confirmed suspects: packs.js 22/max827, particles.js 28/max834, live.js 17/max747, reactions.js 2/max357. Reaction code is much less compressed than the lead suggested; prepare.js (25/max573) and editor.js (18/max523) matter more. CSS has another 60 long lines. ONE repository formatting configuration (existing tooling first; otherwise formatter config plus scoped file list), not a pretend shared UI component. Reflow one file per task and do not change emitted whitespace in template strings, ACT names or payloads. Before/after render/output snapshots must prove strings identical. Tests: narrow existing test for that file (pack_delete, particle_editor, reactions, prompt_tab) and inventory. Payoff medium, risk low only outside templates; 6.1-sol-medium. A whole 71 KB particles.js reformat violates the 150-changed-line mechanical-task cap: use bounded function regions and parent formatting task dependencies.

## Additional confirmed duplication

### D-11 / C-12 — Trash purge waiting duplicated at three sites

live.js:348–350 remPurge and :353–355 remRemove each poll trash/purges every 500 ms up to 240 times; trash.js:48 trxWait polls the same resource every 1200 ms with no loop cap. Different timeout behavior is significant. ONE component: **awaitTerminal** exported by **ui-watch.js**, API awaitTerminal({read,isTerminal,intervalMs,timeoutMs,onProgress}) -> Promise<{state,value}>. Keep each policy explicit. Migration: remPurge, remRemove, trxWait. Tests each: remove_batch.test.js, remove_batch.test.js, trash.test.js plus ui_watch terminal/timeout cases; inventory. Payoff medium, risk medium, luna-6-high for policies; literal migrations sol when bounded.

### D-12 / C-04 — Range-field markup beyond reactions

editor.js:119 sl produces range + number fields; prepare.js:109 defines fld/rng and :110–114 builds separate layer/inspector fields; live.js:220 edgeControlsHtml builds range/output fields. Share **rangeFieldHtml / ui-range.js** from D-03, with pairedInput:'number'|'output' and caller-provided attributes. These are different rendering modes, not permission to change bounds or rounding. Migration after D-03: edge then editor then prepare, one consumer per task. Tests: new range_field tests for paired input and data namespaces; existing ai_editor/particle_editor where relevant, plus narrowly added editor value-propagation and prepare project-payload checks (current tests do not pin every field); inventory. Payoff medium, risk medium, luna-6-high helper, sol adapters only with exact specifications.

### D-13 / C-13 — Rejected picture status/action presentation

studio-tiles.js:136 blockedBox/:144 blockedAnimOverlay and chat-cards.js:196 tileHTML (allow markup :211 onward) repeat reason + allow/take-back presentation. Sheet controls already use shared cellOp/cellAct (studio-tiles.js:89/:133), and whole-sheet recovery is already centralized in sheet-recovery.js; preserve both. Chat operates on an API-provided allow object rather than Studio's loaded generation state. ONE component: **decisionStatusHtml** in **ui-decision.js**, API decisionStatusHtml({reason,eligible,allowed,actionAttrs,labels,context}) -> string, taking eligibility from existing adapters. Do not move eligibility decisions into browser logic. Migration: blockedBox then overlay then chat tile; picture remains adjacent and bulk controls remain. Tests each: allow_tiles, cell_op, then chat_allow; sheet_cells and sheet_recovery after shared dependency change, inventory. Payoff high, risk high (rule10), luna-6-high; lower priority than repairing existing behavior.

### D-14 / C-14 — Escaping copied into isolated helper bundles

app.js:6 esc; agent.js:6 AIU.esc; auth.js:8 AUV.esc; support.js:8 SUV.esc; further pure bundles in tickets/trash/trending/users/welcome use equivalent replacements. These are deliberately self-contained for Node tests, so a common function must remain importable without a DOM. ONE utility: **escapeHtml** in **ui-html.js**, API escapeHtml(value) -> string; expose existing bundle .esc aliases unchanged. Migration: app then AIU then one bundle per task; load before app.js and require/import explicitly in Node fixtures. Tests: agent, auth, support, tickets, trash, imports_trending, users, welcome respectively; malicious payload fixtures and inventory. Payoff low relative to risk/security and fixture churn; luna-6-high. Defer until shared component files actually need it.

### D-15 / C-15 — Relative-time wording

live.js:273 ago and reactions.js:77 rxAgo both implement elapsed-time thresholds, but use different cutoffs/units. ONE utility: **relativeTime** in **ui-format.js**, API relativeTime(epochSeconds,{policy,now}) -> string; preserve each caller's existing threshold policy initially. Migration: ago then rxAgo; tests history_card and reactions plus new ui_format exact boundary tests; inventory. Payoff low, risk low, 6.1-sol-medium only after a literal policy spec; not a high-priority screen change.

## Rejected additional blanket merges

Model selection already shares cloud provider grouping and engine-row markup (tests/js/cloud_models.test.js, enhancer_engine.test.js); image/video provider cards at live.js:55 have different fields from chat-stage.js:45's LLM selection. Do not extract one mega model picker. media/coverMedia already serve Library and Pack (library.js:31/:36); generation-sheet cells and particle sprites have different source shapes and shouldn't be collapsed as a speculative duplicate. No action or parked/near-dead feature may be deleted by this review.

Current branch note (HEAD170f26e): rxPresetChips now owns loading; rxPresetMenu acts on the picked preset (Save as new, Update, Remove). Retain that arrangement during migration; do not recreate the older menu seen in stale served assets. Metrics above were refreshed for fetched app.js/home.js/reactions.js; other scanned files are unchanged.
