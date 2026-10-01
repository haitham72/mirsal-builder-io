# HANDOFF: Mirsal Builder (rewritten 2026-10-01, end of the "Studio, edits, phase order" session)

Read this first, then `CLAUDE.md` (rules), `Phase_01/README.md` (the architecture as built) and `Phase_01/CLAUDE.md` (the Phase 1 finish list). Owner: Haitham (they/them: do not guess pronouns). Repo: `G:\Haitham\VsCode\Mirsal-Builder`, GitHub `haitham72/mirsal-builder-io` (PRIVATE), Windows PC.

**Branch `merge/generate-advanced`** (off `main` @ `22d26cc`; Phase A of the merge is `bf85e47`). **Almost everything below is uncommitted**: check `git status` and commit in small pieces (docs, engine, console, tests). `main` is behind.

## 0. Do these first

1. **Restart the server after every code change.** Python reads code once at start; the page is read from disk on every load, so a server older than the files answers "not found" to new buttons and ignores fixes. The server now warns about this itself (a banner on the Studio). When it is started from a script it runs hidden: find it with `Get-NetTCPConnection -LocalPort 8770`, stop it by PID, then `python -m mirsal serve` from `mirsal/` with the project venv.
2. **Security.** Tokens pasted in chat must be revoked in @BotFather after testing; an older token is in the gitignored `Phase_01/telegram.md` and in git history (`349762b`): offer (do not do without asking) a history scrub with a force-push. Never write a token or key into a tracked file (`mirsal/.env` and `out/telegram.json` are gitignored). `opencode.json` holds an API key and is gitignored: never `git add -A` blind.
3. **Phase 3 (Postgres) is not started and waits for Haitham's explicit confirmation.** The next phase is **Phase 2, live generation through Higgsfield MCP: `phase_02.md`, written ready to go** (its "Ready to go" section has the build order S0-S7). The order of Phases 2 and 3 was swapped on 2026-10-01.

## 1. Run, test, layout

```
cd G:\Haitham\VsCode\Mirsal-Builder\mirsal
.venv\Scripts\python -m mirsal doctor                      # verifier, AI key, workers, TLS, Telegram
.venv\Scripts\python -m mirsal serve [--port N] [--workers N]   # http://127.0.0.1:8770
.venv\Scripts\python -m mirsal profile G068 --sweep 1,6,9  # where animation time goes
.venv\Scripts\python -m mirsal recheck [G001|all]          # border check for animations made before it existed
.venv\Scripts\python -m unittest discover -s tests -t .    # 142 tests, ~2 min, green
```

No JS tests: the page is verified in a browser (Playwright MCP works; save screenshots under the repo root and delete them). Stdlib first, minimal wheels (rule 8). `MIRSAL_ANIM_WORKERS=N` sets how many cells animate at once.

| Where | What |
|---|---|
| `README.md` (root) | the index only |
| `Phase_01/README.md`, `Phase_01/CLAUDE.md` | the Phase 1 architecture as built; the finish list, inputs and builder rules |
| `phase_02.md`, `Phase_02/` | live generation (ready to go), `prompt_samples.md` |
| `phase_03.md`, `Phase_03/` | Postgres, tracing, pool, photo / text / depth (waits) |
| `mirsal/mirsal/engine/` | the pure engine: `verify.py` (44 checks), `video.py` (`AnimCache`, `_Polite`), `render.py`, `ffmpeg.py`, `config.py` |
| `mirsal/mirsal/` | `pipeline.py` (lifecycle, `edit_still`, `studio_edit_*`, `recheck_bounds`), `gates.py`, `library.py`, `telegram.py`, `expander.py` + `llm.py` (AI expansion), `tasks.py`, `prompter.py` |
| `mirsal/mirsal/console/` | `server.py` and the sandbox UI: `generate.js` (the Studio), `prepare.js` (video editor, Studio and pack edit modes), `editor.js`, `packs.js`, `app.js`, `telegram.js` |
| `mirsal/out/` | gitignored: `G00N/` (`source/orig/` keeps originals), `library/`, `cache/anim/`, `tasks/`, `telegram.json` |

## 2. Done this session (142 tests green, browser-verified; committed in pieces on `merge/generate-advanced`, not pushed or merged)

