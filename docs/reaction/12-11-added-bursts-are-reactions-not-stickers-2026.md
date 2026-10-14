# 11. Added bursts are reactions, not stickers (2026-10-13)

<sub>Part of [reaction.md](../reaction.md).</sub>

`Add to pack` still delivers the burst as an ordinary animated pack sticker (Telegram and zip include it), but the screens never mix it into the stickers: the pack grid, its counts, the Library rows, the Home showcase and the burst-emoji vote (`_pack_emoji`) all skip stickers whose `source.particle_set` is set. Added bursts live in **Reactions in this pack** (view + delete). They carry no reaction rows, no creation buttons, no recovery entry and are never offered as reaction sources — a reaction never gets reactions of its own, so the sticker → reaction → sticker loop is gone.
