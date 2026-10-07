# plan.md — extra local-vLLM judge tests (no human labels)

Haitham, 2026-10-07: no labeling, ever, in this track. Everything below runs
on the free local server against the 30 prepared cases; no Postgres, no paid
calls, no OpenAI fallback unless asked. Model-vs-model agreement is tracked;
human accuracy is never claimed (`local_eval/WORKFLOW.md:35`).

## Baseline (do not rebuild)

- `mirsal/local_eval/` runner (`prepare | run | smoke | summary`,
  options `--limit/--timeout/--max-seconds`) + `dataset.json` (30 cases).
- 2026-10-05 Qwen 9B: 25/30 usable verdicts (83.3% usable-response, not
  accuracy), median ~10 s/sticker, 5 UNJUDGED on unsupported reason codes.
  Results in `results.md` / `summary.json`.

## Steps

1. Fresh full run on the current local pick (whatever LM Studio lists now —
   `llm.resolve_local_model`, never a hardcoded id), from the repo root:
   `mirsal/.venv/Scripts/python.exe -B mirsal/local_eval/run.py run`
   Free local server only.
2. Compare `summary.json` against the Oct-05 baseline (usable-rate, median
   latency, UNJUDGED count + reason codes). Append one dated block to
   `docs/measurements.md`; docs are part of the change (rule 12).
3. Two-model disagreement re-check (current pair, S6 shape): record which
   stickers the models split on. A split is a finding about the models,
   never a verdict about the sticker.
4. Delete this plan when done (finished plans are deleted; what was built
   lives in README/docs).
