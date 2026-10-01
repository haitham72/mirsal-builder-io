# Phase_03 — supporting material for `../phase_03.md`

Phase 3 covers prompt expansion, the vision quality check (VLM via vLLM; does each sticker match its prompt and emoji; should the green key have been blue), and the generation APIs. The spec is **`../phase_03.md`**; this folder holds Haitham's inputs to it.

- `prompt_samples.md` holds Haitham's golden prompts and the prompt-lab test inputs.
  - Seed `mirsal/prompts/examples/` from it.
  - Build `planner_v1.md` from its teddy-bear meta-prompt. Its JSON output format is the planner schema.
- `search_queries.md` (pending, from Haitham): ~30 "{topic} doing {action}" queries (English, Arabic, Arabizi) with the sticker IDs he considers relevant, plus ≥5 that should return nothing. It is the checkpoint 3B eval.
- `photos/` (pending, from Haitham; **gitignored**, never commit): 10+ real test photos (pets, people, food) for the 3C cutout and 3E parallax, including a few **iPhone Portrait-mode HEIC** photos, which carry embedded depth.
- **Templates (optional, from Haitham):** extra 3D template art. Drop PNG frame folders into `mirsal/templates/<id>/` using the `template.json` format in `../phase_03.md` Part 7. The builder ships 30+ procedural starters, so nothing blocks on this.
- **Gates:** 3A (prompts, vision check, APIs) → 3B (semantic pool) → 3C (photo cutout) → 3D (text templates) → 3E (parallax photos), each reviewed before the next. No Redis in this phase.
- New examples from Haitham go into `prompt_samples.md`, not into new files.
- **LangSmith (moved here from Phase 2, 2026-10-01):** Haitham decides cloud vs self-hosted and provides `LANGSMITH_API_KEY`. Not blocking: the trace seam ships with the `none` backend and a fake-server test (`../phase_03.md` Part 3b).
- **Prompt templates:** the master prompts are saved template files per grid (3x3, 2x2, 1x1 regen) filled by a small slot JSON plus a small reviewer model (`../phase_03.md` Part 1). Haitham iterates prompt quality later by versioning templates and style presets.
