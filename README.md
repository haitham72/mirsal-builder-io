# Mirsal Stickers

High-quality animated stickers (not emoji). One deterministic engine; interfaces on top.
**This README is the architecture of what is built.** The `phase_0N.md` files are only the hand-off: what is still to do. When a step is done it moves here and disappears from its plan, until the plans are gone.

**Built so far: Phase 1**, which is one phase: the sticker engine, the prompter stub, the lifecycle console and the desktop Sticker Builder on top of them. Everything below describes it.

## How to run it

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

What you get in the browser (left rail): **Generate** (pick a prepared sheet, watch it key, slice and animate; add stickers to a pack), **Library** (search, recent, packs), **Create** (photo or text sticker, then the editor), and **Settings** (paths and ffmpeg health). Typical path: Generate -> `Add all to pack` -> Library -> open the pack -> drag to reorder -> Export `.wastickers`; or Create -> drop a photo -> edit -> Save.

Your prepared sheets and videos are read from `Phase_01\Images_gen` and `Phase_01\videos_gen` (never modified); everything the app writes goes to `mirsal\out\` (`G00N\` per generation, `library\` for packs). If `doctor` says `libvpx-vp9 MISSING`, the page still works but final WEBM/animation exports fail: `pip install imageio-ffmpeg` (or a full ffmpeg build, then set `MIRSAL_FFMPEG` to its path).

## Other commands (Windows / macOS / Linux)

```
python -m mirsal create "create teddy yellow bear for school"    # same pipeline from the CLI
python -m mirsal more | animate [G001] [--slice N]
python -m unittest discover -s tests -t . -v          # stdlib unittest: no pytest needed
```

Python >= 3.10. Everything uses `pathlib`; paths come from `mirsal/paths.py` (`MIRSAL_INPUT`, `MIRSAL_OUT` override; `MIRSAL_FFMPEG` overrides ffmpeg).

## Restricted network / library policy (applies to every phase)

The dev PC has limited internet. So every phase follows these rules:
- **Stdlib first.** The console is `http.server` + one HTML file: no CDN, no fonts, no npm. Tests use `unittest`.
- **Minimal wheels:** `numpy`, `opencv-python-headless`, `pillow`; `imageio-ffmpeg` is only a fallback when no system `ffmpeg` is on PATH.
- **Offline install:** on a connected machine run `pip download -r requirements.txt -d wheels` (same OS + Python version), copy `wheels/` over, then `pip install --no-index --find-links wheels -r requirements.txt`. ffmpeg needs the **libvpx-vp9** encoder (a "full" build).
- **`python -m mirsal doctor` is the single health check.** Each phase adds its own checks (Postgres, Redis, API keys, model weights). Phase 2+ images and any ML weights (e.g. a matting model) are fetched once on a connected machine and loaded from disk (`docker save/load`, weight files by path).
- A new dependency needs a reason in its phase plan and a line in `requirements.txt` + `doctor`.

## Layout

```
Phase_01/                                                   # Haitham's hand-edited watch folders (the app only READS; never renames)
  Images_gen/img-NNN-<subject>/<sheet>.jpg                  # one folder per variant; NNN = variant folder number
  videos_gen/vid-NNN-<subject>/<video>.mp4                  # the 3x3 video of the same NNN
  videos_gen/vid-NNN-<subject>/slices/{quicktime,webm}/<any name> (n).<ext>   # pre-sliced transparent clips, n = grid cell 1..9
  tracker/tracker.py                                        # optional generation tracker (filenames only)
