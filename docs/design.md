# docs/design.md — the look of Mirsal: one shell, one palette

**Status: written 2026-10-02 from Haitham's notes after a pass over the running app; built in the order of §8, and §8 says which steps are done.** It is the design half of the app, kept
in `docs/` because it is architecture, not a log (rule 12): the screens are a sandbox over the API (rule 11), but the *shell* they share is a real, stable
surface that every screen inherits. When a screen's look changes, this file changes in the same step.

`docs/backlog.md` "Visual design" carries the work items; this file says what they add up to.

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
bottom-left of the stage (the first Earlier-batches card on Studio). *(Fixed 2026-10-03: while a job is listed `live.js drawLive` sets `body.hasq` and `studio.css` reserves room under every screen's last content, 96px, 172px on a phone; the Library's Create button is no longer sticky, so it never floats over the list.)*

---

## 2. Non-negotiables (breaking these breaks the app, not just the look)

- **No CDN, no runtime fetch** (rule 8). One self-hosted family: `console/fonts/InterVariable.woff2` (`studio.css:1`), used by `body` at `studio.css:4`.
  No second webfont. Icons are inline SVG (`ic()` in `app.js`).
- **One shared `ACT` object.** A second `ACT.name =` in a later script *silently replaces* the first — this already bit the app once (`history.js` replaced
  `hopen`, so "Earlier batches" opened batch NaN). `tests/test_js.py` fails on any clash not listed as intentional.
