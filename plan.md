# Lottie reactions: pure Lottie bursts from `mirsal/lottie/` (next, Haitham 2026-10-14)

**For implementation by another LLM, on branch `handpicked-lottie`.** A new, separate logic beside Reaction effects: no emoji bank, no Windows/iOS glyphs,
no motion presets (burst/fountain/vortex/rain/confetti). Every particle is a Lottie animation. Read first: `docs/reaction/16-16-handpicked-lottie-files-origin-morph.md`
(the drop zone, already built), `docs/reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md` (the settings table), `mirsal/mirsal/engine/particles.py`
(`ParticleParams`, `trajectories`), `mirsal/mirsal/engine/lottie.py` (`_layers`, the slot export). The old Reaction effects screen stays untouched (rule: no action disappears).

## Fixed decisions (Haitham)
- **Source:** every `*.json` Lottie in `mirsal/lottie/` (`MIRSAL_LOTTIE_DIR`), 20-80 files, imported by file name (the name is the id). The existing
  `handpicked_files()` scan (size cap, Lottie check) is reused. Nothing else is listed.
- **Screen:** a grid of the files by name (`#/lottie`, rail entry "Lottie reactions"); a click opens the editor on that file: the 512 x 512 viewer
  (viewer = export, the Border checkbox kept) and the settings.
- **Default settings:** one neutral default (the `ParticleParams` defaults: burst from the centre, no vortex, no motion preset), **2 s** clip
  (`REACTION_SECONDS`), every current slider kept (Speed, Gravity, Swirl, Rotation, Amount, Spread, Fade out start / duration / variation, Size,
  Size variation, Size in / out).
- **Each particle is its own instance of the Lottie** (its own playhead from its birth), never a raster.
- **The export embeds the origin Lottie and every morph target every time:** one self-contained JSON; each source becomes a precomp asset
  (`assets[{id, layers, ...}]`, its own `w/h/ip/op`); each particle is a precomp layer (`ty: 0`, `refId`) with the trajectory keyframes
  (`p`, `s`, `r`, `o`), scale = particle px / source long side, `sr` (time stretch) = 30 / source fps so the source plays at its own speed.
  Asset ids are prefixed per source so two files never collide. No images, no base64 added by us.

## Build
1. **Morph** (per file: origin -> 1 or more targets). Settings `morph_targets: [file names]`, `morph_at` (s after birth), `morph_var` (+- s per particle),
   a fixed short crossfade (0.15 s). Each particle picks one target (seeded). Export: two precomp layers per particle on the same trajectory,
   origin fades out / target fades in over the crossfade; the target's playhead starts at the morph moment. No target = no morph.
2. **Morph auxiliary (children, 1 level):** setting `children` (0-12, 0 = off). When a particle's **fade starts** it bursts `children` new
   particles from where it is at that moment, with the **exact same settings** (same physics, fades, size, morph) and its own seeded fan; children
   never spawn children. Engine: a second pass in `trajectories()` (or a `child_bursts()` beside it) whose origins are the parents' positions at
   their fade start and whose spawn frames are those frames; children die by `duration - QUIET_TAIL` like everyone. The layer count grows
   (count x (1 + children)): cap the total (e.g. 400) with a clear 400 error.
3. **Cheap spin:** setting `flip` (turns per second, 0 = off) + `flip_var`: the particle's horizontal scale goes 100% -> -100% -> 100% (cos of
   its phase), a card flip, no rotation. Export: the `s` keyframe's x component; preview identical.
4. **Speed variation + pulse:** `speed_var` (0-1: launch speeds spread +-share around Speed; today it is a fixed U(0.5, 1.1)) and
   `speed_pulse` (0-1 amplitude) with `pulse_hz`: each particle's velocity is multiplied by `1 + amp * sin(2 pi f t + seeded phase)` during the
   integration, so particles swell and slow, not all at the same speed.
   New random draws go AFTER every existing draw (older bursts keep their bytes); every new field defaults to off.
