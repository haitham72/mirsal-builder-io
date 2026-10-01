# HANDOFF: Mirsal Builder (tracker: open items only)

This file is a **tracker, not a log**: an entry is deleted the moment it is implemented (the architecture goes into the phase README, the history is in git). If you finish something here, delete its line in the same step (`CLAUDE.md` rules 7 and 12).

Owner: **Haitham** (they/them; never guess pronouns). GitHub `haitham72/mirsal-builder-io` (PRIVATE). Work branch **`merge/generate-advanced`**. Windows PC (macOS also supported).

Read in this order: this file → `CLAUDE.md` (12 binding rules) → `Phase_01/README.md` (engine, verifier, gates, Studio) → `Phase_02/README.md`, `Phase_03/README.md` (what those phases built) → `phase_02.md` (the live steps still open). What is built is described in those READMEs, not here.

## 1. Gates waiting for Haitham

Built unattended on their standing order; each needs their verdict. On approval the line is deleted here and the matching plan items are deleted from `phase_0N.md`.

| Gate | What to check | How |
|---|---|---|
| **S1 prompt text** | The prompts match your golden prompts in English, Arabic and Arabizi. | `python -m mirsal prompt "<request>"`, `prompt lab` (20 inputs), `prompt "<request>" --ai`; compare with `Phase_02/prompt_samples.md`. |
| **S0/S3 first live results** | The sheets are what you expect: G001 (angel reading a newspaper), G002 (batman lego), the S0 tests. | `mirsal/out/G001`, `G002`, `mirsal/out/s0/` (`compare_kling.html` plays std next to pro); numbers in `Phase_02/higgsfield.md`. |
| **Generate menu and the edge** | The menu (references, stroke, styles, model, AI enhancer, Loop, instant Generate), the credits pill with history at the top, the live Stroke/Trim sliders, the Gap slider with its preview and the Earlier batches list feel right; style and logo images are placeholders until you drop yours into `mirsal/mirsal/console/assets/{styles,vendors}/`. G002's stale animations were restored from its stored video (backup: `mirsal/out/G002/result.json.bak-before-reslice`). | Restart `python -m mirsal serve`, hard-reload the page. |
| **S2 jobs** | The "generate it" button works in the browser; a job shows up and completes. | Studio -> Higgsfield dialog -> "No prepared sheet: generate it"; `python -m mirsal jobs`; `mirsal/docs/operator.md` for the operator loop. |
| **S5 AI lab** | The AI-filled concepts are good. | `prompt lab --ai` (20 prompts), rate them. |
| **3A Postgres** | History and search survive a restart on your real data. | `python -m mirsal db up`, `db import`, `list`, `show G078`, `search "teddy book"`, then `docker restart mirsal-db` and `show` again. Needs the real `out/` (original PC). |
| **3B pool** | Search returns the right stickers and nothing for what does not exist. | `python -m mirsal pool search "teddy waving"` and `"falcon dancing"` (must be empty). Precision needs your `Phase_03/search_queries.md` (not written yet). |
| **3C photo** | The cutout edges are clean on real photos. | `python -m mirsal photo <file>` on 10+ photos in `Phase_03/photos/` (gitignored, not provided yet, include a few iPhone Portrait HEIC). |
| **Phase 1** | One animated pack from a real run; the server restarted on the new code. | Finish list in `Phase_01/CLAUDE.md` (items 3 and 6). |

## 2. Next work

