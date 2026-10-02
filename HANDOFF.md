# HANDOFF: what is open (the only tracker)

A **tracker, not a log** (`CLAUDE.md` rule 7): an entry is deleted the moment it is built and documented in `docs/`; history lives in git. The old phase plans (`phase_0N.md`) are retired: what
was still open in them is below, grouped by the area it belonged to, one or a few lines each.

Owner: **Haitham** (they/them; never guess pronouns). GitHub `haitham72/mirsal-builder-io` (private). Windows PC (macOS also supported). Read order: this file, `CLAUDE.md`, `README.md`, then the doc of the
area you touch (`docs/`). Where things are built and how they fit is in those docs, not here.

## 1. Waiting for Haitham (each needs a verdict or an input; delete the line when answered)

| What | How |
|---|---|
| **The AI chat and the Studio look right** (aurora, trace, plan card, carousel, phone swipe) | restart `python -m mirsal serve` (the Studio warns when it runs older code), open `/`; on a phone use the PC's address only through a tunnel (the server binds localhost) |
| **Vision judge is calibrated** | label **30 stickers** (approve / reject, with a reason when you can); then `python -m mirsal judge G### --force` on the same ones; target agreement >= 80%, else point it at OpenAI (`MIRSAL_VISION_PROVIDER=openai`). First runs: `docs/measurements.md` (the two local models disagree) |
| **Pool search precision** | write `docs/inputs/search_queries.md`: ~30 queries "{topic} doing {action}" (English, Arabic, Arabizi) with the sticker ids you consider right, plus >= 5 that must return nothing; then `python -m mirsal pool search "..."` is measured against it (first real run in `docs/measurements.md`) |
| **Photo cutout edges** | judge `mirsal/out/photo/photo-upload.png` and 10+ real photos in `inputs/photos/` (git-ignored; include a few iPhone Portrait HEIC, which are not read yet) |
| **Prompt text (S1) and the AI lab (S5)** | `python -m mirsal prompt lab` and `prompt lab --ai` (20 inputs; the AI now runs on the local model), compare with `docs/inputs/prompt_samples.md` |
| **First live results, jobs, Generate menu, edge** | G001-G008 and `mirsal/out/s0/`; "Generate it" in the Studio; the credits pill, Queue panel, Allow anyway, Stroke / Trim with Apply / Undo |
| **One real animated pack, and Kling `pro` at the default gap** | a real run (spends credits) to close S4: `python -m mirsal measure-cells` then shows the flagged share (first numbers: 0.74 gap = 5.6%, 0.80 = 88.9%, 0.84 = 44.4%) |
| **A real chat -> Create run** | with you present: type a request in the AI chat, press Create (spends about 2 credits for a sheet); nothing in the chat has been run against the real Higgsfield yet, only against fakes and prepared sheets |
| **LangSmith** | open project `mirsal` in the account behind the key; decide cloud vs self-hosted; set `MIRSAL_TRACE=langsmith` in `mirsal/.env` to record real runs (off by default) |
| **Decisions** | keep or delete the parked React gateway `mirsal/web/`; a daily credit cap (`MIRSAL_DAILY_CREDITS`); a backup command for `out/`; Arabic prompt handling; moderation policy before any public API |

Closed by Haitham on 2026-10-02: Telegram sends work on several accounts; merge of `merge/generate-advanced` into `main`; improving the `sharpness` metric; live-LLM quality checks; Redis; the old token is revoked.

## 2. Open work by area (the former phases)

**Engine and Studio (was Phase 1)**
- `sharpness` (`engine/verify.py`) cannot see softening (reads 1.00-1.05): replace the metric (gradient correlation or SSIM on the first frames, alpha-edge ramp width), calibrate on more than two cells (approved; thresholds need real cells).
- The Studio's JavaScript has no tests except the chat helpers (node, `tests/js`); add a browser smoke test for issue colours and Include anyway.
- A second request while a job runs gets 409; a real server-side queue would queue it. `result.json` is read-modify-write under one in-process lock plus the cross-process writer lock: two request threads can still interleave inside the server.
- No rate limiting on the server (localhost only).

**Live generation (was Phase 2)**
- S4 re-run with Kling `pro` and the default gap decision (`slot_fill`); S7 decisions: one 3x3 sheet vs single stickers, the engine's outline vs a model-drawn one.
- The vision judge's recovery is a **recommendation** (`vision/recovery.py`); nothing executes it. Executing means paid regenerations, so it needs your confirmation flow (the chat's edit and another-pass cover the cases by hand).
- Original planner leftovers, ask before building: UAE content rules as a lint (no flags / emblems / text, no real people or rulers, the falcon is always a young brown saker falcon chick, Emirati dress, Commemoration Day solemn), English + Arabic Telegram search keywords per cell (0-20, 64 characters, English first), 4x4 and 16:9 sheets (`split_grid` handles 2x2 and 3x3), no trademarks in pack titles and tags, whether the animation sheet should default to 2x2 (2.25x the pixels per sticker).

