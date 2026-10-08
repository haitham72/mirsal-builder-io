# Live generation: how it is built

A typed request becomes a sheet of 9 stickers made by Higgsfield, and an approved video sheet becomes a Kling animation. Both go through the **unchanged** engine and review
gates; the file store is the primary state (Postgres mirrors it, see [`store-and-search.md`](store-and-search.md)). What the Higgsfield CLI offers, with measurements: [`higgsfield.md`](higgsfield.md).

```
request ─(prompt template v3 + style + stroke [+ AI enhancer] [+ references])─► task (G1 approval)
        ─► sheet job ─► Higgsfield CLI (Nano Banana 2, 2k) ─► out/jobs/J###/result.png
        ─► Pick(sheet) ─► the unchanged stills run ─► G2 ─► video sheet (G3) ─► video job ─► Kling v3.0 ─► attach + slice ─► animations ─► pack
```

## Prompts (`generation/prompter.py`, `generation/emotions.py`, `generation/styles.py`, `prompts/templates/`)

- **Template-locked.** A saved template per grid (`sheet_3x3`, `sheet_2x2`, `single_1x1`, `video`) is filled from a small slot JSON; nobody free-writes a prompt. New plans use **v3**
  (`TEMPLATE_VERSION`; v2 is kept as it was, so batches made with it rebuild to the prompt that was sent; v3 asks for "a wide range of emotions AND different states of action" so no two characters share a pose); a saved plan keeps its own version, and `render_plan(..., 1)` still rebuilds the v1 text exactly.
- **v2 wording is measured, not guessed.** v1 said "sticker" (image models answer with a white die-cut border) and "equal cells / row-major" (Nano Banana 2 painted a
  checkerboard of two greens: bg G 215/252 across cells). v2 says "one illustration of 9 characters arranged in 3 rows of 3 on a single seamless background",
  lists them as `Character N: …`, forbids outlines, and asks for one identical key colour. Measured on Nano Banana 2 at 2k: white-ring share 4.8% → 0.0000, per-cell
  green spread 51 → 0. The stroke is the engine's `outline` (Edge), never the model's.
- **Styles** (`generation/styles.py`): flat, toon shade, glossy 3D, soft clay 3D, realistic, hand-drawn; each is a phrase for the template's Style line. Tile images are optional files
  in `console/assets/styles/<id>.(png|jpg|webp|svg)`; without one a generated placeholder is served.
- **Emotions** (`generation/emotions.py`): a bank of ~35 expressive entries (label = expression + body language, emoji, motion) in nine mood groups; `pick(n, seed)` chooses one per group,
  deterministically per request, so a sheet never repeats a mood. The built-in school and birthday sets carry motions too.
- **Face-only emoji mode (2026-10-08).** A request naming emoji (`generic emojis`, `an emoji pack`, …) renders template **v4** with the face bank (`emotions.FACE_GROUPS`, same moods/keys/emoji, labels and motions mention only the face and head): a real emoji is a face, never a body. `expand` auto-detects it (`EMOJI_WORDS`), stores `slots.face`, and old plans rebuild to their own version as before. A limb-word list (`emotions.LIMB_WORDS`) guards it in `tests/test_face_mode.py`: the only limb words a v4 prompt may carry are its own "Faces only: never …" negations.
- **Preset grids (2026-10-08).** The canonical bank drives the nine directly (`generation/actions.py`: `PRESETS` core/social/reactions/daily-v1, `FACE_SENTENCES` face-only label + motion per token, `preset_cells`). `expand(..., preset=)` names one explicitly (preset words are stripped from the subject; a preset implies face mode); a faceless-emoji 3×3 with no grid named takes `core-v1`, so the first sheet of an emoji pack is happy → thanks in bank order with bank emoji. Cell keys are `{subject}_{token}`, tags carry token + aliases. The claim queue itself (`generate more` takes the next unclaimed grid into the same pack) is still open (`docs/export to team/mirsal-export-architecture.md` §10).
- **Motion per character.** Every cell has a `motion` sentence; `video_v2` lists them as numbered lines, so Kling animates each character differently.
  `Console.video_prompt_for` rebuilds the video prompt for the slots actually approved (empty slots get no motion).
