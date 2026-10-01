# HANDOFF: Mirsal Builder (state of 2026-10-01, end of the unattended build session)

Owner: **Haitham** (they/them; never guess pronouns). GitHub `haitham72/mirsal-builder-io` (PRIVATE). Branch **`merge/generate-advanced`**, committed and pushed; `main` is **12 commits behind and can fast-forward** (Haitham decides when). Windows PC (macOS also supported).

Read in this order: this file → `CLAUDE.md` (12 binding rules) → `Phase_01/README.md` (the architecture as built) → `Phase_02/README.md` and `Phase_03/README.md` (what those phases built) → `phase_02.md` (the live steps still open). `Phase_01/CLAUDE.md` is the Phase 1 leftover list.

## 0. In one minute

- **Phase 1 is built and committed.** Verified sheets/videos -> stickers -> animations, the review gates, the Studio UI, layered editing, packs and one-click Telegram (Haitham confirmed Telegram works). What is left is Haitham's own checks on real data.
- **Phase 2 offline parts are built:** S1 prompt lab (`mirsal prompt`), S2 file jobs (`jobs.py`, API, the "generate it" button, `mirsal/docs/operator.md`), the S5 slot reviewer, the model-call ledger. **Live Higgsfield (S0, S3, S4, then S6, S7) is not started:** it needs a Claude Code session in which the Higgsfield MCP tools exist (`opencode.json` lists no MCP servers). Never fake those calls.
- **Phase 3 is partly built, on Haitham's orders:** 3A Postgres (`mirsal-db`, port 5434), 3B lexical pool (`mirsal pool`), 3C offline photo cutout core (`mirsal photo`). 3B vectors, the 3B eval set, 3C real-photo judgement and 3D-3E are not built. Phases 4-5 are plans only.
- **Gates not yet reviewed by Haitham:** S1 (prompt text vs `prompt_samples.md`), S2 (button walkthrough in a browser), 3A (their own restart proof), 3B, 3C. The build ran unattended on their standing order; each gate still needs their approval before its plan items are deleted (rule 7).
- **Do not rework or revert the UI/UX or the engine. Build on it.** Section 2 says exactly what is safe.

## 1. What is next

1. **Haitham reviews the open gates** (section 0) and answers the open questions: revoke the old bot token (section 5, item 7), `main` fast-forward, keep or drop the `sharpness` check (section 5, item 3).
2. **S0 in a Higgsfield-authorised session.** Run `/mcp` (or search the tool list for "higgsfield"). If the tools are not there, stop and tell Haitham. Then: list every tool, model, parameter, limit and credit cost; make one test image and one test video; write `Phase_02/higgsfield_mcp.md` (is a job id returned, synchronous or polled, first/last frame or loop, output size/format/duration, cost per call, rate limits). That doc decides how S3-S4 are built, so write it from what you saw. Then S3-S7 in the order of `phase_02.md`, adapting to what S0 found. **Where reality disagrees with `phase_02.md`, change the plan** (rule 7: enhance, never shrink) and say why in the doc.
3. **Safe backlog** (section 5) between steps: `_CRF_HINT`, the `sharpness` metric, the Origin/Host check.

The seam to keep: **jobs as files** (`out/jobs/J###.json`, claim/ticket stored *before* waiting, done/fail) so a plain HTTP provider can replace the MCP operator later behind the same interface (an MCP connector is a tool of an interactive session, not an API the server can call; production in Phase 5 needs a real HTTP provider). The engine stays ignorant of who fulfils the job.