mirsal/                                                     # the project (own .gitignore entries: out/, .venv/)
  mirsal/
    prompter.py     # stub of the AI prompter: task text -> 9 modular prompts (plain JSON)
    sources.py      # PhaseDirSource: scans the folders above by naming convention; never opens media
    pipeline.py     # the 7-stage lifecycle, events, result.json; used by CLI and console
    engine/         # PURE: numpy/OpenCV/Pillow/ffmpeg only (config, chroma, grid, render, sheet, video, ffmpeg)
    console/        # server.py (stdlib) + index.html shell + studio.css + app.js / packs.js / editor.js (vanilla JS, no CDN)
    library.py      # packs, saved stickers, photo cutout, .wastickers export (desktop builder)
    matte.py        # optional AI cutout: U2-Net / IS-Net through onnxruntime only (models in mirsal/models/)
    video_project.py# video / GIF StickerProjects: import, autosave, render (trim, key, layers with timing, WebM/WebP/GIF)
    cli.py  paths.py
  tests/            # synthetic fixtures (tests/synth.py), engine + console tests
  out/G001/...      # results (gitignored)
  out/library/      # library.json + files/<img|vid>-NNN-<pack>-<sticker>.<ext> (gitignored)
  out/library/projects/<id>/   # project.json + source.<ext> + frames/ per video / GIF project (gitignored)
```

`mirsal/engine/models.py` (a Pydantic contract from an earlier draft) is **not used**: Phase 1 is plain dicts/dataclasses/JSON. Phase 2+ decides whether to revive it.

## Input pairing

A subject's variants are its `img-NNN-<subject>` folders in number order (`img-001..004-teddy_bear` = variants 1-4). The image in `img-NNN` is paired with `vid-NNN` **by the same folder number** (`pairing: folder`); several takes inside one folder pair by the same `(K)` number, and only as a last resort by position (`pairing: order`, flagged by `doctor`). **Names in the watch folders are final: nothing renames them.** The prompt is matched to a subject by whole words of the folder name (`teddy_bear` <- "teddy yellow bear for school"). In Phase 3 the API ticket replaces filename matching.

**Copied clip sets are ignored.** If a variant's pre-sliced clips have the same per-cell file sizes as an earlier variant's (a stat call; media is never read), they are copies. They would animate the wrong stickers, so they are dropped: `clips_dup_of: "001"` is recorded on the pick and in `result.json`, `doctor` warns, and that variant uses its own 3x3 mp4. Found on the real inputs: vid-002/003/004's clips were byte copies of vid-001's.

**Pre-sliced clips.** When `vid-NNN/slices/` holds clips whose name ends in `(n)` (n = grid cell 1-9, any prefix, `.mov` and/or `.webm`), the app uses them instead of slicing the 3x3 MP4. `mov` (ProRes 4444) is preferred (`clip_prefer`); see "Clip formats".

## Naming convention (outputs)

`<media>-<NNN>-<task_slug>-<key>` where `media` is `img` or `vid`, `NNN` is the generation number, `task_slug` and `key` come from the prompter:
`img-001-teddy_bear_school-teddy_bear_with_a_book.png` and `vid-001-teddy_bear_school-teddy_bear_with_a_book.webm`, side by side in `out/G001/slices/`.

## Prompter contract (`prompts.json`, plain JSON, no LLM in Phase 1)

```json
{ "task": "teddy yellow bear for school", "task_slug": "teddy_bear_school", "subject": "teddy yellow bear",
  "context": "school", "kind": "school", "guidelines": {"sheet": "...", "style": "...", "background": "...", "consistency": "...", "motion": "..."},
  "sheet_prompt": "...", "video_prompt": "...",
  "stickers": [ {"index": 1, "id": "prompt01", "prompt": "teddy yellow bear holding a book", "key": "teddy_bear_with_a_book", "emoji": "📚"} ] }
