# 3. Foundations

<sub>Part of [design.md](../design.md).</sub>

### 3.1 One token set and two themes

`studio.css` defines the light palette in `:root`; `theme.css` remaps it under `html[data-theme=dark]` and supplies component overrides. All screens share `--bg`, `--sf`, `--fill`, `--bd`, `--tx`, `--mut`, `--mut2`, `--pri`, `--pri-d`, `--pri-l`, `--glass`, `--wash`, `--r` and `--sh`. Light mode uses Mirsal blue; dark mode uses black surfaces and cyan actions, with `--on-pri` for text on cyan. Composer, rail and secondary columns use the same surface family. Issue colours preserve their meanings. Media backgrounds, checkerboards and exported canvas pixels stay unchanged.

A sun/moon button at the top-right of every screen switches Dark / Light immediately and stores the choice in this browser. A shared 52px tools row reserves its space above Create’s tabs and screen content, avoiding overlap with page controls. Settings → Appearance offers the same preference. `theme.js` applies the preference before CSS paints, defaults to dark, tolerates blocked storage and synchronizes other tabs. The complete palette and wiring are in [dark-mode.md](../dark-mode.md).

### 3.2 Type, spacing, motion

Inter is self-hosted. The shared type steps are 11.5 / 12.5 / 14 / 16 / 20 / 24px, with radius tokens 8 / 12 / 16 / 24px and a pill radius. `--gutter` governs page spacing. Home's headline sizes remain a scoped exception; some inline script font sizes still await the scale sweep in the backlog.

Interactive elements share hover, press, selected and `:focus-visible` states. Click-opened dialogs, menus and panels use a short entrance animation; content redrawn by polling has none. `prefers-reduced-motion` disables transitions, entrances and film autoplay. Every keyboard control retains a visible focus ring.

### Shared test preview

Edge and frame tests use one TESTCARD presentation, retaining their independent controls and API contracts. Frame controls (grid, scrubber and Position) remain in the frame adapter; both preview cards expose a labelled dialog, live caption and shared busy state.
