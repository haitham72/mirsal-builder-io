# One control per cell, one decision (2026-10-03, UI/UX spec P1-P4)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

Every control on a cell is the SAME control: the sheet's cell (image sheet and video sheet), the tile's x / +, `Use it anyway`, `Include anyway`, `Take it back`, `Bring back`, `Drop from the set`, and a blocked index chip. They all press `ACT.gcell`
(`studio-tiles.js`), which asks `cellOp(g, t, stage)` what to do from the server's word (`g.allow`, `flow/gates.allow_info`) and the review state, so the same click sends the same request and leaves the same decision row:

| state of the cell | op | request |
|---|---|---|
| a Python block that is a judgement call | `allow` | `POST /api/generations/{id}/allow {kind, index, allow: true}` |
| carries a permission that may be taken back now | `unallow` | the same with `allow: false` |
| made and kept | `drop` | `POST .../drop {index, dropped: true}` (a human reject at the stage it is in; never deletes) |
| dropped, or out of bounds (OFF by default, `docs/dev-notes.md` "Locked decisions" stays) | `include` | `POST .../drop {index, dropped: false}` ("Include anyway" / "Bring back") |
| final (Telegram's own limit, no picture, already animated) | `none` | nothing is sent; the click says why |

**The sheet does only that: no click on a cell opens a tile.** Opening belongs to the thumbnail on the right. *The open question* (does `+` override the locked "Include anyway"?) is answered by the table: they stay two engine mechanisms
(a default-off state for out-of-bounds animations versus a recorded override of a BLOCK) and ONE control for the person, which never changes the default. **Thumbnails** are one picture: the Earlier-batches row shows the first sticker that has a
picture (`live.js` `histThumb`), not the 4 or 9 cells of the sheet. **Delete pack** is a labelled button on the pack screen; it is soft: its confirmation says the pack goes to the trash (Settings > Trash restores it or deletes it for good, "Emptying the trash" above), how many stickers came from batches (which keep their own copies) and how many exist only in the pack;
the pool and the batch originals are never touched by it (`tests/test_library.py::PackDeleteKeepsOriginals`). **A sticker's id** (`G103/S2`) is never part of its name: the header shows the title and the emoji, and the id is its own hoverable,
copyable control (`ACT.copyid`).
