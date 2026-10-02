# Mirsal Builder

High-quality **animated stickers** (not emoji) for Telegram. You say what you want, in a chat or a prompt; the app makes the sheet, cuts and keys it into stickers, checks every one with a
deterministic verifier, lets a human approve, animates the approved ones, and puts them in a pack that goes to a Telegram set. One engine; a chat and a Studio on top.

> **Delivery.** The product is an **API / app** for the existing Mirsal app. The screens in this repo (the Studio and the AI chat in `mirsal/mirsal/console/`) are a sandbox that drives and
> demonstrates the engine through [the HTTP API](docs/api.md): every feature is an engine function and a stable JSON shape first, a screen second.

## Start

```
cd mirsal
python -m venv .venv && .venv\Scripts\activate            # once; always use this venv (the Anaconda base env has a broken numpy)
pip install -r requirements.txt                            # once
python -m mirsal db up                                     # Postgres :5434 and Redis :6380 in Docker (both optional: the app falls back to files and memory)
python -m mirsal doctor                                    # one health check for everything
python -m mirsal serve                                     # http://127.0.0.1:8770 : opens on the AI chat, "Studio" is the detailed workspace
python -m unittest discover -s tests -t .                  # the tests (python + the node helpers; the database tests skip when mirsal-db is down)
```

Everything the app writes goes to `mirsal/out/` (the engine's own names, which the database uses; they never change). Copy `mirsal/.env.example` to `mirsal/.env` for keys and options.
Prepared sheets (optional) go in `inputs/Images_gen/img-NNN-<subject>/` and `inputs/videos_gen/vid-NNN-<subject>/` (the folder names are final: never renamed).

## How a sticker is made (the golden path)

```
chat / prompt ─► plan (template-locked prompt, 1-5 tags per cell)  G1  you approve (the price is shown first)
   ─► sheet (Higgsfield · Nano Banana 2, 2k)  ─► Python blocks bad cells  ─► stills                          G2  you approve
   ─► video sheet from the approved stickers only  G3  ─► video (Kling v3.0)  ─► Python checks every frame   ─► animations  G4  you approve
   ─► pack  G5  ─► Telegram
```

Python's blocks are final; a human approves at every gate; the vision model only pre-reviews; rejection never deletes; a sticker keeps its `S#` through every stage. Details:
[engine and gates](docs/engine-and-studio.md).

## What is in it

| | |
|---|---|
| **AI chat** (`#/agent`) | "What will you create today?": an agent with memory per subject, a step trace, plan cards with the price, swipeable carousels, one-tap selection, two settings. [docs/agent-and-chat.md](docs/agent-and-chat.md) |
| **Studio** (`#/studio`) | the detailed workspace: request, prompt, stickers with issue colours, edge and stroke, animation, packs, Telegram. [docs/engine-and-studio.md](docs/engine-and-studio.md) |
| **Engine** | sheet → key → scale → stickers → WEBM; a verifier of 44 checks over 9 stages; the five review gates; Studio edits as layers. [docs/engine-and-studio.md](docs/engine-and-studio.md) |
| **Live generation** | template-locked prompts (v1-v3), an emotion bank, an AI slot filler with a lint, Higgsfield through its CLI, jobs as files, credits and a usage ledger. [docs/generation.md](docs/generation.md), [docs/higgsfield.md](docs/higgsfield.md), [docs/operator.md](docs/operator.md) |
| **Store and search** | Postgres mirror (generations, decisions, tasks, jobs, ledger, chats), the sticker pool with local vector search, photo cutouts, LangSmith tracing. [docs/store-and-search.md](docs/store-and-search.md) |
| **Vision judge** | a local multimodal model pre-reviews stickers and animations; uncalibrated until 30 labels exist. [docs/agent-and-chat.md](docs/agent-and-chat.md) |
| **HTTP API** | JSON routes, SSE events per generation, idempotency keys, signed asset links, accounts (owner / member tokens, per-user ownership), per-minute rate limits, an OpenAPI document, health. [docs/api.md](docs/api.md) |
| **Design** | one shell and one palette for every screen: the rail, the second column, the token set, the style tiles, and the Earlier-batches column. [docs/design.md](docs/design.md) |
| **Independent review** | a ready-made prompt for another LLM to audit the whole app: [docs/review-prompt.md](docs/review-prompt.md) |
| **Measurements** | recorded numbers — slot fill, search precision, vision-judge agreement, sharpness; no opinions: [docs/measurements.md](docs/measurements.md) |
| **Telegram** | send a pack (images and video are split into two sets), a no-token fallback for @stickers. [docs/engine-and-studio.md](docs/engine-and-studio.md) |

## Services, ports and models

| | |
|---|---|
| Studio and API | `127.0.0.1:8770` (`serve --port N`; stdlib server, localhost only) |
| Postgres + pgvector | `localhost:5434` (`mirsal-db`; 5433, 5436 and 5437 belong to other projects: never touched) |
| Redis | `localhost:6380` (`mirsal-redis`; 6379 is another project's) |
| LM Studio | `localhost:1234`: **`qwen3.5-4b:2`** for the assistant, the plan expansion and the vision judge (hardcoded), **`text-embedding-nomic-embed-text-v1.5`** for the pool (hardcoded) |
| Higgsfield | the `higgsfield` CLI (logged in): Nano Banana 2 at 2k for sheets, Kling v3.0 `pro` for animation, never 4k; every paid call is a line in `out/model_calls.jsonl` |
| OpenAI | optional fallback only (`OPENAI_API_KEY`) |

## Folders

```
README.md  CLAUDE.md  HANDOFF.md        this file · the rules for LLM sessions · what is still open and what waits for Haitham
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
change; never commit a token, `.env` or `opencode.json`. The full list is in [CLAUDE.md](CLAUDE.md); the open work is in [HANDOFF.md](HANDOFF.md).
