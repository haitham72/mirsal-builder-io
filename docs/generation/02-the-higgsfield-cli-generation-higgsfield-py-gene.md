# The Higgsfield CLI (`generation/higgsfield.py`, `generation/model_catalog.py`)

<sub>Part of [generation.md](../generation.md).</sub>

- `generation/higgsfield.py` is a thin subprocess wrapper: `account`, `cost`, `create` (WITHOUT waiting, returns the job id), `wait`, `download`, and `dump_models`/`load_models` (the full list:
  34 image, 38 video, 8 audio, 1 text model with every parameter, cached in `out/higgsfield_models.json` for a day). It calls the vendored `hf.exe` directly with an argv list
  (the npm `.cmd` shim would let cmd.exe interpret `&`, `%` or quotes in a prompt). It never runs `auth token`. `MIRSAL_NO_REAL_CLI` (set by `tests/__init__.py`) makes any real call fail:
  no test can spend credits. `NEVER` bans Kling `4k`.
- `generation/model_catalog.py` is the selector's data: 8 image models (Nano Banana 2 / Pro / 2 Lite, GPT Image 2 / 2.5 with the flare/sunburst variant, Seedream 5.0 Pro / Flash / Lite) and
  3 video models (Kling v3.0 always `pro`; Grok Video 1.5 and Grok Imagine 1.5 Lite (`grok_video_v15_lite`, Haitham's pick 2026-10-08, fixed 1:1) always 1080p; nothing below 1080 is offered), each with its selections; `resolve(kind, model, options)` validates and returns the CLI's job_type and params. Every other
  model of the dump is selectable too (options generated from its own parameter list). Defaults: Nano Banana 2 at 2k, Kling v3.0 pro, 3 s.
- Logos: `console/assets/vendors/<logo>.svg` (Google, ByteDance, Kuaishou fetched once from the Simple Icons set); OpenAI and xAI get a monogram until Haitham drops `openai.svg` / `xai.svg`
  into that folder. The app logo is `console/assets/brand/mirsal-logo.png` (the white-background JPEG in `ref/` made transparent).