1. **S4 measurement, then S6, S7.** S0 and S3 are built and ran for real (G001, G002); the Kling path is built. Left: re-run G002 with `pro` and the new gap (the first clip, J004, was `std` and pixelated), write `measure-cells` and record the flagged share, then choose the default gap or 2x2 / one sticker per video. Never simulate a call; Kling is always `pro`, never `4k`; a test can never reach the real CLI (`MIRSAL_NO_REAL_CLI`).
2. **Backlog** (each small, with a failing-then-passing test, no visible change):
   - `engine/video.py:293 _CRF_HINT` is a module-level global mutated by parallel workers: make it per-call or lock it (VP9 size is not strictly monotonic in crf).
   - `console/server.py` has no Origin/Host allow-list: a web page the owner visits can POST to it (trash/restore, the Telegram config, bulk delete).
   - `result.json` is read-modify-write under an in-process lock only: a second process (`mirsal recheck` while the server runs) can race it.
   - `sharpness` (`engine/verify.py:514`) is **kept** (Haitham) but its metric cannot see softening (reads 1.00-1.05): improve it (gradient correlation or SSIM on the first frames, alpha-edge ramp width), calibrated on more than two cells.
   - A server-side job queue (a second request while one runs gets 409); a Playwright smoke test for the issue colours and Include anyway (JS has no tests).
3. **Questions for Haitham** (`report.md` §9, recommended defaults there): a daily credit cap for Phase 2 (`MIRSAL_DAILY_CREDITS`), a backup command for `out/`, Arabic prompt handling, moderation (Phase 5C), Redis necessity (Phase 4).
4. **Security:** an old Telegram bot token is in git history (commit `349762b`). Haitham must revoke it in @BotFather; offer a history scrub with a force-push but **never do it unasked**.

Waiting for Haitham's go: 3B vectors and its eval set, 3C real-photo judgement, 3D, 3E, Phases 4-5.

The seam to keep: **jobs as files** (`out/jobs/J###.json`, ticket stored *before* waiting) so a plain HTTP provider can replace the MCP operator later; the engine stays ignorant of who fulfils a job.

**While doing the live steps:** append every paid or model call to `out/model_calls.jsonl`; if a day's total would burn a large share of the credits left, pause and tell Haitham. Never open or judge media yourself (ffprobe, `doctor`, the verifier, metrics, file sizes; test outputs under `mirsal/out/`, never inside `Phase_01/Images_gen|videos_gen`). Do not block on a gate: finish the step, record the evidence, move on. The video is made from the **normalised video sheet** (`build_video_sheet`, `slot_fill` = 0.74 (the user slides it per batch)), never from raw samples; on the old samples 3 of 9 teddy and 8 of 9 emoji animations left their cell, S4 must bring that near zero. Check each change against `phase_03.md` (Phase 3 imports `out/jobs/*.json`, `out/model_calls.jsonl` and the task tickets).

## 3. Guardrails

| | |
|---|---|
| **Do freely** | Everything in Phase 2: new modules, CLI commands, endpoints, tests, docs, Higgsfield experiments, prompt template **versions** (add `_v2`, never edit `_v1`), measurements. Fix real bugs, each with a test that fails before and passes after. Add verifier checks only with a PASS and a FAIL fixture and a measured threshold. |
| **Additive only** | The Studio UI (`mirsal/mirsal/console/*`): existing style, each control wired to a working backend (rule 6). |
| **Do NOT** | Rework or restyle the UI/UX (five header views, Pack wizard, issue colours and hatching, Include anyway, Edge, sticker detail, Library selection, one-click Telegram) or revert previous work. Rename watch folders or outputs (rule 9). Change the golden path, the gates' meaning, or "a human approves, Python's blocks are final" (rule 10). Loosen a verifier BLOCK. Rewrite history or force-push. Start Phase 4. Commit a token, `.env`, `opencode.json`, `Phase_01/telegram.md`. Open sticker media to judge it. Write inside `Phase_01/Images_gen|videos_gen`. `git add -A` blind. |
| **Ask Haitham first** | Anything that changes what the user sees or decides; verifier severities or measured thresholds; deleting a plan item for a gate that is still unanswered; scrubbing the token; starting 3B vectors, 3D or 3E. |

**Locked decisions (do not reopen):** phase order (1 engine, 2 live generation, 3 Postgres, 4 Redis+LangGraph, 5 API); the product is an API / app and this UI is a sandbox (rule 11): engine function + JSON contract first; the five Studio views; issue colours (orange out of bounds, purple bad green screen, yellow bad loop, pink look or motion, blue file/Telegram limit, red dropped or blocked; hatched = not in the set, dashed = kept with a check); out-of-bounds animations off by default with *Include anyway* (`gates.soft_block`: only when every failed check is WARN); template-locked prompts (the model fills a small JSON, code lints it, the template builds the text).

