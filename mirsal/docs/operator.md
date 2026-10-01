# Operator loop (Phase 2 S3): fulfilling Mirsal jobs with the Higgsfield CLI

The operator is a Claude Code session (or a script) on a PC where `higgsfield auth login` is done and a
workspace is selected. Mirsal never holds Higgsfield credentials; it only writes job files. Read
`Phase_02/higgsfield.md` (S0: the real commands, parameters, costs and the standing model choices:
Nano Banana 2 at 2k, Kling v3.0, never `4k`) before running jobs. Never run `higgsfield auth token`.

## The loop

```
mirsal jobs --status REQUESTED --json          # take the oldest
mirsal job show J001 --json                   # everything needed to call Higgsfield
# check the cost against the daily budget (Haitham's number for the day)
# higgsfield generate cost ...   then   higgsfield generate create <model> ... --wait --json
mirsal job claim J001 --ticket <higgsfield id>   # IMMEDIATELY, before waiting
# poll the Higgsfield job until done or the timeout; download the result
mirsal job done J001 --file <path> --model <name> [--cost <credits>]
# or: mirsal job fail J001 --reason "..."
```

One line per job when done. Repeat until none is waiting.

## Rules

- **Ticket first.** `claim` stores `external_task_id` before the operator waits. A crashed
  re-run finds the CLAIMED job and resumes by ticket instead of paying twice. The ticket is
  mirrored into `out/tasks/<task>.json`.
- **One job at a time.** Never run two paid calls concurrently from one session.
- **Budgets.** The estimated credit cost is printed before a job is created and again at `done`.
  A daily cap (`MIRSAL_DAILY_CREDITS`, default: no cap — set it when Haitham gives the number)
  refuses new paid jobs. If one experiment or the day's total would burn a large share of the
  remaining credits, stop and tell Haitham.
- **Retries.** Transient errors retry at most 2 times; invalid input never retries. There is
  never a "while not good" loop. A job older than `MIRSAL_JOB_TIMEOUT` (default 20 min) shows
  TIMEOUT; a human re-queues it (`job requeue`), the operator never does.
- **Never open or judge media.** Judge with Python (`ffprobe`, the verifier, `measure-cells`
  when it exists, file sizes). Haitham looks at the pictures.
- **Never write inside `Phase_01/Images_gen|videos_gen`.** Downloads go under `mirsal/out/`
  (gitignored); `job done` copies the file into `out/jobs/<J>/`.
- **Ledger.** Every claim/done/fail appends to `out/model_calls.jsonl` (what, parameters,
  latency, cost, output path). Phase 3 imports it as `model_calls`.

## Job kinds

- `sheet`: `{prompt, aspect 1:1, grid, key_colour}` -> one image. `done` starts the stills run
  exactly as a prepared sheet does (S3); the engine cannot tell generated input from prepared input.
- `video`: `{prompt, input_image (the NORMALISED video sheet from `build_video_sheet()`, never raw
  art), duration_s 3, last_frame_equals_first}` -> one video, attached by ticket and sliced (S4).
- `single`: 1x1 regeneration of one rejected sticker, with the first approved sticker as reference
  when the provider supports it.
