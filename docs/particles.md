# Particle sets and bursts

This is the particle area's architecture document (the filename stays for existing links). Particles are owned by library stickers; every saved version is a row under its sticker; the editor offers three equal sources; animated sprites play inside the simulator; mistaken sticker packs can be recovered as particles. Accepted by Haitham in his browser on 2026-10-04. Open work is in `backlog.md` (particles).

## 1. Ownership and vocabulary

A durable particle set (`P###`) belongs to its library stickers, never to a pack. Selected stickers can share a set. Stored `owner[]` records contain `{sticker_id, pack_id, generation, index}`; the library supplies the parent pack and provenance. Each sticker has ordered `particles[]` links, newest last. Pack views show the union of their stickers' sets; sticker views show their own sets.

A **sprite** is reusable still or animated artwork. A **burst** is the composition rendered from selected sprites and motion settings. `E###` is a working generation session, not an owner. Adding a burst as an ordinary animated sticker **affirms** its set in the destination pack: `in the pack ✓`. Neither rendering nor adding changes set ownership.

Unresolvable owners leave a **detached set**, retained visibly in Library > Particles with **Attach to a sticker**. **Stand-alone sets (Haitham, 2026-10-05).** A set may also stand on its own: no sticker owns it (`owner: []`), and it is fully usable: preview, render, download, or make a pack of it. This replaces the earlier rule that there is no stand-alone particle pack. It comes from a plain request ("create particles for lipsticks and ribbons"), through the Studio's **Particles** choice or the chat; see section 8.

## 2. Storage, migration and deletion

`out/particles/P###/set.json` holds owners, source metadata, cells, picked flags, motion, sheets, renders and history. Stored sets have no `packs[]`; API `packs[]` remains derived and read-only for compatibility. Existing records migrate idempotently with an untouched `set.json.pre-owner` backup. Owners come from source sticker IDs or the effect's selected stickers within old packs. Unknown owners are retained as detached sets.

Cells are copied into the set. Image cells use tight alpha sprites rather than 512px sticker canvases. Kling imports retain keyed cell WebMs, poster PNGs, job IDs, credits and source provenance. The corrected animated simulation contract uses each clip's frame sequence: a poster is not a substitute for internal motion. This restoration is under acceptance, not yet declared complete.

Add more appends cells to the same set and preserves existing bytes. Repeated completion/import is idempotent. Job requests retain their target set so restarting resumes the same operation without billing/importing twice. A set may contain mixed image and video sources; the initial source must not restrict later creation choices.

Delete moves a set to `out/trash/particles/`; Restore keeps its ID and ownership. IDs are shared with trash, avoiding collisions. A set in use asks for confirmation and names affected packs. Pack purge detaches owner links in active and trashed sets and retains the sets. Permanent purge of deleted particle sets is still unbuilt.

## 3. One scoped editor

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

## 4. Animated sprites and recovery

The full animated path is **prompt → text-only Kling 2×2/3×3 animated sheet → key and slice → animated sprites in the simulator → render → add to the same pack**. The existing nothing-to-nothing pipeline and technical checks remain. Each flying particle plays its own sprite's frames while simulator movement, spin, scale and fade are applied. Image sprites are single-frame inputs. Selected video tiles loop; job/credit details remain accessible. Directly adding a cut clip remains a secondary legacy action.

Recovery for artwork accidentally saved as a sticker pack is **Use as particle pack → This sticker / All N stickers → Parent pack and target stickers → Use selected · free**. Source artwork is copied without deleting originals. The selected parent stickers own the set; supplying artwork does not make source stickers owners.

## 5. Galleries and chat

The batch section reads `GET /api/generations/{id}/particles`, displaying each READY cell's library sticker or approval offer, owner sets and affirmation. Source kind, job and credits are available on set cards. A sticker with any set cannot read "never created". The badge sums owner sets, legacy E### results and saved stickers once, rather than showing competing badges.

