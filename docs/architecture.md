# docs/architecture.md — how Mirsal is put together

One page for the whole app, then one section per area with the detail that used to live in a hundred files: the layers, where the data lives, how one request travels, and how the browser sandbox is wired. Converged 2026-10-21 (branch `code-audit`); history lives in git.

## 1. What it is

Mirsal makes **animated Telegram stickers**: a new idea defaults to a 2×2 sheet of stills (explicit and existing/imported 3×3 remain supported; Nano Banana 2 through the Higgsfield CLI), the stills
are cut and checked, a video sheet of the approved stills is animated (Kling v3.0), each cell becomes a transparent looping WebM, and the approved
stickers become a pack that can be sent to Telegram. A person approves at every gate; Python only blocks what Telegram itself would reject.

Two interfaces sit on one engine (`CLAUDE.md` "Structure"): the **AI chat** (natural language, an agent over the Studio's own functions) and the
**Studio** (explicit controls). Both are **sandboxes** over a JSON API (rule 11): the product is the API; the screens demonstrate it.

## 2. The layers

```
 browser sandbox   console/ui/{shell,shared,features,styles}, index.html        (one page, one global scope, ACT + RENDER)
        │  JSON over HTTP (+ SSE)                                          docs/api-integration.md, GET /api/openapi.json
 HTTP server       api/app.py (FastAPI on uvicorn) ─ adapter ─ console/server.py (the original handler, Console)
        │
 agent             agent/  (LangGraph turn, memory, resolver, creator)
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

Agent implementation: `agent/graph.py` owns state and public entry points;
`agent/lifecycle/` owns turns, checkpoints, replay and graph construction;
`agent/nodes/` groups intent handlers.

| place | what | owner |
|---|---|---|
| `inputs/Images_gen`, `inputs/videos_gen` | prepared sheets and videos, `img-NNN-<subject>/` + `vid-NNN-<subject>/` (never renamed) | `flow/sources.py`, `flow/watch.py` |
| `mirsal/out/G###[-label]/` | one batch: `result.json` (stickers, reviews, history, video sheets), `events.jsonl`, `source/` (sheet, keyed, plain cells, originals), `slices/`, `video_sheet/A#/` | `flow/pipeline.py`, `flow/gates.py` |
| `mirsal/out/jobs/J###[-label].json` (+ folder) | one paid job, written at `claim` before waiting | `generation/jobs.py`, `generation/jobqueue.py` |
| `mirsal/out/tasks/` | the external task id of every request (the hard truth of rule 10) | `generation/tasks.py` |
| `mirsal/out/library/library.json` + `files/` | packs and their sticker copies | `media/library.py` |
| `mirsal/out/export_resolutions.json` | immutable export interpretation snapshots, keyed by source identity and metadata; file-authoritative, no Postgres mirror yet | `media/export_resolutions.py` |
| `mirsal/out/ai_backend.json` | saved global backend and local/cloud model selections | `services/llm.py` |
| `mirsal/out/particles/`, `effects/` | particle sets and effects | `flow/particle_sets.py`, `flow/effects.py` |
| `mirsal/out/collection_exports/` | one queued AddCollection export each (`<id>.json`: queued → preparing → sending → done/failed) + `collection_exports.jsonl` ledger | `services/collection.py` |
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

**How batches relate**: a request's batches form a **pack of batches** (`pipeline._packs`: same request,
same person, within 6 h, or an explicit link); each batch has a **family** of variations (redo, edited prompt, joined: `flow/groups.py`); each
batch can hold several **video sheets** (`A1`, `A2`, …, `pick_video`, `remove_video`). The Studio shows these as one project map (`docs/design.md`).

## 5. The HTTP server

`python -m mirsal serve` (`cli.py`) starts `api/app.py`: FastAPI on uvicorn. Routes that existed before FastAPI go through an **adapter** over
the original handler in `console/server.py` (byte-identical answers); routes added since are native FastAPI with pydantic models
(`api/schemas/`, grouped by domain); `api/openapi.py` serves the contract. Native routers live in `api/routers/`, common guards in `api/dependencies.py`, and the last-registered legacy bridge in `api/legacy_adapter.py`. The old console Python entry points remain compatibility imports. `serve --lan` adds HTTPS and office accounts (`runtime/users.py`);
`serve --stdlib` keeps the old server for one release. The page (JS, CSS, HTML) is read from disk on every request, the Python only at start
(`Console.stale()` warns when the two differ). Every route: `GET /api/openapi.json`; the contract: `docs/api-integration.md`.

## 6. The browser sandbox (`mirsal/mirsal/console/ui/`)

- **One page.** `index.html` holds the shell (`#rail`, `#col2`, `#stage` with one `<section id=s-<screen>>` per screen, `#toast`, `#modal`,
  `#dlg`, `#welcome`) and loads the scripts **in order**. `console/ui/manifest.json` maps stable `/ui/` URLs to feature/shared/style folders; `console/assets.py` owns the allowlist and resolver.
- **One global scope.** The scripts are plain files sharing globals. Two consequences: a top-level `const` declared twice
  kills the second script, and **every action lives on one object, `ACT`**: `ACT.<name>=` defines it, `data-act=<name>` on any element calls it
  through one click handler (`app.js`). A later `ACT.<name>=` silently replaces an earlier one (`tests/test_js.py` lists the intentional ones).
  New top-level names carry the file's prefix (`hm`, `sp`, `lv`, …). Chat keeps its state private: `chatCardsInit` and `chatStageInit` receive the core state and callbacks instead of introducing shared state globals.
