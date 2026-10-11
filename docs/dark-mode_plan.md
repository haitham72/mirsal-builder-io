# Dark mode — black and cyan blue

Status: planned, not implemented. This plan stays on `edit-design`; the current implementation is merged into `main`. Haitham requested an elegant, clean Higgsfield-inspired interface with black surfaces and cyan blue accents. Finalize the plan through the independent review before starting its implementation.

## Direction and scope

Use [Higgsfield](https://higgsfield.ai/) and the supplied `ref/screencapture-higgsfield.jpg` for the compact creation navigation, media-first grid and restrained controls. The black/cyan palette below comes from Haitham's brief; this is a Mirsal theme, not a claim of pixel-for-pixel reproduction. Keep Inter, the existing inline SVG icons and the shared spacing/radius scale. Use calm surfaces, fine borders and clear hierarchy. Cyan marks the main action, selection and keyboard focus; avoid large glowing backgrounds and purple auroras in dark mode.

Cover Home, Chat, Studio, Library, packs, photo creation, effects, editor/export tools, Settings, Help, Team, Trending, the queue, popovers, dialogs, onboarding and LAN sign-in/approval cards. The rail of four, Create tabs, routes, model selection, spending controls and every existing action remain functional. Issue colours keep their meanings and require accessible text/icons alongside colour. Media, exported pixels and explicit preview-background choices keep their actual colours.

Home keeps its newly implemented two sticker rows followed by the full-width film crop. Theme the tile surface and labels while preserving the shared grid row height, responsive columns, `object-fit:cover`, reduced-motion poster and full-film opening.

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

Treat these as concrete starting values. Measure final text pairs against WCAG AA (4.5:1 for normal text, 3:1 for large text and meaningful controls). Border alone is not a focus indicator: use a visible cyan focus ring. Keep error, warning and success semantics; adjust their dark backgrounds/text only after checking contrast. Buttons, disabled controls, native selects, selection text and scrollbars need deliberate dark values.

## Implementation order

1. **Audit and map surfaces.** Inspect `studio.css`, `agent.css`, `app.js`, `home.js`, `generate.js`, `composer.js`, `packs.js`, `live.js`, `welcome.js`, `auth.js`, and any other loaded script that emits inline colours. Classify hardcoded colours as UI surfaces, semantic issues or media preview controls. Record the exact selectors requiring changes; avoid blanket image filters or indiscriminate colour replacement. Use fake data for representative Home, Chat and Studio views.
2. **Theme foundation.** Add a small external `/ui/theme.js` before styles in `index.html`, plus `/ui/theme.css` after the existing styles. Register both in `server.py`'s `UI_FILES` allow-list. Put shared dark tokens under `html[data-theme=dark]`, set `color-scheme`, and migrate component-specific white/light backgrounds to semantic tokens. Keep light values explicit and working. Reconcile `--ink*`, `--glass`, `--aline`, `--aglow`, `--viol`, `--glow-bg` and primary-button foregrounds so every screen uses the same palette. Prefer flat surfaces with a subtle shadow for elevated menus.
3. **Preference and startup.** Default to dark when no valid preference exists. Expose a labelled Dark / Light preference in Settings, persisted as `mirsal.ui.theme` in localStorage; invalid values fall back to dark. Apply it before the first paint, catch blocked-storage errors and react to cross-tab changes. Theme is a browser preference, not an AI model or account setting; no backend write is needed. Avoid inline scripts that bypass the existing content-security policy.
4. **Integrate every surface.** Start with shell/Home, then Chat/Studio, Library/packs/effects/tools, and finally settings/support/account dialogs, auth, queue and onboarding. Replace theme-dependent inline styles where necessary. Preserve transparent-image checkerboards and intentional preview backgrounds. Maintain readable placeholder text, selected menu items and focus outlines; distinguish hover, selected, running, disabled and error states.
5. **Validate and document.** Check 1440px desktop, 900px tablet and 390px phone, plus container-width changes within the shell. Use fake data only. Check empty/loading/error/disabled states, keyboard navigation, reduced motion, light/dark switching, reload persistence, missing/invalid/blocked storage and cross-tab updates. Write narrowly scoped theme-state tests; if assets are added, test their served routes. Run each relevant test once after its code changes; do not rerun the baseline, full discovery or retired slow tier. Rewrite `docs/design.md`, `docs/onboarding.md` and `docs/architecture.md` with the built behaviour, update README and remove completed plan steps.

The pending console-script refactor in `plan.md` is a separate work phase, not a prerequisite for changing theme tokens. Do not combine a large file split with the theme rollout.

## Acceptance and rollout

- Default dark loads without a light flash; explicit light mode survives reload and works across screens.
- Black surfaces and cyan accents form one consistent theme; text, icons, inputs and focus remain readable.
- Every existing action and override remains reachable, and status colours retain their meanings.
- At narrow widths, navigation, menus and dialogs fit; the Home film continues matching one sticker row in height.
- Sticker/video/export colours are unaffected; reduced motion prevents autoplay of the Home film strip.
- No new paid call, CDN dependency, runtime model change or public deployment is introduced.

Keep implementation commits on `edit-design` until Haitham asks to merge this theme into `main`. The current request authorizes preparing/finalizing this plan; it does not implement dark mode.
