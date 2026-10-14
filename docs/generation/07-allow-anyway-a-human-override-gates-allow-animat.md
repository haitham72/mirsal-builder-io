# Allow anyway (a human override, `gates.allow_animation`)

<sub>Part of [generation.md](../generation.md).</sub>

An animation that Python blocked for **leaving or crossing its slot** (`inside_slot`, `cross_slot`) has no file, because the block saves the encode. The user can **allow it** by clicking the
sticker's warning banner, its "Allow anyway" button, its chip, or its cell on the video sheet (`POST /api/generations/<id>/allow {index, allow}`): the permission is stored on the sticker
(`anim_override`), recorded in its history as a human APPROVE ("allowed anyway: cross_slot"), the cell is cut again with that check downgraded to a warning (still listed, "allowed by you"), and
every later re-slice (an edge change) keeps it. **Allow all (n)** under the sheet's chips allows every blocked animation of the batch in one request (`{all: true}`, one re-cut of all of them), **Take all back (n)** reverses what was allowed, and every cell on the video sheet is a toggle (click: allow; click an allowed one: take it back). Taking one back (the tile's "undo") blocks it again. Technical blocks (format, size, codec, loop) cannot be allowed, and the review gate itself
still refuses a blocked animation. **Dashed + faded means "will NOT be exported"** (a dropped sticker, a blocked animation, a sheet cell outside the set) and **solid means exported** (a kept-with-a-check cell has a thin solid outline); a faded item is never disabled: it stays
clickable, can be opened, brought back or allowed.