- **No duplicate top-level `const` across scripts.** The second declaration is not run at all (`history.js` was dead for a while because of `ago`).
- **`agent.css` selectors stay namespaced** (`ag-`, `is-`, `k-`): the Studio's own CSS already uses `.step`, `.tile`, `.sel`, `.done`.
- **Issue colours are locked** (`docs/dev-notes.md`, "Locked decisions"): orange out of bounds, purple bad green screen, yellow bad loop, pink look or motion, blue file / Telegram
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
- **One motion language (Haitham, 2026-10-04: "subtle animations everywhere, like the AI enhancer")** — `studio.css` after the interaction rules: `--ease` (`cubic-bezier(.2,.8,.2,1)`), `mz-in` (the enhancer's .22s rise-and-fade) on what **opens on a click** (dialogs and their backdrop, the stroke menu, the engine strip, the style tiles with a light stagger), soft hover / press (`scale(.97)`) / selected transitions on every touchable element, a 2px lift on cards, a slide on the toast. Never an entrance animation on what the Studio redraws on a timer (batches, rows, tiles, the variations strip, the credits menu): it would replay on every poll. `prefers-reduced-motion` turns all of it off.
  `:focus-visible`**, matching `.lv-hitem` (`studio.css:353`), which is currently the best-behaved rule in the app and should be the template.

---

## 4. The shell — rules that hold on every screen

1. **The rail is one fixed element in one place.** Same width, same position, same order, on all six sections. Its width is a token; it does not change
   shape per route. Keep the icon-over-label form (`app.js:65`) — it is legible at 72px.
2. **The rail has four items** (Haitham, 2026-10-11, `docs/redesign_plan.md` D5), declared in `RAIL` (`app.js`): **Home, Create, Library, Help**, under the
   Mirsal logo, then the credits chip (`live.js`) and **the avatar** (`.rme`, the person's initials) at the bottom. The avatar opens `#rmenu`: **Settings &
   health**, **Team** (`#/users`, owner and admins), **Trash** (Settings' Trash card, `ACT.rtrash`), **Watch folders** (`#/history`, the owner) and **Sign out**
   (a signed-in person on the LAN); Escape or a click outside closes it. `RAILOF` says which item a screen lights: the Create screens (`agent`, `generate`,
   `create`, `effects`, `editor`, `export`, `prepare`) light Create, `pack` / `animate` / `chat` light Library, `settings` / `users` / `history` light the
   avatar. Every old hash still opens. **Create opens the tab used last** (`CTAB`: Chat or Studio).
   **Create's tabs** (`#ctabs`, `drawCtabs`, D7): above `agent`, `generate`, `create` and `effects`, a segmented **Chat | Studio** control and a **+ New** menu
   (a `<details>`) with **From a photo** (`#/create`) and **Particle effects** (`#/effects`); the full-screen tools have none. The chat preview (`#/chat`) is
   reached from the pack and the Library's sticker viewer (D6).
3. **A persistent second column on every screen that has a list** — Library, Chat, AI for sure, and **Studio and Create** because both have real lists
   (Studio: the batches; Create: the pack/prepared sheets). `drawCol2()` (`app.js:73`) stops being an allow-list of four routes. It must be scrollable,
   collapsible, and remember its width; on a phone it becomes a drawer.
4. **Same geometry everywhere:** same gutters, same card radius, same header height, same place the page title sits. If a screen needs to break the
   pattern for a real reason, the reason goes in this file.
5. **The rail scrolls when it must, it never reflows.** "Scaling instead of fixed" means the rail and second column scale with the viewport (fluid widths,
   clamped) while staying the same element in the same position — not a different layout per route.

---

## 5. Per screen

### Home (built 2026-10-10, `home.js`, `studio.css` `.hm-*`)

The first screen and the Mirsal logo's target: `#/home`, an empty hash, and the first start of every browser session whatever screen the tab or bookmark was on (`hmFirstStart`, `sessionStorage`; a link to one thing such as `#/pack/<id>` is kept), with the welcome film opening over it (`ACT.home`; pressing it on Home scrolls back to the top and redraws). Haitham's Higgsfield-style page (`web/mockups/home-library.html`) drawn from the caller's real library (`GET /api/library`, so each person sees their own packs) inside the shell: the rail stays, there is no second column, and the mockup's own top bar is gone because the rail is the navigation. From the top: the counts and a search, the hero (up to three real stickers, newest pack first, its cover first), two feature cards (Explore animation filters the packs; Try particle effects opens `#/effects`), four shortcuts (Create with AI = a clean AI chat, what the logo used to do; Sticker Studio; Bring your own = Import pack for the owner, From a photo for others; Your library), the packs with All / Animated / Static / With particles (a card opens `#/pack/<id>`, a pack sent to Telegram shows its link), How it works with "Watch the film" (the welcome), the footer. Nothing on it is a preview; the mockup's heart "save" and its pack dialog were dropped (no backend, rule 6; the pack screen already exists). Its two headline sizes (`--hm-d1`, `--hm-d2`, scoped to `.hm`) are the only sizes above `--fs-2xl`: a landing page's headlines, not a screen title. Tests: `tests/js/home.test.js`.

### AI (`agent.js`, `agent.css`) — the reference, keep its character (built; styles added under the box)
- Keep: the cyan/glass/glow depth, the gradients, the hover and selection states on the chat list, the new-chat background.
- **Added (Haitham, 2026-10-02): the style tiles under the AI box**, smaller than the Studio's (46px swatches, 34px once a chat has messages), with chips for the style, grid and spending of the next sheet. Details in `docs/agent-and-chat.md`.
- **Change:** it stops being a special case. Its tokens move to `:root` (3.1) and its rail becomes the standard rail (4). Its second column stays.

### Library (built)
- **Particles tab:** each set is a box card in a grid (`.ps-lib`), and a click on the card itself opens or closes it (`.ps-hit`, pointer cursor; no Open button); the opened card spans the row. **My Stickers** is one box per pack (`.lib-pk`, the pack's name, count and Open pack) inside one selection area, so a drag box still crosses packs. **Trending** cards keep the like and comment count on the card's bottom-left, whatever the name's wrap (`.tr-meta` `margin-top:auto`). (Haitham, 2026-10-05.)
- **Sticker details** gains one field: **Edited outside the app** (file picker + Replace, Undo when there is a previous file): same dialog, existing `.fld`/`.row`/`.btn` classes, no new styles.
- **Rail:** identical to AI's, same scaling, same persistent position — this is the explicit ask.
- **Sticker library gets the same glow background as AI** so the two screens read as one app.
- Keep the rail's fonts, backgrounds, hovers and selection states **character-identical** to AI's. If a value differs between the two, AI wins.

### Studio — "this is where it becomes dirty" (built)
- **Prepared batches** wear a small `keychip` ("Prepared", owner/admin only) beside the Blue key chip; the header says "prepared sheet, 0 credits" with a **Make a new one** button (live price) next to Create more. A sticker whose animation predates its picture says so on its tile with an **Animate again** button; the open view has **Replace file** / **Take back** beside Edit. All existing classes (`.keychip`, `.btn`, `.gwarn`), no new styles.
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
- Currently a single column with no second column. Give it the standard header and the standard card treatment; it is a section like any other. People moved out of it to Users (2026-10-04): Settings keeps "Signed in as" and, for staff, one line that opens Users. Staff also get a **Prepared sheets** card (Turn on/off; `MIRSAL_PREFER_PREPARED` in `.env` wins when set).

### Help (built 2026-10-05, `support.js`, `.su-*`)
- **Its own section at the end of the rail** (icon `help`). A red dot (`.rdot`) shows on it while a notification is unread. Everyone has it.
- **The second column** is the person's issues (title, a state chip, time) and, below them, their notifications. A new question is the `+` in the header. Staff get three tabs at the top: My issues, Queue and FAQ review.
- **The stage** is one conversation: the person's messages on the right and the agent's and admin's on the left (the Chat's bubbles; an agent bubble in `--glass` / `--aline`, an admin bubble in `--pri-l`).
  - Under an answer sit the help entries it read, as small chips; an FAQ chip opens the entry.
  - Then one bar that says what can be done now: "Did this solve it?" Yes / No, Send to support, Attach a screenshot, Waiting for support, Support replied, or Resolved + Reopen.
  - The box at the bottom takes text and a screenshot (📎, or Ctrl+V).
  - The state chips are cyan (answered), amber (waiting), blue (replied) and green (resolved).
- **Staff**:
  - The Queue shows the ticket over the person's conversation, with the screenshots and "Vision model saw" in a wash box. Reply keeps it open; "Reply and resolve" closes it, and the line under the buttons says so.
  - FAQ review shows the published text in a grey box above the proposal's fields, then Save edits, Discard, Publish and Archive.
- Settings keeps one card: for a member, a link to Help; for the owner, the caught failures (Tickets) with a link to the support queue.

### Users (built 2026-10-04, `users.js`)
- **Its own section, Team in the avatar menu** (§4.2; it was a rail item until 2026-10-11), because People in Settings was a cramped list of one-liners with no usage. The **second column is the roster** (a list, so §4.3 applies): an avatar initial, the name, role · status · credits spent · batches, with two rows of filter chips (status, role); the selected person is the `.on` row, the chart icon in its header returns to everyone.
- **The stage** shows the totals (stat tiles, two 30-day bar charts, worked-vs-failed jobs, then People management: add, requests, approve, roles, passwords, credits, Answered lately) or one person: the management card (`AUV.requests` + `AUV.person`), stat tiles, the two charts, jobs with cost against estimate (a cost over its estimate in `--run`), the ledger (folded), and their work by family with prompts (folded) and 64px thumbnails linking to the WEBM when animated.
- **The graphs are hand-drawn SVG** (`UV.bars`, `UV.split`): one rect per day on `--pri` (spend) and `--ai` (batches), an empty day a 1px hairline, the day and value in each bar's title; worked / failed is one split bar in `--ok` / `--bad`. No chart library (rule 8). Stat tiles use the glass depth (`--glass`, `--aline`) like AI.
- **A member** has no Team in the avatar menu (Haitham, 2026-10-05: Users is for the owner and admins). Their own page, **My usage** (their numbers only, no management card), opens from the **My usage** button in Settings, on the "Signed in as" card.

---

## 6. Earlier batches — the redesign (built 2026-10-02)

**Marks and choices (2026-10-05).** A particle batch (`kind: particles`) carries the **particles mark** top-right of its row (`.lv-pbadge`): particles no sticker owns, still usable and exportable. The composer has a **Particles** switch before the AI enhancer (docs/particles.md section 8). The Library's Packs column shows a batch group as one row led by its **parent pack** (Add to a pack > **Assign as parent**, `lead_at`; else the group's first pack) with a fold that stays as the person leaves it; Add to a pack preselects the pack that already holds the batch, so animations upgrade it instead of making a second pack; a second pack made before that folds back with **Merge into parent** on its row (`POST /api/packs/{id}/merge`).

**Built, then simplified the same day (Haitham: showing several batches at once in the Studio is not good).** `live.js` (`histCol`, `histRow`, `drawHist`, `ACT.hopen`), `app.js` (`COL2`, `drawCol2`), `studio.css` (`.lv-hrow`, `.c2n`). Where it differs from the plan below:

- The column lists the batches on **Studio and Create** (both are list-bearing; the list is the same in the same place). Library, Pack, Chat and AI keep their own lists; Settings and the full-screen tools (editor, export, prepare, animate) have no column, because they have no list.
- **A click on a batch presents that batch, and only that batch** (`ACT.hopen`, the same action as the credits pill's recent batches): the Studio's session becomes exactly that one batch and the Studio shows its own view of it, from any screen. The stacked open cards, their open-set, their localStorage key and the per-card copy of the header, views, bar and element ids (`studioFor`, `CT`, `gcardview`, `scopeGens`, the `pfx` ids) are deleted. Under the view, the batch's own per-sticker history and AI captions stay (one block per batch of the session, which is one unless Create more was used).
- **No button, but still paged underneath.** `GET /api/history` caps a page at 50 because it reads one `result.json` per batch; the column asks for the next page by itself when it is scrolled near the end. Page 1 is read again every 10 s while Studio or Create shows, merged over what is loaded, and the column redraws only when something changed.
- A row is marked **on** when it is the batch the Studio presents.
- The grid thumbnail is 26px per cell (a 3x3 is 84px wide) so a row stays a row.

**Plan as first written (kept for the reasoning; the bullets above win where they differ):**

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
4. ~~A row opens the batch as a stacked card, several at once~~ — dropped: a row presents the one batch in the Studio (see the built note above).
5. A batch that is currently working, or that was just edited, keeps re-reading while it is visible.

**Do not confuse this with `history.js`.** That file is the **watch-folder** screen (`#/history`: `inputs/Images_gen` + `videos_gen`, Remove/Restore). It is a
different thing, it is already a vertical list, `docs/waiting-for-haitham.md` (W34) notes nothing in the rail opens it and it once shadowed this very handler. Decide separately
whether to delete it; do not fold it into this column.

---

## 7. What "done" means for this work

- One token set; `--pri` is the accent on every screen; no `#070b1c` island remains.
- Six rail items including AI declared in `app.js`, identical width, position and order on every route; one phone layout (bottom bar) on every screen, not only AI.
- The second column exists on every list-bearing screen and remembers its state.
- **The Animation tab is a studio of its own** (Haitham, 2026-10-04: it used to say there was nothing to see while the controls lived on Stickers). Before any animation exists each batch shows the video sheet that will be sent (the server's preview of the kept stickers), the sheet panel with the model, price and Generate, the editable video prompt with the Prompt tab's footer, and each kept sticker with motion suggestion chips that add a line to that prompt (`generate.js` `animCreate`, `ACT.ganmo`). A prepared-video batch keeps its Animate view.
- Style tiles are compact, honest, and read from `styles.PRESETS`. **They are hidden until the Style chip in the composer bar is clicked** (Haitham, 2026-10-04: always-open tiles took three rows, each as tall as a sticker); picking one closes them and the chip names it (`composer.js` `ACT.cpstyles`, `cpstylepick`). The AI enhancer's engine control under the bar is one compact strip (segment + model drop-down; the cost note is its tooltip), and it reappears every time the enhancer is turned On again.
- Earlier batches: one vertical column, no "Load more", reachable from anywhere.
- `tests/test_js.py` green (it guards the shared `ACT` names and that every `data-act` button has a handler) — **a redesign that trips it has broken the
  app.** `tests/js/*.test.js` must still pass. No duplicate top-level `const`, no new top-level `ACT.*`.
- Checked in a browser on a **copy** of `out/` (`MIRSAL_OUT=<copy>`, never press Create) — see `docs/dev-notes.md` for the Playwright recipe and the
  `location.reload()` trap.

## 8. Order of work (done steps are marked)

1. **Done.** Tokens (§3.1) and the rail (§4.1-4.2) — everything else inherits from these. Also done in this step: one phone layout (bottom bar) and one drawer for the second column on every screen (`#c2tog` below 900px; AI's private drawer is gone), AI declared in `RAIL`, the column's glass background and gradient title are the shell's, `body.agent-view` is gone. Guarded by `tests/test_js.py::ShellTests`.
2. **Done.** The second column everywhere (§4.3), then Earlier batches moved into it (§6). Guarded by `tests/test_js.py` and `tests/js/history_card.test.js`.
3. **Done.** Library, Chat and Settings alignment to AI (§5): the glow (`--glow-bg`, a static CSS version of AI's aurora, behind the whole shell so the glass columns sit on it), AI's row hover / selection (`#F0F9FC` / `#E3F4F9`) on the pack, chat and batch rows, one page width and one header (`.page`, `.ph`) for Library, Create, Pack, Export and Settings, the Chat conversation as a glass panel, and the heading-icon size (the Settings Telegram icon used to fill the page). A pack opened by its address now draws its column after the library is read. Guarded by `tests/test_js.py::ShellTests`.
4. **Done.** The composer's dark panel and the style tiles (§5, Studio): the panel is the shared glass surface (`--glass`, the aurora halo, `--aglow` focus ring), no navy hex is left in `studio.css`; the tiles are 104px wrapping squares with a ring and a check, twelve presets (Minimal, Pixel art, Watercolour, Paper cut, Pop comic, Kawaii added; one entry each in `generation/styles.py`), and the swatch (`console/placeholders.py`) is an abstract orb drawn the way the style looks, derived from the id for any preset with no art. Real tile art still wins: drop `<id>.png` into `console/assets/styles/`. Guarded by `tests/test_js.py::ShellTests` and `tests/test_style_tiles.py`.
5. **Done.** Type / spacing / motion sweep (§3.2): `:root` carries six type steps (`--fs-xs` 11.5, `--fs-s` 12.5, `--fs-m` 14, `--fs-l` 16, `--fs-xl` 20, `--fs-2xl` 24), the radius scale (`--r-s` 8, `--r-m` 12, `--r` 16, `--r-l` 24, `--r-pill`) and `--gutter`; every `font-size` and `border-radius` in `studio.css` and `agent.css` was snapped onto them (so 13px became 14, page titles 22 became 24, a 10px radius 12), the classes that lacked a hover got one, one `:focus-visible` ring covers every button / link / select, interactive elements share one transition, and `prefers-reduced-motion` switches transitions off. Inline `style="font-size"` in the scripts is not covered. Guarded by `tests/test_js.py::ShellTests`.
6. **Built:** the rejection surfaces retain per-picture overrides, bulk allowance and locked technical marks. Particle sets now belong to stickers; owner galleries, trash/restore and the shared burst maker are documented in `particles.md`. The compact editor, rows of saved versions and animated sprites are built and accepted (2026-10-04).

## 9. Every rejected picture carries its own override (2026-10-03)

`CLAUDE.md` rule 10: a rejected picture is never a dead end and never a bare word. This is the design half of that rule.

- **One control, wherever the picture is.** A rejected sticker shows the picture, one plain sentence, and `Use it anyway` / `Take it back` **on that picture** — the Studio tile, a cell of the left sheet, the chat tile. Not a separate panel, not a dialog: the button is on the thing it decides about.
- **The sheet is clickable.** The left sheet already draws every cell's rectangle, cut lines, index and issue mark, so a rejected cell must be as clickable as its tile: a full-cell hit area, `pointer-events` on the mark, the same hover and tooltip, the same `aria` treatment. Clicking allows or takes back; clicking elsewhere on the cell opens the tile.
- **One bulk control per batch, per kind**, above the grid: `Use all anyway (N)` / `Take all back (N)`, N counting what is allow-able **now** (never everything). Same pair on the chat's creator card.
- **The locked issue colours carry the meaning** and are not repainted: a Python-rejected sticker is red, hatched when it is not in the set, solid with a check when it was allowed by the person. An override that has been given reads "allowed by you", not "ok" — the record is visible.
- **A technical block says why and offers nothing.** When Telegram's own limits (format, size, codec) or an empty cell stop something, the sentence names the limit and no allow button appears: that is a rule, not a dead end, and it must read as one.
- **The picture is never hidden by the verdict.** A vision-model rejection dims nothing and hides nothing; the sticker stays in the carousel with its reasons listed, whatever the run does next.
- **A rejected cell wears the locked marks, in red**: hatched and faded while it is not in the set, solid with a check once a person allowed it. The hatch and the fade are the record, so an override is visible on the sheet without opening anything.
- **The sheet's cells are hit areas** (built 2026-10-03, `better_ui/ux`): allow-able cells carry the allow click (still or animation, per stage), any other cell opens the tile, and an allowed cell that can be taken back carries that click instead. The hover names the plain-words reason, plus the final sentence when nothing can be allowed. Every hit rect is `tabindex`/`role="button"` with an `aria-label`, and Enter or Space presses it (a rect answers neither key by itself). Unmarked cells get an invisible hit rect, visible on hover.
- **The chat tile carries the same button per kind**, and the creator's card carries the bulk pair per kind with honest counts. **A blocked chat tile is never dimmed**: hatched red while it is not in the set, a solid red wash with a check once a person allowed it, and "allowed by you" reads as a visible record. No button ever appears without the server's word on it.

---

## 10. The welcome modal and the particles gallery (2026-10-03)

- **Welcome** (`welcome.js`, `studio.css` `.wl-*`, `#welcome` above the dialogs at z 80): a card of five pages, the fast-cut ad film then four sliding feature images, dots that double as a progress bar (a slide advances itself after 6.5 s until the person touches it; the film advances when it ends), arrows, Esc, ← →, "Skip", and "Don't open this when the app starts" (`localStorage`, a per-viewer convenience). **Sound is on by default.** A browser only plays sound after a gesture: when the modal opens from the logo (a click) the film plays with sound; on the very first load the browser refuses, so the film plays muted with a 'Tap for sound' hint and the first tap or key inside the modal turns the sound on (`WL.needTap`, `wlUnlock`). It opens once per browser session (`sessionStorage`) over Home, and from Home's "Watch the film"; the Mirsal logo opens Home (2026-10-10, `home.js`), no longer the film. Text sits on the calm left 34% of each 16:9 image; under 760 px the text moves under the image. `prefers-reduced-motion`: no autoplay, no auto-advance. Media: `console/assets/welcome/`, served by `GET /assets/welcome/<name>` with Range. The prompts and the spend are in `docs/onboarding.md`.
- **Particles:** one editor entered from a sticker, a batch, a pack or a target picker; entering always starts a **new version**. Three equal cards: **Sprites from the sticker** (free), **AI image sprites** and **Kling animated · from scratch** (price on the button, Retry price for an unknown quote). Sprite selection, one preview, presets and **Energy / Float / Swirl / Size** lead to **Save** (the next row, or replace this row) / **Save as new** / **Render → Add to pack → In pack ✓**. A sticker window lists its rows v1, v2...; a batch's Particles section lists each version once (`particles.md` §3, §5).
- Reminder that bit twice: the console scripts share ONE global scope, so a top-level `const` / `let` that two files declare kills the second file (`const PT` in `packs.js` clashed with `let PT` in `generate.js` and the pack screen did not load). Prefix every new top-level name with the file's own.

The sticker window's bottom gallery presents **sets or source runs**, each with a sprite strip and Open in simulator. A slice does not receive a separate pack-like card. Runs already imported into an owned set link to that set rather than suggesting another import. Raw-clip compatibility actions stay collapsed. This grouped display and the lightbox's actual async load target are under browser acceptance; legacy raw-cell cards are not the intended primary flow.



## UI/UX pass of 2026-10-03 (what a click means)

* **The AI vision switch is a chamfered box with a glowing outline** (`agent.css` `.ai-vis` around a plain `.ai-chip`: cut corners by `clip-path`, a conic-gradient outline that rotates while the choice is undecided and rests under reduced motion, a soft drop-shadow on the wrapper because a clip-path would cut a shadow on the button itself). It once looked squashed because it reused `.ai-sw`, the 44x26 px settings toggle with its knob; a chip never takes a toggle's class. Decided, it keeps the box and says "AI vision on" / "AI vision off".
* **A choice with two values in the chat bar is one click-toggle chip** (the sheet size: `<button type="button" class="ag-chip ag-grid" data-act="aggridtoggle">`, labelled "3×3 sheet" / "2×2 sheet", its title says both choices and "Click to change"). It is a native button, so it is keyboard-reachable; a press writes the setting only (no generation, no chat turn), is reversible, and repaints from the saved setting, the gear's pair included. It once was a `<select data-aggrid>` inside `.ag-sel`; that class is the settings panel's full-width drop-down and stretched the chip over its own row, so the chip has its own class `.ag-grid` (`agent.css`). `docs/agent-and-chat.md`, "The bar under the chat box".
* **The stage slider** (2026-10-11, reworked twice the same day after Haitham's look: a pill first, then "use Claude's thinking slider, flat, in Mirsal's colours"; `agent.js` `AIU.stageHTML` / `drawStage` / `stageDetails`, `agent.css` `.ag-stage*`, `.ag-mini`, `.ag-range`, `.sp-*`): how far a new request goes. **Closed it is one small grey pill** left of Send: a tiny track filled to the current stop, its name and a caret ("▬ Stickers ▾"). **A click opens a panel above the box** with *Goes as far as* and **a real slider**: a range input with a white round thumb on a thin track that fills Mirsal blue up to the stop, five tick dots, the five names under it (**Prompt · Stickers · Animation · Telegram · Export**, each also a button), and one line saying what the chosen stop does. Dragging names the stop live; **letting go picks it and closes the panel**; the arrow keys pick and keep it open, Enter or Esc close. Then *Models* (Chat, Stickers, and Video from Animation on; "Default · <name>" first; the chat's own `settings.models`) and *Options*: **Stickers: Creative · Predefined** (`settings.actions`, below), Sheet 3×3 / 2×2, "Approve everything for me" from Animation on, "Ask before spending". Every pick writes the settings route and makes no chat turn. Test: `tests/js/chat_stage.test.js`.
* **The Studio's journey** (2026-10-11, redesign phase 2; `generate.js` `stepsHtml`, `studio.css` `.gsteps`): the old six-box step strip is one slim pill track of stops, Idea · Prompt · Stickers · Motion · (Particles, `particles.js`) · Pack · Telegram. A stop is a 22px dot (a number, a check when done, `!` for a warning, a spinner while working) and a name with a one-line status under it; the open view is the white pill. Each stop is the view it always opened (`gtab`); Pack is the Add-to-pack wizard (`gadd`); Telegram opens the pack once the batch is in one (`gopenpack`). Under 900px the status lines hide and the track scrolls.
* **The project map** (2026-10-11, redesign phase 4; `projmap.js`, `studio.css` `.pm-*`): the Studio's left column, read in one call (`GET /api/generations/{id}/map`). At the top the **project switcher** (the first sheet's picture, "Project", the title, ▾) opens the list of every project, which is the old Earlier-batches list renamed **Projects** (`live.js`: paging by scroll, drag a batch onto another to put it in that project, Removed batches; a ← goes back to the open project). Under it the request in two lines, then each **batch** ("BATCH 1" and its title; ⋯ "Move to its own project") with its **sheets** as a thin tree: a 40px picture, the label (First try / Edited / Redo / Joined, ★ the main one, "· new prompt" when its prompt differs), the G### and the counts, or "Being made…" / "Failed" / "Not cut" in the status colours. The open sheet is the blue row with a blue rule; its ⋯ holds Make this the main sheet, Make it its own batch, Move to another batch…, Report a problem, Remove (red). Under a sheet its **videos** (30px picture, "Video A1", "in use" in green; Use and × on the open sheet), a running job ("A video is being made…"), and on the open sheet the **branches** as quiet blue text buttons: + Make a video / + Another video of this sheet (the Motion view), + Another sheet, same prompt, + Change the prompt, then a new sheet (the Prompt view). "+ Next batch" ends the map. Above the Studio's header a **breadcrumb**: Project › Batch n › Sheet (› Video A1 in the Motion view); the project name opens the list.
* **The Studio's toolbar** (2026-10-11, redesign phase 5; `generate.js` `gview`, `studio.css` `.gh-*`, `.gseg`): the header of a batch is one quiet row. Left: the title (20px) with "N batches · outline · prepared" under it. Right: the view switch **Stickers · Sheet · Both** (`gvmode`, remembered in localStorage `mirsal.view`; Both, the sheet beside the tiles, is the default, as before), Background, a small Size slider, **Next batch**, and ⋯ (Make a new one, Move to another batch…, Download .zip, Export to collection, Report, Remove batch in red). Sheet shows the whole sheet panel wide (its views: raw / keyed / fixed, To send, Video, with every cell's override on it); Stickers shows only the tiles, each with its own override. Full analysis stays a dialog from the sheet panel.
* **The sticker panel** (2026-10-11, redesign phase 6; `generate.js` `gmodal`, `studio.css` `#modal.side`, `.gm-*`): a click on a tile opens the sticker's detail docked on the right (460px, the whole height; on a phone the whole width above the bottom bar), with no dim: the Studio stays usable beside it and, from 1180px, makes room for it. A click on another tile switches it; ‹ › and the arrow keys browse; Esc, × or leaving the Studio close it. Its content is the modal's, unchanged: the name and tags, the id, Edit / Replace file / Take back, the issues, Sticker and Animation one under the other, Edge, the sticker's own override, and three **tabs**: Checks (a red dot when one failed; "Show every check"), History (every decision, newest first), Measurements. The slide-in plays once, when it opens.
* **The density pass** (2026-10-11, redesign phase 7, Haitham: "everything looks big and clunky", the redesign mockups are the reference; the last block of `studio.css`): every screen keeps its gradient background (`--glow-bg`; Haitham asked for the gradients back the same day), cards lose their shadow, buttons are a little tighter (7×13px, weight 550), the big buttons are 38px pills. The Studio's composer (the Idea step) is one quiet white box: no halo, a 28px logo, the prompt in 16px (was 24px), 36px pill chips, 72px style cards, a 38px blue Generate pill. The bottom bar is a floating pill (the counts, then the ONE main button for the state: Animate / Add N to a pack / Open pack), centred 14px above the bottom.
* **The pack screen** (2026-10-11, redesign phase 8; `packs.js` `drawPack`, `studio.css` `.pk-head`, `.pk-tabs`): a breadcrumb (Library › the pack), then ONE header row: the 64px cover, the name (20px) and "N stickers · N animated · a Telegram set takes up to 120", and the buttons, **Send to Telegram** first (blue, the owner only), Preview, Download .zip, **Try it in a chat** (`#/chat`, decision D6), Add sticker, and ⋯ (Rename, Share to Trending, Export to collection, Delete pack in red). Under it two tabs, **Stickers** (the grid, its selection bar and drag to reorder, as before) and **Particles** (the particle studio of the pack, `pkPsHtml`); the tab is remembered while the same pack stays open (`pktab`).
* **Settings** (2026-10-11, redesign phase 9; `app.js` `RENDER.settings`, `studio.css` `.set-page`): titled "Settings" (the avatar menu's item still reads "Settings & health"). Under the title a sticky **section bar** (Account · System health · Prepared sheets, staff only · AI · Telegram · Trash; `setgo` scrolls to the card), then the cards as before, each with its heading. The mockup's Spending section (daily limit, jobs at the same time) is NOT drawn: those are `.env` settings with no route to change them, and a control nothing reads is a dead stub (rule 6); `docs/backlog.md` holds it.
* **The chat restyle** (2026-10-11, redesign phase 10; the last block of `agent.css`): the AI screen keeps its gradient background, glow, dot grid and gradient greeting (Haitham asked for them back the same day); the prompt box, cards, chips and the settings popover are white with a hairline; your own message is a pale blue bubble; Send, the plan's Go and the primary chips are Mirsal blue; the stage slider's accent is blue. The AI-vision chip keeps its rolling highlight on purpose (the one place that asks for attention).
* **The polish** (2026-10-11, redesign phase 11): the shared `--glass` token is flat white, so every surface that used it (Library packs, Trending, the pack's particle rows, particle effects, Help's agent bubbles, the welcome film's buttons, the chat preview) is a white card with its hairline; the side column is flat white; its title is plain ink at 20px; the project list's pictures are 44px. Home is Haitham's own design and is unchanged.
* **Creative or Predefined** (2026-10-11; `tasks.preview(actions_mode)`, the chat's `settings.actions`, the Studio composer's `cpactions` chip, remembered in localStorage `mirsal.actions`): **Creative** (the default) is the plan as before, nine stickers the AI (or the built-in mood list) invents for the idea. **Predefined** takes the first nine of the 36 bank actions (`actions.ACTION_BANK`: happy, laugh, cry, sad, love, angry, wink, kiss, surprised …) drawn as the whole character, and the next batches continue through the 36 the way Next batch always did. An emoji pack (faces) and a named grid ("core-v1") are the 36 already, and a transformation writes its own cells, so for those the switch changes nothing.
* **The chat's style collapses to the chosen one** (2026-10-11): the style tiles show until a style is picked; then only the chip with the chosen style stays (its thumbnail, its name, ▾); the chip opens the tiles again. The Studio's composer already worked this way (`cpstyles`).
* **The batch follow-up is chips, not a new component** (2026-10-09): Regenerate · Batch 02 · Batch 03 · Batch 04 are ordinary `.ai-chip` buttons under one assistant message, each stating its price; the plan card's header and a generation card's header carry "Batch 01 of 04 · core" / "Batch 02 · social" in their existing `<small>` line. No new class, colour or size.
* **Generate prompt is free and says so.** The Studio's primary button reads "Generate prompt" with a "free" chip. The paid step is a second, separate button, "Generate sheet", in the pre-batch Prompt step, and the Higgsfield price is its own line above it, never inside the button. It reuses the Prompt tab's editor and the five-step strip (Request done, Prompt current, the rest "after the sheet"); no new type size, radius or CSS. A person who cannot get a price sees "price unavailable" plus a Retry, never a silently disabled button.
* **The AI enhancer shows the AI screen's engine control** (2026-10-03). Under the composer bar, while the enhancer is On (or cannot run), the Auto / Local / Cloud segment, the local-model drop-down and the one status line are the AI screen's own rows (`.ai-set.cp-eng` reuses `.ai-set .r`, `.ai-seg`, `.ag-sel` flat instead of floating), with the honest note "Local: free. Cloud: one small OpenAI call." The line under the Prompt step's title about the enhancer is `.gdnote` (a quiet note; `.gdnote.bad` in the warning colour when the model failed and the built-in prompt is shown). No new type size or radius.

* **Download .zip** sits in the batch header beside *Add to group* and *Report* (a plain `btn` link with the download glyph, like the pack page's), once the batch's stickers are made (2026-10-05).
* **Remove batch** sits in the batch header beside *Create more* (`btn dng`, trash glyph, like *Delete pack*); its confirm names the batch and says it moves to the trash. **Removed batches (N)** is a folded list under the Earlier-batches column, each row with a **Restore** button (`.c2rem`).

* **The Studio menu says nothing it cannot back** (2026-10-03). The empty prepared-sheets row prints nothing: it never names a folder (`inputs/Images_gen` is a watch-folder name, rule 9), and the other doors into a sheet are already on screen as real controls (the prompt box, the Earlier-batches column, the rail's *Create > Particle effects*). No *Prompt preview* sits under the box (internals such as template ids and `expanded_by` are not for a person). The settings under the box are the composer's own chips (`composer.js` `cpDrawBar`: model, Stroke, Loop, AI enhancer; `composerMount` removes the old *White outline* pills whenever the composer mounts), so the Studio screen has one settings block, not a lookalike.

* **A cell of the sheet does one thing** (allow / take back / include / drop) and never opens a tile; the thumbnail on the right opens it. `Use it anyway`, the tile's x / + and the sheet cell are one control (`docs/engine-and-studio.md`, "One control per cell").
* **One picture per batch** in the Earlier-batches column (the first sticker with a picture), never the sheet's 4 or 9 cells.
* **The id is its own control**: `G103/S2` is a small hoverable, copyable chip beside the name, never inside it. Title, key and id are three fields.
* **A one-time decision is a switch, not a button of the plan**: the AI vision switch sits on the right with a conic glow (`@property --ag-ang`, at rest under reduced motion).
* **Delete pack** is a labelled button with an honest confirmation. **Fixed** is a third view of the sheet.

## Browser look of 2026-10-03 (what Claude fixed, and what is still Haitham's eyes)

P1-P13 and the particle screens were walked in a headless Chromium (Playwright from `mirsal/venv`) on a scratch copy of `out/` (recipe: `docs/dev-notes.md`); Haitham has not looked (`docs/waiting-for-haitham.md` W1). What the walk found and fixed, as rules:

* **A console script must be in `UI_FILES` (`console/server.py`) and in `index.html` in load order.** `sheet-recovery.js` and `job-recovery.js` were missing from `UI_FILES` (the page got a 404 it swallowed, so the recovery controls never drew); `trash.js` loads before the Settings card needs it, so the Trash card draws on first open.
* **Particle entry never guesses an unrelated pack or saved run.** Sticker, batch and pack actions pass explicit target scope; Library asks for the target first. Approve as a pack returns to that batch's editor. Continue is explicit and restricted to matching scope. New set rejects stale async replies. The burst maker lights the chosen preset, then the set default, then `burst`.
* **A blocked animation keeps its finished clip**, dimmed (`.gt.nx`), with the reason and the *Use it anyway* button laid over it (`gblockover`).
* **The key-colour header says the truth**: "Blue screen" / "Green screen" (and "Blue screen & cuts") follows `key_colour`, never a fixed word.
* **Generate prompt gives visible feedback**: the pre-batch Prompt step scrolls into view when it opens, and the button is disabled while the free planner runs.
* **The editor's Save tooltip names where it returns** (the AI or the Studio) when opened from the chat.
* **The Trash card lists a batch by its subject** as well as its number.
* **The bulk "Use all anyway (N)" / "Take all back (N)" buttons are guarded while the re-cut runs**: they disable, read "Cutting again...", and a second click is ignored instead of answering `409 busy`.
* **Remove batch leaves no empty edge strip** (the bordered bar is emptied and loses its class when no batch is open).
* **The Queue pill reserves room at the foot of every screen** (`body.hasq`), so it no longer overlaps the Create button.

Still open from the walk (not fixed, all in `docs/waiting-for-haitham.md`): an empty "New chat" made by a setting click (W22), a chat edit of an animated sticker opening Prepare, "undo" with no "redo", and a bare "the last one" with no person planning a new batch (W23).

## Personal packs and existing-file controls

Every signed-in person sees their own Library packs, Recent and My Stickers, with Trending as a tab. The owner's Library follows the same filter. A pack page has a Public toggle; public cards and details show maker, views and uses. Members can add their batches to their own packs, download them and copy public packs; their Telegram-send button is hidden. The owner and admins can remove a public pack from Trending.

The existing Studio composer adds Use my own sheet and Import from Higgsfield for the owner. The import dialog asks for a file and optional description; videos name the approved destination batch/sheet, or leave it empty to become a batch of their own. The Library's **+** on Packs asks *New pack* (a name, as before) or *Import pack* (owner only: a sheet or a video with no destination; it is cut, a video also animated, and the Studio opens on the batch waiting for review). Provider history distinguishes Import from Open existing. Interrupted imports offer a free Retry import. A file that names a failed provider job offers "Is this the result of …?" (the person's own failed jobs, prompt + time + thumbnail, or Import as a new batch). A replaced pack sticker offers Update in the other packs that hold the same batch sticker. It uses the existing dialog, button and field styles; no new screen or palette is introduced.
