# ZIP, collection and Telegram dialogs — issues and proposed fixes

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

## F-06 — Backdrop hides retime without settling its promise

**Implemented 2026-10-14 (branch `uiux-fixes`, T-002):** `dlg(html,{onDismiss})` + `closeDlg(reason)` carry one active dismissal callback; `retimeAsk` settles exactly once (answer true/false, backdrop/Cancel/replacement null); `ACT.rtans` forgets the dismissal before closing. No Escape handling added. Test `mirsal/tests/js/dialog_cancel.test.js` (4 pass, behavioral).

### Issue

packs.js:47–53 retimeAsk/RTA; app.js:114–121 closeDlg/backdrop. Actual backdrop click leaves typeof RTA==function; explicit Cancel clears it. Applies to ZIP and Telegram retime callers.

**Confidence:** browser confirmed broken. **Impact / reach / risk:** 8 / 3 / 1. **Priority:** 24.0.

### Proposed fix

Every dismissal/replacement settles null once; keep explicit answers true/false and all request payloads.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-06--backdrop-hides-retime-without-settling-its-promise). [J9-01-retime-dark.jpg](../../shots/J9-01-retime-dark.jpg) · [J9-03-telegram-dark.jpg](../../shots/J9-03-telegram-dark.jpg)

### Bounded implementation work

- [T-002](../../../uiux_plan.md) — Settle retime on every dialog cancellation (luna-6-high); mirsal/mirsal/console/app.js, mirsal/mirsal/console/packs.js, mirsal/tests/js/dialog_cancel.test.js.
  Extend dlg(html,{onDismiss}={}) and closeDlg(reason='dismiss') with one active dismissal callback cleared before invocation. retimeAsk registers a callback that captures its own resolver and resolves null exactly once; ACT.rtans clears RTA/callback before closing and returns only true/false/null. Opening a replacement dialog cancels the prior request. Preserve dlg(html) callers; backdrop and ACT.dlgx use the same close path. Do not add Escape handling until dialog lifecycle task.
- [T-037](../../../uiux_plan.md) — Introduce dialog frame and focus lifecycle (luna-6-high); mirsal/mirsal/console/ui-dialog.js, mirsal/mirsal/console/app.js, mirsal/mirsal/console/index.html, mirsal/tests/js/dialog_frame.test.js, mirsal/tests/js/console_vm.js.
  Implement dialogFrameHtml({title,bodyHtml,footerHtml,labelId}) -> string using shared escaped title/body/footer slots. Keep dlg(html,{onDismiss})/closeDlg adapters; add role=dialog/aria-modal/title association on dbox, save initiating focus, focus first input/button and trap Tab within active box; Escape/outside/ACT.dlgx settle dismissal once and return focus when initiating element still exists. Preserve ASK/PK callbacks and explicit rtans response. Include once after app.js; no endpoint changes. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
- [T-038](../../../uiux_plan.md) — Migrate text prompt dialog frame (6.1-sol-medium); mirsal/mirsal/console/app.js, mirsal/tests/js/dialog_frame.test.js.
  Use dialogFrameHtml only inside askText, preserving #askv/title/value, Cancel data-act=dlgx, Save askok, selection/focus and Enter behavior. Keep ASK result callback and ignored empty text exactly. Do not migrate confirmDlg/pickPack here.
- [T-039](../../../uiux_plan.md) — Migrate confirmation dialog frame (6.1-sol-medium); mirsal/mirsal/console/app.js, mirsal/tests/js/dialog_frame.test.js.
  Use dialogFrameHtml only in confirmDlg; title stays escaped exactly once, Cancel data-act=dlgx and confirm data-act=cfok with original ok label. Preserve ASK callback/owner callers and no invocation on outside/Escape. Extend exact malicious-text/callback fixtures.
- [T-040](../../../uiux_plan.md) — Migrate pack-picker dialog frame (6.1-sol-medium); mirsal/mirsal/console/app.js, mirsal/tests/js/dialog_frame.test.js.
  Use dialogFrameHtml only in pickPack. Preserve await loadLib, PK callback, pl rows, coverMedia, data-act=pk/data-id, #npn, pknew Create and Cancel. Keep original pack ordering and new-pack POST body outside presenter. Preserve empty sentence and string ids.
- [T-041](../../../uiux_plan.md) — Migrate retime dialog frame (6.1-sol-medium); mirsal/mirsal/console/packs.js, mirsal/tests/js/dialog_cancel.test.js.
  Use dialogFrameHtml only in retimeAsk; keep one Promise/result true|false|null,3 actions/data-v x|0|1 and explanatory sentences. Preserve12-item short-list cap, Telegram-only warning and default choice. Do not change backend retime flags or downloaded file URL. Cancellation tests cover replacement/backdrop/Escape/button.