- **Router.** `location.hash` (`#/<screen>/<arg>`) → `route()` (`app.js`) shows `#s-<screen>` and calls `RENDER.<screen>(arg)`. `SCREENS`
  lists them; `RAIL` is the left navigation; `RAILOF` maps sub-screens to their rail item; `COL2` says which screens have the second column.
  An empty hash opens Home (`home.js`), and so does the first start of a browser session.
- **Styles.** `studio.css` holds the one token set (`:root`) and every screen's styles with a short prefix; `agent.css` the AI screen's
  (`ag-`, `is-`, `k-`). `theme.js` loads before CSS; `theme.css` loads after both stylesheets and maps the dark palette. The persistent top-right sun/moon button and Settings → Appearance select the browser theme (`docs/design.md`). `tests/test_js.py` holds the type and radius scale.
- **What it can do** — every action, the scripts that draw its button and the server routes it calls — is generated by
  `mirsal/mirsal/console/inventory.py`. `tests/test_ui_inventory.py` keeps a baseline (`mirsal/tests/data/ui_baseline.json`) so no action, screen or route the page uses disappears
  without a recorded new home or Haitham's approval. The baseline is never regenerated during the redesign.

Feature files retain the existing function, action and route names:

Studio extensions register a section in `GSTUDIO` with an eligibility predicate,
body presenter, step data and insertion anchor. `studio-core.js` owns rendering
and numbering; Reactions no longer replaces `gbodyHtml`/`stepsHtml` or parses
rendered button HTML.

`ui/shared/lifecycle.js` owns the shell's `ROUTELIFE` registry. Feature `routeOwner` scopes cancel their
timer and advance a request version before navigation, then enter only matching
routes. Reactions' Studio watcher and saved-set polling use these scopes rather
than an always-running interval. Earlier reads cannot redraw a new route;
cached records and pending edits survive navigation.

| Files | Responsibility |
|---|---|
| `app.js`, `library.js`, `settings.js` | shared shell/router; Library; system settings and Appearance |
| `studio-core.js` | Studio state, polling, toolbar and journey |
| `studio-tiles.js` | tiles, checks, issue overlays and override queue |
| `studio-sheet.js` | sheet/video panels and analysis dialogs |
| `studio-prompt.js` | Prompt tab and pre-batch draft |
| `studio-animate.js` | animation controls and Add-to-pack wizard |
| `studio-panel.js` | sticker detail panel |
| `agent.js` | pure exported `AIU` helpers, usable under Node |
| `chat-cards.js`, `chat-stage.js`, `chat-core.js` | cards/carousels; stage/settings controls; session state, turns and polling |

The former `generate.js` is removed. Studio feature files share the original globals; the chat factories load before `chat-core.js` initializes them. Dependencies are kept in page order:

```
theme.js → app.js → library.js → settings.js → studio-core.js
studio-tiles.js → studio-sheet.js → studio-prompt.js → studio-animate.js → studio-panel.js
sheet-recovery.js → job-recovery.js → live.js → composer.js → imports.js
history.js → telegram.js → packs.js → editor.js → chat.js
agent.js → chat-cards.js → chat-stage.js → chat-core.js → prepare.js
effects.js → reactions.js → particles.js → projmap.js → trash.js → tickets.js
support.js → home.js → animate.js → welcome.js → trending.js
users.js → auth.js
```

Source-reading tests use `tests/js/console_source.js` to resolve legacy logical groups and parse statements with vendored Acorn; VM tests execute the actual feature files.

