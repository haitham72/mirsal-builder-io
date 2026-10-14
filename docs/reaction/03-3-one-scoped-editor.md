# 3. One scoped editor

<sub>Part of [reaction.md](../reaction.md).</sub>

Open Particles from a sticker, batch, pack or Library. Sticker entry chooses that sticker; batch entry chooses only that batch; pack entry chooses its stickers. Library entry asks for the target. No guessed pack or unrelated persisted run is opened. Explicit **Continue the last run** is available only for matching scope.

A batch outside the library offers **Approve as a pack**, using the existing modal and returning directly to its scoped editor after success. Back remains available. The offer costs nothing.

**Rows (Haitham, 2026-10-04).** Every saved version of a sticker's particles is **one row under that sticker**, oldest first: v1, v2, v3... Entering Particles always starts a **new version** (a draft set, `saved_at: null`); it never reopens an older set by itself. A saved row is opened explicitly with **Open** on its row. Each pass picks its own source from three equal cards, whatever earlier rows used:

| Card | Choices |
| --- | --- |
| **Sprites from the sticker** · free | Select slices of its sheet or library artwork, **Use selected · free** |
| **AI image sprites** · credits | prompt, 2×2/3×3, quote, Generate (Nano Banana sheet, keyed and cut to tight sprites) |
| **Kling animated · from scratch** · credits | prompt, 2×2/3×3, quote, Generate (text-only nothing-to-nothing Kling sheet, cut into animated sprites) |

**Add more** inside an open set still appends cells to that set. The default grid is 2×2; 3×3 is available with its measured warning. Advanced contains provider/key settings. Unknown price offers Retry price and starts nothing. Saving/importing is automatic through the engine; normal creation does not need an extra naming or assignment modal.

All paths end in one simulator: selected sprites, preview, presets, **Energy / Float / Swirl / Size**, then **Render → Add to pack → In pack ✓**. Count, spin and sprite resolution live under Advanced; **Size** (`particle_size`) is how big the particles look, sprite resolution only their sharpness. UI copy is labels, actual prices, progress and local warnings; model/ownership explanations belong in these docs.

**Save** turns a draft into the next row; on a row that is already saved it **replaces** that row's motion, count and sizing. **Save as new** (`POST /api/particles/{id}/save-as-new`) keeps the row as it was and saves the same sprites with the edited motion as a **new row**; bursts rendered with the old motion stay with the old row. Example: a fast, chaotic row is reopened, slowed down, then saved over itself or saved as a new row. A row reaches the pack only through **Add to pack** on it (option C): the burst becomes an animated pack sticker carrying `source.particle_set`, `source.render` and `source.parent_sticker`, and the row then reads **In pack ✓**. **Assign to stickers → Test in chat** is the free test path: Echo's reply/reaction plays that sent sticker's current linked set with saved settings. It requires no rendered pack sticker. Replay refreshes assignment rather than remembering an old set.
