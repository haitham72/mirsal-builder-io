# Dark mode — black and cyan blue

Status: planned, not implemented. Reviewed and finalized against the real code on 2026-10-11 (independent review); implementation starts when Haitham asks. This plan stays on `edit-design`; the current implementation is merged into `main`. Haitham requested an elegant, clean Higgsfield-inspired interface with black surfaces and cyan blue accents.

## Direction and scope

Use [Higgsfield](https://higgsfield.ai/) for the compact creation navigation, media-first grid and restrained controls. The black/cyan palette below comes from Haitham's brief; this is a Mirsal theme, not a claim of pixel-for-pixel reproduction. Keep Inter, the existing inline SVG icons and the shared spacing/radius scale. Use calm surfaces, fine borders and clear hierarchy. Cyan marks the main action, selection and keyboard focus; avoid large glowing backgrounds and purple auroras in dark mode.

Cover Home, Chat, Studio, Library, packs, photo creation, effects, editor/export tools, Settings, Help, Team, Trending, the queue, popovers, dialogs, onboarding and LAN sign-in/approval cards. The rail of four, Create tabs, routes, model selection, spending controls and every existing action remain functional. Issue colours keep their meanings and require accessible text/icons alongside colour. Media, exported pixels and explicit preview-background choices keep their actual colours.

Home keeps its two sticker rows followed by the full-width film crop. Theme the tile surface and labels while preserving the shared grid row height, responsive columns, `object-fit:cover`, reduced-motion poster and full-film opening.

## Proposed tokens

| Role | Dark value | Existing token / use |
|---|---|---|
| Page | `#080A0D` | `--bg` |
| Card / rail | `#111419` | `--sf` |
| Elevated surface | `#181C22` | new shared raised-surface token |
| Input / hover | `#20262F` | `--fill` |
| Border | `#2A3039` | `--bd` |
| Text | `#F1F5F9` | `--tx` |
| Secondary text | `#A7B0BE` | `--mut`; choose `--mut2` after contrast measurement |
| Cyan action | `#22D3EE` | `--pri`, cyan family aliases |
| Cyan hover | `#67E8F9` | explicit hover token; do not assume `--pri-d` means darker |
| Selected wash | `#12313B` | `--pri-l`, `--pri-l2`, `--wash` |
| Text on cyan | `#071015` | new primary-button foreground token |

Treat these as concrete starting values. All mapped tokens exist today in `studio.css` `:root` (`--bg`, `--sf`, `--fill`, `--bd`, `--tx`, `--mut`, `--mut2`, `--pri`, `--pri-d`, `--pri-l`, `--pri-l2`, `--wash`, `--ink`, `--ink2`, `--ink3`, `--glass`, `--aline`, `--aglow`, `--viol`, `--glow-bg`); the two `new` rows have no token yet. Measure final text pairs against WCAG AA (4.5:1 for normal text, 3:1 for large text and meaningful controls). Border alone is not a focus indicator: use a visible cyan focus ring. Status colours keep their tokens and meanings (`--bad:#EF4444`, `--run:#F59E0B`, `--ok:#10B981`, `--ok-l:#F0FDF8`); adjust their dark backgrounds/text only after checking contrast. Buttons, disabled controls, native selects, selection text and scrollbars need deliberate dark values.

## Never themed (measured 2026-10-11)

- Transparent-image checkerboards and intentional preview backgrounds: `.checker`, `.bg-checker`, `.bg-light`, `.bg-dark`, `.bg-wall`, `.bg-chat` (`studio.css`).
- The Studio's media preview boxes: `generate.js:643,646` (`style="background:#111"` behind sheet/video previews) — the dark backdrop the media is judged against.
- Canvas layer defaults in `editor.js` / `prepare.js` (`#ffffff` text, `#111111` stroke, `#000` outline): they choose exported pixels, not chrome. The editor's input `background:#fff` fields and the `#ecfdf5` saved wash are chrome and do get themed.
- SVG overlay fills on media (`generate.js` `#fff` fills, `#2563eb` slot overlays, `#facc15` mark boxes, `CAT` issue palette): they sit on pictures; keep them readable against both themes or re-measure, never recolour blindly.

## Implementation order

1. **Audit and map surfaces.** The only stylesheets are `studio.css` (418 hex literals) and `agent.css` (110). The only scripts that emit inline colours are `generate.js` (22: `CAT` issue palette, `#2563eb` slot overlays, `#111` previews, `#22c55e` check dot), `editor.js` (9: canvas/paper values above), `prepare.js` (5: canvas text defaults and shadow), and `composer.js` (3: style-tile glyph placeholder). Every other loaded script (`app.js`, `home.js`, `agent.js`, `chat.js`, `packs.js`, `live.js`, `welcome.js`, `auth.js`, `tickets.js`, `users.js`, `trending.js`, `support.js`, `trash.js`, `telegram.js`, `imports.js`, `history.js`, `animate.js`, `particles.js`, `effects.js`, `projmap.js`, `sheet-recovery.js`, `job-recovery.js`) carries zero hex literals — verified, not assumed. Classify each hardcoded colour as UI chrome (theme it), semantic issue state (keep meaning, re-measure contrast), or media/export colour (never touch). Record the exact selectors; avoid blanket image filters or indiscriminate replacement. Use fake data for representative Home, Chat and Studio views.
2. **Theme foundation.** Add `mirsal/mirsal/console/theme.js` and `mirsal/mirsal/console/theme.css`, served as `/ui/theme.js` and `/ui/theme.css`. Register both in `console/server.py` `UI_FILES` (a name → content-type map: `"theme.js": "text/javascript"`, `"theme.css": "text/css"`), or they are silent 404s. Load the script in `index.html` **before** the two stylesheet links (it runs before first paint, so no light flash) and the stylesheet **after** them. Put shared dark tokens under `html[data-theme=dark]` — specificity (0,1,1) beats `:root` (0,1,0), so overrides hold without `!important` — set `color-scheme`, and migrate component-specific white/light backgrounds to semantic tokens. Keep light values explicit and working. Reconcile `--ink*`, `--glass`, `--aline`, `--aglow`, `--viol`, `--glow-bg` and primary-button foregrounds so every screen uses the same palette. Prefer flat surfaces with a subtle shadow for elevated menus. `theme.js` must define no `ACT.*`, no `data-act`, no `/api/` strings (else `console/inventory.py` picks them up and `docs/ui_inventory.md` plus `tests/data/ui_baseline.json` need entries), and its top-level names must not collide with any loaded script (the shared-global rule `tests/test_js.py` enforces; prefix them, e.g. `thm`).
3. **Preference and startup.** Default to dark when no valid preference exists. Expose a labelled Dark / Light preference in Settings (`app.js` `RENDER.settings`), persisted as `mirsal.ui.theme` in localStorage — that key is free today (no theme key exists; the 17 `mirsal.*` keys are all feature state). Invalid values fall back to dark. Apply it before the first paint (step 2's placement), catch blocked-storage errors and react to cross-tab changes. Theme is a browser preference, not an AI model or account setting; no backend write is needed. There is **no Content-Security-Policy in this app** (no CSP header on any route, no CSP meta tag — verified 2026-10-11); the external `theme.js` in `UI_FILES` is still the right shape because it is served, cached and inventoried like every other console file, not because a policy demands it.
4. **Integrate every surface.** Start with shell/Home, then Chat/Studio, Library/packs/effects/tools, and finally settings/support/account dialogs, auth, queue and onboarding. Replace theme-dependent inline styles where necessary. Preserve the never-themed controls above. Maintain readable placeholder text, selected menu items and focus outlines; distinguish hover, selected, running, disabled and error states.
5. **Validate and document.** Check 1440px desktop, 900px tablet and 390px phone, plus container-width changes within the shell. Use fake data only. Check empty/loading/error/disabled states, keyboard navigation, reduced motion, light/dark switching, reload persistence, missing/invalid/blocked storage and cross-tab updates. The Home film must keep matching one sticker row in height under both themes. Write narrowly scoped theme-state tests; if assets are added, test their served routes. Run each relevant test once after its code change — the mapped tier only (`tests/test_js.py` for the scripts, the script's own node file, `tests/test_ui_inventory.py` if any action/route moved); never a fresh baseline, full discovery or the retired slow tier. Rewrite `docs/design.md`, `docs/onboarding.md` and `docs/architecture.md` with the built behaviour, update README and remove completed plan steps.

The pending console-script refactor in `plan.md` is a separate work phase, not a prerequisite for changing theme tokens. Do not combine a large file split with the theme rollout.

## Acceptance and rollout

- Default dark loads without a light flash; explicit light mode survives reload and works across screens.
- Black surfaces and cyan accents form one consistent theme; text, icons, inputs and focus remain readable.
- Every existing action and override remains reachable, and status colours retain their meanings.
- At narrow widths, navigation, menus and dialogs fit; the Home film continues matching one sticker row in height.
- Sticker/video/export colours are unaffected; reduced motion prevents autoplay of the Home film strip.
- No new paid call, CDN dependency, runtime model change or public deployment is introduced.

Keep implementation commits on `edit-design` until Haitham asks to merge this theme into `main`.