```

**The stub does not look at the image.** Labels are assigned by cell position from `ACTIONS`; they only match a sheet if that sheet was generated from this plan's `sheet_prompt` (shown, copyable, in the console). For a sheet made any other way, put the real 9 prompts in `<sheet name>.json` (e.g. `img-001-teddy_bear (2).json`) or `<folder>/prompts.json` (same shape, `task_slug` + 9 x `{index, prompt, key, emoji}`); it replaces the stub, is validated, and the console shows `labels from: <file>`. The app only reads these files.

Nine stickers, row-major cell order. `key` is the searchable action name and the file-name tail. Colour words are dropped from slugs, kept in prompts. Action sets live in `ACTIONS` (school, birthday, default); a real planner (Phase 3) must return the same shape.

## Lifecycle (`pipeline.py`, one line per transition in `out/G00N/events.jsonl`)

| Stage | What runs | Kind |
|---|---|---|
| `requested` | prompt -> `prompter.expand` -> allocate `G00N`, write `prompts.json` + initial `result.json` | real |
| `sheet_picked` | `sources.find` picks set + variant; sheet copied to `source/sheet.*` | lookup |
| `keyed` | sample real background, auto-threshold, key every cell; `source/keyed.png` | real |
| `sliced` | speck removal, despill, one pack-wide scale, outline, validate -> `slices/img-*.png` | real |
| `video_requested` | scope `slice` (one cell) or `pack` | user |
| `video_picked` | per cell: the pre-sliced clip if present (mov preferred), else the variant's 3x3 MP4 (probed with `ffmpeg -i`, no ffprobe) | lookup |
| `video_sliced` | clips: haze floor + despill; mp4: same keyer as stills. Then per-clip normalise, loop close, VP9+alpha encode -> `slices/vid-*.webm` | real |

Event: `{ts, stage, status: start|done|error, ms, detail}`; `video_cell` sub-events report each finished cell. `--pace S` on `serve` inserts a fixed sleep between stages for live demos; it never changes outputs.

`result.json` is the record Phase 2 persists: generation id/number/`parent`, prompt, task, source (subject, variant, files, video info), stage, error, and per sticker `index, key, name, emoji, prompt, status, reason, report[], metrics{}, png, webm, anim_status, anim_reason, anim_metrics{}`. Statuses: `READY | FAILED` (stills), `NOT_REQUESTED | PROCESSING | READY | FAILED` (video). A failed cell never blocks the other eight; a video failure never fails the still.

## Engine

Stills (`engine/sheet.py`, pure): cut the sheet with `engine/grid.py` (below) -> per cell: sample background from the 4 px border ring (median), colour-difference key `d = K - max(other two)` with `t = 0.5 x median(d on ring)` (alpha linear between `t/2` and `t`) -> drop specks < 64 px (no erosion) -> despill the edge band only -> trim to bbox -> **one pack-wide scale** (median fit, clamped so nothing exceeds 0.85 x 512) -> premultiplied linear resize -> centre on 512x512 -> white outline (12 px) -> validate. Checks: `dimensions, transparent_corners, foreground, inside_cell, no_spill, static_file` (PNG, else lossless WEBP if > 512 KB). `no_spill` counts key-coloured opaque pixels **on the edge band only** (outline + despill band + 3 px from transparency). Key-coloured pixels deeper inside are the subject's own colours: they go to `metrics.chroma_risk` (share of the subject), with `warnings: ["chroma_risk"]` above 3%. That is a warning for the human, never a block. Measured on the 10 real sheets: every pixel the old whole-subject rule failed on was interior, with 0 on the edge. Blank cell -> `empty_subject`; subject touching the cell edge -> `inside_cell`.

**Key-failure branch (`sheet.py`, stills).** A failed cell is never just dropped: (1) **dissect** - log why (border ring pollution, threshold, foreground and edge pixels); (2) **key again** on a bounded ladder chosen by the failure reason (`empty_subject`: sheet-wide background, then threshold x0.6; `no_spill`: threshold x0.75 + 6 px despill, then x0.6 + 10 px; other: sheet-wide background); `inside_cell` is ruled out at once because keying cannot fix a subject crossing its cell border; (3) **rule out** - `FAILED` with `metrics.ruled_out` and the full `metrics.attempts` log, which the console shows under "keying recovery". A future last rung is a matting re-key (see "Keyers"). Healthy cells are never retried.

**Grid (`engine/grid.py`).** Grids are 3x3 (default), 2x2, or 1x1 (one regenerated sticker).
- `detect_grid` counts the interior gutter bands: columns or rows that are at least 97% background and at least 1% of the side wide.
- `split_grid` cuts in the middle of the background band nearest each expected line. Where there is no clear band, that one cut falls back to equal division; `method` is `gutter | equal | mixed | single`.
- The rects are stored in `result.json` (`source.grid`), drawn as cut lines on the console's raw sheet, and reused for the 3x3 mp4: `scale_rects` maps them onto the video, since image-to-video keeps the layout. The live canvas preview uses the same rects.
- Real AI sheets put gutters up to ~90 px off the thirds. Cutting at thirds sliced 12 of 90 real cells (`inside_cell`); cutting at the gutters slices none.
- The prompter's `expand(task, grid)` returns one sticker per cell, and `validate_plan` infers the grid from the sticker count (9, 4, 1).

Video (`engine/video.py`): decode one cell at a time via `ffmpeg crop` (measured rects, else thirds); native fps (<= 30, never upsampled), <= 3 s; background sampled **once** from the first frame; **one transform per clip** (union bbox); loop close: if the last->first `loop_seam` exceeds `max(12, 1.5 x the clip's own median frame-to-frame change)`, the last 6 frames are cross-faded into the first ones; encode `libvpx-vp9 yuva420p` with CRF ladder 30/38/46/54/60 until <= 256 KB. If the ffmpeg in use has no libvpx-vp9 (Anaconda's has none, and it also rejects `-deadline`), every requested cell fails at once with `no_vp9_encoder` and the fix in `metrics.error`, instead of a bare `exception` per cell (which is what happened to every earlier real run). Checks: `size_budget, codec_vp9, dimensions, fps, duration, no_audio, alpha_mode_tag, alpha_decoded` (decoded with `-c:v libvpx-vp9`, since the default decoder hides alpha), `loop_seam`.