**How to work during the live steps:**
- **Freedom:** call Higgsfield as much as needed to learn (prompts, models, sheet vs single, loop options, resolutions, seeds). Keep the ledger: every paid or model call is a line in `mirsal/out/model_calls.jsonl` (what, parameters, latency, credits if shown, output path). If a single experiment or a day's total would burn a large share of the credits left, pause and tell Haitham.
- **Never open or judge generated media yourself.** Judge with Python: `ffprobe`, `python -m mirsal doctor`, the verifier (`engine/verify.py`), `measure-cells`-style metrics, file sizes. Test outputs go under `mirsal/out/` (gitignored), never inside `Phase_01/Images_gen|videos_gen`.
- **Gates:** do not block on Haitham. Finish the step, record the evidence, mark it "awaiting Haitham's review" in `phase_02.md`, and move to the next step that does not depend on their decision.
- **Raw samples are not input to the video model.** The video is made from the **normalised video sheet** (`engine/video_sheet.py: build_video_sheet`, `slot_fill` = 0.55, one scale, margins). Measured on Haitham's pre-rendered samples: 3 of 9 teddy and 8 of 9 emoji animations leave their cell. S4's job is to make that near zero; `slot_fill` is the dial; the fallback is one sticker per video.
- **Docs in the same step** (rule 12): `Phase_02/higgsfield_mcp.md`, `docs/phase2_measurements.md`, `Phase_02/README.md` (architecture), this file, the `phase_02.md` ticks. Check each change against `phase_03.md` and `Phase_03/CLAUDE.md` (Phase 3 imports `out/jobs/*.json`, `out/model_calls.jsonl` and the task tickets: keep their shapes or update `phase_03.md`).

**Built, do not rebuild:** template-locked prompts (`prompter.py`, `prompts/templates/`), the AI subject expander and slot reviewer (`expander.py`, `llm.py`; OpenAI, `gpt-4.1-mini`, key `OPENAI_API_KEY`), tickets (`tasks.py`, `POST /api/plan`, `/api/tasks`, `/api/generations {task}`), jobs (`jobs.py`, `/api/jobs`, `mirsal jobs`/`job`), `mirsal prompt` (+ `prompt lab`), `model_calls.py` (ledger), the video upload endpoint `POST /api/generations/<id>/video_sheet/<A>/video`, the video-sheet builder and layout slicer, `inside_slot` / `inside_frame` / `cross_slot`, `recheck`, `profile`, the animation cache, Send to Telegram, the Postgres store (`store.py` area, `db`/`list`/`show`/`history`/`search`/`task`), `pool.py`, `mirsal photo`. **Not built:** `measure-cells`, the vision judge (S6), the live operator runs, `Phase_02/higgsfield_mcp.md`, `docs/phase2_measurements.md`, vectors/embeddings for the pool.

## 2. Guardrails: what is safe and what is not

