# HANDOFF: the save point

This file holds only what a session was in the middle of when it stopped (it got stuck, the context ran out, something went wrong). Nothing else lives here: the next steps are `plan.md` when there is one (none after v1.0), what exists is in `README.md` and `docs/`, what is open is in `docs/backlog.md` and `docs/waiting-for-haitham.md`.

When a session stops mid-step, write: the step being worked on, the files touched, what is half-done, how to resume. The session that resumes deletes it.

## In progress

**The Mirsal Creator film (`Motion Graphics/`, 2026-10-04): the rough cut plays; waiting on the voiceover.** `Motion Graphics/README.md` "Where it stands" says what is built.

- **Blocked on Haitham:** the voice `wxweiHvoC2r2jFM7mS8b` (Haytham – Dramatic and Narrative) is added to the ElevenLabs account, but text-to-speech returns 402: "Free users cannot use library voices via the API". It needs either the Starter plan, or the read made in the ElevenLabs web app and saved as `Motion Graphics/audio/voiceover.mp3`. The text is the `SCRIPT` in `analysis/align_vo.py`, one paragraph per plate. The free tier also refuses `mp3_44100_192`, so use `mp3_44100_128`.
- **Then:** `uv run --no-project --with onnxruntime --with numpy python analysis/align_vo.py` and `uv run --no-project --with numpy python analysis/audio_vo.py` (these replace the provisional `data/lyrics.json` and `data/audio.json`). After that, write the plates P1 to P8 (README §5), each replacing its `card(...)` entry in `app/src/timeline.ts`. Then sound (§7) and render (§8).
