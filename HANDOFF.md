# HANDOFF: Mirsal Builder (written 2026-10-01 at the end of a long session)

Read this first, then `CLAUDE.md` (project rules), `README.md` (architecture of what is built) and `phase_01.md` ("Session hand-off" at the top of "Next steps"). Owner: Haitham (they/them: do not guess pronouns). Repo: `G:\Haitham\VsCode\Mirsal-Builder`, GitHub `haitham72/mirsal-builder-io` (PRIVATE), branch `main`. Windows PC.

## 0. Do these first (in order)

1. **Security.** A Telegram bot token (bot `@Mirsal_builder_bot`, owner user id `1560629909`) was pasted in chat and ended up in `Phase_01/telegram.md`, which was committed and pushed in `349762b`. The file is now untracked and ignored (`8512a41`) but **the token is still in git history**. Haitham must `/revoke` it in @BotFather. Offer (do not do without asking) a history scrub with a force-push. Never write a token into any tracked file.
2. **Ask Haitham which UI is canonical** (section 2). Their feelings changed several times; do not rebuild anything before they answer.
3. **Fix the two things they just reported** (section 3), whichever UI wins.

## 1. Run, test, layout

```
cd G:\Haitham\VsCode\Mirsal-Builder\mirsal
.venv\Scripts\python -m mirsal doctor
.venv\Scripts\python -m mirsal serve              # http://127.0.0.1:8770 (the desktop builder: one page, no build step)
.venv\Scripts\python -m unittest discover -s tests -t .      # 113 tests, ~2.5 min, last full run green (before the Generate session rewrite)
```
Always use `mirsal/.venv` (the Anaconda base env has a broken numpy). Stdlib-first, minimal wheels (CLAUDE.md rule 8).

