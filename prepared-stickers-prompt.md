# Prompt: serve the prepared Phase_01 stickers to a request, exactly like a Higgsfield batch (paste into a model that can edit this repository)

You are working in **Mirsal Builder** (`G:\Haitham\VsCode\Mirsal-Builder`, branch `review-gaps`), an app that makes animated Telegram stickers. Read `CLAUDE.md` first: its rules override everything below. Then read `docs/dev-notes.md`, `docs/testing.md`, and the parts of `docs/engine-and-studio.md` and `docs/generation.md` that you change.

## The goal
`Phase_01/` holds sticker sets Haitham already generated, laid out as the app's watch folder:

```
Phase_01/Images_gen/img-NNN-<subject>/<sheet>.jpg|png        the 3x3 sheet of variant NNN
Phase_01/videos_gen/vid-NNN-<subject>/<video>.mp4             the 3x3 video of the same NNN
Phase_01/videos_gen/vid-NNN-<subject>/slices/{webm,quicktime}/<name> (n).<ext>   optional pre-cut clips, n = cell 1..9
```

Today it holds `teddy_bear` (001-004) and `generic_emojis` (005-010). When a person asks for one of these subjects, in the Studio or the AI chat, the app must give them that prepared set as a normal batch:
- the same golden path and the same five gates (plan, sheet → stills G2 → video sheet G3 → animations G4 → pack G5);
- the same screens: Earlier batches, the Studio, the Library, Add to pack, Send to Telegram;
- no visible difference from a batch Higgsfield just drew.

**Seamless means the person's experience, not fake records.** Never invent a Higgsfield job, external task id, credit charge, `model_calls.jsonl` line or provider name for these batches. CLAUDE.md rule 10 says every request is traceable to its real source. A prepared batch records its real source: the watch folder, the folder number and the file names. That source is shown only where staff look (batch details, History), never as a warning to the person. Its price is 0 credits, and nothing is spent (rule 13).