**Pre-sliced clips** skip the keying step: alpha haze below `clip_alpha_floor` (12) is zeroed (VP9 alpha leaves values 1-3 around the subject), specks are dropped, the edge band is despilled, then the same transform / loop close / encode / validation as above. `edge_touch_frames` is reported (warning only): it counts frames whose subject touches the slice border, meaning the slice may clip the character.

## Clip formats (measured on the teddy clips; metadata + alpha statistics only)

| | `.mov` | `.webm` |
|---|---|---|
| Codec | ProRes 4444, `yuva444p12le` (real, high-precision alpha) | VP9 `yuv420p` + alpha side channel (`alpha_mode` tag) |
| Size / fps / length | 320x320, 24 fps, 4.04 s, ~10-16 MB | 320x320, 24 fps, 4.00 s, ~350 KB |
| Alpha | clean: median 255, soft edge only | **faint haze**: ~28k stray pixels/frame at values 1-3 (needs the floor above) |
| Edge contact | 51 of 97 frames have opaque pixels on the outer 2 px | none |
| Browser preview | Safari only | Chrome/Firefox |
Verdict: use `.mov` as the master (best alpha), `.webm` is acceptable after haze removal, and both need 320 -> 512 upscaling and trimming to <= 3 s. Neither is the final format: final output is the app's 512x512 VP9 WEBM (Telegram); animated WEBP (WhatsApp) is a later encoder behind the same validation.

## Keyers: ready-made options (for photos / non-green input; Phase 3C and 5)

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

## Console API (seed of the Phase 5 API)

**Generate rotates through the prepared variants** of the matched subject (001 -> 002 -> 003 -> 004 -> 001 ...), each press a new generation; the image of `img-NNN` always goes with `vid-NNN`. The sidebar's "Prepared inputs" panel lists every variant (sheet, video, clip count, pairing, label source) with a **Use** button to pick one explicitly (`POST /api/generations {prompt, variant}`); **More** still walks to the next variant and stops at the last.

The console UI: click any slice (or its name) to open a modal carousel (arrows / keys / thumbnails) with the raw cell + bounding box, the sticker, the video, all checks, metrics and the keying recovery log.

**Video click = instant live preview.** "▶ Animate this" / "▶ Animate all 9" plays the paired 3x3 mp4 in the browser at once: each cell is drawn to a canvas, keyed with the same colour-difference formula (threshold calibrated from the cell's border ring) and framed like its sticker (bbox centre + pack scale from the still's metrics). It is a preview only (no outline, no loop closing). In parallel the server encodes the real 512x512 WEBM; once a slice is READY the tile swaps to it. The preview needs no ffmpeg; the encode does, and a banner shows when ffmpeg has no VP9. Source video is served read-only at `GET /src/<id>/video` (Range supported, only the file recorded in `result.json`); webm clips at `/src/<id>/clip/<n>` are the fallback when no mp4 exists. UI lesson: an inline `onclick="animate(...)"` resolves to `Element.animate`, so handlers are named `playVideo`; a test guards it.