A cut sprite is a cell **inside** its row, never a particle set of its own. The sticker window reads `rows[]` and `drafts[]` from `GET /api/packs/{id}/stickers/{sid}/particles` (`particle_sets.rows_for_sticker`): each row shows `v#`, how it was made (*Sprites*, *AI image sprites*, *Kling from scratch*, *Animated sprites*, *The sticker itself*), its sprite count, credits, job, its newest burst (or a strip of its sprites), **Open**, and **Add to pack** / **In pack ✓**. A set shared by several stickers is a row under each of them in the sticker window. The Studio's batch **Particles** section is **one list** of the versions made for the batch's stickers, each version once, oldest first (`particles.js` `spSecRows`), plus the approval offer for stickers not in a pack; it has no block per sticker (Haitham, 2026-10-04: one Old Man set was drawn nine times, because the per-sticker gallery of 2026-10-03, built when each burst belonged to one sticker, was kept after sets became shared). Drafts are listed apart and never lost. **Older effect runs** that produced something are adopted once as rows by `python -m mirsal particles adopt` (`particle_sets.adopt_effects`, idempotent, free, nothing moved): a Kling run's cut clips become one row of animated sprites, a simulated run's bursts become the row's renders, and runs that produced nothing stay hidden. A run whose **AI particle sheet was drawn but never saved** becomes a row of that sheet's cells (a sheet an older version cut as stickers is first cut again as particles, free, `pipeline.recut_as_particles`); the command takes the writer lock, so with the server running the recut goes through its route (`POST /api/generations/{id}/recut_particles`). A particle sheet held by a row (`pipeline._held_by_particle_rows`) is shown under its stickers and **left out of Earlier batches** (`GET /api/history`); its `G###` folder stays where it is. On 2026-10-04 G100 (E008, Batman Lego), G101 (E013, Barbie in love), G106 and G109 became rows this way. On 2026-10-04 this put the Batman Lego Kling take (E002, J039, 4 cells) under its sticker as a row instead of a stand-alone run (backup: `out/backups/particle-rows-2026-10-04/`). A run not yet adopted still shows as one grouped card (`runs[]`); raw `created[]`/`saved[]` remain for legacy clients.

The chat resolves an explicitly named set first; otherwise it prefers the focused sticker's newest owned set, then the focused set, then the only suitable set, then asks with chips. The explicit-name exception is intentional. Make/more preserve owner scope; linking to another sticker is free. A batch outside the library gets an approval card. The tools call the same engine functions as Studio; see [agent-and-chat.md](agent-and-chat.md).

