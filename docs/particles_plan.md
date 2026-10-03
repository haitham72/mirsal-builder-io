# Particles: the plan (Haitham, 2026-10-03, written at the end of a session)

**Status: phase 1 is BUILT (2026-10-03, branch `better_ui/ux`).** `flow/particle_sets.py` and every route of section 6 are in, with tests (`tests/test_particle_sets.py`, 22, over the real server on the fake CLI). **Still to build:** the screens of section 5 (phase 2), re-pointing the per-sticker gallery (phase 3), the chat intents (phase 4), Telegram delivery (phase 5). This file corrects the model the particles feature was built on; what exists today is in `docs/effects.md`; what is open is in `HANDOFF.md` sections 0a-0c.

## 1. What the task really is (the correction)

In Telegram, when you react to a message with an emoji, a **tiny particle burst** plays on that message. Mirsal makes that burst. The unit is **not a sticker**: a **sticker pack is only the group** the effect is attached to. All stickers of a pack share one set of particles. Barbie pack: hearts and flowers. Batman pack: bat signals. The particles are found "in the Barbie pack" as its *particle studio*.

What the first build got wrong (and what to change):

| built | correct |
|---|---|
| an effect belongs to one sticker; each sticker gets its own burst | a **Particle set** belongs to the **pack(s)** it is assigned to; every sticker of the pack uses it |
| the AI suggests elements, the sheet is drawn, then it "sits there": no way to say "use these particles as the pack's particles" | an explicit **Use as particle set** step that SAVES it as a durable asset |
| the gallery is per sticker (library sticker view, Studio section) | the gallery is per **pack** (and per **set**); a sticker only shows "the particles of its pack" |
| results live inside the `E###` working record | `E###` stays the *working session*; the durable thing is the **Particle set** `P###` |
| no generate-more / delete / rename / reuse | full lifecycle (section 4) |

## 2. Vocabulary

- **Particle set** (`P###`): a named collection of particle images (cells of a drawn sheet, or chosen stickers), the elements it was made from, the default motion, and where it is used. The durable asset.
- **Particle pack**: a set as the person sees it in the library (a card with its particles). A set can be **stand-alone** (assigned to no pack), assigned to **one** pack, or to **several** packs.
- **Burst** (rendered effect): a 3-second 512 px WebM (Telegram limits) made from a set with a motion preset, for a pack (one per preset; optionally one per emoji of the pack). These are what gets added to the pack / sent to Telegram.
- **Working session** (`E###`): today's effect record: analysis, suggestions, drawing, picking, previews. Ends in "Use as particle set".

## 3. Data model (all under `out/`, mirrored to Postgres later like everything else)

```
out/particles/P001/set.json     {id, name, created, user, elements[], source{kind: drawn|stickers|video, effect: E###, generation: G###, job: J###},
                                 cells[{n, file, status, warnings[], picked: bool}], motion{preset, params}, packs[pack ids], history[]}
out/particles/P001/cells/c01.png ...        the cut particle images (kept even when unpicked, so "generate more" never loses them)
out/particles/P001/renders/R001.webm        bursts rendered from this set for a pack (record: pack_id, preset, params, checks, added_to)
out/trash/particles/P001/                   delete = move here (rule 9 spirit: nothing is destroyed on a click; Restore puts it back)
```
A pack's list of sets is derived from `set.packs` (one source of truth); the library pack record gets no copy. Assigning is a list edit, never a copy of files.

## 4. Lifecycle and actions (the "generate more, save, delete" the screen was missing)

