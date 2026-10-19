# 3. Foundations

<sub>Part of [design.md](../design.md).</sub>

### 3.1 One token set and two themes

`studio.css` defines the light palette in `:root`; `theme.css` remaps it under `html[data-theme=dark]` and supplies component overrides. All screens share `--bg`, `--sf`, `--fill`, `--bd`, `--tx`, `--mut`, `--mut2`, `--pri`, `--pri-d`, `--pri-l`, `--glass`, `--wash`, `--r` and `--sh`. Light mode uses Mirsal blue; dark mode uses black surfaces and cyan actions, with `--on-pri` for text on cyan. Composer, rail and secondary columns use the same surface family. Issue colours preserve their meanings. Media backgrounds, checkerboards and exported canvas pixels stay unchanged.

A sun/moon button at the top-right of every screen switches Dark / Light immediately and stores the choice in this browser. A shared 52px tools row reserves its space above Create’s tabs and screen content, avoiding overlap with page controls. Settings → Appearance offers the same preference. `theme.js` applies the preference before CSS paints, defaults to dark, tolerates blocked storage and synchronizes other tabs. The complete palette and wiring are in [dark-mode.md](../dark-mode.md).

### 3.2 Type, spacing, motion

Inter is self-hosted. Five type roles define footnote (12px), body (15px), headline (17px), title (22px) and large title (28px); legacy `--fs-*` names alias those roles. Spacing follows an 8px grid with 4px internal half-steps; radii are 8, 12, 16 and 24px plus the existing pill. `--gutter` governs page spacing. Home headlines remain a scoped exception; legacy inline font sizes still need a separate sweep.

Interactive elements share hover, press, selected and `:focus-visible` states. Click-opened dialogs, menus and panels use a short entrance animation; content redrawn by polling has none. `prefers-reduced-motion` disables transitions, entrances and film autoplay. Every keyboard control retains a visible focus ring.

Selected tabs retain their primary background on hover in dark mode. The generic
dark hover surface must not replace that background while keeping `--on-pri`
text; the browser regression reproduced 1.26:1 contrast on that combination.

### Shared test preview

Edge and frame tests use one TESTCARD presentation, retaining their independent controls and API contracts. Frame controls (grid, scrubber and Position) remain in the frame adapter; both preview cards expose a labelled dialog, live caption and shared busy state.

### Semantic foundations (redesign)

--space-*, --type-*, --control-min, --elevation-*, --focus-ring and --motion-* define the shared surface. Status foreground/background pairs have separate dark/light values and never replace the locked diagnostic issue palette. Controls, segments, icon actions and range inputs have44px floors; check/radio labels provide the target around the native input. Preview cards become bounded bottom sheets on phones and keep frame-specific controls. Reduced motion removes semantic durations.
