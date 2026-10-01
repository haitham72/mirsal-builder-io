# Phase_02 — supporting material for `../phase_02.md`

Phase 2 is **live generation**: the prompt engine, the vision check, and generation through **Higgsfield (CLI)**, on the file store (no database). It was Phase 3 until 2026-10-01 (Haitham reordered: generation first, Postgres second). The spec is **`../phase_02.md`**; start at its "Ready to go" section. This folder holds Haitham's inputs to it.

- `prompt_samples.md` holds Haitham's golden prompts and the prompt-lab test inputs.
  - Seed `mirsal/prompts/examples/` from it.
  - Build `planner_v1.md` from its teddy-bear meta-prompt. Its JSON output format is the planner schema.
- `higgsfield.md`: what the Higgsfield CLI really offers (measured models, params, costs, output formats, the standing model choices). Read it before S3.
- **From Haitham:** keep `higgsfield auth login` valid on the PC that runs jobs (a billing workspace is selected); a daily credit budget for tests; at S5 one decision: OPENAI_API_KEY for the slot filler and the judge, or agent-written slots and an agent judge; 30 sticker labels (approve / reject) at S6; ratings of the first live sheets.
- **Gates:** S0 (the two test outputs) -> S1 (prompt lab) -> S2 (jobs) -> S3 (first real sheet) -> S4 (normalised video, measured) -> S5 (LLM filler) -> S6 (vision judge) -> S7 (quality work), each reviewed before the next.
- **Prompt templates:** the master prompts are saved template files per grid (3x3, 2x2, 1x1 regen) filled by a small slot JSON plus a small reviewer (`../phase_02.md` Part 1). Haitham iterates prompt quality later by versioning templates and style presets.
- New examples from Haitham go into `prompt_samples.md`, not into new files.
- **Read `../Phase_01/README.md` first** (Phase 1 as built), keep the lean-dependency rules (CLAUDE.md rule 8), never commit a key (`.env` only), and never open or judge media (Python and the human judge).
