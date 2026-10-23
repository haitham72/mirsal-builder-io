# Mirsal Builder

[Visual guide](GUIDE.md) · [App and API delivery checklist](DELIVERY_CHECKLIST.md) · [Remaining work](docs/backlog.md)

It turns plain words into video stickers for Telegram: it makes the pictures, cuts them, animates them and packs them. Every step is checkable ([architecture](docs/architecture.md)); the HTTP contract is [here](docs/api-integration.md), the live route inventory at `GET /api/openapi.json`.

## Overview

- **Intent → Spec** Each distinct sticker is fully specified. *Watch folders* (`img-NNN-<subject>/` + `vid-NNN-<subject>/`, see `inputs/`) hold prepared art; *tags* and *margin* fill empty cells; *subject* defaults are `banana` and `cherries`.
- **Spec → Generation** Deterministic *prompt building* (template-locked text); a *plan* previews the cells; a *subject* carries fixed phrasing, references and per-user taste.
- **Processing** Decoding, prep and reference frames accumulate real reusable state. *Reactions* (formerly particles) are bursts attached to stickers, stored as sets (`P###`).
- **Validation** Every gate judges quality before the next step; *batch groups* link variations of one idea; the *pool* reuses approved stickers free.
- **Animation** Video sheets (approved stickers recomposed, `A1`, `A2`, …) are animated, then cut into looping WebMs. *Higgsfield* (sheets) and *Kling v3.0* (animation) run through the Higgsfield CLI as paid jobs (`J###`); *Nano Banana 2* draws the sheets.
- **Persistence** Decisions land in *Postgres* (searchable reviews) and history lines; *tickets* track problems; *model calls* log spend.
- **The glasses** New ideas default to 2×2 (4 stickers); photographers can also ship flat PNG or WebP stickers. One screen holds the project.

## Delivery

The product is the API and the two sandboxes over it: `console/` (the page) and the AI chat. The engine (`mirsal/engine/`) and flow (`mirsal/flow/`) are deterministic and testable first, screens second.

**Start**: `python -m mirsal serve`, then open the printed address. Server default `127.0.0.1:8770`. First run needs: Python 3.11-3.13, venv `mirsal/.venv`, `pip install -r mirsal/requirements*.txt` (fastapi/pydantic/uvicorn for serve), ffmpeg on PATH, Postgres `mirsal-db` on 5434 for the mirror (`python -m mirsal db up`).

## Run

- One checkout per task; check `git branch --show-current` before every commit. Work on `main`; prior work branches were consolidated at Haitham's request on 2026-10-23. Use an isolated branch only when the task calls for one.
- Restart the server from `mirsal/.venv` before judging the browser (the Studio warns when it runs older code). Never kill or automate the real-data server on :8770; it loads new code only when its owner restarts it.
- `python -m mirsal doctor` is the one health check. `serve --lan` serves the office over HTTPS; `serve --stdlib` keeps the old server for one release.
- Keep runs hermetic: tests and scratch runs use `MIRSAL_OUT` copies, never the shared `out/`; only the real `out/` writes through to Postgres.
- Ports 5433/5436/5437 and the other project's `.env` lines are never touched.

## Test budget

One narrowest run per change: `mirsal test fast` / `focused` / `area <module>` (map in `mirsal/test_tiers.py`). Zero tests for docs-only changes; a pass stays valid until its files change. Uncertainty is not a reason to run a bigger suite. Paid tests need Haitham (`MIRSAL_RUN_PAID_TESTS=1`, ≤3 USD, serial). Quirks: Windows file locks (retry), Anaconda `python` ≠ venv, `MIRSAL_NO_REAL_CLI` for fakes.

## The architecture in one breath

The chat (natural language) and the Studio (explicit controls) share one engine: `engine/` pure (sheet, key, video, particles, `verify.py` 44 checks); `flow/` lifecycle (`pipeline`, `gates`, `groups`, `imports`, `support`, `tickets`); `generation/` paid jobs and prompts; `services/` Telegram and models; files are the truth, Postgres mirrors, Redis is disposable. Names carry meaning: `G###` (batch), `S#` (sticker), `J###` (paid job), outcome `READY`/`FAILED`.

## The golden path and the gates

Request → plan (G1) → sheet → stills (G2) → video sheet (G3) → video → per-frame check → animations (G4) → pack (G5). A person approves at every gate; the vision model only pre-reviews; Python blocks only what Telegram would reject, everything else gets "Use it anyway". Rejection never deletes; `S#` is stable; decisions are `reviews` rows + history lines.

## What is in it

| Area | What it does | Doc |
|---|---|---|
| Engine + Studio | Pure media code, the golden path, gates, verifier, Studio flows, Telegram send, imports | [architecture](docs/architecture.md) |
| Chat + agent | Turns, memory, creator, stages, vision judge, Redis, events, Telegram chat, support | [architecture](docs/architecture.md) |
| Storage + search | Postgres mirror, pool, vectors, tickets, Help & Support records | [architecture](docs/architecture.md) |
| Reactions | Presets, emoji map, Lottie slots, super reaction, emoji bank | [architecture](docs/architecture.md) (+ screens in [design](docs/design.md)) |
| Generation (Higgsfield/Kling) | Prompts, jobs, credits, operator runbook | [generation](docs/generation.md) |
| HTTP API | Contract, guards, accounts, office LAN, Users, Trending, integrations | [api-integration](docs/api-integration.md) |
| Export to collection | Queue a pack/batch to the AddCollection CMS | [api-integration](docs/api-integration.md) |
| Design | Shell, screens, themes, welcome, redesign contracts | [design](docs/design.md) |
| Rules | The 13 rules in full + session guardrails | [rules](docs/rules.md) |
| Trackers | Open work and owner verdicts | [backlog](docs/backlog.md), [waiting](docs/waiting-for-haitham.md) |
| Inputs | Reference inputs (prompt samples, telegram spec, eval sets) | [inputs](docs/inputs/) |

Public deployment and Google OAuth stay paused (plan in git history); the office LAN stands in. Open proposals live as one line each in the backlog, full text in git history.

## Services and ports

| Service | Default | Notes |
|---|---|---|
| Local models | `MIRSAL_LOCAL_URL` | Whatever the server lists; readiness is a real probe; embeddings local hardcoded |
| Cloud default | `openai:gpt-6-luna` | Official OpenAI only, effort high; old router ids normalize |
| Database | `mirsal-db:5434` | Mirror; `MIRSAL_DB_WRITE=0` forces off |
| CMS export | `MIRSAL_COLLECTION_API_URL` | `MIRSAL_COLLECTION_API_CREDENTIALS` = `sk-…` in `mirsal/.env`, never in git |

## Folders

`mirsal/` (package, tests, migrations, `out/`, `inputs/`), `docs/` (five files: architecture, design, api-integration, generation, rules · backlog/waiting trackers · `inputs/` reference), `deploy/` (parked), `tools/`, `Faz3/` (separate). On-demand screenshots stay in local `output/playwright/` artifacts.

## Rules in one breath

Telegram limits; lean deps; `pathlib` ASCII-only; file locks for processes/threads; engine never imports `psycopg`; rules live in `docs/rules.md`; errors are exceptions with messages; JSON reports; docs are five files and move with the code; files are the truth; the golden path and its gates; an exception never stands in for a missing feature. Adults accept anything that is genuinely adult; the product is an API: engines, contracts and tests in Python, no logic only in the browser. Strict separation of test/prod — tests use fakes and a temp `out/`. `docs/api-integration.md` is the HTTP contract.
