# docs/architecture.md — how Mirsal is put together

One page for the whole app: the layers, where the data lives, how one request travels, and how the browser sandbox is wired. Every area has its own doc
with the detail (the table in `CLAUDE.md`); this page only says how they fit. Written 2026-10-10 before the redesign (`docs/redesign_plan.md`), so the
redesign has a map of what it must keep.

## 1. What it is

Mirsal makes **animated Telegram stickers**: an idea becomes a 3×3 (or 2×2) sheet of stills (Nano Banana 2 through the Higgsfield CLI), the stills
are cut and checked, a video sheet of the approved stills is animated (Kling v3.0), each cell becomes a transparent looping WebM, and the approved
stickers become a pack that can be sent to Telegram. A person approves at every gate; Python only blocks what Telegram itself would reject.

Two interfaces sit on one engine (`CLAUDE.md` "Structure"): the **AI chat** (natural language, an agent over the Studio's own functions) and the
**Studio** (explicit controls). Both are **sandboxes** over a JSON API (rule 11): the product is the API; the screens demonstrate it.

## 2. The layers

```
 browser sandbox   console/*.js, index.html, studio.css, agent.css        (one page, one global scope, ACT + RENDER)
        │  JSON over HTTP (+ SSE)                                          docs/api.md, docs/http_route_inventory.md
 HTTP server       console/app.py (FastAPI on uvicorn) ─ adapter ─ console/server.py (the original handler, Console)
        │
 agent             agent/  (LangGraph turn, memory, resolver, creator)   docs/agent-and-chat.md
 services          services/ (Telegram send + chat bot, local/cloud LLM, embeddings, AddCollection export)
        │
 flow              flow/   (the lifecycle: pipeline, gates, groups, imports, particle sets, purge, support, tickets, trending, …)
 generation        generation/ (prompts, plans, styles, jobs, the Higgsfield CLI, model calls, usage)
 media             media/  (the Library: packs, cutout, video projects, export names)
 vision            vision/ (the pre-review judge, naming, captions; never approves)
        │
 engine            engine/ (pure: key, cut, render, video, verify)        never imports psycopg, redis, langgraph or a model client (a test enforces it)
        │
 store / runtime   store/ (Postgres mirror, pool, idempotency)  runtime/ (files, names, atomic writes, the writer lock, Redis cache, users, health)
```

Rules that hold across the layers:
- **Files are the truth, Postgres mirrors them, Redis is disposable.** `out/G###/result.json` is the record of a batch; `store/sync.py` writes it
  through to Postgres (searchable reviews, tasks, assets); `runtime/cache.py` can always be rebuilt.
- **One writer per `out/`** (`runtime/writer_lock.py`): a second `serve` on the same folder refuses to start.
- **Paid calls are explicit** (rule 13): every call is a line in `out/model_calls.jsonl`; tests run with `MIRSAL_NO_REAL_CLI` and fakes.
- **Names are code, not hand-built paths** (rule 9): `runtime/names.py`, `pipeline.gen_dir`, `pipeline.out_path`, `jobs.job_dir`.

## 3. Where the data lives

| place | what | owner |
|---|---|---|
| `inputs/Images_gen`, `inputs/videos_gen` | prepared sheets and videos, `img-NNN-<subject>/` + `vid-NNN-<subject>/` (never renamed) | `flow/sources.py`, `flow/watch.py` |
| `mirsal/out/G###[-label]/` | one batch: `result.json` (stickers, reviews, history, video sheets), `events.jsonl`, `source/` (sheet, keyed, plain cells, originals), `slices/`, `video_sheet/A#/` | `flow/pipeline.py`, `flow/gates.py` |
| `mirsal/out/jobs/J###[-label].json` (+ folder) | one paid job, written at `claim` before waiting | `generation/jobs.py`, `generation/jobqueue.py` |
| `mirsal/out/tasks/` | the external task id of every request (the hard truth of rule 10) | `generation/tasks.py` |
| `mirsal/out/library/library.json` + `files/` | packs and their sticker copies | `media/library.py` |
| `mirsal/out/particles/`, `effects/` | particle sets and effects | `flow/particle_sets.py`, `flow/effects.py` |
| `mirsal/out/trash/` | removed batches and deleted packs, restorable until purged | `flow/batches.py`, `flow/purge.py` |
| `mirsal/out/sessions/`, `profile/` | chat sessions and per-person taste | `agent/memory.py`, `agent/profile.py` |
| `mirsal/out/tickets/`, `faq/` | problems as tickets; the support FAQ | `flow/tickets.py`, `flow/faq.py` |
| `mirsal/out/model_calls.jsonl` | every paid or model call | `generation/model_calls.py` |
| Postgres (`mirsal/migrations/`) | the mirror: generations, stickers, reviews, tasks, assets, job queue, groups, idempotency, support, profiles, pack claims | `store/` |
| Redis | the live event stream and short caches | `runtime/cache.py`, `runtime/events.py` |

## 4. One request, end to end (the golden path, rule 10)

1. **Plan (G1)** — the request becomes a plan: 1-5 tags and a margin per cell (`generation/prompter.py`, `expander.py`, `styles.py`,
   `transformations/`). `POST /api/plan`. Nothing is spent.
2. **Sheet** — a paid job (`generation/jobs.py` → `higgsfield.py`), or a prepared sheet from `inputs/` (free). The task id is written first.
3. **Cut and check (G2)** — `engine/sheet.py` keys and cuts, `engine/verify.py` checks every cell; a sheet-level problem never stops it
   (`pipeline.recut`, "Cut it anyway"). A person approves the stills; every judgement-call block has "Use it anyway" (`POST /api/generations/{id}/allow`).
4. **Video sheet (G3)** — `engine/video_sheet.py` recomposes the approved stills; a paid Kling job animates it (several videos per batch: `video_sheets` A1, A2, …).
5. **Animations (G4)** — `engine/video.py` cuts each cell into a looping WebM and checks every frame; same overrides.
6. **Pack (G5)** — `POST /api/generations/{id}/add` puts the approved stickers into a Library pack; `services/telegram.py` sends it.
7. Every decision is a `reviews` row in Postgres and a `history` line in `result.json`; a sticker keeps its `S#` through every stage.

**How batches relate** (the part the redesign makes visible): a request's batches form a **pack of batches** (`pipeline._packs`: same request,
same person, within 6 h, or an explicit link); each batch has a **family** of variations (redo, edited prompt, joined: `flow/groups.py`); each
batch can hold several **video sheets** (`A1`, `A2`, …, `pick_video`, `remove_video`). Today the Studio shows these in three places (the Earlier
batches column, the variations strip, the Animation tab); `docs/redesign_plan.md` puts them in one project map.

