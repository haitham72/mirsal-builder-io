# 10. Migrating random sets onto the map (2026-10-13)

<sub>Part of [reaction.md](../reaction.md).</sub>

`particle_sets.adopt_emoji_map()` (CLI `python -m mirsal particles adopt-emoji-map`): idempotent, free. Keeps every byte; replaces free motion with the emoji map's motion for the set's first owner sticker's emoji token (else its first element); preserves tuned Size/Energy; writes `set.json.pre-emoji-map` once; history `ADOPT_EMOJI`. Sets already mapped (`emoji_motion.version: 1`) are skipped.