- **References.** Up to 4 images, stored by `POST /api/live/ref` as `out/refs/R###.<ext>`, listed on the job (`request.refs`), sent as repeated `--image-references`, and
  explained to the model by `prompter.REFERENCE_CLAUSE` ("change only the expression and the pose"; never edited, it is the default) or by the `ref_clause` the caller sends (`agent/editroute.REF_CLAUSES`: `tweak`, `action`, and `like`, the clause of an edit that must be allowed to add a hat). A model that does not take references refuses them.
- **An edit's 1x1 is the parent's prompt.** `gates.regen_plan` builds it from the parent's slots (style, key colour, cell label and motion, tags) in the `single_1x1` template of the **parent's version** when that is 2 or later (a v1 parent gets the current version: v1's style line ignores the style); the chat appends the change to the cell's label. `POST /api/live/sheet` also takes `erode` beside `outline` (both stored in the job's request and applied by `pipeline.start`), so an edit keeps its parent's edge finish. No template or clause that was used was edited; the `like` clause is new (`docs/agent-and-chat.md`).
- **AI enhancer** (`generation/expander.py`, `services/llm.py`, OpenAI): **off by default and never called while typing.** On, `POST /api/live/sheet {ai: true}` first has the model write the subject
  description and 9 distinct, expressive cells (label, motion, key, tags, emoji), lints them (one repair round), and only then builds and sends the prompt. Off, the typed text goes
  into the template with the built-in emotion sets. **The whole request is planned** (Haitham, 2026-10-04): a place, vehicle or prop after `in / at / with / on` (`prompter.SCENE_WORDS`; `for / during` pick a theme instead) is the plan's `scene` and stays in `subject_description`, which starts every cell prompt ("camel in lamborgini" plans `described` "camel in Lamborghini", shown on the chat's card and on every sticker name); obvious misspellings of kept words are fixed first (`generation/spelling.py`: a near miss of a known proper noun or long word, never a guess); an AI answer whose subject description and labels lose the scene is repaired once, then the built-in sets are used (`expander.scene_missing`). A failed AI step falls back to the built-in sets and the response says why (`expanded_by`, `expand_error`). A
  transformation is **not** a failure: the template writes the cells (`expanded_by: "transformation"`, no `expand_error`) and the page reports that the enhancer was
  not asked instead of showing an error. The Studio's **Generate prompt** reaches the same expander before any sheet exists through `POST /api/plan {ai: true}` (the engine choice and local model are the AI screen's, `docs/agent-and-chat.md`); `docs/engine-and-studio.md`, "Generate prompt, before the sheet".
  `mirsal prompt "<request>" [--ai]` prints the same plan; `prompt lab` runs 20 inputs (English, Arabic, Arabizi).
