# Keyers: ready-made options (for photos / non-green input; Phase 3C and 5)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

Chroma key is the default for generated green-screen sheets: exact, fast, model-free, and it does not flicker across video frames. For an ordinary uploaded image turned into a sticker (no green), use an existing matting library instead of writing one:

| Option | Fit | Notes |
|---|---|---|
| **rembg** (U2-Net, ISNet-general-use, BiRefNet via onnxruntime) | default for "upload a photo -> sticker" | pip + one weight file, CPU-capable; download weights once on a connected PC and load by path (`U2NET_HOME`) |
| transparent-background (InSPyReNet) | alternative with strong edges | pip + weights |
| BiRefNet / RMBG-2.0 | best hair/fur edges | check each model's licence before shipping (RMBG-2.0 is, as far as I know, non-commercial) |
| SAM 2 | click-to-select one subject in a busy photo | heavy, optional |
| OpenCV `grabCut` | zero-download fallback, needs a rough rectangle | already in `cv2`, weakest quality |
| Robust Video Matting | video without green | heavy and flickers; opt-in only |

Integration: one `key_image(rgb, cfg) -> Keyed` contract; the chroma keyer stays first, a `matte` backend is used when the border ring is not a chroma colour (auto-detected by `calibrate`) and as the final rung of the key-failure ladder. Everything after keying (specks, trim, pack scale, outline, validators, loop close) is shared code.

Chroma key is the default and only keyer today: it is exact, fast, model-free and does not flicker across video frames. A matting keyer (rembg/BiRefNet) for non-green input is planned behind the same function signature (Phase 3C).
