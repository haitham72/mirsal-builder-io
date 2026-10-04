# Particle effects: sprites, simulation and Kling

The durable asset is a sticker-owned particle set; [particles_plan.md](particles_plan.md) describes ownership, persistence and compatibility. This document covers the working `E###` pipeline and its measurements. The current full-flow correction is [sticker_particles_flow.md](sticker_particles_flow.md): animated cell clips must play inside the simulator, with peak PNGs used as posters/fallbacks. Animated restoration and compact UI acceptance are underway; they are not declared complete here.

The final burst is an ordinary animated Telegram sticker in the selected parent pack. Emoji tags make it discoverable; Mirsal does not promise Telegram's native Premium effect behavior. Output is 3-second WEBM/VP9 with alpha, 512×512, 30 fps, ≤256 KB.

## 1. What an effect is

- **Input: selected library stickers.** Their pack supplies context and is the default output destination. Working runs retain pack/group context for legacy routes; durable ownership remains in stickers.
- **Smart, not literal.** The burst is made of *related pieces*, never the picture itself: Batman gives bat signals and bats (not Batman), Superman cape pieces and shield badges, a jewelry
  sticker small gold bars and diamonds, a cat paws / ears / fish, a heart hearts, a strawberry strawberries + leaves + seeds. A vision model reads each sticker (`vision/effect_plan.py`) and
  answers a small JSON `{subject, elements, mood}`; code lints it; a table of ~60 emoji and subjects (`LEXICON`) answers when no model may or can. A pack of eight Superman poses is ONE group
  (one video / one sprite sheet), and a sticker's mood picks its motion (sad rains, happy bursts, calm is a fountain).
- **Output: Telegram video stickers.** WEBM VP9 + alpha, 512 x 512, 30 fps, 3 s, <= 256 KB, empty on the first and the last frames (`engine/effect_video.py`, `engine/particles.py`).

## 2. Sprite sources, one simulator

The editor offers three equal cards for every new version: **Sprites from the sticker** (selected slices/library artwork, free), **AI image sprites** and **Kling animated · from scratch**. All paths feed one simulator, and each saved pass is one row under the sticker (`docs/particles_plan.md` §3). Add more retains both AI choices regardless of a set's initial source. Provider options live under Advanced, not in an extra creation screen.

| Source | Preparation | Simulation input |
| --- | --- | --- |
| AI image sheet | 2×2/3×3 through the particle-sheet pipeline, keyed and cut to tight sprites | Static RGBA frames |
| Kling animated sheet | Text-only nothing-to-nothing 2×2/3×3, keyed and sliced to cell clips | Each sprite's temporal RGBA frames; poster PNG only for thumbnails/fallback |
| Existing artwork | Selected batch slices or library still/animated stickers copied without deleting originals | Static or animated frames matching the source |

`engine/particles.py` supplies seeded motion, presets and the Energy / Float / Swirl controls. Sprite animation plays alongside movement, spin, scale and fade. Preview and final render use the same simulator; motion tuning is free. Directly adding a cut Kling clip through legacy `/api/effects/{id}/add` remains available as a secondary action.

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

**Video prompt v2 (2026-10-03, `effect_video` VERSION 2; v1 is kept byte for byte for stored jobs).** Haitham's real Kling run showed boxes / posters / walls behind every emoji. Cause, in the v1 text: "cell" ten times, "invisible grid of 2 by 2 equal square cells", "square frame". Rule now: the layout appears ONCE and only as quadrant names (top-left, top-right, bottom-left, bottom-right; nine names for 3x3), the background is ONE seamless flat uniform pure #00FF00 (blue when a piece is green), described positively once, static camera, and none of these words is ever in a template text (`effect_prompts.BANNED_WORDS`, a test checks it): square, frame, poster, screen, box, cell, grid, panel, section, tile, border, divider, split, layout, invisible; the aspect ratio is a request parameter and is never written. The 2x2 text is about 900 characters (v1 about 1,480). New WARN-only check **`key_is_seamless`** (`effect_checks.screen_flatness` / `seam_line`, measured on the whole clip before keying: `panel_step`, `quarter_step`, `bg_std`, `seam_line`, limits 10 / 10 / 6 / 40). Measured on the real clips: J037 2x2 (rated great) 2.8 / 3.0 / 1.6 / 27 passes; J038 3x3 (poor) 4.2 / 5.8 / 8.5 warns on bg_std; J039 2x2 (the walls) 20.0 / 9.0 / 11.0 warns on panel_step. The particle image-sheet prompt (`effect_pieces` v2) follows the same rule and says "particles". Not yet measured: a real clip made with the v2 prompt (approved 4.5 credits, `docs/waiting-for-haitham.md` W2).

