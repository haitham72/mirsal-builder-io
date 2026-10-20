# 2. Non-negotiables (breaking these breaks the app, not just the look)

<sub>Part of [design.md](../design.md).</sub>

- **No CDN, no runtime fetch** (rule 8). One self-hosted family: `console/ui/fonts/InterVariable.woff2` (`studio.css:1`), used by `body` at `studio.css:4`.
  No second webfont. Icons are inline SVG (`ic()` in `app.js`).
- **One shared `ACT` object.** A second `ACT.name =` in a later script *silently replaces* the first — this already bit the app once (`history.js` replaced
  `hopen`, so "Earlier batches" opened batch NaN). `tests/test_js.py` fails on any clash not listed as intentional.
- **No duplicate top-level `const` across scripts.** The second declaration is not run at all (`history.js` was dead for a while because of `ago`).
- **`agent.css` selectors stay namespaced** (`ag-`, `is-`, `k-`): the Studio's own CSS already uses `.step`, `.tile`, `.sel`, `.done`.
- **Issue colours are locked** (`docs/dev-notes.md`, "Locked decisions"): orange out of bounds, purple bad green screen, yellow bad loop, pink look or motion, blue file / Telegram
  limit, red dropped or blocked; hatched = not in the set, dashed = kept with a check. A redesign must not repaint these — they carry meaning.
- **Never open media to judge it** — a design change is judged on the code and in the browser, stickers are judged by the verifier and by Haitham.

---