1. **Make**: from the Studio Particles tab, the Create > Particle effects screen, or the AI chat. Three ways to get particles: *Pack stickers* (free, pick existing stickers), *Drawn particles* (AI image sheet), *Video particles* (Kling 2x2 clip cut into cells).
2. **Suggest** (drawn): the vision model looks at the pack's own sheet and offers 8-12 text options (hearts, flowers, ...); the person picks N (4 for 2x2, 9 for 3x3).
3. **Draw** (price shown first, click = go-ahead): sheet returned, cut by the exact equal grid, every cell usable (warnings only; any rejected cell has **Use it anyway**).
4. **Pick**: tick the cells to keep.
5. **Use as particle set** (NEW, the missing button): names it (default "<pack> particles"), saves `P###`, and asks where it lives: *this pack* (default when started from a pack), *other packs* (multi-select), or *stand-alone*.
6. **Simulate** live with presets (burst, fountain, vortex, rain, confetti) and the sliders (explosion, gravity, vortex, count, spin), particle size (100 px default, x1-x4 for latency). The preview uses the set's picked cells.
7. **Render** a burst for a pack, **Add to pack** (animated sticker tagged with an emoji of the pack; Telegram needs >= 1 emoji tag).
8. **Generate more**: draws another sheet with the same elements (new variants) or new elements (suggest again) and **appends** the new cells to the same set; old cells stay, none are deleted; the person ticks what to keep.
9. **Manage**: Rename, Duplicate, Assign to a pack, Remove from a pack (the set stays), Delete (to trash, with Restore; a set used by packs says which and asks first), Save / Unsave a single cell (unpick keeps the file).
10. **Never a block a person cannot get past** (CLAUDE.md rule 10 and the standing rule): only Telegram's own limits (size, codec, format of the rendered WebM) fail a render.

## 5. Screens

