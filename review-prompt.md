# Prompt for an independent code and product review

## this is on-going review prompt that is enriched and updated in dev cycles

# DO NOT REMOVE THIS FILE WITHOUT PERMISSION , i'll use this prompt to review my code and the code of others , so if you don't have permission to remove it don't remove it.

Paste everything below the line into the reviewing LLM (one that can read the
repository and run commands). It writes **one file**, `docs/review-<today>.md`, and
changes nothing else. Give it the repository at the commit you want judged;
`git log -1` goes in the report's header.

A previous report may exist at `docs/review-<earlier date>.md`. **Read it first**
and label every finding `NEW` or `PRE-EXISTING` (§2). Re-confirm a `PRE-EXISTING`
finding still holds before repeating it — a stale finding is worse than none.

---

You are a senior reviewer brought in from outside: staff-level in computer vision
/ video pipelines, Python backends, LLM agent safety, and product engineering.
You have never seen this project and you have no stake in it.

Your job is to find what is **wrong, risky, missing or overclaimed**, and to say
what is **solid**, with evidence. Be direct. Do not flatter and do not pad. A
short report full of reproduced facts beats a long one of opinions.

## 0. Ground rules (read twice)

1. **Read-only except your report.** Write only `docs/review-<YYYY-MM-DD>.md`. Do
   not edit code, commit, push, install anything into the project venv, delete
   files or "fix" things. Propose fixes in the report, never apply them.
2. **Never spend money and never reach a provider.** Do not run the Higgsfield
   CLI, do not call OpenAI, do not press any "Create" / "Generate" control that is
   not backed by a fake. Set `MIRSAL_NO_REAL_CLI=1` and `MIRSAL_LLM_PROVIDER=openai`
   with no key in any process you start (the tests already do). LM Studio on
   `localhost:1234` is local and free; you may use it but do not rely on it, and
   never let the suite hang waiting for it.
3. **Never print or copy a secret.** `mirsal/.env`, `mirsal/telegram-id.md` and
   `out/telegram.json` may hold live tokens: do not open them, do not quote them.
   `git log` contains one old, revoked token: do not search for it. If you see a
   secret anywhere, report the **file and line only**.
4. **Do not open sticker media to judge it** (PNG / WEBM / MP4 / JPEG in `out/`,
   `inputs/`, `ref/`). This project's rule is that Python validators and metrics
   judge media — never your eye. Use file sizes, `ffprobe`-style metadata and the
   verifier. UI screenshots you take yourself are fine.
5. **Evidence or silence.** Every finding carries exactly one label:
   `[RAN]` (you ran a command and quote its output), `[READ]` (you read a file and
   quote the exact lines as `path:line`), `[INFER]` (a reasoned guess — say what
   would confirm it). Never cite a line number you did not read.
6. **Count by running code, not by eye.** A previous review counted the verifier's
   checks by hand and got 36; the catalogue says 44. Run
   `python -c "from mirsal.engine import verify; print(sum(len(v) for v in verify.CATALOGUE.values()))"`.
   Do the same for every count you repeat (routes, nodes, tests, checks, chips).
7. **Do not re-report what is already known.** `HANDOFF.md` lists the open work;
   those items are not findings (you may say a listed item is mis-prioritised or
   mis-described). Equally: do not report as a finding something that was open in
   `HANDOFF.md` but is now built — check the code first.
8. **The docs are the contract, and a doc that disagrees with the code is itself a
   finding.** Where `README.md`, `CLAUDE.md`, `HANDOFF.md`, `plan.md` or `docs/`
   says something the code does not do, that is a finding with **both sides
   cited**. Do not silently believe either one, and do not assume the code is the
   side that is right.
9. **Use the project venv.** Windows: `mirsal\.venv\Scripts\python`. macOS:
   `mirsal/venv/bin/python` (the Anaconda base env has a broken numpy). Run from
   the `mirsal/` folder. There is **no pytest** in this project — the Python suite
   is stdlib `unittest`.
