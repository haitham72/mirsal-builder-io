# Mirsal Builder

## Overview and glossary

Mirsal creates **Telegram stickers** from text, images or prepared sheets: request → plan → sheet → still stickers → video sheet → animations → pack → Telegram. One deterministic Python engine serves the **AI chat**, **Studio** and **JSON API**; the screens are a sandbox over that API. Higgsfield generates media through its CLI, local models assist with chat and vision, and `out/` is the source of truth with optional Postgres mirrors and Redis caching. Humans approve review gates and paid calls; tests use fake providers. Read `CLAUDE.md` for rules, `docs/backlog.md` and `docs/waiting-for-haitham.md` for open work, and `docs/` for each area's contract and design.

Mirsal Builder is a local, private app. The words below mean the same in
`README.md`, `CLAUDE.md` and `docs/dev-notes.md`:

- **Batch (`G###`)** — one generation run. Holds a sheet, stickers, a video
  sheet, animations, and a pack.
- **Sticker (`S#`)** — one cell of a batch. Its number never changes.
- **Job (`J###`)** — one paid provider call. Its ticket is stored before
  waiting, so a crash never pays twice.
- **Gates (G1–G5)** — the five human approvals along the path. The vision
  model pre-reviews only and never approves.
- **"Use it anyway" (allow)** — a recorded, reversible human click that lets a
  judgement-call block through. Only Telegram's own limits stay final.
- **Particle set / burst** — still/animated sprites owned by library stickers, and the
  burst rendered from them. Adding the burst affirms it in a pack.

- **Plan** — saved character, cell, tag and prompt instructions before generation.
- **Sheet / video sheet** — a 3×3 or 2×2 character image; the video sheet is rebuilt from approved stickers for animation.
- **Pack / pool** — a named Telegram sticker collection, and the shared searchable sticker store.
- **Test tiers** — the test budget comes first (`docs/testing.md`): one narrow run per change, nothing re-run that already passed, nothing for docs. `area`: mapped checks; `fast`: smoke; `focused`: about 22 reviewed regressions, at most once per phase. The slow tier is retired (Haitham, 2026-10-03): never run, never requested. Python runs alone; focused success is not full verification.

High-quality **animated stickers** (not emoji) for Telegram. You say what you want, in a chat or a prompt; the app makes the sheet, cuts and keys it into stickers, checks every one with a
deterministic verifier, lets a human approve, animates the approved ones, and puts them in a pack that goes to a Telegram set. One engine; a chat and a Studio on top.

> **Delivery.** The product is an **API / app** for the existing Mirsal app. The screens in this repo (the Studio and the AI chat in `mirsal/mirsal/console/`) are a sandbox that drives and
> demonstrates the engine through [the HTTP API](docs/api.md): every feature is an engine function and a stable JSON shape first, a screen second.

## Start

How to set up and run it, alone or for the office: **[run.md](run.md)**.

## Architecture

One engine, two interfaces over it. Every feature is an engine function and a stable JSON contract **first**, a screen second (`CLAUDE.md` rule 11) — the screens in this repo are a sandbox that drives the engine through [the HTTP API](docs/api.md).

```
mirsal/mirrors nothing:  one out/ directory is the source of truth, Postgres mirrors it
browser ── console/ (Studio, AI chat, Library, Create)  ── FastAPI on uvicorn :8770
                          │  JSON only (docs/api.md, OpenAPI in console/openapi.py)
                          ▼
   flow/     the golden path: pipeline.py (stages, result.json), gates.py (G1-G5)
   engine/   pure: sheet, key, video, particles, verify.py (44 checks), no I/O, no deps
   generation/ Higgsfield through its CLI: prompts, jobs (ticket-first), credits, ledger
   vision/   the judge: pre-review only, and effect_plan (what a burst is made of)
   agent/    LangGraph chat over the Studio's own functions; creator.py (run to Telegram)
   store/    Postgres mirror + pgvector pool; media/ library, cutout; runtime/ cache, atomic
   services/ llm, embed, telegram        obs/ tracing        engine/ never imports any of these
```

**The invariants that hold it up** (each is a test, not a promise):

| invariant | where it is enforced |
|---|---|
| the engine is deterministic, pure and free of I/O — no `psycopg`, no `redis`, no model client | `tests/test_store.py::test_engine_boundary` |
| a ticket is written **before** the wait, so a crash never loses or double-charges a paid job | `generation/jobs.py` `fulfil`, `tests/test_jobs.py` |
| no paid call without a shown price and a go-ahead | `agent/graph.py` `n_confirm`, `tests/test_agent.py` |
| the vision model pre-reviews and **never** approves | `vision/judge.py`, `CLAUDE.md` rule 10 |
| Python's blocks are final only where Telegram itself would refuse the file; every other block is a judgement call with one recorded, reversible **Use it anyway** on the picture itself | `engine/verify.py` `OVERRIDABLE` vs `TECHNICAL`, `flow/gates.py` |
| history is append-only: rejection never deletes, a sticker keeps its `S#` | `flow/pipeline.py` `hist` |
| a web page the owner visits cannot drive the local server; `/out/` cannot escape `out/` | `console/server.py` `_foreign` / `_authorize`, `tests/test_hardening.py` |
| no secret ever reaches git or a response | `runtime/users.py`, `services/telegram.py`, `tests/test_hardening.py` |

