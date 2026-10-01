# Mirsal Stickers

High-quality animated stickers (not emoji). One deterministic engine; interfaces on top.
**This README is the architecture of what is built.** The `phase_0N.md` files are only the hand-off: what is still to do. When a step is done it moves here and disappears from its plan, until the plans are gone.

**Built so far: Phase 1**, which is one phase: the sticker engine, the prompter, the verifier, the golden path with its review gates (1F), the lifecycle console, the desktop Sticker Builder and the React gateway frontend (1G). Everything below describes it. Parts that wait for Haitham's hand-run on real material are said so under "Verified".

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

What you get in the browser (left rail): **Generate** (type a request, see the stickers, Animate, Add), **History** (your `Images_gen` / `videos_gen` folders, with Remove), **Library** (search, recent, packs; Send to Telegram), **Chat** (a local echo), **Create** (photo or text sticker, then the editor) and **Settings** (paths, ffmpeg health, Telegram). Typical path: Generate -> Animate -> Add -> Library -> open the pack -> Export `.wastickers` or Send to Telegram; or Create -> drop a photo -> edit -> Save.

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
    prompter.py     # the planner stub: task text -> slot JSON -> prompts rebuilt from prompts/templates/*.txt (tags + margin clause)
    prompts/templates/  # sheet_3x3_v1.txt  sheet_2x2_v1.txt  single_1x1_v1.txt  video_v1.txt  (saved, versioned master prompts)
    sources.py      # PhaseDirSource: scans the folders above by naming convention; never opens media
    pipeline.py     # the lifecycle, events, result.json (+ reviews, history, video_sheets); used by CLI and console
    gates.py        # the golden path's review gates G1-G5, the video sheet build, the returned-video slicing, 1x1 regen, search
    tasks.py        # the Inbox backend: plan preview, task reserve (out/tasks/NNN.json), watch-folder states, run linked to a task
    engine/         # PURE: numpy/OpenCV/Pillow/ffmpeg only (config, chroma, grid, render, sheet, video, ffmpeg, verify, video_sheet)
    watch.py        # History: the watch folders, image + video side by side, Remove -> trash -> Restore
    telegram.py     # Send to Telegram: Bot API client, plan, send, re-send, the @stickers zip (stdlib only)
    console/        # server.py (stdlib) + the desktop builder: index.html, studio.css, app.js (shell, Library, Settings), generate.js, history.js, telegram.js, packs.js, editor.js, chat.js ...
  web/              # PARKED: the React gateway of the first 1G pass. Not served, not maintained; kept in git history for reference
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

**One press is one folder.** A request without an explicit folder takes the first prepared sheet of the matched subject and never advances by itself (it used to rotate 001 -> 002 -> 003 -> 001 on every press, which made a pre-generated test set unusable). `POST /api/generations {prompt, variant?, outline?}` takes the folder with `variant`; History (below) and the sheet chips on the result pick a specific folder.

The console UI: click any slice (or its name) to open a modal carousel (arrows / keys / thumbnails) with the raw cell + bounding box, the sticker, the video, all checks, metrics and the keying recovery log.

**Video click = instant live preview.** "▶ Animate this" / "▶ Animate all 9" plays the paired 3x3 mp4 in the browser at once: each cell is drawn to a canvas, keyed with the same colour-difference formula (threshold calibrated from the cell's border ring) and framed like its sticker (bbox centre + pack scale from the still's metrics). It is a preview only (no outline, no loop closing). In parallel the server encodes the real 512x512 WEBM; once a slice is READY the tile swaps to it. The preview needs no ffmpeg; the encode does, and a banner shows when ffmpeg has no VP9. Source video is served read-only at `GET /src/<id>/video` (Range supported, only the file recorded in `result.json`); webm clips at `/src/<id>/clip/<n>` are the fallback when no mp4 exists. UI lesson: an inline `onclick="animate(...)"` resolves to `Element.animate`, so handlers are named `playVideo`; a test guards it.