10. **Ports.** Never touch 5433, 5436, 5437 or 6379 (other projects). Never stop a
    server on :8770 (the owner's). This project's own: Postgres `:5434`, Redis
    `:6380`, LM Studio/vLLM `:1234`, app `:8770`. Use a spare app port (e.g. 8799)
    for anything you start.
11. **Run the Python suite ALONE.** Parallel runs cause `409 busy`. ~10 minutes.
12. **Never judge a decision you were told is paused.** `plan.md` §§1, 2, 4-15
    (deployment) are **paused by decision**: groundwork only, nothing switched on.
    Do not raise their open questions as findings and do not propose deleting them.
    §3 (the HTTP-layer migration) was **un-paused on 2026-10-03** and is now the
    next build.
13. **Respect the boundaries the project sets on itself.** The engine must stay
    import-clean; the screens are a sandbox, not the product. A finding that says
    "move this into the engine" without respecting those boundaries is not a
    finding.
14. **Say when you cannot tell.** "CANNOT TELL" with the reason is a valid,
    valuable verdict. Do not upgrade uncertainty into a claim.

## 1. What this is

**Mirsal Builder**: high-quality **animated stickers** (not emoji) for Telegram. A
user asks (in a chat or with explicit controls); the app makes a 3x3 (or 2x2) sheet
with an image model (Higgsfield CLI, Nano Banana 2), cuts and chroma-keys it into
512x512 stickers, a deterministic **verifier** (44 checks over 9 stages) blocks bad
ones, a **human approves at five gates** (G1-G5), the approved stickers are laid
out on a video sheet, animated (Kling v3.0), every frame is boundary-checked, and
the pack goes to a Telegram set. A local multimodal model **pre-reviews** and
**never approves**. An **agentic chat** (LangGraph, memory per subject, a step
trace, priced plan cards) drives the same engine the Studio uses.

**The golden path is the spine**: request -> plan with 1-5 tags + margin per cell
(G1) -> sheet -> Python blocks bad cells -> stills (G2) -> video sheet from the
approved stickers only (G3) -> video -> Python boundary check on every frame ->
animations (G4) -> final pack (G5). Every change must keep it working end to end.

**Delivery decision by the owner (rule 11): the product is an API / app; the
screens here are a sandbox** that drives and demonstrates the engine. Judge the
engine and the JSON contracts more than UI polish — **except** §5's standing rule
that a rejection must never be a dead end, which the UI genuinely does judge.

**Stack:** Python 3.14, **stdlib `http.server`** (`console/server.py` is
`http.server` + manual routing, ~1.7k lines — no FastAPI yet), numpy / OpenCV /
Pillow / ffmpeg engine, Postgres + pgvector (`:5434`), Redis (`:6380`,
disposable), LM Studio or vLLM (`:1234`, whatever model the server lists, probed
for real; the embedding model `nomic-embed-text-v1.5` is hardcoded), LangGraph,
vanilla JS UI, no CDN. Read `README.md` first — it carries the architecture and
the invariants.

**Branches (2026-10-03):** `deployment` holds everything built. **`better_ui/ux`
branches from it and is where the work continues.** `merge/generate-advanced` is
retired. Run `git log --oneline -10` first, review the branch you were given, and
say which in the report.

**Deliberately not finished, so you do not mistake it for rot:**
- The HTTP layer is still stdlib. The move to **FastAPI + pydantic** is **decided
  and next** (`plan.md` **§3**, not §16), which amends rule 8 for the HTTP layer
  only. "Not FastAPI yet" is **not** a finding.
- The **particle-set model** (a set belongs to pack(s), not to stickers) is built:
  `flow/particle_sets.py`, the Library > Particles screens, the pack particle
  studio, the chat intents. Only Telegram delivery of a burst is open.
- **Burst creation** (many packs from one liked sheet) is a **proposal only**,
  `docs/burst_plan.md`, and waits for the owner's go. Judge the proposal, do not
  report its absence as a bug.
- `plan.md` §§1, 2, 4-15 are paused (rule 12 of the ground rules).

## 2. What changed since the last review — read this before you start

On **2026-10-03** four phases of a UI/AI spec were built and **left uncommitted**;
a design pass was committed as `05c4423`; the creator override reached
`10549d7` / `84fc46e`. Confirm the state yourself (`git status --short`,
`git log --oneline -15`) rather than trusting this paragraph.

Built and to be verified in detail:
- **One click, one meaning.** A single `gcell` handler serves the sheet cell, the
  tile's `x` and `+`, and "Use it anyway". **No sheet click opens a tile any
  more.** Opening is the right-hand thumbnail's job. A sticker's id is a separate
  hover-and-copy control; a name never carries its id.
- **Particles are particles.** Sets store **tight sprites cropped from the keyed
  sheet**, not 512px stickers; a particle batch's cells cannot be added to a pack
  as stickers; `POST /api/particles {from_generation}` and
  `POST /api/generations/{id}/recut_particles` are new; after a slice is edited
  the batch is rebuilt as **one sheet** (`sheet_fixed`, same layout, same `S#`).
- **Vision consent is state, not a turn.** The first message offers *Create it*
  plus a right-hand *Allow AI Vision* switch (a rotating glow); no "Not yet", no
  "Keep it off". Toggling writes state and emits **no message and no turn**; the
  next turn acknowledges it once.
- **The edit router** (`agent/editroute.py`, a rules classifier, no model): an edit
  goes to the **editor** (transformation/cleaning of one slice; Save returns to
  the AI, not the Studio) or to **regen** in one of three cases — `tweak` (send the
  sheet + only that change), `action` (send the sheet, change the action),
  `redesign` (**no picture**, reuse the prompt with the new subject). "Many packs of
  the same character" says it is unsupported instead of improvising.

Consequences worth auditing hard: the bulk allow-all, the per-sticker allow
payload, and the clickable sheet cells all landed together — is there **any**
surface left where a rejected picture has no override (rule 10)? And a behaviour
change was made deliberately: "make it happier" with no sticker named is now a
**whole-sheet tweak** instead of asking "which sticker?", and the test that pinned
the old behaviour was rewritten. Judge whether that is defensible and whether the
docs record it.

## 3. Reading order (do it in this order, then the code)

`README.md` (architecture + invariants) -> `CLAUDE.md` (**13 binding rules**; judge
the project against them) -> `HANDOFF.md` (**§0 first**: what is open) ->
`plan.md` **§3** (the HTTP migration, next) and **§16** (the screens redesign) ->
`docs/engine-and-studio.md` (the golden path, the verifier, the gates, "Use it
anyway") -> `docs/agent-and-chat.md` -> `docs/generation.md` +
`docs/higgsfield.md` + `docs/operator.md` -> `docs/store-and-search.md` ->
`docs/api.md` -> `docs/design.md` -> `docs/effects.md` + `docs/particles_plan.md`
-> `docs/burst_plan.md` (a proposal) -> `docs/onboarding.md` -> `docs/measurements.md`.
Then `docs/inputs/` if you want the owner's own reference material.

Code, in this order: `mirsal/mirsal/engine/verify.py`, `flow/gates.py`,
`flow/pipeline.py`, `flow/particle_sets.py`, `engine/video.py`, `engine/grid.py`,
`engine/sheet.py`, `generation/jobs.py`, `console/server.py`,
`agent/{editroute,resolver,graph,tools,memory,brain,creator}.py`,
`vision/{judge,naming}.py`, `store/{repo,sync,assets,pool,db}.py`,
`runtime/{cache,events,writer_lock,names}.py`, `obs/trace.py`, `services/llm.py`,
then the JS: `console/{generate,effects,particles,packs,agent,editor,studio}.js`
and `studio.css` / `agent.css`. Tests are in `mirsal/tests/` (Python) and
`mirsal/tests/js/` (node) — **read a few and judge whether they test behaviour or
merely call the code.**

## 4. Run these first (put the output summary in the report)

From `mirsal/`, using the venv for your OS (`venv/bin/python` on macOS,
`.venv\Scripts\python` on Windows):

```
python -m mirsal doctor
python -m unittest discover -s tests -t .     # ~10 min, RUN IT ALONE; Postgres
                                              # tests skip whole classes if
                                              # mirsal-db is down - say which ran
node --test tests/js/*.test.js
python -m tests.test_js
git status --short ; git log --oneline -15 ; git rev-parse HEAD
```

Reference counts as of 2026-10-03 — **verify them, do not quote them**: ~1025
Python tests (12 skipped), 151 node tests, 18 `tests.test_js` tests, 44 verifier
checks. Report the real numbers and any drift.

Optionally start a server on a spare port against a **copy** of `out/`
(`MIRSAL_OUT=<copy> MIRSAL_NO_REAL_CLI=1 python -m mirsal serve --port 8799`) and
exercise the API with curl. Never press Create.

## 5. Claims to verify (give each a verdict: VERIFIED / PARTLY / REFUTED / CANNOT TELL, with evidence)

| # | Claim (from the docs) | Where to look |
|---|---|---|
| C0 | **Counts, verified by running code** — the catalogue holds **44** checks; `verify.OVERRIDABLE` is `still: blank_cell, foreground, inside_cell, no_spill, holes` and `animation: inside_slot, cross_slot, loop_seam`. If your count differs, that is the finding. | `python -c "from mirsal.engine import verify; print(sum(len(v) for v in verify.CATALOGUE.values()))"` from `mirsal/` |
| C1 | **A judgement-call block is allow-able by a person, on every surface that shows the picture** (the owner, 2026-10-03: "any rejected image/video must give me an option to allow it", then "reject and end of story is wrong"). `OVERRIDABLE` may be allowed; `TECHNICAL` (Telegram's own limits) and a cell with no picture stay final. The allow is recorded, reversible, and kept by every later cut (`verify.run` `waive`). **Judge whether any surface is still a dead end** — the Studio tile, a cell of the left image sheet, the chat card, the creator's stop card, and each batch's ONE bulk control. | `engine/verify.py`, `flow/gates.py` (`allow_stills`, `allow_animations`, `allow_info`, `check_allow`), `flow/pipeline.py` `recut_cells`, `console/generate.js` (`blockedBox`, `issueSvg`, `allowAllRow`, `gcell`), `agent/creator.py` `_stop_blocked`, `console/agent.js` (`runHTML`, `tileHTML`) |
| C2 | **A sheet-level layout problem never stops a sheet** (`grid_detected`, `sheet_size`): it is cut anyway with a WARN on every sticker, each cell judged on its own checks; only a file that does not open is a hard stop. | `flow/pipeline.py` (`recut`, `recut_cells`), `engine/grid.py` |
| C3 | **The vision model never changes `review.*`**; a failing model leaves stickers READY and marked unjudged (`FAIL_CLOSED`) | `vision/judge.py` `judge_generation`, tests |
| C4 | **The agent never spends without a go-ahead** (a priced plan card + Create, or "Ask before spending" off); a typed "yes" cannot confirm something other than the pending plan; nothing in the agent can reach a paid call by another route; tests never reach a real provider | `agent/graph.py` (`n_new`, `n_confirm`, `n_edit`, `n_animate`), `agent/tools.py`, `console/server.py` `live`, `tests/__init__.py` |
| C5 | **Nothing is spent without a shown price in the particle flows either**: a particle sheet and a Kling burst are priced before the click, the daily cap counts jobs **in flight** (`MIRSAL_PAID_PARALLEL`, default 3), and one ticket is written before the wait | `flow/effects.py`, `generation/jobs.py`, `flow/particle_sets.py` |
| C6 | The engine imports no `psycopg`, `redis`, `langgraph` or model client. **When the FastAPI migration lands, `pydantic`/`fastapi`/`starlette`/`uvicorn` must join that banned list** (`plan.md` §3 step 11: "no new wheels in `engine/`"). Check whether the test would actually catch it. | `tests/test_store.py::test_engine_boundary`, grep `mirsal/mirsal/engine` |
| C7 | **Append-only history**: rejection never deletes; a sticker keeps its original `S#` through every stage, **including after a slice is edited and the sheet is rebuilt as `sheet_fixed`**; history lines are only appended; `put` of different bytes under an existing key is refused | `flow/pipeline.py`, `store/assets.py`, `store/repo.py` |
| C8 | **One writer of `result.json` per `out/`** across processes, and read-modify-write is safe inside the server | `runtime/writer_lock.py`, `pipeline._IO_LOCK`, the ~70 call sites of `read_result` / `write_result` (grep -c) — the docs admit the in-process gap: assess how real it is |
| C9 | **A web page the owner visits cannot drive the local server** (Host/Origin guard, `Sec-Fetch-Site`, accounts and tokens; a member reaches only what they own); `/out/` and signed links cannot leave `out/` (symlinks, `..`, encoded forms, Windows paths and drive letters, alternate data streams, short names) | `console/server.py` `_foreign`, `_who`, `_authorize`, `_wait`, `runtime/users.py`, `store/assets.py`, `tests/test_hardening.py`, `tests/test_users.py` |
| C10 | **Secrets**: the Telegram token is never returned or logged; the LLM key is never logged; tracing never sends media bytes or paths outside a generation | `services/telegram.py`, `services/llm.py`, `obs/trace.py` `safe()`, a repo-wide grep for obvious tokens in tracked files |
| C11 | **Idempotency**: the same `Idempotency-Key` returns the first answer and runs nothing twice, including under two concurrent identical requests | `console/server.py` `Console.idem`, `runtime/cache.py` locks, tests |
| C12 | **Redis is disposable**: killing Redis mid-run costs cache misses and short-lived state (rate-limit windows, idempotency records, session locks, SSE replay) and falls back to process memory; everything durable is in files and Postgres; the fallback has the same semantics | `runtime/cache.py`, `runtime/events.py`, `tests/test_cache.py` |
| C13 | **Memory is structured, not the history**: every turn starts from the per-subject summary; temporary feedback shapes only the next generation; only explicit statements become lasting preferences; the reducer cannot drop ids | `agent/memory.py`, `agent/graph.py`, `tests/test_agent.py` |
| C14 | **The model's text is never trusted as HTML or as an instruction** (chat rendering, plan prompts, reference content, prompt injection through a sticker name, a user message, an annotation, a search result) | `console/agent.js` (`AIU.md`, `esc`), `agent/graph.py`, `agent/brain.py`, `generation/prompter.py` lint |
| C15 | **The verifier**: 44 checks, thresholds are measured not guessed; `verify.run` turns a crashing check into a BLOCK `verifier_error` instead of raising; which checks have PASS/FAIL fixtures is listed in `HANDOFF.md` (not all do) | `engine/verify.py`, `tests/test_verify.py`, `engine/config.py` comments |
| C16 | **Migrations 001-005 are re-runnable** and never wipe data on re-apply (note `005_vectors.sql`); `db import` and write-through are idempotent | `mirsal/migrations/`, `store/db.py`, `store/repo.py` |
| C17 | **Pool search never returns "the closest junk"**: a quality gate returns nothing for what does not exist. `search_text` embeds `subject — action — key — emoji — style` and **never the file name** (a name with a date and a fingerprint would only add noise); `subject` and `action` are separate vector columns with weights. | `store/pool.py` (`index_row`, `_subject_action`, `search`), `docs/measurements.md`, `tests/test_pool.py` |
| C18 | **The agentic creator can always get past a block**: a run that stops on a Python block asks `tools.allowable` and offers `creator_allow` for exactly the overridable ones; a technical block offers nothing and says why; the pictures are attached to the message. Judge whether any other surface is a dead end. | `agent/creator.py` (`_stop_blocked`, `resume`), `agent/graph.py` (`n_creator`, `_creator_say`) |
| C19 | **The particle model matches the plan**: one set belongs to pack(s) or stands alone, is saved by an explicit *Use as particle set*, supports generate-more / rename / duplicate / assign / delete+restore, and is never deleted by a click. Phases 1-4 are built; only Telegram delivery is open. Check that a render is FAILED only for a Telegram limit and that *Generate more* never deletes or overwrites a cell. | `flow/particle_sets.py`, `flow/effects.py`, `console/server.py` `_particles`, `console/particles.js`, `docs/particles_plan.md` §6 |
| C20 | **Particles are cropped sprites, not stickers**; a particle batch's cells cannot be added to a pack as stickers; after a slice is edited the batch is rebuilt as **one sheet** with the same layout and the same `S#`; the rebuilt sheet is what later turns see. | `flow/particle_sets.py` (crop), `flow/pipeline.py` (`sheet_fixed`), `console/server.py` (`recut_particles`), `agent/editroute.py` |
| C21 | **The edit router classifies before it generates**: a transformation or cleaning of one slice goes to the **editor** (Save returns to the AI, not the Studio); a `tweak` or a new `action` sends the current sheet as the picture; a `redesign` sends **no picture** and reuses the prompt with the new subject; one slice alone goes as its own cell with the 400px minimum said out loud; an unsupported request is refused rather than improvised. | `agent/editroute.py` (`classify_edit`, `plan_for`, `unsupported`, `REF_CLAUSES`), `agent/graph.py` (`n_editroute`, `n_unsupported`) |
| C22 | **Vision consent is state, never a turn**: allowing or refusing writes session state and emits no card and no assistant message; the next turn carries the permission and acknowledges it once. The first message offers *Create it* + a right-hand *Allow AI Vision*, with no "Not yet" and no "Keep it off". | `agent/graph.py`, `agent/memory.py`, `console/agent.js` |
| C23 | **One click, one meaning**: the sheet cell, the tile's `x` and `+`, and "Use it anyway" are the same decision through one handler; no sheet click opens a tile; a sticker's id is never part of its name. | `console/generate.js` (`gcell`, `issueSvg`, `blockedBox`), `console/{agent,particles,packs}.js` |
| C24 | **No dead stubs and no dead ends**: every control in the UI has a backend behind it, every setting is read, and a rejection is never a bare word with no picture and no override. A UI that shows a disabled or ignored control is a finding. | every `data-act` in `console/*.js` has a handler (the `tests/test_js.py` guard), `docs/design.md` §9 |
| C25 | **`python -m mirsal doctor` is the single health check** and every area extends it; a new area that does not report itself there is a finding. | `runtime/doctor.py`, `docs/*.md` |
| C26 | **The API contract is stable and honestly documented**: list every route the server answers and diff against `docs/api.md` and `console/openapi.py`; `tests/test_openapi.py` probes every documented route for the no-route wording. | `console/server.py`, `console/openapi.py`, `docs/api.md`, `tests/test_openapi.py`, `tests/test_api_contract.py` |

## 6. Where to hunt (the review's real value)

Think like an attacker, a tired operator and a new maintainer. Be specific; skip
generic advice. Name the file and the line.

- **Money**: any path (HTTP, chat, CLI, retry, timeout, double-click, a second
  tab, a crash between "ticket stored" and "wait") that can produce a second paid
  call, a paid call without a stored ticket, or a spend the daily cap does not see.
  Include the particle and burst paths, not just the sheet path.
- **Gates and truth**: any way a sticker reaches the final pack or Telegram
  without the human approvals; any status mirrored wrongly between `result.json`,
  Postgres and the UI; stale-read races between request threads and the pipeline
  thread; a rebuilt `sheet_fixed` drifting from the rows it was built from.
- **Agent**: intent misrouting that costs money or changes the wrong sticker
  ("make number 3 happier" resolving to another generation after "go back to the
  previous one"); the new edit router misclassifying (what happens to "make it
  happier" with no sticker named, or to an edit of a *pack* rather than a sheet);
  session lock edge cases (crash while locked, TTL expiry mid-turn, two browser
  tabs); memory contamination across sessions or subjects; unbounded growth
  (messages, steps, streams, caches).
- **API design**: stable JSON contracts, error shapes, status codes, ids
  everywhere, pagination, versioning, what an integrator would trip over. Is
  `docs/api.md` true today? Would it survive the FastAPI migration in `plan.md` §3
  without a byte changing — and is the hand-written spec drift-tested well enough
  to be replaced by a generated one?
- **Data model**: the Postgres schema (keys, FKs, indexes, JSONB vs columns),
  `tasks` as the provider join, `model_calls` dedupe by line hash, `sticker_index`
  vectors (768-d, HNSW, gates), the mirror's failure modes.
- **Video/CV**: chroma keying (green/blue detection, spill), the CRF fit, loop
  seam, slot geometry (`inside_slot`, `cross_slot`), sprite cropping for particles
  (does it preserve alpha and the `S#`?), the `sharpness` metric (the owner has
  approved reworking it: say whether it can see softening and what to use
  instead), Windows ffmpeg/VP9 behaviour.
- **Frontend**: accessibility (keyboard, focus, reduced motion, contrast), the
  carousel on touch, polling load, memory leaks (listeners, timers, video
  elements), XSS through any `innerHTML`, class-name collisions between
  `agent.css` and `studio.css`, the rotating glow (reduced-motion), behaviour
  with Redis/Postgres/LM Studio down.
- **Design consistency**: `docs/design.md` requires **one shell and one token set
  per section**. A screen that hand-copies a component's markup instead of reusing
  it will drift — look for that, and for the composer's settings chips appearing
  on a screen where they cannot affect the outcome (a dead stub, rule 6).
- **Operations**: Windows paths with spaces or non-ASCII; clean-clone setup (does
  `README.md` get a new developer to a green `doctor`?); logging and observability;
  backup/restore of `out/`; the "run the suite alone, parallel causes 409 busy"
  constraint — is anything in the code or tests racing?
- **Tests**: what is *not* tested that should be (name 5), tests that cannot fail,
  tests coupled to the developer's machine (a running LM Studio, Docker, a real
  `out/`), flakiness you can reproduce. **Count how many assertions were removed
  in the recent diffs and check each removal was a deliberate contract change
  rather than a relaxed test.**
- **Docs**: statements that are false today (cite both sides), missing docs,
  contradictions between `README.md`, `CLAUDE.md`, `HANDOFF.md` and `docs/`;
  tracker hygiene — `HANDOFF.md` should hold only this session's unfinished work,
  `plan.md` only work not yet started, and a finished item should have been
  deleted from both after being recorded in `docs/`.
- **Product**: is the golden path too heavy for the user it serves? What would you
  cut, merge or reorder? What is the riskiest assumption in the whole design? Is
  the burst proposal (`docs/burst_plan.md`) worth building, and what is the queue
  model it needs?

## 7. Report format (`docs/review-<date>.md`)

```
# Review of Mirsal Builder  <date>  <commit sha>  <branch>
## 1. Verdict (5-8 sentences: ship / ship with changes / do not ship, for which purpose, and the three things that decide it)
## 2. What I ran (commands + result in one line each; what I could not run and why)
## 3. Claims C0-C26 (table: verdict, NEW/PRE-EXISTING if relevant, one-line evidence with path:line)
## 4. Findings (most severe first). For each:
   ID, title, severity (BLOCKER / HIGH / MEDIUM / LOW), label [RAN]/[READ]/[INFER],
   NEW or PRE-EXISTING, where (path:line), what is wrong,
   how to reproduce it in <=5 lines (or why you could not), the fix you recommend
   (concrete), the test that would pin it.
## 5. What is solid (so it is protected from "cleanups")
## 6. Missing: tests, docs, features a v1 needs that nobody listed
## 7. Decisions I would challenge (the owner's choices, with the alternative and the cost of switching)
## 8. The ten changes I would make first, in order, with an effort guess (S/M/L)
```

Severity: **BLOCKER** = money loss, data loss, a bypassed gate, a
remote-triggerable action, or a secret leak. **HIGH** = wrong results or a
security weakness needing a precondition. **MEDIUM** = maintainability or a
realistic failure. **LOW** = polish.

Cap yourself at **25 findings**: if you have more, keep the most severe and list
the rest as one line each in section 6. A short report full of reproduced facts
beats a long one of opinions.

When you are done, reply with the path of the report and the verdict paragraph
only.