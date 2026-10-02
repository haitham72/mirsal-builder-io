# Operator loop: fulfilling Mirsal jobs with the Higgsfield CLI

The operator is a Claude Code session (or a script) on a PC where `higgsfield auth login` is done and a
workspace is selected. Mirsal never holds Higgsfield credentials; it only writes job files. Read
`docs/higgsfield.md` (S0: the real commands, parameters, costs and the standing model choices:
Nano Banana 2 at 2k, Kling v3.0, never `4k`) before running jobs. Never run `higgsfield auth token`.

## The server does this itself

Pressing Generate in the Studio (or `POST /api/live/sheet`, `/api/live/video`) creates the job and the server runs `jobs.fulfil` in the
background: `generate cost` -> `generate create` WITHOUT waiting -> `claim` with the returned id (ticket first) -> `generate wait` -> download ->
`done`. A job that is already CLAIMED (a crashed run) resumes by its ticket. An operator session can do the same by hand:

```
mirsal jobs --status REQUESTED --json          # what is waiting
mirsal hf run J005                             # fulfil one job through the CLI (cost check, ticket first, wait, done)
mirsal hf status                               # credits and plan
mirsal hf models --type video                  # the full Higgsfield list with parameters (cached in out/higgsfield_models.json)
# or the individual steps: mirsal job claim J005 --ticket <id> ... mirsal job done J005 --file <path> --model <name> --cost <n>
```

## Workers and the durable queue

For jobs that must survive a restart of the server: set `MIRSAL_JOB_MODE=queue` for `mirsal serve` and run `python -m mirsal worker` (any number; `--once` drains and exits, `--kinds sheet`, `--poll 2`).
`mirsal queue status | retry J004 | reap | sync` looks after the table. A provider failure is **not** retried by a worker (it can cost credits again); retry it yourself. Details: `docs/generation.md`, "The durable queue and workers".

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
  TIMEOUT; a human re-queues it (`job requeue`), the operator never does. A job that already holds a provider ticket is not created again: re-queue / retry make it wait for the SAME provider job.
- **Never open or judge media.** Judge with Python (`ffprobe`, the verifier, `measure-cells`
  when it exists, file sizes). Haitham looks at the pictures.
- **Never write inside `inputs/Images_gen|videos_gen`.** Downloads go under `mirsal/out/`;
  `job done` copies the file into `out/jobs/<J>/`.
- **Ledger.** Every claim/done/fail appends to `out/model_calls.jsonl` (what, parameters,
  latency, cost, output path). Postgres mirrors it as `model_calls`.

## Job kinds

- `sheet`: `{prompt, aspect 1:1, grid, key_colour}` -> one image. `done` starts the stills run
  exactly as a prepared sheet does (S3); the engine cannot tell generated input from prepared input.
- `video`: `{prompt, input_image (the NORMALISED video sheet from `build_video_sheet()`, never raw
  art), duration_s 3, last_frame_equals_first}` -> one video, attached by ticket and sliced (S4).
- `single`: 1x1 regeneration of one rejected sticker, with the first approved sticker as reference
  when the provider supports it.