## How a sticker is made (the golden path)

```
chat / prompt ─► plan (template-locked prompt, 1-5 tags per cell)  G1  you approve (the price is shown first)
   ─► sheet (Higgsfield · Nano Banana 2, 2k)  ─► Python blocks bad cells  ─► stills                          G2  you approve
   ─► video sheet from the approved stickers only  G3  ─► video (Kling v3.0)  ─► Python checks every frame   ─► animations  G4  you approve
   ─► pack  G5  ─► Telegram
```

Python's blocks are final where Telegram itself would refuse the file, and nowhere else: every other block is a judgement call the person can allow with one recorded click — **on the picture itself** (the Studio tile, a cell of the left sheet, the chat tile), with a plain-words reason and one `Use all anyway` per batch. A human approves at every gate; the vision model only pre-reviews; rejection never deletes; a sticker keeps its `S#` through every stage. Details:
[engine and gates](docs/engine-and-studio.md).

## What is in it

| | |
|---|---|
| **AI chat** (`#/agent`) | "What will you create today?": an agent with memory per subject, a step trace, plan cards with the price, swipeable carousels, one-tap selection, two settings. [docs/agent-and-chat.md](docs/agent-and-chat.md) |
| **Studio** (`#/studio`) | the detailed workspace: request, prompt, stickers with issue colours, edge and stroke, animation, packs, Telegram. A compact composer (model, Style, Stroke, Loop, AI enhancer chips; the style tiles open from the Style chip). The Animation tab is a create view (the video sheet to be sent, the video prompt, motion suggestions per sticker). **Batch groups**: variations of one idea are one family (Earlier batches shows one entry; the variations strip sits above the steps; drag a batch onto another or *Add to group*: the target is the parent; Postgres `generations.group_id` / `relation`). **Removed batches** have Restore, Remove and Remove all (files and database rows). One motion language: the AI enhancer's rise-and-fade for what opens, soft transitions for what you touch. [docs/engine-and-studio.md](docs/engine-and-studio.md), [docs/design.md](docs/design.md) |
| **"Use it anyway"** | every judgement-call block is allow-able in one click, on the picture, everywhere it appears (Studio tile, a clickable cell of the left sheet, the chat card, the agentic creator), reversible and recorded; only Telegram's own limits are final. [docs/engine-and-studio.md](docs/engine-and-studio.md), [docs/design.md](docs/design.md) |
| **Engine** | sheet → key → scale → stickers → WEBM; a verifier of 44 checks over 9 stages; the five review gates; Studio edits as layers. [docs/engine-and-studio.md](docs/engine-and-studio.md) |
| **Live generation** | template-locked prompts (v1-v3), an emotion bank, an AI slot filler with a lint, Higgsfield through its CLI, jobs as files, credits and a usage ledger. [docs/generation.md](docs/generation.md), [docs/higgsfield.md](docs/higgsfield.md), [docs/operator.md](docs/operator.md) |
| **Store and search** | Postgres mirror (generations, decisions, tasks, jobs, ledger, chats), the sticker pool with local vector search, photo cutouts. [docs/store-and-search.md](docs/store-and-search.md) |
| **Vision judge** | a local multimodal model pre-reviews stickers and animations; uncalibrated until 30 labels exist. [docs/agent-and-chat.md](docs/agent-and-chat.md) |
| **HTTP API** | FastAPI on uvicorn (existing routes through an adapter over the original handler, byte-identical; new routes native with pydantic), JSON routes, SSE events per generation and per chat turn (`/api/chat/sessions/{id}/stream`), idempotency keys, signed asset links, accounts (owner / member tokens, per-user ownership), per-minute rate limits, an OpenAPI document, health. [docs/api.md](docs/api.md) |
| **Office accounts** | `serve --lan` on the office network with HTTPS; `@nadi.ae` email + password; sign-up waits for approval; Settings > People (add people with a generated password shown once, approve, roles, new password, credits); forgot password goes to Haitham; the Telegram bot sends Haitham a card per request (Approve / Reject / Admin / Send new password / +10 credits) and obeys only his user id. HTTPS set-up once: [certificate-guide.md](certificate-guide.md). [docs/api.md](docs/api.md) |
| **Tickets** | every server error, failed job or refused Telegram send, and every **Report** (batch, particle row, chat reply) is a ticket: what happened, the person's words, the issue, a proposed fix drafted by the local model, one-click questions; Settings > Tickets; a Postgres copy. LangSmith is gone. [docs/store-and-search.md](docs/store-and-search.md) |
| **Testing** | tiers chosen by what a change can actually break: `mirsal test fast` (9s), `focused`, `area <module>` (what that file maps to). The slow tier is retired (Haitham, 2026-10-03): never run, never requested. Nothing maps, nothing runs. [docs/testing.md](docs/testing.md) |
| **Particle effects** | AI image or text-only Kling animated sheets, keyed/cut sprites, one deterministic particle simulator, and ordinary animated-sticker delivery. Animated-sprite restoration is undergoing acceptance. [docs/effects.md](docs/effects.md) |
| **Particle sets** | Sets belong to library stickers, one saved version per row (v1, v2...); three equal sources (sticker sprites, AI image sprites, Kling from scratch); animated sprites in the simulator; Save / Save as new / Add to pack; mistaken-pack recovery; soft delete and restore. [docs/particles.md](docs/particles.md) |
| **Trending** | shared packs to like, comment on and use in your workflow (the Library's Trending tab; a member's Library). [docs/api.md](docs/api.md) |
| **Open work** | v1.0 is done (2026-10-04): [docs/backlog.md](docs/backlog.md) by area, [docs/waiting-for-haitham.md](docs/waiting-for-haitham.md) for decisions. Public hosting and Google OAuth stay paused: [deployment_plan.md](docs/deployment_plan.md) |
| **Burst creation (proposal)** | many packs from one liked sheet: reuse the image, pick actions, one queue each, async; waits for Haitham's go (W27) | [docs/burst_plan.md](docs/burst_plan.md) |
| **Design** | one shell and one palette for every screen: the rail, the second column, the token set, the style tiles, and the Earlier-batches column. [docs/design.md](docs/design.md) |
| **Welcome / onboarding** | the modal that opens once per browser session and on the logo: a fast-cut Seedance ad film and four sliding feature images; the prompts, the credits spent and the checks | [docs/onboarding.md](docs/onboarding.md) |
| **Diagrams** | a paste-ready prompt for an LLM with repo access to draw the app as Excalidraw diagrams (overview, golden path, AI chat turn, paid generation, particles, data, what is next): [diagram-prompt.md](diagram-prompt.md) |
| **Independent review** | a ready-made prompt for another LLM to audit the whole app: [review-prompt.md](review-prompt.md) (repo root), updating the single seeded baseline [docs/review.md](docs/review.md). The standing rules above are the outcome of those audits, now architecture here rather than reports. |
| **Measurements** | recorded numbers — slot fill, search precision, vision-judge agreement, sharpness; no opinions: [docs/measurements.md](docs/measurements.md) |
| **Telegram** | send a pack (images and video are split into two sets), a no-token fallback for @stickers. [docs/engine-and-studio.md](docs/engine-and-studio.md) |