Screens today (`RENDER`): home, agent (AI), generate (Studio, `#/studio`), library, pack, chat (a phone preview), create (from a photo),
editor, prepare, animate, export, effects (the Studio's particle editor), reactions (Reaction effects: one bank emoji to Lottie), settings, users, help, history (watch folders).

## 7. Module index

Each line is the module's own first docstring line.

**`engine/`**

- `chroma.py` — Colour-difference chroma key. Shared by the still (sheet) and video paths.
- `config.py` — (settings: EngineConfig)
- `effect_checks.py` — Checks for a particle-effect clip (`engine/particles.py`): is it empty at both ends, does it show a burst, does it stay in its cell, does it move; …
- `effect_video.py` — Particle effects, the video side: a text-only Kling clip (a grid of burst cells on a key-colour screen, each cell empty at the start and at the end) …
- `emoji_glyph.py` — One emoji glyph as a particle sprite, drawn with the system's colour emoji font (Reaction effects).
- `emoji_motion.py` — Every bank emoji's one fixed animation (preset + params), pure.
- `ffmpeg.py` — ffmpeg helpers (subprocess only). Works on Windows/macOS/Linux: uses PATH ffmpeg, else imageio-ffmpeg's bundled binary.
- `grid.py` — Grid geometry: find where to cut a sticker sheet. Pure (numpy only).
- `particles.py` — Particle burst: a few sprite images -> a 3 s Telegram video-sticker frame sequence. Pure, deterministic, no network.
- `lottie.py` — A burst as a playable Lottie JSON: the simulator's trajectories as image layers over the real sprite PNGs (web only).
- `render.py` — Scale + white outline + report, shared by stills and video frames.
- `sheet.py` — Part A: rows x cols sheet (3x3, 2x2, 1x1) -> keyed cells -> 512x512 stickers. Pure: arrays in, results out, never raises per cell.
- `verify.py` — The verifier: ONE catalogue of every check on the golden path (docs/architecture.md, "Engine").
- `video.py` — Part B: prepared grid MP4 (3x3 / 2x2 / 1x1) -> transparent looping WEBM per cell. Same keyer as stills, same settings.
- `video_sheet.py` — G3: the video sheet. Re-composes the APPROVED stickers on a flat key-colour canvas, same slot positions as the stills,

**`flow/`**

- `batches.py` — Remove a batch (Haitham, 2026-10-03, "like remove pack"): `out/G###` moves to `out/trash/batches/G###` and Restore moves it back. Nothing is deleted …
- `effects.py` — Particle effects, the lifecycle of one effect `E###` (docs/architecture.md ("Reactions")).
- `explain.py` — Plain words for a sheet Python could not use (2026-10-02, the falcon sheet G094).
- `faq.py` — The shared FAQ (docs/architecture.md ("Chat and the agent")): what the support agent may answer from, written from resolved tickets and published by an admin.
- `gates.py` — The golden path's review gates (docs/architecture.md, "Engine"). The rules live here, in Python, and every phase keeps them:
- `projects.py` — the project map (redesign phase 3): Project > Batch > Sheet > Video as one tree for one batch, a pure read of `pipeline._packs`, the families, `video_sheets` and the jobs in flight (`GET /api/generations/{id}/map`).
- `groups.py` — Batch groups (Haitham, 2026-10-04): variations of one idea are ONE family. Earlier batches shows a family as one entry with a strip of its …
- `imports.py` — Bring a file into Mirsal, never twice (Haitham, 2026-10-05: "there should be a way of import with deduplication").
- `measure.py` — Phase 2 step S4: how often does a video made from the normalised video sheet leave its cell?
- `metrics.py` — Quality and timing numbers from what is already on disk: no new bookkeeping, no model, no network.
- `notifications.py` — In-app notifications (docs/architecture.md ("Chat and the agent")): what reaches a person when an admin answers or resolves their issue.
- `emoji_reactions.py` — Reaction effects (Create > + New, console/ui reactions.js): one bank emoji -> its fixed motion, flying as the literal glyph -> a Lottie file.
- `particle_sets.py` — Durable sticker-owned particle sets (`docs/architecture.md ("Reactions")`).
- `people.py` — Account requests on the office LAN (docs/api-integration.md): a sign-up waiting for approval, a forgotten password, a request for more
- `pipeline.py` — Generation lifecycle: 7 stages, each a real step with an event line in out/G00N/events.jsonl.
- `purge.py` — Emptying the trash: the purge of removed batches and deleted packs (Haitham, 2026-10-03: "Cleaning the trash"). Remove batch, Delete pack and a …
- `sources.py` — PhaseDirSource: discovers Haitham's prepared inputs by the inputs/ naming convention (read-only, never renames).
- `sticker_history.py` — The generation history of every sticker of a batch, for the page: one summary per sticker with its decisions grouped by stage.
- `support.py` — Help & Support (docs/architecture.md ("Chat and the agent")): a person describes a problem, the support agent answers from what is documented, and a person
- `support_kb.py` — What the support agent may read (docs/architecture.md ("Chat and the agent")): published FAQ entries, the repo's `docs/`, and, for the owner and admins only, …
- `ticket_models.py` — The ticket shapes (docs/architecture.md ("Storage and search")), pydantic, written once: `flow/tickets.py` validates the local model's draft with them and the native routes
- `tickets.py` — Tickets: every problem is one record of what happened, what the person meant, what the issue is and what should be fixed (docs/architecture.md ("Storage and search")).
- `trending.py` — Trending (docs/api-integration.md, Haitham 2026-10-04: "higgsfield 'trending' style … liked and commented, and use pack in your …
- `user_report.py` — What each person made and spent (the Users dashboard, docs/api-integration.md): aggregates computed on request from the stores that already exist, …
- `watch.py` — History = the real watch folders (inputs/Images_gen and inputs/videos_gen), with Remove.

**`generation/`**

- `actions.py` — Indexed export bank: 36 core moods plus 1,898 extended tokens, with explicit ambiguity candidates and saved canonical choices. The preset queue uses only core moods.
- `emoji.py` + `emoji_sequences.json` — Complete emoji extraction and exact validation against 3,773 checked-in Unicode 15.1 fully-qualified sequences, including tones, flags and ZWJ sequences.
- `claims.py` — The pack claim ledger (`docs/api-integration.md`): which preset grid each pack session has taken, and which …
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

- `export_names.py` — Export-as-ZIP display names (`docs/api-integration.md`):
- `export_resolutions.py` — Shared batch/library resolution ledger, atomic writes under process/file locks and additive manifest diagnostics. Metadata edits create snapshots; restoring metadata reuses the previous interpretation.
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

- `admin_bot.py` — Haitham's admin channel in the Mirsal Telegram bot (docs/api-integration.md): the bot already configured in Settings (token + …
- `collection.py` — Export a pack (or one Studio batch) to the Mirsal Creator API's "Submit a Pack for Approval", an external emoji CMS (`docs/api-integration.md`).
- `embed.py` — Text embeddings for the sticker pool (Phase 3B).
- `llm.py` — Chat Completions over urllib, provider-qualified local/router/OpenAI routing, persisted selections and an official OpenAI Luna cloud default with fixed `high` reasoning; old Luna ids normalize on use.
- `llm_catalog.py` — Authenticated cached provider catalogs intersected with approved image-capable cloud models; shared by browser and Telegram selectors and API validation. Official OpenAI uses only `OPENAI_API_KEY`; Nararouter uses only `NARAROUTER_API_KEY` with `MIRSAL_CLOUD_URL`, including vision recovery.
- `telegram.py` — Send a Library pack to Telegram (checkpoint 1H, docs/architecture.md).
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
- `net.py` — The names this machine answers to on the office network (docs/api-integration.md): its LAN addresses, its host name, and …
- `paths.py` — Path config. Cross-platform (pathlib only). Override with env vars MIRSAL_INPUT / MIRSAL_OUT.
- `users.py` — Users and tokens (Phase 5C): who is calling, and what they may see.
- `writer_lock.py` — One writer of result.json per out/ folder, across processes.

**`obs/`**

- `scrub.py` — Free text that may leave this machine (a ticket, an error answer, a console line) never carries where the machine keeps its files.

**`console/`**

- `app.py` — The HTTP server: FastAPI on uvicorn.
- `app_models.py` — The pydantic models of the NATIVE FastAPI routes (console/app.py). Existing routes keep their dict shapes behind the adapter; every route added after …
- `inventory.py` — What the browser sandbox can DO, read from its own scripts: every action (`ACT.<name>=` in console/*.js), the
- `openapi.py` — The HTTP contract as an OpenAPI 3.1 document, served at GET /api/openapi.json and turned into TypeScript types by `python -m mirsal openapi --ts …
- `placeholders.py` — Placeholder art for the Studio until real images are dropped into console/assets/styles/ and console/assets/vendors/.
- `server.py` — The HTTP server: FastAPI on uvicorn over the original handler (byte-identical answers); `serve --stdlib` keeps the old ThreadingHTTPServer for one release. Binds 127.0.0.1.

## 8. Engine

Deterministic dict/dataclass/JSON (`mirsal/mirsal/engine/`); purity: no fastapi/pydantic/psycopg/langgraph/model clients. Thresholds live in `EngineConfig` only.

- **Stills** — grid-cut (`grid.py`: gutter-band detect, thirds fallback) + per-cell border-ring chroma key, speck drop, edge-band despill, bbox trim, one pack-wide median scale (clamped ≤0.85×512), premultiplied resize, 12px white outline (0 = plain twin). Failed cells go through the key-recovery ladder, then FAILED with a `ruled_out` + attempts log; healthy cells are never retried. Grid default 2×2 (`expand(task, grid=(2,2))`), explicit 3×3, 1×1 regen; templates in `prompts/templates/<id>_v<N>.txt`, `render_plan` rebuilds prompts from slots (template wins); every cell carries 1–5 tags, `tags[0]` is the key.
- **Video** — decode cell by cell (ffmpeg, bicubic + full-chroma SWS, native fps ≤30, ≤3s), one transform per clip (keep approved size / same scale / resize-hotspot + `anim_scale` 0.5–1.5 + `anim_offset`), loop close = `loop_end` retiming then premultiplied-alpha 6-frame crossfade (never blends to transparent black), VP9 yuva420p down a CRF ladder to ≤256KB. Pre-sliced mov-preferred clips skip keying.
- **Verifier** (`engine/verify.py`, one catalogue) — 44 checks, 9 stages (sheet/still/video_sheet/video/slot/anim/pack/telegram/telegram_set). `Check{id,stage,severity,value,limit,detail,note,reason}`; `run()` never raises (a crash is BLOCK `verifier_error`); the Report's first failing BLOCK is the reason, WARNs go to `metrics.warnings`; `VERIFY_VERSION` stored per result; fixture table in `tests/test_verify_fixtures.py`.
  - `OVERRIDABLE` (a human may allow): still{blank_cell,foreground,inside_cell,no_spill,holes}, animation{inside_slot,cross_slot,loop_seam}, video_sheet{no_outline_on_sheet,video_specs,layout_match}.
  - `TECHNICAL` (final): still{dimensions,transparent_corners,static_file}, animation{size_budget,codec_vp9,dimensions,fps,duration,no_audio,alpha_mode_tag,alpha_decoded}. Crashes + empty cells are always final.
  - `waived()` / `animation_verdict()` demote allowed BLOCKs to WARN "(allowed by you)".
- **Gates** (`flow/gates.py`, 409 on out-of-order) — G1 plan → G2 stills → G3 video sheet (2048px, one scale, no outline) → G4 anims → G5 pack (G2 AND G4). Locks: G1 before G2, plan locked after the still decision, sheet build needs all READY decided + ≥1 approved, G5 locks anim decisions. Python FAILED is final; rejection never deletes; `S#` stable. `allow` API: `kind=` still|animation|video_sheet + bulk allowAll; `soft_block` (WARN-only anims OFF by default, includable) vs real BLOCK refused. Layout match IoU ≥0.6, blank slots stay empty. Batches are families (`flow/groups.py`: group/pick/hand_over, pack derivation, 6h gap); generations + resheet/redo_video with `versions/` + `anim_versions`. Recut is free (`SHEET_FATAL={sheet_decodes}` is the only hard stop).
- **Telegram** (`services/telegram.py`, stdlib urllib only, token never returned/logged) — verifier `telegram` + `telegram_set` stages judge before send (video ≤256KB VP9+alpha ≤3s ≤30fps 512-side; static PNG/WebP ≤512KB; 1–120 stickers, keys, emoji, name ends `_by_<bot>`). Mixed packs split `_v`/`_s`; `addStickerToSet` up to 50 + rest; sets stored on the pack (only new stickers re-sent, no deletion sync). Dry-run GET, `telegram.zip` no-credentials fallback, owner notified with the Add-Stickers link. Never-twice sends (`mode=` once|replace|new_set).
- **Imports** (`flow/imports.py`, free lifecycle) — a sheet becomes `pipeline.start` + `run_stills` (a normal batch); a video attaches grid-matched (48×48 MAD sheet match, detected-grid 409 with cut-anyway `grid_ok=1`, duplicate/again/as_new, SHA-256 + reservation dedupe). Manual 9-emoji batches via `gates.quick_add`.

## 9. Chat and the agent

The chat's backend is the Studio: `agent/tools.py` is a small interface over the Studio's own engine. `agent/graph.py` owns state and entry points; `agent/lifecycle/` owns turns, checkpoints, replay and graph construction; `agent/nodes/` groups intent handlers.

- **One turn** — hybrid routing (deterministic rules first in `resolver.py`, small schema-checked model calls in `brain.py` only for what rules cannot classify), intents, a 409 lock while a turn runs, a priced go-ahead before spending, prepared subjects served free instead of paid. The step trace (`message.steps[]`) streams; the page polls the newest card.
- **Memory** — session shape with TEMPORARY/PERSISTENT feedback, per-subject traits, a 15-turn reducer, 400/300/200 bounds (migration 004). Taste votes are JSON-only; `profile.py` keeps per-person taste across chats (`out/profile/<user>.json`).
- **Durable turns** — `checkpoints.sqlite` + `SAFE_RESUME` replay bound; profiles in `profiles.sqlite` + JSON. Creator recovery at every external side effect is not proven (backlog).
- **Stages** — how far a new request goes: six stops (`stages.py`: `of`/`need_of`/`resolve`/`at_least`), batch follow-up (`batch-01`, `MAX_BATCHES=4`).
- **Creator** (`creator.py`) — the agentic creator: one go-ahead from a request to a pack on Telegram. A state machine with a bypass and money rules.
- **Vision judge** (`vision/judge.py`) — pre-reviews only, never approves. `FAIL_CLOSED`: configured cloud model → `MIRSAL_LLM_FALLBACK` via Nararouter → local LM Studio → "unjudged". Consent asked once per session/browser (`vision/consent.py`); captions stored per cell (`transcribe.py`, grid-agnostic).
- **Models** (`services/llm.py`, `llm_catalog.py`) — local = whatever the local server lists (`resolve_local_model`, readiness by a real one-token probe); cloud default `openai:gpt-6-luna` (effort high); embeddings local `nomic-embed-text-v1.5` hardcoded.
- **Redis** (`runtime/cache.py`) — disposable: the live event stream, short caches, lock/session keys. Everything rebuildable.
- **Events** — `pipeline.emit` + Phase-5 names, SSE per generation and per chat turn (`docs/api-integration.md`).
- **Edits by meaning** (`editroute.py`, pure) — editor/tweak/action/redesign, `REF_CLAUSES`; a person reference reuses the parent prompt (`delta_of`); reference roles for numbered edits; undo has a defined scope, no redo (W23).
- **Subjects** — several subjects per request; per-subject feedback and refine; presets-only styles.
- **Reaction sets in chat** — intent routing into set flows with `_focus_set` order; the Echo overlay offers free lookup.
- **Support** (`flow/support.py`, local-only model) — cite-or-decline from published FAQ + `docs/` (+ code for staff), watches, private replies, notifications, one ticket + one Telegram ping per escalation. FAQ seeds in `faq/<category>/<slug>.md` (`mirsal support import-faq`); drafts publish in Help > FAQ review. Screenshots read by the local vision model.
- **Telegram chat** (`services/tg_chat.py`) — the same agent on the bot: each writer gets a member account, questions are native buttons, finished animations arrive as real stickers. A picture sent to the bot is not read yet; never run against the real bot without W51.

## 10. Storage and search

Durable state, identity, lineage, decisions and search. The file store stays the primary store and the app works without the database; Postgres mirrors it. Local `mirsal-db` (`pgvector/pgvector:pg16`, host port **5434**; 5433, 5436, 5437 belong to other projects, never touched).

```
cd mirsal
python -m mirsal db up        # start mirsal-db (5434) + mirsal-redis (6380), then migrate
python -m mirsal db migrate   # apply migrations/*.sql in order (every file re-runnable)
python -m mirsal db status    # declared / applied / pending / unknown files
python -m mirsal db check     # does the LIVE schema match the files (throwaway schema, rolled back)
python -m mirsal db import    # backfill out/tasks, out/jobs, out/model_calls.jsonl, every out/G### (idempotent)
python -m mirsal pool reindex # index approved stickers + vectors (local embeddings, free)
```

`MIRSAL_DATABASE_URL` (or `mirsal/.env`) overrides the local URL; `MIRSAL_DB_WRITE=0` forces write-through off. Only the real `out/` writes through (tests and copies never touch the shared database).

- **Migrations** (`mirsal/migrations/`): 001 base (generations, stickers, assets, video_sheets, reviews, events, tasks, search_log), 002 ledger (`model_calls`), 003 pool (`sticker_index` + pg_trgm), 004 sessions, 005 vectors (768-d cosine HNSW, re-runnable), 006 users, 007 job queue, 008 idempotency (24h keys), 009 groups (`group_id` + relation), 010 tickets, 011 user profiles + support records, 012 pack claims. A drift `db check` reports is fixed by writing the next numbered migration, never automatically.
- **Mapping** (files → rows): `result.json` → `generations`; stickers → `stickers` (+ `assets`, bytes hashed, never opened); `history[]` → `reviews` (actor python|human|vlm); `events.jsonl` → `generation_events`; `tasks` joins the provider (`UNIQUE (provider, external_task_id)`); `model_calls.jsonl` → `model_calls` (sha256 of the line); sessions → `sessions`/`interactions`/`feedback`.
- **Pool** (`store/pool.py`) — every APPROVED sticker indexed (subject, action, topics, `shared`, `hidden`). A request first fetches matches (free); vectors (`0.5·cos(subject) + 0.4·cos(action) + 0.1·lexical`, gates 0.50/0.40) + lexical fallback + hybrid; ≤2 hits per generation; `--style` filters; reference-image stickers are `shared=false` forever. Embeddings: local `nomic-embed-text-v1.5` 768-d hardcoded, cloud fallback with its own key.
- **Tickets** (`flow/tickets.py`) — problems are tickets, not traces (LangSmith retired 2026-10-04). `out/tickets/T###.json` + a Postgres row: what happened, the person's words, the issue, a fix, 2–4 questions, status (open/answered/fixed/won't fix). Automatic tickets fold by fingerprint; the local model drafts (`ticket_models.py`, validated); free text scrubbed of absolute paths (`obs/scrub.py`). Support tickets add a thread, `replied`/`pinged`/`faq` states. Screen: Settings > Tickets + Report on a batch/row/reply.
- **Help & Support records** — files are the record, Postgres mirrors + vectors: `faq` (`out/faq/F###.json`, only `published` answers), `support_chunks` (one row per section of `docs/` or block of code, replaced per changed file), `support_conversations`, `notifications`.
- **Principles**: Postgres holds paths/hashes/metadata, never bytes. History is append-only. Natural language is never an identifier (`G###`, `G###/S#`, `tasks.external_task_id`). The engine never imports `psycopg`/`redis` (a test enforces it). Decisions are rows. Gate rules stay in Python; the repository stores, never decides.

## 11. Reactions

Labels say "reaction" everywhere since 2026-10-13; routes, storage and code keep `particles`. Screens in `docs/design.md`.

- **Vocabulary** — a reaction set (`P###`, `out/particles/P###/`) belongs to library stickers (`owner:[{pack_id,sticker_id,generation,index}]`); `packs[]`/`used_in[]` derived read-only; one saved version per row (v1, v2…); trash/restore, purge-detach. An effect (`E###`) is the Kling/simulated build behind a burst.
- **One animation per emoji** — every bank emoji has one fixed motion (`engine/emoji_motion.py`: 36 core + hash fallback); 5 preset signatures in `engine/particles.py`; per-emoji map + variations on top; swirl flow-field. Bursts rendered onto a pack are reactions, never stickers (excluded from sticker surfaces).
- **Galleries and chat** — rows/drafts/adopt; Save / Save-as-new / Add to pack; mistaken-pack recovery; the Echo overlay offers free set lookup from the chat.
- **Lottie** — slot presets, emoji-free, no base64 (`engine/lottie.py`); every emoji holds a preset; zip manifest. Handpicked files: drop zone, `handpicked[]` storage, zip rule. Lottie-style reactions: Particular settings (Emitter → Particle → Physics → Aux), `START`, export, `MAX_PARTICLES`.
- **Reaction tabs** — Emoji | Lottie | Super Emojis | Packs, one shared tab state.
- **Super reaction** — hold, release, the screen plays. Engine (`engine/super_reaction.py`): aspect buckets, bottom emitters, auto/solid/gradient glow, a centre pop that floats up. Library (`flow/super_reactions.py`, `out/particles/super/library.json`): every file a seeded random look until saved; Shuffle, Save, Save-as, Remove, presets. Export: JSON per screen + `superReactions.zip` (× 8 buckets + manifest). Sandbox `#/super` (desktop frame plays in its chat area, iPhone whole phone, both resizable) with Size/Amount/Rise/Float/Sway/Spread/Glow sliders and one-frame tuning at Animation frame (0–100%).
- **Emoji bank** — one canonical bank (36 core + 1,898 extended, `generation/actions.py`, `emoji_sequences.json`): binding rule (the saved per-sticker emoji always wins), core-36 table, readers = reactions + export tags + planner.

## 12. Studio

A thin layer over the gates (`review`/`drop`/`allow`, `add` resolving G2+G4+G5 in one call, replace|add modes, idempotent). One control per cell (`ACT.gcell` ← `gates.allow_info`); issue colours (orange out of bounds, purple green screen, yellow loop, pink look/motion, blue file limit, red blocked/dropped); the sheet is a first-class clickable surface; appearance (outline, erode) re-renders from source/plain + STALE anims; prompt draft + AI enhancer (plan untrusted, re-linted server-side, price shown before spend); a stale-server banner (`Console.stale` vs `.py` mtimes). Studio edits as layers (`studio_edit_open`/`commit`, `edit_still`, `replace_still`, `rebuild_sheet`); video/GIF projects with a server-frame preview (chroma-then-matte providers). Layout and the creation panel: `docs/design.md`.

## 13. Measurements

Recorded numbers, never opinions. `python -m mirsal measure-cells --record` appends a block here; the other sections were written by
hand from a real run. Dates are absolute. (Carried over from `docs/measurements.md`, deleted in the 2026-10-21 convergence.)

## Video cells that leave their slot (`measure-cells`, 2026-10-02, 36 cells in 4 video sheets of the real G00x batches)

```
slot_fill  gap  sheets  cells  flagged  share   cross_slot  inside_slot  inside_frame  subject_px(mean/min)
0.74       26%       2     18        1   5.6%           1            0             0  257.2/160
0.80       20%       1      9        8  88.9%           8            7             0  427.1/390
0.84       16%       1      9        4  44.4%           1            3             0  439.2/408
```

A wider gap between stickers on the video sheet flags fewer cells: 0.74 (the default) is the best measured, but it is 2 sheets and some of
those clips were made with the cheaper Kling `std` model. **Open:** re-run with `pro` at 0.74 to reach "nothing flagged" and choose the default.

## Pool search (3B), first real run (2026-10-02, 45 approved stickers of G001-G005, local embeddings)

Embeddings: `text-embedding-nomic-embed-text-v1.5` on LM Studio (768-d, hardcoded), documents as `search_document: ...`, queries as
`search_query: ...`. Thresholds are **provisional** (`SUBJECT_MIN` 0.50, `ACTION_MIN` 0.40; `MIRSAL_POOL_SUBJECT_MIN` / `MIRSAL_POOL_ACTION_MIN`
override them) until Haitham's eval set (`docs/inputs/search_queries.md`, not written) exists.

| query | result | cosine subject / action |
|---|---|---|
| batman | G002 batman lego stickers (a pack; 2 shown by the default diversity cap) | 0.746 / - |
| batman throwing | G002/S2 `throwing_batarang`, G002/S7 `gliding_in_air` | 0.746 / 0.597, 0.402 |
| angel reading a newspaper | G001/S6, S7 | 0.966 / - |
| old man sleeping | G004/S8 `old_man_pixar_style_sleepy` | 0.610 / 0.695 |
| barbie love | G005/S5, S9 | 0.788 / - |
| mouse with a gold chain | G003/S2 `mouse_shy`, S1 `mouse_proud` | 0.556 / - |
| **falcon dancing** | nothing (no falcon in the pool) | below the gate |
| **penguin skiing** | nothing | below the gate |
| **tedy bear** (typo; no teddy in the pool) | nothing | below the gate |
| a hero fighting | nothing ("hero" is not "Batman" at this gate) | below the gate |

A related query scores 0.55-0.97 on the subject, an unrelated one 0.20-0.35. Latency is the query embedding (1.3-2.2 s the first time, a Redis
hit after); the SQL is single-digit ms on 45 rows.

**The first real search found a bug, fixed:** the lexical scorer returned the old man's stickers for "batman" (trigram overlap of "man", rank
0.22). Word coverage now compares whole words (`_close`), so "batman" is not "man" and typos ("tedy bok") still match (`tests/test_pool.py`).

**Open:** precision@5 >= 0.8 needs Haitham's labelled queries; the gap flow shows "Found N, generate M more?" without a price.

## Vision judge (S6), first live runs (2026-10-02, G002 Batman Lego, 9 stickers, a COPY of out/)

| model | approved | rejected | unjudged | per sticker |
|---|---|---|---|---|
| `mistralai/ministral-3-3b:2` | 7 | S2 (batarang), S7 (gliding) | 0 | about 3 s |
| `qwen3.5-4b:2` with `reasoning_effort: "none"` | 7 | S5 (victory pose) | S7 (invalid JSON twice) | about 4 s |

The two small models disagree on which stickers are bad, and nobody has checked either against a person: **the judge is uncalibrated until
Haitham labels 30 stickers** (target: agreement >= 80%, otherwise point the same code at OpenAI). Thinking models spend the token budget on hidden
reasoning when it is left on (300 tokens gave an empty answer): the client sends `reasoning_effort: "none"` (0 reasoning tokens, a 2 s answer).

## Vision judge: local Qwen 9B evaluation (2026-10-05)

Actual model: `qwen/qwen3.5-9b`, served locally through LM Studio's `http://localhost:1234/api/v1/chat`. All 30 prepared cases were run. The supplied rhyme smoke request also returned a rhyming answer (`mirsal/local_eval/smoke.json`).

| Measurement | Result |
|---|---:|
| Unique READY still-sticker cases completed | 30/30 |
| APPROVE | 24 |
| REJECT | 1 (G104/S1: AMBIGUOUS_ACTION, WEAK_CONCEPT) |
| UNJUDGED | 5 |
| Usable first-pass verdicts through the production parser | 25/30 (83.3%) |
| Median end-to-end time per sticker | 10.437 s |
| Independently human-labelled cases | 0 |
| Agreement with a human | Not measured |

The five UNJUDGED cases are G004/S1, G096/S1, G097/S1, G105/S1 and G004/S2. Their responses used unsupported reason codes such as CONCEPT_MATCH and WARM_EXPRESSION. These failures were retained rather than repaired or counted as passes.

Method: deterministic round-robin sampling across existing batches, unique source-image hashes, the production review prompt and verdict parser, one still image on grey per request, temperature 0, reasoning off, 700 maximum output tokens, no stored chat and no automatic repair call. The production judge normally offers one repair round; this run measures first-pass behavior only. Source hashes are pinned. No cloud fallback, paid generation, live review changes or application configuration changes were made.

Scope: this tests local vision responses, parser compatibility and latency. It does not evaluate animation motion, reference-image consistency, pool search or chat resolution. The sample is not a balanced or representative accuracy benchmark. **83.3% is the usable-response rate, not model accuracy.** Independent labels are empty, so the judge remains uncalibrated against Haitham's judgments. Saved review states are context only and are never provided to the model as answers.

Artifacts and runner: [results](../mirsal/local_eval/results.md), [summary](../mirsal/local_eval/summary.json), [dataset](../mirsal/local_eval/dataset.json), [instructions](../mirsal/local_eval/README.md). Haitham does not want manual testing; no labelling task remains in the waiting tracker. Human agreement stays unmeasured. Future objective checks can be prepared and run by an agent with explicit expected outputs; model-to-model agreement must not be presented as human accuracy. Independent labels remain optional, and the advisory judge does not require them to run.

## Photo cutout (3C), test photo `ref/upload.jpeg` (2026-10-02)

`python -m mirsal photo ref/upload.jpeg` -> `out/photo/photo-upload.png`: method `chroma_green`, foreground 0.289 of the canvas (91 598 px),
512x512, 193 KB PNG, all checks ok. Edge quality on a real photo is Haitham's judgement (not looked at by the builder, by rule).

## Sharpness (the reworked `sharpness` check, 2026-10-02)

**Why it was rebuilt.** The old metric compared the decoded clip to its own encoder input, so softness that happened *before* the encode (a 320 px source cell upscaled to 512, the cheaper Kling `std`
model) read 1.00 on every clip. A down-up "retention" metric was tried and rejected (flat at 0.97-1.0 and not monotonic in blur). The check now also compares the animation's mean edge energy to its
**own approved still's** (`detail_vs_still`) and says how soft that is in pixels of blur (`soft_sigma`: the Gaussian radius that takes the still down to that level); it fails (WARN) on the worse of the
encode loss (`sharp_kept` < 0.8) and the detail ratio (`detail_vs_still` < 0.75). `python -m mirsal measure-sharpness` measures every stored animation.

On the 31 real animations of this PC the metric separates the batch the owner called soft from the rest: G002 (Kling `std`, 320 px cells) reads a mean of 0.65 (lowest 0.58, about 1.3 px of blur), all 8 flagged; G001 (mean 0.91, lowest 0.89),
G003 (mean 1.00, lowest 0.97) and G005 (mean 1.17, lowest 1.02: the animation is sharper than its still) pass. The threshold 0.75 sits in the gap between the two groups: **provisional until Haitham confirms by eye** that the flagged
cells are the ones he sees as soft (the measurement itself used no media viewing).

## measure-sharpness 2026-10-02 05:12

```
31 animations, 8 softer than 0.75x of their still's edge detail
generation  cells  mean_detail  min_detail  mean_blur_px  flagged
G001            5         0.91        0.89           0.7        0
G002            8         0.65        0.58           1.3        8
G003            9         1.00        0.97           0.1        0
G005            9         1.17        1.02           0.0        0
```

## Particle effects: Kling text-only clips (2026-10-02)

Two clips for the strawberry burst (method in git history, former `docs/effects.md` §3), judged by `alpha / background coverage per cell and frame`, never by eye: 2x2 (J037) 4 of 4 cells empty at the start, burst from
0.33 s, edge crossing <= 0.24 %, 1 of 4 empty at the end (0.7 % covered on the others), engine output 4 READY stickers of 199-237 KB; 3x3 (J038) 9 of 9 empty at the start, edge crossing 10-26 %, 0 of 9 empty at
the end. Particle simulator: 90 frames x 30 particles in 0.53 s at 512 px, 0.15 s at 256 px; the five presets encode to 201-245 KB WebM (crf 38-46).

## The pixelated outline of returned video sheets (2026-10-09)

Metrics only, no media viewed. Video-sheet batches G121/G122: the provider returns **1440x1440** (Kling 3.0) / **1424x1424** (Grok Imagine 1.5 Lite) for a
2048 px sheet; at `slot_fill` 0.59-0.62 each character is **296-368 px** in the video (`subject_px_in_video`) and is **enlarged 1.08-1.34x** (`scale`) to
fit 512; prepared-video batches G116/G117 were reduced (0.79-1.14). The encode is not the cause: `sharp_kept` 1.00-1.02 at crf 30-38.
Cause: ffmpeg's default yuv420p -> RGB copies each half-resolution colour sample to 2x2 pixels, so the colour-difference key cuts the edge in 2-pixel steps.
Synthetic H.264 (crf 18, 480 px, five subject colours on green), mean |alpha - truth| in the edge band:

| decode | native | after the 1.3x enlargement |
|---|---|---|
| default (copied colour) | 0.060-0.081 | 0.070-0.092 |
| `scale=flags=bicubic+full_chroma_int+accurate_rnd` (adopted, `ffmpeg.SWS_CHROMA`) | 0.030-0.056 | 0.041-0.067 |

Rejected: a guided filter on the mask with luma as guide (4x worse on an orange subject, whose luma equals the green's), keying after enlarging the RGB
(worse once the colour is interpolated). Test: `tests/test_video_decode.py`.

## 14. Where to read more

`README.md` (index), `CLAUDE.md` (rules and the routing table), `run.md` (how to run), `docs/rules.md` (rules in full),
`docs/design.md` (the look), `docs/api-integration.md` (the HTTP contract), `docs/generation.md` (live generation),
`docs/backlog.md` and `docs/waiting-for-haitham.md` (what is open).
