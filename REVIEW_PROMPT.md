# REVIEW PROMPT: independent audit of Mirsal Builder (give this whole file to the reviewing LLM)

You are an independent senior reviewer: a staff-level engineer who also understands product strategy, computer vision / video pipelines, and the Telegram sticker platform. You have read/execute access to this repository (`G:\Haitham\VsCode\Mirsal-Builder`, Windows 11; macOS also supported). Your job is to audit the project, its plan, and its next phases, and to write **one file: `report.md` at the repository root**. A different AI (Claude Sonnet 5.5) built most of this under the direction of the owner, Haitham (they/them). The owner wants a **second opinion that is allowed to disagree with the builder**. Flattery has no value. Specific, evidenced, prioritised findings do.

Do not skim. This prompt is long on purpose; read it fully before touching anything.

---

## 0. Hard rules (violating any of these invalidates the review)

1. **Write exactly one file: `report.md` in the repository root.** Do not edit, create, move or delete anything else (code, docs, plans, tests, configs). If you want to propose a change, put it in the report as a diff or snippet. Scratch files go in the OS temp directory, never in the repo.
2. **Secrets.** These files hold or may hold credentials. **Do not open, print, quote, or summarise their contents**, and never copy a secret into the report: `Phase_01/telegram.md` (a Telegram bot token), `mirsal/.env` (Anthropic key, if present), `opencode.json` (an API key), `mirsal/out/telegram.json`, anything under `.git` that you would only read to extract a token. You may state that such a file exists and whether it is git-ignored (`git check-ignore -v <path>`). An older bot token is also in git history (commit `349762b` tracked `Phase_01/telegram.md`; it was untracked later in `8512a41`). You may establish *that* from `git show --stat 349762b` / `git log --stat -- Phase_01/telegram.md` (file names only); never print the file's content from history. Just report "a token is in history, revoke it and consider a scrub" and move on.
3. **Never open or "look at" sticker media** (PNG/WEBP/WEBM/MP4/MOV under `mirsal/out/`, `Phase_01/Images_gen/`, `Phase_01/videos_gen/`, `.playwright-mcp/`, `*.png` screenshots). This is a project rule (`CLAUDE.md` rule 9): sticker quality is judged with validators and metrics, not eyes. You may read JSON metadata (`result.json`, `events.jsonl`, `library.json`), file sizes and `ffprobe` output.
4. **Do not write inside `Phase_01/Images_gen/` or `Phase_01/videos_gen/`** (the owner's inputs; names are final).
5. **No git writes.** No commit, push, checkout of other branches, stash, reset, clean. Reading git history is fine. Do not install anything into the project venv; if you need a tool, say so in the report.
6. **Phase 3 (Postgres) is not started and must not be started.** You may critique its plan; you may not build any of it. The owner decided: Phase 3 starts only after their explicit confirmation.
7. **Do not call paid or external services.** No Telegram API calls, no Anthropic/Higgsfield calls. Everything runs offline (the test suite uses a fake Telegram and a fake model). If you want to judge the live paths, judge them by reading code and tests.
8. **Distinguish what you verified from what you inferred.** Every finding carries one tag: `[RAN]` (you executed it and saw the result), `[READ]` (you read the code/doc and are confident), `[INFER]` (reasoned from partial evidence). Never present `[INFER]` as fact. If a command could not run, say so and why.
9. **Be honest about uncertainty and about your own limits.** "I could not verify X" is a valid and valuable line. Fabricated file paths, line numbers or test results are a firing offence; cite `path:line` only for lines you actually read.

---

## 1. What the product is (so you can judge whether the plan serves it)

**Mirsal Stickers / Mirsal Builder**: a tool that produces high-quality, flashy **animated stickers** (not emoji) for Telegram. Emoji appear only as the ≥1 emoji tag Telegram requires on every sticker. A user types a request ("teddy bear for school"); the system produces a 3×3 (or 2×2) sheet of distinct poses of one character on a flat key colour; Python cuts, keys, scales, outlines and verifies each sticker; an image-to-video model animates a "video sheet" built from the approved stickers; Python slices the video per sticker, checks every frame, encodes **WEBM/VP9 + alpha**; the human approves at every gate; the pack is sent to Telegram in one click.

**Telegram sticker constraints the engine must obey** (also `Phase_01/telegram-plan.md`, Telegram's own docs, the owner's input): video stickers WEBM/VP9 with alpha, ≤256 KB, 512×512 (one side exactly 512, other ≤512), ≤30 FPS, ≤3 s, loop; static PNG/WEBP with transparency, ≤512 KB (the build uses 512×512), every sticker tagged with 1–20 emoji, set names `[a-z0-9_]`, ending `_by_<botusername>`, white stroke recommended on static stickers.

**Two interfaces over one engine** (per `CLAUDE.md`): Creator Mode (explicit controls, deterministic) and Conversational Mode (natural-language, iterative; Phase 4). Never collapse into one monolithic LLM prompt: creative intent → spec → generation → processing → validation → animation → persistence are separate stages. The generation engine must be **deterministic and independently testable** (rule 3).

**Delivery decision (owner, 2026-10-01):** the product ships as an **API / app**. The browser UI in this repo ("Studio", served by a stdlib HTTP server) is a **sandbox/proposal**; an existing `mirsal-builder` front end exists elsewhere. So: the engine, the verifier, the gates and the API shape matter more than UI polish.

---

## 2. The phases and the builder's claimed status (verify these claims; do not trust them)

| Phase | Scope (plan file) | Builder's claim |
|---|---|---|
| **1** | Engine (prepared sheets → key/scale/outline → stickers → WEBM), the verifier (`engine/verify.py`), golden path with 5 review gates G1–G5 (`gates.py`), the Studio UI, Send to Telegram, layered Studio edit, AI subject expansion. Architecture in `Phase_01/README.md`; finish list in `Phase_01/CLAUDE.md`. `phase_01.md` was deleted as done. | **~92–97% done.** Built and tested; left: owner's real-data checks (AI key, colours on real batches), commit/merge decision. |
| **2** | `phase_02.md`: template-locked prompt engine + vision judge + **live generation through the Higgsfield MCP connector** (an "operator" Claude Code session claims jobs from `out/jobs/J###.json`, calls Higgsfield tools, downloads results). Steps S0–S7. | **~15%.** Done early: template-locked prompts (`prompter.py`, `mirsal/prompts/`), the AI expander (`expander.py` + `llm.py`, S5 partly), the normalised video-sheet builder (`engine/video_sheet.py`, S4 partly). **Not started:** S0 (discover the MCP tools; the connector was unauthorised in the build session), jobs, operator loop, vision judge, measurements. |
| **3** | `phase_03.md`: Postgres (durable state, identity, lineage, reviews), LangSmith tracing, semantic sticker pool, photo cutout, CapCut-style text stickers, 3D parallax photos. | **0%** (waits for owner confirmation). Today's state is files: `out/G###/result.json`, `out/library/library.json`, `out/tasks/`. |
| **4** | `phase_04.md`: Redis + LangGraph + creative intelligence (references, slots, annotation, memory). | **0%.** |
| **5** | `phase_05.md`: HTTP API + workers, React frontend, production hardening/export. | **~5%** (the sandbox UI and a parked React app in `mirsal/web/`). |

The owner suspects the phases were worked "quite randomly" and that parts of later phases were adopted early. **Judge that explicitly** (§6.A).

---

## 3. Repository map and reading order

Top level: `CLAUDE.md` (rules; 12 rules, binding), `README.md` (index), `HANDOFF.md` (state + quirks), `phase_02.md` … `phase_05.md`, `Phase_0N/CLAUDE.md` (inputs and review gates per phase), `Phase_01/README.md` (**architecture as built; the most important doc**), `Phase_01/CLAUDE.md` (finish list), `Phase_01/telegram-plan.md` (Telegram's docs), `Phase_02/prompt_samples.md` (owner's golden prompts), `ref/` (UI design spec + mockup; `ref-only.jpg` is not to be viewed), `mirsal/` (the code), `_to_delete/` (old backups; ignore), `opencode.json` (**secret, do not open**).

Code (`mirsal/`): `mirsal/engine/` is the pure engine (numpy/OpenCV + ffmpeg subprocess): `verify.py` (44 checks, 9 stages; thresholds in `config.py`), `video.py` (per-cell animation, `AnimCache`, `_encode_fit`, polite batch), `render.py` (scale + outline/erode `apply_edge`), `chroma.py`, `grid.py`, `sheet.py`, `video_sheet.py`, `ffmpeg.py`, `config.py`. `mirsal/*.py` is the application layer: `pipeline.py` (lifecycle; `result.json` read/write with an in-process lock and retry for Windows; `record_anim`, `recheck_bounds`, `studio_edit_*`, `set_appearance`), `gates.py` (the review rules; `soft_block`, `drop`, `quick_add`), `library.py` (packs, stickers, `encode_frames`), `telegram.py` (Bot API client over urllib; tolerant TLS context), `tasks.py`, `prompter.py`, `expander.py`, `llm.py`, `video_project.py`, `watch.py`, `sources.py`, `matte.py`, `cli.py`. `mirsal/console/` is the sandbox UI: `server.py` (stdlib `ThreadingHTTPServer` bound to 127.0.0.1) and the JS pages (`generate.js` = the Studio, `prepare.js`, `editor.js`, `packs.js`, `app.js`, `telegram.js`, `history.js`), `studio.css`. `mirsal/web/` is a parked React gateway (not served). `mirsal/tests/` is 142 `unittest` tests plus `synth.py` (synthetic sheets/videos) and `fake_telegram.py`. `mirsal/out/` is gitignored runtime data.

**Reading order (do it in this order):** `CLAUDE.md` → `README.md` → `HANDOFF.md` → `Phase_01/README.md` (all of it; ~340 lines, dense) → `Phase_01/CLAUDE.md` → `phase_02.md` (all) → `phase_03.md` (skim the schema and the "hard truth" section, read Exit and Explicitly deferred) → `phase_04.md`, `phase_05.md` (read all) → `Phase_0N/CLAUDE.md` (all four) → then the code, starting with `engine/verify.py`, `gates.py`, `pipeline.py`, `engine/video.py`, `engine/render.py`, `library.py`, `telegram.py`, `console/server.py`, then `generate.js`.

---

## 4. How to run things (all offline)

All commands from `mirsal/` using the project venv (the Anaconda base env has a broken numpy; do not use it):

```
cd G:\Haitham\VsCode\Mirsal-Builder\mirsal
.venv\Scripts\python -m mirsal doctor                                   # health: verifier checks, ffmpeg+VP9, AI key (reports on/off only), TLS, workers
.venv\Scripts\python -m unittest discover -s tests -t .                 # 142 tests, ~2 minutes, expected green
.venv\Scripts\python -m unittest tests.test_verify -v                   # fast, per-check PASS/FAIL fixtures
```

To look at the UI without touching real data: copy one generation folder to a temp dir and serve it on another port:
`set MIRSAL_OUT=<temp dir containing a copy of out\G078>` then `.venv\Scripts\python -m mirsal serve --port 8789`. The owner's own server runs on 8770 against the real `out/`; **do not use or restart it**, and do not point `MIRSAL_OUT` at the real `mirsal/out`. Playwright MCP, if available to you, may drive the page; any screenshot goes to the temp dir and is deleted. Remember rule 3 of §0: looking at the layout is fine, judging sticker art is not.

---

## 5. State of the working tree, and what the builder admits is unverified

- Branch `merge/generate-advanced` (off `main` @ `22d26cc`). A large part of the work may be **uncommitted or committed locally in pieces; nothing is pushed or merged**. Run `git status` and `git log --oneline -15` and report which it is.
- **Not verified live:** the real Anthropic call in `llm.py`/`expander.py` (no key in the build environment; covered only by fake-model tests); anything in Higgsfield (S0 never ran; its tools have not been listed); the colours/hatching on *the owner's real batches* (verified on a staged copy of G078 in headless Chromium).
- **Verified live by the owner:** Telegram: image and video packs arrive in the Telegram app (one click send, deep link). The build had a long chain of "it still fails" reports that were all a **stale server process** (Python loads code once; the UI is read from disk on each load); a banner now warns when the server is older than the files.
- The `sharpness` check (new) and the animation-quality changes were measured on **two cells of one generation (G078)**, no other data. Treat the conclusions as weakly supported and say how you would strengthen them.
- JavaScript has **no automated tests**; the UI was checked by hand in a browser. Python has 142 tests; VP9 output is not byte-stable between runs, so tests assert metrics and checks, not hashes.
- Open known weak spots the builder lists: no server-side job queue (a second request while one runs gets 409 and the client waits); history of a token in git; no auth (localhost-only server); `result.json` is the "database" until Phase 3.

---

## 6. What to review, and the questions you must answer

Work through every area. For each, give findings (§8 format) *and* a one-paragraph verdict. If an area has no findings, say what you checked so the owner knows it was covered.

### A. Plan and phasing (this is the owner's main worry)

1. Is the phase order right (1 engine → 2 live generation → 3 Postgres/pool/photo/text/depth → 4 Redis+LangGraph → 5 API/frontend)? The owner swapped 2 and 3 on 2026-10-01 to get generation first. Argue for or against; propose a better order if you have one. Particularly: is **Postgres before the API** right, or should a thin API + auth come earlier? Is **Redis** justified at all for a product of this scale, and is **LangGraph** over-engineering for what is largely a deterministic pipeline with human gates? Name the simplest architecture that meets the stated goals.
2. For each of phases 2–5: are the acceptance/exit criteria **measurable, falsifiable and sufficient**? Which are vague? Which contradict each other across files (e.g. one phase "hands" something the next does not expect)? Which items are quietly doing two jobs?
3. **Scope drift check:** which items in phases 3–5 were already built under Phase 1 (e.g. AI expansion, the video-sheet normaliser, a sandbox React UI, Telegram sending)? Is anything built that no plan asked for? Is anything the plan says is done *not actually* done (compare plan ticks to code)?
4. Estimate **true completion per phase** with your own numbers and a short justification each (not the builder's). Give a rough remaining-effort estimate in engineer-days and name the **critical path** and the **riskiest unknown** (the builder thinks it is the Higgsfield MCP integration).
5. What is **missing from the plan entirely**? Consider: cost control and budgets per request; rate limits; retries and idempotency of paid generation calls; observability; content moderation / copyrighted characters / real people / trademarked IP in generated stickers; abuse; privacy of user photos (Phase 3C); Arabic and RTL text (Phase 3D); accessibility; backup/restore of `out/`; data migration from files to Postgres; versioning of prompt templates; licensing of the image/video models' outputs; Telegram API limits and bot ToS (sticker-set creation rate limits, set ownership, `by_<bot>` naming); multi-user isolation; deployment target (is "app" a desktop app, a service, a SaaS?).
6. **Strategy:** the owner asked "is this worthy to be SaaS?" and the builder never answered in text. Give a concise, honest answer: who pays, for what, why Telegram specifically, defensibility (the verifier + gates + normalised video sheet?), unit economics (generation cost per pack vs price), the risks (platform dependence, model-provider dependence/ToS, quality variance, copyright), and a cheaper way to test demand before building Phases 3–5.

### B. Architecture and boundaries

1. Does the code actually honour `CLAUDE.md` rule 3 (deterministic, independently testable engine) and the separation intent → spec → generation → processing → validation → animation → persistence? Where do layers leak (e.g. engine importing application code, UI deciding policy, the server doing business logic)?
2. **`result.json` as the database:** read/write path (`pipeline.read_result/write_result/_atomic_write`, `_IO_LOCK`), concurrency between the request threads, the background job thread, `animate_cells` workers and the UI poller. Find real races, lost updates, partial writes, read-modify-write windows (e.g. two threads loading, mutating, and saving different stickers of the same generation). Is the in-process lock enough given a second process (e.g. `python -m mirsal recheck` while the server runs)? Is Windows `os.replace` handled everywhere or only in one place?
3. **The golden path and gates** (`gates.py`, `Phase_01/README.md` "The golden path"): does the state machine allow impossible/contradictory states (e.g. a sticker `APPROVED` at G4 whose still was later `REJECTED`, a pack `APPROVE`d then mutated, `review.anim` values `NONE|PENDING|APPROVED|REJECTED|BLOCKED` mixed with `anim_status` values `NOT_REQUESTED|PROCESSING|READY|FAILED|STALE`)? Is every transition tested? Is the history/event log complete and append-only?
4. **Rule 10 vs the new override.** Rule 10 says "Python's blocks are final". The builder introduced `gates.soft_block` / *Include anyway*: an animation whose only failures are **WARN**-severity (`inside_frame`: the character leaves its cell) is switched off by default (`review.anim = BLOCKED`) but a human can approve it. Is that consistent with rule 10, or is it a hole? Is "BLOCKED" the right name/state for something overridable? What are the failure modes (a human overrides and a clipped sticker ships)? Should the pack gate (G5) re-check?
5. **The operator-session design for Higgsfield** (`phase_02.md`, "The operator loop"; jobs as `out/jobs/J###.json` with claim/ticket/done/fail; a Claude Code session with the MCP connector acts as the worker): is this a sound design for a product, or a development-time hack that must not survive into Phase 5? What breaks when the session dies mid-job, when two operators run, when credits run out, when the MCP tool returns asynchronously, when the tool schema changes? Is the seam (`GenOutput`, provider interface) clean enough that a real HTTP provider (Higgsfield API, Replicate, fal, Runway, Veo, Kling, etc.) can replace it without touching the engine? Is "MCP connector = a tool of an interactive session, not an HTTP API" a fatal flaw for a delivered product? Be concrete.
6. **Phase 3 schema** (`phase_03.md` `001_init.sql`, `002_models.sql`): normalisation, keys, indexes, JSONB vs columns, migration of existing `out/` data, the "hard truth" lookup (`external_task_id` → `tasks` row → `name_key`), the `reviews` table, lineage. Would you change it before it is built? Are there design errors that will be expensive after data exists?
7. Phase 4/5 designs: graph state vs Postgres vs Redis (source of truth?), SSE/Last-Event-ID, worker model, idempotency keys, signed URLs, auth. Anything that is infeasible, redundant, or contradicts earlier phases?

### C. Correctness of the core engine

1. **The verifier** (`engine/verify.py`, 44 checks): for each stage, is every check (a) correct, (b) at the right severity (BLOCK vs WARN), (c) tested with both a PASS and a FAIL fixture (`tests/test_verify.py`), (d) free of obvious false positives/negatives on real data? The thresholds in `config.py` were "measured on the 10 real sheets"; challenge that sample size. Look hard at: `inside_cell`, `inside_slot`, `inside_frame`, `cross_slot`, `no_spill`, `holes`, `single_subject`, `duplicate_cell`, `identity_kept`, `loop_seam`, `alpha_stable`, `layout_match`, `blank_slots_stay_empty`, `telegram_*`. Is there a way for a bad sticker to pass (or a good one to be blocked) that the tests do not cover?
2. **The new `sharpness` check/metric** (`engine/video.py: edge_energy`, `_finish`; `verify.sharpness`): metric = mean luminance gradient (Sobel magnitude) over alpha>8 pixels of the first 4 *decoded* frames divided by the same on the *encoder input* frames. The builder observed ratios of 1.00–1.05. **A ratio above 1 means the metric rewards compression blocking/ringing**, so it cannot detect softening reliably. Is the metric valid at all? Propose a better one (SSIM/MS-SSIM or LPIPS-free alternatives, edge-spread-function width, gradient *correlation* rather than energy ratio, alpha-edge ramp width) and say how to calibrate a threshold without eyes on media.
3. **Animation pipeline** (`engine/video.py`, `render.py`, `ffmpeg.py`): one transform per clip, bicubic upscale (new), `apply_edge` (erode then dilate-blur outline, ROI-only), loop closing (`close_loop`, `loop_seam`), CRF ladder `(30,34,38,42,46,50,54,58,62)` with a fit that starts at a **module-global hint** `_CRF_HINT` shared by parallel worker threads (and now by `library.encode_frames`). Is that global a correctness or reproducibility problem (not just performance)? Does the fit always produce the *best* crf under 256 KB, or can the walk stop at a non-monotonic local result (file size is not strictly monotonic in CRF for VP9)? Is `-deadline good -cpu-used 4 -row-mt 1` sensible? Should two-pass be used? Is `yuva420p` chroma subsampling the real source of edge softness? Are the measured "kept" ratios consistent with that? Is the alpha plane encoded at the same quality as the colour plane, and does Telegram care?
4. **Cache** (`AnimCache`): key = sha1 of `[CACHE_VERSION, VERIFY_VERSION, asdict(cfg) without workers, parts]`, `parts` includes the source file's stat. Can a stale or wrong result be served (e.g. same source stat, different cell geometry from a regenerated grid; edge settings stored on the generation but not in `cfg`; ffmpeg version change; code change without a version bump)? Is `put` atomic? Can two workers write the same key?
5. **Windows-specific robustness:** WinError 5 on `os.replace` (fixed with lock+retry), below-normal process priority (`_Polite`, `LOW_PRIORITY`), OpenCV thread limits, subprocess handling, path length, file locks held by the browser `<video>` element. Anything still fragile?
6. **Studio layered edit** (`pipeline.studio_edit_open/commit`, `edit_still`, `video_project.py`, `console/prepare.js`): one edit re-renders the animation *and* composites the same layers onto the original still; originals kept once in `source/orig/`; pack copies refreshed via `Library.refresh_from_generation`. Look for: overlay PNGs baked in the browser trusted by the server (size limits, decompression bombs, alpha handling), non-idempotent re-edits, divergence between the still and the animation, the library/pack copy desync, and failure halfway (animation replaced, still not).
7. **Telegram client** (`telegram.py`): TLS (`_ssl_context` falls back to loading certificates one at a time when `create_default_context()` raises on a malformed Windows store entry; verification stays `CERT_REQUIRED`/`check_hostname` — confirm this, and say whether skipping bad certs weakens anything), token handling (stored in `out/telegram.json`, plain text, gitignored), error mapping, set-name rules, rate limits and retries on 429, large-pack batching, partial failure and resume, the owner notification message, deep link correctness, `replace` vs `add` semantics when a still and its animation exist (`replace_static_with_animated`).
8. **AI expander** (`expander.py`, `llm.py`): prompt design, JSON extraction (`re.search(r"\{.*\}", ...)` greedy), lint rules, the single repair round, temperature, model default (`claude-sonnet-5-5`), key loading from `mirsal/.env` into `os.environ` (process-wide side effect), error messages never containing the key (check `replace(key, ...)` coverage), prompt-injection through the user's request into labels/tags/emoji that are later written into prompts and file/pack names (path or set-name injection?), Arabic/Arabizi handling, cost/latency without a cache, timeouts.

### D. Security and privacy (local tool today, a service later)

1. `console/server.py`: binds 127.0.0.1 but has **no authentication, no Origin/Host check and no CSRF protection** (confirm). Any web page the owner visits can `fetch('http://127.0.0.1:8770/api/...')` (simple POSTs with JSON bodies, DNS rebinding). Which endpoints are dangerous (delete, trash/restore, `/api/telegram` token set, file paths in requests)? What is the minimum fix?
2. Path handling for `/out/…`, `/src/…`, uploads, `name` parameters, pack/sticker ids, `names` passthrough on Add (user-controlled names become file names or Telegram titles), zip export, trash/restore (watch folders). Look for traversal, absolute-path injection, reserved Windows names, over-long names, symlinks.
3. Request body limits and memory (`Content-Length` handling, base64 PNG overlays, large video uploads read into memory), the single-job lock and denial of service by the owner's own browser.
4. XSS in `console/*.js`: the pages build HTML with template strings and `innerHTML`; verify every untrusted string (sticker names, prompts, tags, error text from the server/Telegram/LLM, file names) goes through `esc()`. Look at the new code in `generate.js` (issue captions, legend, detail modal, Edge dialog) and at `title="…"` attributes.
5. Secrets hygiene: what is tracked vs ignored (`git ls-files`, `git check-ignore`), `.env` loading, tokens in logs/events/history/`result.json`, the token in git history (commit `349762b`, `Phase_01/telegram.md` was later untracked), `opencode.json`. Give a prioritised remediation (revoke, scrub with a history rewrite and force-push only on the owner's explicit say-so, secret scanning in CI).
6. For the future service: what must change before anyone else's photos/prompts touch this (auth, tenancy, signed URLs, quotas, PII handling for Phase 3C photos, retention).

### E. UX / product behaviour of the Studio (sandbox, but it encodes product decisions)

1. The five-step header (Request → Prompt → Stickers → Animation → Pack) and the gate counts: does the UI correctly reflect the golden path, or does it hide states (e.g. what "kept/dropped/blocked/out of bounds (off)" mean)?
2. **Issue colour system** (new): orange out of bounds, purple bad green screen, yellow bad loop, pink look/motion, blue file/Telegram limits, red dropped/blocked; same colour on tile, chip, in-place hatch over the cell on both the green-screen sheet and the video sheet (hatch = not in the set, dashed = kept with a check), legend. Is it accessible (colour-blind users, contrast of yellow, reliance on colour alone)? Is the mapping of every verifier check id to a category right (`CATOF` in `generate.js`)? What happens for an id not in the map? Is "hard before soft" ordering of the primary colour sensible?
3. *Include anyway*, *Drop*, *Bring back* semantics; re-animation resetting decisions; the `STALE` flow after changing the Edge (outline/trim) — does the user always know what to do next?
4. Cognitive load and error recovery: busy 409 handling, the stale-server banner, long operations without progress, destructive actions (bulk delete, trash/restore).
5. Is anything shipped as a control without a working backend (rule 6: **no dead stubs**)? Find any.

### F. Tests

1. Map tests to risks. Which critical behaviours have **no** test (list them)? Which tests are tautological (assert the implementation back), time-dependent, port- or ordering-dependent, or slow for little value (the suite takes ~2 min)?
2. Run the suite. Report pass/fail counts, duration, and any warnings (there are `ResourceWarning: unclosed socket` noise lines; are they harmless leaks in test servers or a real leak in the server?). Re-run once to look for flakiness.
3. JS has no tests: what is the smallest, cheapest test setup that would have caught the bugs the builder hit (an unquoted SVG attribute swallowing `/>`, CSS specificity hiding a background, a stale-state race)?
4. Is there a golden/regression corpus for the verifier (known-bad and known-good stickers with expected verdicts, stored as metadata not media)? If not, design it.

### G. Documentation and process

1. Spot-check the claims in `Phase_01/README.md`, `HANDOFF.md`, `phase_02.md` against the code. Report every **drift** you find (a function, route, field, count, default, file path or command that no longer exists or behaves differently). Use the claims table in §7 as a start, then find ten more yourself.
2. Contradictions between `CLAUDE.md` rules and what the plans/code do. Stale text. Duplicated sources of truth. Is the doc set (root `README.md` index, `HANDOFF.md`, `Phase_01/README.md` architecture, `Phase_01/CLAUDE.md` finish list, `phase_0N.md` plans, `Phase_0N/CLAUDE.md` inputs/gates) navigable by a new engineer or a fresh LLM in 30 minutes? What would you cut?
3. The process rules (plans are hand-off, README is architecture, a plan item is deleted only after the owner approves, docs are updated at every major step): are they followed? Is "Updating a plan means enhancing it, never shrinking it" creating bloat (phase_03.md is ~700 lines)?

### H. Performance and resource use

The owner's PC hangs during batch animation. The builder measured: ~5 s CPU per sticker (35% rendering frames, 40% VP9 encode, 12% loop check, 7% ffmpeg start, 8% read+key) and made the batch "polite" (below-normal priority, 2 OpenCV threads, default workers = half the cores up to 6, result cache). Challenge the diagnosis and the fix. Is there a fundamentally cheaper design (render at 512 only once, avoid a full-frame float32 pipeline, encode with hardware, reduce frames, share work across stickers on one sheet, GPU, process pool vs threads given the GIL and OpenCV releasing it)? Where is memory spent (n frames × 512×512×4 as float32/uint8 copies × workers)? What is the worst-case peak memory with 6 workers?

---

## 7. Claims to verify (start list; add your own)

For each: confirm / refute / partially, with the evidence and the tag `[RAN]`/`[READ]`/`[INFER]`.

1. `python -m mirsal doctor` reports 44 checks over 9 stages, verifier v2. 
2. The full test suite is 142 tests and passes in about 2 minutes.
3. `gates.soft_block(s)` is true only if the animation exists and **every** failed check in `anim_report` has severity WARN; approving a sticker blocked by a real BLOCK check returns HTTP 409. (`tests/test_console.py::test_a_soft_blocked_animation_can_be_included_anyway_but_a_real_block_cannot`)
4. `set_appearance` re-renders only stickers that are READY, not edited, and have a `source/plain/S#.png`; marks every sticker that has a `webm` as `STALE`, resets `review.anim` to `NONE`, and never writes a file the verifier BLOCKs.
5. `AnimCache.key` changes when `CACHE_VERSION`, `VERIFY_VERSION` or any `EngineConfig` field (except `anim_workers`) changes.
6. `engine/render.render_sticker` upscales with `INTER_CUBIC`, downscales with `INTER_AREA`, and clips overshoot (alpha to [0,1]; colour via the later `np.clip`). Does premultiplied bicubic overshoot ever produce a visible halo, and does the `despill` step see it?
7. `_encode_fit` returns the lowest crf of the ladder that fits 256 KB *assuming monotonic size*; it then updates the global `_CRF_HINT`.
8. `library.encode_frames` (webm branch) calls `_encode_fit`; the WebP/GIF branches keep their own ladders.
9. `record_anim` sets `review.anim = BLOCKED` when `inside_frame` fails on a READY animation; `recheck_bounds` does the same retroactively and marks `bounds_checked`.
10. `console/server.py` has no Origin/Host/CSRF check; it binds only to 127.0.0.1; a second job gets 409.
11. The Telegram client never sends or logs the bot token in a URL that ends up in `events.jsonl`/`result.json`/error messages shown in the UI (the Bot API puts the token in the URL path: check every exception path).
12. `Phase_01/telegram.md` is git-ignored and untracked now, but `git log --all` still contains a token (`349762b`).
13. The `mirsal/web/` React app is not served by `python -m mirsal serve` (the server serves `console/` only).
14. `phase_02.md`'s "What exists already (do not rebuild)" list matches the code (e.g. `build_video_sheet`, `measure-cells` — the builder believes `measure-cells` is **not yet** a CLI command; check `cli.py`).
15. Every verifier check id in `verify.py` has an entry in `CATOF` (`generate.js`) or falls back sensibly.
16. `CLAUDE.md` rule 9's naming convention (`img-NNN-<subject>/`, `vid-NNN-<subject>/`; outputs `<media>-<NNN>-<task_slug>-<key>.<ext>`) is what the code produces; watch-folder names are never renamed by the app.
17. Library bulk delete, replace-still-with-animated, and rename keep `file_name` metadata equal to the generator's name (e.g. `img-027-generic_emojis-generic_emojis_laughing`).
18. The `STALE`/edge flow cannot leave a sticker `READY` with the old edge.

---

## 8. Format of `report.md` (follow exactly)

```
# Mirsal Builder: independent review (<date>, reviewer: <your model name>)

## 0. Executive summary            (≤ 20 lines: verdict, the 5 things that matter most, and whether the owner should continue Phase 1 / start Phase 2 / change the plan)
## 1. Scope, method, limits        (what you read, ran, could not run; git state; time spent)
## 2. Phase scoreboard             (table: phase | builder's % | your % | confidence | why | biggest risk | remaining effort)
## 3. Top findings                 (the 10–15 highest-priority findings, ranked; each in the template below)
## 4. Findings by area A–H         (every finding, grouped; same template; plus a 1-paragraph area verdict)
## 5. Claims verification table    (the §7 list + your additions: claim | verdict | evidence | tag)
## 6. Plan critique and proposed re-plan  (what to cut, merge, reorder, add; a revised phase list with exit criteria; what to do in the next 2 weeks)
## 7. Strategy answer              (the SaaS question, honest and concise; demand test)
## 8. Second opinion on the builder's decisions   (table: decision | agree/disagree/partly | reasoning | what you would do)
## 9. Questions for the owner      (≤ 12, each one blocking a decision, with your recommended default)
## 10. Appendix                    (commands run and results; files read; anything unverifiable)
```

**Finding template:**

```
### F-<area letter><nn>  <one-line title>
Severity: S0 blocker / S1 serious / S2 should fix / S3 nit        Tag: [RAN|READ|INFER]       Effort: XS/S/M/L
Where: path:line (and function)
What: the defect or risk, in 2–4 sentences.
Evidence: the exact code/command/output (short excerpt) that proves it.
Impact: what goes wrong, for whom, and when (a concrete scenario with inputs and result).
Fix: the smallest change that resolves it (a diff or a few lines), and a test that would pin it.
```

Severity scale: **S0** loses/leaks data or secrets, ships a wrong/invalid sticker silently, or makes the plan unachievable; **S1** likely to hurt in normal use or will be expensive to fix later; **S2** real but contained; **S3** polish.

**Section 8 must cover at least these builder decisions** (the owner wants them challenged): (1) *Include anyway* override of WARN-level blocks; (2) finer CRF ladder + bicubic upscale + `sharpness` check, based on two cells; (3) not adopting `-cpu-used 1`; (4) the polite-batch defaults (workers = half the cores ≤ 6, below-normal priority, 2 OpenCV threads); (5) the AnimCache design; (6) swapping Phases 2 and 3 and pulling the AI expander (S5) into Phase 1; (7) using a Claude Code "operator" session with the Higgsfield MCP connector as the generation worker via a file-based job queue; (8) file-based storage (`result.json`) until Phase 3; (9) deleting `phase_01.md` and moving the architecture README into `Phase_01/`; (10) keeping a parked React app instead of deleting it; (11) the tolerant TLS context fallback; (12) one-click Telegram (connect once, send, open the app, the bot also messages the owner); (13) making the sandbox UI the place where product decisions (colour semantics, gates) are encoded; (14) the stale-server banner approach to a recurring failure instead of auto-reload / versioned API; (15) rule 10 "a human approves at every gate, Python's blocks are final" as the core quality model.

---

## 9. Standards for the report

- **Evidence over opinion.** No finding without `path:line` or a command and its output. Quote at most ~8 lines per excerpt.
- **Prioritise ruthlessly.** 12 well-evidenced findings beat 80 nits. Put nits (S3) in one compact list at the end of §4.
- **Quantify.** Prefer numbers (sizes in KB, ms, counts, percentages, thresholds) to adjectives.
- **Be constructive but unsparing.** The owner prefers "this will fail when X; do Y" over diplomacy. Praise only where it changes a decision (e.g. "keep this design, it's the moat").
- **Be self-aware.** If you suspect a finding might be a false positive because you could not run something, say so and lower the severity or tag it `[INFER]`.
- **Length:** as long as needed, no padding; typically 6,000–12,000 words. The executive summary must stand alone.
- **Do not reproduce this prompt** or the project docs in the report. Do not propose rewriting the project in another language or framework unless you can show a concrete failure that justifies it.
- **Finish by** writing `report.md`, then reply in chat with only: the path, the executive-summary verdict in ≤ 5 lines, the count of findings per severity, and anything you could not do.

Begin by running `git status`, `git log --oneline -15`, and `python -m mirsal doctor`, then follow the reading order in §3.