## 5. The HTTP server

`python -m mirsal serve` (`cli.py`) starts `console/app.py`: FastAPI on uvicorn. Routes that existed before FastAPI go through an **adapter** over
the original handler in `console/server.py` (byte-identical answers); routes added since are native FastAPI with pydantic models
(`console/app_models.py`); `console/openapi.py` serves the contract. `serve --lan` adds HTTPS and office accounts (`runtime/users.py`);
`serve --stdlib` keeps the old server for one release. The page (JS, CSS, HTML) is read from disk on every request, the Python only at start
(`Console.stale()` warns when the two differ). Every route: `docs/http_route_inventory.md`; the contract: `docs/api.md`.

## 6. The browser sandbox (`mirsal/mirsal/console/`)

- **One page.** `index.html` holds the shell (`#rail`, `#col2`, `#stage` with one `<section id=s-<screen>>` per screen, `#toast`, `#modal`,
  `#dlg`, `#welcome`) and loads the scripts **in order**; each script must also be in `UI_FILES` (`console/server.py`) or it is a silent 404.
- **One global scope.** The scripts are plain files sharing globals. Two consequences (`docs/design.md` §2): a top-level `const` declared twice
  kills the second script, and **every action lives on one object, `ACT`**: `ACT.<name>=` defines it, `data-act=<name>` on any element calls it
  through one click handler (`app.js`). A later `ACT.<name>=` silently replaces an earlier one (`tests/test_js.py` lists the intentional ones).
  New top-level names carry the file's prefix (`hm`, `sp`, `lv`, …).
