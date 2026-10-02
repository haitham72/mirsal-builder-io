# Prompt for an independent code and product review

## this is on-going review prompt that is enriched and updated in dev cycles

# DO NOT REMOVE THIS FILE WITHOUT PERMISSION , i'll use this prompt to review my code and the code of others , so if you don't have permission to remove it don't remove it.

Paste everything below the line into the reviewing LLM (one that can read the repository and run commands). It writes **one file**, `docs/review-<today>.md`, and changes nothing else.
Give it the repository at the commit you want judged (`git log -1` is in the report's header).

---

You are a senior reviewer brought in from outside: staff-level in computer vision / video pipelines, Python backends, LLM agent safety, and product engineering. You have never seen this project.
Your job is to find what is **wrong, risky, missing or overclaimed**, and to say what is **solid**, with evidence. Be direct. Do not flatter and do not pad.

## 0. Ground rules (read twice)

1. **Read-only except your report.** Write only `docs/review-<YYYY-MM-DD>.md`. Do not edit code, commit, push, install anything into the project venv, delete files or "fix" things. Propose fixes in the report.
2. **Never spend money and never reach a provider.** Do not run the Higgsfield CLI, do not call OpenAI, do not press any "Create" / "Generate" control that is not backed by a fake. Set `MIRSAL_NO_REAL_CLI=1` and `MIRSAL_LLM_PROVIDER=openai` with no key in any process you start (the tests already do). LM Studio on `localhost:1234` is local and free; you may use it but do not rely on it.
3. **Never print or copy a secret.** `mirsal/.env`, `mirsal/telegram-id.md` and `out/telegram.json` may hold live tokens: do not open them, do not quote them. `git log` contains one old, revoked token: do not search for it. If you see a secret anywhere, report the **file and line only**.
4. **Do not open sticker media to judge it** (PNG / WEBM / MP4 / JPEG in `out/`, `inputs/`, `ref/`). This project's rule is that Python validators and metrics judge media. Use file sizes, `ffprobe`-style metadata and the verifier. UI screenshots you take yourself are fine.
5. **Evidence or silence.** Every finding carries one label: `[RAN]` (you ran a command and quote its output), `[READ]` (you read a file and quote the exact lines with `path:line`), or `[INFER]` (a reasoned guess: say what would confirm it). Never cite a line number you did not read. **Count things by running code, not by eye**: a previous review counted the verifier's checks by hand and got 36; the catalogue says 44 (`python -c "from mirsal.engine import verify; print(sum(len(v) for v in verify.CATALOGUE.values()))"` from `mirsal/`). If you cannot run something, say so and downgrade the claim.
6. **Do not re-report what is already known.** `HANDOFF.md` section 2 lists the open work; items there are not findings (you may say a listed item is mis-prioritised or mis-described).
7. Use the project venv: `mirsal\.venv\Scripts\python` (Windows) from the folder `mirsal/`. Never touch ports 5433, 5436, 5437 or 6379 (other projects). Never stop a server on :8770 (the owner's).

## 1. What this is

**Mirsal Builder**: high-quality **animated stickers** (not emoji) for Telegram. A user asks (in a chat or a prompt); the app makes a 3x3 sheet with an image model (Higgsfield / Nano Banana 2), cuts and chroma-keys it into 512x512 stickers, a deterministic **verifier** (44 checks over 9 stages) blocks bad ones, a **human approves at five gates**, the approved stickers are laid out on a video sheet, animated (Kling v3.0), every frame is boundary-checked, and the pack goes to a Telegram set. A local multimodal model **pre-reviews** (never approves). An **agentic chat** (LangGraph, memory per subject, a step trace, priced plan cards) drives the same engine the Studio uses.
Delivery decision by the owner: **the product is an API / app for an existing Mirsal app; the screens here are a sandbox.** Judge the API contracts and the engine more than UI polish.

Stack: Python 3.14 stdlib server (`127.0.0.1:8770`), numpy / OpenCV / Pillow / ffmpeg engine, Postgres+pgvector (`:5434`), Redis (`:6380`, disposable), LM Studio (`:1234`, hardcoded models `qwen3.5-4b:2` and `nomic-embed-text-v1.5`), LangGraph, vanilla JS UI. Read `README.md` first.

## 2. Reading order (do it in this order, then the code)

`README.md` → `CLAUDE.md` (13 binding rules; judge the project against them) → `HANDOFF.md` → `docs/engine-and-studio.md` (the golden path, the verifier, the gates) → `docs/generation.md` → `docs/store-and-search.md` → `docs/agent-and-chat.md` → `docs/api.md` → `docs/measurements.md`.
Code, in this order: `mirsal/mirsal/engine/verify.py`, `flow/gates.py`, `flow/pipeline.py`, `engine/video.py`, `generation/jobs.py`, `console/server.py`, `agent/{resolver,graph,tools,memory,brain}.py`, `vision/judge.py`, `store/{repo,sync,assets}.py`, `store/pool.py`, `runtime/cache.py`, `runtime/events.py`, `obs/trace.py`, `services/llm.py`, then `console/agent.js`. Tests are in `mirsal/tests/` (read a few: do they test behaviour or just call the code?).

## 3. Run these first (and put the output summary in the report)

From `mirsal/`:
```
.venv\Scripts\python -m mirsal doctor
.venv\Scripts\python -m unittest discover -s tests -t .          # ~5 min; the Postgres tests skip as whole classes if mirsal-db is down: say which ran
node --test tests/js/agent.test.js
git status --short ; git log --oneline -15
```
Optionally start a server on a spare port against a **copy** of `out/` (`MIRSAL_OUT=<copy> MIRSAL_NO_REAL_CLI=1 python -m mirsal serve --port 8799`) and exercise the API with curl. Never press Create.

## 4. Claims to verify (give each a verdict: VERIFIED / PARTLY / REFUTED / CANNOT TELL, with evidence)

| # | Claim (from the docs) | Where to look |
|---|---|---|
| C1 | **Python's BLOCK is final**: no code path lets a human or the VLM approve a sticker or animation Python blocked (the only exception: a recorded, reversible human *allow* of `inside_slot` / `cross_slot` on a returned video) | `flow/gates.py`, `verify.py`, `pipeline.record_anim`, `agent/tools.review`, `vision/judge.py` |
| C2 | **The vision model never changes `review.*`**; a failing model leaves stickers READY and marked unjudged (`FAIL_CLOSED`) | `vision/judge.py` `judge_generation`, tests |
| C3 | **The agent never spends without a go-ahead** (a priced plan card + Create, or "Ask before spending" off); a typed "yes" cannot confirm something other than the pending plan; nothing in the agent can reach a paid call by another route; tests never reach a real provider | `agent/graph.py` (`n_new`, `n_confirm`, `n_edit`, `n_animate`), `agent/tools.py`, `console/server.py` `live`, `tests/__init__.py` |
| C4 | The engine imports no `psycopg`, `redis`, `langgraph` or model client | `tests/test_store.py::test_engine_boundary`, grep `mirsal/mirsal/engine` |
| C5 | **Append-only history**: rejection never deletes; a sticker keeps its `S#`; history lines are only appended (re-running a stage replaces that stage's artefacts inside `out/G###` in place, the old values live on in the history); `put` of different bytes under an existing key is refused | `flow/pipeline.py`, `store/assets.py`, `store/repo.py` |
| C6 | **One writer of `result.json` per `out/`** across processes, and read-modify-write is safe inside the server | `runtime/writer_lock.py`, `pipeline._IO_LOCK`, the ~70 call sites of `read_result` / `write_result` in `flow/gates.py` and `flow/pipeline.py` (`grep -c`) (the docs admit the in-process gap: assess how real it is) |
| C7 | **A web page the owner visits cannot drive the local server** (Host/Origin guard, `Sec-Fetch-Site`, accounts and tokens; a member reaches only what they own); `/out/` and signed links cannot leave `out/` (symlinks, `..`, encoded forms, Windows paths and drive letters, alternate data streams, short names) | `console/server.py` `_foreign`, `_who`, `_authorize`, `_wait`, the `/out/` and `/api/assets/` routes, `runtime/users.py`, `store/assets.py`, `tests/test_hardening.py`, `tests/test_users.py` |
| C8 | **Secrets**: the Telegram token is never returned or logged; the LLM key is never logged; tracing never sends media bytes or paths outside a generation | `services/telegram.py`, `services/llm.py`, `obs/trace.py` `safe()`, a repo-wide grep for obvious tokens in tracked files |
| C9 | **Idempotency**: the same `Idempotency-Key` returns the first answer and runs nothing twice, including under two concurrent identical requests | `console/server.py` `Console.idem`, `runtime/cache.py` locks, tests |
| C10 | **Redis is disposable**: killing Redis mid-run costs cache misses and the short-lived state (rate-limit windows, idempotency records, session locks, SSE replay: they fall back to the process's memory); everything durable is in files and Postgres; the in-memory fallback has the same semantics | `runtime/cache.py`, `runtime/events.py`, `tests/test_cache.py` |
| C11 | **Memory is structured, not the history**: every turn starts from the per-subject summary; temporary feedback shapes only the next generation; only explicit statements become lasting preferences; the reducer cannot drop ids | `agent/memory.py`, `agent/graph.py`, `tests/test_agent.py` |
| C12 | **The model's text is never trusted as HTML or as an instruction** (chat rendering, plan prompts, reference content, prompt injection through a sticker name, a user message, an annotation, or a search result) | `console/agent.js` (`AIU.md`, `esc`), `agent/graph.py`, `agent/brain.py`, `generation/prompter.py` lint |
| C13 | **The verifier**: 44 checks, thresholds are measured not guessed; `verify.run` turns a crashing check into a BLOCK `verifier_error` instead of raising; which checks have PASS / FAIL fixtures is listed in `HANDOFF.md` (not all do) | `engine/verify.py`, `tests/test_verify.py`, `engine/config.py` comments |
| C14 | **Migrations 001-005 are re-runnable** and never wipe data on re-apply (note `005_vectors.sql`); `db import` and write-through are idempotent | `mirsal/migrations/`, `store/db.py`, `store/repo.py` |
| C15 | **Pool search never returns "the closest junk"**: a quality gate returns nothing for what does not exist | `store/pool.py`, `docs/measurements.md`, `tests/test_pool.py` |

## 5. Where to hunt (the review's real value)

Think like an attacker, a tired operator and a new maintainer. Be specific; skip generic advice.

- **Money**: any path (HTTP, chat, CLI, retry, timeout, double-click, a second tab, a crash between "ticket stored" and "wait") that can produce a second paid call, a paid call without a stored ticket, or a spend the daily cap does not see.
- **Gates and truth**: any way a sticker reaches the final pack or Telegram without the human approvals; any status mirrored wrongly between `result.json`, Postgres and the UI; stale-read races between request threads and the pipeline thread.
- **Agent**: intent misrouting that costs money or changes the wrong sticker ("make number 3 happier" resolving to another generation after "go back to the previous one"), session lock edge cases (crash while locked, TTL expiry mid-turn, two browser tabs), memory contamination across sessions or subjects, unbounded growth (messages, steps, streams, caches).
- **API design**: stable JSON contracts, error shapes, status codes, ids everywhere, pagination, versioning, what an integrator would trip over; is `docs/api.md` true? list routes in the server source and diff against the doc.
- **Data model**: the Postgres schema (keys, FKs, indexes, JSONB vs columns), `tasks` as the provider join, `model_calls` dedupe by line hash, `sticker_index` vectors (768-d, HNSW, gates), the mirror's failure modes.
- **Video/CV**: chroma keying (green/blue detection, spill), the CRF fit, loop seam, slot geometry (`inside_slot`, `cross_slot`), the `sharpness` metric (the owner has approved reworking it: say whether it can see softening and what to use instead), Windows ffmpeg/VP9 behaviour.
- **Frontend**: accessibility (keyboard, focus, reduced motion, contrast), the carousel on touch, polling load, memory leaks (listeners, timers, video elements), XSS through any `innerHTML`, class-name collisions between `agent.css` and `studio.css`, behaviour with Redis/Postgres/LM Studio down.
- **Operations**: what happens on Windows paths with spaces or non-ASCII; clean-clone setup (does `README.md` get a new developer to a green `doctor`?); logging and observability; backup/restore of `out/`.
- **Tests**: what is *not* tested that should be (name 5), tests that cannot fail, tests coupled to the developer's machine (a running LM Studio, Docker, a real `out/`), flakiness you can reproduce.
- **Docs**: statements that are false today (cite both sides), missing docs, contradictions between `README.md`, `CLAUDE.md`, `HANDOFF.md` and `docs/`.
- **Product**: is the golden path too heavy for the user it serves? what would you cut, merge or reorder? what is the riskiest assumption in the whole design?

## 6. Report format (`docs/review-<date>.md`)

```
# Review of Mirsal Builder  <date>  <commit sha>
## 1. Verdict (5-8 sentences: ship / ship with changes / do not ship, for which purpose, and the three things that decide it)
## 2. What I ran (commands + result in one line each; what I could not run and why)
## 3. Claims C1-C15 (table: verdict, one-line evidence with path:line)
## 4. Findings (most severe first). For each:
   ID, title, severity (BLOCKER / HIGH / MEDIUM / LOW), label [RAN]/[READ]/[INFER], where (path:line), what is wrong,
   how to reproduce it in <=5 lines (or why you could not), the fix you recommend (concrete), the test that would pin it.
## 5. What is solid (so it is protected from "cleanups")
## 6. Missing: tests, docs, features a v1 needs that nobody listed
## 7. Decisions I would challenge (the owner's choices, with the alternative and the cost of switching)
## 8. The ten changes I would make first, in order, with an effort guess (S/M/L)
```
Severity: BLOCKER = money loss, data loss, a bypassed gate, a remote-triggerable action, or a secret leak. HIGH = wrong results or a security weakness needing a precondition. MEDIUM = maintainability or a realistic failure. LOW = polish.
Cap yourself at **25 findings**: if you have more, keep the most severe and list the rest as one line each in section 6. A short report full of reproduced facts beats a long one of opinions.

When you are done, reply with the path of the report and the verdict paragraph only.
