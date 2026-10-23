# docs/design.md — the look of Mirsal: one shell, one palette

**Last synchronized: 2026-10-23 · `main` · implementation baseline `27009185`.** The saved-price and export-price controls passed desktop/phone checks in both themes; broader owner visual acceptance remains open in the [checklist](../DELIVERY_CHECKLIST.md).

The design half of the app: the shell every screen inherits, the screens, the themes, the welcome modal, and the redesign contracts that guard them. Converged 2026-10-21 (branch `code-audit`); history lives in git. **Read this before changing any CSS, the Studio's markup, or adding a screen.** `docs/backlog.md` "Visual design" carries the work items; this file says what they add up to.

## Shell

- One 96px rail of four — Home · Create · Library · Help (`app.js` RAIL) — with an avatar menu (Settings & health, Team, Trash, Watch folders, Sign out). A shared second column (392px) on list routes; a drawer under 900px, a bottom bar under 760px.
- Create opens the last tab, new and empty. Chat | Studio segmented tabs + a New menu (From a photo, Particle effects, Super reaction).
- One page, one global scope, one `ACT` object, file-prefixed top-level names, hash router (`docs/architecture.md` §6). No CDN, one self-hosted family (`ui/fonts/InterVariable.woff2`, served `/ui/fonts/`). New scripts go in `UI_FILES` (now via `console/assets.py`) and `index.html` in load order, or the page swallows a 404 silently.
- Locked issue colours are never repainted: orange out of bounds, purple green screen, yellow loop, pink look/motion, blue file limit, red blocked or dropped. Checkerboards and export files are unthemed.

## Screens

- **Home** — the logo's target: first start of each browser session opens it; a two-band 24-sticker showcase with the welcome/onboarding films preserved across filter and resize (`home.js`). An empty library shows the most-liked public packs instead of "No packs yet" (shared-only, so the admin's shared current work is the default until likes arrive), opening Trending detail.
- **AI chat** — composer + Chat | Studio tabs, stage slider (Prompt · Stickers · Animation · Telegram · Export), model selectors and creation options as their own controls; box selection; newest-card polling.
- **Studio** — 352px left creation panel (settings + fixed action footer) + artwork workspace + Batches drawer (earlier batches + project map). One control per cell; issue overlays + override queue; sheet/video panels; Prompt tab (what is typed is what is SENT); animation controls + Add-to-pack wizard; sticker detail panel (Checks · History · Measurements). Box selection; batch-grouped pack; sticky sections.
- **Library / pack** — the caller's own packs only (the owner's too); pack page with viewer grid; sticker editor (named controls); selection box with focus-within; counts additive after the visibility filter. The header shows Collection price and Edit price (saved with pack metadata; blank clears, 0 is free). Export to collection prefills that value in a labelled price input; edits there apply to that export only, and blank omits its price. Validation leaves the dialog and entered values intact. No currency is assumed; generation credits remain separate.
- **Reactions** — Emoji | Lottie | Super Emojis | Packs tabs, one shared state. Emoji presets by motion (Assign, Lottie slot export); Lottie-style editor (Particular groups, START, export, `MAX_PARTICLES`); super sandbox `#/super` (desktop frame + iPhone, one-frame tuning); one scoped editor (draft/row/save-as-new); Echo badge/heart/tray for free lookup; wall 120/page, collapsed motion rows, open-only previews.
- **Settings / Help / Users / Trending / Trash** — sticky Settings sections; native support controls; Users > People (approve/reject/admin); Trending gallery; trash rows with Remove/Restore/purge.
- **Audit fixes built in** (2026-10-20): keyboard-reachable tiles (UX-03), named editor controls (UX-04), frame-card focus/Escape (UX-05), phone editors/Save (UX-01), watch-folder rows (UX-09), Test workspace badge (UX-06), reaction ownership heading + owner names (UX-08/11), compact Chat config (UX-10).
- **Personal packs** (unverified against code — verify before building on it): per-person Library filter, Public toggle, Telegram-send hidden for members, Import-pack flows.
- **LLM selector** (unverified): top-right popup grouping eligible models under Local / Nararouter / OpenAI from the server catalog; saved choices survive reopen.