5. **Storage + API** (native FastAPI routes with pydantic, rule 11 + server rules): `out/particles/lottie/library.json`
   `{files: {name: {settings, morph_targets, ...}}}`. `GET /api/particles/lottie-reactions` (files with metadata + saved settings),
   `POST /api/particles/lottie-reactions/{name}` (save settings; 400 for an unknown key, 404 for a file not in the zone),
   `GET /api/particles/lottie-reactions/{name}.json` (the composed, self-contained export), `GET /api/particles/lottie-reactions.zip` (all + manifest).
6. **Viewer:** the browser cannot show this burst from a WebP (the server cannot rasterize Lottie). Default: bundle **lottie-web** (MIT, a pinned
   file under `console/vendor/`, no CDN at runtime) and play the exported JSON itself in the 512 viewer, so viewer = export byte for byte.
   (Haitham may choose otherwise; the alternative is a server renderer such as rlottie, a new native dependency.)
7. Docs: a new section file `docs/reaction/17-...lottie-reactions.md` + its line in `docs/reaction.md`; the routes in `docs/http_route_inventory.md`
   and `docs/api-parts/`; `ui_baseline.json` for the new rail entry. Tests: engine numbers only (children origins/spawns, flip scale sign, pulse,
   speed spread, morph layer timing, precomp ids unique, `sr`), one route test, a JS test for the grid/editor. Narrowest runs only.

## Open (ask Haitham only if blocking)
- Does a morph target keep the origin's size, or its own aspect? (Default: same particle px, each source scaled by its own long side.)
- Does a child burst inherit the parent's current Lottie (origin or target) or always start from the origin file? (Default: the origin file.)

---

# Earlier: Reaction effects UI items still open

**For implementation by another LLM.** The open items of the reaction UI spec (2026-10-13). Built and removed from this plan: the rename to "reaction"
(labels only; `/api/particles`, `out/particles/`, internal names unchanged), Lottie export, the Size in / Size out envelope (scale over time), the
"Recovered" naming, the pack's own "Reactions in this pack" section, and the simplified header. Architecture: `docs/reaction.md`, `docs/effects.md`;
the look: `docs/design.md`. Find code by name, not by line number (the files moved since the spec was written).

Keep API routes, storage and internal variable names unchanged; only labels and UI move. Test on a copy of `out/` (`MIRSAL_OUT=<copy>`), in both themes and below 760 px.

## UI cleanup

1. **Set card** (`spSetCard`, `console/particles.js`): the cell / picked counts and "made for N stickers" only on hover; the cost line only when something was spent;
   Duplicate / Rename / Delete in a "⋯" menu. Keep: preview strip, name, Open, Attach / Add to pack.
2. **Sticker unlink list** (the `psunassign` rows in the open set card): hidden by default behind "Manage stickers", with "Attached to N stickers" as the summary.
3. **Motion presets**: show only the selected preset with a "Change" button (or a `<details>`) instead of every chip at once.
4. **One Advanced section** (the two `<details class=fx-adv>` in the burst editor, "reactions, spin" and "sprite resolution"): one collapsed
   `<details>` whose summary reads its values ("Advanced: 28 reactions, spin 1, 100 px").
5. **Burst rows** (`pkBurst`, `console/packs.js`): drop the preset name (the set card shows it): "burst · ready · in <pack>", keep the download.

## Pack view

6. **No tabs** (`PKTAB`, `ACT.pktab`, the `.pk-tabs` segment in `drawPack`): always the stickers grid with its selection bar first, then the reactions
   section (`pkPsHtml`), with a separator; delete `PKTAB` and `pktab`.
7. **"Open in Studio" on Library pack cards**: a button that opens the pack's stickers in the Studio (the single-sticker view already has one: `lcopenstudio`).

## Features

8. **"Open and save" on a set card**: opens the editor on that set and saves it as a new row on close or on an explicit Save.
9. **Erosion in the reaction Timeline**: `erosion_px` (default 0) on `ParticleParams` (`engine/particles.py`), applied to each sprite's alpha after keying
   and before despill (a morphological erosion; `engine/chroma.py` already has the keyer's), and a slider beside the motion controls.

Each new control is read by the backend (rule 6), and `tests/test_ui_inventory.py` must stay green (a removed action needs a `retired` entry in `tests/data/ui_baseline.json`).