- **Studio:** the page is the "Studio" (`#/studio`); five header views (Request, Prompt, Stickers, Animation, Pack wizard); the Animation view has the video-sheet panel and analysis; the sheet panel marks not-accepted stickers red (cell tint + chip).
- **Edit a created sticker (layered):** a sticker with an animation is edited as layers over its ORIGINAL animation; **Save to sticker** updates the animation AND the image together, closes the editor and refreshes the pack copies. From a pack: Edit in Studio / Open in Studio; pack stickers without a source edit in the video editor and replace in place. Details: `Phase_01/README.md`, "Editing a created sticker".
- **Library:** square markers + Explorer-style drag box (Shift adds, Ctrl un-selects), bulk delete; the WhatsApp export is removed.
- **Telegram:** one click (connect once; send; the app opens on the set; a small card), images and video proven live, the bot also messages the owner the link.
- **Animation:** parallel cells, result cache (0.3 s repeat), exact speedups, the border check (`inside_frame`: WARN, blocked for review) also applied retroactively (`recheck`), a polite batch (below-normal priority, 2 OpenCV threads, default workers = half the cores up to 6).
- **AI expansion (pulled forward from Phase 2 S5):** `expander.py` + `llm.py`: a subject becomes the full named set (key, tags, emoji per sticker), linted, one repair round, built-in sets as fallback; the saved template still builds every prompt. **Needs `ANTHROPIC_API_KEY` in `mirsal/.env`** to run live; covered by fake-model tests.
- **Issue colours (third part of the session):** orange out of bounds, purple bad green screen, yellow bad loop, pink look / motion, blue file limits, red dropped or blocked; on tiles, chips, as a hatch in place over the cells of the green-screen sheet and the video sheet, and in legends. Rejected (out-of-bounds) animations are off by default and the human can **Include anyway** (`gates.soft_block`). Header gate counts, the sticker detail (checks, path, measurements), the **Edge** dialog (outline + trim, `/appearance`), the Size slider (verified). Animation quality: bicubic upscale, finer crf ladder, `sharpness` check (44 checks, `VERIFY_VERSION = 2`, `CACHE_VERSION = 2`). Details: `Phase_01/README.md`.
- **Docs:** phases 2 and 3 swapped; `phase_01.md` removed (done); the Phase 1 README moved into `Phase_01/`; the root `README.md` is the index; the delivery rule (the product is an API / app, the UI is a sandbox) and the docs-in-every-major-step rule are `CLAUDE.md` rules 11 and 12.

## 3. Open (in order)

1. **Phase 1 is built; what is left of its finish list** (`Phase_01/CLAUDE.md`): Haitham's checks (the AI key in `mirsal/.env`, real stickers through the Studio edit, the colours on real batches), then the decision to merge `merge/generate-advanced` into `main`. An external review prompt is in `REVIEW_PROMPT.md` (the reviewer writes `report.md`).
2. **Phase 2** (`phase_02.md`): S0 discover the Higgsfield MCP in a session where it is authorised (in the build session it was listed as unauthorised, so its tools could not be read), then S1-S7.
3. Server-side job queue (today: 409 busy + the client waits quietly).
4. **Phase 3** only when Haitham confirms.

Animation-quality measurements (re-measure after changes; `Phase_01/README.md`, "Animation quality"): the black line is mostly in the source art (raw edge band -36 luma vs core, keying adds ~3), so Edge's trim is the fix; source cells are 320 px upscaled 1.28x (now bicubic: +6% edge detail), then VP9 at crf 34-46 on the finer ladder (budget use up to 255.6 of 256 KB); the encode keeps 1.00-1.03x of the edge detail, so the softness that remains comes from the source resolution.

## 4. Facts worth knowing

- Every "it still fails" report on Telegram, bulk delete and unflagged out-of-bounds was a **stale server process**; compare the process start time with the file times first.
- VP9 (`row-mt`) output is not byte-stable between runs; compare metrics and checks, not WebM hashes.
- The prepared Higgsfield samples in `Phase_01/Images_gen|videos_gen` are pre-rendered and not normalised (3 of 9 teddy and 8 of 9 emoji animations leave their cell); Phase 2 never sends a raw sheet to the video model, it sends the normalised video sheet.
- Never open or judge sticker media yourself; never write inside `Phase_01/Images_gen|videos_gen`.
- Tool quirks here: a Bash heredoc breaks on some quote mixes (write a patch script with the Write tool, run it); PowerShell has no `&&` and re-encodes non-ASCII when it rewrites files (use Python); the Write/Edit tools fail if the file changed since your last Read (copy from a scratch file instead); do not stop processes by a command-line pattern that also matches your own shell; a Playwright click on something that closes a dialog may report "no match" although it worked.

## 5. Prompt to give the next LLM

> Read `HANDOFF.md`, `CLAUDE.md`, `Phase_01/README.md` and `Phase_01/CLAUDE.md`. Review `git status`, run the 140 tests, and commit the working tree in pieces. Restart Haitham's server from `mirsal/.venv`. Then finish the Phase 1 finish list (B3-B5, animation quality) with Haitham or, when they say so, start `phase_02.md` at step S0 (discover the Higgsfield MCP tools). Phase 3 (Postgres) starts only on Haitham's confirmation. Update the docs in the same step as every major change (rule 12) and never commit a token or `opencode.json`.
