# Proposal: Size, Position and Lottie style settings (2026-10-15; Haitham: "do it")

Haitham, 2026-10-15: "this is just way too cluttered — `Size: Approved size | Fit motion | Same scale · Video size − 80% +`. Let's redesign this."
**A, B and C are built** (2026-10-15; Haitham approved the answers as built: Resize off = one scale, on = the hot spot matched to the approved still; Approved size / Fit motion / Same scale leave the screen). **D is built too** (both steps). Only the four Global / emitter items below are still open; they wait for a go.

## Built (details live in the area docs, not here)

- A. One-frame previews: every Size / Position test renders one PNG frame (`GET /api/generations/{id}/anim_preview`), the full clip is cut only on Apply. See `docs/engine-and-studio/09-engine.md` (`preview_frame`, `gates.anim_preview`).
- B. Size: `[✓] Resize + Size − 100% + Reset`. Resize off = Same scale (one shared factor, sheet-relative sizes kept); on = the hot-spot core box (`hot_share` 0.5) matched to the approved still. *Fit motion* and *Approved size* retired from the screen (old batches still read). See `docs/engine-and-studio/09-engine.md` (`size_window`, `anim_hotspot`, `anim_same_scale`).
- C. Position: per-sticker Size / X / Y sliders under every animated tile behind an Adjust toggle (readout on input, one `/position` POST 500 ms after release, Reset clears); the frame editor keeps guide grid, scrubber and Centre. See `docs/engine-and-studio/09-engine.md` (`anim_offset`, `cell_cfgs`).
- D. Lottie style: Particular's Emitter → Particle → Physics → Aux groups with over-life curves, presets and time sampling. See `docs/reaction/17-17-lottie-style-reactions.md` ("The Trapcode Particular-style settings").

## Still open (waits for a go)

From D's Global group and emitter options, not built: **Pre-run**, **Time scale** (Global), the **Sticker-silhouette emitter**, and **blend modes**. Require default-off behaviour and byte-identical default proof; do not add a runtime rasterizer merely for silhouettes. See `plan.md` item 5.
