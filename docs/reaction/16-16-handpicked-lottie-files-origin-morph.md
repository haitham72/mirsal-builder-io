# 16. Handpicked Lottie files: origin → morph (2026-10-14)

<sub>Part of [reaction.md](../reaction.md).</sub>

**The decision (Haitham, 2026-10-14):** downloaded Lottie files beat generated vectors. The drop zone is `mirsal/lottie/*.json` (overridable with `MIRSAL_LOTTIE_DIR`); anything the person drops there is listed on the Reaction effects screen (`#/reactions`, "Handpicked Lottie files" with KB, dimensions, fps, frames, layers, image/base64 flags and a download link). Select emojis + Assign gives them an **origin** file and an optional **morph** file. The chat app plays origin, then morph.

- **Files are referenced, never rendered.** Assigning is instant like preset assignment. Oversized (>2 MB), unreadable and non-Lottie files are skipped; only `*.json` directly inside the zone counts. Missing zone = empty list, never an error.
- **Storage:** `library.json` `handpicked[token] = {origin, morph?}` beside `assign` (explicit picks only; Origin "none" clears the entry back to preset-only). Preset assignment is untouched and still runs on every Assign.
- **Contract:** `GET /api/particles/reaction-handpicked` → `{files: [{file, name, bytes, w, h, fps, frames, layers, images, base64}]}`; `GET .../reaction-handpicked/{file}.json` → raw bytes (traversal-safe 404s); `POST .../reaction-handpicked/assign {tokens (required, explicit), origin (""/null clears), morph?}` → `{assigned, cleared}`.
- **Export:** the zip carries the used files as `handpicked/<file>` and the manifest gains `"handpicked": {token: {origin, morph}}`; presets, `assign`, `unicode` and `slot` are unchanged. A handpicked token wins over its preset at the player; anything unlisted keeps the preset path byte for byte.
- **No preview renderer:** the server cannot rasterize arbitrary Lottie JSON (previews stay simulator-only WebP), so the dashboard shows metadata + download; the person knows their own files. No new CSS, no new ACT names, no route removed.
