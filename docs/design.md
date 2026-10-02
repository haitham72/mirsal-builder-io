# docs/design.md — the look of Mirsal: one shell, one palette

**Status: written 2026-10-02 from Haitham's notes after a pass over the running app; built in the order of §8, and §8 says which steps are done.** It is the design half of the app, kept
in `docs/` because it is architecture, not a log (rule 12): the screens are a sandbox over the API (rule 11), but the *shell* they share is a real, stable
surface that every screen inherits. When a screen's look changes, this file changes in the same step.

`HANDOFF.md` §2 "Visual design" carries the work items; this file says what they add up to.

---

## 1. The one problem behind every item on the list

Haitham's notes read as five separate complaints. They are one: **the sections do not agree about what the shell is, and the app has three palettes.**

*(Corrected the same day after checking the first draft against the code: the draft said the rail turns into a horizontal bar on AI, is 72px wide and is missing AI.
None of that holds on desktop. What is really inconsistent is below.)*

**The desktop shell is one rail with a second column that appears on some screens.**

| | where | what it does |
|---|---|---|
| rail | `#app{grid-template-columns:96px 1fr}` (`studio.css:6`) | a **96px** column on every screen; 72px is the width of one `.rbtn` inside it |
| second column | `body.col2 #app{... 96px 392px 1fr}` (`studio.css:7`) | on only for `['library','pack','chat','agent']` (`app.js:73`); Studio, Create and Settings have none, so the page starts at x=96 there and at x=488 elsewhere |
| col2 width | `studio.css:120` 300px at <=1180px; **`agent.css:180` 280px** at <=1180px, and **`agent.css:181` hides it below 900px on AI only** | the same column has three widths depending on the screen |

**The responsive layer is where the shell really splits.** The bottom-bar rail (`agent.css:182-186`: `flex-direction:row`, `.rbtn{width:auto;flex:1}`) sits inside
`@media (max-width:760px)` and is scoped to `body.agent-view`, so **only AI has a phone layout**. At 390px Library is still a 96px rail plus a 300px column (measured:
rail 96, col2 300, 0px left for the page).

**AI is in the rail, but not where the rail is declared.** `RAIL` (`app.js:63`) lists five items; `agent.js:37` does `RAIL.unshift(['agent','ai','AI'])` and `SCREENS.push('agent')`
when it loads, and `route()` falls back to `'agent'` for an unknown hash (`app.js:67`). It works, but the navigation's own data does not say so and depends on script order.

**Three palettes.**

| where | tokens | feel |
|---|---|---|
| `studio.css:2` `:root` | `--pri:#3B82F6` blue, `--bg:#F7F9FB`, `--sf:#fff`, `--r:16px` | light, flat, blue |
| `agent.css:5` `#s-agent` | `--ai:#06B6D4`, `--ai2:#22D3EE`, `--wash:#F2FBFE`, `--glass`, `--aglow`, `--viol` | cyan, glass, glow |
| `studio.css:297` `.cp` | `linear-gradient(180deg,#070b1c,#050816)` + `#2a52ff` glow, `.cp-box` `#0b1124d9` | near-black navy |

