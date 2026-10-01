# Phase 2 — built so far: Higgsfield discovery (S0), prompt lab (S1), file jobs (S2), slot reviewer (S5 remainder)

Live generation runs on the file store (no database). Higgsfield is driven through its **CLI**
(`Phase_02/higgsfield.md`: the measured models, params, costs and outputs, and the standing choices
Nano Banana 2 at 2k and Kling v3.0, never 4k). S0 made one sheet and two videos (std, pro) for
12.25 credits, all in `out/model_calls.jsonl`; the jobs seam below is proven with a fake operator and
is what S3 connects to the CLI.

## S1 — prompt lab, offline (`mirsal prompt`)

`mirsal prompt "<request>" [--grid 3x3|2x2|1x1] [--style ID] [--ai] [--review-ai] [--mode sheet|single]`
prints the locks, the 9 concepts, the template-built sheet/single/video prompts and the lint verdict,
through the same `tasks.preview` + `prompter.validate_plan` contract the console uses. `mirsal prompt lab`
runs 20 inputs (English, Arabic, Arabizi, occasion, green subject, constraint, style blend): **20/20 pass
lint** (deterministic filler; 9 cells, 9 unique keys, emoji each).

Finding: the deterministic filler does not apply the green-word rule (a green frog still gets a green
key); the AI path (`expander.py`) does. Template versions stay `_v1`; prompt quality is iterated by
adding `_v2` templates, never editing `_v1` in place.

Live smoke (2026-10-01, one call): `prompt "falcon dancing" --ai` -> 9 distinct dance concepts, lint PASS,
logged to `out/model_calls.jsonl` (`LLM_PLAN openai gpt-4.1-mini, 228+414 tokens, 5.9 s`). Haitham's
approval of the text against `prompt_samples.md` still pending.

## S2 — jobs as files (`mirsal/jobs.py`)

`out/jobs/J###.json` (`REQUESTED|CLAIMED|DONE|FAILED|TIMEOUT`), claim stores `external_task_id`
**before** waiting and mirrors it into `out/tasks/<task>.json`; `done` copies the result into
`out/jobs/<J>/` with sha256; `fail` records the reason; `requeue` gives a timed-out job a fresh
waiting period (a human act, never automatic). Every transition appends to `out/model_calls.jsonl`.

- CLI: `mirsal jobs [--status] [--json]`, `mirsal job show|create|claim|done|fail|requeue`.
- API: `GET /api/jobs[?status]`, `GET /api/jobs/<id>`, `POST /api/jobs`,
  `POST /api/jobs/<id>/claim|done|fail|requeue` (same shapes; JobError -> the same error JSON).
- UI (additive, existing style): the Higgsfield dialog grew a "No prepared sheet: generate it" button
  that creates the sheet job and polls `GET /api/jobs/<id>` every 5 s with the elapsed time until
  DONE/FAILED. The button walkthrough in a browser awaits Haitham (no browser in this session);
  the API behind it is covered by tests.
- Operator loop: `mirsal/docs/operator.md`.

## S5 remainder — slot reviewer (`expander.review`)

Code lint first, then a cheap second model answering `{ok, problems[]}` (one repair round already
lives in `expand`). Opt-in per call (`review_ai=True`, `prompt --review-ai`): the default stays one
model call so unattended runs do not double spend. Fake-model tested; live reviewer runs stay with
the 20-prompt AI lab (Haitham's call).

## Tests

`tests/test_jobs.py` (8): fake-operator flow, ticket-first mirroring, fail/requeue, TIMEOUT display,
ledger lines, the API round trip (incl. 409 on double-claim, 400 on bad kind), the offline lab,
the reviewer (lint + fake-model accept/reject, never a live call).

## Not built (needs the authorised session or Haitham)

S3 first real sheet through the unchanged stills run, S4 normalised video + `measure-cells`,
S6 vision judge + 30 labels, S7 measurements. `out/jobs/*.json` and `out/model_calls.jsonl` keep the
shapes `phase_03.md` expects, so Phase 3 imports them unchanged.
