# docs/design.md — the look of Mirsal: one shell, one palette

**Status: built design; updated 2026-10-11 for the dark/light themes, two-band Home showcase and console feature split.** It is the design half of the app, kept
in `docs/` because it is architecture, not a log (rule 12): the screens are a sandbox over the API (rule 11), but the *shell* they share is a real, stable
surface that every screen inherits. When a screen's look changes, this file changes in the same step.

`docs/backlog.md` "Visual design" carries the work items; this file says what they add up to.

---

## Sections

This is an index: each section is its own file under [`design/`](design/); read only the one a task needs.

| section | what it covers |
|---|---|
| [1. Shared shell](design/01-1-shared-shell.md) | Every screen uses the same rail, palette, typography and responsive layout. Desktop has a 96px rail and, on list-bearing routes, a 392px second column; at wi… |
| [2. Non-negotiables (breaking these breaks the app, not just the look)](design/02-2-non-negotiables-breaking-these-breaks-the-app.md) | No CDN, no runtime fetch (rule 8). One self-hosted family: `console/fonts/InterVariable.woff2` (`studio.css:1`), used by `body` at `studio.css:4`. |
| [3. Foundations](design/03-3-foundations.md) | `studio.css` defines the light palette in `:root`; `theme.css` remaps it under `html[data-theme=dark]` and supplies component overrides. All screens share `-… |
| [4. The shell — rules that hold on every screen](design/04-4-the-shell-rules-that-hold-on-every-screen.md) | 1. The rail is one fixed element in one place. Same width, same position, same order, on all sections. Its width is a token; it does not change |
| [5. Per screen](design/05-5-per-screen.md) | The first screen and the Mirsal logo's target: `#/home`, an empty hash, and the first start of each browser session (`hmFirstStart`, `sessionStorage`; entity… |
| [6. Earlier batches — the redesign (built 2026-10-02)](design/06-6-earlier-batches-the-redesign-built-2026-10-02.md) | Marks and choices (2026-10-05). A particle batch (`kind: particles`) carries the particles mark top-right of its row (`.lv-pbadge`): particles no stick… |
| [7. What "done" means for this work](design/07-7-what-done-means-for-this-work.md) | One token set; `--pri` is the accent on every screen; no `#070b1c` island remains. |
| [8. Built foundations](design/08-8-built-foundations.md) | Shared tokens, the responsive rail and list drawer, aligned Library/Chat/Settings, compact style tiles, type/radius scales, motion rules and per-picture over… |
| [9. Every rejected picture carries its own override (2026-10-03)](design/09-9-every-rejected-picture-carries-its-own-overrid.md) | `CLAUDE.md` rule 10: a rejected picture is never a dead end and never a bare word. This is the design half of that rule. |
| [10. The welcome modal and the particles gallery (2026-10-03)](design/10-10-the-welcome-modal-and-the-particles-gallery-2.md) | Welcome (`welcome.js`, `studio.css` `.wl-*`, `#welcome` above the dialogs at z 80): a card of five pages, the fast-cut ad film then four sliding feature im… |
| [UI/UX pass of 2026-10-03 (what a click means)](design/11-ui-ux-pass-of-2026-10-03-what-a-click-means.md) | The AI vision switch is a chamfered box with a glowing outline (`agent.css` `.ai-vis` around a plain `.ai-chip`: cut corners by `clip-path`, a conic-gradie… |
| [Browser look of 2026-10-03 (what Claude fixed, and what is still Haitham's eyes)](design/12-browser-look-of-2026-10-03-what-claude-fixed-and.md) | P1-P13 and the particle screens were walked in a headless Chromium (Playwright from `mirsal/venv`) on a scratch copy of `out/` (recipe: `docs/dev-notes.md`);… |
| [Personal packs and existing-file controls](design/13-personal-packs-and-existing-file-controls.md) | Every signed-in person sees their own Library packs, Recent and My Stickers, with Trending as a tab. The owner's Library follows the same filter. A pack page… |
| [LLM selector catalog](design/14-llm-selector-catalog.md) | The top-right LLM popup groups eligible listed models under Local, Nararouter and OpenAI, using the server catalog. Saved session choices survive reopen; the… |
| [16. App-audit fixes (2026-10-20)](design/16-app-audit-fixes-2026-10-20.md) | What the 2026-10-19 audit's fixes built: keyboard-reachable tiles (UX-03), named editor controls (UX-04), frame-card focus/Escape (UX-05), phone editors/Save (UX-01), watch-folder rows (UX-09), the Test workspace badge (UX-06), reaction ownership heading and owner names (UX-08/11). |
| [Studio left-panel plan](design/15-studio-creation-sidebar-plan.md) | Proposed: creation settings left, active artwork right; always-open New request, accessible batch history and cyan-accented neutral dark surfaces. Layout not implemented. |