`GET /` · `GET /out/<path>` · `GET /src/<id>/video` · `GET /src/<id>/clip/<n>` (traversal -> 400) · `GET /api/generations` · `GET /api/generations/<id>` (result + events) · `POST /api/generations {prompt}` · `POST /api/generations/<id>/more` · `POST /api/generations/<id>/animate {scope: "pack"|"slice", index?}`. One background job at a time (`409 busy`); the UI polls every 500 ms.

## Desktop Sticker Builder

One page, eight screens (Chat is a local echo contact: send a sticker or text, it comes back and your message gets a like; messages stay in the browser until Phase 5 adds a real chat backend; from a pack or the Library carousel use **Send to chat**), one stdlib server; routes are hash-based (`#/library`, `#/generate`, `#/create`, `#/editor`, `#/pack/<id>`, `#/animate/<pack>/<sticker>`, `#/export`, `#/chat`, `#/settings`). Look and layout follow `ref/Mirsal-Builder.jpg` (Mirsal blue `#3B82F6`, tokens in one `:root` set at the top of `studio.css`, light surfaces, left rail) and `ref/mirsal_sticker_builder_architecture_design.md`. Look: Inter (bundled `console/fonts/InterVariable.woff2`, SIL OFL, so no CDN), a left rail, and a second column that takes the chat-list position of the mockup and lists the packs (real rows, no fake chats). Editor and animation screens are three white cards (tools/layers, canvas, properties) as in the mockup, plus a History strip (one thumbnail per undo state; click to jump) where the mockup has its bottom strip. Files: `studio.css`, `animate.js` (animated editor), `app.js` (shell, dialogs, Library, Settings, and the Phase 1 Generate/lifecycle console with its carousel and live video preview), `packs.js` (pack manager), `editor.js` (Create, Editor, Export). No inline `onclick` for new code: buttons carry `data-act` and one delegated listener dispatches to `ACT[...]` (inline handlers resolve names on the element first, which once broke `animate`).

**Library backend (`library.py`).** Plain files under `out/library/`: `library.json` (packs -> stickers, atomic write, one lock) and `files/`. Saved names follow the repo convention `<img|vid>-<NNN>-<pack_slug>-<sticker_slug>.<ext>`, NNN counting inside the pack. Adding a generated sticker copies the READY PNG (or WEBM) from `out/G00N/slices/`; saving from the editor posts the 512x512 canvas PNG, which goes through the same validators as engine stickers (dimensions, foreground, size, PNG else lossless WebP). Every pack operation is an API call (`POST /api/packs`, `/api/packs/<id>` for name/cover/order, `.../stickers`, `.../render`, `.../delete`, `GET /api/library`, `GET /api/packs/<id>/export`, `POST /api/cutout`, `GET /lib/<file>`, `GET /ui/<file>` from a whitelist).

**Cutout (`library.cutout`).** Already-transparent input is kept; a border ring whose green/blue excess is at least 40 uses the engine's chroma key (same `key_image` as the sheets); anything else uses OpenCV GrabCut seeded with an inset rectangle (offline, no weights), then speck removal and a tight crop. It reports `method`, `foreground` fraction and a warning when nearly everything was kept. Learned matting (README "Keyers") replaces GrabCut in Phase 3C behind this same function.

**Editor model.** Layers `subject | text | emoji`, each with x, y, scale, rotation, visibility and lock; one shared border config; adjustments per subject. The visible canvas, the selection overlay and the exported PNG all come from one `compose()` (layers -> silhouette -> 32-direction dilation outline -> optional shadow -> layers). Undo/redo stores JSON snapshots plus a versioned canvas per erase/restore stroke. One route, contextual inspector per tool (spec section 7).

