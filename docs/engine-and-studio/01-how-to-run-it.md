# How to run it

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

Always from the folder that holds `requirements.txt` (`Mirsal-Builder\mirsal`), not from the inner `mirsal\mirsal`.

```
cd Mirsal-Builder\mirsal
python -m venv .venv                       # once. Always use this venv: the Anaconda base env on the dev PC has a broken numpy
                                           # (1.26 and 2.0 files mixed) that crashes onnxruntime; the venv is clean
.venv\Scripts\Activate.ps1                 # Windows PowerShell (cmd: .venv\Scripts\activate.bat; macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt            # once (offline machine: see "library policy" below)
python -m mirsal doctor                    # health check: must say numpy/opencv/pillow OK and "libvpx-vp9 ready"
python -m mirsal serve                     # then open http://127.0.0.1:8770
```

Stop with **Ctrl+C**; to restart, run `python -m mirsal serve` again and hard-refresh the page (Ctrl+F5). Another port: `python -m mirsal serve --port 8771`.

What you get in the browser (left rail): **Generate** (type a request, see the stickers, Animate, Add), **History** (your `Images_gen` / `videos_gen` folders, with Remove; **removed from the rail on 2026-10-01 at Haitham's request**, the Studio's Earlier batches replaced it, the screen's code is still reachable at `#/history`), **Library** (search, recent, packs; Send to Telegram), **Chat** (a local echo), **Create** (photo or text sticker, then the editor) and **Settings** (paths, ffmpeg health, Telegram). Typical path: Generate -> Animate -> Add -> Library -> open the pack -> Send to Telegram; or Create -> drop a photo -> edit -> Save.

Your prepared sheets and videos are read from `inputs\Images_gen` and `inputs\videos_gen`; everything the app writes goes to `mirsal\out\` (`G00N\` per generation, `library\` for packs). If `doctor` says `libvpx-vp9 MISSING`, the page still works but final WEBM/animation exports fail: `pip install imageio-ffmpeg` (or a full ffmpeg build, then set `MIRSAL_FFMPEG` to its path).
