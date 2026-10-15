# Proposal: Size, Position and Lottie style settings (2026-10-15; Haitham: "do it")

Haitham, 2026-10-15: "this is just way too cluttered — `Size: Approved size | Fit motion | Same scale · Video size − 80% +`. Let's redesign this."
**A, B and C are built** (2026-10-15; Haitham approved the answers as built: Resize off = one scale, on = the hot spot matched to the approved still; Approved size / Fit motion / Same scale leave the screen; their details now live in `docs/engine-and-studio/09-engine.md` and `docs/api-parts/05-…`). **D is built too** (both steps; the details live in `docs/reaction/17-17-lottie-style-reactions.md`, "The Trapcode Particular-style settings"). Not built from D: Pre-run and Time scale (Global), Sticker-silhouette emitter and blend modes; they wait for a go.

## A. One-frame previews (the speed fix, everything else rests on it)

Today a size test re-cuts the whole clip: decode every frame of the cell, key, render, loop-close, encode a WebM ladder (2+ VP9 encodes). That is seconds per click.

Proposed: every Size / Position test renders **one frame** of the cell. Decode only that frame (`ffmpeg.decode_cell` with `max_frames=1`, seeking to it), key it, render it through the same window as the real cut, and return a PNG. The default is frame 0, the approved pose. A small scrubber (first / middle / last, or a slider) picks another frame. Expected cost is tens of milliseconds instead of seconds. The full clip is cut only on **Apply**, once, in the background, as today. Hot-spot data (B) is measured once, when the clip is sliced, so a preview never has to read all the frames.

## B. Size

Batch row, replacing the three buttons and the Video size stepper:

```
[✓] Resize    Size − 100% +    Reset
```

- **Resize off**: no per-sticker sizing. Every sticker is cut from its cell at one shared scale (today's *Same scale*), so the sizes stay as they are on the sheet. The Size stepper scales them all alike.
- **Resize on**: each sticker is sized by its **hot spot** (below), then the Size stepper multiplies.
- **Retired:** *Fit motion* (the union of every frame's outer pixels; one stray pixel or a tear flying to the edge shrinks the whole sticker) and *Approved size* (the first frame's outer box matched to the still). Both read outer pixels, so both give the uneven sizes you saw. Old batches that stored `keep_size` still read correctly; they are just not offered any more. Each removed control gets a `retired` entry in `ui_baseline.json`.

### The hot spot: can it weight 50% of the frames? Yes.

When a clip is sliced, the frames are already in memory as keyed alpha. One extra pass builds an **occupancy map**: for every pixel, the share of frames in which it is opaque. Then:

- **Core** = the pixels opaque in **at least 50% of frames**. A circular emoji's face is present in almost every frame, so it is core. Tear drops scattering outward are each in a few frames, so they fall below 50% and are left out. The core box is the face boundary, as you described.
- **Size** = the core box's longest side fitted to the target (the approved still's subject size, or a fixed share of the canvas). The drops are still drawn, and they may be cut off at the edge, but they no longer shrink the face.
- **Centre** = the core's weighted centroid (each pixel weighted by its occupancy), so a face that bobs is centred on where it spends its time.
- The 50% is one threshold (`hot_share`, default 0.5). A slider is possible but probably not needed. The stored metrics (`core_bbox`, `core_share`, `cut_off_frames`) show what it did. The proposal is **shown as the default value**; a person can still change Size or Position.

## C. Position (per sticker, on one thumbnail)

Clicking a sticker's size opens the **frame editor** on that one thumbnail, a card like today's test card. It draws the one frame from A on the checkerboard:

```
┌──────────── S3 · frame 0 ──────────────┐
│  ┌──────┬──────┬──────┐   [✓] Grid     │
│  │      │      │      │   Size − 92% + │
│  ├──────┼──(●)─┼──────┤   ← ↑ ↓ →      │
│  │      │      │      │   Centre       │
│  └──────┴──────┴──────┘   frame ▭──●── │
│     core box dashed       Apply Cancel │
└────────────────────────────────────────┘
```

- Drag the frame to move it; the arrow keys nudge 1% at a time; **Centre** puts the hot-spot centroid on the canvas centre. Size is the same stepper as the batch's, for this sticker only.
- **Grid on/off**: thirds, the centre cross and the 512 safe edge, plus the dashed core box from B, so you can see what Resize measured.
- Stored per sticker as `anim_offset: [dx, dy]` (a share of the canvas) beside the existing `anim_scale`. It is applied by shifting the render window at slice time, so it costs nothing extra and needs no new video. The engine stays deterministic, and both values go into the animation cache key.
- Apply cuts this sticker's clip once (free, from the stored video).

### Inline sliders under every animated tile (built 2026-10-15; Haitham: "each animated emoji -> add position x,y sliders and resize slider under every one")

