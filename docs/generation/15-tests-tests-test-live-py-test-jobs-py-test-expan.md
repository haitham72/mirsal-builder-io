# Tests (`tests/test_live.py`, `test_jobs.py`, `test_expander.py`; fake CLI, no credits)

<sub>Part of [generation.md](../generation.md).</sub>

Ticket-first and resume, the daily cap, the Kling 4k ban, catalog defaults, usage roll-up, prompt v2 / v3 properties, the AI enhancer (never while typing, off = no call, on = expand then send,
failure = fallback with a reason), references, a full run through the console (request → sheet job → stills → G2 → video sheet → G3 → Kling job → sliced), history paging, the gap and Loop,
Retry, the named export folders and their root, allow anyway / allow all, **the edge** (a preview writes nothing; Apply makes one snapshot; the same edge twice adds none; Undo restores; the
video and the pack commit a pending edge) and **the blue screen** (detect, key, video sheet, and the mark only when it is blue, on a synthetic blue sheet; the real failed batch G006 was re-run on a copy: 0/9 -> 9/9). The tests run through the tiers of `docs/testing.md` (the store and pool classes skip when Postgres is down); the full `unittest discover` is not a routine gate and runs only if Haitham asks.
