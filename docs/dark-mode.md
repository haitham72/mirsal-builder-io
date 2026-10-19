# Dark and light themes

Implemented on `redesign-ui-ux`; merging into `main` remains a separate request. A persistent sun/moon button at the top-right switches themes on every screen: sun switches to light, moon switches to dark. Its accessible name describes the next theme. Settings → Appearance also offers Dark and Light. Appearance renders before system settings finish loading, and switching updates the page and pressed states without replacing the focused button.

`console/theme.js` loads before the stylesheets and applies `html[data-theme]` before paint. The browser preference is `localStorage['mirsal.ui.theme']`; missing or invalid values default to dark. Blocked storage still permits switching for the current page. Storage changes, including a cleared key, synchronize other tabs. No account or backend setting is written.

`studio.css` supplies the light palette, `agent.css` the chat styles, and `theme.css` loads last with dark tokens and scoped component overrides. All three assets and the bootstrap script are registered in `console/server.py` `UI_FILES`. Native controls use the theme's `color-scheme`.

| Role | Dark value | Token |
|---|---|---|
| Page | `#101214` | `--bg` |
| Card / rail | `#171A1D` | `--sf` |
| Raised surface / composer / menu | `#202428` | `--raise` |
| Input / hover | `#2A3035` | `--fill` |
| Border | `#3B454D` | `--bd` |
| Text | `#EDF1F5` | `--tx` |
| Secondary text | `#B6C0CA` / `#9BA8B4` | `--mut` / `--mut2` |
| Primary action / hover | `#22D3EE` / `#67E8F9` | `--pri` / `--pri-d` |
| Selected wash | `#18343E` | `--pri-l` |
| Text on primary | `#071015` | `--on-pri` |
| Chat canvas | `#13171A` | `--wash` |
| User message / edge | `#22343E` / `#3A535F` | `--chat-user-bg` / `--chat-user-border` |

The shell, Home, Chat, Studio, Library, packs, effects, tools, Settings, support, account cards, menus, dialogs, queue and welcome chrome share these tokens. Light mode keeps the existing blue action palette. Issue colours retain their meanings; dark backgrounds and readable labels distinguish running, failed, selected and disabled states.

Checkerboards, explicit media preview backgrounds, sheet overlays, canvas layer defaults and exported pixels keep their colours. Editor inputs and save feedback use surface/status tokens. Theme changes never filter or recolour the underlying sticker/video assets.

`tests/js/theme.test.js` covers startup, persistence, invalid/blocked storage, cross-tab changes and pressed-state synchronization and the global toggle. `tests/js/avatar.test.js` proves that redrawing the clicked avatar keeps its menu open until an outside click. Home tests cover distinct responsive bands, mounted film preservation and reduced motion; `tests/test_welcome.py` checks served theme assets and onboarding media Range requests. Browser checks use fake media and API responses; they establish layout and interaction behaviour, while final visual approval remains with Haitham.


## Neutral dark rework (2026-10-19)

The public [Higgsfield Video interface](https://higgsfield.ai/ai/video) informed
the neutral surface hierarchy; Mirsal keeps its existing cyan accent. Dark Chat
disables the broad aurora, dots and pointer glow, uses neutral heading text,
separates user messages from the reading canvas and raises the composer/menus.
Primary buttons retain cyan and contrasting dark text on hover. Light Chat's
palette and ambience are unchanged. Media/checkerboards/exported pixels and the
locked issue colors are not recolored.

`tests/js/theme_palette.test.js`: three regressions failed before and pass after;
it checks surface depth, readable text pairs, primary hover and Chat roles.
[Dated browser evidence](uiux_review/dark-rework-2026-10-19.md) records 36 states,
the unchanged sampled light colors and dark hover at 13.24:1. This is technical
evidence; final visual acceptance remains Haitham's.