- **Transformations** (`transformations/`, run first by `expander.expand`, with or without the AI): "dog as banana", "turn my cat into a pizza", "a frog shaped like a pear" are ONE new character
  (a banana with the dog's face), not a dog next to a banana. `detect` needs `as`, `into`, `turned into`, `shaped like` or `looks like`; "dog with bananas", "a dog holding / eating a banana", "dog and
  banana", a role or costume ("dog as a pilot"), a size comparison and requests about stickers themselves are **not** transformations and take the normal plan. The versioned template
  `subject_as_target` v1 guarantees the cells **dance, shock and squash** (wording sharpened per target by a lexicon: `banana.py`; any other target gets the generic wording), fills the rest of the
  grid from the emotion bank, puts the "one single character, not holding or wearing it" sentence into every prompt, flips a green target (avocado) to a blue screen, and lints itself
  (`validate`: required cells present, nothing the user ruled out, a full grid). The user overrides in the request: "no dancing", "without squash or shock", "no crying" (a required cell they
  name is dropped; any other word is kept out of every cell). Stored with the generation as `slots.transformation = {id, version, flavour, subject, target, required, forbidden}`. The chat adds a
  note to its steps and the plan card carries `transformation`; the planner cache key includes `transformations.signature()`. English patterns only (Arabic / Arabizi requests are not detected yet).

## The Higgsfield CLI (`generation/higgsfield.py`, `generation/model_catalog.py`)

- `generation/higgsfield.py` is a thin subprocess wrapper: `account`, `cost`, `create` (WITHOUT waiting, returns the job id), `wait`, `download`, and `dump_models`/`load_models` (the full list:
  34 image, 38 video, 8 audio, 1 text model with every parameter, cached in `out/higgsfield_models.json` for a day). It calls the vendored `hf.exe` directly with an argv list
  (the npm `.cmd` shim would let cmd.exe interpret `&`, `%` or quotes in a prompt). It never runs `auth token`. `MIRSAL_NO_REAL_CLI` (set by `tests/__init__.py`) makes any real call fail:
  no test can spend credits. `NEVER` bans Kling `4k`.
- `generation/model_catalog.py` is the selector's data: 8 image models (Nano Banana 2 / Pro / 2 Lite, GPT Image 2 / 2.5 with the flare/sunburst variant, Seedream 5.0 Pro / Flash / Lite) and
  2 video models (Kling v3.0 always `pro`, Grok Video 1.5 always 1080p; nothing below 1080 is offered), each with its selections; `resolve(kind, model, options)` validates and returns the CLI's job_type and params. Every other
  model of the dump is selectable too (options generated from its own parameter list). Defaults: Nano Banana 2 at 2k, Kling v3.0 pro, 3 s.
- Logos: `console/assets/vendors/<logo>.svg` (Google, ByteDance, Kuaishou fetched once from the Simple Icons set); OpenAI and xAI get a monogram until Haitham drops `openai.svg` / `xai.svg`
  into that folder. The app logo is `console/assets/brand/mirsal-logo.png` (the white-background JPEG in `ref/` made transparent).

## Video quality, the gap, Loop and the edge (measured on G002, 2026-10-01)

- **Pixels.** The first Kling clip was `std`: 960x960 for the whole sheet, 320 px per slot, the sticker filled 55% of its slot, so about 176 px of picture were scaled 2x to 512:
  that is the pixelation. Kling is now always `pro` (1440 px, 480 px per slot; `std` is not offered) and Grok always 1080p. A 2x2 sheet would give each sticker 2.25x the pixels of a 3x3
  one (open question).
- **The gap is the user's to slide.** The server fills each slot to `slot_fill` (0.74, so the free space per slot went 45% -> 34% -> 26%) and the animation box shows a **Gap** slider
  (8-50%) with a small preview of the exact sheet that would be sent (`GET /api/generations/<id>/sheet_preview?fill=`, built on the fly, never stored). `POST /api/live/video {slot_fill}` builds the
  sheet at that fill; if the user moved the slider after a sheet was built, the old sheet is **rejected (never deleted)** and a new one is built. The fill is stored on the sheet (`slot_fill`).
  A fuller slot leaves less room for expressive motion, so more cells can fail the out-of-bounds checks (those are warnings the user can include anyway).
- **Loop is a choice, off by default** (like the stroke): the saved plan has `slots.loop`, the composer has a Loop chip, the animation box a Loop checkbox. Off: `video_v2` contains no loop
  wording at all and the Kling job gets only a start image; on: "seamless loop", "End on the starting pose so the clip loops" and start = end image. The engine closes loops itself
  (`close_loop` eases the last frames of a clip whose end does not match its start into frame 0, so the clip starts on its own first pose and the thumbnail is never a dissolve; it used to start on the tail's pose and cross-fade into the head, which showed as a ghost on the first frames), so the model never needs the word. `loop_seam` stays a technical block.
- **The edge is a preview until it is applied, and it never loses a video.** Stroke and trim are sliders in the edge bar (and in the open thumbnail's view). Dragging one changes **one
  thumbnail only**: the open one, else the last one picked, else the first. Outside the open view that is a **floating card** under the sliders (the test sticker, large, on the checkerboard,
  with **Apply** and **Cancel**); in the open view the big sticker pane is the preview. The grid is never touched, nothing is stored and nothing is re-rendered while a slider moves
  (`GET /api/generations/<id>/edge_preview?index=&outline=&erode=`, one PNG rendered from the stroke-free twin by the same `apply_edge` the real render uses).
  **Apply** (`POST /api/generations/<id>/edge {outline, erode}`) saves **one snapshot** (`result.json edge_history`, seeded with how the batch started) and applies the edge to the whole batch:
  the stills are re-rendered (about 0.2 s) and the animations are re-cut from the stored video (`gates.reslice`, no credits; the animation cache keys on the edge, so a setting used before comes
  back in about 2 s and a new one takes about 13 s for 9 stickers). **Undo** steps back one real snapshot (the log is replayed as a stack: an `undo` entry pops, so two Undos never flip between two
  values) and is itself recorded; **Cancel** only drops the test. The same edge twice changes nothing and adds no snapshot. Besides Apply, a pending edge is applied automatically in exactly
  two moments: when the **video is generated from the image** (`POST /api/live/video {outline, erode}`) and when the **stickers go into a pack** (the add endpoint); both go through
  `Console.commit_edge`, which refuses while another job holds the pipeline. The video sheet is built from the stroke-free stickers on purpose, so changing the stroke never needs a new Kling video.
- **The returned video stays visible.** The Animation view shows the Kling video with the slot lines (a light 720 px `preview.mp4` is made when the video is attached, or on demand for older
  ones), and a batch with a Kling video counts as having a video everywhere in the UI.
- **Warnings in plain words.** A kept-with-a-check sticker says what Python noticed and what to do (for example "looks almost the same as S1: the same pose drawn twice? Kept: drop one with the
  x"), not a check name.
- `video_v2` also asks for "a wide range of emotions" and "highly expressive faces and bodies".

## Files and names

The engine keeps its files in `out/G00N/` and `out/jobs/` under its own names (`{media}-{subject}-{action}-{UTC time}-{hash}.{ext}`, `runtime/names.py`; older batches keep `<media>-<NNN>-<task_slug>-<key>`; the database stores them and they never change once made). `POST /api/generations/<id>/reveal` opens the batch's folder in the file manager (the Studio's **Open folder**), `GET .../files` returns the paths. The watch folders
(`inputs/Images_gen`, `videos_gen`) are never written to: a returned Kling video is laid out for the normalised video sheet, so pairing it with the raw sheet there would be wrong (and a
prepared pair dropped there is picked up as before).

## The screen colour (blue key)

The sheet prompt asks for the key in `slots.key_colour` (green; blue when the AI enhancer sees a green subject, `expander.GREEN_WORDS`). What the model **returns** wins: `run_stills` measures the outer ring
(`chroma.detect_key`, the colour with the higher key difference, `asked` when neither is clear so the sheet check still blocks it) and, when the screen is blue, writes `key_colour: "blue"` on the batch.
`pipeline.cfg_for` then makes every later step use `chroma = "blue"` (keyer, despill, the sheet check, the **video sheet**, the keying of the returned video) and `video_prompt_for` names the screen
that was really sent. It is **marked only when it is blue**: the task file gets `key_colour: "blue"` (plus `key_detected: true` when the prompt had asked for green, i.e. the model drifted), `prompts.txt` gets a
`KEY: blue` line and the batch header a "Blue key" chip; a green screen leaves no mark anywhere. A sheet with neither screen is still blocked (`background_is_key`).

## The queue (`GET /api/jobs`, `live.js`)

The **Queue** is a small panel fixed at the bottom left next to the credits (collapsed: "N running · stage · elapsed of about typical", or "N failed"; open: the rows, expanding upward, state remembered). It lists every job the server knows (it survives a reload): kind, request, model and settings, credits, start time, the Higgsfield job id (with a copy button), a progress bar
against the typical duration of that model (median of the ledger), and the real stage: waiting to start, Higgsfield is working (elapsed against typical), downloading the result, cutting the
animations (n of 9 for a video), done, or the reason it failed in plain words (for example a content-filter refusal, `nsfw`, or a temporary HTTP 5xx). A running job also shows on the credits pill.
Stalled jobs carry four explicit actions, cheapest first: **Refresh** (local state and generation SSE only), **Check · free** (one `generate get`, then download/attach a completed result by ticket), **Continue · same ticket** (`POST /api/jobs/<id>/continue`, `jobs.resume`, no second charge), and **Retry · SPENDS** (a separately priced and confirmed new request, never the default). A local FAILED/TIMEOUT ticket with a completed provider task is labelled **“Divergence, not a failure”** and reconciled with human history. The Queue, Studio job panels and chat all use the same controls (`console/job-recovery.js`, loaded before `live.js`; the Queue lists every active, recent and FAILED/TIMEOUT job instead of only the last day's eight, and its pill says "N need attention"). Routes and bodies: `docs/api.md`, "Job recovery"; the runbook: `docs/operator.md`.

## Allow anyway (a human override, `gates.allow_animation`)

An animation that Python blocked for **leaving or crossing its slot** (`inside_slot`, `cross_slot`) has no file, because the block saves the encode. The user can **allow it** by clicking the
sticker's warning banner, its "Allow anyway" button, its chip, or its cell on the video sheet (`POST /api/generations/<id>/allow {index, allow}`): the permission is stored on the sticker
(`anim_override`), recorded in its history as a human APPROVE ("allowed anyway: cross_slot"), the cell is cut again with that check downgraded to a warning (still listed, "allowed by you"), and
every later re-slice (an edge change) keeps it. **Allow all (n)** under the sheet's chips allows every blocked animation of the batch in one request (`{all: true}`, one re-cut of all of them), **Take all back (n)** reverses what was allowed, and every cell on the video sheet is a toggle (click: allow; click an allowed one: take it back). Taking one back (the tile's "undo") blocks it again. Technical blocks (format, size, codec, loop) cannot be allowed, and the review gate itself
still refuses a blocked animation. **Dashed + faded means "will NOT be exported"** (a dropped sticker, a blocked animation, a sheet cell outside the set) and **solid means exported** (a kept-with-a-check cell has a thin solid outline); a faded item is never disabled: it stays
clickable, can be opened, brought back or allowed.

## Jobs (`generation/jobs.py`)

`out/jobs/J###.json` (`REQUESTED|CLAIMED|DONE|FAILED|TIMEOUT`; a job created since 2026-10-04 is labelled `J058-<subject>-<kind>.json` with its files in `J058-<subject>-<kind>/`, the subject from its task, else its batch, else the request's label; the id stays `J058` and `jobs._path` / `jobs.job_dir` find either form; J001-J057 keep their bare names) as before, plus `params`, `cost_estimate` and, for sheets, the `generation` it started. `fulfil(out, jid)`:

1. resolves the selection through the catalog (and refuses references the model cannot take);
2. `generate cost` (and the optional daily cap `MIRSAL_DAILY_CREDITS`, refused before anything is paid);
3. `generate create` **without `--wait`**, then `claim` with the returned id **immediately** (ticket first, mirrored into `out/tasks/NNN.json`);
4. `generate wait`, download the result (`higgsfield.download`: plain HTTPS through the **tolerant TLS context** `telegram._ssl_context()`, which skips a malformed entry in a Windows certificate store; the default context failed with `[ASN1: NOT_ENOUGH_DATA]` on one PC AFTER the job had been paid, which leaves the job `FAILED` with its ticket: **Check** or **Continue** downloads it without a second charge. Telegram, the LLM client, embeddings, tracing and this download all use that one context), `done` (copies it to `out/jobs/J###/result.<ext>`, writes the ledger line with cost, params and the Higgsfield id).

A job already CLAIMED resumes by its ticket and never creates a second paid job: `fulfil` refuses (409) to create for ANY job that holds a stored ticket unless it is CLAIMED, `requeue` of a ticketed job is a `resume` (it waits for the same provider job), and a CLAIMED job whose wait timed out is resumed, not created again. One paid call at a time (a lock in the process and a file lock `out/.paid.lock` across processes): the job is read AGAIN under that lock, so two runs of one job pay once and the loser (`JobBusy`) reports what is true, pays nothing and marks nothing failed; `done()` (the ledger row the daily cap sums) runs under the same lock, so the next call sees this one's spend. `POST /api/live/sheet | video` and the task form of `POST /api/generations` accept `Idempotency-Key` (the Studio sends one per click). Transient wait errors with a ticket exhaust bounded retries into `TIMEOUT`; terminal errors or failures without a ticket end as `FAILED` with the reason.
`Console.fulfil_async` runs it in a thread (or hands it to the durable queue, below); on a finished **sheet** `Console.start_from_job` builds a `Pick` from the result file (the app never writes into the watch folders), starts
the generation linked to the task, and runs the stills; on a finished **video** `attach_video_from_job` attaches and slices it. A video job needs a video sheet **approved at G3**.

### The durable queue and workers (`generation/jobqueue.py`, migration `007_job_queue`)

By default a job is fulfilled by a thread of the server, so a server restart loses the wait and the follow-up. With **`MIRSAL_JOB_MODE=queue`** (and Postgres up) the server only *enqueues* the job
(`job_queue` row `QUEUED`); one or more **`python -m mirsal worker`** processes claim rows (`FOR UPDATE SKIP LOCKED`: two workers never get the same job), run `jobs.fulfil` and mark the row; the
server's ingest loop then follows up every `DONE` row exactly once (`Console.follow_up`: a sheet starts the stills run, a video is attached and sliced), leased for ten minutes so a crash before it
finished just lets the lease run out. Jobs that were finished while the server was down are followed up when it starts.

| row | meaning |
|---|---|
| `QUEUED` | waiting (also after a retry with backoff 30 s, 60 s, ...) |
| `RUNNING` | a worker holds it (`locked_by`, `locked_at`); a row with no finish after the job timeout + 5 min is **reaped** back to `QUEUED` (the ticket in the job file makes the next run resume, not pay again) |
| `DONE` | the job file holds the result; `ingested_at` says the server followed up |
| `FAILED` | **the provider** said no: never retried automatically, because a retry can spend credits; a human retries (`mirsal queue retry J004`, or the Studio's Retry) |
| `DEAD` | **the worker itself** failed `max_attempts` (3) times (disk, a bug): needs a human |

`out/jobs/J###.json` stays the truth for the request, ticket and result; the table only says who runs it and when (`mirsal queue sync` re-enqueues unfinished job files after a database reset).
Workers add durability and isolation, **not paid concurrency**: the paid-call lock is shared, so one paid call runs at a time on the machine however many workers there are.
`GET /api/health` shows the mode and the counts; `mirsal queue status` prints them with the rows that need a human.

## Credits and usage (`generation/usage.py`, `out/model_calls.jsonl`)

Every paid or model call is a ledger line (what, model, params, cost, latency, Higgsfield id, output). `usage.summary` rolls it up by model, by kind, by request (job → task → generation)
and per call; `spent_today` feeds the cap. Estimates match the balance exactly (checked: 7.75 estimated, 7.75 spent). `GET /api/higgsfield` gives the live balance (cached 6 s).

## Prepared instead of paid (`flow/sources.py`)

When Higgsfield is connected, a request that names a prepared subject is served from the watch folder instead of a paid call. The signature rule is one sentence: a request is served from the watch folder when one whole word of a prepared subject's folder name, singularised and ignoring generic, appears as a whole word of the request.

| request | served from |
|---|---|
| teddy bear for school | teddy_bear |
| teddy | teddy_bear |
| bear in a teddy costume | teddy_bear |
| bear | teddy_bear |
| emoji keyboard | generic_emojis |
| generic emojis laughing | generic_emojis |
| emojis | generic_emojis |
| emoji | generic_emojis |
| a dragon dancing | Higgsfield (no signature word) |
| school stickers | Higgsfield (no signature word) |

Preferring prepared is a setting, default on: `MIRSAL_PREFER_PREPARED` in `mirsal/.env` (wins when set), else the owner's switch in Settings (`out/prepared.json`, `POST /api/prepared/setting`; `GET /api/prepared/match?prompt=` says which subject matches). A prepared batch runs the same golden path and gates with the same screens; it records its real source (the watch folder, folder number, file names, `source.prepared: true`), costs 0 credits, and creates no job, task or ledger line. A fresh request starts at variant 1 again; Create more walks the remaining variants; **Make a new one** (the Studio header, the chat plan card's chip) draws a fresh provider sheet at the normal price. The batch carries a small Prepared chip for owner/admin only. Decided with Haitham, 2026-10-05: whole-word signature match (both near-misses match), variant 1 again, the chip for staff only.

## A manual download completes its failed job (`flow/imports.py`)

When a provider download fails after the ticket was paid (J022-J025: the certificate store), the downloaded-by-hand file completes that job instead of starting an unrelated batch. The file links by its provider id (`hf_<date>_<time>_<uuid>`, `imports.job_id_of`), the job picked in Import from Higgsfield, or the dialog's explicit choice ("Is this the result of …?": the person's own failed jobs only, prompt, time and thumbnail; exactly one match links automatically, several ask, import-as-new skips the link). Completing a job sets it `DONE` (`recovered_by: "manual import"`, no second charge): a sheet job's batch is built from the job's own saved plan and carries its external task id (cells, tags, emoji as approved, one human history line "recovered from a manual download of task \<uuid\>"); a video job attaches to the job's own destination batch and sheet. The existing recovery actions (`generation/recovery.py` Check / Continue / Retry) stay for when the provider itself can still download.

## API (all JSON, addressable by id)

`GET /api/higgsfield`, `/api/models`, `/api/usage`, `/assets/{styles,vendors,brand}/…`; `POST /api/live/cost`, `/api/live/ref` (raw image), `/api/live/sheet`, `/api/live/video`;
the job endpoints (`/api/jobs`, `/api/jobs/<id>[/claim|done|fail|requeue]`) from the first pass are unchanged.

## The Studio (additive; every control calls one of the endpoints above)

`composer.js` replaces the old input row of the Studio with the Generate menu: a dark stage lit by the logo's blue, the prompt as its centre, reference images inside the prompt box
(button, drag-and-drop or paste), a bar with the **model** chip (opens the model dialog), **stroke** (none / thin 4 / medium 8 / bold 12 / max 16 px, previews drawn with the real width),
the **AI enhancer** switch and **Generate** with its price inside the button (Higgsfield-style); below it the six style cards. Generate **starts at once** with the selection made before:
no confirmation, a click is the decision (it is refused only when the price is above the balance). `composer.js` also puts the **Higgsfield credits at the top** (a pill whose drop-down shows the balance, today's spend, the Usage log and the recent batches; a click on a batch in that list, or on a row of the Earlier-batches column, **presents it in the Studio**, `ACT.hopen`), and `live.js` holds the credits chip (bottom of the rail, opens the **Usage** log), the **edge bar** (Stroke / Trim test on one thumbnail, Apply / Cancel / Undo), the **Earlier batches** column (the shared second column on Studio and Create: a plain title, then **one row per batch**, vertical and scrolling, no Load more: the stickers as the sheet's own 3x3 / 2x2 grid with its title, `G###`, ready / animated counts and edited time; every batch ever made from `GET /api/history` (`grid` + `cells`, read out of `result.json`), 50 per request, the next page asked for when the list is scrolled near its end; **a click presents that batch and only that batch** in the Studio (`ACT.hopen`: the session becomes exactly that batch, so its working Request > Prompt > Stickers > Animation > Pack header, Animate / Add to a pack / Make a video act on it) and below that view its per-sticker history and the AI captions stay (`GET /api/generations/<id>/history`, `/captions`), re-read while the batch is edited or still working), the model
dialog, the job cards that follow a running sheet or Kling job, and the **animation box under the green screen** on each batch without a video: a model drop-down and one priced button.
It sends one request: the server approves the kept stills, builds and approves the video sheet (`gates.quick_sheet`, the click is the decision) and starts the Kling job; "use my own tool"
keeps the manual download/upload path. Prepared sheets stay one click away in the chips under the stage (they never trigger a generation); without the Higgsfield CLI the old
prepared-sheet lookup runs. Everything below the stage (results, gates, packs) is unchanged.

## Commands

`mirsal prompt …`, `mirsal jobs`, `mirsal job …`, `mirsal hf status | models [--type image|video] [--refresh] | run J###`, `mirsal doctor` (reports the CLI, credits and plan).

## Tests (`tests/test_live.py`, `test_jobs.py`, `test_expander.py`; fake CLI, no credits)

Ticket-first and resume, the daily cap, the Kling 4k ban, catalog defaults, usage roll-up, prompt v2 / v3 properties, the AI enhancer (never while typing, off = no call, on = expand then send,
failure = fallback with a reason), references, a full run through the console (request → sheet job → stills → G2 → video sheet → G3 → Kling job → sliced), history paging, the gap and Loop,
Retry, the named export folders and their root, allow anyway / allow all, **the edge** (a preview writes nothing; Apply makes one snapshot; the same edge twice adds none; Undo restores; the
video and the pack commit a pending edge) and **the blue screen** (detect, key, video sheet, and the mark only when it is blue, on a synthetic blue sheet; the real failed batch G006 was re-run on a copy: 0/9 -> 9/9). The tests run through the tiers of `docs/testing.md` (the store and pool classes skip when Postgres is down); the full `unittest discover` is not a routine gate and runs only if Haitham asks.

## Not built

The vision judge is built (`mirsal/vision/`, see [`agent-and-chat.md`](agent-and-chat.md)) but **uncalibrated** until Haitham labels 30 stickers; `python -m mirsal measure-cells` is built and its first
numbers are in [`measurements.md`](measurements.md) (the target "nothing flagged" needs a re-run with Kling `pro`); the sheet-vs-single and outline decisions, the 20-prompt AI lab rating, and the
leftovers of the original planner design that wait for Haitham's word (UAE content rules, English + Arabic Telegram keywords, 4x4 sheets) are listed in `docs/backlog.md` (live generation).
`out/jobs/*.json` and `out/model_calls.jsonl` are mirrored into Postgres (write-through and `db import`).

## The Prompt tab writes the prompts (2026-10-02)

The Studio's Prompt tab (a batch's own, and the same tab inside an Earlier-batches card) is editable: what is typed is what is SENT. Server side: `POST /api/live/sheet {prompt, from_generation?, sheet_prompt?}` starts a NEW sheet from that
batch's own plan (same cells, same tags) with the person's text in place of the template's sheet prompt (`prompter.apply_custom` / `clean_custom`, at most 6000 characters, empty or non-text is a 400; the text lives in the new task's `plan.custom` and on the
batch as `custom_prompts: ["sheet_prompt"]`, and survives a rebuild of the plan); `POST /api/live/video {generation, video_prompt?}` sends the person's video prompt verbatim and keeps what was sent on the video sheet (`video_prompt_sent`, `video_prompt_custom`).
Both are recorded on the job (`request.custom_prompt`) and stay under the Idempotency-Key. A member can only start from a batch they own (404 otherwise). Client side (`generate.js`): drafts live per batch and kind (`PD`), so a refresh while a batch works never loses what was
typed (and the poll does not re-render while a box has the focus); the buttons say "with my prompt" only when the text really differs from the template's, show the live price, and are off without Higgsfield; "Generate video" needs a kept sticker and a sheet that has no returned video
(the engine does not animate a sliced sheet twice); Reset puts the template back. The templates themselves are never edited (`_v4`, never edit one that was used).

## Several paid jobs at once, and text-only video (2026-10-02)

- **Parallel jobs** (`generation/jobs.py`): Haitham asked for several sheets / effects "all at once". `fulfil` holds the paid lock (`_paid`: in-process lock + `out/.paid.lock`) only while it decides, checks the daily cap, creates the provider job and stores its ticket (rule 10: the ticket is stored before anything waits). The wait and the download are outside it, inside one of `paid_parallel()` places (`MIRSAL_PAID_PARALLEL`, default 3, 1 = the old one at a time, max 8) that is taken **before** a job is created, so at most that many provider jobs exist at once. The ledger line (`done`) is written under the lock again. The daily cap counts the credits of jobs already in flight (`_inflight`, CLAIMED jobs with a ticket and `cost_estimate`). One waiter per ticket: a second run of a job that is being waited for (another thread, or another live process, `waiting_pid` on the job file) returns the job as it stands and pays nothing. Tests: `tests/test_live.py::FulfilTests`.
- **Text-only video** (`request.t2v = true`): no start image is required (Kling v3.0's `start_image` is optional); any other video job still refuses a missing start image. Used by the particle effects: the prompt is built by `generation/effect_prompts.py` (template `effect_video` v1, see `docs/effects.md`). Kling pro, 3 s, 1:1 costs **4.5 credits** (std 3.75; the standing rule is pro).
