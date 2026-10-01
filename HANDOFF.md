# HANDOFF: Mirsal Builder (final rewrite, 2026-10-01; the previous builder has no session left)

Owner: **Haitham** (they/them; never guess pronouns). Repo `G:\Haitham\VsCode\Mirsal-Builder`, GitHub `haitham72/mirsal-builder-io` (PRIVATE), Windows PC (macOS also supported). Branch **`merge/generate-advanced`**, committed and pushed; `main` is 5+ commits behind and can fast-forward (Haitham decides when).

Read in this order: this file → `CLAUDE.md` (12 binding rules) → `Phase_01/README.md` (the architecture as built) → `phase_02.md` (your phase). `Phase_01/CLAUDE.md` is the Phase 1 leftover list.

## 0. In one minute

- **Phase 1 is about 97% built, tested (142 tests green) and committed.** It turns prepared sheets/videos into verified stickers and animations, has the review gates, the Studio UI, layered editing, packs and one-click Telegram. Haitham confirmed Telegram works. What is left is only their own checks on real data.
- **Phase 2 (live generation through Higgsfield) is about 15% and is now YOURS to take over, with freedom to experiment.** Haitham authorised the Higgsfield connector in their own terminal. The previous builder's session could not see it, so nothing about Higgsfield's tools is verified yet. You are the first to touch it.
- **Phase 3 (Postgres) is NOT started and must not be started without Haitham's explicit confirmation.** Phases 4-5 are plans only.
- **Do not rework or revert the UI/UX or the engine. Build on it.** Section 2 says exactly what is safe.

## 1. Your mission: take over Phase 2 (`phase_02.md`, "Ready to go" has steps S0-S7)

You own this phase end to end: experiment with Higgsfield as much as you like, learn what it really offers, build the jobs/operator loop, generate real sheets and videos, measure, and tune. The previous plan was written blind; **where reality disagrees with `phase_02.md`, change the plan** (rule 7: enhance it with findings, do not shrink it) and say why in the doc.

**Step S0 first, and only in a session where the Higgsfield tools exist.** In Claude Code run `/mcp` (or search the tool list for "higgsfield"). If the tools are not there, stop and tell Haitham; do not simulate them, do not fake outputs. Then: list every tool, model, parameter, limit and the credit cost of each call; make one test image and one test video; write `Phase_02/higgsfield_mcp.md` (is a job id returned, is the call synchronous or polled, can it take a first and last frame or loop, output size/format/duration, resolution, cost per call, rate limits). That doc decides how S2-S4 are built, so write it from what you saw, not from what the plan guessed.

Then S1-S7 in the order of `phase_02.md`, adapting it to what S0 found. The seam to keep: **jobs as files** (`out/jobs/J###.json`, claim/ticket stored *before* waiting, done/fail) so that a plain HTTP provider can replace the MCP operator later behind the same interface (an MCP connector is a tool of an interactive session, not an API the server can call; production in Phase 5 will need a real HTTP provider, so keep the engine ignorant of who fulfils the job).