- **Library > Particles** (new section/tab of the Library): every set as a card (the picked cells as a strip, name, "used in: Barbie, Princess" or "stand-alone", cost spent, created). Actions on the card: Open, Assign, Duplicate, Delete. A big "New particle set".
- **Pack page > Particle studio** (new panel on `#/pack/<id>`, the place the person expects): the sets assigned to this pack, the bursts rendered for it (looping thumbnails with Add to pack / Delete), and buttons: *Make particles for this pack* (starts the wizard with the pack chosen), *Use an existing set* (picker), *Generate more*.
- **Studio > Particles tab** (small wizard; built by agent C, see HANDOFF): steps 1-7 of section 4; ends on "Use as particle set".
- **Create > Particle effects** (pro studio): the same steps with every control; reads/writes the same sets.
- **Sticker view / pack grid**: no per-sticker gallery as the main thing. A sticker shows one line: "Particles of this pack: Barbie hearts and flowers" (a link to the pack's particle studio), and the pack grid badge counts bursts per pack, not per sticker.
- **AI chat**: "make particles for my Barbie pack" -> plan card (elements suggested, price, grid) -> go-ahead -> the set is saved and assigned; "also use them for the Princess pack"; "make more"; "delete the bat particles".

## 6. API (owner only for now; JSON first, screens second; each route also in `console/openapi.py`)

```
GET    /api/particles                       list sets (cells, packs, used_in)
POST   /api/particles                       {from_effect: E###, name?, packs?: [ids], picked?: [cells]}   -> 201 set   (Use as particle set)
GET    /api/particles/{id}
POST   /api/particles/{id}                  {name?, picked?, motion?}            rename / pick / default motion
POST   /api/particles/{id}/assign           {packs: [ids]}   and  /unassign {packs}
POST   /api/particles/{id}/more             {grid, elements?, go?}   price first, 409 unless go (draws a sheet, APPENDS cells)
POST   /api/particles/{id}/duplicate
POST   /api/particles/{id}/delete           -> out/trash/particles/ (Restore: POST /api/particles/{id}/restore)
POST   /api/particles/{id}/preview | render {pack_id, preset, params, sprite_px?, scale?}   (the existing preview / render, keyed by set)
POST   /api/particles/{id}/add              {renders: [...], pack_id}            animated sticker(s) into the pack
GET    /api/packs/{pack}/particles          the pack's sets and bursts (replaces the per-sticker counts)
```
The existing `/api/effects/*` routes stay (the working session) and `POST /api/particles {from_effect}` is the bridge. Engine functions live in a new `flow/particle_sets.py` (engine purity rule: no `psycopg`, `redis`, `langgraph`, model client in `engine/`).

**What phase 1 actually built, and where it differs from the sketch above:**

| planned | built (`flow/particle_sets.py`) |
|---|---|
| `POST /api/particles/{id}/more {grid, elements?, go?}` | **not built.** It needs a sheet job like `POST /api/effects/{id}/particles` (price first, `go: true`) that APPENDS to the set's cells. The screen cannot offer *Generate more* without it; nothing else in the model depends on it. |
| `POST /api/particles/{id}/preview` / `/render` / `/add` | **not built.** They need a burst record per (set, pack, preset) under `renders/`; `for_pack` already reads `renders[]`, so only the writers are missing. The simulation itself is `flow/effects.py sim_preview` / `sim_render` and needs re-pointing at a set's picked cells instead of an effect's group. |
| `GET /api/particles` cards | built: `id, name, created, user, kind, elements, packs, used_in[{id, name}], cells[], picked[], n_cells, n_picked, renders, credits` |
| delete → trash + restore | built, with the refusal that matters: a set assigned to packs answers **409 with the pack names** unless `{confirm: true}` (so a set in use cannot vanish under a pack). Ids are shared with the trash, so a restore can never collide with a new set. |
| motion | `motion{preset, params}` is linted against the engine itself: the preset must be in `engine/particles.PRESETS` and the params must pass `ParticleParams.from_dict`, so a set's motion can never mean something the renderer does not read (400 otherwise). |
| one source of truth | `set.packs` only. The library pack record gets no copy; `GET /api/packs/{id}/particles` answers `{pack_id, sets, bursts, counts}` (the old per-sticker counts are kept so nothing that reads them breaks). |

## 7. Migration and what to change in the code already written (do these first)

- **`flow/effects.py`**: `sprites` per group stays for the working session; add `set_from_effect()` (creates `P###` from `E###`: copies cells into `out/particles/`, records the source). The per-sticker `for_sticker` / `counts_for_pack` are re-pointed to pack level (`for_pack`); keep `for_sticker` as "the particles of the pack(s) this sticker is in".
- **Group semantics**: stop splitting stickers into VLM groups for drawn sets (one set per pack: agent A's `effect.set` already is one per effect; make "effect = pack" the rule). Per-sticker presets (mood) stay as the default *motion variety* inside a pack.
- **`console/packs.js`** Particles section of the sticker view and `ptBadge`: re-point to the pack.
- **`live.js`**: the Studio's replacement of "History of G###" shows the **pack's particle studio** for the pack(s) the open batch's stickers belong to (agent C is building it per sticker; change the data source, not the markup).
- **Existing data**: E008's drawn sheet (G100) becomes `P001` ("Batman Lego particles") through `set_from_effect`, E002's video cells likewise (a video set's cells are the keyed cell clips; its render is the clip itself).

## 8. Phases (each ends green and documented)

1. **DONE (2026-10-03, `e56146a`)** `flow/particle_sets.py` + routes + tests (set from effect, rename/elements/motion/picked, assign/unassign, duplicate, delete/restore with the in-use refusal, the pack listing). *Left out on purpose: `more`, `preview`, `render`, `add` — see section 6; `more` is the next backend step because the wizard's *Generate more* needs it.*
2. Library > Particles section + Pack page particle studio + the "Use as particle set" step in both wizards. The backend answers both reads (`GET /api/particles`, `GET /api/packs/{id}/particles`), so this phase is screens only.
3. Re-point the sticker view / pack grid / Studio section to the pack; remove per-sticker framing from copy.
4. AI chat intents (make, assign, more, delete).
5. Telegram: how the burst is delivered (open question 3).

## 9. Acceptance (what Haitham should be able to do)

Open a Barbie pack -> Particle studio -> *Make particles* -> choose 2x2 -> see "hearts, flowers, sparkles, ..." -> pick 4 -> price -> particles appear -> untick one -> **Use as particle set** "Barbie hearts" -> it is saved on the pack -> **Generate more** adds 4 more cells to the same set -> simulate with a preset -> render -> Add to pack. Then open the Princess pack -> *Use an existing set* -> "Barbie hearts" -> the same set, no new credits. Delete it from the library: both packs say it is gone, Restore brings it back. Nothing is ever blocked for a reason that is not Telegram's.

## 10. Open questions (for Haitham)

1. One burst per **pack** (all emoji of the pack the same effect), or one per **emoji** of the pack (different motion per emoji, same particles)? The plan assumes: one set per pack, one rendered burst per motion preset, tagged with the pack's emojis.
2. Should a stand-alone set be a **real library pack** of animated stickers (so it can be sent to Telegram on its own) or only a library asset?
3. How should the burst reach Telegram: as ordinary animated stickers in the pack (works today), or only as a file to download / use as a Telegram *effect*? (Telegram's own effect stickers are tied to Premium; today's plan is "animated stickers tagged with the emoji".)
4. Cost visibility: show the credits a set cost (sum of its sheets) on the card? (The plan says yes.)
