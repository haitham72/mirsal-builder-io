# plan.md — next build: pack resolver, short codes, picker, versions (ledger core built)

Source of truth for each phase is `docs/export to team/mirsal-export-architecture.md` §9–§10.7. Build in order; each phase ends green
(one narrowest test run per change, `docs/testing.md`) before the next starts. No paid call without Haitham's explicit yes (rule 13).

## Next (Haitham, 2026-10-08): the Studio's batch -> generation rows, then Import inside a batch

Backend is built and tested (`docs/engine-and-studio.md` "Batches, generations, regenerate"); the screens are not.

1. **Stickers view header.** Title `Batch 1`, `Batch 2` … (no `sheet 044 · G119`; the G### goes in a tooltip). Under it ONE row `generation 01 … n` from
   `GET /api/generations/{id}/family` (fetched when the batch view changes and after a regenerate, never on every poll): click = view it; on each chip
   **pick** (`POST …/pick`, one per batch, the picked one marked), **remove** (the existing trash route, confirm first), **report** (`data-act=tkreport
   data-k=generation data-id=G###`). Animate / Add act on each batch's PICKED generation. Replace the old Variations strip (`gvarsHtml` in live.js and its
   lines in `tests/js/history_card.test.js`) with this row.
2. **Animation view: the same, adapted.** Under the batch title the picked generation, then `animation 01 … n` = its video sheets that have a video:
   pick (`POST …/pick_video`), remove (`POST …/remove_video`), report (`data-k=animation data-id=G###/A2`). Regenerate (video) is already one button.
3. **Import inside a batch** (Haitham: "import in Stickers and in Animation, proper naming"). Stickers: an imported image becomes the next generation of
   THIS batch (the batch's plan/cells and naming, `parent` + `regen_of`, like Regenerate) — extend `flow/imports.import_file` with the batch. Animation: an
   imported video attaches to THIS batch's picked generation; which sheet it was animated from is decided by comparing its first frame with the image sheet
   and with the generation's video sheet (the closer one wins: image sheet -> sliced as a prepared 3x3 video; video sheet -> `quick_sheet` + attach as the
   next animation, after `redo_video` when one exists). No question to the person; the answer says which one was used.
4. Then plan Phase 2 below (the claim ledger behind Next batch: today "unclaimed" is derived from the batches on screen, not from `claims.py`).

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

- Built 2026-10-08: earlier results are kept (`stickers[].anim_versions[]`, retired video sheets, every generation of a batch). Still open: a switcher to look at an earlier animation clip without re-cutting, the Postgres mirror of picks and versions, export naming per version (`revision`).
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