## What already exists (verify it, do not rebuild it)
- `mirsal/mirsal/flow/sources.py` scans the watch folder by name only, never opening media. `find(root, prompt)` matches a request's words to a subject; `scan()` pairs each sheet with its video and pre-cut clips.
- `mirsal/mirsal/runtime/paths.py` `input_root()`: the watch folder is `inputs/` and falls back to `Phase_01/` while `inputs/Images_gen` does not exist. That is the case today, so `Phase_01` is the live watch folder.
- `mirsal/mirsal/flow/pipeline.py` `start(prompt, ..., pick=...)` builds a batch from a `Pick`. The prepared path already runs the whole golden path from a sheet, a video and pre-cut clips. "One press is one folder": the first variant, never advancing by itself; Create more moves to the next.
- `mirsal/mirsal/console/server.py`: the create route decides between a live Higgsfield call (`c.live("sheet", ...)`) and the prepared path. Find exactly where, and in which cases (live connected or not, the person's settings).
- What the scanner reports today: all 10 pairs are found. The pre-cut clips of `teddy_bear` 002, 003 and 004 are byte-identical copies of 001's, so the scanner drops them (`clips_dup_of: 001`), and those variants animate from their own mp4. Keep that rule.

## What to build
1. **Prefer the prepared set for a matching request.** When Higgsfield is connected, a request whose subject matches a prepared subject is served from the watch folder instead of a paid call.
   - Make this a setting with a default of on: `MIRSAL_PREFER_PREPARED` in `mirsal/.env`, plus a Settings switch for the owner. Rule 6: the switch must be read.
   - A request that does not match still goes to Higgsfield exactly as today.
   - Match on whole subject words (`teddy bear`, `teddy`, `emoji`/`emojis`), not on any shared word. Write tests for near-misses such as "bear in a teddy costume" or "emoji keyboard". Decide with Haitham whether those should match (see the questions below).
2. **The same experience.**
   - The plan step, the progress the person sees, the stills arriving, the gates, the animation, the history lines and the result all look like a live batch.
   - Where a live batch shows a price, a prepared one shows 0 credits, with no special banner.
   - The AI chat's plan card and creator run use the same path (`mirsal/mirsal/agent/`): the chat says it is making the batch, not that it found a file.
   - Keep the waits short. Do not add fake delays to imitate rendering. If Haitham wants a pacing delay for demos, it is an explicit setting that defaults to off, and you ask him first.
3. **Names and labels.**
   - The new batch folder follows rule 9 (`out/G###-<task_slug>-<UTC time>/`, built only through `pipeline.gen_dir`). Its stickers get proper keys, tags and emoji from the plan; generic emojis need a sensible name per cell.
   - If a prepared folder has a hand-written prompts file beside the sheet, use it. If not, the planner names the cells the way it does for a live sheet; check the cells are named from the sheet's subject, not from the file names.
   - Never rename, move or delete anything in `Phase_01/` (rule 9: the watch-folder names are final).
4. **Repeat requests.** The first request for a subject takes variant 1. "Create more" takes the next folder. A second, separate request for the same subject takes variant 1 again, as today. Ask Haitham whether it should take the next unused variant instead.
5. **Docs and trackers (rule 12):** `docs/engine-and-studio.md` (Console API, the prepared path), `docs/generation.md` (when a request is not sent to Higgsfield), `docs/api.md` if a field changes, `README.md` when the index changes, and `docs/backlog.md` / `docs/waiting-for-haitham.md` for anything left open or a question for Haitham.

## Part 2: recheck and finish the manual paths (the same files, the other way in)
The `Phase_01` files are real Higgsfield outputs, so they are also the right test material for the three ways a person brings a picture in by hand. For each path, check what exists against the code and docs, try it on a scratch server, then build what is missing.

**A. Manual import: "Use my own sheet", "Import from Higgsfield"** (`mirsal/mirsal/flow/imports.py`, `console/imports.js`, `docs/api.md` "Import an existing sheet or video"). Verify end to end on the scratch server:
- a `Phase_01` sheet imported becomes a batch with the normal gates;
- its video imported onto the approved G3 sheet animates;
- the same bytes imported twice open the existing batch instead of creating a second;
- a Retry after an interrupted import reuses its batch.

Fix what does not hold. Add tests only where a case is not covered (`tests/test_imports.py`).

**B. A connection failure, then a manual download from Higgsfield, linked back to its task.** This happened for real: jobs J022-J025 are `FAILED` with their Higgsfield task ids, because the download hit a certificate error (`docs/waiting-for-haitham.md` item 5).
- *Today:* `imports.known()` lets such a file be imported, but the import is **not linked**. The job stays `FAILED`; the new batch does not take the job's plan (the cells, tags and emoji the person approved); the task id lives only in the import ledger.
- *Build:* when an imported file matches a job that holds its task id (`FAILED`, or `TIMEOUT` with an id), the import **completes that job** instead of starting an unrelated batch. The match comes from:
  - the uuid in a Higgsfield download name, `hf_<date>_<time>_<uuid>.<ext>` (`imports.job_id_of`);
  - the job picked in "Import from Higgsfield";
  - or, for a file without one, a choice in the import dialog: "Is this the result of …?", listing the person's own failed jobs that hold a task id.
- *What completing it does:*
  - The job becomes `DONE` with `recovered_by: "manual import"`, the generation set and **no second charge**.
  - A sheet job's batch is built from the job's own saved plan and carries its external task id.
  - A video job attaches to the job's own destination batch and sheet, without asking for them.
  - The batch's history gets one line, actor human: "recovered from a manual download of task <uuid>".
- The existing recovery actions (`mirsal/mirsal/generation/recovery.py`, *Check · free* / *Continue · same ticket*) stay; this is the path for when they cannot download either.
- Test with fake job records shaped like J022-J025; never call Higgsfield.

**C. Edited outside the app (Photoshop), back into the same place.**
- *Today:* the Studio's editor saves a canvas as a NEW pack sticker (`POST /api/packs/{id}/render`). `Library.replace_file` exists but only the reloop refresh calls it. A person cannot replace a still or a pack sticker with a file they edited.
- *Build:* "Replace with an edited file" on a sticker:
  - **in the Studio** (a batch's still `S#`): the new picture goes through the stills verifier and keeps its `S#`; that sticker returns to waiting for approval; an override stays possible (rule 10);
  - **in the Library** (a pack sticker): it keeps its id, name, emoji and particle links, and a static or animated type follows the file; the Telegram limits are checked (512 px, 256 KB video / 512 KB static).
- Rejection never deletes, so the replaced file is kept as the sticker's previous version, with a history line and an undo.
- An engine/flow function and a stable JSON route come first, then the button (rule 11). Update `docs/api.md`, `docs/engine-and-studio.md` and `docs/design.md`.

## Rules (follow every one)
- **Never open `Phase_01/telegram.md`**, and never print, copy or commit its contents. It holds a Telegram token. Never commit `.env`, `opencode.json` or `mirsal/telegram-id.md`, and never `git add -A`.
- **No paid calls.** Tests never reach a real provider (`MIRSAL_NO_REAL_CLI=1`, fakes). Never call Higgsfield to compare.
- **Never open media files to judge them.** Use the validators and metrics (rule 9).
- **Tests:** follow the test budget in `docs/testing.md`: the narrowest tier for the files you change, run once (`mirsal test focused`, or a single module). The slow tier and full discovery are retired: never run them. Use an isolated `out/` (a temp folder) and set `MIRSAL_DB_WRITE=0`, because `mirsal/.env` forces Postgres writes even for temp folders.
- **Do not touch the running server's `out/`.** To try it end to end, start a scratch server: `MIRSAL_OUT=<temp> MIRSAL_DB_WRITE=0 python -m mirsal serve --port 8791` from `mirsal/`, with `mirsal/.venv` on Windows.
- Leave these alone: `faq/**`, `mirsal/local_eval/**` (another model owns them), and Help & Support (`mirsal/mirsal/flow/support*.py`, `faq.py`, `notifications.py`, `console/support.js`).
- One commit per phase with explicit paths and the repository's commit style. Push `review-gaps` when a phase is done (Haitham authorized commit and push).

## Questions to put to Haitham before you build the matching (do not guess)
1. Should "bear in a teddy costume" or "emoji keyboard" match a prepared set, or only requests that name the subject?
2. Should a second, separate request for the same subject get the same variant 1, or the next unused one?
3. Should staff see a small "prepared" mark on the batch (like the particles mark), or only in History and the batch details?
4. (Part 2 C) When a still is replaced with an edited file, should its existing animation be marked stale and made again, or kept until the person animates it again?
5. (Part 2 C) When a pack sticker is replaced, should the batch it came from get the edited picture too, or only the pack?
6. (Part 2 B) When an imported file could match two failed jobs, the person chooses; is that right, or should the newest job always win?

## When you finish
Do Part 1 and Part 2 as separate phases, each with its own commit. Report the files changed per phase, the tests run with their real output, how a request for "teddy bear" and one for "generic emojis" behaved on the scratch server (batch id, gates reached, credits shown, source recorded), each manual path's result (A, B and C), and what is still open.
