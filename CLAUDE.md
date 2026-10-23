# CLAUDE.md — Mirsal Builder (rules + routing)

**Last updated: 2026-10-23.** Implementation baseline `27009185` is on `main`, the only local/remote branch. Pack/export pricing is implemented and locally verified; CMS JSON delivery and stored-price readback remain open. Current acceptance: [DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md).

**Product:** flashy **animated Telegram stickers**, not emoji (emoji only as the ≥1 tag per sticker). v1.0 done 2026-10-04; open work is `docs/backlog.md`, human verdicts `docs/waiting-for-haitham.md`. Public deployment and Google OAuth stay paused (plan in git history). The full text of every rule below, with its history, is [`docs/rules.md`](docs/rules.md): read it only when a rule's detail matters.

**Starting a session (lean: a cold start must stay small).** Start from the current user request and read **only the doc of the area you touch** (table below). App review and API delivery use `DELIVERY_CHECKLIST.md`; read `docs/backlog.md` and `docs/waiting-for-haitham.md` when the task touches open work. Prefer `rg` over reading whole files; never dump a whole doc.

Plans and handoffs are temporary notes for active work, removed when stale or finished; they are not required startup files or standing trackers. What is built lives in `README.md` and `docs/`; acceptance checks live in `DELIVERY_CHECKLIST.md`.

| area | start at |
|---|---|
| engine, verifier (44 checks), golden path, gates G1–G5, Studio, "Use it anyway", Telegram send, imports, naming | `docs/architecture.md` |
| AI chat, agent, memory, Redis, vision judge, events, Telegram chat, support agent | `docs/architecture.md` |
| Postgres, search, pool, photos, tickets, Help & Support records, measurements | `docs/architecture.md` |
| reactions engine (presets, emoji map, Lottie slots, super reaction), emoji bank | `docs/architecture.md` |
| live generation, prompts, Higgsfield/Kling, jobs, credits, operator runbook | `docs/generation.md` |
| HTTP contract, accounts, office LAN, Users, Trending, credits, Export to collection | `docs/api-integration.md` (live routes: `GET /api/openapi.json`) |
| look of the screens (shell, rail, palette, tiles, Home, themes, welcome, redesign contracts) — **read before any CSS or markup change** | `docs/design.md` |
| rules in full + session guardrails | `docs/rules.md` |
| reference inputs (prompt samples, telegram spec, eval sets) | `docs/inputs/` |
| what is open / what needs Haitham | `docs/backlog.md`, `docs/waiting-for-haitham.md` |

## Standing instructions

- **Tests (budget, Haitham 2026-10-04):** one narrowest run per change (`mirsal test fast` / `focused` / `area <module>`; map in `mirsal/test_tiers.py`); zero tests for docs; a pass stays valid until its files change; the slow tier and full `unittest discover` are retired, never run. Uncertainty is not a reason to run a bigger suite.
- **Git:** unattended coding, then commit + push, is authorized (2026-10-04); one commit per phase, explicit paths, never `git add -A`; never commit a Telegram token, `.env`, `opencode.json`, `mirsal/telegram-id.md`, credentials or keys. `main` is the maintained branch; Haitham requested consolidation and removal of the other branches on 2026-10-23. Work on `main` unless a task explicitly calls for an isolated branch. Two sessions can share one checkout: check `git branch --show-current` before every commit.
- **Server:** FastAPI on uvicorn (`api/app.py`, native `api/routers/`, `api/schemas/`; compatibility imports remain in `console`); existing routes go through the adapter byte for byte, new routes are native with pydantic; `serve --stdlib` stays one release. Restart from `mirsal/.venv` before judging the browser.
- **Office LAN** (`serve --lan`, email + password, approval in Users > People and the Telegram bot) stands in for the paused deployment.

## Structure

One engine, two interfaces (the AI chat; the Studio), never one monolithic prompt: intent → spec → generation → processing → validation → animation → persistence.

