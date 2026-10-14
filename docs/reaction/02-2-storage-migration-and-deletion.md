# 2. Storage, migration and deletion

<sub>Part of [reaction.md](../reaction.md).</sub>

`out/particles/P###/set.json` holds owners, source metadata, cells, picked flags, motion, sheets, renders and history. Stored sets have no `packs[]`; API `packs[]` remains derived and read-only for compatibility. Existing records migrate idempotently with an untouched `set.json.pre-owner` backup. Owners come from source sticker IDs or the effect's selected stickers within old packs. Unknown owners are retained as detached sets.

Cells are copied into the set. Image cells use tight alpha sprites rather than 512px sticker canvases. Kling imports retain keyed cell WebMs, poster PNGs, job IDs, credits and source provenance. The corrected animated simulation contract uses each clip's frame sequence: a poster is not a substitute for internal motion. This restoration is under acceptance, not yet declared complete.

Add more appends cells to the same set and preserves existing bytes. Repeated completion/import is idempotent. Job requests retain their target set so restarting resumes the same operation without billing/importing twice. A set may contain mixed image and video sources; the initial source must not restrict later creation choices.

Delete moves a set to `out/trash/particles/`; Restore keeps its ID and ownership. IDs are shared with trash, avoiding collisions. A set in use asks for confirmation and names affected packs. Pack purge detaches owner links in active and trashed sets and retains the sets. Permanent purge of deleted particle sets is still unbuilt.