**Store and search (was Phase 3)**
- 3B: the eval set and precision@5 >= 0.8; an Arabic / Arabizi query parser (a small model; deterministic patterns today); a search-result cache keyed by a `pool_version` counter (embeddings and plans are cached, hits are not); the gap flow shows no price.
- 3C: an `edge_quality` check (a soft alpha gradient, not a binary edge), `--subject N`, a stronger matte (BiRefNet, MIT) and SAM 2 click-to-refine, HEIC input (`pillow-heif`), `SOURCE_PHOTO` asset rows, optional paid AI motion (price first), a composites test (IoU >= 0.92).
- **3D text template stickers (not started).** A library of flashing template stickers with a text slot, CapCut-style: `mirsal/templates/<id>/template.json` (`id, version, tags {en[], ar[]}, occasion, mood, frames[1-4] {art | null, duration_ms, text_style}, slot {x,y,w,h,rotation,align,max_chars,font_id}`,
  optional `subject_slot` for a photo cutout), 30+ procedural starters (greetings, reactions, love, birthday, UAE occasions), text rendered by code (Cairo, OFL, covers Latin and Arabic; Pillow with raqm, fallback `arabic-reshaper` + `python-bidi`; never split a word),
  encoded as WEBM VP9 alpha and animated WebP (not GIF: 1-bit alpha), matched to the last chat message when it is <= 4 words / 24 characters (exact occasion tag, then the embedding, then generic), editing re-renders in under a second as a child generation. Tests: every template passes `template check`, Arabic joins, Telegram validators, "happy eid" ranks Eid templates first.
- **3E 3D parallax photos (not started).** A photo gets depth and tilts with the phone: embedded Portrait-HEIC depth first, else Depth Anything V2 **Small** (Apache-2.0; the larger ones are non-commercial) through onnxruntime, edge-aware guided filter, focal plane at the subject's median depth (the cutout), a self-contained WebGL viewer
  (`parallax.html`, gyroscope with the iOS permission tap, mouse fallback, reduced motion = static), optional `--layers 2|3` with inpainting, optional `--bake` loop video. On-device only; private assets.
