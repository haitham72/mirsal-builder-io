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

**The grid must match (Haitham, 2026-10-14).** A prepared sheet serves only a request in its own grid: `sources.match_subject(root, prompt, grid)` measures each sheet once (`sheet_grid`: its gutters on a green or a blue screen, cached by path and mtime; one that cannot be measured counts as 3x3, as `pipeline.start` cuts it). The chat (`tools.prepared_match(prompt, grid)`), the Studio (`GET /api/prepared/match?prompt=&grid=`) and `pipeline.start` all pass the grid. Why: "original emojis kawai" in 2x2 was served from the 3x3 `generic_emojis` folder (the shared word "emoji"): 9 old stickers instead of 4 new ones (G149). All 202 prepared sheets measure 3x3 today, so a 2x2 request always goes live. The Studio composer has a **Grid** chip (3x3 / 2x2, remembered with Loop, `LIVE.grid`, `cpGrid()`); before it, every Studio sheet, plan and job request was hard-coded 3x3.