Mirsal Echo is separate from AI-chat language selection. `preview_for_sticker` chooses only a set linked to the actual sent sticker: its **latest saved version** (the highest v# under the sticker, by `saved_at`), with that version's saved motion; only a sticker with no saved version yet falls back to its newest linked draft. Unassigned stickers get no particles. The browser retains sticker IDs, rejects stale/cleared message requests, and plays the burst **out of the reaction badge's heart**: the image is drawn inside the badge and shifted by the burst's own `origin` (the preview's `params.origin`; a fountain starts low, rain at the top), so the particles leave from the heart whatever the preset, 80 px (Haitham, 2026-10-05: 60% smaller), as Telegram plays a reaction's effect (`chat.js` `chParticleH`, `studio.css` `.bub .react .ch-particle`). Echo's preview is rendered at `ECHO_PX` = 160 px (twice the shown size), about half the bytes of the 256 px editor preview (P008: 544 KB to 273 KB). It is an animated WebP for the browser; the file for Telegram is the separate 512 px VP9 WebM render (`renders/R###.webm`, within 256 KB). Echo's own returned sticker can be **liked** (the heart on hover, or a double-click, like Telegram's double-tap): the like is the same ❤️ badge and plays that sticker's burst, and a click on the badge replays it (`chat.js` `chLike`). The chat header switches between a **mobile view** (a 390 px phone frame) and the full-width desktop view; the choice is per browser (`mirsal.chat.view`). The sticker button opens a **sticker panel shaped like Telegram's** (`chat.js` `chTrayH`, `studio.css` `.tg*`): a small card above the composer on the right with one Stickers tab, a search box (name or emoji tag, across every pack) beside the emoji tags the stickers carry as one-tap filters, a borderless 5-column grid, and the packs along the bottom (their covers) with Recent, the stickers sent in this chat, first. A click outside it, Esc, or picking a sticker (which sends it) closes it.

## 6. JSON contract and compatibility

The authoritative shapes and errors are in [api.md](api.md) and the OpenAPI document. Functions live in `flow/particle_sets.py`, using the pure simulator in `engine/particles.py` and shared video verification in `engine/effect_video.py`.

| Route | Purpose |
| --- | --- |
| `GET /api/particles`, `GET /api/particles/{id}` | Sets with owners, derived packs, source metadata, cells, renders and affirmation |
| `GET /api/particles/deleted` | Trash listing with Restore |
| `GET /api/generations/{id}/particles` | Per-cell owners, sets, approval offer and legacy results |
| `GET /api/packs/{id}/particles` | Sticker-set union, bursts and summed per-sticker counts |
| `GET /api/packs/{id}/stickers/{sid}/particles` | That sticker's sets and legacy gallery |
| `GET /api/packs/{id}/stickers/{sid}/particle-preview` | Free current-owned-set preview with saved motion for Echo |
| `POST /api/particles` | Create/import via owners and `from_effect`, `from_generation`, `from_slices` or `from_video`; free `from_stickers` recovery with a selected parent is being tested; imports can target an existing set |
| `POST /api/particles/{id}` | Rename, pick cells and save motion |
| `POST /api/particles/{id}/link`, `/unlink` | Free edits to sticker links |
| `POST /api/particles/{id}/more` | Quote first, confirmed AI generation, append to the same set |
| `POST /api/particles/{id}/preview`, `/render` | Same deterministic simulator; render verifies Telegram limits |
| `POST /api/particles/{id}/add` | Add render to destination pack and record affirmation |
| `POST /api/particles/{id}/duplicate`, `/delete`, `/restore` | Independent copy; soft delete; restoration |

Legacy `/api/effects/*`, `packs` input and `/assign`/`unassign` remain for one release. Pack input maps to its library stickers. It does not restore pack ownership. Member reads preserve their authorization boundaries; writes remain owner-only.

## 8. Particles on their own: from a request to Telegram (2026-10-05)

**The request.** `particle_sets.from_request(text, grid, kind)` reads the particles a sentence names, deterministically (no model): the lead-in ("create particles for", "particles on their own for") goes, the rest splits on commas, "and", "&", "+", "/"; each name is singular (a sprite is one thing), at most five words, at most the sheet's cells (four for 2x2). The names pass `effect_prompts.lint_plan` (no text, logos, people). The set is created with `plan {subject, elements, style}` and `request`; a sentence that names nothing is a 400 that asks for the particles. `POST /api/particles {from_request, grid?, kind?}` is the route.

**The Studio.** The composer has a **Particles** switch before the AI enhancer (`composer.js` `ptOn`, per browser). On, **Generate prompt** and Enter take the particle route (`particles.js` `spStudio`): the request becomes a stand-alone set, its sheet is priced (`/more {mode: drawn, estimate}`), **Generate · N credits** starts it (`/more {go}`), Cancel deletes the empty set (trash, restorable). The sheet is a particle batch (`G###`, `kind: particles`) that shows in Earlier batches with the **particles mark** top-right (`live.js` `histRow`, `.lv-pbadge`); opening it opens its set (`spOpenBatch`). The editor opens on the set itself (`spOpenSet`, scope `{set}`), headed by its name, "on their own". Only **still sprites** (Nano Banana) are offered on their own: the Kling animated path builds an effect from a pack's stickers and still needs a sticker (open, `docs/backlog.md`).

**Render, download, a pack.** A stand-alone set renders with no pack (`render` asks for a pack only when the set has packs or its particles are a pack's own stickers); its bursts are listed under **On their own**. Every READY burst has **Download** (the transparent 512 px WebM). **Make a pack of it** (`POST /api/particles/{id}/add {renders, new_pack: <name>}`) creates a pack named after the set and adds the burst as an animated sticker tagged ✨ (an empty pack has no emoji to borrow).

**Telegram.** The Bot API has no particle format: Telegram's own reaction effects are drawn by the apps, and a bot cannot make them. What a bot can upload is a **video sticker** (`createNewStickerSet` / `addStickerToSet`, `format: video`): WEBM, VP9 with alpha, 512 px on one side, at most 3 s, at most 30 fps, at most 256 KB, no audio, and at least one emoji. A rendered burst already is exactly that (the same checks as every animated sticker, `engine/effect_video.TECHNICAL`). So particles reach Telegram as a pack of bursts: **Make a pack of it** (or **Add to pack** into an existing pack), then the pack's normal **Send to Telegram**. Custom emoji (100x100) stay out (the product is stickers, CLAUDE.md).

**The chat.** "create particles for lipsticks and ribbons" with no pack named and no batch in focus asks: "Sure: lipstick, ribbon. For which pack, or on their own?" with chips for the recent packs, **The last pack, {name}**, and **On their own**; with no packs at all it offers them on their own. "... on their own" (or alone, no pack, without a sticker) shows the priced plan card ("Particles · on their own"); the go-ahead calls `tools.particles_alone`, which makes the set and starts its sheet; the started card has **Open the particles** (`agpopen`). A request that starts with "particles" needs no verb (`resolver.particles_intent`). Tests: `tests/test_particle_chat_owner.py` `ParticlesOnTheirOwn`, `tests/test_particle_more_modes.py`, `tests/test_particle_animated.py`.

## 7. How it is tested, and what is open

Fake providers, temporary libraries and scratch copies of `out/` only; the browser on a spare port, never the live server; nothing is generated for a check (`docs/testing.md`, the test budget). The guards: `tests/test_particle_rows.py` (rows, Save / Save as new, Add to pack and its parent link, adopting older runs and drawn sheets), `tests/test_particle_sets.py`, `tests/test_particle_owner.py`, `tests/test_particle_animated.py`, and the node tests `pack_particles`, `particles`, `particle_editor`.

Ordinary animated stickers in the destination pack are the settled delivery. Open (`backlog.md`): per-emoji motion (W25), separate Telegram effect delivery, sprite refinement from the chat, a permanent purge of deleted sets, and burst creation across packs (W27, [burst_plan.md](burst_plan.md)).
