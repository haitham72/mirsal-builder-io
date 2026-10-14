# Reaction effects: what is still open


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
