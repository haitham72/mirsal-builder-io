# Walked screen/state inventory

> **Concurrent implementation notice:** Evidence belongs to the audited snapshot, while another LLM advanced source during review. Reconcile current CLAUDE.md and [concurrent-work.md](concurrent-work.md) before treating a finding or task as current.

Reviewed 2026-10-14 at `170f26e36893a194248eaf5d88449ecba9e9bcd7`. All 11 requested journeys were walked on copied data at localhost:8795 with paid providers off. No source changes or paid/external acceptance. The review browser and its server were stopped; only verified scratch outcopy was deleted. Owner port 8770 was not used or stopped.

## Journey paths and click evidence

Counts below count explicit navigation/activation steps in the reconstructed path, not typing, hover, scrolling, setup or polling. They are path descriptions, not measured interaction telemetry; no extra-click penalty is inferred from them.

| Journey | Path / explicit steps | Verdict / stopping boundary |
|---|---|---|
| J1 | Create > Studio (2); request > Generate prompt (1 activation); existing ready batch > Animation > size control (3) | Draft and preview reviewed; Cancel; stopped before paid Create sheet/Generate video. |
| J2 | Create > Chat (2); type > submit request (1) | Free built-in plan and saved carousel; no price/job acceptance. Live cloud price not testable with providers off. |
| J3 | Library > pack > sticker (3); close > hover > Timeline (2 activations); viewer > Edit in Studio (2) | Native cover Timeline blocked by badge; another works. Edit reaches prepare project, not #/studio; no Save/Export. |
| J4 | Create > + New > Reaction effects (3); emoji > Presets > Animation presets (3); Select > first > Shift last (3) | Search/filter/sliders/preset and five-item batch state reviewed; no batch/all/create. |
| J5 | Library > pack > Reactions (3); expand set > Motion (2); standalone #/effects comparison | Distinct workflows share presentation pieces; no Render. |
| J6 | Studio earlier-batch selection > decision picture (2) | G001 blocked animations and G012 human-dropped still; no override submitted. G012 detail used existing read-only pmopen fixture. Saved chat parity unverified. |
| J7 | Logo (1); welcome feature slide (1) > close (1) | Settled theme pair shows dark welcome contrast drift; wlClose corrects CSS-only harness dismissal. |
| J8 | Settings (1) > theme/Trash > scroll Tickets; Help > Queue/FAQ; public catalog | Account no-op, tiny Trash targets, Tickets shortcut absent, keyboard Help issue. No support write. |
| J9 | Pack > ZIP/collection/Telegram entry (1 each) > Cancel (1 each) | Retime and export fields reviewed; no download/export/transfer completion. |
| J10 | Theme toggle (1 per paired state); repeat Studio, pack, reaction editor, settings/trash, welcome and decision overview | Five priority theme pairs plus pack/phone editor comparisons; Studio theme captures J10-09/10 have different media tabs and are context comparisons. |
| J11 | 390×844 Library > drawer/pack > viewer; reaction wall > editor | No page horizontal scroll; local tab overflow and viewer metadata collapse; dark/light editor. |

**Skipped:** Users requires LAN mode, absent here. Spending is explicitly tracked unbuilt backend-first work; no imaginary broken route. Real cloud prices, support submission, export completion and cross-person privacy were not exercised.

## Every recorded state

M is the diagnostic subtotal from findings.md before manual interaction/promise/primary adjustments. It is not the finding impact. `controls` excludes discovery items in final probes. Older raw counts are preserved for traceability; superseded rows are not authoritative scores or image evidence. Styles count all mounted DOM, not only visible content. Every finding uses its stated settled/source evidence.

