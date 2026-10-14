# Console code review — Phase A2 (2026-10-14; refreshed against HEAD170f26e)

> **Concurrent implementation notice:** Evidence belongs to the audited snapshot, while another LLM advanced source during review. Reconcile current CLAUDE.md and [concurrent-work.md](concurrent-work.md) before treating a finding or task as current.

Paths are relative to mirsal/mirsal/console/ unless stated. Reviewed/scanned all 38 top-level JS files, the three CSS files, index.html and docs/ui_inventory.md; manually inspected implicated functions and narrow JS-test descriptions. No engine code read, no source edited, no providers called and no tests run: this is a docs-only review. Component contracts, per-copy differences, migration order and narrow checks are in duplication_map.md. Static findings use C-ids so the orchestrator can merge them with browser F-ids rather than count them twice.

## Highest-value evidence

**C-01 — Keep approved size bypasses its test card (broken documented behavior).** studio-core.js:858 defines staged VZ.keep + vzPreview; :901 defines ACT.gkeepsize again and immediately POSTs keep_size with reslice. The later assignment wins. keepSizeBtn at :767 still reads VZ's staged state, and the comment at :792 promises Apply/Cancel. Therefore the handler at :858 is dead at runtime and a Keep click mutates/reslices immediately. This is exact source evidence, not a guessed rendering issue. No existing JS test names gkeepsize/vzCard/vzPreview/egCard. A follow-up executor should pin zero writes until Apply, zero writes on Cancel and exactly the original JSON on Apply, then remove the late overwrite; no repair in this review.

**C-05 — Overlapping Studio polling and repeated queue replacement.** studio-core.js:973 schedules async tick every 700 ms; tick :913 has route/modal gating but no in-flight or document.hidden guard. Each active iteration requests the generations list and each selected generation sequentially (:916/:930), sometimes family/main generation too. With N selected generations, minimum steady-state reads are about(1+N)/0.7 per second before family calls, provided responses keep up; if responses are slow, interval callbacks overlap. liveTick has an LTB guard (:168), proving the app already has the appropriate pattern. live.js:185 and :191 both replace queue innerHTML via drawLive at1s while active; egSync/applyEdgePreview at :267 runs every 800 ms even off-route. These are scheduling/redraw defects, not evidence of measured server latency. Use one bounded watcher and a single text-only queue clock.

**C-06 — Closing retime outside its explicit buttons leaves an await pending.** packs.js:47 returns a Promise stored in RTA; only ACT.rtans at :53 settles it. app.js:119–121 backdrop closing and generic closeDlg at :114 only clear markup. The ZIP handlers at packs.js:56 and studio-core.js:894 await retimeAsk. Outside-dismissal leaves that flow unresolved. This does not prove the previously reported collection-export freeze: colWatch is a different workflow. Pin cancel settlement before dialog extraction.

**C-02/C-03/C-04/C-07 — Surface consistency has small, real shared components.** The test card is explicitly copied (studio-core.js:792), the Library/Pack grouped containers duplicate their CSS declarations (studio.css:781/:783), and six effect parameter descriptors/five presets overlap (effects.js:17–19/reactions.js:16–18). The existing .gseg style serves five different HTML builders; Pack uses role=tab with aria-pressed (packs.js:31), while choices/navigation have different semantics. Shared testCard, groupedGridHtml and segmentedHtml address the broad surface first; rangeFieldHtml follows. Do not merge three reaction screens: FX/SP already share effect state/handlers and spBurstHtml.

