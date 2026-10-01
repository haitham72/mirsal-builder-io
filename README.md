# Mirsal Builder

High-quality **animated stickers** (not emoji) for Telegram: a request or a prepared sheet becomes keyed, scaled, verified stickers, then animations, then packs, then a Telegram set. One deterministic Python engine; everything else sits on top.

> **Delivery (Haitham, 2026-10-01).** The product is an **API / app** for the existing Mirsal app. The screens in this repo (the "Studio" sandbox in `mirsal/mirsal/console/`, the parked React gateway) are a sandbox and proposal that drive and demonstrate the engine. Every feature is an engine function plus a stable JSON contract first, a screen second.

## Where things are
| What | Where |
|---|---|
| Project rules, routing, the golden path | [`CLAUDE.md`](CLAUDE.md) |
| Session state, open list, next prompt | [`HANDOFF.md`](HANDOFF.md) |
| Prompt for an independent LLM review (it writes `report.md`) | [`REVIEW_PROMPT.md`](REVIEW_PROMPT.md) |
| **Phase 1 — built:** engine, verifier, gates, Studio, Telegram. Architecture, how to run, API, tests | [`Phase_01/README.md`](Phase_01/README.md), finish list in [`Phase_01/CLAUDE.md`](Phase_01/CLAUDE.md) |
| **Phase 2 — live generation built, measuring next:** prompt lab, jobs, the Higgsfield CLI fulfiller, model selector, usage log, the Generate menu; the vision judge and the measurements are open | [`phase_02.md`](phase_02.md) (open steps), arch in [`Phase_02/README.md`](Phase_02/README.md), inputs in [`Phase_02/`](Phase_02/CLAUDE.md) |
| **Phase 3 — 3A, 3B lexical pool and 3C photo core built; 3B vectors, 3D, 3E next:** Postgres, tracing, pool, photo / text / depth stickers | [`phase_03.md`](phase_03.md), arch in [`Phase_03/README.md`](Phase_03/README.md), inputs in [`Phase_03/`](Phase_03/CLAUDE.md) |
| Phase 4 Redis + LangGraph + intelligence; Phase 5 API + hardening (+ reference client) | [`phase_04.md`](phase_04.md), [`phase_05.md`](phase_05.md) |
| Design spec and mockup of the sandbox UI | [`ref/`](ref/) |

(The order of Phases 2 and 3 was swapped on 2026-10-01; older notes saying "Phase 2 = Postgres" are stale.)

## Run it
```
cd mirsal
python -m venv .venv && .venv\Scripts\activate     # once; always use this venv
pip install -r requirements.txt                      # once
python -m mirsal doctor                              # health check
python -m mirsal serve                               # http://127.0.0.1:8770  (Ctrl+C, run again to restart it after code changes)
python -m unittest discover -s tests -t .            # the tests
```
Everything the app writes goes to `mirsal/out/` (git-ignored). Details, every command, the API and the architecture: `Phase_01/README.md`.

## Docs rule
A major step is not finished until the docs are: the phase README (architecture), `HANDOFF.md`, the phase plan, `CLAUDE.md` and the affected `Phase_0N/CLAUDE.md` are updated and stale text is deleted (`CLAUDE.md` rule 12).
