# Restricted network / library policy

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

The dev PC has limited internet. So every phase follows these rules:
- **Stdlib first.** The console is `http.server` + one HTML file: no CDN, no fonts, no npm. Tests use `unittest`.
- **Minimal wheels:** `numpy`, `opencv-python-headless`, `pillow`; `imageio-ffmpeg` is only a fallback when no system `ffmpeg` is on PATH.
- **Offline install:** on a connected machine run `pip download -r requirements.txt -d wheels` (same OS + Python version), copy `wheels/` over, then `pip install --no-index --find-links wheels -r requirements.txt`. ffmpeg needs the **libvpx-vp9** encoder (a "full" build).
- **`python -m mirsal doctor` is the single health check.** It checks the engine, Postgres and its write-through counters, Redis, the language and vision models, tracing, Higgsfield, Telegram and the model weights. Images and any ML weights (e.g. a matting model) are fetched once on a connected machine and loaded from disk (`docker save/load`, weight files by path).
- A new dependency needs a reason in `README.md`'s tables or here, a line in `requirements.txt` and a check in `doctor`.