Under every animated tile (`vsizeRow`, `studio-core.js`), three sliders for that sticker: **Size** 50–150%, **X** and **Y** −50%…+50% of the canvas. Tiles stay compact: the sliders hide behind an **Adjust** toggle per sticker (`ACT.vslopen`, `aria-expanded`, open state kept across redraws). A 409 busy (a cut still running) waits and sends once more instead of erroring (`postBusy`, 1 s apart, at most 12 tries — the server starts nothing on 409, so resending is safe). The readout moves on input (kept across poll redraws, so a drag is never reset mid-drag); one `POST /api/generations/{id}/position` (`{index, offset, scale, reslice}`, the existing route — rule 6: no new backend) goes out 500 ms after the release, so a drag cuts the clip once, free. An untouched release sends nothing. **Reset** (shown when the sticker has its own values) clears both through `/position` (`offset: null`) + `/video_size` (`scale: null`) with a single re-cut. The frame-editor button stays beside them: guide grid, frame scrubber and Centre live only there.

## D. Lottie style: settings modelled on Trapcode Particular

Today's sliders: Motion (Speed, Speed variation, Speed pulse, Pulse rate, Gravity, Swirl, Spread, Amount), Spin (Rotation, Flip, Flip variation), Shape (Size, Size variation, Size in/out), Fade out (start, duration, variation), Morph, Children. They are one flat list, and every particle is born at once from one point.

Particular's structure is Emitter → Particle → Physics → Aux System, with **over-life curves** everywhere. Mirsal bakes every particle's path into Lottie keyframes, so anything that is a function of time can be baked too; that is most of Particular. Proposed groups, existing sliders folded in:

| group | settings | notes / Lottie limit |
|---|---|---|
| **Emitter** | Type: Point · Ring · Box · Line · *Sticker silhouette* (born on the sticker's alpha edge); Emitter size X/Y; **Burst ↔ Stream** (all at t=0, or a birth rate over an emit duration); Direction + Spread (today's Spread); Velocity, Velocity random (today's Speed variation); **Velocity distribution** (even ↔ centre-weighted) | Stream raises the count; the 400-particle cap stays and is shown live |
| **Particle** | Life + Life random (replaces the fixed 1.8 s); Size + Size random; **Size over life** (curve presets: Grow, Shrink, Pop, Pulse, Custom 3-point); **Opacity over life** (presets; replaces the three Fade out sliders); Rotation, Rotation random, Rotation speed; Flip (kept); **Sprite time sampling**: Start at birth · Random start · Random still · Loop | time sampling is a precomp time remap (`tm`), which lottie-web 5.12 plays |
| **Physics** | Gravity (kept); **Air resistance**; **Wind X/Y**; **Turbulence** (affect position, affect size, scale, evolution speed, seeded noise; this subsumes today's Speed pulse and Pulse rate); Spin field (today's Swirl); **Bounce** off a floor line (floor Y, bounce, slide) | all baked into the hold keyframes, so the file size grows with motion but not with settings |
| **Aux system** (today's Children) | Emit: **at morph** (today) · **at death** · **at bounce** · **continuously (trail)**; aux per second; **inherit velocity**; aux life; aux size and opacity over life; aux source = the picked morph targets | trails multiply the count, so they get their own cap |
| **Morph** | kept as it is (Mirsal's own, Particular has no equivalent) | |
| **Global** | Seed (re-roll the same settings); **Pre-run** (start mid-burst); Time scale | |
| **Presets** | Particular-Designer-style tiles: Pop, Fountain, Confetti, Snow, Fireworks (burst → aux at death), Orbit, Rain of hearts | a preset only fills the sliders |

Not proposed, because Lottie and lottie-web cannot carry them reliably: motion blur, depth of field / 3D camera, shading and lights, and per-particle colour over life on a nested Lottie (lottie-web's Tint/Fill effects are partial). Blend modes (`bm`) work in the SVG renderer only for some modes; offered later, if wanted.

Layout: the groups as collapsible sections (Emitter open, the rest closed), each with a one-line summary when closed (`Physics · gravity 0.4 · turbulence on`), instead of one long list.

## Order, if approved

A (one-frame preview) → B (Resize + hot spot) → C (Position editor) → D (Lottie groups, in two steps: the restructure + over-life curves first, then Emitter types, Stream, Bounce and Aux modes).

## Decisions for Haitham

1. **Resize off = Same scale** (uniform, as on the sheet), **Resize on = hot spot**. Is that the meaning you want for the checkbox?
2. With Resize on, what is the hot-spot core fitted to: **the approved still's subject size** (the animation starts at the size you approved), or **a fixed share of the canvas** (e.g. the core fills 80%)?
3. May *Approved size* and *Fit motion* be retired from the screen (old batches still read correctly)?
4. Lottie: all of D, or the first step only (groups + over-life curves + time sampling)?
