# plan.md — next build: pack resolver, short codes, picker, versions (ledger core built)

Source of truth for each phase is `docs/export to team/mirsal-export-architecture.md` §9–§10.7. Build in order; each phase ends green
(one narrowest test run per change, `docs/testing.md`) before the next starts. No paid call without Haitham's explicit yes (rule 13).

## Phase 2 — resolver + chat wiring (pack intent, generate more)

- Pack intent (`"generate sticker pack for {subject}"`) → new session + first claim; `generate more` → next unclaimed preset, same session;
  all-claimed → "pack complete" with choices (custom 9-pick / new pack), in words. Loser of a double-click reads the winner's row.
- Call the built ledger (`generation/claims.py`): `claim_next` for both intents, `mark_requested` when the sheet job is created, `link_generation` when its batch exists (the job's DONE path), `ClaimError` text as the answer.
- Tests: resolver/agent tests by name. Needs Haitham's eyes on the reply wording once (W1-style browser look, not a test gate).

## Phase 3 — short codes (exports stop emitting `G###`)

- Registry `out/export_codes.json` + allocator (random 4, check, retry) at claim time; lazy backfill at first export for old batches;
  `export_names` id field becomes the code, manifest carries both ids; Postgres mirror column + migration.
- Tests: allocator collisions on a fake registry, export output with codes, re-export stability.

## Phase 4 — exporter bank picker UI (Studio export dialog)

- Per-`unresolved` cell bank choice (recorded human pick, reversible, saved on the sticker); fallback stays until picked.
- Tests: `tests/js` builder test for the dialog + route test by name; one browser look at the end.

## Phase 5 — in-batch versions

- `sticker.versions[]` (+ `normalise` default, write-through), Studio version switcher, export ships latest approved; old versions kept.
- Non-preset batches keep new-batch regen until unified (open decision, do not mix into this phase).

## Phase 6 — paid proof (Haitham's yes first, ~2 credits + one pack later)

- One face-preset sheet (`generic emojis`, v4 + core-v1): measure keying/cut only, never open the media. If limbs persist, tighten the
  v4 clause once (new `_v5` files, never edit v4 after use) and retry once. Then one pack at the default gap.

---

# plan.md — extra local-vLLM judge tests (no human labels)

(Kept from before, untouched. Runs after or between the phases above; it needs no code changes.)

Haitham, 2026-10-07: no labeling, ever, in this track. Everything below runs
on the free local server against the 30 prepared cases; no Postgres, no paid
calls, no OpenAI fallback unless asked. Model-vs-model agreement is tracked;
human accuracy is never claimed (`local_eval/WORKFLOW.md:35`).

## Baseline (do not rebuild)

- `mirsal/local_eval/` runner (`prepare | run | smoke | summary`,
  options `--limit/--timeout/--max-seconds`) + `dataset.json` (30 cases).
- 2026-10-05 Qwen 9B: 25/30 usable verdicts (83.3% usable-response, not
  accuracy), median ~10 s/sticker, UNJUDGED on unsupported reason codes.
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
