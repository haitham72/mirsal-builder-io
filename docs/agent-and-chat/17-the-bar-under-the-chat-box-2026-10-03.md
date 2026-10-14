# The bar under the chat box (2026-10-03)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

`drawBar` (`chat-core.js`) paints the bar into `#ag-bar` (the style chip `.ag-cur` and the sheet size) and the style tiles into `#ag-styles`.

* **The sheet size is one native click-toggle**: `<button type="button" class="ag-chip ag-grid" data-act="aggridtoggle">`, labelled "3×3 sheet" (nine stickers, the default) or "2×2 sheet" (four), its title explaining both ("nine (3×3) or four (2×2). Click to change."). `ACT.aggridtoggle` flips the saved grid and calls `saveSet({grid})`; there is no `<select>`, no `data-aggrid`, no `.ag-sel` (that class is the settings panel's full-width model drop-down and stretched the chip over its own row). The class is `.ag-grid` (`agent.css`), never shared with a panel control.
* **It changes a setting, nothing else**: `saveSet` posts `POST /api/chat/sessions/{id}/settings` with `{grid}` (never a message, never a generation, never a turn), then repaints from the **saved** settings: `A.sess.settings = r.j.settings`, `setSet()` (the gear) and `drawBar()`. The press is reversible (3×3 and 2×2 swap), and the gear's 3×3 / 2×2 pair (`ACT.agsetgrid`) uses the very same route and the same repaint, so the two controls never disagree.
* **Before the first message** a press calls `ensureSession()`, which creates one empty chat (`POST /api/chat/sessions`, `messages: []`, hash `#/agent/<id>`) and saves the size into it; no turn is sent. Rendering the bar never creates a session.
* **A refused update** (the settings route answers an error) leaves the old size on the chip, repaints nothing, and shows the server's sentence as a toast.
* The style metadata beside the chip is escaped (`AIU.esc`), never interpreted as markup.
* Covered by `tests/js/sheet_size_chip.test.js` (the renderer and handlers executed with local stubs, no browser or server).

The one-time AI vision switch under a message is `chipHTML` -> `<span class="ai-vis"><button class="ai-chip" data-act=agsetting>` (look: `docs/design.md`; behaviour: "The AI vision switch" below).