- **Router.** `location.hash` (`#/<screen>/<arg>`) → `route()` (`app.js`) shows `#s-<screen>` and calls `RENDER.<screen>(arg)`. `SCREENS`
  lists them; `RAIL` is the left navigation; `RAILOF` maps sub-screens to their rail item; `COL2` says which screens have the second column.
  An empty hash opens Home (`home.js`), and so does the first start of a browser session.
- **Styles.** `studio.css` holds the one token set (`:root`) and every screen's styles with a short prefix; `agent.css` the AI screen's
  (`ag-`, `is-`, `k-`). `tests/test_js.py` holds the type and radius scale.
- **What it can do** — every action, the scripts that draw its button and the server routes it calls: `docs/ui_inventory.md`, generated by
  `mirsal/mirsal/console/inventory.py`. `tests/test_ui_inventory.py` keeps a baseline so no action, screen or route the page uses disappears
  without a recorded new home or Haitham's approval.

Screens today (`RENDER`): home, agent (AI), generate (Studio, `#/studio`), library, pack, chat (a phone preview), create (from a photo),
editor, prepare, animate, export, effects, settings, users, help, history (watch folders).

## 7. Module index

Each line is the module's own first docstring line.

**`engine/`**

- `chroma.py` — Colour-difference chroma key. Shared by the still (sheet) and video paths.
- `config.py` — (settings: EngineConfig)
- `effect_checks.py` — Checks for a particle-effect clip (`engine/particles.py`): is it empty at both ends, does it show a burst, does it stay in its cell, does it move; …
- `effect_video.py` — Particle effects, the video side: a text-only Kling clip (a grid of burst cells on a key-colour screen, each cell empty at the start and at the end) …
- `ffmpeg.py` — ffmpeg helpers (subprocess only). Works on Windows/macOS/Linux: uses PATH ffmpeg, else imageio-ffmpeg's bundled binary.
- `grid.py` — Grid geometry: find where to cut a sticker sheet. Pure (numpy only).
- `particles.py` — Particle burst: a few sprite images -> a 3 s Telegram video-sticker frame sequence. Pure, deterministic, no network.
- `render.py` — Scale + white outline + report, shared by stills and video frames.
- `sheet.py` — Part A: rows x cols sheet (3x3, 2x2, 1x1) -> keyed cells -> 512x512 stickers. Pure: arrays in, results out, never raises per cell.
- `verify.py` — The verifier: ONE catalogue of every check on the golden path (docs/engine-and-studio.md, "The verifier").
- `video.py` — Part B: prepared grid MP4 (3x3 / 2x2 / 1x1) -> transparent looping WEBM per cell. Same keyer as stills, same settings.
- `video_sheet.py` — G3: the video sheet. Re-composes the APPROVED stickers on a flat key-colour canvas, same slot positions as the stills,

**`flow/`**

