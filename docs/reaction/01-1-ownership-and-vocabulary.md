# 1. Ownership and vocabulary

<sub>Part of [reaction.md](../reaction.md).</sub>

A durable particle set (`P###`) belongs to its library stickers, never to a pack. Selected stickers can share a set. Stored `owner[]` records contain `{sticker_id, pack_id, generation, index}`; the library supplies the parent pack and provenance. Each sticker has ordered `particles[]` links, newest last. Pack views show the union of their stickers' sets; sticker views show their own sets.

A **sprite** is reusable still or animated artwork. A **burst** is the composition rendered from selected sprites and motion settings. `E###` is a working generation session, not an owner. Adding a burst as an ordinary animated sticker **affirms** its set in the destination pack: `in the pack ✓`. Neither rendering nor adding changes set ownership.

Unresolvable owners leave a **detached set**, retained visibly in Library > Particles with **Attach to a sticker**. **Stand-alone sets (Haitham, 2026-10-05).** A set may also stand on its own: no sticker owns it (`owner: []`), and it is fully usable: preview, render, download, or make a pack of it. This replaces the earlier rule that there is no stand-alone particle pack. It comes from a plain request ("create particles for lipsticks and ribbons"), through the Studio's **Particles** choice or the chat; see section 8.
