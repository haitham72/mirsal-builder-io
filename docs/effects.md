# docs/effects.md — particle effects: the burst that Telegram plays when you press an emoji

**Status (2026-10-02): built and tested: the engine, the prompts, the vision step, the `E###` lifecycle, the `/api/effects` routes, and the screen (Create > Particle effects, `#/effects`, checked in a browser on a scratch copy). The AI-chat entry is built (§8). NOT built: an AI-drawn sprite sheet for the simulated mode, real tile art / examples (§8).**
Haitham asked for this on 2026-10-02: when someone presses an emoji in Telegram a burst of small pieces explodes from it (a strawberry bursts strawberries, a heart hearts). The product
is the same thing as **animated stickers**: one 3-second WEBM per effect, starting from nothing and ending with nothing, tagged with the source emoji.

## 1. What an effect is

- **Input: a pack** (an emoji / sticker pack in the library). The effect is made per sticker of the pack, and the effect stickers are added to the same pack (or a new one) as animated
  stickers linked to their source and tagged with its emoji (Telegram then offers them for that emoji).
- **Smart, not literal.** The burst is made of *related pieces*, never the picture itself: Batman gives bat signals and bats (not Batman), Superman cape pieces and shield badges, a jewelry
  sticker small gold bars and diamonds, a cat paws / ears / fish, a heart hearts, a strawberry strawberries + leaves + seeds. A vision model reads each sticker (`vision/effect_plan.py`) and
  answers a small JSON `{subject, elements, mood}`; code lints it; a table of ~60 emoji and subjects (`LEXICON`) answers when no model may or can. A pack of eight Superman poses is ONE group
  (one video / one sprite sheet), and a sticker's mood picks its motion (sad rains, happy bursts, calm is a fountain).
- **Output: Telegram video stickers.** WEBM VP9 + alpha, 512 x 512, 30 fps, 3 s, <= 256 KB, empty on the first and the last frames (`engine/effect_video.py`, `engine/particles.py`).

## 2. Two ways to make the burst (both built at the engine level)

| | A. Simulated (`engine/particles.py`) | B. Video from scratch (`generation/effect_prompts.py`, `engine/effect_video.py`) |
|---|---|---|
| pieces | sprites: the pack's own stickers, or an AI-drawn sheet of the pieces (an ordinary batch through the golden path, cut into cells) | whatever Kling draws from the text |
| motion | a seeded, deterministic simulator with sliders: **explosion magnitude, gravity (negative floats up), vortex (swirl, either direction)**, plus count, size, spin, lifetime, presets (burst, fountain, vortex, rain, confetti) | Kling, from a timeline in the prompt |
| cost | the sprite sheet (about 2 credits per subject group) once; every re-tune is free | **4.5 credits per clip** (Kling pro, 3 s, 1:1) for 4 cells (2x2) or 9 (3x3) |
| start / end empty | by construction (pieces spawn from frame 3 and are all gone 0.2 s before the end) | asked for in the prompt, checked, and repaired by `settle` (a fade) |
| preview | the same engine at 256 px (0.15 s), so the sliders are live | no |

## 3. Video from scratch: what was measured (real Kling, 2026-10-02)

