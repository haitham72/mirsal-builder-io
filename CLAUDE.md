# CLAUDE.md — Mirsal Builder / Mirsal Stickers (routing + rules)

**Status:** Active rebuild. Previous version: [`proposals/Mirsal-chat-emojis`](../Mirsal-chat-emojis) (archived backup; context-aware stickers for chat).

**Product:** high-quality, flashy **animated stickers**, **not emoji**. Emoji appear only as the ≥1 tag Telegram requires per sticker; there is no 100×100 custom-emoji output.

Live plan: **`phase_01.md` … `phase_05.md`** (one spec per phase) + `Phase_0N/` folders (Haitham's inputs and review gates per phase). **`README.md` is the architecture of what is already built.**

## Structure

Two interfaces sharing one generation engine:
1. **Creator Mode** — explicit controls, prompt-driven, deterministic
2. **Conversational Mode** — natural-language creative direction, iterative

Never collapse into monolithic LLM prompt; separate creative intent → spec → generation → processing → validation → animation → persistence.

## Rules

1. **Telegram sticker specs:** WEBM/VP9 + alpha (video); PNG/WEBP + transparency (static). Max 256 KB, 512×512, 30 FPS, 3s max. Every sticker tagged with ≥1 emoji.
2. **Phases (the build plan):** `phase_01.md` engine (prepared sheets → key/scale → stickers + WEBM) plus the desktop Sticker Builder UI over it (Parts D and E: video/GIF projects and the optional AI matte; `ref/` holds its design spec and mockup; desktop only, Phase 5C expands it to mobile) and the golden path with review gates (1F, rule 10) → `phase_02.md` Postgres (+ reviews, search; seamless integration, nothing new for the user) → `phase_03.md` template-locked prompt engine + VLM check + generation APIs + LangSmith tracing (3A) , semantic sticker pool (3B), photo cutout stickers (3C), CapCut-style text template stickers (3D), and 3D parallax photos (3E) → `phase_04.md` Redis + LangGraph + intelligence (4A/4B/4C) → `phase_05.md` API + frontend + hardening (5A/5B/5C). Build only the phase you're given. Each `Phase_0N/` folder's CLAUDE.md lists that phase's inputs from Haitham and its review gates. The original `mvp plan.md` / `full plan.md` were fully absorbed into these phases and removed. They're in git history; don't look for them in the tree.
3. **Generation engine is deterministic and independently testable** — never hide it behind conversational abstractions.
4. **Input types:** text, image, text+image, previous generation, previous stickers, event/topic, natural-language transformation.
5. **Default output:** 3×3 master (9 stickers), 2K → 512px final, transparent, 3s animation @ 30 FPS; all user-configurable.
6. **No dead stubs** — if a UI control exists, the backend is implemented.
7. **Plans are hand-off / next steps; the README is the architecture.** Once a step is built and verified, record it in `README.md` (as architecture: what exists, how it fits, the naming and contracts) and tick it in its `phase_0N.md`. A plan item is deleted only after Haitham approves that gate, so the plan thins out over time and is eventually removed. Updating a plan means **enhancing** it (findings, corrected assumptions, sharper next steps), never shrinking it. Every change in one phase must be checked against the following phase's plan and `Phase_0N/CLAUDE.md`, and those updated if it affects them.
8. **Restricted network + cross-platform.** The dev PC has poor internet and runs Windows (macOS also supported). Stdlib first, minimal wheels, no CDN/npm at runtime, `pathlib` only, no shell-specific commands, ffmpeg from PATH or `imageio-ffmpeg`. Anything fetched from the internet (wheels, Docker images, model weights) is fetched once on a connected machine and loaded from disk. `python -m mirsal doctor` is the single health check and each phase extends it. Details: `README.md`, "Restricted network / library policy".
9. **Naming convention:** inputs are one folder per variant, `img-NNN-<subject>/` and `vid-NNN-<subject>/` (paired by NNN), plus optional pre-sliced clips in `vid-NNN/slices/`; **the watch-folder names are final, never rename them**. Outputs `<media>-<NNN>-<task_slug>-<key>.<ext>` in `mirsal/out/G00N/slices/`. Never open media files to judge them; use validators and metrics.
10. **The golden path is the spine** (`phase_01.md`, checkpoint 1F). The flow is: request → plan with 1–5 tags + margin per cell (**G1**) → sheet → Python blocks bad cells → stills (**G2**) → video sheet from the approved stickers only (**G3**) → video → Python boundary check on every frame → animations (**G4**) → final pack (**G5**). Every phase keeps it working end to end. Python's blocks are final; a human approves or rejects at every gate (the VLM only pre-reviews); rejection never deletes; a sticker keeps its original `S#` through every stage. From Phase 2 every decision is a `reviews` row in Postgres (searchable) and from Phase 3 it is mirrored to LangSmith when tracing is on. Grids are 3×3 or 2×2 (user's choice); regenerating one sticker is a 1×1 through the same engine.
