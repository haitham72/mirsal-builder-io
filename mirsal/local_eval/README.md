# Local Qwen 30-sticker evaluation

Uses the supplied LM Studio native endpoint `http://localhost:1234/api/v1/chat` and exactly `qwen/qwen3.5-9b`. No remote fallback, paid generation, plugins or application configuration changes. Chats use `store: false`, temperature 0 and reasoning off. Native API schema: https://lmstudio.ai/docs/developer/rest/chat.

From the `mirsal/` directory in PowerShell:

```powershell
& .\.venv\Scripts\python.exe -B local_eval/run.py prepare
& .\.venv\Scripts\python.exe -B local_eval/run.py smoke
& .\.venv\Scripts\python.exe -B local_eval/run.py run
```

The dataset selects 30 unique READY still stickers round-robin across existing batches. Source files are read only. Their hashes are pinned; changed images are refused. Generation reviews, Library, app settings and live model-call ledgers are never modified.

The model receives the production vision-review prompt and one sticker on grey, then its answer is parsed by the existing verdict parser. This checks local vision responses, structured verdicts and latency. It does not test animation motion, reference-image consistency, pool search, or chat resolution. Sampling is deterministic, not a representative random sample or a balanced accuracy benchmark.

Outputs: `dataset.json`, resumable `results.jsonl`, `summary.json`, `results.md`, and the example rhyme response in `smoke.json`. Each invocation has a four-minute budget and stops after three consecutive failures. Already recorded cases are skipped on the next run, including failures; inspect a failure before deliberately removing its result to retry it. No automatic repair calls are made.

Independent human labels start empty. Saved review states are retained as context, never passed to the model and never treated as fresh ground truth. Optionally fill `human_decision` with `APPROVE` or `REJECT` and `human_reason` in dataset.json, then regenerate metrics without calling the model:

```powershell
& .\.venv\Scripts\python.exe -B local_eval/run.py summary
```

Agreement includes UNJUDGED responses as mismatches for labelled cases. The 80%/30-case target from the tracker is a provisional agreement criterion, not proof of general model quality. With empty labels the report explicitly says quality agreement is not measured. Creating this dataset does not complete human calibration.