## 4. What is enforced and what is only said

Haitham's standing rule (2026-10-02): **never a block a person cannot get past** (`CLAUDE.md` rule 10). So the only hard failures of an effect are the limits Telegram itself enforces
(`engine/effect_video.TECHNICAL`: size, codec, dimensions, fps, duration, no audio, alpha). Everything about the effect is a **WARN with the reason**, `engine/effect_checks.py` (PASS or WARN, never
BLOCK): `effect_empty_start`, `effect_empty_end`, `effect_has_burst`, `effect_not_a_still`, `effect_inside_cell`; plus `effect_tail_faded` when the engine repaired a clip that had not emptied.
Anim checks that describe a character that stays itself (`loop_seam`, `alpha_stable`, `identity_kept`, `sharpness`, `motion_present`) do not apply to a burst (`NOT_FOR_BURSTS`).

## 5. Money and concurrency

- Nothing is spent without the price shown and a go-ahead (rule 13). The measured 2026-10-02 video price was 4.5 credits; current calls use the actual free quote, shown on its own line before Generate. Unknown quotes offer Retry price and start nothing.
- Several provider jobs may be in flight at once (Haitham, "all at once"): `jobs.fulfil` now holds the paid lock only while it decides, checks the daily cap, creates the job and stores its
  ticket; the wait is outside it, bounded by `MIRSAL_PAID_PARALLEL` (default 3, 1 = the old one-at-a-time), and the daily cap counts the jobs already in flight. One waiter per ticket.

## 6. Code map

