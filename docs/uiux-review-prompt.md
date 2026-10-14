# UI/UX review of Mirsal Builder — a prompt for an orchestrating LLM

Paste everything below the line into a fresh session that has this repository, a shell, Playwright (or a browser tool) and the ability to start
subagents. Written 2026-10-14 by the session that built the reaction branch; every path, command and rule here was checked against the repo that day.

---

## 0. Who you are and what you deliver

You are the **orchestrator** of a UI/UX and code-structure review of **Mirsal Builder**, a web app that makes animated Telegram stickers
(the screens are a sandbox over an engine; the product is the engine + its JSON API). You do **not** redesign or refactor anything in this run.
You **review, measure, rank, and write a plan** that a second LLM will cut into tasks for two executor models:

- **`6.1-sol-medium`** — fast, cheap, literal. Give it small, mechanical, fully-specified tasks: one file or one component, exact selectors, exact
  before/after, an acceptance check. It must never have to decide anything.
- **`luna-6-high`** — slower, careful, good at judgement. Give it the tasks that need design decisions, cross-file refactors, or a shared
  component extracted from several copies.

Your deliverables (all on branch `ui/ux-review`, committed and pushed):

1. `docs/uiux_plan.md` — THE plan (format in §7). This is the only file the next LLM must read.
2. `docs/uiux_review/findings.md` — the evidence: every finding with its id, screen, screenshot file, severity score and the code it points at.
3. `docs/uiux_review/duplication_map.md` — every feature implemented more than once (§5).
4. `docs/uiux_review/screens.md` — the screen/state inventory you walked, with a one-line verdict per state.
5. Screenshots under `docs/uiux_review/shots/` — **only the ones cited by a finding** (budget in §4.4); everything else stays in a scratch dir and is never committed.

No source file under `mirsal/` changes in this run. If you find a crash or a broken route, record it as a finding with severity "broken"; do not fix it.

## 1. First, set up (do these in order)

1. Read `CLAUDE.md` (short: rules and routing). It is binding. The full rule text is `docs/rules.md`; read only the rules you need.
2. `git fetch --all`, then create the branch from the newest work: `git checkout -b ui/ux-review origin/reactions`
   (`reactions` = `edit-design` + everything since 2026-10-13; `main` is older). Push it once at the start: `git push -u origin ui/ux-review`.
3. Make a scratch dir outside the repo for screenshots and notes (e.g. `%TEMP%/uiux` on Windows, `/tmp/uiux` on macOS).
4. Start **your own** server on a spare port against a **copy** of the data, with every paid or external provider off. Never use the owner's
   server on **:8770** and never kill it. Windows (PowerShell is fine; `mirsal\.venv`), macOS uses `mirsal/venv`:

   ```
   # copy the data (skip the heavy and irrelevant folders)
   robocopy mirsal\out <scratch>\outcopy /E /XD cache trash jobs          # macOS: rsync -a --exclude cache --exclude trash --exclude jobs mirsal/out/ <scratch>/outcopy/
   # then, from mirsal/, with these environment variables set:
   MIRSAL_OUT=<scratch>\outcopy  MIRSAL_DB_WRITE=0  MIRSAL_TRACE=none  MIRSAL_NO_REAL_CLI=1
   MIRSAL_LLM_PROVIDER=none  MIRSAL_AGENT_PROVIDER=none  MIRSAL_VISION_PROVIDER=none
   .venv\Scripts\python.exe -m mirsal serve --port 8795
   ```

   Check `http://127.0.0.1:8795/api/health` answers before you trust anything you see. Keep `library/files` in the copy (the Library needs it).
