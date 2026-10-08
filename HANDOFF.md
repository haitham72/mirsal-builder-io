# HANDOFF: the save point

This file holds only what a session was in the middle of when it stopped (it got stuck, the context ran out, something went wrong). Nothing else lives here: the next steps are `plan.md` when there is one (none after v1.0), what exists is in `README.md` and `docs/`, what is open is in `docs/backlog.md` and `docs/waiting-for-haitham.md`.

When a session stops mid-step, write: the step being worked on, the files touched, what is half-done, how to resume. The session that resumes deletes it.

## In progress


Session of 2026-10-08 (Claude Opus 5.5), stopped to switch LLM. Code is committed and pushed (`88e99ae`); what is left is checking and two answers from Haitham.

1. **Built, not yet seen in a browser:** Library > Packs > **+** asks *New pack* / *Import pack* (`console/app.js` `ACT.newpack`, `console/imports.js` `ACT.impackopen`); a video imported with no destination is its own batch (`flow/imports.py` `first_frame`: frame 0 is the sheet, then `run_stills` + `run_animate`). Docs updated (api.md, design.md, engine-and-studio.md, W1(e)). Tests: `mirsal test area flow/imports` PASS (20), `node --test tests/js/imports_trending.test.js` PASS. **Resume:** restart `serve --lan` (the running server, started before this change, still has the old import code), then try + > Import pack with one PNG sheet and one MP4 sheet in the browser.
2. **Generic emoji packs made from the watch folders** (free, prepared): img-005..010 -> G112..G117, animated; *Add* put only the clean animations into packs *Generic Emojis 005..009* (1/2/7/6/3 stickers). The rest are soft-blocked (`inside_frame` WARN: the character leaves its cell; `gates.soft_block`), so including them is Haitham's click (Approve on the animation, then Add). G117 (img-010) has no pack yet: all 9 are soft-blocked. Do not approve them for him.
3. **Open questions to Haitham** (asked in chat, not answered): should a request saying "original emojis" map to the `generic_emojis` subject (it became its own subject `original_emojis`, paid sheet G111 / J058 / task 042)? Should a generated sheet ever be copied into `inputs/Images_gen` (that would change rule 9's "the app never writes in the watch folders"; recommendation: no)?
4. **Untracked/runtime, left as is:** `mirsal/out/` changes (G111-G117, J058, task 042, library.json, 48 particle files moved to `out/trash/particles/` by the app) are runtime artifacts, never committed. `batch_import_inputs.py` at the repo root (commit 8c9c2b4) calls `pl.Config.default()` / `pl.Pace.default()`, which do not exist, so it does not run; the Studio (type "generic emojis", Create more) or `POST /api/generations {prompt, variant}` does the same job. Delete or fix it on Haitham's word.
5. `plan.md` (extra local-vLLM judge tests) is untouched by this session and still the next planned work.