## 4. This checkout and how to run

`D:\Vscode\mirsal-builder-io` is a fresh clone: no `mirsal/out/` (no generations, library, jobs or ledger), no `Phase_01/Images_gen|videos_gen` sample media (`doctor` reports "MISSING input" for that, expected). Its `mirsal/.venv` is Python 3.14, numpy 2.5, OpenCV 5.0, Pillow 12.3: thresholds in `engine/config.py` were calibrated on an older stack, so re-check metrics here before trusting them. Haitham's real data and database are on their original PC.

`mirsal/.env` here was copied from another project: it holds `PGHOST/PGPORT/PGDATABASE` (reglens, 5432), `REDIS_URL` and a LangSmith key with project "NeoHealth". Mirsal ignores `PG*` (it uses `MIRSAL_DATABASE_URL`, default `localhost:5434/mirsal`) and tracing is off unless `MIRSAL_TRACE=langsmith`. **Remove the `PG*`, `REDIS_URL` and `LANGSMITH_*` lines**, or set `MIRSAL_TRACE` only after giving Mirsal its own LangSmith project (`mirsal/.env.example`).

```
cd D:\Vscode\mirsal-builder-io\mirsal
.venv\Scripts\python -m mirsal db up                        # Postgres on 5434 (needed by 14 tests and by search)
.venv\Scripts\python -m mirsal doctor                       # health check
.venv\Scripts\python -m unittest discover -s tests -t .     # 167 tests, ~2 min (14 skip without the database)
.venv\Scripts\python -m mirsal serve --port 8789            # YOUR server; MIRSAL_OUT=<copy of one out\G### folder> keeps real data untouched
```

Always use `mirsal/.venv` (the Anaconda base env has a broken numpy). Never touch ports 5433 (`reglens`/temporal_note) or 5436. Never kill Haitham's server on :8770; the Studio shows a banner when it runs older code than the files on disk. Where things live: `README.md` (index), `Phase_0N/README.md` (architecture), `Phase_0N/CLAUDE.md` (inputs and gates), `phase_0N.md` (plans), `report.md` (independent review, triaged).

## 5. Quirks that cost time before

- **Most "it still fails" reports were a stale server process** (Python loads code once). Compare process start time with file times first.
- VP9 (`row-mt`) output is not byte-stable; compare metrics, never WebM hashes.
- Windows `os.replace` fails with WinError 5 on an open file: keep using `pipeline._atomic_write`.
- Tool quirks: a Bash heredoc breaks on some quote mixes (write a patch script with the Write tool); PowerShell has no `&&` and mangles non-ASCII when it rewrites files (use Python); Write/Edit fail if the file changed since your last Read; a Playwright click that closes a dialog may report "no match" though it worked; hard-reload a cached tab. JS has no tests: verify UI in a browser (Playwright MCP works; screenshots are gitignored).
- Any bot token pasted into a chat is compromised and must be revoked after testing. `mirsal/.env` and `out/telegram.json` are gitignored.

## 6. Prompt for the next LLM

> Read `HANDOFF.md`, `CLAUDE.md`, `Phase_01/README.md`, `Phase_02/README.md`, `Phase_03/README.md`, `phase_02.md`. Work the open items in `HANDOFF.md` §1 and §2 in order: apply Haitham's gate verdicts (delete approved items from the plans and from this file); S0 only in a session where the Higgsfield MCP tools exist (never simulate); then the backlog with tests. Judge media only with Python. Do not rework or restyle the UI/UX or engine, start 3B vectors/3D/3E/Phase 4, rewrite history, or commit a token, `.env` or `opencode.json`. Use `mirsal/.venv`. **HANDOFF and the plans are trackers: delete an entry the moment it is implemented and documented in the phase README.**
