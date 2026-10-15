# 3. Foundations

<sub>Part of [design.md](../design.md).</sub>

### 3.1 One token set and two themes

`studio.css` defines the light palette in `:root`; `theme.css` remaps it under `html[data-theme=dark]` and supplies component overrides. All screens share `--bg`, `--sf`, `--fill`, `--bd`, `--tx`, `--mut`, `--mut2`, `--pri`, `--pri-d`, `--pri-l`, `--glass`, `--wash`, `--r` and `--sh`. Light mode uses Mirsal blue; dark mode uses black surfaces and cyan actions, with `--on-pri` for text on cyan. Composer, rail and secondary columns use the same surface family. Issue colours preserve their meanings. Media backgrounds, checkerboards and exported canvas pixels stay unchanged.

A sun/moon button at the top-right of every screen switches Dark / Light immediately and stores the choice in this browser. A shared 52px tools row reserves its space above Create’s tabs and screen content, avoiding overlap with page controls. Settings → Appearance offers the same preference. `theme.js` applies the preference before CSS paints, defaults to dark, tolerates blocked storage and synchronizes other tabs. The complete palette and wiring are in [dark-mode.md](../dark-mode.md).

### 3.2 Type, spacing, motion

Inter is self-hosted. The five type roles are footnote12 / body15 / headline17 / title22 / large title28px; legacy --fs-* names map to these roles. The spacing grid is8px (with4px internal half-steps). The shared radius steps are8 /12 /16 /24px. Previously, type steps were11.5 /12.5 /14 /16 /20 /24px, with a pill radius retained. `--gutter` governs page spacing. Home's headline sizes remain a scoped exception; some inline script font sizes still await the scale sweep in the backlog.

Interactive elements share hover, press, selected and `:focus-visible` states. Click-opened dialogs, menus and panels use a short entrance animation; content redrawn by polling has none. `prefers-reduced-motion` disables transitions, entrances and film autoplay. Every keyboard control retains a visible focus ring.

### Shared test preview

Edge and frame tests use one TESTCARD presentation, retaining their independent controls and API contracts. Frame controls (grid, scrubber and Position) remain in the frame adapter; both preview cards expose a labelled dialog, live caption and shared busy state.

### Semantic foundations (redesign)

--space-*, --type-*, --control-min, --elevation-*, --focus-ring and --motion-* define the shared surface. Status foreground/background pairs have separate dark/light values and never replace the locked diagnostic issue palette. Controls, segments, icon actions and range inputs have44px floors; check/radio labels provide the target around the native input. Preview cards become bounded bottom sheets on phones and keep frame-specific controls. Reduced motion removes semantic durations.
