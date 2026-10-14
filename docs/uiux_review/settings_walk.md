# J8 Settings / Help / Trending; short J7 Home / welcome pass

2026-10-14, isolated http://127.0.0.1:8795, copied data, disabled paid/model providers; never :8770. Desktop 1440×900, DPR 0.5. Playwright skill followed using root's handed-over desktop session and approved runner. No submitted questions, likes, comments, settings mutations, recovery/restore/purge/send/export calls. Users skipped because non-LAN. Account and Spending absence checked without writes. Root has browser control again, at #/settings in dark mode, welcome closed.

## Measurements and scoring

Probe JSON lines: scratch/J8-probes.jsonl. “Visible” excludes offscreen elements and clipped descendants; primary count is visible enabled .btn.pri. Styles still count all mounted DOM, including inactive screens. Modal probe does not account for occlusion of the background, so welcome's button count is an upper bound. Rows with no required single primary (Settings and empty Queue/FAQ) are not penalized for zero primary.

Score = 2×floor(max(buttons−15,0)/10) +2 if tiny>5 +2 if font sizes>6 +2 if text colours>8 +1 if inline styles>20 +1 if depth>25 +4 if horizontal scrolling. Add +5 for confirmed broken keyboard/navigation behavior and +2 for violated doc promise in findings below. No +4 for intentional decorative hero overflow or translated carousel track; neither produced page horizontal scrolling.

| State | Buttons | Primary | Tiny | Fonts/colours | Inline | Metric score |
|---|---:|---:|---:|---:|---:|---:|
| J8-settings-appearance | 22 | 0 | 9 | 7/8 | 90 | 5 |
| J8-settings-trash | 37 | 0 | 28 | 6/5 | 94 | 7 |
| J8-settings-tickets | 37 | 0 | 28 | 6/5 | 94 | 7 |
| J8-help-new | 14 | 1 | 1 | 5/4 | 96 | 1 |
| J8-help-queue | 11 | 0 | 0 | 6/6 | 95 | 1 |
| J8-help-faq | 12 | 0 | 1 | 6/7 | 182 | 1 |
| J8-trending | 31 | 1 | 4 | 7/6 | 96 | 5 |
| J7-home | 27 | 2 | 3 | 8/15 | 97 | 7 |
| J7-welcome-slide | 45 | 1 | 6 | 4/9 | 99 | 11 |
| J8-tickets-bottom | 33 | 0 | 18 | 6/5 | 98 | 5 |

All states had no horizontal scroll, depth 8–13, and pageHeight900 (content scrolls inside app containers). The first “settings-tickets” attempt merely brought the heading edge into view and remained on Trash; its screenshot is an unselected duplicate. The final tickets-bottom state uses explicit scroll-to-heading and is the evidence. 10 probes retained; 8 screenshots captured, **7 selected**.

## Findings for merge

**J8-F01 — Settings section bar contains a dead Account shortcut (score10).** Settings top metric5 + broken5. In this non-LAN state #au-me count is0, but Account remains in the section bar. Handler checks for the absent element then does nothing. Code: mirsal/mirsal/console/settings.js:19 and :41; account card only mounts through auth wrapper at mirsal/mirsal/console/auth.js:82. Evidence: J8-01-settings-dark.jpg. Acceptance: section entries reflect actual rendered cards; in LAN preserve the Account action and card.

**J8-F02 — Tickets are below all Trash rows with no section shortcut (score7).** Tickets-bottom metric5 + shell navigation promise2. Appearance, Account, Health, Prepared sheets, AI, Telegram, Trash are in the sticky bar; Tickets is omitted despite the owner card and Support queue. Reaching Tickets is two avatar clicks plus scrolling past nine trash rows. Code: settings.js:19, tickets.js:50–:53; trash.js:67 appends preceding Trash. Evidence: J8-06-tickets-bottom-dark.jpg. Add a role-aware section entry rather than another route.

**J8-F03 — Dense, undersized Settings/Trash actions (score7).** Trash metric7. 37 viewport buttons, 28 below the probe's target threshold; dimensions round to28px while actual heights are just under28. Nine repetitive Restore/Delete for good pairs compete with Delete all. All deletion paths already confirm; no removal/recovery submitted here. Code: mirsal/mirsal/console/trash.js:17/:25/:56, mirsal/mirsal/console/studio.css:1058 (section bar). Evidence: J8-02-trash-dark.jpg. Preserve each action and confirmation; give target wrappers44px and group repeated item actions consistently.

