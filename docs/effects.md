# docs/effects.md — particle effects: the burst that Telegram plays when you press an emoji

**Status: engine and prompts built and measured on real Kling clips (2026-10-02); the pack-level flow, routes, the `#/effects` screen, the Create tile and the chat intent are NOT built yet (§8).**
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

## 7. The contract that is planned (not built)

`E###` records under `out/effects/E###/effect.json` `{id, pack_id, stickers[{sticker_id, name, emoji, group}], mode: sim|video, grid, groups[{id, subject, elements, key, stickers, presets}],
video{job, grid, cells[{index, sticker_id, checks, file}]}, results[{id, sticker_id, file, bytes, checks, params}], history[]}` and routes `GET/POST /api/effects`, `GET /api/effects/{id}`,
`POST /api/effects/{id}/plan` (edit pieces), `/estimate` (price + prompt, free), `/video` (`{go: true}` spends), `/preview` (mode A, WebP), `/render`, `/add` (the click that puts results into the
pack, recorded in the history).

## 8. Open

1. `flow/effects.py` (the E### lifecycle: create, analyse in the background, video job and its `on_done`, per-cell results, preview / render for mode A, add to pack), the routes of §7, `docs/api.md`.
2. Mode A sprites: the pack's own stickers as pieces (free), and the AI sprite sheet as an ordinary batch (`outline 0`, base plan with the pieces as cells).
3. The screen (`console/effects.js`): **Create gets a "Particle effects" tool**, `#/effects`: pick a pack, pick stickers, analyse (edit the pieces), choose Simulate (sliders + live preview) or Video
   (price, 2x2 default), render, add. Also reachable from the AI chat.
4. The chat intent ("make particle effects for my Superman pack") with a plan card (subjects, count, total price).
5. Real tile art / examples; a 3x3-specific prompt (smaller pieces, bigger margins) if 3x3 matters; the green-frame start/end variant if 2x2 ever fails.
