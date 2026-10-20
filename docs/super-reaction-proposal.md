# Super reaction (Reactions 2.0) — proposal, waiting for a go

Requested by Haitham, 2026-10-20. Nothing is built yet.

## The interaction (modelled on Instagram's story heart)

1. **Hold** an emoji's reaction button. While the finger or mouse stays down, small copies of the emoji stream out of the button. The stream gets denser the longer the hold lasts, up to a cap.
2. **Release.** The full-screen scene for that emoji plays over whatever is on screen. Examples: 🔥 fire climbs up from the bottom edge, 🎈 balloons rise and sway off the top, ❤️ a big heart pops in the centre with a heart shower.
3. A short tap is still an ordinary reaction. A hold that is cancelled (dragged off the button) plays nothing.

## Why the existing presets are not enough

Today every preset is a Lottie on a square 512 canvas. Scaling that canvas to a 9:19.5 phone or a 16:10 desktop either crops the scene or letterboxes it. A scene like "fire along the bottom edge" has to know where the edges are.

## Design: one scene, three layers, laid out against the viewport

A super reaction is a **scene** in normalized units: x/y as a share of the viewport's width and height, and sizes as a share of `min(w, h)`. The client measures the visible area and lays the scene out:

| layer | anchored to | made from | example |
|---|---|---|---|
| **hold stream** | the pressed button (its screen position) | the emoji's existing preset (`{motion}_{NN}`), looping, rate grows with hold time | hearts spraying up from the button |
| **ambient** | the viewport edges | a full-screen Lottie generated per **aspect bucket** (phone portrait ≈ 9:19.5, tablet ≈ 3:4, desktop ≈ 16:10, square) by the existing engine with a non-square `W×H` and edge emitters (`line` on the bottom edge, `box` below the screen) | fire along the bottom, balloons rising |
| **finale** | the viewport centre, sized to `min(w, h)` | a square Lottie (a big emoji pop: scale overshoot then fade) | the big heart |

The client picks the closest aspect bucket and plays it with `preserveAspectRatio: xMidYMid slice`. The small difference to the bucket is then cropped, never stretched. All three layers keep the emoji-free rule: one external `emoji.png` slot, no base64.

**"Checks the current screen":** web uses `window.visualViewport` (width, height, offset) and CSS `env(safe-area-inset-*)`. iOS uses the view's `safeAreaInsets`. The overlay is `position: fixed`, `pointer-events: none`, and sits above the app's menus, so the content stays clickable while the scene plays. Rotating or resizing during playback re-lays out the layers (the bucket is chosen once per play).

**iOS** plays the same files with lottie-ios: three `LottieAnimationView`s in a non-interactive overlay window. The emoji picture is supplied through an image provider, which works the same way as the slot today.

## Engine and contract (rule 11: engine first, screen second)

- `engine/lottie.py`: `export_lottie(..., size=(W, H))` accepts a non-square canvas, and the emitters accept edge anchors. This stays deterministic, so a test can pin it.
- `engine/super_reaction.py` (new, pure): `scene(token) -> {hold, ambient: {bucket: lottie}, finale, timing}`. `timing` holds the hold-rate curve, the max hold and the finale delay.
- The library gains a `super` preset per emoji, in the same `library.json` as the existing assignments. It defaults to the emoji's own motion, plus a few named scenes: `fire_floor`, `balloon_rise`, `heart_pop`, `confetti_rain`, `snow_fall`.
- `GET /api/particles/super/{token}` returns the scene. Export all adds `super/{token}/…` and a `super` map to `manifest.json`, so the chat app ships the files itself.
- Web console: one overlay module, plus a press-and-hold on the Reactions screen's preview so it can be tried in the app.

## Decisions for Haitham

1. **Where can a person hold to super-react?** Only the Reactions screen preview (a tester), or also chat messages and stickers in the console?
2. **Desktop overlay:** the whole window above every menu (recommended), or only the content area between the menus?
3. **Scope of the first cut:** 5 named scenes (fire, balloons, hearts, confetti, snow), with every other emoji getting an automatic scene from its motion. Or a scene for every emoji from day one?
4. **The Instagram reference JSON:** put it in `docs/inputs/` and the timing (hold-rate ramp, finale length, easing) will be matched to it.