**J8-F04 — Help lists use click-only div rows (score6).** FAQ metric1 + keyboard-broken5. Accessibility snapshot exposes 87 draft titles as text, not actionable buttons; rows have data-act but no role/tabindex/native button. Same builders cover My issues/Queue. Code: mirsal/mirsal/console/support.js:14 (conversation), :46 (queue), :55 (FAQ), :73–:79 (column). Evidence: J8-04-faq-dark.jpg. This is a structural accessibility finding supported by source and accessibility snapshot, not a simulated screen-reader test. Use native controls retaining suopen/suq/sufaq, current selection/scroll, and Enter/Space behavior. No draft published or issue replied to.

**J8-F05 — Trending sticker totals include added reactions (score9).** Trending metric7 + promise2. Angel Reading Newspaper card says10 stickers while its sidebar says9 stickers·1 reaction; Batman Lego card says19 while sidebar says17·2 reactions. This contradicts docs/reaction/12-11-added-bursts-are-reactions-not-stickers-2026.md:5 (“Library rows…skip” source.particle_set). Code display: mirsal/mirsal/console/trending.js:11, compared with mirsal/mirsal/console/app.js:430 and library.js:400, which explicitly exclude source.particle_set. Evidence: J8-05-trending-dark.jpg. Contract dependency: determine whether public pack summary needs an additive reaction count/API change; do not guess by subtracting metadata or change JSON silently. Like targets are24px high (same shot; studio.css:407).

**J7-F01 — Home remains visually coherent but has competing creation doors and type/colour density (metric7).** Two enabled primary buttons, 27 visible buttons, 8 font sizes/15 colours; three20px text links. Homepage creative art has intended decorative overflow; do not report it as horizontal-scroll failure. Evidence: J7-01-home-dark.jpg. Keep90% direction fits this page; align targets/type tokens and clarify one primary while preserving all shortcuts. Code: mirsal/mirsal/console/home.js:49/:51 (two primaries), :54/:55/:62 (small links), studio.css .hm-*; current Home contract docs/design/05-5-per-screen.md:7–:13. No claim about media quality.

**J7-F02 — Welcome navigation dots are18px targets; contrast candidate needs settled proof.** Welcome raw metric11 includes occluded background; rank actual target finding +2 and retained top J7 state, rather than treating45 buttons as modal choice overload. All five tabs are72×18; Skip about41×28. Code: mirsal/mirsal/console/welcome.js:42, studio.css:594. Evidence: J7-02-welcome-slide-dark.jpg, captured immediately after tab click during the .6s transition at studio.css:576. Do not treat its transitional layout as a bug. Title/body use --ink/#d9e9ef and --ink2/#9dc0cc in dark (theme.css:7; studio.css:583–:584) over unchanged light artwork; possible contrast defect, requires a settled dark slide check before a high-severity claim. Film opens; tab navigation and Skip work.

## Passing states and limits

- Help fresh question: one clear Ask, readable explanation/attachment hint, no overflow; no request submitted.
- Help Queue: one existing report, explicit “Pick an issue on the left”; not marked broken for no primary.
- FAQ review: pending drafts and publishing warning visible; no publication or edit submitted.
- Settings Appearance has Dark/Light pressed state. This pass did not toggle preference; root J10 handles theme persistence/light pair.
- Spending has no text/card/control (count0), matching existing open backend-first work at docs/backlog.md:151. Do not score absent unbuilt Spending as a broken screen.
- Ticket T004's existing ModuleNotFoundError and old job errors are copied data, not a new crash in this pass. CLI console12-error count was inherited from earlier browser work/server restart; no new error delta captured, so no generic +5 added.
- Source file:line references use current checkout. Server was restarted by root just before this pass; browser session was shared and not reloaded here. If source changed after root's initial page load, validate these affected builders against the final source snapshot.
- J7 short pass does not establish first-session autoplay, muted/unlock behavior, all film crops, filter/resize preservation or phone layout. No source edits/tests.

## Selected scratch screenshots

Base: C:/Users/H7068~1.IBR/AppData/Local/Temp/mirsal-uiux-JLvrj7/

1. J8-01-settings-dark.jpg — F01
2. J8-02-trash-dark.jpg — F03
3. J8-04-faq-dark.jpg — F04
4. J8-05-trending-dark.jpg — F05
5. J8-06-tickets-bottom-dark.jpg — F02
6. J7-01-home-dark.jpg — J7-F01
7. J7-02-welcome-slide-dark.jpg — J7-F02

All JPEG quality60 viewport-only, 720×450 output. Each inspected once. **Do not keep J8-03-tickets-dark.jpg**: duplicate Trash view. Files remain scratch for root's ranking/copy/contact-sheet merge; no commit/push.

Additional source leads for merge: Home summary totals at home.js:44 count all pack stickers, while showcase filtering excludes source.particle_set at :24; this may share Trending count debt. Home “Try reaction effects” button at home.js:55 routes to effects, whereas Create menu at app.js:295 routes Reaction effects to reactions. The link was observed in the snapshot but not clicked in this pass; verify route mismatch in browser before ranking it.
