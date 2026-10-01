# Phase 2 — live generation: how it is built

A typed request becomes a sheet of 9 stickers made by Higgsfield, and an approved video sheet becomes a Kling animation. Both go through the **unchanged** Phase 1
engine and review gates; the file store is the only state (no database). What the Higgsfield CLI offers, with measurements: [`higgsfield.md`](higgsfield.md).

```
request ─(prompt template v2 + style + stroke [+ AI enhancer] [+ references])─► task (G1 approval)
        ─► sheet job ─► Higgsfield CLI (Nano Banana 2, 2k) ─► out/jobs/J###/result.png
        ─► Pick(sheet) ─► the unchanged stills run ─► G2 ─► video sheet (G3) ─► video job ─► Kling v3.0 ─► attach + slice ─► animations ─► pack
```

## Prompts (`prompter.py`, `emotions.py`, `styles.py`, `prompts/templates/`)

- **Template-locked.** A saved template per grid (`sheet_3x3`, `sheet_2x2`, `single_1x1`, `video`) is filled from a small slot JSON; nobody free-writes a prompt. New plans use **v2**
  (`TEMPLATE_VERSION`); a saved plan keeps its own version, and `render_plan(..., 1)` still rebuilds the v1 text exactly.
- **v2 wording is measured, not guessed.** v1 said "sticker" (image models answer with a white die-cut border) and "equal cells / row-major" (Nano Banana 2 painted a
  checkerboard of two greens: bg G 215/252 across cells). v2 says "one illustration of 9 characters arranged in 3 rows of 3 on a single seamless background",
  lists them as `Character N: …`, forbids outlines, and asks for one identical key colour. Measured on Nano Banana 2 at 2k: white-ring share 4.8% → 0.0000, per-cell
  green spread 51 → 0. The stroke is the engine's `outline` (Edge), never the model's.
- **Styles** (`styles.py`): flat, toon shade, glossy 3D, soft clay 3D, realistic, hand-drawn; each is a phrase for the template's Style line. Tile images are optional files
  in `console/assets/styles/<id>.(png|jpg|webp|svg)`; without one a generated placeholder is served.
- **Emotions** (`emotions.py`): a bank of ~35 expressive entries (label = expression + body language, emoji, motion) in nine mood groups; `pick(n, seed)` chooses one per group,
  deterministically per request, so a sheet never repeats a mood. The built-in school and birthday sets carry motions too.
- **Motion per character.** Every cell has a `motion` sentence; `video_v2` lists them as numbered lines, so Kling animates each character differently.
  `Console.video_prompt_for` rebuilds the video prompt for the slots actually approved (empty slots get no motion).
- **References.** Up to 4 images, stored by `POST /api/live/ref` as `out/refs/R###.<ext>`, listed on the job (`request.refs`), sent as repeated `--image-references`, and
  explained to the model by `prompter.REFERENCE_CLAUSE`. A model that does not take references refuses them.
- **AI enhancer** (`expander.py`, `llm.py`, OpenAI): **off by default and never called while typing.** On, `POST /api/live/sheet {ai: true}` first has the model write the subject
  description and 9 distinct, expressive cells (label, motion, key, tags, emoji), lints them (one repair round), and only then builds and sends the prompt. Off, the typed text goes
  into the template with the built-in emotion sets. A failed AI step falls back to the built-in sets and the response says why (`expanded_by`, `expand_error`).
  `mirsal prompt "<request>" [--ai]` prints the same plan; `prompt lab` runs 20 inputs (English, Arabic, Arabizi).

## The Higgsfield CLI (`higgsfield.py`, `model_catalog.py`)

- `higgsfield.py` is a thin subprocess wrapper: `account`, `cost`, `create` (WITHOUT waiting, returns the job id), `wait`, `download`, and `dump_models`/`load_models` (the full list:
  34 image, 38 video, 8 audio, 1 text model with every parameter, cached in `out/higgsfield_models.json` for a day). It calls the vendored `hf.exe` directly with an argv list
  (the npm `.cmd` shim would let cmd.exe interpret `&`, `%` or quotes in a prompt). It never runs `auth token`. `MIRSAL_NO_REAL_CLI` (set by `tests/__init__.py`) makes any real call fail:
  no test can spend credits. `NEVER` bans Kling `4k`.
- `model_catalog.py` is the selector's data: 8 image models (Nano Banana 2 / Pro / 2 Lite, GPT Image 2 / 2.5 with the flare/sunburst variant, Seedream 5.0 Pro / Flash / Lite) and
  2 video models (Kling v3.0 always `pro`, Grok Video 1.5 always 1080p; nothing below 1080 is offered), each with its selections; `resolve(kind, model, options)` validates and returns the CLI's job_type and params. Every other
  model of the dump is selectable too (options generated from its own parameter list). Defaults: Nano Banana 2 at 2k, Kling v3.0 pro, 3 s.
- Logos: `console/assets/vendors/<logo>.svg` (Google, ByteDance, Kuaishou fetched once from the Simple Icons set); OpenAI and xAI get a monogram until Haitham drops `openai.svg` / `xai.svg`
  into that folder. The app logo is `console/assets/brand/mirsal-logo.png` (the white-background JPEG in `ref/` made transparent).

