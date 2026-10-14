# Lifecycle (`flow/pipeline.py`, one line per transition in `out/G00N/events.jsonl`)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

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

`result.json` is the record Phase 3 persists: generation id/number/`parent`, prompt, task, source (subject, variant, files, video info), stage, error, and per sticker `index, key, name, emoji, prompt, status, reason, report[], metrics{}, png, webm, anim_status, anim_reason, anim_metrics{}`. Statuses: `READY | FAILED` (stills), `NOT_REQUESTED | PROCESSING | READY | FAILED` (video). A failed cell never blocks the other eight; a video failure never fails the still. `result.json` is rewritten after every animated cell while the UI polls it, so `pipeline._atomic_write` (tmp + `os.replace`) and `read_result` share one in-process lock, and the replace retries ~2 s on `PermissionError` (Windows WinError 5 when something else has the file open). If an animate job dies, cells it never reached go back from `PROCESSING` to `NOT_REQUESTED` (the UI would otherwise show "Animating…" forever); `tests/test_atomic_write.py` covers the lock and the retry. Animation runs `EngineConfig.anim_workers` (4) cells at a time (`video._run_cells`; `on_cell` is serialised, so callers may save state in it): 9 cells of a 960 px 3x3 video went 55 s to 21 s with byte-identical WEBMs.