- Library packs still live in `out/library/library.json` (the old plan moved them to `packs` / `pack_stickers`; wait for the app's pack curation). `reviews.trace_run_id` exists and nothing writes it. Per-video task rows. An S3-compatible store behind `AssetStore`.

**Agent and chat (was Phase 4)**
- Transformation templates ("dog as banana": required slots dance / shock / squash of the target, "dog with bananas" is not a transformation, the user can override "no dancing") are not built; the plan comes from the slot filler.
- Annotation: what is visible on an approved sticker (`stickers.annotation`, cached by image hash), `build_context(HIGH)` with the real images, annotation text added to the pool's `search_text`.
- Multi-reference: "make 5 like 2" copies sticker 2 into `out/refs/` and sends it as a reference image; the other roles (pose, expression, ...) are recorded (`generation_references`) but not yet worded into prompts.
- The 40-utterance resolver eval (>= 95% exact ids) needs `docs/inputs/resolver_utterances.md` from you; transformation examples likewise.
- Several edited stickers are one 1x1 generation each (at most 4); one generation for all of them, and `inherited_from` carry-over rows, are not built.
- The chat polls; streaming the agent's steps over SSE is not built. There is no terminal `mirsal chat` (the AI screen replaced it). The reducer's model summary has only run against fakes.

**API and production (was Phase 5)**
- An OpenAPI document and generated TypeScript types; user accounts and per-user authorization (`010_users`: `user_id` on sessions, generations, packs; Redis keys switch from `u:local`); rate limiting.
- A durable `jobs` table with `mirsal worker` processes (`FOR UPDATE SKIP LOCKED`, dead-letter after the maximum); Postgres as the durable idempotency backstop; per-job temp directories and retention policies.
- JSON logs (`request_id, session_id, generation_id`), timing and quality metrics (time to first sticker, approval and regeneration rates), the regression suites (visual, chroma, transformation, conversation datasets) in one command.
- The React frontend: decide whether `mirsal/web/` is extended or deleted; the editor's mobile screens.

## 3. Guardrails

| | |
|---|---|
| **Do freely** | Fix real bugs with a failing-then-passing test; add engine functions, CLI commands and API routes with tests; new prompt template **versions** (add `_v4`, never edit one that was used); measurements; docs. |
| **Ask first** | Spending credits (live generation, bulk embeddings through OpenAI, anything paid); verifier severities or thresholds (the `sharpness` rework is approved); deleting an open item whose gate is unanswered; scrubbing the token from history; deleting `mirsal/web/`; anything that changes what the user sees or decides. |
| **Never** | Rename watch folders or outputs (rule 9). Loosen a verifier BLOCK or change "a human approves, Python's blocks are final". Open sticker media to judge it. Commit a token, `.env`, `opencode.json`, `mirsal/telegram-id.md`. Write inside `inputs/Images_gen|videos_gen`. `git add -A` blind. Force-push. Touch ports 5433 / 5436 / 5437 or the other project's `.env` lines. |

**Locked decisions:** the product is an API / app and the screens are a sandbox (rule 11); the golden path and its gates; issue colours (orange out of bounds, purple bad green screen, yellow bad loop, pink look or motion, blue file / Telegram limit, red dropped or blocked; hatched = not in the set, dashed = kept with a check);
out-of-bounds animations off by default with *Include anyway* (`gates.soft_block`); template-locked prompts (the model fills a small JSON, code lints it, the template builds the text); the local models are hardcoded (`qwen3.5-4b:2`, `nomic-embed-text-v1.5`) and nothing asks LM Studio for its model list;
the agent never spends without a go-ahead unless "Ask before spending" is off; the vision model never approves.

## 4. This checkout and how to run

`D:\Vscode\mirsal-builder-io` (work branch `merge/generate-advanced`, merged into `main` on 2026-10-02). `mirsal/.venv` is Python 3.14 (numpy 2.5, OpenCV 5.0, Pillow 12.3: thresholds in `engine/config.py` were calibrated on an older stack, re-check metrics before trusting them).
`mirsal/out/` holds the real generations G001-G008, the library, jobs and the ledger of this PC. Docker Desktop must be running for `db up` (Postgres :5434, Redis :6380); both are optional at runtime.

`mirsal/.env` was copied from another project and holds `PG*`, `REDIS_URL` and `LANGSMITH_*` lines for it: Mirsal ignores `PG*` and `REDIS_URL` and always uses its own project name for tracing, but remove those lines. `mirsal/telegram-id.md` (git-ignored) holds a bot token in plain text: delete it once Telegram is configured in Settings.
**Security:** an old bot token is in git history (commit `349762b`, revoked by Haitham). Offer a history scrub with a force-push but **never do it unasked**.

```
cd mirsal
.venv\Scripts\python -m mirsal doctor                       # health check (a missing sample folder is only a NOTE)
.venv\Scripts\python -m unittest discover -s tests -t .     # all tests (~4 min); the Postgres tests skip as whole classes when mirsal-db is down
.venv\Scripts\python -m mirsal serve --port 8789            # YOUR server on a spare port; MIRSAL_OUT=<copy of out\G###> keeps real data untouched
```

Never kill Haitham's server on :8770. The Studio shows a banner when it runs older code than the files on disk.

## 5. Quirks that cost time

- **Most "it still fails" reports were a stale server process** (Python loads code once). Compare the process start time with the file times first.
- VP9 (`row-mt`) output is not byte-stable: compare metrics, never WebM hashes. Windows `os.replace` fails with WinError 5 on an open file: keep using `pipeline._atomic_write`.
- **Never put a regex with `\b` in a Python string written through a shell heredoc**: it becomes a backspace character and silently breaks the pattern (`grep -rlP "\x08"` finds such damage). Write scripts with the Write tool and use `chr(92)` or raw strings; PowerShell has no `&&` and mangles non-ASCII when it rewrites files.
- Two scripts of the Studio must not declare the same top-level `const` (the second one is not run at all; `history.js` was dead for a while because of `ago`). Class names in `agent.css` are namespaced (`ag-`, `is-`, `k-`) because the Studio's own CSS already uses `.step`, `.tile`, `.sel`, `.done`.
- LM Studio loads a model on the first request (the first call is slow); `qwen3.5-4b:2` thinks unless `reasoning_effort: "none"` is sent (the client does). A test must never reach the real Higgsfield CLI (`MIRSAL_NO_REAL_CLI` is set by `tests/__init__.py`).
- For browser checks without a browser tool: `pip install --target <scratch> playwright` and launch the installed Chrome with `executable_path`; run it against a **copy** of `out/` and never press Create.
- Any bot token pasted into a chat is compromised and must be revoked after testing. `mirsal/.env` and `out/telegram.json` are git-ignored.

## 6. Prompt for the next LLM

> Read `HANDOFF.md`, `CLAUDE.md`, `README.md` and the doc of the area you touch. Apply Haitham's answers from section 1 (delete the lines they close), then work section 2 in order of the area you were given, with a failing-then-passing test for every fix, docs updated in the same step, and no paid call without Haitham's go. Judge media only with Python. Use `mirsal/.venv`. **HANDOFF is a tracker: delete an entry the moment it is implemented and documented.**
