# Prepared instead of paid (`flow/sources.py`)

<sub>Part of [generation.md](../generation.md).</sub>

When Higgsfield is connected, a request that names a prepared subject is served from the watch folder instead of a paid call. The signature rule is one sentence: a request is served from the watch folder when one whole word of a prepared subject's folder name, singularised and ignoring generic, appears as a whole word of the request.

| request | served from |
|---|---|
| teddy bear for school | teddy_bear |
| teddy | teddy_bear |
| bear in a teddy costume | teddy_bear |
| bear | teddy_bear |
| emoji keyboard | generic_emojis |
| generic emojis laughing | generic_emojis |
| emojis | generic_emojis |
| emoji | generic_emojis |
| a dragon dancing | Higgsfield (no signature word) |
| school stickers | Higgsfield (no signature word) |

Preferring prepared is a setting, default on: `MIRSAL_PREFER_PREPARED` in `mirsal/.env` (wins when set), else the owner's switch in Settings (`out/prepared.json`, `POST /api/prepared/setting`; `GET /api/prepared/match?prompt=` says which subject matches). A prepared batch runs the same golden path and gates with the same screens; it records its real source (the watch folder, folder number, file names, `source.prepared: true`), costs 0 credits, and creates no job, task or ledger line. A fresh request starts at variant 1 again; Create more walks the remaining variants; **Make a new one** (the Studio header, the chat plan card's chip) draws a fresh provider sheet at the normal price. The batch carries a small Prepared chip for owner/admin only. Decided with Haitham, 2026-10-05: whole-word signature match (both near-misses match), variant 1 again, the chip for staff only.