5. **Never spend.** Do not press any button that creates a paid job (Generate / Create sheet / Animate / Regenerate with a model, "Send to
   Telegram", "Export to collection" → Send). The fakes above make most of them safe, but you are reviewing, not producing. Opening a dialog and
   closing it is fine and expected.
6. In the browser, dismiss the welcome modal first (`document.getElementById('welcome').classList.remove('on')`), otherwise it eats clicks.

## 2. What the app is (so you do not rediscover it)

- **Shell:** one page app, `mirsal/mirsal/console/` (≈38 scripts, ~1 MB of JS/CSS). Routing by hash (`#/home`, `#/create`, `#/studio`,
  `#/library`, `#/pack/<id>`, `#/reactions`, `#/effects`, `#/chat`, `#/trending`, `#/settings/...`, `#/help`, ...). Each screen is a
  `RENDER.<name>` function; every button is `data-act=<name>` dispatched to `ACT.<name>(el, event)` by one global click handler in `app.js`.
- **The generated inventory of everything clickable:** `docs/ui_inventory.md` (≈480 actions, 17 screens, the routes each one calls), produced by
  `python -m mirsal.console.inventory`. **Use it as your checklist** instead of guessing what exists.
- **Design reference:** `docs/design.md` is an INDEX; its sections are in `docs/design/` (one shell, one token set, the rail of four, the
  AI screen as the visual reference, §9 "every rejected picture carries its own override"). Themes: `docs/dark-mode.md` (`theme.css`).
- **The redesign that already happened:** `docs/redesign_plan.md` (rail of four, Create = Chat | Studio, journey bar, project map).
- **Big area docs are indexes** with one file per section: `docs/engine-and-studio/`, `docs/agent-and-chat/`, `docs/api-parts/`, `docs/design/`,
  `docs/generation/`, `docs/reaction/`. Read the index, then only the sections you need.
- **Hard constraints any proposal must respect** (from `CLAUDE.md`):
  - **No action, screen or route may disappear** without a `renamed` / `retired` entry in `mirsal/tests/data/ui_baseline.json`
    (`tests/test_ui_inventory.py` enforces it). A redesign MOVES things; it never silently drops them.
  - **Rule 10:** a rejected picture is never a dead end — on every surface that shows it, the picture, a one-sentence reason and a
    "Use it anyway" / "Take it back" button sit right there. Do not propose hiding these.
  - **Rule 11:** logic lives in the engine/API, never only in the browser. A UI refactor may not move a decision into JS.
  - **Rule 6:** no control without a backend that reads it.
  - Owner-only actions (Telegram, Export to collection) stay owner-only.

## 3. Phase A — two reading subagents, in parallel (start them first; they need no browser)

Start both at the same time. Give each the text of its brief below plus §2. Each returns a markdown report to you; you merge them in §6.

### Subagent A1 — "docs reader"

> Read `README.md`, `CLAUDE.md`, `docs/rules.md`, `docs/architecture.md`, the index files of every split doc and the sections of `docs/design/`,
> `docs/redesign_plan.md`, `docs/dark-mode.md`, `docs/onboarding.md`, `docs/reaction/` (sections 12-14), `docs/backlog.md`,
> `docs/waiting-for-haitham.md`. Do not read code. Report:
> 1. **Contradictions** between docs (two docs describing the same screen differently; a doc describing something the inventory no longer has).
>    Give file + line for both sides.
> 2. **Stale statements** (dates, "two rows", "Your reactions", counts that changed, routes that moved). List them; do not fix.
> 3. **Doc structure refactors**: which docs are still too big for an LLM to read cheaply (anything over ~25 KB that a task must read whole),
>    which split sections are mis-cut (a section that is really two topics, or two sections that are one), duplicated explanations living in
>    several docs (name the one that should own it), and the reading path a UI task should take (≤ 8 KB before code).
> 4. **The UX promises the docs make** (e.g. "one shell for every section", "every rejected picture has its override", "Create = Chat | Studio",
>    "the AI screen is the reference") as a numbered checklist, so the browser phase can test each one.
> 5. **Open UI items already tracked** in `backlog.md` / `waiting-for-haitham.md` (so the plan does not re-propose them as new; it may merge them).
> Keep the report under 6 pages. Every claim cites a path.

### Subagent A2 — "code reader"

> Read `mirsal/mirsal/console/*.js`, `studio.css`, `theme.css`, `agent.css`, `index.html` (or whatever the shell is), and `docs/ui_inventory.md`.
> Do not read the engine. Measure before you judge: write small scripts (Python or Node) to count things, and paste the numbers. Report:
> 1. **The duplication map** — every UI feature implemented more than once (§5 lists known suspects; confirm, reject, and find the rest).
>    For each: the copies (file:line), how they differ, and the ONE shared component it should become (name, file, signature).
> 2. **Structural smells, measured:** lines over 300 characters per file (several files are written as one long line per function: packs.js,
>    particles.js, reactions.js, live.js); functions over 80 lines; inline `style="..."` counts per file; hard-coded colours/sizes that bypass
>    the tokens in `studio.css :root` / `theme.css`; `!important` counts; CSS rules never matched by any markup (best effort); global names
>    defined in more than one script; `setInterval`/`setTimeout` polling loops (list them all: each one is a cost and a source of flicker).
> 3. **Coupling:** which scripts call which (build the call graph of top-level functions across files with a regex pass), cycles in it, and the
>    screens that render another screen's private markup. Name the circular / spaghetti paths precisely.
> 4. **Dead or near-dead code:** `ACT.*` with no `data-act` button anywhere, `RENDER.*` no route reaches, CSS classes no JS emits, parked
>    files (`console/history.js` is retired — W34; `mirsal/web/` React is parked — W33).
> 5. **Refactor proposals ranked by payoff/risk**, each with: files, the change, what must not change (byte-identical JSON, `ui_baseline.json`),
>    the tests that cover it (`node --test mirsal/tests/js/<file>.test.js`; `python -m unittest tests.test_ui_inventory`), and which executor
>    model should take it (sol-medium = mechanical; luna-high = judgement).
> Keep the report under 8 pages; put raw counts in an appendix table.

## 4. Phase B — the browser walk (you, or one browser subagent per screen group)

This is the main job and the most expensive. Hundreds of screenshots are a failure mode: they cost more than they reveal. Measure the DOM first,
photograph second, and only photograph what the numbers flag.

### 4.1 The journeys to walk (each is "a main action")

Walk each as a user would, from the rail, on your copy (§1.4). For every step note: clicks to reach it, what is on screen, what is confusing.

| # | journey | where it starts | stop before |
|---|---|---|---|
| J1 | **Create a new sticker set** (Studio): request → Generate prompt → the plan → stickers → Animation tab → video size / keep size test card → approve | Create › Studio | any paid "Create sheet" / "Generate video" |
| J2 | **Create via the AI chat**: type a request, see the plan card, the carousels, the price ask | Create › Chat | accepting a price |
| J3 | **Check the library**: Library → packs column → a pack (header: Open in Studio · Download .zip · Send to Telegram · ⋯) → batch groups → a sticker viewer → Edit → Timeline | Library | Send / Export |
| J4 | **Create a new reaction**: Reaction effects (`#/reactions`) → wall (search, Done/Not done, hover) → open an emoji → sliders → Presets ▾ → Animation presets → Select + Shift-click → the batch bar | Create › + New › Reaction effects | pressing a batch "All 1800" |
| J5 | **Pack reactions / particles** (the Studio's pack particles `#/effects`, the pack's Reactions tab, the reaction studio) | a pack › Reactions tab | Render |
| J6 | **A rejected sticker**: find a batch with a blocked still and a blocked animation (G005 in the copy has allowed ones) and check rule 10 on every surface: Studio tile, sheet slice, chat card | Earlier batches column | — |
| J7 | **Home + welcome modal** (logo target, film, feature slides) | logo | — |
| J8 | **Trending, Help & Support, Settings** (Appearance, Trash, Tickets, Spending), **Users** (only if `--lan`; skip otherwise) | rail | — |
| J9 | **Export dialogs**: Download .zip (retime ask), Export to collection (name, description, Quality Full/Light), Telegram send — open and cancel | a pack | Send |
| J10 | **Dark mode** — repeat a short pass of J1, J3, J4 with the theme switched (sun/moon top right) | — | — |
| J11 | **Phone width** — repeat J3 and J4 at 390×844 | — | — |

### 4.2 Measure every state with one DOM probe (no screenshot yet)

For each state you reach, run ONE `page.evaluate` probe and store its JSON line in `<scratch>/probes.jsonl`. Suggested probe (adapt):

```js
() => {
  const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const all = [...document.querySelectorAll('body *')].filter(vis);
  const btn = all.filter(e => e.matches('button,[role=button],a.btn,.btn'));
  const tiny = btn.filter(e => { const r = e.getBoundingClientRect(); return r.width < 32 || r.height < 28; });
  const over = all.filter(e => e.scrollWidth > e.clientWidth + 2 && getComputedStyle(e).overflowX === 'visible');
  const fonts = new Set(all.map(e => getComputedStyle(e).fontSize));
  const colors = new Set(all.map(e => getComputedStyle(e).color));
  return { route: location.hash, buttons: btn.length, primary: document.querySelectorAll('.btn.pri:not([disabled])').length,
    tinyTargets: tiny.length, inlineStyles: document.querySelectorAll('[style]').length, overflowing: over.length,
    fontSizes: fonts.size, textColors: colors.size, depth: Math.max(...all.map(e => { let d = 0, n = e; while (n.parentElement) { d++; n = n.parentElement } return d; })),
    pageHeight: document.documentElement.scrollHeight, horizontalScroll: document.documentElement.scrollWidth > innerWidth,
    dialogs: document.querySelectorAll('dialog[open],.dlg.on,#welcome.on').length };
}
```

### 4.3 Score, then decide what to photograph

Give each state a **severity score** from the probe plus what you saw (write the formula in `findings.md` so it is reproducible). A starting point:

- +5 broken (error toast, empty screen, console error, a route 404)
- +4 horizontal scroll or overflowing text at the tested width
- +3 more than 2 enabled primary buttons, or no clear primary action
- +2 per 10 visible buttons over 15 (choice overload)
- +2 tiny tap targets (> 5) ; +2 font sizes > 6 ; +2 text colours > 8 ; +1 inline styles > 20 ; +1 DOM depth > 25
- +3 a rule-10 surface missing its picture / reason / override
- +2 a doc promise from A1 §4 that this state breaks
- +1 per extra click versus the shortest sensible path for the journey step

### 4.4 Screenshot budget and settings

- Context: viewport **1440×900, deviceScaleFactor 0.5** (half resolution, about 720×450 px files); JPEG quality 60; `fullPage: false`
  (one viewport — scroll and take a second only if the problem is below the fold). Phone pass: 390×844, deviceScaleFactor 1.
- **Budget: at most 60 screenshots in total.** One per journey step that scores ≥ 5, plus the top 3 of each journey regardless of score, plus a
  before/after-theme pair for the 5 worst. Name them `J<journey>-<step>-<slug>-<theme>.jpg`.
- Make a **contact sheet** per journey (a grid of the thumbnails, e.g. with Pillow) so the reviewer sees a journey in one image.
- If you ever exceed 60, stop and re-rank: drop the lowest scores. Hundreds of screenshots is a failure, not thoroughness.
- Look at each kept screenshot once and write its finding immediately (what, why it hurts, which principle, which code). Never re-open images to
  "check again" — the probe numbers are your memory.

### 4.5 What to judge (the UX lens)

Hierarchy (one obvious primary action per screen), grouping (related controls together, separated sections), progressive disclosure
(advanced settings folded), consistency (the same feature looks and behaves the same everywhere — this is where the duplication map and the UI
meet), feedback (every long action shows progress and a way out; nothing freezes — the old "Export to collection" froze at "Sending…"),
reversibility (rule 10; undo where promised), empty states, error wording (plain sentences, never a bare code), density on phone, dark mode
contrast, motion that explains rather than decorates.

## 5. Known duplication suspects (confirm or reject each; find more)

These were seen while building the reaction branch; treat them as leads, not facts:

1. **"Test card with Apply / Cancel"** — the Edge test card (`live.js` `egCard`, `#egcard`) and the Video size / Keep approved size card
   (`studio-core.js` `VZ`, `vzCard`, `#vzcard`) are the same UI written twice. One component.
2. **Grouped sticker grids** — My Stickers grouped by pack (`library.js` `lib-bypack` / `.lib-pk`) and the pack screen grouped by batch
   (`packs.js` `pkGroups` / `.pk-bybatch` / `.pk-grp`) duplicate markup and CSS.
3. **Three reaction/particle screens** — `effects.js` (`#/effects`), `particles.js` (pack reaction studio, 72 KB), `reactions.js`
   (`#/reactions`); overlapping sliders, presets, previews and hover code. Map exactly what is shared and what is not.
4. **Background-job polling** — `tick()` (Studio), `colWatch` (collection export), `rxWatch` (reaction batches), the 800 ms `egSync` interval,
   the history refresh, Hugging/HF refresh intervals. One polling/subscription helper (or the existing SSE `/events`) instead of N loops.
5. **Dialogs and menus** — `dlg`, `confirmDlg`, `askText`, `retimeAsk`, `pickPack`, and many `<details class=gh-more>` menus built by hand.
6. **Segmented controls / toggles** — `.gseg` built inline in several screens with different markup.
7. **Download helpers** — several "create an `<a download>` and click it" copies.
8. **Preview endpoints and caches** — `edge_preview`, `anim_preview`, `sheet_preview`, `emoji-preview` (with its JS caches `RXS.pv`, `ppv`).
9. **Toasts vs inline warnings vs notifications** — three ways to tell the user the same kind of thing.
10. **Long one-line functions** in `packs.js`, `particles.js`, `reactions.js`, `live.js`: unreadable diffs; a mechanical reflow task.

For each confirmed duplicate, the plan must name the single shared component, its file, its API, and the order to migrate the copies
(one copy per task, tests green after each).

## 6. Phase C — merge, rank, decide

1. Merge A1, A2 and your browser findings into `findings.md`. De-duplicate: a finding that is both a UI inconsistency (browser) and a
   duplicated implementation (code) is ONE finding with both kinds of evidence. That overlap is the most valuable thing you can produce.
2. Rank by **impact × reach ÷ risk**: impact = the severity score; reach = how many journeys/screens it touches; risk = how much behaviour
   could change (JSON contracts, rule 10, owner-only actions, the baseline). Put the top 15 at the top of the plan.
3. **The redesign direction — "modern iOS, keep 90%":** keep the shell, the rail of four, the routes, every action and the current information
   architecture. Change the surface: an 8-pt spacing grid; one type scale (large title, title, headline, body, footnote; no ad-hoc font sizes);
   grouped inset lists and cards for settings-like screens; segmented controls for 2-4 way choices; sheets (bottom on phone, centred on desktop)
   instead of ad-hoc floating cards; one primary button per view, secondary as plain/tinted; translucent material only for bars and sheets; SF
   Symbols-like line icons at one weight; motion 150-250 ms ease-out that explains a change; 44-pt tap targets; tokens for everything (no
   inline colours). Every proposed change names the tokens/components it introduces and the screens it touches. Show 3-5 before/after sketches
   (ASCII or a short HTML mock in `docs/uiux_review/mocks/`) for the worst screens only.
4. Anything that needs the owner's verdict (a product choice, a removal, a visual direction with real alternatives) goes to a "Questions for
   Haitham" list with a recommendation each — do not decide it.

## 7. The format of `docs/uiux_plan.md` (what the next LLM receives)

```
# UI/UX plan (branch ui/ux-review)
## Summary            — 10 lines: the 5 worst problems, the 3 shared components that fix most of them, the redesign direction in one paragraph.
## Ground rules       — the constraints of §2 restated in 8 bullets; the test commands; the no-spend server recipe.
## Phases             — P1 mechanical cleanup (reflow, tokens), P2 shared components, P3 screen redesigns (worst first), P4 docs and inventory.
## Tasks              — one block per task:
   ### T-012  Extract the test card component            [model: luna-6-high]  [risk: medium]  [depends: T-004]
   Why: F-07 (findings.md) — two copies (live.js egCard, studio-core.js vzCard) behave differently (scroll, theme, disabled state).
   Files: console/testcard.js (new), live.js, studio-core.js, studio.css, index.html (script order)
   Do: <numbered exact steps>
   Do not: change any route, any ACT name, any JSON; drop "Use it anyway".
   Accept: node --test mirsal/tests/js/<x>.test.js green; python -m unittest tests.test_ui_inventory green; the probe of J1 step 6 shows ≤1 primary button.
   Size: ~120 lines changed.
## Questions for Haitham  — numbered, each with options and a recommendation.
## Not doing            — what you considered and rejected, one line each, so nobody re-proposes it.
```

Task sizing rules: a `6.1-sol-medium` task touches ≤ 2 files, ≤ 150 changed lines, has zero design decisions and an exact acceptance check; a
`luna-6-high` task may touch up to ~6 files and make bounded decisions, but must still end with tests green. No task depends on more than two
others. Every task cites at least one finding id.

## 8. Testing and cost discipline (binding, from `docs/testing.md`)

- One narrowest run per change; docs-only changes run no tests; the slow tier and full `unittest discover` are retired — never run them.
- In this review run you change no code, so the only tests you may run are ones that **measure** (e.g. `python -m mirsal.console.inventory`,
  `node --test mirsal/tests/js/<file>.test.js` to see what is pinned before proposing a change to it).
- Never call a paid provider; never use :8770; delete the scratch copy of `out/` at the end.

## 9. Finishing

1. Commit `docs/uiux_plan.md`, `docs/uiux_review/` (findings, duplication map, screens, the cited screenshots and contact sheets, mocks) with
   explicit paths — never `git add -A`, never anything from `mirsal/out/`, `.env`, `opencode.json` or `mirsal/telegram-id.md`.
2. Push `ui/ux-review`.
3. Your final message: the 5 worst findings in one line each, the number of screenshots kept (must be ≤ 60), the task count per model, and the
   questions for Haitham.