**C-19 — Token coverage is incomplete, though literal counts are not all defects.** Existing six-size type scale is at studio.css:5. There are610 non-custom CSS declarations containing literal colors (324 studio,106 agent,180 theme), including studio.css:15 rail material and :17 rail text; CSS token definitions themselves were excluded from that610. Theme-specific exceptions are still literal declarations and are not automatically wrong. 290 JS style attributes and 218 literal px occurrences show presentation distributed through markup; prepare.js alone has50 style attributes, editor39. Examples bypassing type tokens: editor.js:102/126/128 and prepare.js:120/126. CAT status colors (studio-tiles.js:4–9), cut overlays (studio-sheet.js:68–87) and composer glyph (:24) also bypass named presentation tokens. Editor/prepare user artwork colors and canvas coordinates are content data, not CSS theme tokens; never replace them mechanically. Introduce explicit spacing/type/status/material tokens and migrate one bounded block per task after choosing its intended meaning.

## Coupling and reachability

The lexical/regex pass found 828 top-level declarations (first declarator of each const/let/var statement plus named functions; an approximation), **no same-name top-level declarations across scripts**, and **one 18-file strongly connected component** in the file call graph. Local esc names in isolated bundles are not global collisions. Calls may be overcounted when locally shadowed; callbacks, ACT/RENDER dispatch and implicit global-state reads are undercounted. The graph is an architecture hint, not an executable dependency tree; raw edges retain callsite + definition lines in scratch/code-metrics.json.

Precisely evidenced reciprocal paths:

- app.js:414 calls live.js:363 histCol; live.js:26 wraps app's drawRail, and calls its helpers. Shell → feature → shell is a two-way ownership dependency.
- studio-core.js:327 calls liveOffer (live.js:79); liveStart :85 calls postWait (studio-core.js:78), completion :182 calls tick :913, and tick :964 calls applyEdgePreview (live.js:244). This is a distributed lifecycle, not necessarily stack recursion.
- library.js:53 selRefresh calls drawPack (packs.js:7); Pack :32 calls selBarHtml (library.js:292), :33 media (:31). Shared selection in the screen file makes component isolation harder.
- effects.js:189–190 fxMotion calls spBurstState/spBurstHtml (particles.js:359/:380); particles.js:11 initializes from fxNew (effects.js:13), :92 calls fxDrCells (:109), and :367 maps fxWords (:28). The common effect controller imports a second screen's private markup.
- studio-core.js:556 calls sheetPanel (studio-sheet.js:313) and tileHtml (studio-tiles.js:224); sheet :12 calls mark (tiles :176), tile chip :198 calls cellState (sheet :94), and both call core tick/postWait. Cut/decision presentation forms a three-file cycle.
- editor.js:70 imports video using prepare.js:13 importVideo; prepare.js:48 uses editor.js:6 cssv. A low-risk escape hatch is to move cssv to a UI-only style utility; do not merge editors.

**C-18 — Script ordering also supplies behavior.** live.js:188–190 captures/wraps RENDER.generate; composer.js:130–131 captures/replaces ACT.ggo intentionally. Settings chains settings.js:7 → trash.js:65 → tickets.js:51 → auth.js:81 in index.html order. particles.js:120–121 wraps the pro effects renderer for an argumentless reaction editor. projmap.js:41–67 wraps histCol/histLoad/gview. These replace functions rather than duplicate globals. An explicit view-extension hook would reduce wrapper chains, but is a high-risk architecture task; defer until component extraction offers a bounded seam. Keep index.html script order and every named action intact.

**C-16 — ACT candidates require classification, not deletion.** The inventory flags26 definitions with no literal data-act button, but several are live through HTML/dynamic names: c2tog/thmtoggle are in index.html; railcreate is generated at app.js:278; jr* use JR controls; hmonboarding/spscope/rosscope are dynamic; rxpload now has a literal preset-chip button (reactions.js rxPresetChips); ggo is Enter/form-driven, gmore is a fallback, ginc is change-driven. qretry (live.js:163) is explicitly compatibility for old saved markup. Stronger near-dead candidates with no source literal button, dynamic string or ACT call: agsetgrid (chat-stage.js:40), psusesave (effects.js:249), vlmyes (live.js:294), sppack/spall/spnovlm/spmake (particles.js:63/:68/:71/:139), psmorechip/psmoreadd/pspackassign (:341/:346/:447). psusesave uses fxPendingSet (effects.js:238), but no current markup/call path was found for that compatibility-style action. Eligibility for retirement needs a baseline entry and owner verdict; retain compat actions unless explicitly authorized. C-01's earlier gkeepsize is proven overwritten, unlike these candidates.