`GET /` · `GET /out/<path>` · `GET /src/<id>/video` · `GET /src/<id>/clip/<n>` (traversal -> 400) · `GET /api/generations` · `GET /api/generations/<id>` (result + events) · `POST /api/generations {prompt}` · `POST /api/generations/<id>/more` · `POST /api/generations/<id>/animate {scope: "pack"|"slice", index?}`. One background job at a time (`409 busy`); the UI polls every 500 ms. **Added by 1F/1G:** `GET /legacy` (the vanilla console) · `GET /assets/*`, `/fonts/*` (the built React app) · `POST /api/plan {prompt, grid, style_id}` · `GET|POST /api/tasks`, `GET /api/tasks/<NNN>` · `GET /api/inbox` · `POST /api/generations {task}` (run a reserved task) · `POST /api/generations/<id>/review {gate: plan|still|video_sheet|anim|pack, decision: APPROVE|REJECT, index?: n|"ready"|"A1", note?}` · `POST /api/generations/<id>/video_sheet` (build `A<n>`) · `POST /api/generations/<id>/video_sheet/<A>/video?name=` (raw body: attach the returned video, then slice) · `POST /api/generations/<id>/regen {index, subject?}` · `POST /api/generations/<id>/pack_add {pack_id}` (the final pack into a Library pack) · `GET /api/search?q=`. Reviews are refused with `409` while a job runs.

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

## The verifier (`engine/verify.py`, checkpoint 1F)

One catalogue holds every check of the golden path. A check is one function `fn(inp, cfg) -> Check` with the fixed shape `{id, stage, severity BLOCK|WARN, ok, value, limit, detail{}, note, reason}`; `verify.run(stage, inp, cfg)` runs the stage in catalogue order and never raises (a crashing check is a BLOCK `verifier_error`). Thresholds live in `EngineConfig` only. `Report` is a view over `list[Check]`: the first failing BLOCK is the sticker's `reason`, failing WARNs go to `metrics.warnings`. `result.json` keeps the old `{name, ok, detail}` row and adds `severity, stage, value, limit, data`. `VERIFY_VERSION = 1` is stored on every result. Pure (numpy/OpenCV): ffmpeg work stays in `video.py` and hands arrays in. `python -m mirsal doctor` prints the check count and the template files.