AI is the good one and is the reference. `.cp` (the Studio's composer panel) is the "ugly dark blue that has no other match in the app" — a dark island in a light app.
**Target: one token set, AI's character, available to every screen.**

Smaller defects found while measuring (fixed with the screen they sit on): the Settings Telegram icon renders unsized and fills the page; the fixed Queue pill covers the
bottom-left of the stage (the first Earlier-batches card on Studio).

---

## 2. Non-negotiables (breaking these breaks the app, not just the look)

- **No CDN, no runtime fetch** (rule 8). One self-hosted family: `console/fonts/InterVariable.woff2` (`studio.css:1`), used by `body` at `studio.css:4`.
  No second webfont. Icons are inline SVG (`ic()` in `app.js`).
- **One shared `ACT` object.** A second `ACT.name =` in a later script *silently replaces* the first — this already bit the app once (`history.js` replaced
  `hopen`, so "Earlier batches" opened batch NaN). `tests/test_js.py` fails on any clash not listed as intentional.
- **No duplicate top-level `const` across scripts.** The second declaration is not run at all (`history.js` was dead for a while because of `ago`).
- **`agent.css` selectors stay namespaced** (`ag-`, `is-`, `k-`): the Studio's own CSS already uses `.step`, `.tile`, `.sel`, `.done`.
- **Issue colours are locked** (`HANDOFF.md` §3): orange out of bounds, purple bad green screen, yellow bad loop, pink look or motion, blue file / Telegram
  limit, red dropped or blocked; hatched = not in the set, dashed = kept with a check. A redesign must not repaint these — they carry meaning.
- **Never open media to judge it** — a design change is judged on the code and in the browser, stickers are judged by the verifier and by Haitham.

---

## 3. Foundations

### 3.1 One token set

Lift AI's tokens out of `#s-agent` into `:root` in `studio.css`, keep the light base, and let every screen read the same names:

```
--pri / --pri-d / --pri-l / --pri-bd      one accent (cyan-leaning, AI's --ai family), light/dark/border/glow
--bg --sf --fill --bd --tx --mut --mut2   surfaces and text
--glass --glow --wash                      the AI depth cues, now available everywhere
--r --sh                                   16px radius, the existing soft shadow
```

Then: **`--pri` is the accent everywhere.** `.cp` loses `#070b1c`/`#050816`/`#2a52ff` and its `.cp-box` `#0b1124d9`. If the composer should feel like the
AI screen, it gets the glass and glow; if it should feel light like the Studio, it gets `--sf`. **Pick one and hold it** — the current failure is precisely
that it is neither.

**Decision (2026-10-02, built):** `--pri` stays Mirsal blue `#3B82F6` (the logo's blue, AI's own `--blu`) as the action colour: buttons, selection, focus. AI's cyan
family (`--ai`, `--ai2`, `--aid`, `--ink*`, `--wash`, `--glass`, `--aline`, `--aglow`, `--viol`) moved from `#s-agent` into `:root` and is the *depth* every screen shares
(glass columns, the glow, gradient titles, hover washes). Repainting every primary button cyan would have changed all screens' meaning of "primary"; it is one token
(`--pri`) if Haitham wants it later. `--rail-w` and `--col2-w` are tokens too, so the column has ONE width on every screen (392px, 300px at <=1180px).

*Enhancement:* keep a single dark surface as a deliberate accent rather than an accident — the composer box and the plan card can be the app's one dark
island if it is *designed* as such (same radius, same border, same glow token) instead of an unrelated navy.

### 3.2 Type, spacing, motion

- One family, one scale. Today sizes are set ad hoc per component (`.lv-ht` 15px, `.lv-hmeta b` 14px, `.cp-style b` 14px, `.cp-style em` 11.5px, `.rbtn`
  12px, `.sh` …). Define ~6 steps and use them, so a screen cannot drift.
- **One radius scale** derived from `--r:16px` (8 / 12 / 16 / 24). The composer currently uses 20/24/30px on its own.
- Motion: the app already has `transition:box-shadow .2s` on `.cp-box` and `.lv-hitem` hover transitions. **Every interactive element gets a hover and a
  `:focus-visible`**, matching `.lv-hitem` (`studio.css:353`), which is currently the best-behaved rule in the app and should be the template.

---

## 4. The shell — rules that hold on every screen

1. **The rail is one fixed element in one place.** Same width, same position, same order, on all six sections. Its width is a token; it does not change
   shape per route. Keep the icon-over-label form (`app.js:65`) — it is legible at 72px.
2. **The rail has six items and AI is one of them**, declared in `RAIL` (`app.js:63`) in this order: **AI, Studio, Library, Chat, Create, Settings.** It shows six
   today only because `agent.js:37` unshifts AI in; the declaration moves into `app.js` so the navigation does not depend on script order. `RAILOF` still maps the sub-routes (`pack→library`, `editor`/`export`/`prepare`→`create`,
   `animate→library`).
3. **A persistent second column on every screen that has a list** — Library, Chat, AI for sure, and **Studio and Create** because both have real lists
   (Studio: the batches; Create: the pack/prepared sheets). `drawCol2()` (`app.js:73`) stops being an allow-list of four routes. It must be scrollable,
   collapsible, and remember its width; on a phone it becomes a drawer.
4. **Same geometry everywhere:** same gutters, same card radius, same header height, same place the page title sits. If a screen needs to break the
   pattern for a real reason, the reason goes in this file.
5. **The rail scrolls when it must, it never reflows.** "Scaling instead of fixed" means the rail and second column scale with the viewport (fluid widths,
   clamped) while staying the same element in the same position — not a different layout per route.

---

## 5. Per screen

### AI (`agent.js`, `agent.css`) — the reference, keep its character
- Keep: the cyan/glass/glow depth, the gradients, the hover and selection states on the chat list, the new-chat background.
- **Change:** it stops being a special case. Its tokens move to `:root` (3.1) and its rail becomes the standard rail (4). Its second column stays.

### Library (built)
- **Rail:** identical to AI's, same scaling, same persistent position — this is the explicit ask.
- **Sticker library gets the same glow background as AI** so the two screens read as one app.
- Keep the rail's fonts, backgrounds, hovers and selection states **character-identical** to AI's. If a value differs between the two, AI wins.

### Studio — "this is where it becomes dirty"
- **The composer panel loses the dark navy** and takes the shared surface (3.1). This is the single biggest visual defect in the app.
- **Style tiles: fewer sizes, more choices.**
  - Today: `.cp-styles` (`studio.css:324`) is a horizontal scroller and each `.cp-style` (325) is `flex:1 0 150px; max-width:250px`, `aspect-ratio:3/4` —
    **huge portrait cards, six of them, in a row.** They dominate the panel and still cannot be compared at a glance.
  - Change to a compact **chip or square tile** (one row, wrapping, ~72–96px), label below or beside, `aspect-ratio:1`. Selection by ring + check, not by
    size. The hint text stays but gets quieter.
  - *Enhancement:* the tiles must be honest. `console/assets/styles/` is **empty**, so all six currently render `placeholders.py`'s `style_svg()` teddy heads.
    Ship real tile art (`<id>.png/.jpg/.webp/.svg` per `styles.py`'s docstring) or make the placeholder deliberately abstract — a large photo of a teddy is
    worse than a clean swatch.
- **More presets.** Six (`styles.py`) is not enough to feel like a choice, and the chat cannot even reach four of them. Add presets as real phrases and give
    the tiles room to breathe. Every new preset is one entry in `PRESETS` — the tile list reads from the API (`server.py:980` already sends
    `styles=styles.PRESETS, default_style=styles.DEFAULT`), so a new preset appears in both surfaces with no UI change.

### Chat (built)
- Rail and second column per §4. The conversation keeps AI's gradients and hover/selection; the header matches every other screen's header.

### Settings (built)
- Currently a single column with no second column. Give it the standard header and the standard card treatment; it is a section like any other.

---

## 6. Earlier batches — the redesign (built 2026-10-02)

**Built.** `live.js` (`histCol`, `histRow`, `histItem`, `drawHist`, `ACT.hbx`), `app.js` (`COL2`, `drawCol2`), `studio.css` (`.lv-hrow`, `.c2n`). Where it differs from the plan below:

- The column lists the batches on **Studio and Create** (both are list-bearing; the list is the same in the same place). Library, Pack, Chat and AI keep their own lists; Settings and the full-screen tools (editor, export, prepare, animate) have no column, because they have no list.
- **No button, but still paged underneath.** `GET /api/history` caps a page at 50 because it reads one `result.json` per batch; the column asks for the next page by itself when it is scrolled near the end (and keeps reading pages until every *open* batch is found). Page 1 is read again every 10 s while Studio or Create shows, merged over what is loaded, and the column redraws only when something changed.
- A row is a **button that opens the batch**; the card is in the Studio's main area under the composer (a 392px column has no room for a Studio view). On Studio a second click closes it; from Create it opens the card and goes to the Studio. A row is marked **on** when its card is open and **cur** when it is the batch the Studio works on.
- The grid thumbnail is 26px per cell (a 3x3 is 84px wide) so a row stays a row.

**Today** (`live.js:340-343`, styles `studio.css:348-375`): a block *inside the Create/live screen* (`#ghist`), titled "Earlier batches", a
**vertical stack of horizontal rows** (`.lv-hlist` is already `flex-direction:column`; each `.lv-hitem` is a row: grid on the left, `.lv-hmeta` on the
right, caret at the end), paginated by a **"Load more"** button (`.lv-hmore`).

**Target** (Haitham's ask): every previous generation lives in a **persistent left column, in the same position and at the same scale as the AI and Library
columns**, listed vertically, each entry showing its **3×3 grid, its name and its info**. No "Load more" — the column scrolls.

1. It moves out of the Create screen's body into the shared second column, so it is reachable from every screen and always in the same place.
2. One vertical list, **no pagination.** `GET /api/history` is paged today; the column asks for the full set and virtualises or caps the render (a few hundred
   cards at most) rather than paginating.
3. Each row keeps what it has — `histGrid` (the sheet's own grid via the `--c` custom property, `lv-hnoimg` checkerboard for a cell with no picture) and
   the meta line (`G###`, ready count, animated count, edited time) — but is styled as a **column entry**: grid on top or leading, name and info beneath,
   the same hover / selected / focus states as the AI chat list.
4. **A row opens the batch**, exactly as `ACT.hbx` does now (`live.js:344`), and an expanded card still shows that batch's Studio view (`studioFor`,
   `generate.js:215`) — several may stay open, remembered in `localStorage mirsal.hbopen`. This behaviour is good; only its *place* and *shape* change.
5. A batch that is currently working, or that was just edited, keeps re-reading while it is visible.

**Do not confuse this with `history.js`.** That file is the **watch-folder** screen (`#/history`: `inputs/Images_gen` + `videos_gen`, Remove/Restore). It is a
different thing, it is already a vertical list, `HANDOFF.md` §1 notes nothing in the rail opens it and it once shadowed this very handler. Decide separately
whether to delete it; do not fold it into this column.

---

## 7. What "done" means for this work

- One token set; `--pri` is the accent on every screen; no `#070b1c` island remains.
- Six rail items including AI declared in `app.js`, identical width, position and order on every route; one phone layout (bottom bar) on every screen, not only AI.
- The second column exists on every list-bearing screen and remembers its state.
- Style tiles are compact, honest, and read from `styles.PRESETS`.
- Earlier batches: one vertical column, no "Load more", reachable from anywhere.
- `tests/test_js.py` green (it guards the shared `ACT` names and that every `data-act` button has a handler) — **a redesign that trips it has broken the
  app.** `tests/js/*.test.js` must still pass. No duplicate top-level `const`, no new top-level `ACT.*`.
- Checked in a browser on a **copy** of `out/` (`MIRSAL_OUT=<copy>`, never press Create) — see `HANDOFF.md` §5 for the Playwright recipe and the
  `location.reload()` trap.

## 8. Order of work (done steps are marked)

1. **Done.** Tokens (§3.1) and the rail (§4.1-4.2) — everything else inherits from these. Also done in this step: one phone layout (bottom bar) and one drawer for the second column on every screen (`#c2tog` below 900px; AI's private drawer is gone), AI declared in `RAIL`, the column's glass background and gradient title are the shell's, `body.agent-view` is gone. Guarded by `tests/test_js.py::ShellTests`.
2. **Done.** The second column everywhere (§4.3), then Earlier batches moved into it (§6). Guarded by `tests/test_js.py` and `tests/js/history_card.test.js`.
3. **Done.** Library, Chat and Settings alignment to AI (§5): the glow (`--glow-bg`, a static CSS version of AI's aurora, behind the whole shell so the glass columns sit on it), AI's row hover / selection (`#F0F9FC` / `#E3F4F9`) on the pack, chat and batch rows, one page width and one header (`.page`, `.ph`) for Library, Create, Pack, Export and Settings, the Chat conversation as a glass panel, and the heading-icon size (the Settings Telegram icon used to fill the page). A pack opened by its address now draws its column after the library is read. Guarded by `tests/test_js.py::ShellTests`.
4. The composer's dark panel and the style tiles (§5, Studio).
5. Type/spacing/motion sweep last, once the structure has stopped moving (§3.2).