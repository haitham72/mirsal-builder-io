# HANDOFF: the save point

This file holds only what a session was in the middle of when it stopped (it got stuck, the context ran out, something went wrong). Nothing else lives here: the next steps are `plan.md`, what exists is in `README.md` and `docs/`, what is open is in `docs/backlog.md` and `docs/waiting-for-haitham.md`.

When a session stops mid-step, write: the step being worked on, the files touched, what is half-done, how to resume. The session that resumes deletes it.

## In progress

Session of 2026-10-08 (Muse Spark), all work committed and pushed through `c0a6d55`. Nothing half-written; everything below is built or planned-only.

**Just finished implementing (all on `main`, all pushed):**
- Export-as-ZIP follows the final filename contract + manifest v1 in both ZIPs (`2b2ebd4`: `generation/actions.py` 36-bank, `media/export_names.py` builder/parser, both `export_zip`s, `tests/test_export_names.py`).
- Snake_case slugs + clean fallback tags (`bc89279`): `-` separates identifiers, `_` joins inside; fallback strips subject words, collapses repeats, flags `unresolved`. Verified on real G112 (S7 now `grumpy_arms_crossed`).
- Face-only emoji prompts (`162c6e3`): template v4 files + `emotions.FACE_GROUPS` + `EMOJI_WORDS` auto-detect + limb-word guard test. v1–v3 byte-identical.
- Preset grids drive emoji sheets (`1349c7a`): `actions.PRESETS` + `FACE_SENTENCES`, `expand(..., preset=)`, faceless-emoji 3×3 defaults `core-v1`.
- Claim-ledger DB design (`c0a6d55`): `docs/export to team/mirsal-export-architecture.md` §10.7 — pack sessions, `C###` claims, regenerate lineage. Design only, zero code.

**Stuck / still open (not started or blocked):**
1. `tests.test_batches.RemoveRoutes` fails on a Windows file-lock in teardown — fails identically on the clean tree (verified via `git stash`), pre-existing environment flake, not from this work.
2. Exports still emit `G###` — the short-code allocator (§10.4) is designed, not built.
3. Claim ledger (§10.7), exporter bank picker UI, in-batch versions, preset claim queue: designed/planned in `plan.md`, not built. Needs Haitham's go + a W number.
4. Paid proof pending (needs Haitham's explicit yes, ~2 credits): one face-preset sheet to prove the model draws faces without limbs; one pack at the default gap if the sheet passes.
5. Particles ordering (Studio step 5 after Animation, section only when versions exist): investigated (`particles.js` `spSteps`/`spSecHtml`, tests in `tests/js/particles.test.js`), not implemented. Next bench item after the go-ahead in `plan.md`.
6. Still true from the previous session: Import-pack browser check never happened (restart `serve --lan` first — the open server predates that code); `batch_import_inputs.py` at repo root does not run (`pl.Config.default()` does not exist); Haitham's open questions (original-emojis mapping, copying sheets into `inputs/`) unanswered.

**Resume:** read this file, then `plan.md` (phases in build order), then `docs/export to team/mirsal-export-architecture.md` §9–§10.7. Windows checkout, venv `mirsal/.venv`, branch `main` (in sync with origin). Test budget (`docs/testing.md`): one narrowest run per change, never re-run green suites, slow tier + full discovery retired.