**C-20 — History is reachable, React is parked.** index.html:47 loads history.js, app.js:203 includes history in SCREENS, :266 exposes owner Watch folders, history.js:8 registers the renderer and :35 polls /api/watch. docs/waiting-for-haitham.md item34 calling it retired is stale; it is not currently dead. mirsal/web/ exists with src/e2e and is not loaded by this console shell; item33 calls it parked. Do not delete either.

**C-21 — Inventory header count disagrees with its own rows.** docs/ui_inventory.md:5 reports482 unique actions/483 definitions. The table has483 rows but481 unique names: ggo and gkeepsize each appear twice.17 screen keys/22 actual renderer assignments remain reachable through app's generic router; no unreachable RENDER key found. The bogus extra match from RENDER.effects==='function' was excluded. The supplied inventory generator's omission of shell/dynamic markup is a limitation, not proof of missing UI controls.

**C-17 — Conservative unused CSS candidates.** After excluding obvious dynamic patterns and URL/font false positives, there are37 absent-class candidates in studio.css,6 in theme.css,1 in agent.css; these occur in81/4/1 selector arms respectively. Examples: .gwrap :113, .sheetbox :119, .gleft :243, legacy .gvar/:409, .pk-pt-grid :541, .sp-st :630; theme duplicates .gvar/:73 and .lv-job/:80; agent .is-running/:241. This is best-effort source matching, not browser coverage; server-supplied class names and unvisited states may exist. Do not delete CSS from a single walk. Dynamic .bg-* /.vbg-* /.hm-* /.gv-* /.st-* /.k-* and no_cells were explicitly excluded from deletion candidates.

## Ranked refactor proposals (impact × reach / behavior risk)

| Rank | Finding | Change / files | Payoff / risk | Executor / narrow validation |
|---|---|---|---|---|
|1|C-01|Remove later gkeepsize override in studio-core.js, add staged-preview regression|Very high/low–medium|6.1-sol-medium; new size_preview.test.js; inventory|
|2|C-06|Settle retime Promise on every dismissal; packs.js + app.js plus focused test in separate task|High/medium|luna-6-high; new dialog cancellation test; inventory|
|3|C-05|Non-overlapping watchResource, migrate tick then one watcher per task|Very high/high|luna-6-high helper; literal sol migrations; ui_watch + each consumer's narrow test|
|4|C-02|ui-testcard.js then VZ then EG, separate tasks|High/medium|luna-6-high; ui_testcard + size_preview + anim_create|
|5|C-07|ui-segment.js then five consumers one each|High/medium|luna-6-high helper; sol adapters; segmented + targeted consumer test|
|6|C-03|ui-grouped-grid.js, Library then Pack; retain indices/selection/order|High/medium|luna-6-high; grouped_grid + packs_column/pack_delete|
|7|C-19|Meaningful type/spacing/status tokens, one bounded selector/markup region per task|High/medium|luna-6-high token mapping; sol literal substitutions; theme + DOM probe|
|8|C-09|ui-preview.js request generation + bounded cache; endpoint bodies unchanged|High/high|luna-6-high; preview_session + reactions/pack_studio|
|9|C-08/C-12|ui-download and terminal-purge watcher, each consumer separately|Medium/low–medium|luna-6-high helpers; sol adapters; ui_download/ui_watch + consumer test|
|10|C-11/C-17|Reflow outside template strings, then confirm one CSS candidate family|Medium/low if bounded|6.1-sol-medium; emitted HTML byte equality + targeted test; no bulk delete|
|11|C-04/C-13|rangeFieldHtml; optional decision-status presentation, keep existing eligibility adapter|Medium/high for rule10|luna-6-high; particle_editor/reactions; allow_tiles/chat_allow/sheet_cells|
|12|C-18/C-14/C-15|Explicit extensions, escape alias utility, relative-time policy utility|Low/high churn|Defer; luna-6-high bounded architecture tasks; exact contracts first|

