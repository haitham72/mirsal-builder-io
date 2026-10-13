# Reaction sets and bursts (renamed from Particles, 2026-10-13)

This is the reaction area's architecture document (formerly `docs/particles.md`; that path stays as a pointer). Reactions are owned by library stickers; every saved version is a row under its sticker; the editor offers three equal sources; animated sprites play inside the simulator; mistaken sticker packs can be recovered as reactions. Accepted by Haitham in his browser on 2026-10-04. Open work is in `backlog.md` (reactions). User-facing copy says **reaction** everywhere; API routes (`/api/particles`), storage (`out/particles/P###`) and internal names keep `particles` for compatibility.

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

Fake providers, temporary libraries and scratch copies of `out/` only; the browser on a spare port, never the live server; nothing is generated for a check (`docs/testing.md`, the test budget). The guards: `tests/test_particle_rows.py` (rows, Save / Save as new, Add to pack and its parent link, adopting older runs and drawn sheets), `tests/test_particle_sets.py`, `tests/test_particle_owner.py`, `tests/test_particle_animated.py`, `tests/test_emoji_motion.py` (the per-emoji map, the preset signatures, Size in / out, hue, the glyph, Lottie image layers), `tests/test_emoji_lottie.py` (the Reaction effects routes), and the node tests `pack_particles`, `particles`, `particle_editor`.

Ordinary animated stickers in the destination pack are the settled delivery. Open (`backlog.md`): separate Telegram effect delivery, sprite refinement from the chat, a permanent purge of deleted sets, and burst creation across packs (W27, [burst_plan.md](burst_plan.md)).

## 8. One animation per emoji, pack variations on top (2026-10-13)

**The rule (Haitham).** Every predefined emoji owns **one fixed animation**, shared by every pack; a pack varies only sprite art plus Size/Energy. This closes W25 (per-emoji vs shared motion) as per-emoji motion with locked type. Batch create/recreate is untouched. The bank's human home is [emoji-bank.md](emoji-bank.md).

**The map.** `engine/emoji_motion.py` (pure, rule 3): `CORE_MOTIONS` pins the 36 mood tokens to a preset + param overrides; any other bank token falls back deterministically by hash onto the five simulator presets.

**The five presets are measurably distinct** (`engine/particles.PRESETS`; `tests/test_emoji_motion.py` checks every preset and every pinned token on `trajectories()`, numbers only):

| preset | signature | measured on the preset (median) |
| --- | --- | --- |
| `burst` | radial outward, a 360° fan from the centre | tangential/radial speed ratio ≈ 0.3 |
| `fountain` | origin (0.5, 0.8), spread ≤ 90°, launched upward, falls back | mean vertical speed over the first 0.2 s < 0 (up) |
| `vortex` | `|vortex|` ≥ 1.5, magnitude ≤ 0.6; tangential ≫ radial; stays on the canvas | ratio ≈ 5, ≥ 2 turns, 90% of samples within 0.5 of the origin |
| `rain` | origin (0.5, 0.1), magnitude ≤ 0.5, gravity down, spread ≤ 120° | > 80% of visible motion goes down |
| `confetti` | ≥ 48 particles, gravity ≤ 0.5, spin ≥ 2.5, spread ≥ 150° | under 60% of motion goes down: it scatters |

**Swirl is a flow field** (2026-10-13). Before, `vortex` added a tangential push proportional to the distance from the origin, so particles flung off the canvas (1.5 canvas widths) after less than half a turn: a burst that started elsewhere. Now a particle's velocity relaxes toward a rotation about the origin (`VORTEX_W` 7.5 rad/s per unit of `vortex`, rate `VORTEX_RELAX` 2.5/s, weaker swirls in proportion) and a centripetal term keeps the orbit. At `vortex` 0 the step is exactly the old one: a burst, fountain, rain or confetti with no swirl renders **byte-identical** frames to the previous engine (checked against the committed engine on 2026-10-13). A saved set with a non-zero Swirl renders the new swirl from now on; its stored WebM files are untouched. The vortex, rain and confetti preset values and the 36 pinned rows were retuned to their signatures (vortex rows `scared`, `confused`, `think`, `eye-roll`, `scheme`, `shrug`; `eye-roll` and `scheme` turn counter-clockwise). Motion sentences come from the existing `FACE_SENTENCES` / `BODY_SENTENCES` (`generation/actions.py`). `flow/particle_sets.emoji_motions()` merges the map with `generation_bank()` (>1800, glyph + order) for the read-only wall: `GET /api/particles/emoji-motions` (alias `/api/particles/reactions`).