Text only: no start image (Kling's `start_image` is optional; `jobs.fulfil` takes `request.t2v = true`). The prompt is built by code from the plan (`effect_prompts.video_prompt`, template
`effect_video` v1: screen colour, an invisible rows x cols grid, a timeline "0.0-0.4 s empty, 0.4 s the pieces appear at the centre and burst in a vortex growing a little, 1.2 s gravity,
2.6 s empty again", one variation per cell). The screen is **green unless a piece is green** (leaves, grass, a frog: then blue, `key_colour_for`); the screen that is really there wins
(`chroma.detect_key`). Two clips for the strawberry (J037 2x2, J038 3x3, 4.5 credits each, 9.0 in total, both in `out/jobs/` and `out/model_calls.jsonl`), judged by numbers only:

| | 2x2 (J037) | 3x3 (J038) |
|---|---|---|
| clip | 1440x1440, 24 fps, 3.04 s | 1440x1440, 24 fps, 3.04 s |
| every cell empty at the start | **4 of 4** | **9 of 9** |
| the burst starts | 0.33-0.38 s (asked 0.4) | 0.29-0.54 s |
| pieces crossing a cell edge (worst frame, share of the edge strip) | 0.0-0.24 % | **10-26 %** |
| empty on the last frames | 1 of 4 (the others 0.7 % covered: still falling) | **0 of 9** (2.5-10 % covered) |
| after the engine (`finish_cell`) | 4 READY, 199-237 KB, 3 with the warning `effect_tail_faded` | not worth cutting: the cells overlap |

**Conclusion: 2x2 is the default and holds up; 3x3 is offered but is poor (pieces cross cells, nothing ends empty) and says so.** The "green frame as start and end image" variant was not tried
(2x2 already works, so it was not worth 4.5 credits).

## 4. What is enforced and what is only said

Haitham's standing rule (2026-10-02): **never a block a person cannot get past** (`CLAUDE.md` rule 10). So the only hard failures of an effect are the limits Telegram itself enforces
(`engine/effect_video.TECHNICAL`: size, codec, dimensions, fps, duration, no audio, alpha). Everything about the effect is a **WARN with the reason**, `engine/effect_checks.py` (PASS or WARN, never
BLOCK): `effect_empty_start`, `effect_empty_end`, `effect_has_burst`, `effect_not_a_still`, `effect_inside_cell`; plus `effect_tail_faded` when the engine repaired a clip that had not emptied.
Anim checks that describe a character that stays itself (`loop_seam`, `alpha_stable`, `identity_kept`, `sharpness`, `motion_present`) do not apply to a burst (`NOT_FOR_BURSTS`).

## 5. Money and concurrency

- Nothing is spent without the price shown and a go-ahead (rule 13). A real video costs 4.5 credits; the page shows it before the click.
- Several provider jobs may be in flight at once (Haitham, "all at once"): `jobs.fulfil` now holds the paid lock only while it decides, checks the daily cap, creates the job and stores its
  ticket; the wait is outside it, bounded by `MIRSAL_PAID_PARALLEL` (default 3, 1 = the old one-at-a-time), and the daily cap counts the jobs already in flight. One waiter per ticket.

## 6. Code map

| file | what |
|---|---|
| `engine/particles.py` | `ParticleParams`, `PRESETS`, `simulate(sprites, params) -> frames`, `to_webm`, `preview_webp` (pure, deterministic, 0.5 s at 512 px) |
| `engine/effect_checks.py` | the PASS / WARN checks, `coverage_curve` |
| `engine/effect_video.py` | `cut_cells` (key a returned clip into cells), `resample` (Telegram's clock), `settle` (empty ends by construction), `finish_cell`, `encode_and_check` (shared with mode A) |
| `generation/effect_prompts.py` | template `effect_video` v1: `lint_plan`, `video_prompt`, `key_colour_for`, `describe` |
| `vision/effect_plan.py` | `analyse(stickers, allowed=...)` (vision model or table, groups, moods -> presets, consent as for captions), `lexicon_plan` |
| `generation/jobs.py` | `request.t2v` (no start image), parallel jobs (`paid_parallel`) |
| tests | `test_particles` (38), `test_effect_video`, `test_effect_plan`, `test_effect_prompts`, `test_live.FulfilTests` (t2v, parallel, cap in flight) |

## 7. The contract (built: `flow/effects.py`, `console/server.py` `_effects`, `docs/api.md`)

`E###` records under `out/effects/E###/effect.json` `{id, pack_id, pack_name, mode: sim|video, grid, note, status: NEW|READY|VIDEO_REQUESTED|RESULTS|DONE|ERROR, stickers[{sticker_id, name, emoji, file, src}],
groups[{id, subject, elements, style, key, stickers, moods, preset, by, sprites}], per_sticker, notes, analysed_by, video{group: {job, grid, key, status, cells, cost}}, results[{id, mode, group, cell | sticker_id,
file, bytes, status, checks, warnings, blocks, metrics, params, added_to}], history[]}`, `src/` (the source pictures), `results/R###.webm`, `previews/<digest>.webp`. Routes: `GET/POST /api/effects`,
`GET /api/effects/{id}`, `POST .../analyse | plan | estimate | video | preview | render | add`. The analysis runs in a background thread (consent: `allow_vlm`), the video needs `go: true`, a result that breaks a
Telegram limit is FAILED and cannot be added, everything else can. **Adding is the person's click** (history `APPROVE`); a video result goes to the stickers of its group cell by cell (round robin).

## 8. The screen (built) and what is open

The screen (`console/effects.js`, `studio.css` `.fx-*`): 1 choose the pack, 2 which stickers, 3 Simulate or Video (2x2 default, a warning on 3x3), a note for your own pieces, then the effect: per group the pieces
(editable chips, the screen colour, who chose them), Simulate rows with presets, **explosion / gravity / vortex / pieces / spin sliders** and a live preview (debounced, the same engine at 256 px), Render; Video with the
price in the button (`estimate`, free) and the job's state; the results with their warnings in words and "Add N to the pack". The Queue pill cannot cover the last buttons (`.page.fx` bottom padding).

Open:
1. **The AI chat entry (built 2026-10-03)**: intent `EFFECTS` (`resolver.classify`: particle / burst / explosion / confetti + effect / pack / sticker / emoji), node `graph.n_effects`: finds the library pack the words name (or the only pack; else asks which, with chips), calls `tools.effects_start` (the same `fx.create` + background `analyse` as `POST /api/effects`, owner only), and answers with an `effects` card linking `#/effects/E###`. Nothing is spent in chat; the video's price is shown on the screen's button. Open: refining the pieces from chat ("only bat signals").
2. **An AI-drawn sprite sheet for the simulated mode** (a button that makes a 2x2 sheet of the pieces through the normal batch pipeline with outline 0; today a person makes it in the Studio and types the batch number).
3. Real tile art / examples, mobile layout check, 3x3-specific prompt, the green-frame start/end variant only if 2x2 ever fails.
4. A real end-to-end paid run from the screen (the price and the job path are tested on a fake CLI; the real Kling path was exercised by the two experiment clips through `jobs.fulfil`).