Every implementation step keeps byte-identical backend JSON, server decision authority, ui_baseline.json names/routes, owner-only exports and rule10 picture/reason/override adjacency. Docs-only review runs zero tests; listed tests are proposed executor checks, not claimed passing runs. No full discovery/slow tier. Avoid a whole-file mechanical reformat that breaches ≤150 changed lines/≤2 files or changes template output. Cross-file helpers use luna tasks of ≤6 files, then one consumer per migration.

## Raw-count appendix

Counts are UTF-8 bytes, physical lines including final blank, lines strictly longer than 300 characters, literal quoted style attributes, color literals (#hex or rgb/hsl calls), px literals and timer callsites. Color/px counts include comments, content/artwork values and token definitions; they are not automatic violations. Expression/anonymous callbacks are not all captured by the block-function brace scan, which handles comments/strings/regex and template interpolation; treat function inventory as best effort. Reproducible lexical script and fuller JSON (edges/functions/selectors/actions/timer text) are at the scratch path below and are not source changes.

Scratch: C:/Users/H7068~1.IBR/AppData/Local/Temp/mirsal-uiux-JLvrj7/measure-console.mjs and code-metrics.json.

| JS file | Bytes | Lines | >300 | Max | style | Colors | px | Timers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|agent.js|9288|186|3|341|1|0|0|0|
|animate.js|10638|72|5|376|13|0|11|2|
|app.js|21168|455|5|571|4|0|1|3|
|auth.js|13834|88|5|389|5|0|2|1|
|chat-cards.js|21539|323|7|720|0|0|0|1|
|chat-core.js|32990|798|2|377|1|0|2|5|
|chat-stage.js|16971|386|4|554|0|0|0|0|
|chat.js|11946|89|3|520|3|0|0|4|
|composer.js|18368|149|7|567|0|3|0|0|
|editor.js|33845|226|18|523|39|6|35|1|
|effects.js|34340|250|8|452|4|0|4|3|
|history.js|4917|36|1|392|4|0|3|1|
|home.js|11894|81|9|545|0|0|0|0|
|imports.js|8733|53|9|905|3|0|5|0|
|job-recovery.js|3147|40|0|227|0|0|0|0|
|library.js|17357|439|6|441|8|0|7|1|
|live.js|51538|380|17|747|7|0|3|11|
|packs.js|47887|302|22|827|18|0|12|3|
|particles.js|71703|481|28|834|5|1|6|7|
|prepare.js|34923|213|25|573|50|6|48|3|
|projmap.js|9377|69|4|478|1|0|2|0|
|reactions.js|34133|353|2|357|2|0|0|5|
|settings.js|4864|56|4|767|9|0|5|0|
|sheet-recovery.js|2598|26|1|363|0|0|0|0|
|studio-animate.js|18226|399|4|411|9|0|5|0|
|studio-core.js|48279|982|14|736|8|0|16|3|
|studio-panel.js|9673|187|2|720|8|1|7|0|
|studio-prompt.js|33378|687|10|715|6|0|2|1|
|studio-sheet.js|26281|453|9|598|19|10|8|0|
|studio-tiles.js|23751|466|5|963|10|12|2|0|
|support.js|21068|141|7|439|13|0|4|3|
|telegram.js|6965|55|3|371|14|0|12|0|
|theme.js|1465|13|1|398|0|0|0|0|
|tickets.js|7539|58|2|539|7|0|2|0|
|trash.js|8896|70|4|422|8|0|5|1|
|trending.js|6874|48|3|325|3|0|1|1|
|users.js|10051|68|4|455|8|0|8|0|
|welcome.js|9675|78|1|354|0|0|0|1|
|**Total (38)**|**760119**|**9256**|**264**|**963**|**290**|**39**|**218**|**61**|

| CSS file | Bytes | Lines | >300 | Max | !important | Color literals | px | Absent classes / selectors |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|agent.css|35257|321|8|504|1|142|519|1/1|
|studio.css|158552|1084|51|523|7|435|2568|37/81|
|theme.css|17566|234|1|898|0|242|81|6/4|

index.html: 3,559 bytes; 51 physical lines; 2 lines >300, max537;38 script tags;17 screen sections. Shell HTML styles0, timers0. Top-level scanned source totals975,053 bytes including CSS/HTML (about0.97 MB), excluding assets/vendor/dist.

Functions over 80 physical lines: AIU IIFE agent.js:5–184 **180**; chatCardsInit chat-cards.js:2–322 **321**; RENDER.agent chat-core.js:168–249 **82**; paint chat-core.js:279–384 **106**; chatStageInit chat-stage.js:2–385 **384**; gmodal studio-panel.js:2–94 **93**. Initialization closures contain multiple helpers: do not split those solely to pass a line-count rule. No >80 candidate found elsewhere in this lexical pass; compressed logical functions may still be large.

### All timer callsites (11 intervals, 50 timeouts)

Each listed line is a callsite, not the number of live timers. I=interval, T=timeout. A zero/omitted delay is asynchronous deferral, not polling. Rate is ms. Edge cases and transport watchers retain caller policies.

| File:line | Kind / delay | Purpose and guard |
|---|---|---|
|animate:16|T800|Video seek deadline in thumbnail loop; token/route guarded|
|animate:68|T4000|Object URL cleanup|
|app:29|T3500/6000|Toast lifetime, prior timeout cleared|
|app:372,379|T100 each|Trash-scroll retry;40-attempt cap|
|auth:52|T15000|Pending approval auth refresh|
|chat-cards:288|T60|Drag click suppression cleanup|
|chat-core:244|T60|Composer focus after render; route/stage guard|
|chat-core:276|T1200|Bottom pin/scroll cleanup|
|chat-core:762|T2500|Chat fallback retry on failed read|
|chat-core:768|T700/1600/4000|Chat job polling; route/hidden/session guarded; SSE preferred|
|chat-core:777|T500|First fallback polling read|
|chat:53|T180|Tray close transition cleanup|
|chat:69|T3200|Reaction playback end; epoch/request guard|
|chat:71|T450|Mock typing; epoch guard|
|chat:72|T1500|Mock reply; epoch guard|
|editor:194|T400|Debounced arrow-key commit|
|effects:65|T2200|Busy effect read; state alive guard; not universal subscription|
|effects:155,156|T350 each|Draw estimate debounce|
|history:35|I4000|Watch folders refresh, route guarded|
|library:386|T0|Trending load deferral|
|live:113|T120|Sheet fill preview debounce|
|live:184|I2500|Job reads; LTB prevents overlap; no hidden guard|
|live:185|I1000|Elapsed text and queue markup replacement|
|live:191|I1000|Second active queue markup replacement|
|live:195|I20000|Provider status refresh; unconditional|
|live:251|T40|Edge preview debounce|
|live:267|I800|Edge state/preview synchronization; unconditional|
|live:285|I10000|Earlier batch refresh; visible + create/generate only|
|live:349,354|T500 each|Trash purge loops;240 iterations|
|live:374|T0|Particle-batch open deferral|
|packs:79|T2500|Collection export retry;404/tries>720 stop, no hidden guard|
|packs:144|T220|Sticker reaction hover debounce|
|packs:301|T300|Reaction wall search debounce|
|particles:164|I2500|Studio reaction section; visible/generate; SPS.busy guard|
|particles:231|T250|Emoji-bank search debounce|
|particles:271|T2500|While sets drawing; route-specific reads, timer can wake off-route|
|particles:336|T500|More-sprite estimate debounce|
|particles:412|T220|Burst parameter preview debounce|
|particles:413|T350|Burst resolution preview debounce|
|particles:450|T300|Chat → Studio set-open deferral|
|prepare:70|T500|Autosave debounce|
|prepare:164|T350|Project commit/redraw debounce|
|prepare:198|T4000|Object URL cleanup|
|reactions:249,256|T1500 each|Running reaction batch progress; first/next reads|
|reactions:265|T150|Wall search debounce|
|reactions:269|T300|Editor preview debounce (shares RXS.t with search)|
|reactions:281|T220|Wall hover preview debounce|
|studio-core:66|Tvariable|Promise wait used by postWait retry|
|studio-core:836|T250|Animation preview debounce; VZ.n latest-reply guard|
|studio-core:973|I700|Studio generation polling; route/modal guard, no overlap/hidden guard|
|studio-prompt:656|I5000|Operator job read; clears on error, terminal status or missing DOM|
|support:92|T15000|Support conversation watch; route/state/hidden checks|
|support:139|T1500 + I30000|Initial/persistent notifications; interval hidden guard|
|trash:48|T1200|Purge wait; until terminal/read error, no explicit deadline|
|trending:40|T300|Use-public-pack → Studio composer deferral|
|welcome:77|T450|Welcome opening after auth gate check|

CSS candidates and lexical counts are starting evidence. No runtime request/CPU timing or comprehensive CSS coverage was measured by this subagent; the browser walk provides the screen scores and actual layout evidence.

### Regex cross-file call adjacency (raw appendix)

Names below omit .js. Includes calls in local closures/template interpolation; excludes property dispatch, implicit state reads and indirect callbacks. Ubiquitous app/Library helpers remain visible so the18-file SCC is reproducible. Local shadowing may overcount an edge. Definitions/callsite lines and symbols are retained in scratch/code-metrics.json.

| Script | Calls helpers declared in |
|---|---|
|agent|app, composer|
|animate|library, app|
|app|library, studio-core, theme, live, chat|
|auth|app, welcome|
|chat-cards|app|
|chat-core|app, composer, studio-core, chat-cards, studio-panel, chat-stage|
|chat-stage|app|
|chat|app, library|
|composer|studio-prompt, app, live, studio-core|
|editor|app, prepare, library|
|effects|app, library, live, particles, packs|
|history|app, studio-core|
|home|app, library, welcome|
|imports|app, studio-core|
|job-recovery|live, app, studio-core|
|library|app, packs, particles|
|live|studio-core, app, composer, particles, studio-prompt|
|packs|library, app, studio-core, studio-panel, prepare, reactions, particles, effects|
|particles|effects, app, library, live, studio-sheet, studio-core, packs|
|prepare|app, library, editor, animate|
|projmap|studio-prompt, app, live, studio-core, particles, composer|
|reactions|app|
|settings|theme, app, telegram|
|sheet-recovery|app, studio-core|
|studio-animate|studio-core, live, app, studio-sheet, studio-prompt, library, particles, packs, studio-panel|
|studio-core|app, studio-sheet, studio-prompt, composer, live, particles, studio-panel, studio-tiles, library, packs, studio-animate|
|studio-panel|studio-core, app, studio-tiles, live|
|studio-prompt|app, live, studio-core, studio-sheet, composer, particles|
|studio-sheet|studio-core, studio-tiles, app, live, studio-prompt|
|studio-tiles|studio-core, app, studio-sheet, studio-panel|
|support|app, studio-tiles, studio-core|
|telegram|library, app, packs|
|theme|none|
|tickets|app|
|trash|app, library|
|trending|app, library, composer, packs|
|users|app, history|
|welcome|app|

Measurement reconciliation: app.js/home.js/reactions.js changed between the initial read and the fetched clean review branch. The current counts above were re-read on HEAD170f26e. Current reaction source paginates with RXPAGE=120 and uses rxPresetChips plus picked-preset Update/Remove; older served Load/Remove menus are asset drift, not a recommendation to restore old UI. Use named anchors if a later concurrent edit moves a line.
