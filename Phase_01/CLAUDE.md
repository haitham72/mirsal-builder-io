# Phase_01 — supporting material, status and finish list

Phase 1 is the sticker engine, the verifier, the golden path with its gates, the Studio (the desktop builder) and Send to Telegram. **It is built, tested (130+ tests) and in use. What is left is the finish list below.** The architecture is in **`README.md` in this folder**; there is no `phase_01.md` any more (removed 2026-10-01 at Haitham's request: Phase 1 is built, its plan items are recorded in the README, its history is in git).

## Finish list (Haitham, 2026-10-01: "perfect phase 01 first; every step adds 1-5% and it compounds")
Done when Haitham approves; then Phase 1 closes and this list is deleted.
1. ~~**Studio:** the main page is called **Studio**, and any created sticker can be sent back to it ("Open in Studio").~~ **Done 2026-10-01** (rail, heading, `#/studio`, Open in Studio from the pack and the lightbox).
2. ~~**Edit a created sticker** (add text, emoji, trim), in the Studio and from a pack; one edit updates the image and the animation; the edit lives as layers and is exported from the Studio; Save closes the editor.~~ **Done 2026-10-01** (README, "Editing a created sticker"). Haitham to try it on real stickers.
3. **AI expand + key names** (pulled forward from Phase 2 step S5): **built** (`expander.py`, `llm.py`, `POST /api/plan {ai}`, the Studio preview badge, the Settings card; the deterministic sets are the fallback and the tests use a fake model). **Needs from Haitham:** `OPENAI_API_KEY` in `mirsal/.env`, then one live look at the result. The expansion feeds the Phase 2 jobs; a prepared sheet keeps the names of its own prompts file.
4. ~~**Merge leftovers:** B3 gate counts and per-tile approve/reject, B4 sticker detail, B5 Edge (outline + trim) from the page, the Size slider.~~ **Done 2026-10-01** (README, "Issue colours, Include anyway, the gate counts, the sticker detail and Edge"). Also done there: one colour per kind of problem, hatching in place on both sheets, rejected animations off by default with *Include anyway*.
5. ~~**Animation quality (Phase C):** better upscale, a finer encode ladder, a sharpness metric.~~ **Done 2026-10-01** (README, "Animation quality": bicubic upscale +6% edge detail, ladder 34-46 instead of all 46, `sharpness` check). The black key line is in the source art and is removed by Edge's trim; the remaining softness is the 320 px source cells (Phase 2's normalised video sheet).
6. **Haitham's checks:** the two Telegram packs (images, video) show in their Telegram; one animated pack from a real run; the server restarted with the new code.
7. Commit in pieces; decide when `merge/generate-advanced` goes to `main`.

## Inputs and rules for this folder
- **Inputs (Haitham):** one folder per variant: `Images_gen/img-NNN-<subject>/<sheet>` and `videos_gen/vid-NNN-<subject>/<3x3 video>`, paired by the same `NNN`. Pre-sliced transparent clips live in `vid-NNN/slices/{quicktime,webm}/<name> (n).<ext>` (n = grid cell 1-9; `.mov` preferred). The app reads everything in place; **these names are final and are never renamed** (by me or the app). They are test samples, not the product's input: Phase 2 generates live.
- **Naming rule for new subjects:** three-digit id + snake_case subject, identical on the image and video side. Outputs are named `<media>-<NNN>-<task_slug>-<key>` (README, "Naming convention").
- **Generation tracker:** `tracker/tracker.py` (`python tracker.py`, then http://127.0.0.1:8765) scans these folders live (filenames and sizes only) and stores status and chosen takes in `tracker/tracker.json`.
- **Telegram:** `telegram-plan.md` is Telegram's own documentation (Haitham's input, not edited). `telegram.md` is a **gitignored** scratch file that may hold an old bot token: do not read it out, never commit it, and Haitham should revoke that token. The send is built and proven (images and video); enter the token and user id in Settings -> Telegram.
- **Desktop UI design reference:** `../ref/mirsal_sticker_builder_architecture_design.md` and `../ref/Mirsal-Builder.jpg`, the only reference image the builder may view (Haitham renames the other ref image to "ref-only"). The screens are a sandbox / proposal (root `CLAUDE.md` rule 11).

## Builder rules (carried over from the plan)
- Build only the phase you are given. If something belongs to a later phase, write it down; don't build it.
- **Never open image or video files to judge quality** (the builder never views media; tests use synthetic fixtures and printed metrics). Use validators, printed metrics and `result.json`; Haitham judges the look.
- Python >= 3.10 on Windows/macOS/Linux (`pathlib` only, no shell-specific commands). Version floors are in `mirsal/requirements.txt`; ffmpeg needs `libvpx-vp9`. Network is restricted: stdlib first, minimal wheels, `python -m mirsal doctor` first (README, "Restricted network / library policy").
- Docs are part of every major step (root `CLAUDE.md` rule 12).