**Animated editor (DESKTOP_04).** Opened from an animated sticker in a pack. The sticker's WEBM plays in the browser (Chrome decodes VP9 alpha); a thumbnail timeline has draggable trim handles, playhead and frame step; properties set loop, frame rate and format. The server does the real work in `library.anim_export`: decode the WEBM (libvpx-vp9 decoder), pick frames for the trimmed range resampled to the chosen fps, then encode **WebM** (VP9+alpha, the engine's CRF ladder to <=256 KB), **WebP** (`libwebp_anim`, quality ladder to <=500 KB, WhatsApp) or **GIF** (palette with 1-bit alpha, no size cap). `POST /api/packs/<id>/stickers/<sid>/animate {start,end,fps,format,loop,save,name}` returns the file (header `X-Animate` has frames/kb/crf) or, with `save` (WebM only), stores a new animated sticker in the pack. Needs an ffmpeg with libvpx-vp9 (see doctor); WebP needs libwebp.\n\n**Export.** `.wastickers` = `title.txt`, `author.txt`, `tray.png` (96x96, <=50 KB) and 512x512 WebP stickers <=100 KB (quality search 90 -> 30, WebP method 4: method 6 with `exact=True` took ~4 s per sticker); animated stickers are converted to animated WebP <=500 KB at 15 fps (skipped and listed if conversion fails). Needs 3-30 stickers. The limits are constants in `library.py`, not in the UI.

**Verified.** 25 unit tests (`tests/test_library.py`: cutout methods, pack CRUD/reorder/cover, export limits, bad renders; `AnimateTests`: trim to WebP/GIF/WebM and save-back, animated stickers inside `.wastickers`; `tests/test_console.py`: library routes, path traversal, UI file whitelist, the `animate` regression guard). Headless Chromium on synthetic inputs: photo -> GrabCut cutout -> text + emoji -> erase (alpha pixels 25937 -> 25144, undo restores 25937) -> border -> save to a new pack -> Generate -> add all 9 -> drag reorder -> set cover -> `.wastickers` download (zip with tray + WebPs), no console errors. Not yet exercised on real photos or by Haitham.

## Video / GIF projects (checkpoint 1E, spec section 21)

**Flow.** Create -> drop a video or GIF -> the **Prepare** screen (`#/prepare/<id>`): tools + layers on the left, a 512 canvas in the centre, contextual properties on the right, the trim timeline underneath. Trim, frame rate, fit/fill, optional GIF conversion, optional background removal, text / emoji / sticker layers with their own visible-from/to range, then Download (WebM / WebP / GIF) or Save to pack (WebM). Any animated sticker in a pack can be opened the same way from the animated editor ("Add text / effects...").

**One shared model.** `video_project.Projects` keeps a `StickerProject` per import in `out/library/projects/<id>/project.json` (type `animated`, `source`, `canvas.fit`, `video{trimStartMs,trimEndMs,currentTimeMs,fps}`, `gif{enabled,loop,quality}`, `videoBackgroundRemoval{enabled,status,provider}`, `layers[]` with `transform`, `opacity`, `timing{startMs,endMs}`, `payload`). The upload is stored untouched as `source.<ext>`; a failed render or removal never changes it. The page autosaves (500 ms debounce, server clamps every value); heavy data (frames, masks, baked layer PNGs) never enters the project or the undo history (a JSON snapshot stack of the small state).

**Preview = server frames.** Import decodes preview frames once with ffmpeg (fit in 360 px, JPEG, PNG when the container can carry alpha, up to 240 frames, rotation applied), so any container ffmpeg reads works and GIFs need no special case. The canvas plays those frames, draws the layers, and shows the green/blue key live; the AI matte preview loads one masked frame at a time (`/proj/<id>/mask/<n>.png`, cached).

