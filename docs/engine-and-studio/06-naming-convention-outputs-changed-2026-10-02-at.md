# Naming convention (outputs; changed 2026-10-02 at Haitham's request)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

One function, `runtime/names.py`, names every media file Mirsal makes, in the engine and in the library:

    {media}-{subject}-{action}[-{pack}]-{YYYYMMDDTHHMMSS}-{hash6}.{ext}
    img-falcon_stickers-open_arms-20261002T133320-a3f9c1.png      vid-falcon_stickers-open_arms-20261002T133320-a3f9c1.webm      (a batch's still and its animation share one stem)
    img-falcon_stickers-open_arms-gold_pack-20261002T140100-5be201.png                                                            (a copy made in the library: its pack and the moment it was added)

Readable (what it is), traceable (when it was made, UTC) and non-repeatable (the fingerprint carries the batch number, the sticker key and, in the library, the sticker id: two files never share a name, even
for the same subject and action in the same second). The pack is optional on purpose: a sticker can move to another pack, so the pack of a sticker lives in the library's data and is stamped into a file name only
at birth. `names.parse` reads both conventions.

- **Batch folders carry a label** (Haitham, 2026-10-04, `runtime/names.folder`): a new batch is `out/G111-dog_as_banana-20261005T093012/` (id, task slug, UTC creation time), so a folder list reads by itself. The id stays the address: `pipeline.gen_dir(out, 111)` finds the bare or the labelled folder, `list_ids` / `removed_ids` read the id back (`names.folder_id`), `/out/G111/...` URLs and asset keys `G111/...` reach it through `pipeline.out_path` (the server and `LocalAssetStore`), and the library files a new copy under the same folder name. `pipeline._allocate` makes the folder; two processes that pick one number see each other's folder and the loser takes the next. G001-G110 keep their bare names (nothing is renamed). Code never builds `out / "G111"` itself.
- **Engine outputs** are `out/G00N/slices/<name>` (`pipeline.media_name`; the time is the batch's creation time). **G001-G096 keep their old names** (`img-005-barbie_love-barbie_blow_kiss`: media, batch number, task, key): nothing is renamed, `names.parse` says `legacy`.
- **The library** keeps its own copy of a sticker (it can be edited there) in `out/library/files/<group>/`: `G012/` for a sticker that came from batch G012, `own/` for what was made in the library (imports, cut-outs, editor renders, trims). `library.json`'s `file` is that relative path; the generator's own name stays in `file_name`.
  A move between packs changes `library.json` only. A library from before (one flat folder, `img-001-<pack>-<name>`) is regrouped and renamed once, automatically, when the server (or any command) first opens it (`Library.migrate_layout`, flag `layout: 2`, all or nothing).
- **The watch folders** (`img-NNN-<subject>/`, `vid-NNN-<subject>/` in `inputs/`) are inputs and keep their names: they are final.
- **Search never reads a file name.** The pool's `subject` and `action` fields are embedded (cosine, 90% of the rank); the lexical 10% reads `search_text` = subject, action, the sticker's KEY words, emoji, style. The name of the file is not part of it (it used to be; a date and a fingerprint would only be noise).
  A file is found through Postgres (`stickers.png` is its path inside the batch) or `library.json`, never by its name.