| file | what |
|---|---|
| `engine/particles.py` | `ParticleParams`, `PRESETS`, `simulate(sprites, params) -> frames`, `to_webm`, `preview_webp` (pure, deterministic, 0.5 s at 512 px) |
| `engine/effect_checks.py` | the PASS / WARN checks, `coverage_curve` |
| `engine/effect_video.py` | `cut_cells` (key a returned clip into cells), `resample` (Telegram's clock), `settle` (empty ends by construction), `finish_cell`, `encode_and_check` (shared with mode A) |
| `generation/effect_prompts.py` | template `effect_video` v2 (v1 retained for stored jobs): `lint_plan`, `video_prompt`, `key_colour_for`, `describe`; template `effect_pieces` v2 (the image-sprite sheet): `pieces_cells`, `pieces_prompt`, `describe_pieces` |
| `flow/effects.py` | the `E###` lifecycle; `pieces_base_plan` / `pieces_plan` / `request_pieces` / `link_pieces` (the drawn sheet); `for_sticker` / `counts_for_pack` (the gallery) |
| `console/effects.js`, `console/packs.js` | the effects screen (incl. the pieces panel `fxPiecesPanel`); the sticker view's Particles section (`ptHtml`, `ptCard`, `ptBadge`) and the pack grid counter |
| `vision/effect_plan.py` | `analyse(stickers, allowed=...)` (vision model or table, groups, moods -> presets, consent as for captions), `lexicon_plan` |
| `generation/jobs.py` | `request.t2v` (no start image), parallel jobs (`paid_parallel`) |
| tests | `test_effect_pieces` (14), `test_effect_gallery` (13), `tests/js/pack_particles.test.js`, `test_particles` (38), `test_effect_video`, `test_effect_plan`, `test_effect_prompts`, `test_live.FulfilTests` (t2v, parallel, cap in flight) |

## 7. The contract (built: `flow/effects.py`, `console/server.py` `_effects`, `docs/api.md`)

`E###` records under `out/effects/E###/effect.json` `{id, pack_id, pack_name, mode: sim|video, grid, note, status: NEW|READY|VIDEO_REQUESTED|RESULTS|DONE|ERROR, stickers[{sticker_id, name, emoji, file, src}],
groups[{id, subject, elements, style, key, stickers, moods, preset, by, sprites}], per_sticker, notes, analysed_by, video{group: {job, grid, key, status, cells, cost}}, results[{id, mode, group, cell | sticker_id,
file, bytes, status, checks, warnings, blocks, metrics, params, added_to}], history[]}`, `src/` (the source pictures), `results/R###.webm`, `previews/<digest>.webp`. Routes: `GET/POST /api/effects`,
`GET /api/effects/{id}`, `POST .../analyse | plan | estimate | video | preview | render | add`. The analysis runs in a background thread (consent: `allow_vlm`), the video needs `go: true`, a result that breaks a
Telegram limit is FAILED and cannot be added, everything else can. **Adding is the person's click** (history `APPROVE`); a video result goes to the stickers of its group cell by cell (round robin).

## 8. Screens and remaining acceptance

New entry points use the scoped editor (`console/particles.js`, common helpers in `effects.js`). The clicked sticker/batch establishes the target; a batch outside the library offers Approve as a pack and continues automatically. Image, animated and existing sources feed the same sprite selection and simulator. See [design.md](design.md) for compact copy and control placement.

The batch/sticker gallery combines owner sets with legacy created/saved results; the pack view displays its stickers' union. Kind, job and credits remain accessible. Adding a rendered burst affirms it. A set with no cells still counts as created; a detached set remains attachable. The explicit old `#/effects/E###` route is retained for one release.

Legacy cut results are sprites within a run. `particle_sets.for_sticker` adds `runs[]`, grouping `created[]` and effect-linked `saved[]` by E### and recording `imported_as[]` owned set IDs. The sticker-window gallery is being integrated to display set/run cards with sprite strips and **Open in simulator**, not one full particle-pack card per slice. Raw clip Add is secondary under collapsed compatibility details. Existing raw result arrays and legacy Add routes stay available for one release; browser acceptance includes the real lightbox loader target and grouped display.

The AI image-sheet path is an ordinary paid sheet job with outline 0 and exact equal-grid particle cutting. `pieces_estimate`/`pieces` retain their legacy quote/go contract; the job request identifies the effect/group. READY cells become tight sprites. Judgment warnings have Use it anyway; technical unreadability/Telegram limits get a reason and next action.

The old Kling working pipeline remains text-only `estimate → video → cut_cells → finish_cell`; its cell clips, timing, job and credits are retained on import. The restoration must demonstrate animation inside flying particles, not merely keep WebMs alongside static peak frames. The normal flow saves into its target set automatically and does not ask where a pack-owned set lives.

Acceptance uses already-created sheets/clips copied into scratch out: follow their stored job/effect/generation paths, diagnose blocked state, then exercise free recut/import/recovery, temporal simulation, Render and Add. Synthetic temporal fixtures supplement that proof. Do not make a new provider call merely for acceptance, and do not treat an injected finished Render panel as the complete pipeline.

Open work outside the current flow: real v2 prompt/sheet measurements (W2), examples/tile art, a 3×3-specific prompt, chat refinement of sprite choices, and the green-frame start/end experiment only if 2×2 fails. Per-emoji motion and separate Telegram effect/download delivery remain distinct choices; ordinary animated-sticker delivery is settled.

## Particles are particles, not stickers (2026-10-03, UI/UX spec P6)

A set built from a drawn sheet stores its cells as **tight sprites** (`engine/particles.trim_sprite`: the alpha bounding box plus 2 px of air, cropped out of the batch's keyed sheet at native resolution by `pipeline.particle_sprites`), never the 512 px sticker
that the still stage makes of the same cell (a sticker canvas is the deliverable of a sticker, with the sticker size checks). The slice file is the fallback only for a batch with no keyed sheet (`cells[].sprite: false`). The same holds for the cells *Generate more*
appends. A batch cut as particles cannot be added to a pack as stickers (409); it becomes a set (`POST /api/particles {from_generation}` or the scoped editor's automatic import). The cause of the original "Batman Lego pieces" trouble (separator lines drawn by the image model)
is recorded in `docs/engine-and-studio.md`: the cut is not weakened.
