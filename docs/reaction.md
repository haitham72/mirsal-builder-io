# Reaction sets and bursts (renamed from Particles, 2026-10-13)

This is the reaction area's architecture document (formerly `docs/particles.md`; that path stays as a pointer). Reactions are owned by library stickers; every saved version is a row under its sticker; the editor offers three equal sources; animated sprites play inside the simulator; mistaken sticker packs can be recovered as reactions. Accepted by Haitham in his browser on 2026-10-04. Open work is in `backlog.md` (reactions). User-facing copy says **reaction** everywhere; API routes (`/api/particles`), storage (`out/particles/P###`) and internal names keep `particles` for compatibility.

## Sections

This is an index: each section is its own file under [`reaction/`](reaction/); read only the one a task needs.

| section | what it covers |
|---|---|
| [1. Ownership and vocabulary](reaction/01-1-ownership-and-vocabulary.md) | A durable particle set (`P###`) belongs to its library stickers, never to a pack. Selected stickers can share a set. Stored `owner[]` records contain `{stick… |
| [2. Storage, migration and deletion](reaction/02-2-storage-migration-and-deletion.md) | `out/particles/P###/set.json` holds owners, source metadata, cells, picked flags, motion, sheets, renders and history. Stored sets have no `packs[]`; API `pa… |
| [3. One scoped editor](reaction/03-3-one-scoped-editor.md) | Open Particles from a sticker, batch, pack or Library. Sticker entry chooses that sticker; batch entry chooses only that batch; pack entry chooses its sticke… |
| [4. Animated sprites and recovery](reaction/04-4-animated-sprites-and-recovery.md) | The full animated path is prompt → text-only Kling 2×2/3×3 animated sheet → key and slice → animated sprites in the simulator → render → add to the same pa… |
| [5. Galleries and chat](reaction/05-5-galleries-and-chat.md) | The batch section reads `GET /api/generations/{id}/particles`, displaying each READY cell's library sticker or approval offer, owner sets and affirmation. So… |
| [6. JSON contract and compatibility](reaction/06-6-json-contract-and-compatibility.md) | The authoritative shapes and errors are in api.md and the OpenAPI document. Functions live in `flow/particle_sets.py`, using the pure simulator in `engine/pa… |
| [8. Particles on their own: from a request to Telegram (2026-10-05)](reaction/07-8-particles-on-their-own-from-a-request-to-teleg.md) | The request. `particle_sets.from_request(text, grid, kind)` reads the particles a sentence names, deterministically (no model): the lead-in ("create partic… |
| [7. How it is tested, and what is open](reaction/08-7-how-it-is-tested-and-what-is-open.md) | Fake providers, temporary libraries and scratch copies of `out/` only; the browser on a spare port, never the live server; nothing is generated for a check (… |
| [8. One animation per emoji, pack variations on top (2026-10-13)](reaction/09-8-one-animation-per-emoji-pack-variations-on-top.md) | The rule (Haitham). Every predefined emoji owns one fixed animation, shared by every pack; a pack varies only sprite art plus Size/Energy. This closes… |
| [9. Three outputs, all optional (2026-10-13)](reaction/10-9-three-outputs-all-optional-2026-10-13.md) | WebM VP9+alpha stays the primary and only Telegram delivery. Kling-animated sprites stay the paid path. Lottie JSON is the third, web-only output: `engin… |
| [10. Migrating random sets onto the map (2026-10-13)](reaction/11-10-migrating-random-sets-onto-the-map-2026-10-13.md) | `particle_sets.adopt_emoji_map()` (CLI `python -m mirsal particles adopt-emoji-map`): idempotent, free. Keeps every byte; replaces free motion with the emoji… |
| [11. Added bursts are reactions, not stickers (2026-10-13)](reaction/12-11-added-bursts-are-reactions-not-stickers-2026.md) | `Add to pack` still delivers the burst as an ordinary animated pack sticker (Telegram and zip include it), but the screens never mix it into the stickers: th… |
| [12. Library Create flow (2026-10-13)](reaction/13-12-library-create-flow-2026-10-13.md) | Library > Reactions > Create offers two paths. Predefined is the emoji bank (`GET /api/particles/bank`): every token with `finished` (a covering set… |
| [13. Reaction effects: one emoji, flying as itself, to Lottie (2026-10-13)](reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md) | The product decision. Create > + New > Reaction effects (`#/reactions`, its own screen and file `console/reactions.js`; `#/effects` stays the Studio's… |
| [14. The animation preset library (2026-10-14)](reaction/15-14-the-animation-preset-library.md) | 10-15 emoji-free animation presets {motion}_{NN} grouped by motion; every bank emoji holds one; no base64 in the Lottie. |
| [15. Handpicked Lottie files: origin → morph (2026-10-14)](reaction/16-16-handpicked-lottie-files-origin-morph.md) | Dropped files in `mirsal/lottie/*.json`, handpicked per emoji as origin + optional morph; referenced, never rendered; shipped in the zip + manifest. |
| [17. Lottie style reactions (2026-10-14)](reaction/17-17-lottie-style-reactions.md) | The second permanent style beside Emoji style: every dropped Lottie is a reaction whose particles are that Lottie; morph targets, child bursts, flip, speed pulse; one self-contained export embedding every source; lottie-web viewer = export. |
