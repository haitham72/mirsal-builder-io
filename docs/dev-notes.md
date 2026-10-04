# Dev notes: glossary, guardrails, how to run this checkout, quirks

What a session needs that is neither architecture (the other files of `docs/`) nor a tracker (`waiting-for-haitham.md`, `backlog.md`). Owner: **Haitham** (they/them; never guess pronouns). GitHub `haitham72/mirsal-builder-io` (private). Windows PC (macOS also supported). Read order: `CLAUDE.md`, `HANDOFF.md` (a save point), this file, then the doc of the area you touch.

## Glossary (the words the docs keep using)

Mirsal Builder is a local, private app that makes animated Telegram stickers (not emoji). One engine serves a chat and a Studio on top.

- **Batch (`G###`)** — one generation run (e.g. G005). Holds a sheet, stickers, a video sheet, animations, and a pack.
- **Sticker (`S#`)** — one cell of a batch (S1-S9). Its number never changes, through review, edits, and rebuilds.
- **Job (`J###`)** — one paid provider call (Higgsfield/Kling). The provider's ticket is stored before waiting, so a crash never pays twice.
- **Gates (G1-G5)** — the five human approvals along the golden path: plan, stills, video sheet, animations, pack. The vision model pre-reviews only and never approves.
- **"Use it anyway" (allow)** — a recorded, reversible human click that lets a judgement-call block through. Only Telegram's own limits stay final.
- **Sheet / video sheet / `sheet_fixed`** — the model-drawn grid; the video sheet rebuilt from approved stickers; `sheet_fixed` is the edited-sheet view.
- **Particle set / burst** — a set of effect sprites linked to library stickers, and the animation rendered from it.
- **Paused** — public deployment (`deployment_plan.md`) and Google OAuth remain parked. What comes next is `plan.md`.

## Where things are tracked (CLAUDE.md rule 7)

| need | file |
|---|---|
| a verdict, eyes or money from Haitham | `waiting-for-haitham.md` (numbered W1-W48) |
| open work to build, by area | `backlog.md` |
| this file: guardrails, how to run, quirks | `dev-notes.md` |
| the paused deployment plan and its nine questions | `deployment_plan.md` |
| the independent audit baseline | `review.md` (appendix A holds the triage of the 2026-10-02 review; a fresh audit updates that one file per `review-prompt.md`) |

An entry is deleted the moment it is built and documented (history lives in git). The old phase plans, the Devin report and the 2026-10-02 review are retired the same way: what was still true of the build is in the tracker files, what was built is in the docs of its area.

## Guardrails

| | |
|---|---|
| **Do freely** | Fix real bugs with a failing-then-passing test; add engine functions, CLI commands and API routes with tests; new prompt template **versions** (add `_v4`, never edit one that was used); measurements; docs. |
| **Ask first** | Spending credits (live generation, bulk embeddings through OpenAI, anything paid); verifier severities or thresholds; deleting an open item whose gate is unanswered; scrubbing the token from history; deleting `mirsal/web/`; anything that changes what the user sees or decides. |
| **Never** | Rename watch folders or outputs (rule 9). Loosen a verifier BLOCK or change "a human approves, Python's blocks are final". Open sticker media to judge it. Commit a token, `.env`, `opencode.json`, `mirsal/telegram-id.md`, `out/users.json`, `out/.asset_secret`. Write inside `inputs/Images_gen|videos_gen`. `git add -A` blind. Force-push. Touch ports 5433 / 5436 / 5437 or the other project's `.env` lines. |