- [T-042](../../../uiux_plan.md) — Migrate collection dialog frame (6.1-sol-medium); mirsal/mirsal/console/packs.js, mirsal/tests/js/collection_dialog.test.js.
  Use dialogFrameHtml only in ACT.colopen. Preserve #col-name maxlength40; #col-desc maxlength160 and required; optional #col-retime values1|0; #col-light Full0 selected/Light1; #col-res; Close data-act=dlgx and colsend kind/id/config-disabled. Preserve owner gate, configured notice and read-only status/short reads. No Send in test/browser acceptance.
- [T-043](../../../uiux_plan.md) — Migrate Telegram connection/status frames (luna-6-high); mirsal/mirsal/console/telegram.js, mirsal/tests/js/telegram_dialog.test.js.
  Migrate only tgFlow's final send/confirmation dlg to dialogFrameHtml, retaining every existing branch/form field/action, owner restriction and short-animation retime handling. Do not change tgConnectForm/tgSettingsCard/tgDone or launch tg://. Test local fixtures for configured/unconfigured/status/error flows; assert no external send on open/cancel.
- [T-044](../../../uiux_plan.md) — Introduce details-menu presenter (luna-6-high); mirsal/mirsal/console/ui-menu.js, mirsal/mirsal/console/index.html, mirsal/tests/js/more_menu.test.js, mirsal/tests/js/console_vm.js.
  Implement moreMenuHtml({label,itemsHtml,className,summaryAttrs,popClass,summaryHtml}) -> string. Emit details + summary + role=menu popover, exact caller classes and trusted prebuilt items; escape label attrs. Support gh-more/gh-pop and pm-menu existing wrapper variants; keep native details behavior and app.js outside/pick closing. Include once after app.js; test classes/menu labels and unchanged action markup. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
- [T-045](../../../uiux_plan.md) — Migrate Pack more menu (6.1-sol-medium); mirsal/mirsal/console/packs.js, mirsal/tests/js/pack_delete.test.js.
  Replace only drawPack's gh-more menu wrapper with moreMenuHtml; reuse identical items string in same order Rename/Public/Collection/Preview/full ZIP/chat/add/delete. Preserve conditional owner/export and disabled flags, summary btn class/title and label More for this pack. No menu action disappears.
- [T-046](../../../uiux_plan.md) — Migrate Studio toolbar more menu (6.1-sol-medium); mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_menu.test.js.
  Replace only gview gh-more toolbar wrapper; retain identical item expressions/order and summary btn sm/title More for this batch. Do not migrate project-map menus or any action body. Canonical emitted menu HTML is byte-identical except intentional accessibility label normalization from foundation.
- [T-047](../../../uiux_plan.md) — Migrate reaction preset menu (6.1-sol-medium); mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
  Replace only rxPresetMenu(k) details/summary/pop wrapper using gh-more rx-pmenu and gh-pop. Preserve current Save as new, picked-preset Update/Remove actions, empty sentence Pick a preset to update or remove it, data-id and rxpdel dng style. Keep rxPresetChips outside this menu unchanged: chips own loading and motion-first ordering. Never recreate the old Load/Remove submenu from stale assets.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-08 — Download lifecycle is copied

### Issue

animate.js:68, prepare.js:198 blob/object URL/anchor/revoke; editor.js:224 data URL; particles.js:429 and reactions.js:317–346 server URLs. Telegram tg:// is not a download.

**Confidence:** confirmed duplicate. **Impact / reach / risk:** 3 / 4 / 1. **Priority:** 12.0.

### Proposed fix

downloadFile owns only object URLs it creates; preserve filenames and each URL/body; migrate consumers separately.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-08--download-lifecycle-is-copied). Source/document evidence; no screenshot claimed.

### Bounded implementation work

- [T-026](../../../uiux_plan.md) — Introduce URL/blob download utility (luna-6-high); mirsal/mirsal/console/ui-download.js, mirsal/mirsal/console/index.html, mirsal/tests/js/ui_download.test.js, mirsal/tests/js/console_vm.js.
  Implement downloadFile({url,blob,filename,revokeAfterMs=4000}) with exactly one source. Append anchor, assign href/download, click, remove in finally; create object URL only for blob and revoke only helper-owned URL after specified delay. Existing URL/data-URL must never be revoked. No fetch or Telegram launch in helper. Include once after app.js; stub document/URL/timers. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
- [T-027](../../../uiux_plan.md) — Migrate Timeline blob download (6.1-sol-medium); mirsal/mirsal/console/animate.js, mirsal/tests/js/ui_download.test.js.
  Replace only anCall's response blob/createObjectURL/anchor/remove/revoke sequence with downloadFile({blob,filename: original sanitized A.st.name+'.'+A.fmt}). Preserve fetch/body, busy state, original4000ms cleanup timing and save branch. Extend fixture proving filename/source ownership and zero new network requests.