| Probe ID | Route / theme | Controls / tiny | M | Verdict | Kept image |
|---|---|---:|---:|---|---|
| J2-01 | `#/agent` / dark | 47 / 12 | 10 | Chat shell and saved-session list are dense; draft creation stays free. | [J2-01-chat-dark.jpg](shots/J2-01-chat-dark.jpg) |
| J2-02 | `#/agent` / dark | 47 / 12 | 10 | Superseded: Transient request state; discarded image, use J2-03 for the settled plan. | — |
| J1-01 | `#/studio` / dark | 44 / 12 | 8 | Empty Studio preserves the route and controls; advanced inspector competes with the request. | [J1-01-studio-dark.jpg](shots/J1-01-studio-dark.jpg) |
| J1-02 | `#/studio` / dark | 51 / 19 | 12 | Built-in prompt draft reached; stopped before Create sheet. | [J1-02-plan-dark.jpg](shots/J1-02-plan-dark.jpg) |
| J1-03 | `#/studio` / dark | 107 / 63 | 23 | Superseded: Early probe included hidden/clipped controls; superseded by J10-09/10. | [J1-03-batch-dark.jpg](shots/J1-03-batch-dark.jpg) |
| J1-04 | `#/studio` / dark | 109 / 65 | 23 | Video-size preview card opens and cancels; Keep handler overwrite is established from loaded/source code, without invoking its POST. | [J1-04-preview-dark.jpg](shots/J1-04-preview-dark.jpg) |
| J3-01b | `#/library` / dark | 22 / 2 | 3 | Library packs/recent view loads; no new functional failure. | — |
| J3-02 | `#/library` / dark | 20 / 1 | 3 | My Stickers grouped by pack repeats pack-grid markup and calls mixed media totals stickers. | [J3-02-grouped-dark.jpg](shots/J3-02-grouped-dark.jpg) |
| J3-03 | `#/pack/9ebb180c` / dark | 33 / 12 | 9 | Superseded: Pack header/grouped batches present; initial broad probe superseded by J3-03b. | [J3-03-pack-dark.jpg](shots/J3-03-pack-dark.jpg) |
| J3-03b | `#/pack/9ebb180c` / dark | 23 / 4 | 3 | Settled pack keeps header actions and both tabs. | — |
| J3-04 | `#/pack/9ebb180c` / dark | 39 / 11 | 9 | Viewer opens; compact navigation/background/close targets need larger hit areas. | [J3-04-viewer-dark.jpg](shots/J3-04-viewer-dark.jpg) |
| J9-01 | `#/pack/9ebb180c` / dark | 26 / 4 | 5 | Retime dialog opened/cancelled; source shows backdrop can leave the awaiting promise unresolved. | [J9-01-retime-dark.jpg](shots/J9-01-retime-dark.jpg) |
| J9-02 | `#/pack/9ebb180c` / dark | 25 / 4 | 5 | Collection fields and Full/Light choices visible; cancelled without Send. | [J9-02-collection-dark.jpg](shots/J9-02-collection-dark.jpg) |
| J9-03 | `#/pack/9ebb180c` / dark | 23 / 4 | 3 | Telegram entry opens retime ask in this fixture; cancelled without transfer. | [J9-03-telegram-dark.jpg](shots/J9-03-telegram-dark.jpg) |
| J3-05a | `#/pack/9ebb180c` / dark | 28 / 9 | 7 | Cover badge intercepts native Timeline click; no forced click used as acceptance. | [J3-05-cover-hover-dark.jpg](shots/J3-05-cover-hover-dark.jpg) |
| J3-05 | `#/animate/9ebb180c/fc6b6fcf` / dark | 19 / 1 | 1 | Another sticker reaches animation Timeline normally; route is working. | [J3-05-timeline-dark.jpg](shots/J3-05-timeline-dark.jpg) |
| J4-01 | `#/reactions` / dark | 372 / 10 | 75 | Superseded: Stale pre-reload wall capture discarded; broad item count is not controls overload. | — |
| J9-03b | `#/pack/9ebb180c` / dark | 26 / 4 | 5 | Repeat Telegram retime ask confirms cancellation boundary; no acceptance. | [J9-03-telegram-dark.jpg](shots/J9-03-telegram-dark.jpg) |
| J4-01b | `#/reactions` / dark | 23 / 12 | 5 | Current wall separates discovery items from controls; search/filter route works. | — |
| J4-02 | `#/reactions` / dark | 20 / 10 | 5 | Emoji preview editor opens; Close and Reset have small hit areas. | [J4-02-editor-dark.jpg](shots/J4-02-editor-dark.jpg) |
| J4-03 | `#/reactions` / dark | 28 / 8 | 7 | Superseded: Stale preset menu capture discarded; use J4-03c. | — |
| J4-04 | `#/reactions` / dark | 23 / 12 | 5 | Superseded: Earlier selection state superseded by current J4-04c. | [J4-04-batch-dark.jpg](shots/J4-04-batch-dark.jpg) |
| J4-05 | `#/reactions` / dark | 24 / 12 | 5 | Search/filter interaction stays local; no batch job created. | — |
| J4-06 | `#/reactions` / dark | 24 / 12 | 5 | Animation preset navigation observed; no render submitted. | — |
| J4-07 | `#/reactions` / dark | 26 / 13 | 7 | Preset and preview controls remain available; no creation acceptance. | — |
| J10-01 | `#/reactions` / light | 26 / 13 | 9 | Superseded: Light editor probe before current paired calibration; use J4-02c/J10-03. | [J4-02-editor-light.jpg](shots/J4-02-editor-light.jpg) |
| J4-06b | `#/reactions` / light | 26 / 13 | 7 | Current preset menu exposes update/remove operations; none submitted. | — |
| J10-02 | `#/pack/9ebb180c` / light | 23 / 4 | 3 | Light pack comparison retains header/actions and grouped information. | [J3-03-pack-light.jpg](shots/J3-03-pack-light.jpg) |
| J5-01 | `#/pack/9ebb180c` / light | 30 / 9 | 9 | Pack Reactions tab loads distinct pack workflow; do not merge its engine contract with emoji wall. | [J5-01-pack-reactions-light.jpg](shots/J5-01-pack-reactions-light.jpg) |
| J5-04 | `#/effects` / light | 27 / 1 | 2 | Standalone effects route opens sticker chooser/galleries; large fixed galleries are a layout issue, not a missing route. | [J5-04-effects-light.jpg](shots/J5-04-effects-light.jpg) |
| J4-01c | `#/reactions` / light | 27 / 13 | 6 | Current light wall has search, Done/Not done and load-more discovery. | [J4-01-wall-light.jpg](shots/J4-01-wall-light.jpg) |
| J4-02c | `#/reactions` / light | 26 / 14 | 6 | Current light emoji editor works; sliders and advanced layout need grouping. | [J4-02-editor-light.jpg](shots/J4-02-editor-light.jpg) |
| J4-03c | `#/reactions` / light | 27 / 14 | 7 | Current Animation presets menu shows saved preset operations. | [J4-03-presets-light.jpg](shots/J4-03-presets-light.jpg) |
| J10-03 | `#/reactions` / dark | 26 / 14 | 9 | Current dark emoji editor paired with J4-02c; tiny targets persist across theme. | [J4-02-editor-dark.jpg](shots/J4-02-editor-dark.jpg) |
| J5-02 | `#/pack/9ebb180c` / light | 30 / 9 | 8 | Expanded P010 set card exposes raw unlink IDs and competing controls. | [J5-02-set-card-light.jpg](shots/J5-02-set-card-light.jpg) |
| J6-01 | `#/studio` / dark | 60 / 31 | 13 | Superseded: Earlier blocked-animation probe superseded by J6-01b. | [J6-01-blocked-animation-dark.jpg](shots/J6-01-blocked-animation-dark.jpg) |
| J11-01 | `#/library` / dark | 14 / 2 | 0 | Phone Library tabs exceed their local row; page has no horizontal scroll. | [J11-01-library-dark.jpg](shots/J11-01-library-dark.jpg) |
| J5-03 | `#/pack/9ebb180c` / light | 32 / 12 | 6 | Pack motion panel repeats range controls and advanced sections; Render not pressed. | [J5-03-motion-light.jpg](shots/J5-03-motion-light.jpg) |
| J7-03 | `#/settings` / dark | 43 / 24 | 11 | Settled dark welcome slide uses pale ink over pale artwork. | [J7-03-welcome-settled-dark.jpg](shots/J7-03-welcome-settled-dark.jpg) |
| J10-04 | `#/settings` / light | 43 / 24 | 11 | Settled light welcome comparison remains readable; dark-specific contrast drift confirmed visually. | [J7-03-welcome-settled-light.jpg](shots/J7-03-welcome-settled-light.jpg) |
| J6-02 | `#/studio` / light | 40 / 7 | 9 | Superseded: Still detail transition; use J6-02b/c settled overview/detail. | [J6-02-rejected-still-light.jpg](shots/J6-02-rejected-still-light.jpg) |
| J6-02b | `#/studio` / light | 64 / 31 | 13 | Human-rejected G012S5 retains picture, drop reason and Bring back. | [J6-02-rejected-still-light.jpg](shots/J6-02-rejected-still-light.jpg) |
| J10-05 | `#/studio` / dark | 64 / 31 | 13 | Dark rejected-still overview retains decision controls; many tiny targets. | [J6-02-rejected-still-dark.jpg](shots/J6-02-rejected-still-dark.jpg) |
| J2-03 | `#/agent/S018` / dark | 35 / 3 | 7 | Nine-falcon request yields free four-step draft; Create it/Allow vision left untouched. | [J2-03-plan-dark.jpg](shots/J2-03-plan-dark.jpg) |
| J6-03 | `#/agent/S010` / dark | 36 / 4 | 7 | Superseded: Saved chat loading state; superseded by J6-03b. | — |
| J6-03b | `#/agent/S010` / dark | 43 / 9 | 9 | Saved S010 card inspected; rejected G012 picture not present, so chat override parity remains unverified. | [J6-03-chat-review-dark.jpg](shots/J6-03-chat-review-dark.jpg) |
| J10-06 | `#/studio` / light | 66 / 35 | 15 | Superseded: Earlier settled batch diagnostic: 66 controls/35 tiny; retained as density example, screenshot replaced by final J10-09/10 context captures. | [J1-03-batch-light.jpg](shots/J1-03-batch-light.jpg) |
| J10-07 | `#/settings` / light | 22 / 9 | 7 | Light Settings top shows local Account shortcut with no target. | [J8-01-settings-light.jpg](shots/J8-01-settings-light.jpg) |
| J10-08 | `#/settings` / light | 22 / 9 | 7 | Superseded: Trash transition; superseded by J10-08b. | [J8-02-trash-light.jpg](shots/J8-02-trash-light.jpg) |
| J10-08b | `#/settings` / light | 37 / 28 | 7 | Settled light Trash: 37 controls/28 tiny; restore/delete operations not submitted. | [J8-02-trash-light.jpg](shots/J8-02-trash-light.jpg) |
| J6-01b | `#/studio` / dark | 67 / 37 | 15 | G001 blocked animations S2/S9 show picture, reason and Use it anyway; allowed S1/S7 lose visible boundary reason. | [J6-01-blocked-animation-dark.jpg](shots/J6-01-blocked-animation-dark.jpg) |
| J4-04c | `#/reactions` / dark | 30 / 15 | 7 | Current Select plus Shift-click selects five emoji; batch controls too compact, no job pressed. | [J4-04-batch-dark.jpg](shots/J4-04-batch-dark.jpg) |
| J6-02c | `#/studio` / dark | 41 / 19 | 9 | Settled human-rejected still detail distinguishes Bring back from Python override. | [J6-02-rejected-still-detail-dark.jpg](shots/J6-02-rejected-still-detail-dark.jpg) |
| J11-02 | `#/library` / dark | 14 / 2 | 0 | Phone Library drawer can open/close; no page horizontal scroll. | — |
| J11-03 | `#/pack/9ebb180c` / dark | 16 / 4 | 0 | Phone pack preserves tabs/actions with reduced density. | [J11-03-pack-dark.jpg](shots/J11-03-pack-dark.jpg) |
| J11-04 | `#/pack/9ebb180c` / dark | 21 / 9 | 2 | Superseded: Transitional phone viewer capture replaced by settled J11-04b. | [J11-04-viewer-dark.jpg](shots/J11-04-viewer-dark.jpg) |
| J11-05 | `#/reactions` / dark | 17 / 8 | 4 | Phone reaction wall fits page width; discovery remains available. | [J11-05-wall-dark.jpg](shots/J11-05-wall-dark.jpg) |
| J11-06 | `#/reactions` / dark | 18 / 5 | 2 | Phone dark editor fits page but Close remains too narrow. | [J11-06-editor-dark.jpg](shots/J11-06-editor-dark.jpg) |
| J11-07 | `#/reactions` / light | 18 / 5 | 5 | Phone light editor matches dark behavior; advanced layout remains dense. | [J11-06-editor-light.jpg](shots/J11-06-editor-light.jpg) |
| J11-04b | `#/pack/9ebb180c` / dark | 29 / 8 | 6 | Settled phone viewer squeezes metadata into a word column despite zero page overflow. | [J11-04-viewer-dark.jpg](shots/J11-04-viewer-dark.jpg) |
| J8-settings-appearance | `#/settings` / dark | 22 / 9 | 5 | Appearance theme choices work; local Account shortcut is a no-op. | — |
| J8-settings-trash | `#/settings` / dark | 37 / 28 | 7 | Trash presents many compact restoration/deletion controls. | — |
| J8-settings-tickets | `#/settings` / dark | 37 / 28 | 7 | Tickets are below Trash without a section shortcut; not a missing route. | — |
| J8-help-new | `#/help` / dark | 14 / 1 | 1 | Help issue rows are click-only divs; no support submission. | — |
| J8-help-queue | `#/help/queue` / dark | 11 / 0 | 1 | Support queue opens; empty/browsing state needs no forced primary action. | — |
| J8-help-faq | `#/help/faq` / dark | 12 / 1 | 1 | FAQ rows are clickable but lack native keyboard semantics. | — |
| J8-trending | `#/library` / dark | 31 / 4 | 5 | Public catalog shows mixed reaction/sticker totals; content route is Library. | — |
| J7-home | `#/home` / dark | 27 / 3 | 7 | Home loads; Reaction effects label points to a different workflow than + New. | — |
| J7-welcome-slide | `#/home` / dark | 45 / 6 | 11 | Superseded: Initial slide observation superseded by settled J7-03/J10-04 theme pair. | — |
| J8-tickets-bottom | `#/settings` / dark | 33 / 18 | 5 | Scrolled Tickets area is present and reachable, with no direct section shortcut. | — |
| J10-09 | `#/studio` / dark | 57 / 28 | 13 | Final dark Studio probe: 57 controls/28 tiny; capture shows Raw/Both context, so it is not a matched media-tab contrast test. | [J1-03-batch-dark.jpg](shots/J1-03-batch-dark.jpg) |
| J10-10 | `#/studio` / light | 57 / 28 | 13 | Final light Studio probe: 57 controls/28 tiny; capture shows Video/Both context, different from dark. Async redraw makes the exact screenshot/probe pairing unsuitable for contrast certification. | [J1-03-batch-light.jpg](shots/J1-03-batch-light.jpg) |
| J3-06 | `#/prepare/679a843f70` / light | 21 / 1 | 1 | Edit in Studio opens existing #/prepare project with 66 frames at 24 fps; no Save/Export, no broken route. | [J3-06-edit-project-light.jpg](shots/J3-06-edit-project-light.jpg) |

## Contact sheets

One derived sheet per journey; J10 compares existing paired screenshots and adds no new capture. [J1](shots/contact-J1.jpg) · [J2](shots/contact-J2.jpg) · [J3](shots/contact-J3.jpg) · [J4](shots/contact-J4.jpg) · [J5](shots/contact-J5.jpg) · [J6](shots/contact-J6.jpg) · [J7](shots/contact-J7.jpg) · [J8](shots/contact-J8.jpg) · [J9](shots/contact-J9.jpg) · [J10](shots/contact-J10.jpg) · [J11](shots/contact-J11.jpg).

The retained-image manifest is authoritative: 48 source screenshots + 11 contact sheets = 59 images, within 60. Five discarded/transitional captures remain outside the repo.