## Rejected pictures (the design half of rule 10)

A rejected picture is never a dead end and never a bare word: on every surface that shows one — Studio tile, clickable sheet cell, chat card, creator message — the picture is visible, one plain sentence says why, and "Use it anyway" / "Take it back" sits on that picture. One bulk control per batch ("Use all anyway (N)" / "Take all back (N)"). A rejection with no picture and no override is a bug.

## Themes

Light tokens in `studio.css` `:root`, dark remap in `theme.css`; preference in `localStorage mirsal.ui.theme` (default dark), applied pre-paint, synced across tabs; sun/moon button top-right + Settings → Appearance.

## Welcome and onboarding

A 5-page modal over Home once per session (fast-cut film + four slides, sound after gesture); media in `console/assets/welcome/` (welcome + onboarding mp4, slides, posters) served with Range. Films: Seedance take 2 (105 credits, take 1 rejected as too slow); on-screen words never spell-checked by anyone but Haitham (W9).

## Redesign contracts (still binding)

- The JSON API, byte for byte. The engine, the gates, the verifier: redesign touches `console/` only. Rule 10 on every surface. No dead stubs, no CDN, one `ACT` + prefix rule, role gates, "Ask before spending" + price on every paid button.
- The rail of four; avatar menu (Settings, Team, Trash, Watch folders, System health, Sign out); every old hash keeps working. Create = Chat | Studio + New menu. Project map (Project › Batch › Sheet › Video), breadcrumb + highlighted node, branch-where-it-stands with priced buttons.
- D1–D7 (Haitham accepted all, 2026-10-11): Project/Batch/Sheet/Video words; project switcher replaces the column; Animate/Add act on the selected batch only ("Animate every batch" in a menu); retire `gbdrop`; rail of four + avatar menu; chat preview lives on the pack; two interfaces, one workspace, one project ("Ask Mirsal" side panel after phase 7, only if Haitham agrees).
- **No action, screen or route may disappear** without a `renamed`/`retired` entry in `mirsal/tests/data/ui_baseline.json` (`tests/test_ui_inventory.py`); the baseline is never regenerated during the redesign. The inventory itself regenerates from `mirsal/mirsal/console/inventory.py`. When markup moves, the selector in the test changes, the behaviour it asserts does not.
- Use code and on-demand screenshots for review; capture local browser artifacts under `output/playwright/`. The former fixed `docs/shots/` set has been removed.


## Browser acceptance toolkit

`tools/acceptance/redesign/` contains isolated browser scripts, not a second review guide. From the repository root, `prepare.py` copies G146 artwork and imports a synthetic 3×3 G156 video into disposable output; its location is written to ignored `output/playwright/scratch.txt`. Start a task-owned server on free port 8797 with that `MIRSAL_OUT`, real CLI/providers/database writes disabled. Never point these tools at real output or :8770.

Use the Playwright CLI skill and `playwright-cli -s=<isolated-session> run-code --filename <script>` after opening the server and taking a snapshot. `sliders.js` covers the eight theme/width cells; `retry.js` busy retries; `reactions.js` both surfaces; `frame.js` the frame editor; `hover-contrast.js` contrast; `defaults.js` fresh 2×2 defaults and unchanged 3×3 fixtures. `extended.js` currently selects one retry cell; restore its width/theme arrays for a full run. Seed nonempty reactions and the synthetic long session in the scratch copy when needed. Screenshots are recreated on demand, not maintained documentation.

Latest pricing/delivery evidence and the single app-review checklist are in [DELIVERY_CHECKLIST.md](../DELIVERY_CHECKLIST.md). The historical October 19 acceptance report is in Git. Technical browser checks do not establish owner visual acceptance or paid-model quality. The separate [film kit](../Motion%20Graphics/README.md) documents rendering, not product acceptance.
