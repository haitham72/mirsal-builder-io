# 8. One animation per emoji, pack variations on top (2026-10-13)

<sub>Part of [reaction.md](../reaction.md).</sub>

**The rule (Haitham).** Every predefined emoji owns **one fixed animation**, shared by every pack; a pack varies only sprite art plus Size/Energy. This closes W25 (per-emoji vs shared motion) as per-emoji motion with locked type. Batch create/recreate is untouched. The bank's human home is [emoji-bank.md](../emoji-bank.md).

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
