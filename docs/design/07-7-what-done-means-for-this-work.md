# 7. What "done" means for this work

<sub>Part of [design.md](../design.md).</sub>

- One token set; `--pri` is the accent on every screen; no `#070b1c` island remains.
- Four rail items declared in `app.js`, identical width, position and order on every route; one phone layout (bottom bar) on every screen, not only AI.
- The second column exists on every list-bearing screen and remembers its state.
- **The Animation tab is a studio of its own** (Haitham, 2026-10-04: it used to say there was nothing to see while the controls lived on Stickers). Before any animation exists each batch shows the video sheet that will be sent (the server's preview of the kept stickers), the sheet panel with the model, price and Generate, the editable video prompt with the Prompt tab's footer, and each kept sticker with motion suggestion chips that add a line to that prompt (`studio-animate.js` `animCreate`, `ACT.ganmo`). A prepared-video batch keeps its Animate view.
- Style tiles are compact, honest, and read from `styles.PRESETS`. **They are hidden until the Style chip in the composer bar is clicked** (Haitham, 2026-10-04: always-open tiles took three rows, each as tall as a sticker); picking one closes them and the chip names it (`composer.js` `ACT.cpstyles`, `cpstylepick`). The AI enhancer's engine control under the bar is one compact strip (segment + model drop-down; the cost note is its tooltip), and it reappears every time the enhancer is turned On again.
- Earlier batches: one vertical column, no "Load more", reachable from anywhere.
- `tests/test_js.py` green (it guards the shared `ACT` names and that every `data-act` button has a handler) — **a redesign that trips it has broken the
  app.** `tests/js/*.test.js` must still pass. No duplicate top-level `const`, no new top-level `ACT.*`.
- Checked in a browser on a **copy** of `out/` (`MIRSAL_OUT=<copy>`, never press Create) — see `docs/dev-notes.md` for the Playwright recipe and the
  `location.reload()` trap.