**Render (`Projects.render`).** Decode the trimmed range at the chosen fps straight to 512 (fit keeps the frame and pads transparent, fill crops), optionally remove the background, composite each layer PNG (baked by the page at 512x512 with its transform and opacity, so Arabic/RTL shaping and fonts are the browser's) on exactly the frames inside its timing range, then encode with the shared size ladders: WebM VP9+alpha <= 256KB, WebP <= 500KB (WhatsApp), GIF (palette 32-256, 1-bit alpha). Stickers are clipped to 3 s, GIF to 10 s; the response header `X-Render` reports frames, fps, kb and whether it was clipped.

**Background removal = a capability behind providers.** `videoBackgroundRemoval.status` is `UNAVAILABLE | READY | PROCESSING | READY_WITH_MASK | ERROR`. Providers, first match wins: **chroma** (border ring of the first frame is a green/blue screen; the engine's `key_image`, calibrated once per clip) then **matte** (`matte.py`, per frame with light temporal smoothing) else UNAVAILABLE with the reason shown in the panel. An error keeps the project and offers Try again / Continue without removal.

**AI cutout (`matte.py`, optional).** U2-Net / IS-Net (Apache-2.0) run through **onnxruntime only**: no rembg, torch or network. `library.cutout` order: existing alpha, green/blue key, AI matte, GrabCut; the Create screen has an Auto / AI matte / GrabCut selector. Models live in `mirsal/models/` (`isnet-general-use.onnx` 178 MB for photos, `u2netp.onnx` 4.6 MB for video frames and as the in-git fallback; see `mirsal/models/README.md` for sources, md5 and the offline install). `python -m mirsal doctor` reports which is active; without onnxruntime or a model the app falls back to GrabCut and says so.

**Routes.** `GET /api/projects`, `GET /api/projects/<id>`, `POST /api/projects?name=` (raw video/GIF body, 300 MB max), `POST /api/projects/from_sticker {pack_id,sticker_id}`, `POST /api/projects/<id>` (autosave), `POST /api/projects/<id>/delete`, `POST /api/projects/<id>/render {format, overlays{layerId: PNG data URL}, save?{pack_id,name,emoji}}`, `GET /proj/<id>/f/<n>`, `GET /proj/<id>/mask/<n>.png`. `POST /api/cutout?method=auto|matte|grabcut`.

**Not in yet.** Draw layer, crop, per-frame editing, keyframed layer motion (layers have one position over their visible range), border/outline on the keyed subject, the mobile layout (the spec's scrollable-controls rule is Phase 5C), a stronger video matte (BiRefNet / SAM 2 video, Phase 3C).

## Verified

- 17 unit tests pass (stills, recovery ladder, pre-sliced clip path, folder/clip discovery, plan files, console lifecycle); the console UI was driven headlessly in Chromium (carousel, keyboard, thumbnails, no JS errors). Earlier list: statuses, detached detail survives, pack-consistent scale, golden determinism, blue-chroma with green subject, WEBP fallback, engine import boundary (no fastapi/psycopg/langgraph/anthropic/pydantic), synthetic video + loop close, console lifecycle end to end.
- Real `teddy_bear` sheets (2048x2048 JPG): a first sheet gave 8/9 READY with `no_spill` on one slice; the current `img-001` sheet gives 9/9 READY in ~1 s. Haitham judges the look.
- Real pre-sliced clip: `teddy_ (1).mov` -> READY 512x512 WEBM, 242 KB, ~17 s (encode dominates).
- Real teddy video is 960x960, 24 fps, 4.04 s (cells are 320 px, upscaled to 512).
- **Pass of 2026-10-01** (project venv, imageio-ffmpeg 7.1 with libvpx-vp9):
  - all 10 prepared sheets come out **90/90 READY** (6 generic_emojis + 4 teddy); one generic cell carries a `chroma_risk` warning at 46%;
  - all 4 teddy packs animate **36/36 READY** at 149-254 KB, ~5 s per sticker (~50 s per pack, down from ~18 s per sticker); teddy 001 from its `.mov` clips, 002-004 from their own mp4s. The generic_emojis have no videos;
  - on the mp4 path, characters touch their slice edge in up to 72 of 96 frames (teddy 004): the video model moves them across the cut line. The 1F `inside_slot` gate is built for exactly this.
- 41 unit tests pass, including grid (off-third gutters, 2x2, 1x1, mp4 with measured rects), prompter grids, copied-clip detection, and edge-band spill vs interior colour.