**Locked decisions:** the product is an API / app and the screens are a sandbox (rule 11); the golden path and its gates; issue colours (orange out of bounds, purple bad green screen, yellow bad loop, pink look or motion, blue file / Telegram limit, red dropped or blocked; hatched = not in the set, dashed = kept with a check); out-of-bounds animations off by default with *Include anyway* (`gates.soft_block`: `inside_frame` is a WARN check, so this is a default-off state and not an override of a Python BLOCK; the only recorded override of a BLOCK is `inside_slot` / `cross_slot`); template-locked prompts (the model fills a small JSON, code lints it, the template builds the text); **the local model is whatever the local server lists (LM Studio or vLLM at `MIRSAL_LOCAL_URL`): the chat's dropdown (`GET /api/llm/models`, `POST /api/ai/backend {model}`), else `MIRSAL_LOCAL_MODEL` as a wish (a `:N` suffix falls back to the base id), else the server's first chat model; readiness is a real probe; the embedding model stays local and hardcoded (`nomic-embed-text-v1.5`)** (Haitham, 2026-10-02; `docs/agent-and-chat.md`, Models); the agent never spends without a go-ahead unless "Ask before spending" is off; the vision model never approves.

**Decided by Haitham, 2026-10-02 / 03 (settled: build them, do not re-ask)**