| Stage | Checks (BLOCK unless WARN) |
|---|---|
| `sheet` (on arrival) | `sheet_decodes` (gate: nothing else runs without it), `sheet_size` (>= 1024 px), `background_is_key` (ring key difference >= 60), `grid_detected` (equals the plan's grid), WARN `cut_clean` (gutter cuts), WARN `background_flat` (std-dev <= 12) |
| `still` (per cell) | `blank_cell` (reason `empty_subject`, gate), `dimensions`, `transparent_corners`, `foreground`, `inside_cell`, `no_spill` (edge band only), WARN `chroma_risk`, `holes` (WARN above 1% of the subject, BLOCK above 30%; measured on the finished sticker so the white outline closes thin-ring gaps), WARN `single_subject` (a second part >= 12%), WARN `duplicate_cell` (dHash distance <= 4 to an earlier cell), `static_file` |
| `video_sheet` (G3 build) | `slots_match_approved` (filled slots = approved S#, blank slots pure key colour), `no_outline_on_sheet` (no white ring round a coloured subject) |
| `video` (returned, before slicing) | `video_decodes` (gate), `video_specs` (>= 1 s), `layout_match` (first frame vs the sheet, per slot IoU >= 0.6: proves the video came from THIS sheet), `blank_slots_stay_empty` (blocks the generation's video, not the stickers) |
| `slot` (per approved slot, before the encode) | `inside_slot` (a block saves the ~5 s encode: first frame and px over the edge band), `cross_slot` (a foreign part in the gutter that never enters the slot's core) |
| `anim` (per encoded WEBM) | `size_budget, codec_vp9, dimensions, fps, duration, no_audio, alpha_mode_tag, alpha_decoded, loop_seam` as built, WARN `identity_kept` (shape IoU of frame 0 vs the approved still >= 0.5), WARN `motion_present`, WARN `alpha_stable` (area CV <= 0.35) |
| `pack` (G5) | `pack_limits` (1-120 stickers, unique keys, an emoji each, files within their limits) |

`subject_px_in_video` is recorded per slot as a metric only (no warning, no gate). `engine/verify.py` was introduced with **no behaviour change**: the 10 real sheets gave identical status, reason, metrics and PNG hashes before and after the move, and with the new checks they are still 90/90 READY (the `holes` metric is new). Thresholds were measured on those sheets (ring difference 135-209, background std 1.2-2.3, largest hole share 0.074 before the outline, smallest cell-pair hash distance 5) and sit well clear of them; the synthetic noisy sheet is the loosest case (std ~8). **Known limits:** a thin ring with a wide gap round a character is a real hole and will BLOCK `holes`; a neighbour crossing into a slot's gutter also trips that slot's `cross_slot` (conservative: both are blocked, and a human can regenerate).

## The golden path (`gates.py`, checkpoint 1F)

request -> **G1 plan** -> sheet -> Python blocks bad cells -> **G2 stills** -> **video sheet** from the approved stills only -> **G3** -> returned video attached to `A<n>` -> Python blocks bad slots -> **G4 animations** -> **G5 pack** (approved at G2 AND G4). The rules live in Python and the page only displays them: an out-of-order or illegal action is a `409` whose message is the reason.

- **Python's block is final.** Nobody can approve or reject a `FAILED`/blocked sticker. Rejection never deletes. A sticker keeps its original `S#` (slot n of every video sheet holds `S<n>`).
- **Order and locks.** G2 needs the plan approved (G1), the stills sliced and no active video sheet; the plan decision is locked once a still is decided; stills decisions are locked while a video sheet is not `REJECTED`; the sheet build needs every READY sticker decided and at least one approved; the upload needs the sheet approved (G3) and is allowed again after `VIDEO_BLOCKED`; G4 needs sliced animations; G5 needs every READY animation decided and passes `pack_limits`; animation decisions lock once the pack is approved. "Approve all READY" only touches stickers still `PENDING`.
- **`result.json` additions.** `tags` (1-5 per sticker, `tags[0]` = key), `review {still, anim}` (`PENDING|APPROVED|REJECTED|BLOCKED`), `history[]` (`{ts, stage, actor python|human|vlm, decision PASS|BLOCK|APPROVE|REJECT, reason, ref, detail}`; stages `sheet, sliced, still, video_sheet, video, anim, pack`; `detail` carries the failing check's `value`, `limit` and data, e.g. `inside_slot` frame and px over), `reviews {plan, video_sheet{A1}, pack}` (each `{decision, by, ts, note}`; pack also `stickers[]`), `video_sheets[] {id, slots, grid, file, layout, video, status BUILT|APPROVED|REJECTED|VIDEO_RETURNED|VIDEO_BLOCKED|SLICED, verify[], blocked, video_checks[], video_flags[], video_info}`, `verify {sheet[]}`, `template_id/version`, `slots`, `task_id`, `name_key`, `regen_of`. Results written before 1F load with empty versions of these (`pipeline.normalise`). `state()` adds the computed `gate` (what to ask next) and `final` (the G2 AND G4 stickers).
- **Events** gain `actor` and `decision` (`review` per decision, plus `plan_reviewed, stills_reviewed, video_sheet_built, video_sheet_reviewed, video_returned, video_flag, anim_reviewed, pack_final`). `STAGES` grew by those names; `check_animate` accepts any stage from `sliced` on.
- **Files** under `out/G00N/`: `source/plain/S#.png` (the sticker rendered with `outline_px=0` from the very keyed cell, recovery included: the video sheet is built from these), `video_sheet/A<n>/{sheet.png, layout.json, video.<ext>}`.
- **Video sheet (`engine/video_sheet.py`, pure, golden-hash tested).** `build_video_sheet(stickers_rgba, approved, cfg, grid) -> (sheet_rgb, layout)`: a 2048 px canvas of the exact key colour (`#00FF00` or blue), the slots tile the canvas, ONE scale for the whole sheet so the largest subject's longest side is <= 55% of its slot (>= 22% margin per side), premultiplied resize, no outline (it is added once, after the video), rejected slots left pure key colour. `layout.json` = `{canvas, key_rgb, grid, slots[{slot, sticker, rect, subject_rect, scale, subject_px}]}`.
- **Layout slicing.** `process_video(..., layout=, refs=)` decodes each approved slot from the layout's exact rectangles (scaled onto the video), keys every frame with the stills keyer, runs `inside_slot`/`cross_slot` before the encode, then the same normalise / loop close / VP9 encode as before plus `identity_kept` against the approved still. `check_returned_video` runs the `video` stage. The prepared-video sandbox path (`animate`, folder pairing, pre-sliced clips) is unchanged and its results get the same `review`/`history` fields; `edge_touch_frames` stays a warning there.
- **1x1 regeneration** (`POST .../regen {index, subject?}`): a new generation from a prepared 1x1 sheet, `regen_of: "G00N/S#"`, `parent`, the sticker's own key/tags/emoji in the `single_1x1` template, the parent's plan approval inherited; the parent is never modified. 2x2 and 1x1 go through every gate like 3x3.
- **Search** (`GET /api/search?q=`): file search over key, tags, name, task, prompt and emoji, newest first; each row carries its still/animation review state and `final`. Phase 2 swaps Postgres in behind the same route.

## Prompter: templates, slots, tags (`prompter.py`)

`expand(task, grid)` fills a slot JSON `{subject_description, style_id, mode, cells[{pos, label, tags, emoji}], action_guidance, key_colour}` deterministically and `render_plan(slots, template_id, version)` rebuilds every prompt from the saved template file (`prompts/templates/<id>_v<N>.txt`; `sheet_3x3`, `sheet_2x2`, `single_1x1`, plus `video` for the video prompt). `prompts.json` stores `{template_id, template_version, slots}`; `validate_plan` rebuilds the sheet and video prompts from them, so stored free text never wins over the template. Every cell has 1-5 tags (`[a-z0-9_]+`, unique, the first one is the key) and its prompt ends with the margin clause *"full body, centred, generous empty margin on every side (at least 20% of the cell), nothing touching or crossing the cell edge"*. A prompts file without `tags` is valid (`tags = [key]`). Phase 3 swaps only the filler (LLM); the templates and `render_plan` stay.

## The simple flow (`console/generate.js`; 1G, redone 2026-10-01)

> **Session model (latest, written but not yet browser-verified: see `phase_01.md`, "Session hand-off").** A request starts a *session*: **Batch 1**; **Create more** adds the next prepared sheet of the same subject on purpose; each batch has an include checkbox, a **Green screen & cuts** viewer (raw / background-removed sheet, measured cut lines, each sticker's boundary box, the sheet analysis) and, when it has no prepared video, **Make a video...**; **Animate** acts on every included batch; **Add to a pack** asks for the pack (a new one with an editable name, or an existing one) and adds the kept stickers of all included batches (1-n). Background is a dropdown, a Size slider scales the tiles, and a step that has to wait for a running job waits quietly (`postWait`) instead of showing "busy". The description below still holds for one batch.

The Generate screen is one panel: **type a request -> the stickers appear -> Animate -> Add**. Nothing else is needed for the common path, and the review gates are still decided and recorded, behind those clicks:

- **Generate** (or a prepared-sheet chip) starts the run and counts as the human's **G1** decision (`reviews.plan.note = "approved by pressing Generate"`; an Inbox task keeps its own approval).
- The grid shows the stickers. The only per-sticker control is the small **x** (drop it from the set / bring it back): `POST /api/generations/<id>/drop {index, dropped}` is a human reject (or approve) at the stage the sticker is in (G2 before animation, G4 after), reopening an approved pack when needed. Blocked stickers (Python's block is final) show the reason and have no x.
- **Animate** (sheets with a prepared video) runs the live in-browser preview at once and encodes the real WEBMs; stickers that were dropped are skipped. **Make a video...** (sheets without one, such as the generic emojis) is the single multi-step path: `POST .../quick_sheet` approves the kept stills, builds the video sheet and approves it for sending; a dialog offers the download, the video prompt and the upload (attached to `A<n>`), and closes when the slots are sliced.
- **Add to pack** (`POST /api/generations/<id>/add {pack_id? | pack_name?}`) is G2 + G4 + G5 in one call: it approves what is still pending, approves the final pack (`pack_limits`), and adds the **animated** stickers when there are any, else the **stills**, to the Library pack (a new one named after the subject when none is chosen; the last pack is remembered, "change" opens the picker). Pressing Add twice adds nothing twice (`result.added`).
- One primary button per state: Generate -> Animate (or Add N to pack when there is no video) -> Add N to pack -> Open pack. The alternative is a quiet link ("or add the stills", "Make a video...").
- **The white outline is a choice**, per generation: On (12 px) or Off, next to the prompt (remembered in the browser). `outline_px` is stored on the result and used for the stills and for the animations; `0` makes the sticker equal to its plain cutout. The video sheet never has an outline (it is added once, after the video).
- When nothing prepared matches a request the page offers **Get the Higgsfield prompt**: `POST /api/plan` (the template and slots, copyable sheet and video prompts) and `POST /api/tasks` (reserves the next `img-NNN-<subject>` / `vid-NNN-<subject>` names and writes `out/tasks/NNN.json`, the Phase 2 `tasks` row: `provider: higgsfield-manual`, `external_task_id` = the reserved folder, `name_key`, `request`, `plan`). `tasks.py` also serves `GET /api/inbox` (every watch folder with its state, misnamed ones with the nearest valid name) and `POST /api/generations {task}` (a run linked to its task); the page does not need them for the common path.
- The detailed gate API (`review`, `video_sheet`, `.../video`, `regen`, `pack_add`) is unchanged and tested; the UI above is a thin layer over it.

## History: the watch folders, with Remove (`watch.py`, `console/history.js`)

History lists what is in `Phase_01/Images_gen` and `Phase_01/videos_gen` **now**: one row per folder number with the sheet folder and its video folder side by side (files, sizes, a small cached thumbnail at `GET /api/watch/thumb/<img folder>`), the generations made from it, **Generate** (that exact folder) and **Remove**. Remove (`POST /api/watch/remove {number, subject}`) never deletes outright: the image and video folder move to `out/trash/<id>/` (the media is not in git, so a mistaken click must be undoable) and appear under "Removed" with **Restore** (back under their own, final names; refused if the name exists again) and **Delete for good** (`/api/watch/restore`, `/api/watch/purge`). Folder names are validated (`img|vid-NNN-<subject>`), so nothing outside the two watch folders can be touched. Generations that used a folder keep their own copies of the sheet; only the prepared-video path reads the watch-folder video, and says so when it is gone.

## Send to Telegram (`telegram.py`, `console/telegram.js`; checkpoint 1H, phase_01.md Part H)

Pack screen -> **Send to Telegram**. Bot API over `urllib` (no new dependency); the token comes from `MIRSAL_TELEGRAM_TOKEN` / `MIRSAL_TELEGRAM_USER` or from Settings (`out/telegram.json`), is verified with `getMe` when saved, and is never returned by the API, logged or put in an error message. Before any network call every sticker is judged by the verifier's `telegram` stage (video: WebM VP9 + alpha, <= 256 KB, <= 3 s, <= 30 fps, 512 on one side; static: PNG/WebP with transparency, <= 512 KB; 1-20 emoji; WARN when a static sticker lacks the white stroke) and every set by `telegram_set` (1-120 stickers, unique keys, a valid name ending `_by_<bot>`). A Telegram set holds one kind, so a mixed pack becomes `<name>_v_by_<bot>` and `<name>_s_by_<bot>`. Creation sends up to 50 stickers, the rest through `addStickerToSet`; the result is stored on the pack (`library.json` -> `telegram.sets[]` with `file_unique_id`s), so sending again adds only what is new (deletions are not synced). Errors are plain (`press Start on your bot`, `name already taken`, `Cannot reach Telegram`); 429 waits `retry_after`. `GET /api/packs/<id>/telegram` is the dry-run plan, `GET .../telegram.zip` the no-credentials fallback (files + `stickers.txt` + steps for @stickers), `GET /api/telegram`, `POST /api/telegram/config|disconnect` the connection. `MIRSAL_TELEGRAM_API` points the client at the stdlib fake Telegram in `tests/fake_telegram.py`. **Not proven against the real service yet:** the live attempt of 2026-10-01 found and fixed two real-world problems (a malformed Windows certificate broke Python's default TLS context: `_ssl_context()` now loads the store one certificate at a time; an empty multipart body got HTTP 400: calls without files go out as JSON) and then hit intermittent `WinError 10060` timeouts from Python while `curl` worked (open: proxy / IPv6 path). Not built: TGS/Lottie animated stickers (our animations are video stickers), the importing SDK (Phase 5C), set thumbnails (Telegram uses the first sticker).

## Verified

- **1F/1G pass of 2026-10-01** (project venv; synthetic inputs for everything that needs a video): 41 unit tests at the start, 113 at the end (stdlib `unittest`, synthetic fixtures, a fake Telegram), all green; one run under heavy machine load timed out once in a 2x2 test and passed on every rerun. The synthetic golden-path scenario (`tests/test_golden.py`; the first React pass also drove it in a real Chromium, the simple flow was walked in Chromium by hand): G2 rejects 5 and 6, the video sheet has 7 filled slots, Python blocks 1 and 2 with `inside_slot` (frame 27-30, 3 px over the edge band), G4 approves the rest, the final pack is 3, 4, 7, 8, 9 and goes into a Library pack; every sticker's `history` tells its path; the final WEBMs carry the 12 px outline exactly once (alpha-ring test), and the video sheet has none. 2x2 and 1x1 regeneration go through every gate; a misnamed folder is flagged; a sheet without a green screen is blocked on arrival (`background_is_key`); a video made from another sheet is blocked before slicing (`layout_match`).
- **Cost.** On a real 2048 px sheet the sheet stage takes ~170 ms and the 9 cells ~535 ms of which the per-cell checks ~330 ms (the first check carries the lazy sticker render), under the 1 s budget; a full generation (copy, checks, key, slice, plain twins, files) takes ~1.1 s; on the layout slice the verifier is 0.7% of the encode time (budget 20%).
- 17 unit tests pass (stills, recovery ladder, pre-sliced clip path, folder/clip discovery, plan files, console lifecycle); the console UI was driven headlessly in Chromium (carousel, keyboard, thumbnails, no JS errors). Earlier list: statuses, detached detail survives, pack-consistent scale, golden determinism, blue-chroma with green subject, WEBP fallback, engine import boundary (no fastapi/psycopg/langgraph/anthropic/pydantic), synthetic video + loop close, console lifecycle end to end.
- Real `teddy_bear` sheets (2048x2048 JPG): a first sheet gave 8/9 READY with `no_spill` on one slice; the current `img-001` sheet gives 9/9 READY in ~1 s. Haitham judges the look.
- Real pre-sliced clip: `teddy_ (1).mov` -> READY 512x512 WEBM, 242 KB, ~17 s (encode dominates).
- Real teddy video is 960x960, 24 fps, 4.04 s (cells are 320 px, upscaled to 512).
- **Pass of 2026-10-01** (project venv, imageio-ffmpeg 7.1 with libvpx-vp9):
  - all 10 prepared sheets come out **90/90 READY** (6 generic_emojis + 4 teddy); one generic cell carries a `chroma_risk` warning at 46%;
  - all 4 teddy packs animate **36/36 READY** at 149-254 KB, ~5 s per sticker (~50 s per pack, down from ~18 s per sticker); teddy 001 from its `.mov` clips, 002-004 from their own mp4s. The generic_emojis have no videos;
  - on the mp4 path, characters touch their slice edge in up to 72 of 96 frames (teddy 004): the video model moves them across the cut line. The 1F `inside_slot` gate is built for exactly this.
- 41 unit tests pass, including grid (off-third gutters, 2x2, 1x1, mp4 with measured rects), prompter grids, copied-clip detection, and edge-band spill vs interior colour.