| | |
|---|---|
| **Do freely** | Everything in Phase 2: new modules (operator tooling, vision judge), new CLI commands, new endpoints, new tests, new docs, Higgsfield experiments, prompt template **versions** (add `_v2`, never edit `_v1` in place), measurements. Fix real bugs you find, each with a test that fails before and passes after. Add checks to the verifier only with a PASS and a FAIL fixture and a measured threshold. |
| **Additive only** | The Studio UI (`mirsal/mirsal/console/*`). Add controls **in the existing style** (same components, colour system, wizard) and wire each to a working backend (rule 6: no dead stubs). Do not restyle, rearrange, rename or remove anything that exists. |
| **Do NOT** | Rework or redesign the UI/UX (the five header views, the Pack wizard, the issue-colour system and the hatching on both sheets, Include anyway, Edge, the sticker detail, the Library box selection, one-click Telegram). Revert or "simplify" previous work. Rename the watch folders or outputs (rule 9). Change the golden path, the meaning of the gates, or "a human approves, Python's blocks are final" (rule 10). Loosen a verifier BLOCK. Rewrite git history or force-push. Push or merge to `main`. Start Phase 4. Commit a token, `.env`, `opencode.json`, or `Phase_01/telegram.md`. Open sticker media to judge it. Write inside `Phase_01/Images_gen|videos_gen`. Use `git add -A` blind. |
| **Ask Haitham first** | Anything that changes what the user sees or how they decide; any change to verifier severities or thresholds that were measured; deleting plan items (only Haitham's approval of a gate deletes them); merging `merge/generate-advanced` into `main`; scrubbing the token from git history; starting 3B vectors, 3D or 3E. |

**Locked decisions (Haitham; do not reopen):** phase order (1 engine, 2 live generation, 3 Postgres, 4 Redis+LangGraph, 5 API); the product is an **API / app** and this UI is a sandbox (rule 11), so every feature is an engine function plus a stable JSON contract first; the Studio's five views; the issue-colour semantics (orange out of bounds, purple bad green screen, yellow bad loop, pink look or motion, blue file/Telegram limit, red dropped or blocked; hatched = not in the set, dashed = kept with a check); out-of-bounds animations are off by default and a human may **Include anyway** (`gates.soft_block`: only when every failed check is WARN; a real BLOCK stays final); template-locked prompts (the model fills a small JSON, code lints it, the saved template builds the text).

## 3. State

- **Git:** `merge/generate-advanced` is committed and pushed (working tree clean at the start of the wrap-up); 12 commits ahead of `main`, which is its ancestor, so `main` can fast-forward. Run `git status` and `git log --oneline -8` first.
- **This checkout (`D:\Vscode\mirsal-builder-io`) is a fresh clone.** It has no `mirsal/out/` (so none of the 92 generations, the library, jobs or the ledger), no `Phase_01/Images_gen|videos_gen` sample media, no `mirsal/.env` (no OpenAI key), and no `mirsal-db` container. Haitham's real data and database live on their original PC. Its `mirsal/.venv` was created on 2026-10-01 with **Python 3.14, numpy 2.5.3, OpenCV 5.0.0.93, Pillow 12.3.0, psycopg 3.3.6**; the thresholds in `engine/config.py` and the crf ladder were calibrated on an older stack, so run `python -m mirsal doctor` and the tests before judging any metric here.
- **Tests:** 166 in total. **152 run without a database and pass here (117 s, 2 skipped classes).** The other 14 (`test_store` 10, `test_pool` 4) need `mirsal-db` (`python -m mirsal db up`: pulls the pgvector image and creates the container) and skip without it. `mirsal doctor`: verifier v2, 44 checks over 9 stages, plus Postgres (mirsal-db:5434) and the trace backend.
- **Database (original PC):** local `mirsal-db` on 5434 holds 92/92 generations (live write-through on; `db import` idempotent). Never touch 5433 (`reglens`/temporal_note) or 5436.
- **Servers:** Haitham's server on :8770 runs in their terminal; the Studio shows a banner when the running server is older than the files on disk. Never kill it yourself; start your own on another port with a copy of data (section 4).
- **Verified live by Haitham:** Telegram (images and video packs arrive, one click, the app opens). **Verified by the previous builder in a browser on a staged copy of one generation (G078):** the issue colours and hatching, Include anyway, Edge, the sticker detail, the Size slider, a re-animate with the new quality settings. **Verified once live by the unattended session:** the OpenAI path (`prompt "falcon dancing" --ai`: 9 distinct concepts, lint PASS, ledgered). **Not verified:** the colours on Haitham's real batches, the "generate it" button in a browser, and everything about Higgsfield.
- **Animation quality, as measured (two cells of G078 only; re-measure on more):** source cells are ~320 px upscaled 1.28x; bicubic gives +6% edge detail over linear; the VP9 encode keeps 1.00-1.03x of the edge detail; the crf ladder is `(30,34,38,42,46,50,54,58,62)` and lands on 34-46. The dark key line is in the source art; the Edge dialog's trim removes it. The remaining softness is source resolution, which Phase 2's normalised video sheet is meant to improve.

## 4. Run, test, layout

```
cd D:\Vscode\mirsal-builder-io\mirsal
.venv\Scripts\python -m mirsal doctor                       # verifier, ffmpeg+VP9, AI key (on/off only), TLS, workers, Telegram, Postgres
.venv\Scripts\python -m unittest discover -s tests -t .     # 166 tests (152 without the database), ~2 min
.venv\Scripts\python -m mirsal serve --port 8789            # YOUR server; MIRSAL_OUT=<a copy of one out\G### folder> keeps real data untouched
.venv\Scripts\python -m mirsal profile G078 --sweep 1,6,9   # where animation time goes
.venv\Scripts\python -m mirsal recheck [G001|all]           # border check for animations made before it existed
```

Always use `mirsal/.venv` (the Anaconda base env has a broken numpy). Stdlib first, minimal wheels (rule 8). There are **no JS tests**: verify UI changes in a browser (Playwright MCP works; screenshots go to the temp dir or the repo root and are deleted; `.playwright-mcp/` and `/shot-*.png` are gitignored).

| Where | What |
|---|---|
| `README.md` | the index only |
| `Phase_01/README.md` | the architecture as built (engine, verifier, gates, Studio, edit, Telegram, perf, verified, decisions) |
| `Phase_02/README.md`, `Phase_03/README.md` | what those phases built so far (prompt lab, jobs, slot reviewer; Postgres store, pool, photo core) |
| `Phase_01/CLAUDE.md` | Phase 1 leftovers and the input/naming rules; `Phase_0N/CLAUDE.md` = each phase's inputs from Haitham and its review gates |
| `phase_02.md` … `phase_05.md` | the plans (02 holds the live steps S0, S3, S4, S6, S7; 03 holds 3B vectors, 3C judgement, 3D, 3E) |
| `REVIEW_PROMPT.md`, `report.md` | the prompt for an independent LLM review and its result (65 KB). Triaged 2026-10-01, see section 5. |
| `mirsal/mirsal/engine/` | the pure engine: `verify.py` (44 checks), `video.py` (`AnimCache`, `_encode_fit`, `_Polite`), `render.py`, `video_sheet.py`, `ffmpeg.py`, `config.py` (thresholds live here only) |
| `mirsal/mirsal/` | `pipeline.py` (lifecycle, `record_anim`, `recheck_bounds`, `studio_edit_*`, `set_appearance`), `gates.py`, `library.py`, `telegram.py`, `tasks.py`, `jobs.py`, `model_calls.py`, `prompter.py`, `expander.py` + `llm.py`, `pool.py`, `matte.py`, `video_project.py`, `watch.py`, `cli.py` |
| `mirsal/mirsal/console/` | `server.py` (stdlib, 127.0.0.1) and the sandbox UI: `generate.js` (the Studio), `prepare.js`, `editor.js`, `packs.js`, `app.js`, `telegram.js`, `studio.css` |
| `mirsal/out/` | gitignored runtime data: `G00N/` (`result.json`, `source/orig/`), `library/`, `cache/anim/`, `tasks/`, `jobs/`, `photo/`, `model_calls.jsonl`, `telegram.json` (token: never commit) |

## 5. Safe backlog (non-destructive; good work between Phase 2 steps)

Triage of the independent review (`report.md`), checked against the code on 2026-10-01. Each item is small, testable and does not change what the user sees:
1. **Not reproduced, no action:** report F-A2 (`numpy.core` import crash in `matte.py`: no code imports `numpy.core`; it came from the reviewer's broken Anaconda env) and F-A3 (`test_video_project` orphan project: the test passes).
2. `engine/video.py:293 _CRF_HINT` is a module-level global mutated by the parallel workers and by `library.encode_frames`. It only moves where the crf search starts, so results stay correct; make it per-call or lock it, and note that VP9 size is not strictly monotonic in crf.
3. The `sharpness` check (`engine/verify.py:514`, `edge_energy` decoded / encoder-input ratio) reads 1.00-1.05, i.e. it cannot see softening. **Haitham decides: replace it** (gradient correlation or SSIM on the first frames, alpha-edge ramp width, calibrated on more than two cells) **or drop it** (the reviewer's suggestion: the crf ladder already controls quality).
4. `console/server.py` binds 127.0.0.1 but has no Origin/Host check, so a web page the owner visits can POST to it (trash/restore, the Telegram config, bulk delete). Add an allow-list (no UI change) with a test.
5. `result.json` is read-modify-write under an in-process lock; a second process (`python -m mirsal recheck` while the server runs) can race it. Add a lock file or route the CLI through the server.
6. A server-side job queue (today a second request while one runs gets 409 and the client waits quietly); pairs with the S2 jobs. JS has no tests: a tiny Playwright smoke test against a throwaway `out/` (the staged-G078 method) would pin the issue colours and Include anyway.
7. Security hygiene: an old Telegram bot token is in git history (commit `349762b`, already on GitHub). Haitham must revoke it in @BotFather; offer a history scrub with a force-push but **never do it unasked**. No live secret is in the tracked files (scanned 2026-10-01; the only token-shaped string is the fake in `tests/fake_telegram.py`).
8. Open questions from `report.md` §9 for Haitham (recommended defaults in the report): a daily credit cap for Phase 2 (`MIRSAL_DAILY_CREDITS`), a backup command for `out/`, Arabic prompt handling, moderation (Phase 5C), Redis necessity (Phase 4).

## 6. Facts and quirks that cost time before

- **Most "it still fails" reports were a stale server process** (Python loads code once; the page is read from disk on each load). Compare the process start time with the file times before debugging.
- VP9 (`row-mt`) output is not byte-stable between runs; compare metrics and checks, never WebM hashes.
- Windows `os.replace` fails with WinError 5 when a file is open: `pipeline._atomic_write` locks and retries; keep using it.
- Tool quirks in this environment: a Bash heredoc breaks on some quote mixes (write a patch script with the Write tool and run it); PowerShell has no `&&` and mangles non-ASCII when it rewrites files (use Python for edits); the Write/Edit tools fail if the file changed since your last Read; do not stop a process by a command-line pattern that also matches your own shell; a Playwright click that closes a dialog may report "no match" though it worked; a browser tab cached a page once — hard reload.
- Pasted tokens: any bot token Haitham pastes into a chat is compromised and must be revoked after testing. `mirsal/.env` (`OPENAI_API_KEY`) and `out/telegram.json` are gitignored.

## 7. Prompt to give the next LLM

> Read `HANDOFF.md`, `CLAUDE.md`, `Phase_01/README.md`, `Phase_02/README.md`, `Phase_03/README.md` and `phase_02.md`. Built and committed: Phase 1; Phase 2 offline (S1 prompt lab, S2 file jobs, slot reviewer); Phase 3A (Postgres), 3B lexical pool, 3C offline photo core. 166 tests (152 need no database). Do not redo any of that. Work in this order: (a) if Haitham has reviewed the open gates (HANDOFF section 0), apply their verdicts to `phase_02.md` / `phase_03.md` and delete only the plan items they approved; (b) **S0** in a session where the Higgsfield MCP tools exist (check `/mcp`; if absent, stop and tell Haitham, never simulate), then S3 and S4 adapted to what `Phase_02/higgsfield_mcp.md` says; (c) backlog items 2-4 of HANDOFF section 5, each with a failing-then-passing test (item 3 only after Haitham chooses replace or drop). Judge media only with Python, never by opening it. Do not rework, restyle or revert the UI/UX or the engine; only add to the Studio in its existing style, each control wired to a working backend. Do not start 3B vectors, 3D, 3E or Phase 4, push or merge to `main`, rewrite history, or commit a token, `.env` or `opencode.json`. Use `mirsal/.venv` for everything. Update the docs in the same step as every major change (rule 12) and keep this file current.