| Decision | What it means now |
|---|---|
| Public deployment and Google OAuth are paused | none of it is worked on, extended, turned on or deleted (the office LAN's sign-in throttling and the per-token limit are the rate limits in use). `deploy/` and `deployment_plan.md` (branch `deployment`) are groundwork. `deploy/gateway/ratelimit.py` stays inert; the engine's per-minute 429 (`console/server.py` `_wait`) stays untouched. Do not raise these unless asked. The local FastAPI + pydantic migration is separately authorized after particles (2026-10-04) |
| Everything stays local for now | embeddings stay local and hardcoded (`services/embed.py` `EMBED_MODEL`, the DB is local). `gpt-4o-mini` is for greeting and routing only; the real work runs on the local server. No hosted embeddings, no swap of the embedding model |
| Never a block a person cannot get past (2026-10-02) | every new check is a WARN with a visible "use it anyway"; only limits Telegram itself rejects (format, size, codec) or a file that does not open may stop something, and even then with words and a next step (`CLAUDE.md` rule 10). Applied: `pipeline.SHEET_PROCEED`, `recut`, `engine/effect_checks.py` |
| Several sheets / effects are made all at once (2026-10-02) | `jobs.paid_parallel()`; `CLAUDE.md` rule 13 |
| Tracking stays in Postgres; **LangSmith is removed** (2026-10-04: problems are tickets, `store-and-search.md` "Tickets") | decisions, tasks, jobs, chats and tickets are recorded in Postgres (`MIRSAL_DB_WRITE=1`, `docs/store-and-search.md`). Old `LANGSMITH_*` / `MIRSAL_TRACE` lines in `mirsal/.env` are ignored; delete them |
| Particle effects: both modes, video first-class, 2x2 default (2026-10-02) | the video is text-only (no start image) and starts and ends empty; 3x3 is offered but measured poor; the simulated mode has gravity / explosion / vortex sliders (`docs/effects.md`) |
| The daily credit cap must never block the owner | decided in principle; the code change is W36 |

## This checkout and how to run

**Two checkouts exist.** macOS: `/Users/haithammohamedibrahim/VsCode/mirsal-builder-io`, branch **`better_ui/ux`** (from `deployment`); the venv is **`mirsal/venv`** (not `.venv`); the server Haitham has open is `python -m mirsal serve` on **:8770** (never kill it); `mirsal/.env` has `MIRSAL_DAILY_CREDITS=` empty (= no cap). Windows: `G:\Haitham\VsCode\Mirsal-Builder`, where most of the code was first written (its former work branch `merge/generate-advanced` is retired; its content is in `deployment`) and where the `.env` had `MIRSAL_DAILY_CREDITS=15`; the venv there is `mirsal\.venv` (use `.venv\Scripts\python` in place of `venv/bin/python`).

Python 3.14 (numpy 2.5, OpenCV 5.0, Pillow 12.3: thresholds in `engine/config.py` were calibrated on an older stack, re-check metrics before trusting them). The code under `mirsal/mirsal/` is grouped by concern (`docs/engine-and-studio.md`, "Layout"): `engine/` (pure), `flow/` (pipeline, gates), `generation/` (Higgsfield, jobs, prompts), `services/` (LLM, embeddings, Telegram), `runtime/` (cache, events, paths, accounts, atomic writes), `media/` (library, video projects, cutout), `store/` (Postgres, pool), `agent/`, `vision/`, `obs/`, `console/`; only `cli.py` stays at the top. Import from the folder (`from mirsal.generation import jobs`), never from the old flat paths. `mirsal/out/` holds the real generations (G001-G105 at the time of writing), the library, jobs and the ledger of this PC, and is mostly tracked in git (`docs/engine-and-studio.md`, "What git tracks of out/"; whether that is on purpose is W29). Docker Desktop must be running for `db up` (Postgres :5434, Redis :6380); both are optional at runtime.

`mirsal/.env` was copied from another project and holds `PG*`, `REDIS_URL` and `LANGSMITH_*` lines for it: Mirsal ignores `PG*` and `REDIS_URL` and always uses its own project name for tracing, but remove those lines. `mirsal/telegram-id.md` (git-ignored) holds a bot token in plain text: delete it once Telegram is configured in Settings. **Security:** an old bot token is in git history (commit `349762b`, revoked by Haitham). Offer a history scrub with a force-push but **never do it unasked**. Any bot token pasted into a chat is compromised and must be revoked after testing. `mirsal/.env` and `out/telegram.json` are git-ignored.

```
cd mirsal
venv/bin/python -m mirsal doctor                              # one health check (its test line says the slow tier is retired)
venv/bin/python -m mirsal test fast                           # Tier 1, under a minute: cross-cutting smoke checks; never claims verification
venv/bin/python -m mirsal test focused                        # approved ~22-case regression loop; exact item-0 gate first, not full verification
venv/bin/python -m mirsal test area engine/video              # Tier 2: the explicit module -> test-class map in mirsal/test_tiers.py
node --test tests/js/*.test.js && venv/bin/python -m tests.test_js   # the console scripts; the slow tier is RETIRED (never run), full `unittest discover` also RETIRED (never run or requested)
venv/bin/python -m mirsal serve --port 8789                   # YOUR server on a spare port; MIRSAL_OUT=<copy of out/G###> keeps real data untouched
venv/bin/python -m mirsal serve --lan                         # the office network over HTTPS (certificate-guide.md); colleagues sign in
venv/bin/python -m mirsal serve --stdlib                      # the old stdlib server (kept for one release; the default is FastAPI on uvicorn)
```

**Test tiers and counts.** The tiers are explicit commands; `focused [profile]` is the approved ~22-case regression selection with the exact item-0 gate first. Tier 1 (`fast`) is the fast edit loop. Tier 2 (`area`) first uses the reviewable hand-picked module -> test-class map; for the rest it derives a lower-bound map from the production modules each test imports directly, and says when a module maps to nothing instead of guessing upward. Each run prints **SELECTED**, **RAN** and **SKIPPED** separately; any skip is never a PASS. **Tier 3 (`mirsal test slow`: `test_golden`, `test_effect_video`, `test_allow_still`, `test_anim_speed`, `test_engine`, `test_verify`) is RETIRED by Haitham, 2026-10-03: it is never run and never requested** (it was a 15-20 minute "required media gate" and the old bar for "verified"; a legacy command remaining in code must not be run; `doctor` no longer asks for it). Those six modules still run as ordinary test modules through `area`/`focused` when a change maps to them. Full `unittest discover` is also RETIRED: never run or requested. "Verified" is Haitham's own browser look. Full policy: `docs/testing.md`. Python test runs go **one at a time** (parallel runs collide with `409 busy`).

**The test budget (Haitham, 2026-10-04; `docs/testing.md`, first section):** one run per change, the narrowest (the test you wrote, by name, else the mapped `area`); a pass stays valid until a file it covers changes, so nothing is re-run to be sure, before a commit or at the start of a session; docs-only changes run nothing; `focused` at most once at the end of a gate/recovery/video-sheet phase; a failure outside your change is one `still unknown:` line, not a loop. The slow tier and full discovery are retired.

The tests pin `MIRSAL_NO_REAL_CLI=1` and `MIRSAL_LLM_PROVIDER` / `MIRSAL_AGENT_PROVIDER` / `MIRSAL_VISION_PROVIDER` = `none`, `MIRSAL_DB_WRITE=0`, `MIRSAL_TRACE=none` and LangSmith off (`tests/__init__.py`): no test reaches Higgsfield, OpenAI, LM Studio, the real Postgres or LangSmith; a test that needs an answer passes a fake. The node tests (`tests/test_js.py`) fail without node (`MIRSAL_SKIP_JS=1` skips them on purpose).

## Looking at the app in a browser

Playwright is installed in `mirsal/venv` and a headless Chromium works (Claude walked P1-P13 and the particle screens this way on 2026-10-03; the earlier note that a browser could not be opened is obsolete). Never use Haitham's live data or server (:8770). Recipe:

```
rsync -a --exclude cache --exclude trash --exclude library/files --exclude jobs mirsal/out/ <scratch>/outcopy/
MIRSAL_OUT=<scratch>/outcopy MIRSAL_DB_WRITE=0 MIRSAL_TRACE=none LANGSMITH_TRACING=false MIRSAL_NO_REAL_CLI=1 MIRSAL_LLM_PROVIDER=none MIRSAL_AGENT_PROVIDER=none MIRSAL_VISION_PROVIDER=none venv/bin/python -m mirsal serve --port 8795
```

Dismiss the welcome modal first (`document.getElementById('welcome').classList.remove('on')`) or it intercepts every click; open a batch with `ACT.hopen({dataset:{id:'5'}})`. G005 has 9 animations, several already allowed by hand (a good case for switch off / on); G012 has no video. Check that the server is alive (`/api/health`) before believing a browser result. Never press Create. The browser caches `studio.css`, so reload after a CSS change; after a selection click the pack grid re-renders, so re-query elements; Playwright's `goto` to the same URL with only a hash does NOT reload the page (use `location.reload()` after restarting the test server). The Studio shows a banner when it runs older code than the files on disk. **Most "it still fails" reports are a stale server process.**

**To try the resolver without the server:** `cd mirsal && venv/bin/python -c "from mirsal.agent import resolver as R; print(R.classify('make him wear winter coat', False, True, False)); print(R.resolve('make him wear winter coat', {...}))"`. Importing `mirsal.agent` pulls in `cv2` and the whole pipeline, so the venv is required.

## Quirks that cost time

- **Most "it still fails" reports were a stale server process** (Python loads code once). Compare the process start time with the file times first.
- VP9 (`row-mt`) output is not byte-stable: compare metrics, never WebM hashes. Windows `os.replace` fails with WinError 5 on an open file (and a reader can get `PermissionError` for an instant): write through `runtime/atomic.py`, read through `atomic.read_text`; never a fixed `<name>.tmp`.
- **Never put a regex or a Windows path (`\b`, `\d`, `\1`, `\t`, `\a`) in a Python string written through a shell heredoc**: the backslash sequence becomes a control character (a backspace, chr(1), a tab) and silently breaks the pattern or the test (`grep -rlP "\x08"` finds such damage). Write scripts and tests with the Write / Edit tools and use raw strings (`r"..."`) or `chr(92)`; PowerShell has no `&&` and mangles non-ASCII when it rewrites files. A heredoc that contains an apostrophe can also fail to parse in the Bash tool: use the Write tool for the file.
- Two scripts of the Studio must not declare the same top-level `const` (the second one is not run at all; `history.js` was dead for a while because of `ago`). They also share ONE `ACT` object: a second `ACT.name =` in a later script silently replaces the first (`history.js` replaced `hopen`, so "Earlier batches" opened batch NaN); `tests/test_js.py` fails on any such clash that is not listed as intentional, and on a `data-act` button nothing handles. Class names in `agent.css` are namespaced (`ag-`, `is-`, `k-`) because the Studio's own CSS already uses `.step`, `.tile`, `.sel`, `.done`.
- **A new console script must be added to `UI_FILES` in `console/server.py` and to `index.html` in the right load order** (the recovery scripts `sheet-recovery.js` and `job-recovery.js` load before `live.js`; `trash.js` before the Settings card needs it). A script missing from `UI_FILES` is a 404 the page swallows silently; this was found in the browser look of 2026-10-03.
- A move of files needs the import paths in STRINGS fixed too (`mock.patch("mirsal.services.telegram._ssl_context")`, a `python -c` snippet): an AST pass cannot see them.
- The Edit tool fails on a **multi-line** match in a CRLF file (`tests/test_live.py` is CRLF: `git ls-files --eol`) but works for a single line: patch such files with a small script written by the Write tool (it sets `newline=""` and re-joins with `\r\n`), never with a PowerShell heredoc.
- LM Studio loads a listed model on first use (the first call is slow); `qwen3.5-4b:2` is an instance suffix that exists only while a second copy is loaded (use `qwen3.5-4b`); Qwen thinks unless the closed think block is prefilled (the client does). A test must never reach the real Higgsfield CLI (`MIRSAL_NO_REAL_CLI` is set by `tests/__init__.py`).
- **A `# comment` after a value in `mirsal/.env` used to become part of the value** (the chat's provider was `"auto   # the chat assistant;..."`): fixed by one parser, `runtime/envfile.py`; the suite pins `MIRSAL_DB_WRITE=0` and `MIRSAL_TRACE=none` because the real `.env` sets them.
- The venv is `mirsal/venv` on the macOS checkout (Python 3.14) and `mirsal/.venv` on Windows. In a bash heredoc, an apostrophe or `\\1` / `\\n` inside a Python string is mangled: write edit scripts with the Write tool and raw strings, run them afterwards.

## Starting a session (the prompt for the next LLM)

> Read `CLAUDE.md`, `HANDOFF.md` (a save point: anything left half-done), this file and the doc of the area you touch. Then:
>
> 1. **Built, do not redo:** the visual redesign (`docs/design.md`), the sheet-problem fix (cut anyway + `recut`), the local model (`docs/agent-and-chat.md` Models), parallel paid jobs, the particle-effects engine and its Kling measurements (`docs/effects.md`), particle sets owned by library stickers with the burst maker, the trash and the chat intents (`docs/particles.md`), one control per cell and edits by what they mean, verdict replay, stalled-job recovery, G3 overrides, the trash purge and the Generate prompt step (`docs/engine-and-studio.md`, `docs/agent-and-chat.md`, `docs/api.md`).
> 2. **Open:** `docs/backlog.md` for what to build, `docs/waiting-for-haitham.md` for what only a person can settle. Public deployment and Google OAuth remain paused.
> 3. **Standing rules from Haitham:** never a block a person cannot get past (`CLAUDE.md` rule 10); several paid jobs may run at once but never spend without the price shown and a go-ahead; judge media only with numbers; tracking stays in Postgres and LangSmith is off.
> 4. **Paused, do not touch, do not delete, do not re-ask:** public deployment (`docs/deployment_plan.md` and the `deployment` branch's gateway files) and Google OAuth (the office LAN's sign-in throttling in `api.md` "Office accounts on the LAN" §2.2 is the one planned use of the rate limiter), and every held question in `waiting-for-haitham.md` marked held or parked.
>
> Method: a failing-then-passing test for every fix, run alone by name (the test budget in `docs/testing.md`: never re-run what already passed, never stack tiers), docs updated in the same step, no paid call without Haitham's go, judge media only with Python, and use `mirsal/venv` on the macOS checkout. The trackers are trackers: delete an entry the moment it is implemented and documented.
