# CLAUDE.md — Mirsal Builder (rules + routing)

**Product:** high-quality, flashy **animated stickers**, **not emoji**. Emoji appear only as the ≥1 tag Telegram requires per sticker; there is no 100×100 custom-emoji output.
The app is in its **dev cycle**: the build phases are retired; what exists is documented in `docs/`, what is open is in `HANDOFF.md`. The root `README.md` is the index.

**Session hand-off:** read `HANDOFF.md` first (open work by area, gates waiting for Haitham, guardrails, quirks), then the doc of the area you touch:

| area | doc |
|---|---|
| engine, verifier, gates, Studio, Telegram | `docs/engine-and-studio.md` |
| live generation (prompts, Higgsfield, jobs, credits) | `docs/generation.md`, `docs/higgsfield.md`, `docs/operator.md` |
| Postgres, search, the pool, photos, tracing | `docs/store-and-search.md` |
| the AI chat, the agent, memory, Redis, the vision judge, events | `docs/agent-and-chat.md` |
| the HTTP contract | `docs/api.md` |
| recorded numbers | `docs/measurements.md` |
| a prompt to hand to an independent reviewing LLM | `docs/review-prompt.md` |

Work branch: `merge/generate-advanced` (merged into `main`). Restart the server from `mirsal/.venv` before judging anything in the browser (the Studio warns when it runs older code than the files on disk).
Never commit a Telegram token (any token pasted in chat must be revoked), `.env`, `opencode.json` or `mirsal/telegram-id.md`, and never `git add -A` blind.

## Structure

One generation engine, two interfaces on top, never collapsed into a monolithic prompt: creative intent → spec → generation → processing → validation → animation → persistence.
1. **The AI chat** — natural-language direction with memory per subject, an agent over the Studio's own functions (`docs/agent-and-chat.md`).
2. **The Studio** — explicit controls, prompt-driven, deterministic (`docs/engine-and-studio.md`).

## Rules

1. **Telegram sticker specs:** WEBM/VP9 + alpha (video); PNG/WEBP + transparency (static). Max 256 KB (video) / 512 KB (static), 512×512, 30 FPS, 3s max. Every sticker tagged with ≥1 emoji.
2. **Areas, not phases.** Engine → live generation (Higgsfield through its CLI; Nano Banana 2 for sheets, Kling v3.0 for animation; the video always comes from the normalised video sheet) → Postgres mirror, search, pool, photos, tracing → the agent and chat (LangGraph, Redis, local models) → the HTTP API. Each has one doc in `docs/`. Open work per area is in `HANDOFF.md`; build only what you are asked.
3. **The generation engine is deterministic and independently testable** — never hide it behind conversational abstractions. The engine (`mirsal/engine/`) never imports `psycopg`, `redis`, `langgraph` or a model client (a test enforces it).
4. **Input types:** text, image, text+image, previous generation, previous stickers, event/topic, natural-language transformation.
5. **Default output:** 3×3 master (9 stickers), 2K → 512px final, transparent, 3s animation @ 30 FPS; all user-configurable.
6. **No dead stubs** — if a UI control exists, the backend is implemented; no setting that nothing reads.
7. **HANDOFF is a tracker, not a log (Haitham, hard rule).** An entry is deleted the moment it is implemented: record what exists as architecture in the area's doc in `docs/`, then delete the line from `HANDOFF.md` in the same step (history lives in git). What stays is only what is open: unbuilt work, gates waiting for Haitham's verdict, backlog, questions. Check every change against the open items of the areas next to it.
8. **Lean dependencies + cross-platform.** Windows dev PC (macOS also supported). Use the project venv `mirsal/.venv` (the Anaconda base env has a broken numpy). Stdlib first, minimal wheels, no CDN at runtime, `pathlib` only, no shell-specific commands, ffmpeg from PATH or `imageio-ffmpeg`. Anything fetched from the internet (wheels, Docker images, model weights) is fetched once and loaded from disk. `python -m mirsal doctor` is the single health check; every area extends it.
9. **Naming convention:** inputs are one folder per variant, `img-NNN-<subject>/` and `vid-NNN-<subject>/` (paired by NNN), plus optional pre-sliced clips in `vid-NNN/slices/`; **the watch-folder names are final, never rename them** (History's Remove moves a folder pair to `out/trash/` on Haitham's click and Restore puts it back under the same names). Outputs `<media>-<NNN>-<task_slug>-<key>.<ext>` in `mirsal/out/G00N/slices/` (the engine's names, which the database uses; they never change). The readable mirror of a live batch is `generated/images/…` and `generated/videos/…` (git-ignored; `MIRSAL_EXPORT_DIR` overrides). Never open media files to judge them; use validators and metrics.
10. **The golden path is the spine** (`docs/engine-and-studio.md`, "The golden path"). request → plan with 1–5 tags + margin per cell (**G1**) → sheet → Python blocks bad cells → stills (**G2**) → video sheet from the approved stickers only (**G3**) → video → Python boundary check on every frame → animations (**G4**) → final pack (**G5**). Every change keeps it working end to end. Python's blocks are final (one exception, at Haitham's request: a human may **allow** an animation Python blocked for leaving or crossing its slot — `inside_slot` and `cross_slot` of a returned video — with an explicit recorded click that can be taken back; every technical block, format, size or codec, stays final); a human approves or rejects at every gate (**the vision model only pre-reviews and never approves**); rejection never deletes; a sticker keeps its original `S#` through every stage. Every decision is a `reviews` row in Postgres (searchable), mirrored to LangSmith when tracing is on, and a `history` line in `result.json`. Grids are 3×3 or 2×2 (user's choice); regenerating one sticker is a 1×1 through the same engine. **Hard truth:** request → external task id (written to `out/jobs/*.json` and `out/tasks/*.json` at `claim`, before waiting) → Postgres `tasks` row `{external_task_id, name_key}` → dev lookup and search. The verifier (`engine/verify.py`) runs at every stage and its BLOCK verdicts are final.
11. **Delivery (Haitham): the product is an API / app, not these screens.** Everything under `mirsal/mirsal/console/` and `mirsal/web/` is a **sandbox** that drives and demonstrates the engine. Design every feature as an **engine function + a stable JSON contract first** and the screen second; never put logic only in the browser. Edits, packs, jobs, chats and Telegram sends are addressable by id and reproducible from their stored data.
12. **Docs are part of every change.** A new feature area, a changed contract or a change of provider is not finished until its doc in `docs/`, `README.md` (when the index changes), `HANDOFF.md` and these rules are updated in the same step. Stale statements are deleted, not left beside the new ones.
13. **Never spend without a go-ahead.** Paid calls (Higgsfield, OpenAI) happen only after the price is shown and the user agrees (or turned "Ask before spending" off); tests never reach a real provider (`MIRSAL_NO_REAL_CLI`, fakes); one paid call at a time; every call is a line in `out/model_calls.jsonl`. The local models (`qwen3.5-4b:2`, `nomic-embed-text-v1.5`) are hardcoded and free; nothing asks LM Studio which models exist.
