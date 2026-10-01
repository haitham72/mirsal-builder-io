# Phase_01 — supporting material for `../phase_01.md` (hand-off) and `../README.md` (architecture)

Phase 1 is the sticker engine plus the Lifecycle Console. **Built**; the remaining steps and review gates live in `../phase_01.md` ("As built" section).

- **Inputs (Haitham):** one folder per variant: `Images_gen/img-NNN-<subject>/<sheet>` and `videos_gen/vid-NNN-<subject>/<3x3 video>`, paired by the same `NNN`. Pre-sliced transparent clips live in `vid-NNN/slices/{quicktime,webm}/<name> (n).<ext>` (n = grid cell 1-9; `.mov` preferred). The app reads everything in place; **these names are final and are never renamed** (by me or the app).
- **Naming rule for new subjects:** three-digit id + snake_case subject, identical on the image and video side. Outputs are named `<media>-<NNN>-<task_slug>-<key>` (README, "Naming convention").
- **Generation tracker:** `tracker/tracker.py` (`python tracker.py`, then http://127.0.0.1:8765) scans these folders live (filenames and sizes only) and stores status and chosen takes in `tracker/tracker.json`.
- **1F, 1G and 1H are built (2026-10-01) and wait on Haitham's real runs.** Run it with `python -m mirsal serve` from `mirsal/`: one page, no build step (the first React pass in `mirsal/web` is parked, not served). The flow (type -> stickers -> Animate -> Add), History with Remove, the verifier, the gates and Send to Telegram are described in `../README.md`.
- **Telegram (1H):** `telegram-plan.md` is Telegram's own documentation (Haitham's input, not edited). The plan built from it is `../phase_01.md` Part H. The real test needs Haitham's bot token and numeric user id (Settings -> Telegram).
- **Gate 1G (React gateway, added 2026-10-01):** Haitham's manual loop: reserve a task in the Inbox → generate in Higgsfield → name the files into the reserved folders → run → gates → video sheet → upload → final pack. Spec: `../phase_01.md` Part G. Load the `frontend-design` skill before building it, and verify every screen in Chrome.
- **Gate 1F (golden path, added 2026-10-01; the prerequisite for Phase 2):** Haitham runs a real teddy sheet through every review gate: approve/reject the stills, build the video sheet, make the video from it in his own tool, upload it, approve/reject the animations, get the final pack. Spec: `../phase_01.md`, "Golden path".
- **Gate:** Haitham reviews the 1A stills in the console (100% zoom, all four backgrounds) before 1B video is signed off. He runs the real-video pack himself while the VPS network block is open.
- **Never open image or video files** to judge them (builder rule). Use validators, printed metrics and `result.json`; Haitham judges the look.
- **Restricted network:** see `../README.md` "library policy". Run `python -m mirsal doctor` from `mirsal/` before anything else.

- **Desktop UI (Part D):** design reference is `../ref/mirsal_sticker_builder_architecture_design.md` and `../ref/Mirsal-Builder.jpg`, the only reference image the builder may view (Haitham renames the other ref image to "ref-only"). His sticker media is still never opened. The gate and next steps live in `../phase_01.md` (Part D).