- `batches.py` — Remove a batch (Haitham, 2026-10-03, "like remove pack"): `out/G###` moves to `out/trash/batches/G###` and Restore moves it back. Nothing is deleted …
- `effects.py` — Particle effects, the lifecycle of one effect `E###` (docs/effects.md).
- `explain.py` — Plain words for a sheet Python could not use (2026-10-02, the falcon sheet G094).
- `faq.py` — The shared FAQ (docs/agent-and-chat.md "Support"): what the support agent may answer from, written from resolved tickets and published by an admin.
- `gates.py` — The golden path's review gates (docs/engine-and-studio.md, checkpoint 1F). The rules live here, in Python, and every phase keeps them:
- `groups.py` — Batch groups (Haitham, 2026-10-04): variations of one idea are ONE family. Earlier batches shows a family as one entry with a strip of its …
- `imports.py` — Bring a file into Mirsal, never twice (Haitham, 2026-10-05: "there should be a way of import with deduplication").
- `measure.py` — Phase 2 step S4: how often does a video made from the normalised video sheet leave its cell?
- `metrics.py` — Quality and timing numbers from what is already on disk: no new bookkeeping, no model, no network.
- `notifications.py` — In-app notifications (docs/agent-and-chat.md "Support"): what reaches a person when an admin answers or resolves their issue.
- `particle_sets.py` — Durable sticker-owned particle sets (`docs/particles.md`).
- `people.py` — Account requests on the office LAN (docs/api.md, Office accounts on the LAN): a sign-up waiting for approval, a forgotten password, a request for more
- `pipeline.py` — Generation lifecycle: 7 stages, each a real step with an event line in out/G00N/events.jsonl.
- `purge.py` — Emptying the trash: the purge of removed batches and deleted packs (Haitham, 2026-10-03: "Cleaning the trash"). Remove batch, Delete pack and a …
- `sources.py` — PhaseDirSource: discovers Haitham's prepared inputs by the inputs/ naming convention (read-only, never renames).
- `sticker_history.py` — The generation history of every sticker of a batch, for the page: one summary per sticker with its decisions grouped by stage.
- `support.py` — Help & Support (docs/agent-and-chat.md "Support"): a person describes a problem, the support agent answers from what is documented, and a person
- `support_kb.py` — What the support agent may read (docs/agent-and-chat.md "Support"): published FAQ entries, the repo's `docs/`, and, for the owner and admins only, …
- `ticket_models.py` — The ticket shapes (docs/tickets_plan.md), pydantic, written once: `flow/tickets.py` validates the local model's draft with them and the native routes
- `tickets.py` — Tickets: every problem is one record of what happened, what the person meant, what the issue is and what should be fixed (docs/tickets_plan.md).
- `trending.py` — Trending (docs/api.md, Office accounts on the LAN, Haitham 2026-10-04: "higgsfield 'trending' style … liked and commented, and use pack in your …
- `user_report.py` — What each person made and spent (the Users dashboard, docs/api.md "Users"): aggregates computed on request from the stores that already exist, …
- `watch.py` — History = the real watch folders (inputs/Images_gen and inputs/videos_gen), with Remove.

**`generation/`**

- `actions.py` — The canonical action bank for export tags (`docs/export to team/mirsal-export-architecture.md` §6): 36 tokens, each with a
- `claims.py` — The pack claim ledger (`docs/export to team/mirsal-export-architecture.md` §10.7): which preset grid each pack session has taken, and which …
- `effect_prompts.py` — Prompts of the particle effects: the text Kling gets for a text-only burst video, built by code from a small plan (template-locked: a model or a …
- `emotions.py` — A wide bank of expressive emotions for the built-in (no-AI) sets. Every entry is (key suffix, label, emoji, motion):
- `expander.py` — Subject -> the full named set. The user asks for `{subject}`; the AI expands it into N distinct, animatable stickers and gives every one its key name,
- `higgsfield.py` — Higgsfield through its CLI (`@higgsfield/cli`): a plain subprocess that prints JSON, so Mirsal can fulfil a job without an MCP session.
- `jobqueue.py` — The durable job queue (Postgres `job_queue`, migration 007) and the workers that drain it.
- `jobs.py` — Phase 2: jobs as files. Mirsal writes the job; it is fulfilled by `fulfil()` (the Higgsfield CLI, see generation/higgsfield.py) or by an operator
- `model_calls.py` — Every paid or model call is one line in out/model_calls.jsonl (what, parameters, latency,
- `model_catalog.py` — The models a user can pick, and the selections each one offers. Pure data + validation: the UI draws it, the fulfiller (jobs.fulfil) calls
- `prompter.py` — Stub of the AI prompter agent (Phase 1 = deterministic, plain JSON, no LLM/pydantic/langgraph).
- `recovery.py` — Explicit human recovery: look locally, check once, continue the ticket, or buy a new request.
- `spelling.py` — Obvious misspellings of the words a request keeps ("camel in lamborgini" -> "camel in Lamborghini"), so the plan, its cells and the card say the …
- `styles.py` — Style presets: what the user picks next to the subject. `phrase` is the text the saved templates plug into the prompt (the word
- `tasks.py` — The Inbox backend (checkpoint 1G): Haitham's manual loop until Phase 3 automates generation.
- `usage.py` — What was spent and on which models: a read-only roll-up of out/model_calls.jsonl (the ledger every paid or model call appends to) and

**`media/`**

- `export_names.py` — Export-as-ZIP display names (`docs/export to team/mirsal-export-architecture.md` §1-2):
- `library.py` — Sticker library: packs, imported/edited stickers, photo cutout, pack export (desktop builder).
- `matte.py` — Learned background matte (optional provider). U2-Net / IS-Net through onnxruntime and nothing else (no rembg, torch or network).
- `video_project.py` — Video / GIF sticker projects (checkpoint 1E). One StickerProject per imported video or GIF, kept on disk under

**`transformations/`**

- `banana.py` — The banana lexicon for `subject_as_target` ("dog as banana"): sharper wording for the three required cells and for the body. A flavour only changes …
- `base.py` — Transformation templates: "dog as banana" is ONE new character (a dog that IS a banana), not a dog next to a banana.
- `registry.py` — The registry: which templates exist, which lexicon sharpens a target, and the one function the planner calls.

**`vision/`**

- `consent.py` — Consent for AI vision: "Allow AI vision of generated media?", asked ONCE (per chat session, per browser), never per run.
- `effect_plan.py` — The smart step of a particle effect: what bursts out of THIS sticker.
- `judge.py` — VisionJudge: a pre-reviewer, never the gate.
- `naming.py` — Better names for stickers, proposed after looking at the picture (2026-10-02).
- `recovery.py` — Bounded recovery after the judge (pure rules, no model, no spend): what SHOULD be regenerated, and when to stop.
- `transcribe.py` — Per-frame vision: one caption per cell of a sheet, grid-agnostic (2x2, 3x3, anything `result.json` says), stored with the sticker.

**`agent/`**

- `brain.py` — The model behind the agent: a few SMALL, schema-checked calls. The rules decide first (resolver.py); the model only classifies what the
- `creator.py` — The agentic creator: ONE go-ahead from a request to a sticker pack on Telegram (Haitham, 2026-10-02).
- `editroute.py` — What an edit request MEANS, by rules (the UI/UX spec P11-P13). Pure: no model, no files, no network.
- `graph.py` — The agent graph (LangGraph): one turn of the chat as a small state machine over the Studio's engine.
- `memory.py` — Sessions and memory.
- `profile.py` — What the chat learns about a person's taste, across chats (`out/profile/<user>.json`).
- `refine.py` — Feedback about a whole subject becomes a change to the prompt that made it: "the cherries were so realistic, make them more cartoonish; the banana …
- `resolver.py` — Intent rules and the reference resolver. DETERMINISTIC FIRST: regex and rules handle numbers, `#3`, ordinals, lists ("2 and 7"),
- `stages.py` — How far a NEW chat request goes (Haitham, 2026-10-09): the chat's stage, one of four, picked in the chat bar like a reasoning-level picker.
- `subjects.py` — Several subjects in one request: "create three sticker packs of fruits" is a NEW request that names a count and a category, not one subject.
- `tools.py` — What the agent can DO: a small interface over the Studio's own engine, so "the chat's backend is the Studio" is literally true.

**`services/`**

- `admin_bot.py` — Haitham's admin channel in the Mirsal Telegram bot (docs/api.md, Office accounts on the LAN): the bot already configured in Settings (token + …
- `collection.py` — Export a pack (or one Studio batch) to the AddCollection API, an external emoji CMS (`docs/Api/AddCollection-API .md`).
- `embed.py` — Text embeddings for the sticker pool (Phase 3B).
- `llm.py` — A minimal chat-completions client over urllib (no new dependency) for two backends that speak the same protocol:
- `telegram.py` — Send a Library pack to Telegram (checkpoint 1H, docs/engine-and-studio.md Part H).
- `tg_chat.py` — The AI chat in Telegram (Haitham, 2026-10-09: "can the Telegram bot NOW be exactly like the AI chat"). The same bot as the admin cards

**`store/`**

- `assets.py` — The AssetStore seam (Phase 3A, A3): how the rest of the program reaches a stored file.
- `db.py` — psycopg 3 connection. DATABASE_URL from the environment or mirsal/.env (git-ignored).
- `idem.py` — The durable half of idempotency: `Idempotency-Key` answers kept in Postgres for 24 hours (migration 008), behind the cache.
- `pool.py` — Phase 3B pool: every APPROVED sticker is indexed by topic; a request first fetches matching stickers (free, instant) and only the missing
- `purge_rows.py` — The database half of purging a batch (flow/purge.py is the caller): what a purge would remove from Postgres, and removing it.
- `repo.py` — Phase 3A repository: save_generation() is one transaction (generation + stickers + assets +
- `sync.py` — Best-effort write-through: pipeline.write_result() calls sync_result(), which persists the

**`runtime/`**

- `activity.py` — The server's terminal, in a few words per thing that happened (Haitham, 2026-10-09: "generating, received, exported, error", not every request).
- `atomic.py` — One way to replace a file: write a temp file that is UNIQUE to this write (process, thread, counter) next to it, then `os.replace` it over the target.
- `cache.py` — Redis, introduced in Phase 4: fast and DISPOSABLE. Postgres and the files are the truth; everything here can be rebuilt or
- `envfile.py` — mirsal/.env, read the way every dotenv reader reads it: `KEY=value`, optional quotes, and a trailing ` # comment` is a comment, not part of the value.
- `events.py` — The live event stream of a generation (Phase 4 Redis, read by Phase 5's SSE).
- `health.py` — One place that answers "what is this app connected to and is it healthy": Postgres (and whether write-through is failing), Redis,
- `names.py` — ONE naming convention for every media file Mirsal makes (Haitham, 2026-10-02).
- `net.py` — The names this machine answers to on the office network (docs/api.md, Office accounts on the LAN): its LAN addresses, its host name, and …
- `paths.py` — Path config. Cross-platform (pathlib only). Override with env vars MIRSAL_INPUT / MIRSAL_OUT.
- `users.py` — Users and tokens (Phase 5C): who is calling, and what they may see.
- `writer_lock.py` — One writer of result.json per out/ folder, across processes.

**`obs/`**

- `scrub.py` — Free text that may leave this machine (a ticket, an error answer, a console line) never carries where the machine keeps its files.

**`console/`**

- `app.py` — The HTTP server: FastAPI on uvicorn.
- `app_models.py` — The pydantic models of the NATIVE FastAPI routes (console/app.py). Existing routes keep their dict shapes behind the adapter; every route added after …
- `inventory.py` — What the browser sandbox can DO, read from its own scripts (docs/ui_inventory.md): every action (`ACT.<name>=` in console/*.js), the
- `openapi.py` — The HTTP contract as an OpenAPI 3.1 document, served at GET /api/openapi.json and turned into TypeScript types by `python -m mirsal openapi --ts …
- `placeholders.py` — Placeholder art for the Studio until real images are dropped into console/assets/styles/ and console/assets/vendors/.
- `server.py` — Lifecycle Console server: stdlib http.server + one index.html. Binds 127.0.0.1. One background job at a time.

## 8. Where to read more

`README.md` (index), `CLAUDE.md` (rules and the routing table), `run.md` (how to run), `docs/testing.md` (which tests a change earns),
`docs/dev-notes.md` (guardrails and quirks), and the area docs it routes to.
