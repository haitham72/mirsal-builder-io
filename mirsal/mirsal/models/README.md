# AI cutout models (optional, offline)

`mirsal/matte.py` runs a U2-Net / IS-Net model through **onnxruntime only** (no rembg, torch or network). Photos that are not a
green/blue screen use it for the cutout, and so does video background removal. Without a model the app falls back to OpenCV GrabCut.

| file | size | use | md5 |
| --- | --- | --- | --- |
| `u2netp.onnx` | 4.6 MB | fast; used for video frames; kept in git as the fallback | 8e83ca70e441ab06c318d82300c84806 |
| `isnet-general-use.onnx` | 178 MB | best quality; used for photos when present; NOT in git | fc16ebd8b0c10d971d3513d564d01e29 |

Both are Apache-2.0 (U2-Net: xuebinqin/U-2-Net, IS-Net: xuebinqin/DIS), as packaged by danielgatis/rembg releases
(`https://github.com/danielgatis/rembg/releases/download/v0.0.0/<name>.onnx`). Other rembg models (`u2net`, `u2net_human_seg`, `silueta`)
also work; `MIRSAL_MATTE_MODEL=<path>` forces one file. The only Python dependency is `pip install onnxruntime`.
Offline: `pip download onnxruntime -d wheels` on a connected PC (same Windows Python version), then `pip install --no-index --find-links wheels onnxruntime`.