## Rules (short form; detail in `docs/rules.md`)

1. **Telegram specs:** WEBM/VP9+alpha (≤256 KB) or PNG/WEBP (≤512 KB), 512×512, 30 fps, ≤3 s, ≥1 emoji tag.
2. **Areas, not phases;** five docs hold it all; build only what is asked. Sheets: Nano Banana 2; animation: Kling v3.0 from the normalised video sheet; Higgsfield through its CLI.
3. **The engine (`mirsal/engine/`) is deterministic and testable;** it never imports `psycopg`, `redis`, `langgraph` or a model client (a test enforces it).
4. **Inputs:** text, image, both, a previous generation or stickers, an event/topic, a natural-language transformation.
5. **Default output:** 2×2 master (4 stickers), 2K → 512 px, transparent, 3 s @ 30 fps; explicit 3×3 and existing/imported grids remain supported (Haitham, 2026-10-19).
6. **No dead stubs:** a UI control always has a backend that reads it.
7. **Trackers are trackers, not logs:** an implemented entry is written into its area doc and deleted from `backlog.md` / `waiting-for-haitham.md` in the same step.
8. **Lean and cross-platform:** venv `mirsal/.venv` on Windows and macOS (create locally; commands in `run.md`); stdlib first for engine and CLI; `pathlib`; ffmpeg from PATH or imageio-ffmpeg; no CDN at runtime; `python -m mirsal doctor` is the one health check, extended by every area.
9. **Names:** watch folders `img-NNN-<subject>/` + `vid-NNN-<subject>/` are final; outputs `{media}-{subject}-{action}[-{pack}]-{UTC}-{hash}.{ext}` (`runtime/names.py`); new batches `out/G###-<slug>-<UTC>/`, jobs `out/jobs/J###-<subject>-<kind>.json`; the id is the address; never build `out / "G111"` by hand (`pipeline.gen_dir`, `out_path`, `jobs.job_dir`); older names are never renamed. Never open media to judge it: validators and metrics.
10. **The golden path is the spine:** request → plan (G1) → sheet → stills (G2) → video sheet from approved stickers (G3) → video → per-frame boundary check → animations (G4) → pack (G5). Python's blocks are final **only** where Telegram would reject the file (format, size, codec, dimensions, fps, duration, audio, alpha) or nothing was cut; **every other block gets a visible, recorded, reversible "Use it anyway"** on every surface that shows the picture (Studio tile, sheet slice, chat card, creator message), plus one bulk control per batch; a sheet-level layout problem never stops a sheet. Never add a block a person cannot get past. A human approves at every gate (the vision model only pre-reviews); rejection never deletes; `S#` is kept; every decision is a `reviews` row + a `history` line; problems are tickets (LangSmith retired). `engine/verify.py` (`OVERRIDABLE`, `TECHNICAL`) is the one table.
11. **The product is an API:** `console/` and `web/` are a sandbox; every feature is an engine function + a stable JSON contract first, the screen second; never logic only in the browser.
12. **Docs are five files, and they move with the code:** the affected doc, `README.md` when the index changes, the trackers when open work changes, these rules when a rule changes, in the same step; stale statements deleted. No new doc file without a reason Haitham accepts.
13. **Never spend without a go-ahead:** paid calls only after the price is shown and accepted; tests never reach a real provider (`MIRSAL_NO_REAL_CLI`, `MIRSAL_LLM_PROVIDER=none`, fakes); several paid jobs may run at once (`MIRSAL_PAID_PARALLEL`, default 3); every call is a line in `out/model_calls.jsonl`. Models: local chat = what the local server lists (`llm.resolve_local_model`, readiness by a one-token probe); cloud default `openai:gpt-6-luna` (effort high; `services/llm_catalog.py`); embeddings local `nomic-embed-text-v1.5`; vision judge: configured cloud model → `MIRSAL_LLM_FALLBACK` via Nararouter → local LM Studio → "unjudged" (`FAIL_CLOSED`).
