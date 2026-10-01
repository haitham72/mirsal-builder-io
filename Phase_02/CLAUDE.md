# Phase_02 — supporting material for `../phase_02.md`

Phase 2 is **live generation**: the prompt engine, generation through **Higgsfield (CLI)** on the file store (no database), and the vision check. It was Phase 3 until 2026-10-01 (Haitham reordered: generation first, Postgres second). **The live half is built and in use** (architecture: `README.md` in this folder). The open work is `../phase_02.md` ("Open steps": S4 measurement, S5 AI-lab rating, S6 vision judge, S7 quality work). This folder holds Haitham's inputs to it.

- `prompt_samples.md` holds Haitham's golden prompts and the prompt-lab test inputs. New examples go into it, not into new files.
- `higgsfield.md`: what the Higgsfield CLI really offers (measured models, params, costs, output formats, the standing model choices: Nano Banana 2 at 2k for sheets, Kling v3.0 `pro` for animation, never 4k).
- **From Haitham:** keep `higgsfield auth login` valid on the PC that runs jobs (a billing workspace is selected); a daily credit budget for tests (`MIRSAL_DAILY_CREDITS`); at S6 one decision (the judge on `OPENAI_API_KEY`, which is already set for the slot filler, or an agent judge) and **30 labelled stickers** (approve / reject); ratings of the live sheets and of the 20-prompt AI lab.
- **Gates:** S0 (built, ran) -> S1 (prompt lab text) -> S2 (jobs) -> S3 (first real sheet, ran: G001-G008) -> S4 (normalised video, measured) -> S5 (AI lab) -> S6 (vision judge) -> S7 (quality work), each reviewed before the next.
- **Prompt templates:** the master prompts are saved template files per grid (`mirsal/prompts/templates/`, versioned `_v1` ... `_v3`, never edited once used) filled by a small slot JSON plus a small reviewer. Haitham iterates prompt quality later by adding template versions and style presets.
- **Read `../Phase_01/README.md` first** (Phase 1 as built), keep the lean-dependency rules (CLAUDE.md rule 8), never commit a key (`.env` only), and never open or judge media (Python and the human judge).