| Where | What |
|---|---|
| `mirsal/mirsal/engine/` | pure engine: `verify.py` (41 checks, 9 stages, the verifier), `sheet.py`, `video.py`, `video_sheet.py`, `grid.py`, `chroma.py`, `render.py`, `ffmpeg.py`, `config.py` (all thresholds) |
| `mirsal/mirsal/pipeline.py`, `gates.py` | lifecycle + the golden path gates G1-G5 (409 on illegal order; Python's BLOCK is final), `quick_sheet` / `quick_add` / `drop` (the one-click wrappers), `regen`, `search` |
| `mirsal/mirsal/prompter.py` + `prompts/templates/*.txt` | slot JSON -> prompts (tags 1-5, margin clause) |
| `mirsal/mirsal/tasks.py` | Higgsfield manual loop backend: plan preview, reserve folder names, inbox states |
| `mirsal/mirsal/watch.py` | History: the watch folders, Remove -> `out/trash/` -> Restore / Delete for good |
| `mirsal/mirsal/telegram.py` | Send to Telegram (Bot API, stdlib), plan, send, resend, zip fallback |
| `mirsal/mirsal/console/` | `server.py` (stdlib HTTP), the desktop builder UI: `index.html`, `studio.css`, `app.js` (shell, Library, Settings), `generate.js`, `history.js`, `telegram.js`, `packs.js`, `editor.js`, `chat.js`, `prepare.js`, `animate.js` |
| `mirsal/web/` | **parked React app** (Vite + React + TS + Tailwind v4 + shadcn-style + TanStack Query + Zustand + Playwright e2e) |
| `mirsal/tests/` | `unittest`; `synth.py` fixtures; `fake_telegram.py` (fake Bot API); `test_golden.py` (end-to-end scenario) |
| `Phase_01/Images_gen`, `videos_gen` | Haitham's mock sample sheets/videos (not in git, 478 MB). Names are final. The app reads them; only History -> Remove moves a folder pair (to the trash, restorable) |
| `mirsal/out/` | generated results (gitignored): `G00N/`, `library/`, `tasks/`, `trash/`, `telegram.json` (token, gitignored) |

## 2. The UI question (the main open issue)

There are three UIs and Haitham has praised and hated each at different moments:

- **Desktop builder, original ("legacy")**: rail + list column + panels, matches `ref/Mirsal-Builder.jpg`; has Library, Chat echo with likes, Create, Editor, Pack manager. Haitham: "extremely appealing and easy".
- **React gateway** (`mirsal/web`, commits `92a2be6` + restyle `5e007b8`): Inbox / Generate+gates / Video sheet / History screens, gate track G1-G5, **inline raw sheet with measured cut lines and a keyed toggle ("green screen with the borders")**, tiles on four backdrops. Haitham: "more professional", "loved the green screen and boundary viewer", **"I am starting to like your http://127.0.0.1:8771 version, sadly you completely wiped it out"**. But earlier: "so many routes between menus, so many clicks, I hate it". **A demo server of this React build is STILL RUNNING on http://127.0.0.1:8771** (an old process: stop it with `Get-NetTCPConnection -LocalPort 8771`, never by process name). Its built files still exist on disk in `mirsal/mirsal/console/dist/` (gitignored). The Python server no longer serves them: the dist routes were removed in `adad63d` (see `git show 5e007b8:mirsal/mirsal/console/server.py` for the code, and `web/` for the source: `cd mirsal/web && npm ci && npm run build`).
- **New simple flow** inside the legacy shell (`generate.js`, `history.js`, current default on 8770): type a request -> Batch 1 -> Create more -> Animate -> Add (asks the pack name). Written last, **never browser-verified**.

Haitham's stable requirements across all of this: (1) very few clicks: **type a request -> stickers -> animate -> add to pack**; (2) History = the real `Images_gen` / `videos_gen` folders with Remove; (3) the white outline is a choice, never forced; (4) one press = one folder, never auto-cycle to the next; (5) the look follows the ref images (`ref/Mirsal-Builder-upscaled.jpg`, `ref/ref-only.jpg`): Mirsal blue `#3B82F6`, Inter, icon rail + list column + white rounded panels, pill tabs; (6) **show the raw sheet as a green screen with the cut lines / boundaries on the page, not hidden**.

**Recommended next move:** keep the simple flow's behaviour (sessions, Add asks name, outline choice, drop x, no gate screens) but put it in the look Haitham says is more professional and show the sheet panel inline as React did (`mirsal/web/src/screens/Generate.tsx` `SheetView`: raw/keyed toggle + dashed cut lines + numbered cells, left column 300 px). Either (a) make the legacy page show that panel inline (cheap, no second stack), or (b) restore React as `/` and port the simple flow into it (Library/Chat/Create/Editor would then be unreachable until ported). **Ask Haitham which; do not guess.** Haitham said they are not in favour of any stack.

## 3. The two newest reports (not fixed)

- **"Scaling doesn't work"**: the Size slider in `generate.js` sets CSS var `--tile` on `<html>`; the grid rule is at the end of `studio.css` (`.gtiles{grid-template-columns:repeat(auto-fill,minmax(var(--tile,220px),1fr))!important}`). Debug in a browser (specificity, `.tiles`/`.gtiles` duplicates, the var not applying, or Haitham meant a whole-UI zoom, e.g. `document.documentElement.style.zoom` or font-size scale). Unverified guess; reproduce first.
- **"Bring back the images as green screen with the borders"**: see section 2 point 6. Currently only a button `Green screen & cuts` per batch opens a dialog (`sheetDlg` in `generate.js`); Haitham wants it visible like the React left panel. The data is in each generation's state: `source.sheet_copy`, `source.keyed`, `source.grid {rects, xs, ys, method}`, `source.sheet_size`, per sticker `metrics.cell` / `metrics.bbox`, `verify.sheet[]`.

## 4. Status of every piece

- **Done and tested (113 tests):** verifier (every check has pass + fail fixtures), gates + video sheet + returned-video slicing + 1x1 regen + search, prompter templates/tags, tasks/Inbox backend, simple-flow endpoints (`/api/generations/<id>/add`, `/drop`, `/quick_sheet`; `outline` per generation), History/trash backend + tests, Telegram client + verifier stages + zip + fake server tests (19).
- **Done but not verified in a browser:** `generate.js` session rewrite (Create more, batches, include checkboxes, Add dialog with pack name, background `<select>`, Size slider, `postWait` quiet retry, Green screen & cuts dialog, optimistic Animate), `history.js` (was walked once before the rewrite), `telegram.js` (walked once against the fake: connect, plan, create two sets, links). `history.js` now calls `openGen()` from `generate.js`.
- **Telegram live test: NOT proven.** `getMe` works (curl and once from Python). Fixed during the live attempt: Python's TLS context crashed on a malformed Windows certificate (`telegram._ssl_context()` skips bad certs), empty multipart bodies got HTTP 400 (calls without files now go as JSON). **Open:** later Python POSTs timed out with `WinError 10060` while curl worked: check OS proxy / IPv6 / IPv4-first / retry. Then one live round trip with a throwaway pack of synthetic stickers (`png()` and `webm()` in `tests/test_telegram.py`), resend adds 0, add one sticker adds 1, finally `deleteStickerSet` to clean up. A user-side network quirk also exists: Haitham says `127.0.0.1` does not work on their WiFi but works on LAN; a server that was simply not running was the likely cause once.
- **Not built:** a server-side job queue (the server runs one background job at a time and answers 409 busy; `postWait` retries client-side as a workaround); Phase 2 (Postgres), Phase 3+ (not started; plans updated with the exact shapes to import: `phase_02.md` "Notes from building 1F + 1G"); Telegram deletion sync, TGS/Lottie, set thumbnails; mobile.
- **Haitham's own gates (unticked in `phase_01.md`):** one real teddy sheet through every gate; one real Higgsfield loop; one real Telegram send.

## 5. Facts worth knowing

- 10 real sheets: 90/90 READY; thresholds measured on them (README "The verifier"). `holes` is measured on the finished sticker; with the outline off a thin ring with a wide gap is a real hole and BLOCKs (a test fixture hugs its ring for this reason).
- Animation encode is ~5 s per sticker (VP9 + alpha CRF ladder to <= 256 KB): ~45-50 s per 9-sticker pack; the verifier is under 1% of that. Levers if needed: process pool, start the CRF ladder near the estimate.
- Gates are still recorded behind the one-click flow (`history[]` per sticker, `reviews`), notes like "approved by pressing Generate" / "approved by Add" / "dropped from the set".
- A rule from the original task: never open or judge sticker media yourself (use metrics); never write inside `Phase_01/Images_gen|videos_gen` yourself. Haitham later asked for the Remove feature, which moves folder pairs to `out/trash` on their click only.
- Tool quirks in this environment: bash heredocs containing apostrophes break (write a file with the Write tool and run it); `Write` fails if the file changed since the last Read (re-read first); PowerShell `Get-NetTCPConnection -LocalPort N` is the safe way to stop only one server; `git add -A` will commit anything untracked, **check `git status` for secrets first**; Playwright MCP can only save screenshots/uploads under the repo root (use `.playwright-mcp/`, gitignored).
- Docs hygiene: plans are hand-off, README is architecture (CLAUDE.md rule 7); update both when something is built; never shrink a plan.

## 6. Prompt to give the next LLM

> Read `HANDOFF.md`, then `CLAUDE.md`, `README.md` and the top of `phase_01.md`. Do not build anything yet. First ask Haitham which UI should be canonical (the legacy-shell simple flow on :8770 or the parked React app they liked on :8771), remind them to revoke the Telegram token, then fix the two reported issues (Size slider scaling; the raw sheet as a green screen with cut lines and boundaries visible on the page), browser-verify the whole Generate flow end to end, and finally finish the live Telegram test.