**The two views (the anti-chaos).** The pack's Reaction studio has a scope switch: **This pack** (default) shows `GET /api/packs/{id}/reactions` (`reactions_for_pack`): one row per emoji in the pack — glyph, token, inherited preset + motion sentence (locked), its stickers and sets; art is changed per row, Size/Energy are the only tunable sliders. **All 1800** shows the generic wall (glyph + token + preset chip, search, first 120 matches): read-only, no Edit/Duplicate/Delete, motion never tunable there. Five legacy surfaces (Library cards, pack studio cards, sticker rows, batch section, `#/effects`) keep working; new work goes through these two views.

## 9. Three outputs, all optional (2026-10-13)

WebM VP9+alpha stays the primary and only Telegram delivery. Kling-animated sprites stay the paid path. **Lottie JSON** is the third, web-only output: `engine/particles.export_lottie(p, png_or_pngs, size=512)` maps the deterministic trajectories onto **image layers** (`ty: 2`) over the real sprite, embedded once as a base64 PNG asset (`e: 1`), so a standard player (lottie-web, the LottieFiles preview) plays the picture flying. Before 2026-10-13 it emitted white ellipse placeholders, which is why players showed shapes or nothing. Each layer lives from its particle's birth to its death (`ip`/`op`) with one hold keyframe per frame for position, scale, rotation and opacity; layers are ordered biggest on top, as `simulate()` draws them. Lottie cannot turn an image's hue, so with `hue_var` > 0 each particle's hue is rounded to `HUE_STEP` (10°) and every step in use is one more tinted asset. `POST /api/particles/{id}/export-lottie` embeds the set's picked sprites (an animated sprite as its fullest frame: Lottie image layers are stills) and is a 409 when the set has none; it stores `renders/L###.lottie.json`; the burst panel's **Lottie** button downloads it. No new dependency (stdlib JSON + Pillow). Limits: 300-750 KB per file (keyframes per frame per particle, plus one PNG per hue step), renderer differences, Telegram never reads it.

## 10. Migrating random sets onto the map (2026-10-13)

`particle_sets.adopt_emoji_map()` (CLI `python -m mirsal particles adopt-emoji-map`): idempotent, free. Keeps every byte; replaces free motion with the emoji map's motion for the set's first owner sticker's emoji token (else its first element); preserves tuned Size/Energy; writes `set.json.pre-emoji-map` once; history `ADOPT_EMOJI`. Sets already mapped (`emoji_motion.version: 1`) are skipped.

## 11. Added bursts are reactions, not stickers (2026-10-13)

`Add to pack` still delivers the burst as an ordinary animated pack sticker (Telegram and zip include it), but the screens never mix it into the stickers: the pack grid, its counts, the Library rows, the Home showcase and the burst-emoji vote (`_pack_emoji`) all skip stickers whose `source.particle_set` is set. Added bursts live in **Reactions in this pack** (view + delete). They carry no reaction rows, no creation buttons, no recovery entry and are never offered as reaction sources — a reaction never gets reactions of its own, so the sticker → reaction → sticker loop is gone.

## 12. Library Create flow (2026-10-13)

