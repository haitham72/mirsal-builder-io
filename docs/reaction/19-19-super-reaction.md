# 19. Super reaction: the whole screen, not a square (2026-10-20)

<sub>Part of [reaction.md](../reaction.md).</sub>

**The decision (Haitham, 2026-10-20).** "Reactions 2.0", the Instagram story heart: hold the reaction and small copies stream out of it; release and the whole screen plays. The simulator stays the one that makes the square reactions, but a super reaction's canvas is the **entire screen**. Particles are born along the **bottom** (the emoji box, no finer placement yet), rise across the screen, and the screen **lights up** with the emoji's colour. The colour is picked automatically, or set as a solid colour or a gradient. For now the sources are the files dropped in **`mirsal/lottie`**, read again on every request and listed by file name (drop a file and it appears).

## The engine (`engine/super_reaction.py`, pure)

- **Unit = the screen's short side.** The simulator's canvas unit (1 = the old square's side) becomes the short side, and the canvas runs `width/height` units along the long side, so nothing is stretched. Physics, sizes and `trajectories()` are unchanged. Every position is shifted after simulation (the simulator is translation-invariant), so `ParticleParams` gains no field.
- **Buckets.** A super reaction is made for the nearest of `BUCKETS` (phone 9:19.5, phone-tall 9:16, tablet 3:4, square, tablet-wide 4:3, desktop 16:10, desktop-wide 16:9, ultrawide 21:9; nearest by ratio). The canvas is `UNIT_PX` = 512 on the short side. The player plays it with `preserveAspectRatio: xMidYMid slice`, so the small difference is cropped, never stretched.
- **Bottom emitters.** `scene_params` keeps the look (`size_min/max`, `particle_size`, `spin`, zoom in/out, flip, speed variation, size curve) and replaces the placement:
  - a `line` emitter just under the bottom edge, launched up, with a 1.6 s stream and a 3 s clip;
  - **Rise** = `magnitude × screen height in units`, **Float** = `−gravity × height`, **Sway** = turbulence;
  - **Spread** ÷ height, because the fan opens with the launch speed;
  - a wide screen gets one emitter per unit of width (an emitter is at most one unit wide; ultrawide has 3).
  
  **Size** multiplies the look's own particle size (0.25–3 after the engine clamp). `SUPER_START` (count 36, size 1, rise 0.7, float 0.2, sway 0.4, spread 40, glow 0.55, pop on) was tuned by numbers. In every bucket, ≥83% of particle time is on screen; the 10th percentile of height reaches the top quarter and the 90th starts in the bottom quarter.
- **Glow.** One shape layer behind the particles: a full-screen linear gradient from the bottom edge up. It fades in over 0.35 s, holds at 70% until 1.6 s, and fades out by the end. Modes: `auto` (the dominant colour: `dominant_color` of the emoji glyph, or `lottie_rgba` of a Lottie's static fills and strokes), `solid` (`color`), `gradient` (`colors` = [bottom, top]; the top keeps 35%), `none`. lottie-web and lottie-ios both play it.
- **Pop.** The big one in the centre (0.45 × the short side): it scales in with an overshoot, holds a beat, and fades out by 1.25 s.
- **Sources.** Either the emoji slot (`emoji.png`, no base64, like every preset) or a Lottie document: `source=` embeds it once as precomp `L0` through `engine.lottie.export_lottie_burst(..., shift=(dx, dy))`. `shift` (0, 0) is the old burst byte for byte.

## Flow and HTTP (free; nothing is stored)

- `flow/lottie_reactions.py`:
  - `super_listing()` returns `{files: [{file, name, w, h, fps, frames}], buckets, glow_modes, keys, start}`.
  - `super_compose(out, file, aspect, glow, color, colors, settings)` uses the file's saved Lottie-style look (neutral defaults if unsaved) and returns `{file, name, bucket, aspect, glow, color, lottie}`.
  - Errors: 404 for a file not in the drop zone, 400 for a bad option.
- `flow/emoji_reactions.py`: `held_preset(out, token)` (the wall's rule, on the server) and `super_lottie(out, token, aspect, ...)`, the same for a bank emoji with its held preset. It has no route yet.
- Routes (native, `api/routers/reactions.py`, member): `GET /api/particles/super`, `POST /api/particles/super` with `SuperReactionBody` `{file, aspect, glow?, color?, colors?, settings?}`, and `POST /api/particles/super/export.zip` with `SuperExportBody` `{files?, glow?, color?, colors?, settings?}`.
- **Export, like Lottie style** (`super_export_zip`): `superReactions.zip` holds every dropped file (or `files`) for EVERY bucket, as `superReactions/<name>/<bucket>.json`, made with the sandbox's settings, plus `manifest.json` `{superReactions: [{file, name, color, buckets: {bucket: path}}], buckets, glow, color, colors, settings, seconds, unit_px}`. An app picks the bucket nearest its chat area's width / height and plays it with `xMidYMid slice`. In the sandbox, **JSON · desktop** and **JSON · phone** download what that screen plays (`<name>-superReaction-<bucket>.json`), and **Export all (.zip)** downloads the zip.

## The sandbox (`console/ui/features/reactions/super.js`)

It lives at Create › + New › **Super reaction** (`#/super`), and as the **Super Emojis** tab of the shared reaction tabs (Reaction effects and Library › Reactions, [18](18-18-reaction-tabs-emoji-lottie-packs-2026-10-15.md)). Every host is a `.sup-root`; the folder is listed on each visit.

- **Two resizable screens** follow the Mirsal app (`ref/ref-only.jpg`) and reuse the Chat screen's pieces (`.chat`, `.chh`, `.chm` bubbles, the `.chc` "Type a message" bar):
  - a desktop window: title bar, icon rail, the Chats list, the conversation. **The super reaction plays in the chat area only** (the conversation pane, `[data-supstage]`): the rail and the Chats list stay above it, like the app's panels and modals, and the bucket comes from the chat area's own width / height;
  - an iPhone: status bar, notch, chat, bar; it plays over the whole phone screen.
  
  Drag a corner to resize. Each frame shows its px size and bucket.
- **The gesture.** The reaction sits in the bar.
  - **Hold** (≥ 250 ms): copies of the file rise from it, faster the longer the hold. The full-screen file is requested at once, so it is ready by the release.
  - **Release** on the button: the screen plays, made for that frame's current shape. The layer covers the rail and menus with `pointer-events: none`.
  - Dragging off the button cancels; a short tap plays nothing.
- **Controls** (each sent to the server, rule 6): Lottie (the folder by name), Light (Auto, which shows the picked colour after a play; Solid; Gradient; None) with colour pickers, and Size, Amount, Rise, Float, Sway, Spread and Glow.
- **One frame while tuning** (Haitham 2026-10-20, like the emoji pack's first-frame preview). Moving any slider, colour or Light mode shows ONE still frame in every screen instead of playing. It is the super reaction made for that screen's shape, stopped (`goToAndStop`) at **Animation frame** (0–100%, default 80%). The frame slider only moves the playhead of the animation already loaded (about 10 ms); other settings ask the server again 140 ms after the slider stops (about 20–200 ms a compose, cached by settings and shape). Holding the reaction clears the still; Reset clears it and returns the frame to 80%. Animation frame is a viewer control (the playhead), so the server never needs it.

Tests: `tests/test_super_reaction.py` covers buckets, whole-screen coverage, wide emitters, emoji-free determinism, glow modes and errors, the dominant colour, the Lottie source and its colour, `shift` (0,0) byte-identity, and the folder listing and compose errors. Browser check (isolated :8797, providers off):
- the desktop and phone frames play;
- Library › Reactions › Super Emojis and Reaction effects › Super Emojis mount;
- no horizontal overflow at 390 px;
- no console errors.

**Open.**
- Emoji-bank super reactions (`super_lottie`) need a route and a picker in the sandbox.
- The real chat apps (desktop HTML, iOS lottie-ios) are not wired.
- A visual verdict is Haitham's.
