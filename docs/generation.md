# Live generation: how it is built

A typed request defaults to a 2×2 sheet of 4 stickers made by Higgsfield, and an approved video sheet becomes a Kling animation. Explicit 3×3 remains available. Both go through the **unchanged** engine and review
gates; the file store is the primary state (Postgres mirrors it, see [`store-and-search.md`](store-and-search.md)). What the Higgsfield CLI offers, with measurements: [`higgsfield.md`](higgsfield.md).

```
request ─(prompt template v3 + style + stroke [+ AI enhancer] [+ references])─► task (G1 approval)
        ─► sheet job ─► Higgsfield CLI (Nano Banana 2, 2k) ─► out/jobs/J###/result.png
        ─► Pick(sheet) ─► the unchanged stills run ─► G2 ─► video sheet (G3) ─► video job ─► Kling v3.0 ─► attach + slice ─► animations ─► pack
```

## Sections

New-plan defaults and the independently animated cell prompt are documented in
[2×2 and independent video sequences](generation/19-independent-cell-video-and-2x2.md).

This is an index: each section is its own file under [`generation/`](generation/); read only the one a task needs.

| section | what it covers |
|---|---|
| [Prompts (`generation/prompter.py`, `generation/emotions.py`, `generation/styles.py`, `prompts/templates/`)](generation/01-prompts-generation-prompter-py-generation-emotio.md) | Template-locked. A saved template per grid (`sheet_3x3`, `sheet_2x2`, `single_1x1`, `video`) is filled from a small slot JSON; nobody free-writes a prompt.… |
| [The Higgsfield CLI (`generation/higgsfield.py`, `generation/model_catalog.py`)](generation/02-the-higgsfield-cli-generation-higgsfield-py-gene.md) | `generation/higgsfield.py` is a thin subprocess wrapper: `account`, `cost`, `create` (WITHOUT waiting, returns the job id), `wait`, `download`, and `dump_mod… |
| [Video quality, the gap, Loop and the edge (measured on G002, 2026-10-01)](generation/03-video-quality-the-gap-loop-and-the-edge-measured.md) | Pixels. The first Kling clip was `std`: 960x960 for the whole sheet, 320 px per slot, the sticker filled 55% of its slot, so about 176 px of picture were s… |
| [Files and names](generation/04-files-and-names.md) | The engine keeps its files in `out/G00N/` and `out/jobs/` under its own names (`{media}-{subject}-{action}-{UTC time}-{hash}.{ext}`, `runtime/names.py`; olde… |
| [The screen colour (blue key)](generation/05-the-screen-colour-blue-key.md) | The sheet prompt asks for the key in `slots.key_colour` (green; blue when the AI enhancer sees a green subject, `expander.GREEN_WORDS`). What the model ret… |
| [The queue (`GET /api/jobs`, `live.js`)](generation/06-the-queue-get-api-jobs-live-js.md) | The Queue is a small panel fixed at the bottom left next to the credits (collapsed: "N running · stage · elapsed of about typical", or "N failed"; open:… |
| [Allow anyway (a human override, `gates.allow_animation`)](generation/07-allow-anyway-a-human-override-gates-allow-animat.md) | An animation that Python blocked for leaving or crossing its slot (`inside_slot`, `cross_slot`) has no file, because the block saves the encode. The user… |
| [Jobs (`generation/jobs.py`)](generation/08-jobs-generation-jobs-py.md) | `out/jobs/J###.json` (`REQUESTED/CLAIMED/DONE/FAILED/TIMEOUT`; a job created since 2026-10-04 is labelled `J058-<subject>-<kind>.json` with its files in `J05… |
| [Credits and usage (`generation/usage.py`, `out/model_calls.jsonl`)](generation/09-credits-and-usage-generation-usage-py-out-model.md) | Every paid or model call is a ledger line (what, model, params, cost, latency, Higgsfield id, output). `usage.summary` rolls it up by model, by kind, by requ… |
| [Prepared instead of paid (`flow/sources.py`)](generation/10-prepared-instead-of-paid-flow-sources-py.md) | When Higgsfield is connected, a request that names a prepared subject is served from the watch folder instead of a paid call. The signature rule is one sente… |
| [A manual download completes its failed job (`flow/imports.py`)](generation/11-a-manual-download-completes-its-failed-job-flow.md) | When a provider download fails after the ticket was paid (J022-J025: the certificate store), the downloaded-by-hand file completes that job instead of starti… |
| [API (all JSON, addressable by id)](generation/12-api-all-json-addressable-by-id.md) | `GET /api/higgsfield`, `/api/models`, `/api/usage`, `/assets/{styles,vendors,brand}/…`; `POST /api/live/cost`, `/api/live/ref` (raw image), `/api/live/sheet`… |
| [The Studio (additive; every control calls one of the endpoints above)](generation/13-the-studio-additive-every-control-calls-one-of-t.md) | `composer.js` replaces the old input row of the Studio with the Generate menu: a dark stage lit by the logo's blue, the prompt as its centre, reference image… |
| [Commands](generation/14-commands.md) | `mirsal prompt …`, `mirsal jobs`, `mirsal job …`, `mirsal hf status / models [--type image/video] [--refresh] / run J###`, `mirsal doctor` (reports the CLI,… |
| [Tests (`tests/test_live.py`, `test_jobs.py`, `test_expander.py`; fake CLI, no credits)](generation/15-tests-tests-test-live-py-test-jobs-py-test-expan.md) | Ticket-first and resume, the daily cap, the Kling 4k ban, catalog defaults, usage roll-up, prompt v2 / v3 properties, the AI enhancer (never while typing, of… |
| [Not built](generation/16-not-built.md) | The vision judge is built (`mirsal/vision/`, see `agent-and-chat.md`) but uncalibrated until Haitham labels 30 stickers; `python -m mirsal measure-cells`… |
| [The Prompt tab writes the prompts (2026-10-02)](generation/17-the-prompt-tab-writes-the-prompts-2026-10-02.md) | The Studio's Prompt tab (a batch's own, and the same tab inside an Earlier-batches card) is editable: what is typed is what is SENT. Server side: `POST /api/… |
| [Several paid jobs at once, and text-only video (2026-10-02)](generation/18-several-paid-jobs-at-once-and-text-only-video-20.md) | Parallel jobs (`generation/jobs.py`): Haitham asked for several sheets / effects "all at once". `fulfil` holds the paid lock (`_paid`: in-process lock + `o… |
