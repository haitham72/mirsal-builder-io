# 7. How it is tested, and what is open

<sub>Part of [reaction.md](../reaction.md).</sub>

Fake providers, temporary libraries and scratch copies of `out/` only; the browser on a spare port, never the live server; nothing is generated for a check (`docs/testing.md`, the test budget). The guards: `tests/test_particle_rows.py` (rows, Save / Save as new, Add to pack and its parent link, adopting older runs and drawn sheets), `tests/test_particle_sets.py`, `tests/test_particle_owner.py`, `tests/test_particle_animated.py`, `tests/test_emoji_motion.py` (the per-emoji map, the preset signatures, Size in / out, hue, the glyph, Lottie image layers), `tests/test_emoji_lottie.py` (the Reaction effects routes), and the node tests `pack_particles`, `particles`, `particle_editor`.

Ordinary animated stickers in the destination pack are the settled delivery. Open (`backlog.md`): separate Telegram effect delivery, sprite refinement from the chat, a permanent purge of deleted sets, and burst creation across packs (W27, [burst_plan.md](../burst_plan.md)).
