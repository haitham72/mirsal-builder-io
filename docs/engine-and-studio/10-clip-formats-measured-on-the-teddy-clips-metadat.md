# Clip formats (measured on the teddy clips; metadata + alpha statistics only)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

| | `.mov` | `.webm` |
|---|---|---|
| Codec | ProRes 4444, `yuva444p12le` (real, high-precision alpha) | VP9 `yuv420p` + alpha side channel (`alpha_mode` tag) |
| Size / fps / length | 320x320, 24 fps, 4.04 s, ~10-16 MB | 320x320, 24 fps, 4.00 s, ~350 KB |
| Alpha | clean: median 255, soft edge only | **faint haze**: ~28k stray pixels/frame at values 1-3 (needs the floor above) |
| Edge contact | 51 of 97 frames have opaque pixels on the outer 2 px | none |
| Browser preview | Safari only | Chrome/Firefox |
Verdict: use `.mov` as the master (best alpha), `.webm` is acceptable after haze removal, and both need 320 -> 512 upscaling and trimming to <= 3 s. Neither is the final format: final output is the app's 512x512 VP9 WEBM (Telegram); animated WEBP (WhatsApp) is a later encoder behind the same validation.