- [T-028](../../../uiux_plan.md) — Migrate video-editor blob download (6.1-sol-medium); mirsal/mirsal/console/prepare.js, mirsal/tests/js/ui_download.test.js.
  Replace only prCall's response-blob download sequence with downloadFile; preserve (e.name||P.p.name).replace(/[^\w-]+/g,'_')+'.'+e.format exactly, original4000ms cleanup, encoding request/body and save branches. No change to project persistence/timing/canvas.
- [T-029](../../../uiux_plan.md) — Migrate still-editor PNG download (6.1-sol-medium); mirsal/mirsal/console/editor.js, mirsal/tests/js/ui_download.test.js.
  Replace only ACT.xdl anchor construction with downloadFile({url:E.dataUrl,filename: original sanitized (E.name||'sticker')+'.png'}). Keep action name and data URL; do not fetch/revoke it. Pin fallback/special-character filenames.
- [T-030](../../../uiux_plan.md) — Migrate particle Lottie download (6.1-sol-medium); mirsal/mirsal/console/particles.js, mirsal/tests/js/particle_editor.test.js.
  Replace only ACT.psblottie success-path anchor download with downloadFile({url: original server URL,filename: original name}). Preserve original export-lottie POST, touched-only params/scale, busy button recovery and filename wording. Test fake response, never render or call a model.
- [T-031](../../../uiux_plan.md) — Migrate reaction ZIP and Lottie downloads (6.1-sol-medium); mirsal/mirsal/console/reactions.js, mirsal/tests/js/reactions.test.js.
  Replace only rxzip and rxdl anchor creation with downloadFile; preserve zip URL query for selected tokens, encoded join order, filename reactions.zip and individual token/id .lottie.json filename. Keep all download controls/data attributes, no fetch added. Test selected/full and individual versions.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.

## F-10 — Feedback markup repeats with different lifetimes

### Issue

app.js:24 toast; packs.js:60–74 persistent collection validation; particles.js spBurstHtml warning; notifications are durable outcomes.

**Confidence:** partial duplicate. **Impact / reach / risk:** 4 / 5 / 2. **Priority:** 10.0.

### Proposed fix

Share inline status markup only; retain toast, field errors and durable notifications as different channels.

### Evidence and scope

[Full finding and qualifications](../../findings.md#f-10--feedback-markup-repeats-with-different-lifetimes). [J9-02-collection-dark.jpg](../../shots/J9-02-collection-dark.jpg)

### Bounded implementation work

- [T-048](../../../uiux_plan.md) — Introduce durable inline status presenter (luna-6-high); mirsal/mirsal/console/ui-feedback.js, mirsal/mirsal/console/index.html, mirsal/tests/js/feedback_message.test.js, mirsal/tests/js/console_vm.js.
  Implement statusMessageHtml({kind,text,bodyHtml,actionsHtml,live='off',className}) -> string with exactly one of escaped text or explicitly trusted prebuilt bodyHtml, plus supplied trusted action markup. Use existing warn/mut/bad classes to preserve visuals; warning/error can use explicit role/status/live mode without altering persistence. Keep toast() transient and /api/notifications persistent; no new transport or eligibility logic. Include once after app.js. Update console_vm loadConsole to load this helper once before its actual consumer scripts in VM tests (deduplicate resolved filenames); standalone statement-extraction fixtures inject its export explicitly in their one consumer test. Preserve original console_source canonicalization and do not change grouping of unrelated files.
- [T-049](../../../uiux_plan.md) — Migrate collection inline validation (6.1-sol-medium); mirsal/mirsal/console/packs.js, mirsal/tests/js/collection_dialog.test.js.
  Use statusMessageHtml only for empty-description and failed-post #col-res warnings in ACT.colsend. Keep exact sentences, busy/reset behavior and original input/body fields; kind error, live polite. Preserve background terminal toast and notifications; no popup/toast substitute for validation.
- [T-050](../../../uiux_plan.md) — Migrate burst warning presentation (6.1-sol-medium); mirsal/mirsal/console/particles.js, mirsal/tests/js/pack_studio.test.js.
  Use statusMessageHtml for spBurstCard blocks/warnings only. Keep fxWords mapping, original block/warning order, file/no-file media, disabled/add eligibility, Use it anyway label and backend-written statuses. Preserve original fx-w/bad class variants through className adapter; no technical block becomes overridable.
- [T-051](../../../uiux_plan.md) — Migrate Studio inline stale/health warnings (6.1-sol-medium); mirsal/mirsal/console/studio-core.js, mirsal/tests/js/studio_poll.test.js.
  Use statusMessageHtml only in tick's #ghealth stale-server and no-VP9 notices, with exact existing trusted code fragments as caller body/action slots; use text escape for dynamic errors. Preserve condition/order, system-health diagnostics and current message refresh behavior. Do not convert rejected-picture warnings or generic say() here.

**Preserve:** routes, ACT names, UI baseline, existing JSON and engine authority; per-picture reason/override and owner-only send/export boundaries. No paid calls in acceptance.