## Services, ports and models

| | |
|---|---|
| Studio and API | `127.0.0.1:8770` (`serve --port N`; FastAPI on uvicorn, `serve --stdlib` for the old server; localhost only) |
| Postgres + pgvector | `localhost:5434` (`mirsal-db`; 5433, 5436 and 5437 belong to other projects: never touched) |
| Redis | `localhost:6380` (`mirsal-redis`; 6379 is another project's) |
| LM Studio (or vLLM) | `localhost:1234` (`MIRSAL_LOCAL_URL`): **whatever the server lists** for the assistant, the plan expansion and the vision judge (the chat's model dropdown; a real readiness probe; a `:N` instance suffix falls back to the base id), **`text-embedding-nomic-embed-text-v1.5`** for the pool (hardcoded) |
| Higgsfield | the `higgsfield` CLI (logged in): Nano Banana 2 at 2k for sheets, Kling v3.0 `pro` for animation, never 4k; every paid call is a line in `out/model_calls.jsonl` |
| OpenAI | optional fallback only (`OPENAI_API_KEY`) |

## Folders

```
README.md  CLAUDE.md  HANDOFF.md        this file · the rules for LLM sessions · a pointer to the trackers in docs/ plus the session state
docs/                                    the documentation (one file per area) · docs/inputs/ (Haitham's inputs and reference)
mirsal/                                  the app: requirements.txt, docker-compose.yml, migrations/, tests/, .env.example
  mirsal/                                the Python package, one folder per concern: engine/ (pure engine) · flow/ (the golden path: pipeline, gates) · generation/ (Higgsfield, jobs, prompts, planner) ·
                                         services/ (LLM, embeddings, Telegram) · runtime/ (cache, events, paths, accounts) · media/ (pack library, video projects, cutout) ·
                                         store/ (Postgres, pool) · agent/ · vision/ · obs/ · console/ (server + Studio + AI screen) · cli.py
  web/                                   a parked React gateway (not served)
inputs/                                  prepared sheets and videos (git-ignored media)
tools/tracker/                           a small tracker for hand-made sheets
ref/                                     the UI design reference and mockup
```

## Rules in one breath

Build only what is asked; the engine is deterministic and independently testable; never open media to judge it (validators and metrics do); no dead controls; docs are part of every
change; never commit a token, `.env` or `opencode.json`. The full list is in [CLAUDE.md](CLAUDE.md); the open work is in [docs/backlog.md](docs/backlog.md) and [docs/waiting-for-haitham.md](docs/waiting-for-haitham.md).
