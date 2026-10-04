# Particle sets and bursts

This is the particle area's architecture document; the filename remains for existing links. The ownership rework is implemented in the working tree. The compact editor, animated-sprite restoration and mistaken-pack recovery are being completed against [the flow design](sticker_particles_flow.md). The active implementation checklist is [particles_rework_plan.md](particles_rework_plan.md); retain it until those acceptance checks pass.

## 1. Ownership and vocabulary

A durable particle set (`P###`) belongs to its library stickers, never to a pack. Selected stickers can share a set. Stored `owner[]` records contain `{sticker_id, pack_id, generation, index}`; the library supplies the parent pack and provenance. Each sticker has ordered `particles[]` links, newest last. Pack views show the union of their stickers' sets; sticker views show their own sets.

A **sprite** is reusable still or animated artwork. A **burst** is the composition rendered from selected sprites and motion settings. `E###` is a working generation session, not an owner. Adding a burst as an ordinary animated sticker **affirms** its set in the destination pack: `in the pack ✓`. Neither rendering nor adding changes set ownership.

Unresolvable owners leave a **detached set**, retained visibly in Library > Particles with **Attach to a sticker**. There is no standalone particle pack.

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

Recovery for artwork accidentally saved as a sticker pack is **Use as particle pack → This sticker / All N stickers → Parent pack and target stickers → Use selected · free**. Source artwork is copied without deleting originals. The selected parent stickers own the set; supplying artwork does not make source stickers owners. This recovery action is being implemented; see the flow document's acceptance checks.

## 5. Galleries and chat

The batch section reads `GET /api/generations/{id}/particles`, displaying each READY cell's library sticker or approval offer, owner sets and affirmation. Source kind, job and credits are available on set cards. A sticker with any set cannot read "never created". The badge sums owner sets, legacy E### results and saved stickers once, rather than showing competing badges.

A cut sprite is a cell **inside** its row, never a particle set of its own. The sticker window reads `rows[]` and `drafts[]` from `GET /api/packs/{id}/stickers/{sid}/particles` (`particle_sets.rows_for_sticker`): each row shows `v#`, how it was made (*Sprites*, *AI image sprites*, *Kling from scratch*, *Animated sprites*, *The sticker itself*), its sprite count, credits, job, its newest burst (or a strip of its sprites), **Open**, and **Add to pack** / **In pack ✓**. A set shared by several stickers is a row under each of them in the sticker window, and in the Studio's batch **Particles** section it is ONE row drawn once, *Shared by S1, S2...* (`particles.js` `spSecShared`), with each sticker's block saying *Uses the shared particles above* instead of repeating it (Haitham, 2026-10-04: one Old Man set showed nine times). Drafts are listed apart and never lost. **Older effect runs** that produced something are adopted once as rows by `python -m mirsal particles adopt` (`particle_sets.adopt_effects`, idempotent, free, nothing moved): a Kling run's cut clips become one row of animated sprites, a simulated run's bursts become the row's renders, and runs that produced nothing stay hidden. A run whose **AI particle sheet was drawn but never saved** becomes a row of that sheet's cells (a sheet an older version cut as stickers is first cut again as particles, free, `pipeline.recut_as_particles`); the command takes the writer lock, so with the server running the recut goes through its route (`POST /api/generations/{id}/recut_particles`). A particle sheet held by a row (`pipeline._held_by_particle_rows`) is shown under its stickers and **left out of Earlier batches** (`GET /api/history`); its `G###` folder stays where it is. On 2026-10-04 G100 (E008, Batman Lego), G101 (E013, Barbie in love), G106 and G109 became rows this way. On 2026-10-04 this put the Batman Lego Kling take (E002, J039, 4 cells) under its sticker as a row instead of a stand-alone run (backup: `out/backups/particle-rows-2026-10-04/`). A run not yet adopted still shows as one grouped card (`runs[]`); raw `created[]`/`saved[]` remain for legacy clients.

The chat resolves an explicitly named set first; otherwise it prefers the focused sticker's newest owned set, then the focused set, then the only suitable set, then asks with chips. The explicit-name exception is intentional. Make/more preserve owner scope; linking to another sticker is free. A batch outside the library gets an approval card. The tools call the same engine functions as Studio; see [agent-and-chat.md](agent-and-chat.md).

Mirsal Echo is separate from AI-chat language selection. `preview_for_sticker` chooses only a set linked to the actual sent sticker, newest link first, and uses saved defaults. Unassigned stickers get no particles. The browser retains sticker IDs, anchors the preview to the replied-to outgoing sticker, and rejects stale/cleared message requests.

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

## 7. Acceptance and remaining work

Use fake providers and temporary libraries. Headless Chromium runs against scratch out on a spare port. Named/area Python tests run serially, with fast, node and `tests.test_js` as appropriate. Slow tier and full discovery are retired; neither is run or requested.

Acceptance prioritizes already-created sheets/clips copied to scratch, following stored effect/job/generation paths and free recut/import/recovery through the real simulator and Add. Diagnose stuck-state causes without fresh provider calls. Synthetic temporal fixtures supplement this evidence. Required coverage also includes scoped approval, no stale-run reopening or stale async replies, own-set-first chat with explicit-name override, summed counts, idempotent append/resume, animated frame changes inside particles, mixed static/video sets, full fake Kling-to-Add browser flow, free recovery preserving originals, warnings/override, soft delete/restore and purge retention. An injected completed fixture at Render is not an end-to-end video check.

Ordinary animated stickers in the destination pack are the settled delivery. Per-emoji motion remains a separate open design choice (W25). Separate Telegram effect/download delivery, refinement of sprites from chat, real v2 Kling/AI-sheet measurements, and permanent deleted-set purge remain open. The multi-pack burst-creation proposal is independent and unbuilt (W27, [burst_plan.md](burst_plan.md)).

Recorded-artifact debugging (2026-10-04) found connected failures rather than generation failures. E013/G101 already held a completed sheet but lacked a durable set; free import opens the simulator directly. Reopening an imported E run hid its entry; **Open in simulator** now reuses its saved set. E002's old clips lacked poster/timeline fields and a copied global job file; import decodes the existing clips, caches temporal frames and recovers recorded job/cost. G100 was classified as stickers by the older gutter layout path; free particle recut or slice/recovery import is available without generating another sheet. Settings previously lived only in previews/renders; explicit Save now persists motion and sizing, and stale preview results cannot replace a newer preset. Echo previously dropped sticker IDs and merely displayed a heart; it now requests current owned particles on reply/reaction. The sticker-window gallery exposed raw slice results as separate top-level cards and its loader targeted an obsolete lightbox element; the grouped-run read model and correct DOM target are being integrated and browser-checked. Scratch checks preserve original bytes and spend nothing.
