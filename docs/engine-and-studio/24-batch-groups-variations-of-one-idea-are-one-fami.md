# Batch groups: variations of one idea are one family (`flow/groups.py`, 2026-10-04)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

A batch's family is derived when it is read, so nothing was migrated: an explicit `group: "G###"` in result.json (written by **Add to group** or by dragging a batch onto another), else the family of its recorded `parent` (a chat edit, *more*, a redo), else itself. **The target is always the parent** (Haitham): "add X to Y" or dragging X onto Y puts X and its whole family under Y's root, and the family shows the root's title. A join writes only on X's old root, so a member can still **leave** with its own edits (`groups.leave`; the root cannot leave). `relation` says why a batch is there: `joined`, `redo` (`regen_of`), `edit` (`parent`), none for the root; `group_history` records each JOIN / LEAVE with actor and time.

Earlier batches (`GET /api/history`) lists **families**: one plain entry with the root's title and "N variations" (`live.js` `histRow`). The variations are chosen in the **Studio's view of the batch, above its workflow steps** (`gvarsHtml`, Haitham 2026-10-04: not in the column): one thumbnail per batch of the family, the one in view outlined, `×` on each non-root one to leave. Any entry can be dragged onto another (`histJoin`, `POST /api/generations/{id}/join {to}`); the batch header has **Add to group** (`ACT.ggroup`), a picker of the other families. A family shares its particles: the batch's Particles section also lists the versions made for its sister variations' stickers (`particle_sets.for_generation` `family`). Postgres mirrors `generations.group_id` (the root) and `relation` (`migrations/009_groups.sql`). G104 + G105 (Superhero Dubai, a chat edit) became one family this way on 2026-10-04 with no data change.

**The Library follows the groups (Haitham, 2026-10-05).** `GET /api/library` gives each pack a `group` (`"G104"`, the family root; `null` when none): the family most of its stickers came from (`source.generation`), and only when that family has more than one pack (`groups.pack_groups`, a pure read, so a join or leave in the Studio shows at the next read). The Packs column shows a group as one row (its first pack, "N packs · group G104") with a fold that lists the others (`app.js` `packEntries`, `pkgrp`); My Packs frames the group's packs together. Packs themselves are unchanged: grouping never moves or merges stickers.

**Packs in Earlier batches (2026-10-09).** Above families there is the PACK: the batches of one pack (Next batch, a multi-batch Generate) are separate families,
and the column showed them apart. `pipeline._packs` derives it when the column is read, nothing migrated: families of the same request (grid names left out,
`actions.strip_presets`) by the same person, each made within `PACK_GAP_S` (6 h) of the previous one, are ONE pack; an emoji pack's batches are in grid order
(core 1-9, social 10-18, reactions 19-27, daily 28-36). `GET /api/history` pages by pack: an item is its first batch's family item plus `batches[]` (each a
family item with its `variants`). The column draws a pack as one entry, its head (title without the grid name, "N batches · M stickers") opens every batch
of it in the Studio, and its batches sit under it as **Batch 1 … n**. **Drag and drop moves a batch between packs**: drop a batch on any entry and it becomes
another batch of that entry's pack (`POST /api/generations/{id}/pack {to}`, `groups.set_pack`, stored as `pack` + `pack_history` on the family root; an
explicit link beats the derived grouping); the x on a batch of a pack takes it out (`{to: null}` stores a link to itself, so the derived grouping does not
pull it back). It is never a regeneration (that is `join`, the Studio's Add to group). The drop highlight is `hdrop` (the old `drop` class was the upload
area's 300 px style, which made the entry under the pointer jump).