## Video quality (measured on G002, 2026-10-01)

The first Kling clip was `std`: 960x960 for the whole sheet, 320 px per slot, and the sticker filled only 55% of its slot, so about 176 px of picture were scaled 2x to the 512 px sticker:
that is the pixelation. Now Kling is always `pro` (1440 px, 480 px per slot) and `slot_fill` is 0.66 (was 0.55; the gap between two stickers drops by about a quarter, from nearly a whole
sticker wide to about 60% of one), so the picture per sticker is about 317 px. A 2x2 sheet would give each sticker 2.25 times the pixels of a 3x3 one (open question for Haitham).
`video_v2` also asks for "a wide range of emotions" and "highly expressive faces and bodies".

## Jobs (`jobs.py`)

`out/jobs/J###.json` (`REQUESTED|CLAIMED|DONE|FAILED|TIMEOUT`) as before, plus `params`, `cost_estimate` and, for sheets, the `generation` it started. `fulfil(out, jid)`:

1. resolves the selection through the catalog (and refuses references the model cannot take);
2. `generate cost` (and the optional daily cap `MIRSAL_DAILY_CREDITS`, refused before anything is paid);
3. `generate create` **without `--wait`**, then `claim` with the returned id **immediately** (ticket first, mirrored into `out/tasks/NNN.json`);
4. `generate wait`, download the result, `done` (copies it to `out/jobs/J###/result.<ext>`, writes the ledger line with cost, params and the Higgsfield id).

A job already CLAIMED resumes by its ticket and never creates a second paid job. One paid call at a time (`_PAID` lock). Provider errors end as `FAILED` with the reason.
`Console.fulfil_async` runs it in a thread; on a finished **sheet** `Console.start_from_job` builds a `Pick` from the result file (the app never writes into the watch folders), starts
the generation linked to the task, and runs the stills; on a finished **video** `attach_video_from_job` attaches and slices it. A video job needs a video sheet **approved at G3**.

## Credits and usage (`usage.py`, `out/model_calls.jsonl`)

Every paid or model call is a ledger line (what, model, params, cost, latency, Higgsfield id, output). `usage.summary` rolls it up by model, by kind, by request (job → task → generation)
and per call; `spent_today` feeds the cap. Estimates match the balance exactly (checked: 7.75 estimated, 7.75 spent). `GET /api/higgsfield` gives the live balance (cached 6 s).

## API (all JSON, addressable by id)

`GET /api/higgsfield`, `/api/models`, `/api/usage`, `/assets/{styles,vendors,brand}/…`; `POST /api/live/cost`, `/api/live/ref` (raw image), `/api/live/sheet`, `/api/live/video`;
the job endpoints (`/api/jobs`, `/api/jobs/<id>[/claim|done|fail|requeue]`) from the first pass are unchanged.

## The Studio (additive; every control calls one of the endpoints above)

`composer.js` replaces the old input row of the Studio with the Generate menu: a dark stage lit by the logo's blue, the prompt as its centre, reference images inside the prompt box
(button, drag-and-drop or paste), a bar with the **model** chip (opens the model dialog), **stroke** (none / thin 4 / medium 8 / bold 12 / max 16 px, previews drawn with the real width),
the **AI enhancer** switch and **Generate** with its price inside the button (Higgsfield-style); below it the six style cards. Generate **starts at once** with the selection made before:
no confirmation, a click is the decision (it is refused only when the price is above the balance). `live.js` holds the credits chip (bottom of the rail, opens the **Usage** log), the model
dialog, the job cards that follow a running sheet or Kling job, and the **animation box under the green screen** on each batch without a video: a model drop-down and one priced button.
It sends one request: the server approves the kept stills, builds and approves the video sheet (`gates.quick_sheet`, the click is the decision) and starts the Kling job; "use my own tool"
keeps the manual download/upload path. Prepared sheets stay one click away in the chips under the stage (they never trigger a generation); without the Higgsfield CLI the old
prepared-sheet lookup runs. Everything below the stage (results, gates, packs) is unchanged.

## Commands

`mirsal prompt …`, `mirsal jobs`, `mirsal job …`, `mirsal hf status | models [--type image|video] [--refresh] | run J###`, `mirsal doctor` (reports the CLI, credits and plan).

## Tests (`tests/test_live.py`, `test_jobs.py`, `test_expander.py`; fake CLI, no credits)

Ticket-first and resume, the daily cap, the Kling 4k ban, catalog defaults, usage roll-up, v2 prompt properties, the AI enhancer (never while typing, off = no call, on = expand then send,
failure = fallback with a reason), references, and a full run through the console: request → sheet job → stills → G2 → video sheet → G3 → Kling job → sliced.

## Not built

The vision judge (S6, with Haitham's 30 labels), `measure-cells` and the `slot_fill` tuning on real Kling runs (S4), the sheet-vs-single and outline decisions (S7), the 20-prompt AI lab rating (S5).
`out/jobs/*.json` and `out/model_calls.jsonl` keep the shapes `phase_03.md` expects (only fields were added), so Phase 3 imports them unchanged.