**How to work, so that the owner can follow and nothing is lost:**
- **Freedom:** call Higgsfield as much as you need to learn (prompts, models, sheet vs single, loop options, resolutions, seeds). Haitham said so explicitly. Keep a ledger: append every paid or model call to `mirsal/out/model_calls.jsonl` (what, parameters, latency, credits if shown, output path). If the tool shows a credit balance and a single experiment or a day's total would burn a large share of what is left, pause and tell Haitham.
- **Never open or judge generated media yourself.** Judge with Python: `ffprobe`, `python -m mirsal doctor`, the verifier (`engine/verify.py`), the new `measure-cells`-style metrics you add, file sizes. Haitham looks at the pictures. Put test outputs under `mirsal/out/` (gitignored), never inside `Phase_01/Images_gen|videos_gen`.
- **Gates:** the plan says "stop at each gate for Haitham". Do not block on that. Finish the step, record the evidence (files, numbers, the doc), mark it "awaiting Haitham's review" in `phase_02.md`, and move on to the next step that does not depend on their decision.
- **Raw samples are not input to the video model.** The video is made from the **normalised video sheet** (`engine/video_sheet.py: build_video_sheet`, `slot_fill` = 0.55, one scale, margins). Measured on the owner's pre-rendered samples: 3 of 9 teddy and 8 of 9 emoji animations leave their cell. Phase 2's job is to make that near zero; `slot_fill` is the dial; the fallback is one sticker per video.
- **Docs in the same step** (rule 12): `Phase_02/higgsfield_mcp.md`, `docs/operator.md`, `docs/phase2_measurements.md` as the plan names them, the architecture of whatever you build in a new `Phase_02/README.md` (that is the repo convention: each built phase's README is its architecture), this file, and `phase_02.md` ticks. Check each change against `phase_03.md` and `Phase_03/CLAUDE.md` (Phase 3 imports what you write: keep `out/jobs/*.json`, `out/model_calls.jsonl` and the task tickets in the shapes `phase_03.md` expects, or update `phase_03.md`).

**Already built for you (do not rebuild):** template-locked prompts (`prompter.py`, `mirsal/prompts/templates/`), the AI subject expander (`expander.py`, `llm.py`; S5 is partly done). **Important drift:** `llm.py` was switched from Anthropic to OpenAI (default `gpt-4.1-mini`, key var `OPENAI_API_KEY`) but `expander.py:69`, `tests/test_expander.py`, and the doctor output still reference `ANTHROPIC_API_KEY` — the AI expansion path is currently broken. Fix all four before declaring Phase 1 complete. Tickets (`tasks.py`, `POST /api/plan`, `/api/tasks`, `/api/generations {task}`), the video upload endpoint `POST /api/generations/<id>/video_sheet/<A>/video`, the video-sheet builder and layout slicer, `inside_slot` / `inside_frame` / `cross_slot`, `recheck`, `profile`, the animation cache, and Send to Telegram. **Not built:** `jobs.py` and `/api/jobs`, `mirsal prompt`, `measure-cells`, the operator doc and loop, the vision judge, the slot reviewer.

## 2. Guardrails: what is safe and what is not

| | |
|---|---|
| **Do freely** | Everything in Phase 2: new modules (`jobs.py`, operator tooling, vision judge), new CLI commands, new endpoints, new tests, new docs, Higgsfield experiments, prompt template **versions** (add `_v2`, never edit `_v1` in place), measurements. Fix real bugs you find, each with a test that fails before and passes after. Add checks to the verifier only with a PASS and a FAIL fixture and a measured threshold. |
| **Additive only** | The Studio UI (`mirsal/mirsal/console/*`). Phase 2 needs a small number of new controls (for example S2's "No prepared sheet: generate it" entry and a "waiting for the generator" state). Add them **in the existing style** (same components, same colour system, same wizard) and wire each to a working backend (rule 6: no dead stubs). Do not restyle, rearrange, rename or remove anything that exists. |
| **Do NOT** | Rework or redesign the UI/UX (the five header views, the Pack wizard, the issue-colour system and the hatching on both sheets, Include anyway, Edge, the sticker detail, the Library box selection, one-click Telegram). Revert or "simplify" any of the previous work. Rename the watch folders or outputs (rule 9). Change the golden path, the meaning of the gates, or "a human approves, Python's blocks are final" (rule 10). Loosen a verifier BLOCK. Rewrite git history or force-push. Push or merge to `main`. Start Phase 3. Commit a token, `.env`, `opencode.json`, or `Phase_01/telegram.md`. Open sticker media to judge it. Write inside `Phase_01/Images_gen|videos_gen`. Use `git add -A` blind. |
| **Ask Haitham first** | Anything that changes what the user sees or how they decide; any change to verifier severities or thresholds that were measured; deleting plan items (only Haitham's approval of a gate deletes them); merging `merge/generate-advanced` into `main`; scrubbing the token from git history. |

**Locked decisions (Haitham; do not reopen):** phase order (1 engine, 2 live generation, 3 Postgres, 4 Redis+LangGraph, 5 API); the product is an **API / app** and this UI is a sandbox (rule 11), so every feature is an engine function plus a stable JSON contract first; the Studio's five views; the issue-colour semantics (orange out of bounds, purple bad green screen, yellow bad loop, pink look or motion, blue file/Telegram limit, red dropped or blocked; hatched = not in the set, dashed = kept with a check); out-of-bounds animations are off by default and a human may **Include anyway** (`gates.soft_block`: only when every failed check is WARN; a real BLOCK stays final); file store (`result.json`) until Phase 3; template-locked prompts (the model fills a small JSON, code lints it, the saved template builds the text).

## 3. State

- **Git:** `merge/generate-advanced` is pushed. Four commits on top of `bf85e47` (engine + app layer, Studio UI, tests, docs) plus this handoff. A pull request can be opened at `https://github.com/haitham72/mirsal-builder-io/pull/new/merge/generate-advanced`. Run `git status` and `git log --oneline -8` first.
- **Tests:** `142 tests, ~2 minutes, OK` (all green with `mirsal/.venv/Scripts/python`; running with Anaconda python gives false failures from a numpy-core import crash in `matte.py`). `mirsal doctor`: verifier v2, 44 checks over 9 stages.
- **Haitham's server on :8770** was started before the final changes unless they restarted it; the Studio shows a banner when the running server is older than the files on disk. Never kill it yourself (it runs in their terminal); start your own on another port, with a copy of data (section 4).
- **Verified live by Haitham:** Telegram (images and video packs arrive, one click, the app opens). **Verified by the previous builder in a browser on a staged copy of one generation (G078):** the issue colours and hatching, Include anyway, Edge, the sticker detail, the Size slider, a re-animate with the new quality settings. **Not verified:** the real Anthropic call (no key was available; fake-model tests only), the colours on Haitham's real batches, and everything about Higgsfield.
- **Animation quality, as measured (two cells of G078 only; re-measure on more):** source cells are ~320 px upscaled 1.28x; bicubic gives +6% edge detail over linear; the VP9 encode keeps 1.00-1.03x of the edge detail, so the encoder does not soften the picture; the crf ladder is `(30,34,38,42,46,50,54,58,62)` and now lands on 34-46 instead of all 46. The dark key line is in the source art; the Edge dialog's trim removes it. The remaining softness is source resolution, which is what Phase 2's normalised video sheet is meant to improve.

## 4. Run, test, layout

```
cd G:\Haitham\VsCode\Mirsal-Builder\mirsal
.venv\Scripts\python -m mirsal doctor                       # verifier, ffmpeg+VP9, AI key (on/off only), TLS, workers, Telegram
.venv\Scripts\python -m unittest discover -s tests -t .     # 142 tests, ~2 min
.venv\Scripts\python -m mirsal serve --port 8789            # YOUR server; MIRSAL_OUT=<a copy of one out\G### folder> keeps real data untouched
.venv\Scripts\python -m mirsal profile G078 --sweep 1,6,9   # where animation time goes
.venv\Scripts\python -m mirsal recheck [G001|all]           # border check for animations made before it existed
```

Always use `mirsal/.venv` (the Anaconda base env has a broken numpy). Stdlib first, minimal wheels (rule 8). There are **no JS tests**: verify UI changes in a browser (Playwright MCP works; screenshots go to the temp dir or the repo root and are deleted; `.playwright-mcp/` and `/shot-*.png` are gitignored).

| Where | What |
|---|---|
| `README.md` | the index only |
| `Phase_01/README.md` | the architecture as built (engine, verifier, gates, Studio, edit, Telegram, perf, verified, decisions) |
| `Phase_01/CLAUDE.md` | Phase 1 leftovers and the input/naming rules; `Phase_0N/CLAUDE.md` = each phase's inputs from Haitham and its review gates |
| `phase_02.md` … `phase_05.md` | the plans (02 is yours; 03 waits) |
| `REVIEW_PROMPT.md` | a prompt Haitham gives to another LLM for an independent review; it writes `report.md`. A review HAS been run and `report.md` is in the repo root (65 KB, 560 lines). **Triage it, do not apply blindly:** fix evidenced bugs with tests, take plan advice into `phase_0N.md` as findings, and bring anything that touches the UI, the gates or the locked decisions to Haitham. Top-priority items from the review: the bot token in git history (`349762b`, must be revoked at @BotFather), the invalid `sharpness` metric in the verifier, the `_CRF_HINT` global-race, and the Anthropic→OpenAI drift in `llm.py`. |
| `mirsal/mirsal/engine/` | the pure engine: `verify.py` (44 checks), `video.py` (`AnimCache`, `_encode_fit`, `_Polite`), `render.py`, `video_sheet.py`, `ffmpeg.py`, `config.py` (thresholds live here only) |
| `mirsal/mirsal/` | `pipeline.py` (lifecycle, `record_anim`, `recheck_bounds`, `studio_edit_*`, `set_appearance`), `gates.py`, `library.py`, `telegram.py`, `tasks.py`, `prompter.py`, `expander.py` + `llm.py`, `video_project.py`, `watch.py`, `cli.py` |
| `mirsal/mirsal/console/` | `server.py` (stdlib, 127.0.0.1) and the sandbox UI: `generate.js` (the Studio), `prepare.js`, `editor.js`, `packs.js`, `app.js`, `telegram.js`, `studio.css` |
| `mirsal/out/` | gitignored runtime data: `G00N/` (`result.json`, `source/orig/`), `library/`, `cache/anim/`, `tasks/`, `telegram.json` (token: never commit) |

## 5. Safe backlog (non-destructive; good work between Phase 2 steps)

These come from the previous builder's own doubts and the independent review (`report.md`). Each is small, testable and does not change what the user sees:
1. **Anthropic→OpenAI drift in `llm.py`** (S2, do first): `llm.py` now uses OpenAI (`OPENAI_API_KEY`, default `gpt-4.1-mini`) but `expander.py:69`, `tests/test_expander.py`, and the doctor output still reference `ANTHROPIC_API_KEY`. Fix all four and run `python -m unittest tests.test_expander -v` — this unblocks AI expansion entirely.
2. `engine/video.py: _CRF_HINT` is a module-level global mutated by the parallel workers and now by `library.encode_frames`. It only moves where the crf search starts, so results stay correct, but make it per-call or lock it, and note that VP9 size is not strictly monotonic in crf (the walk can stop at a local result).
3. The `sharpness` check (`edge_energy`, decoded / encoder-input gradient ratio) reads 1.00-1.05, i.e. it cannot see softening (compression blocking raises the ratio). Replace or complement it with a better measure (gradient correlation or SSIM on the first frames, alpha-edge ramp width), calibrated on more than two cells.
4. `console/server.py` binds 127.0.0.1 but has no Origin/Host check, so a web page the owner visits can POST to it. Add an Origin/Host allow-list (no UI change) with a test.
5. `result.json` is read-modify-write under an in-process lock; a second process (`python -m mirsal recheck` while the server runs) can race it. Consider a lock file or route the CLI through the server.
6. A server-side job queue (today a second request while one runs gets 409 and the client waits quietly). This pairs naturally with S2's jobs.
7. JS has no tests. A tiny Playwright smoke test against a throwaway out/ (the previous builder's staged-G078 method) would pin the issue colours and Include anyway.
8. Security hygiene: an old Telegram token is in git history (commit `349762b`, already on GitHub). Haitham must revoke it in @BotFather; offer a history scrub with a force-push but **never do it unasked**.

## 6. Facts and quirks that cost time before

- **Most "it still fails" reports were a stale server process** (Python loads code once; the page is read from disk on each load). Compare the process start time with the file times before debugging.
- VP9 (`row-mt`) output is not byte-stable between runs; compare metrics and checks, never WebM hashes.
- Windows `os.replace` fails with WinError 5 when a file is open: `pipeline._atomic_write` locks and retries; keep using it.
- Tool quirks in this environment: a Bash heredoc breaks on some quote mixes (write a patch script with the Write tool and run it); PowerShell has no `&&` and mangles non-ASCII when it rewrites files (use Python for edits); the Write/Edit tools fail if the file changed since your last Read; do not stop a process by a command-line pattern that also matches your own shell; a Playwright click that closes a dialog may report "no match" though it worked; a browser tab cached a page once — hard reload.
- Pasted tokens: any bot token Haitham pastes into a chat is compromised and must be revoked after testing. `mirsal/.env` (now `OPENAI_API_KEY`, previously `ANTHROPIC_API_KEY`) and `out/telegram.json` are gitignored. An old bot token is in git history (commit `349762b`): Haitham must revoke it in @BotFather; offer a history scrub with a force-push but never do it unasked.

## 7. Prompt to give the next LLM

> Read `HANDOFF.md`, `CLAUDE.md`, `Phase_01/README.md` and `phase_02.md`. First triage `report.md` (the independent review is already done): fix the critical bugs with tests (token revoke is Haitham's call), take plan advice into the phase docs. Then fix the Anthropic→OpenAI drift: `llm.py` now targets OpenAI (`OPENAI_API_KEY`, model `gpt-4.1-mini` by default) but `expander.py:69`, `tests/test_expander.py` and the doctor output still say `ANTHROPIC_API_KEY` — update all four and run `python -m unittest tests.test_expander -v` to confirm. Use `mirsal/.venv/Scripts/python` for everything (Anaconda python has a broken numpy that crashes `matte.py`). You own Phase 2 (live generation through Higgsfield): start with step S0 in a Claude Code session where the Higgsfield connector is authorised (if its tools are not visible, tell Haitham and stop; never fake them), write `Phase_02/higgsfield_mcp.md` from what you actually see, then build S1-S7, adapting the plan to what the tools really do and recording every call in `out/model_calls.jsonl`. Experiment freely with Higgsfield. Judge media only with Python, never by opening it. Do not rework, restyle or revert the UI/UX or the engine; only add to the Studio in its existing style, each control wired to a working backend. Do not start Phase 3 (Postgres), push to `main`, rewrite history, or commit a token, `.env` or `opencode.json`. Update the docs in the same step as every major change (rule 12) and keep this file current.
