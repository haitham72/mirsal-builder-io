# Higgsfield: what it really offers (S0, measured 2026-10-01)

Everything here was observed on this PC with the Higgsfield **CLI** (`higgsfield`, aliases `higgs`, `hf`; v1.1.26), the way Claude Code is meant to use it (Higgsfield's help center: Claude Code does not use the MCP connector `https://mcp.higgsfield.ai/mcp`, which is for claude.ai / Claude Desktop; Haitham confirmed the CLI). Test outputs are in `mirsal/out/s0/` ; the three calls are in `out/model_calls.jsonl`.

## Access

- Install `npm i -g @higgsfield/cli` (done). Login `higgsfield auth login` (browser OAuth, done by Haitham). **Never run `higgsfield auth token`** (prints the access token).
- A billing workspace must be selected or every call fails with "No workspace selected": `higgsfield workspace set <id>`. Haitham has one (owner, plan `creator`); it is selected on this PC. `workspace unset` undoes it.
- Paid plan required; every generation deducts credits. Balance on 2026-10-01 before S0: 4005.12. Rate limits and concurrency: **not stated** by the CLI or the help center (S3 finds them by running; never run two paid calls at once meanwhile).

## Interface (all non-interactive, scriptable, `--json`)

| Need | Command |
|---|---|
| balance, plan | `higgsfield account status --json` |
| models, params | `higgsfield model list --image\|--video --json`; `model get <job_type> --json` (params, enums, rules) |
| cost before paying | `higgsfield generate cost <job_type> [same params as create] --json` -> `{"credits": N}` |
| create and wait | `higgsfield generate create <job_type> --prompt ... [--param value] --wait --wait-timeout 10m --wait-interval 5s --json` |
| later poll | `generate wait <job_id>`, `generate get <job_id>`, `generate list` |

- `--json` returns an array of jobs: `id` (UUID), `job_type`, `display_name`, `status` (`completed`), `created_at`, `params` (echo), `result_url` (full-quality file on cloudfront; images also `min_result_url`, videos `thumbnail_url`). The result is downloaded with a plain HTTPS GET (no auth header was needed).
- **Job ids double as media inputs:** `--start-image <job id>` / `--end-image <job id>` accepted the sheet's job id with no download or upload. Local paths are auto-uploaded too (`--image`, `--image-references`, `--start-image`, `--end-image`, `--video-references`).
- The async shape without `--wait` was **not tested** (the help says `create` returns the job and `generate wait <id>` polls); S3 must record the id at create time (the ticket-first rule) and test it once.
- The cost estimate matched the balance exactly: estimated 2 + 2 + 3.75 = 7.75, balance fell from 4005.12 to 3997.37.

## Standing choices (Haitham, 2026-10-01)

- **Images: Nano Banana 2 (`nano_banana_flash`) at 2k.** 2 credits, about 22 s.
- **Video: Kling v3.0 (`kling3_0`). Never use its `4k` mode** (18 credits for 3 s; Haitham's rule). Always `pro` (`std` returns 960 px for a square sheet and looked pixelated); Grok always 1080p.

## What was run

| Call | Model (`job_type`) | Params | Time | Credits | Output |
|---|---|---|---|---|---|
| sheet (comparison only) | Nano Banana Pro (`nano_banana_pro`) | 1:1, 2k, template `sheet_3x3_v1` prompt for "teddy bear" | 37.0 s | 2 | PNG 2048x2048 RGB, 4.3 MB |
| **sheet** | **Nano Banana 2 (`nano_banana_flash`)** | same | 22.5 s | 2 | PNG 2048x2048 RGB, 4.4 MB |
| **video, std** | **Kling v3.0 (`kling3_0`)** | 1:1, duration 3, mode std, sound off, `--start-image` = `--end-image` = the NB2 sheet, template `video_v1` prompt | 82.4 s | 3.75 | MP4 H.264 yuv420p **960x960, 24 fps, 3.04 s (73 frames)**, 3.2 MB, no audio stream |
| **video, pro** | Kling v3.0 (`kling3_0`) | same, mode **pro** | 166.6 s | 4.5 | MP4 H.264 yuv420p **1440x1440, 24 fps, 3.04 s (73 frames)**, 5.5 MB; first-vs-last frame diff 2.34 (mean step 5.48), so also a continuous loop |

Prices from `generate cost`: Nano Banana 2 1k 1.5 / 2k 2 / 4k 3 credits; Kling v3.0 3 s std 3.75 / pro 4.5 (4k exists, 18 credits, **not to be used**); Kling 3.0 Turbo 3 s 4.5. Balance after S0: 3992.87 (spent 12.25 = 2 + 2 + 3.75 + 4.5).

## What it means for Mirsal (numbers, not looks; nobody opened the media)

- **No alpha anywhere.** Image PNG is RGB and the video is yuv420p: transparency stays the engine's job (chroma key), as in Phase 1.
- **The key is not a flat #00FF00.** In both the sheet and the video the background is about RGB (12, 222, 27) with a green std of about 20 (video and sheet agree), ~53% of the sheet and 43-49% of the video frames. The Phase 1 key/spill logic has to be what handles it; S3 shows whether the stills pass it.
- **Video resolution is the quality dial, and `pro` fixes most of it.** A 3x3 sheet video is 960 px in `std` = 320 px per cell (the same softness measured on the old samples) but **1440 px in `pro` = 480 px per cell**, close to the 512 px final sticker, for 0.75 credits more and about twice the wait. S4 uses `pro` unless Haitham says otherwise; the 2x2 grid or one sticker per video remain the fallbacks.
- **24 fps, 3.04 s:** Telegram needs <= 30 fps, <= 3 s. The encode step must trim to 3.0 s; resampling to 30 fps is the engine's existing path (S4 verifies).
- **Loop:** with start image = end image the mean absolute difference between the last and first frame is 3.64, about one ordinary frame step (3.93, max 5.35), so the clip is continuous across the loop point. This was measured on one clip.
- **The first video was made from the raw sheet, as discovery only.** Production S4 uses the normalised video sheet (`build_video_sheet`, decision 3), never raw art.
- **Provider seam:** because the CLI is a plain subprocess that prints JSON, it can serve as a real provider behind the jobs interface (the plan assumed an MCP operator could not be called by the server). S3 decides whether `generation/jobs.py` gets a `higgsfield-cli` fulfiller or the operator session keeps running the same commands.

## Other models seen, not tested

Video: `veo3_1`, `seedance_2_0` (start/end image, duration, 480p-4k), `kling3_0_turbo`, `kling2_6`, `minimax_h3`, plus tools `sam_3_video` (Remove Background: could give alpha directly, S7 candidate), `topaz_video`, `bytedance_video_upscale`, `fps_boost`, `depth_anything_video`. Image: `gpt_image_2_5`, `seedream_v5_pro`, `ideogram_4_5`, `recraft_v4_1`, `flux_2`, `image_background_remover`. 34 image and 30+ video job types in total (`model list`).