Library > Reactions > **Create** offers two paths. **Predefined** is the emoji bank (`GET /api/particles/bank`): every token with `finished` (a covering set holds a READY render) or `unclaimed` state, multi-select up to 9, then **Build**: one stand-alone set per emoji (`from_request` with the bank token name), the free procedural sparkle when it has no drawn cells (`default-sprite`, idempotent), and the default animation presented as a preview with the fixed per-emoji motion. **Approve** renders (free) and the build card collapses into the finished list, exactly like a finished reaction; custom sprites remain available later through the set card's Generate more. A finished token rebuilds as a new take. **Stickers** picks one of your stickers and continues in the Studio Particles tab. Nothing here spends without the priced Generate-more step, which stays inside the set card.

## 13. Reaction effects: one emoji, flying as itself, to Lottie (2026-10-13)

**The product decision.** Create > New > **Reaction effects** (`#/effects`) is the emoji bank **only**: no packs, no stickers, no Kling, no sheets, no "create from sheet" (all of those stay in the Studio). The one flow: **open an emoji → its fixed animation plays, flying as the literal emoji → Download Lottie**.

**The sprite is the glyph.** `engine/particles.render_emoji(glyph, px)` draws the Win+. glyph with the system's colour emoji font (`EMOJI_FONTS`: Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji; a bitmap font is opened at its own strike size) and trims it to its alpha box like `trim_sprite`. Exactly one sprite exists: no picker, no Generate more. Without a text-shaping library a ZWJ sequence draws as its parts side by side. The glyph art belongs to the font's vendor: check its licence before a file leaves the office. A machine with no colour emoji font answers 503.

**The only controls** (strict `ParticleParams` fields, unknown key → `ValueError`):

| field | range | screen default | effect |
| --- | --- | --- | --- |
| `size_in_dur` | 0–1.5 s, ≤ lifetime/2 | 0.4 | each particle's scale ramps 0 → 100% over this long after birth |
| `size_out_dur` | 0–1.5 s, ≤ lifetime/2 | 0.4 | … and 100% → 0 over this long before death |
| `hue_var` | 0–180° | 25 | each particle's colours turn by a seeded hue in [−hue_var, +hue_var] |
| preset | its own, or one of the five | its own | an override takes that preset's own look (the token's pinned values belong to its own preset) |

The envelope multiplies the pop-in and the flight growth, never replaces them. The hue is one draw per particle from the same `default_rng(seed)` stream, drawn **last**, so every earlier draw (positions, sizes, spin) is unchanged; it is the CSS `hue-rotate()` matrix (a turn about the grey axis: linear, so exact on premultiplied colour; alpha untouched). Hue-shifted emoji are stylised, not the platform glyph; `hue_var` 0 is the glyph's native colours. The dataclass defaults are 0 / 0 / 0, so every older set, preview and render is unchanged; only this screen starts at 0.4 / 0.4 / 25.

**Deterministic.** Same emoji + options + seed → the same params, the same preview file and byte-identical Lottie JSON on the same machine (the glyph comes from that machine's emoji font).

**The contract.** `flow/particle_sets.py`: `emoji_token` (a token name or the glyph, `actions.token_for_emoji`; 409 outside the bank), `emoji_burst` (motion + override + options → `ParticleParams`), `emoji_preview` (cached WebP under `out/particles/emoji/<token>/previews/`), `export_emoji_lottie` (stores `out/particles/emoji/<token>/renders/L###.lottie.json` + `L###.png`, appends to that emoji's `emoji.json` with history `LOTTIE`; no `P###` set is made, and the set scans never see the `emoji/` folder). Routes: `POST /api/particles/emoji-preview`, `POST /api/particles/emoji-lottie` ([api.md](api.md)). The screen is `effects.js` `fxSetup` / `fxEkOpen` ([design.md](design.md) §4, Create's tabs). Tests: `tests/test_emoji_lottie.py`, `tests/test_emoji_motion.py`, node `effects_core`.

**Verified** (2026-10-13): `kiss` (burst, 28 layers, 329 KB), `scared` (vortex, 36 layers, 314 KB) and `celebrate` (confetti, hue 90°, 64 layers, 19 assets, 742 KB) played in lottie-web 5.12.2 (canvas renderer): at frame 30 each frame held 400-840 distinct colours, the glyph itself.
