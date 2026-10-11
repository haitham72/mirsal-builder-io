# docs/redesign_plan.md — one clean app, with nothing lost (branch `edit-design`)

**Status: Haitham accepted every recommendation of §7 (2026-10-11); the outside review (§9) is still to come.** Built so far on this branch:
the safety net (§3) and phase 1 (§5). This file exists only while the redesign is open; each phase deletes its part once built, and the architecture moves into
`docs/design.md` / `docs/architecture.md`.

Haitham, 2026-10-10: the app grew in increments and is "a little bit chaotic, so many informations everywhere"; the Home page he designed is the
direction ("simpler and cleaner"); the logic of batches, sheets and videos is "highly confusing" (make more videos from a sheet, go back and edit
the prompt, move to the next batch, go back to batch 1 and branch again); and: **"I am super scared any logic would be lost."**

## 1. What does not change

- **The JSON API, byte for byte.** No route changes its answer. New routes are native FastAPI with pydantic (rule 11; §6 needs one).
- **The engine, the gates, the verifier.** This is a redesign of `mirsal/mirsal/console/` only (plus §6).
- **Rule 10 on every surface:** a rejected picture is visible, has one plain sentence why, and its override ("Use it anyway" / "Take it back")
  sits on that picture: the tile, the whole-sheet cell (image sheet and video sheet), the chat card; plus one bulk control per batch.
- **No dead stubs (rule 6), no CDN (rule 8), the one `ACT` object and the prefix rule** (`docs/architecture.md` §6), **role gates** (owner /
  admin / member see what they see today), **"Ask before spending"** and the price on every paid button.
- **The look:** Haitham's Home page (`web/mockups/home-library.html`, built as `home.js`): light, Mirsal blue for actions, Inter, the locked
  issue colours (orange out of bounds, purple green screen, yellow loop, pink look/motion, blue file limit, red blocked or dropped).
- **Who builds it:** one session at a time, Opus on medium effort (Haitham, 2026-10-10); one commit per phase; the test budget of
  `docs/testing.md` (one narrowest run per change).

## 2. The new structure

Mockups (static, real media, not wired): `mirsal/web/mockups/redesign/` — `studio.html` (the reference), `create-chat.html`, `pack.html`,
`settings.html`, `shell.css`; `index.html` there only links them.

- **The rail: four places** — **Home · Create · Library · Help**; the avatar at the bottom opens **Settings, Team (Users), Trash, Watch folders,
  System health** (owner/admin items only for them) and Sign out. Every old hash keeps working (`#/users`, `#/settings`, `#/chat`, `#/create`,
  `#/history`, `#/effects` …): routes are not removed, only the rail is shorter.
- **Create has two tabs: Chat | Studio** (today's AI and Studio). Create > "From a photo" (today's `#/create`) and "Particle effects"
  (`#/effects`) are entries in Create's "+ New" menu.
- **The journey bar** (both tabs). **In Chat it is built** (2026-10-11): the stage slider, Prompt · Stickers · Animation · Telegram · Export
  (`agent/stages.py` has five stages; `docs/design.md` "The stage slider"), with its details (the chat's models and options). Still to build: the
  Studio header's version, which shows where the selected sheet or video is on the same five stops.
- **The project map** (Studio, left column; replaces the Earlier-batches column, the variations strip and the Animation tab's video row):

  ```
  Project  = one idea (today: a "pack of batches", pipeline._packs: same request, same person, within 6 h, or a drag-and-drop link)
   └ Batch  = one set of stickers (Batch 1 Everyday moods, Batch 2 Reactions …; today: each family in the pack)
      └ Sheet = one try at that batch (first try, redo, prompt changed, joined; today: the family's variations, flow/groups.py)
         └ Video = one animation of that sheet (A1, A2 …; today: result.json video_sheets, pick_video / remove_video)
  ```
  Every node can branch where it stands, with the price on the button: **+ Another video of this sheet**, **+ Another sheet, same prompt**,
  **+ Change the prompt, then a new sheet**, **+ Next batch**, **Make a video** (a sheet with stills only). A breadcrumb (Project › Batch ›
  Sheet › Video) and the highlighted node always say where you are. Above the map, a project switcher lists every project (what Earlier batches
  lists today, one row per project).
- **The Studio's work area** (for the selected sheet or video): a toolbar (**Stickers | Whole sheet**, Edge, Background, ⋯, Size), the tiles,
  and a **bottom bar** with the counts, "Use all anyway (N)" and ONE main button for the state (Make the sheet → Animate / Make a video → Add N
  to a pack → Open pack).
- **The sticker panel** (right; replaces the sticker modal `gmodal`): animation and still, name and emoji, tabs **Checks · History ·
  Measurements**, and the sticker's actions.
- **The Idea step** (journey bar's first stop, and the map's "The idea and its prompts"): today's Request and Prompt tabs and the pre-batch
  prompt draft (`GD`), with the composer (prompt, references, style, loop, AI enhancer, particles, outline, models, price).

## 3. The safety net (built on this branch, first commit)

- `docs/architecture.md` — the whole app on one page: layers, data, the golden path, the HTTP server, how the sandbox is wired, every module.
- `docs/ui_inventory.md` — generated by `mirsal/mirsal/console/inventory.py`: all 429 actions, the scripts that draw each button, the server
  routes each one calls; the 16 screens; the 155 routes the page names.
- `mirsal/tests/data/ui_baseline.json` + `mirsal/tests/test_ui_inventory.py` — the three lists as they were. While the redesign runs, an action,
  screen or route may only leave the console with an entry under `renamed` (old -> new, the new one must exist) or `retired` (a reason, with
  Haitham's approval and the date). **The baseline is never regenerated during the redesign.** Run: `python -m unittest tests.test_ui_inventory`.
- The behaviour tests that pin today's Studio (`tests/test_js.py`, `tests/js/*.test.js`: cell_op, allow_tiles, anim_row, sheet_cells,
  sheet_fixed, sheet_recovery, prompt_tab, prompt_step, studio_menu, remove_batch, history_card, job_recovery, model_pick, sticker_id,
  enhancer_engine, ai_editor, anim_create): when markup moves, **the selector in the test changes, the behaviour it asserts does not**.
  Deleting an assertion needs the same approval as retiring an action.

## 4. Every Studio action and its new home

Homes: **MAP** (a node of the project map, or its menu), **PROJ** (the project switcher), **IDEA** (the Idea step), **COMP** (the composer, in
IDEA and on New project), **TOOL** (the toolbar or its ⋯ menu), **GRID** (a tile), **SHEET** (the Whole-sheet view), **PANEL** (the sticker
panel), **BAR** (the bottom bar), **JOUR** (the journey bar), **PILL** (the credits pill and its jobs list), **DLG** (its dialog, unchanged),
**AVATAR** (the avatar menu: Settings / Trash / Watch folders), **SAME** (stays where it is). The server route is the same in every row.

### `generate.js` (67)

| action | today | new home |
|---|---|---|
| `goutline` | outline px (old header) | TOOL Edge (with `cpstrokeset`) |
| `ggo` | Generate (replaced by composer.js's) | COMP Create |
| `gmore` | Create more: the next prepared sheet of the subject | MAP + Another sheet, same prompt (free when a prepared one exists) |
| `gnext` | Generate the next sheet as the next batch | MAP + Next batch |
| `gbdrop` | take a batch out of the browser session | MAP batch menu "Hide from this view" (decision D4) |
| `ginc` | include a batch in Animate / Add | MAP batch checkbox in "several batches" mode (decision D3) |
| `ganimslice` | animate one sticker again | PANEL Animate again |
| `greplace` / `grepundo` | replace a still with a file / take it back | PANEL Replace file / Take back |
| `ggen` | show another variation of the family | MAP click a sheet |
| `gmain` | make a variation the family's main | MAP sheet menu "Make this the main sheet" |
| `gdel` | delete a variation (to the trash) | MAP sheet menu "Remove" |
| `ganmo` | a motion suggestion into the video prompt | IDEA video prompt suggestions; also in "+ Another video" |
| `gcutany` | Cut it anyway (sheet-level problem) | MAP sheet status "Not cut" + SHEET banner button |
| `gretrysheet` | try a failed sheet again | MAP failed sheet "Try again" |
| `greqgo` | Request tab: send the edited request | IDEA "Make a new sheet from this request" |
| `gopenfolder` | open the batch folder (local) | TOOL ⋯ Open folder (staff, as today) |
| `pgresheet` | new sheet from an edited sheet prompt | IDEA + MAP "+ Change the prompt, then a new sheet" |
| `pgredo` | new video from an edited video prompt | MAP "+ Another video of this sheet" (prompt shown, editable) |
| `pgsheet` | sheet again, same prompt (live) | MAP "+ Another sheet, same prompt" |
| `pgvideo` | make the first video (live) | MAP sheet "Make a video" / BAR |
| `pgreset` | reset an edited prompt | IDEA Reset |
| `gdnb` | how many batches (pre-batch draft) | IDEA "How many batches" |
| `gdtab` | draft tab Request / Prompt | IDEA tabs |
| `gddiscard` | discard the draft | IDEA Discard |
| `gdpriceretry` | ask the price again | IDEA price line "Retry price" |
| `gprompt` / `gpromptfree` | Generate prompt (AI enhancer) / the built-in one | COMP Write the prompts / IDEA "Use the built-in prompt" |
| `gdsheet` | Generate sheet from the draft | IDEA main button "Make the sheet · N credits" |
| `ggroup` / `ggroupgo` | Add to group (join a family) | MAP sheet menu "Move to another batch…" + drag a sheet onto a batch |
| `grm` | Remove batch(es) | MAP batch menu "Remove batch" |
| `gtab` | the Request / Prompt / Stickers / Animation / Pack tabs | JOUR (Particles opens `spopen` as today) |
| `ganimate` | Animate (prepared video) | BAR main button |
| `gadd` / `pwgo` / `gopenpack` | the Add-to-pack wizard / go / open the pack | BAR "Add N to a pack" → DLG (3 steps unchanged) → BAR "Open pack" |
| `gvideo` / `gpickvideo` / `gsheetapprove` / `gvclose` / `gcopyprompt` | Make a video… (quick sheet, download, upload, copy prompt) | MAP sheet "Make a video" / BAR → DLG |
| `gapick` | use another video (A1/A2) | MAP video menu "Use this video" (the used one carries a mark) |
| `garm` | take a video out of the row | MAP video menu "Remove" |
| `gvsheet` / `gaclose` | the video-sheet dialog | SHEET (Video sheet) |
| `gptog` | open a cell's prompt | IDEA cell prompts |
| `gshk` | Raw / Keyed on a sheet panel | SHEET switch |
| `gsheet` / `gsview` / `gstog` / `gsclose` | Full analysis: view, cut lines, boxes | SHEET toggles (Raw / Keyed / Fixed, Lines, Boxes) |
| `ghiggs` / `hcopy` / `hgenop` / `hreserve` | the manual Higgsfield path | IDEA ⋯ "Manual Higgsfield path" (as gated today) |
| `gopen` / `gstep` / `gmall` / `gmclose` | sticker detail: open, next/prev, every check, close | GRID click → PANEL; PANEL arrows; "Show every check"; × |
| `gedit` | Edit (layers) | PANEL Edit → the editor (SAME) |
| `openstudio` / `lcstudioedit` / `lcopenstudio` | from a pack or the Library into the Studio | SAME: opens the map at that sheet with the sticker in PANEL |
| `gcell` | a tile's one control (drop, bring back, use anyway, take back) | GRID tile + SHEET cell + PANEL |
| `gallowall` | Use all anyway (N) / Take all back (N) | BAR |

### `live.js` (20)

| action | today | new home |
|---|---|---|
| `lusage` | Usage dialog | PILL "Usage" → DLG |
| `lstyle` / `lmodels` / `lmpick` / `lmdone` | style; the model dialog | COMP style; COMP models → DLG |
| `qtoggle` / `qcopy` / `qretry` / `ljdismiss` | the jobs queue: open, copy id, continue, dismiss | PILL jobs list; a job of the open project also shows on its MAP node ("Being made · about N min") |
| `egapply` / `egundo` | Edge: apply / undo | TOOL Edge popover |
| `vlmyes` | consent to AI vision | DLG (SAME) |
| `hopen` / `hopenpack` | open a batch / every batch of a pack | PROJ row / MAP |
| `hunpack` | take a batch out of its pack | MAP batch menu "Move to its own project" |
| `hleave` | a variation leaves its family | MAP sheet menu "Make it its own batch" |
| `gpurge` / `gpurgeall` / `gpurgeallgo` / `grestore` | Removed batches: purge, purge all, restore | AVATAR > Trash (with `trash.js`) |

### `composer.js` (12)

`cpmenu`, `cpadd`, `cprefx`, `cppart`, `cploop`, `cpai`, `cpstroke`, `cpstrokeset`, `cpstyles`, `cpstylepick`, `ggo` → **COMP** (same order,
same switches). `gnewlive` (a fresh paid sheet instead of the prepared one) → COMP and the MAP sheet of a prepared batch: "Make a new one".

### `imports.js` (9)

`impopen` → PROJ "+ New" › "Import a sheet or video"; `impackopen` → Library and Home (SAME); `impupload`, `impchoose`, `impnew`, `impretry`,
`imphistory`, `imphf` → DLG (SAME); `impbatch` (import into a batch: a picture is its next sheet, a video its next animation) → MAP batch
"+ … › Import a sheet" and sheet "+ … › Import a video".

### `history.js` (5), `sheet-recovery.js` (1), `job-recovery.js` (4)

`hsopen`, `hgen`, `hremove`, `hrestore`, `hpurge` (the watch folders) → AVATAR > Watch folders (owner; `#/history` SAME). `ssallow` (a rejected
video sheet: use it anyway) → SHEET (Video sheet) and the MAP video node. `jrrefresh`, `jrcheck`, `jrcontinue`, `jrretry` (a stuck or failed
job) → the MAP node of that job + PILL (Retry shows its price first, as today).

### Every other script (screen level)

| script (actions) | new home |
|---|---|
| `app.js` (21) | shell: rail of four + avatar menu; Library; dialogs and pickers SAME |
| `agent.js` (28) | Create > Chat, restyled; the stage slider is built (`ag-stage`'s route `settings.stage` unchanged, plus `settings.models`) |
| `packs.js` (35) | the pack screen (`pack.html`): header with Send to Telegram, tabs Stickers · Particles · History |
| `particles.js` (54), `effects.js` (29) | pack > Particles tab; PANEL Particles; Create "+ New" › Particle effects (`#/effects` SAME) |
| `editor.js` (27), `prepare.js` (24), `animate.js` (8) | full-screen tools SAME, opened from PANEL / Library |
| `chat.js` (9) | pack "Try it in a chat" (`#/chat` SAME) |
| `telegram.js` (5) | pack Send to Telegram; AVATAR > Settings > Telegram |
| `support.js` (26), `tickets.js` (8) | Help (rail) |
| `users.js` (3), `auth.js` (12) | AVATAR > Team; avatar menu (sign out, credits request) and the sign-in gate SAME |
| `trash.js` (5) | AVATAR > Trash |
| `trending.js` (8) | Library > Trending tab SAME |
| `welcome.js` (7), `home.js` (6) | Home SAME |

## 5. Phases (one commit each; after each: the inventory test, the tests its files map to, Haitham's look in the browser)

1. **Built 2026-10-11** (the rail of four, the avatar menu, Create's tabs: `docs/design.md` §4.2). `studio.css`'s `:root` already carried the
   mockup's palette; a mockup token (e.g. the issue colours) joins `:root` in the phase that first reads it, never unused (rule 6).
2. **The journey bar in the Studio header** (prefix `jb`): the same five stops as the chat's slider (built 2026-10-11), showing where the
   selected sheet or video is.
3. **The project map's data** (§6): `flow/projects.py` + one native route + OpenAPI + a test on fakes. No UI yet.
4. **Studio frame:** the map column (replacing Earlier batches), the project switcher, the breadcrumb, every MAP / PROJ action of §4 wired to
   its existing `ACT`.
5. **Studio work area:** the toolbar, Stickers | Whole sheet (merging `sheetPanel`, `videoPanel` and the Full-analysis dialog), the tiles.
6. **The sticker panel** (replacing `gmodal`).
7. **The bottom bar and the Idea step** (the Request and Prompt tabs, the pre-batch draft, the composer).
8. **Pack screen. 9. Settings and the avatar items. 10. Chat restyle. 11. Library, Help, Home polish.**

Each phase ends with `renamed` / `retired` filled for whatever left, `docs/ui_inventory.md` regenerated, the area doc updated (rule 12), and the
part of this file it built deleted.

## 6. The one new piece of backend: the project map

The browser must not stitch the tree from four calls (rule 11). `flow/projects.py` `project_map(out, gid, user)` reads what exists — the pack
of batches (`pipeline._packs`), each family (`flow/groups.py`), each batch's `video_sheets`, the jobs in flight (`generation/jobs.py`) — and
returns one JSON tree: `{project: {title, request}, batches: [{root, title, stickers, sheets: [{id, label, relation, prompt_changed, status,
thumb, counts, videos: [{id: "A1", status, used, counts, job}]}]}]}`. A native route `GET /api/generations/{id}/map` (pydantic model in
`app_models.py`, OpenAPI, `docs/api.md`). Pure reads: nothing migrates, nothing is written. Tested on a temp `out/` with fakes.

## 7. Decisions (Haitham accepted every recommendation below, 2026-10-11)

- **D1 — the words.** Project / Batch / Sheet / Video, or another set (e.g. Set / Try / Animation). Recommendation: as written.
- **D2 — Earlier batches.** The project switcher replaces the column entirely (one row per project). Recommendation: yes.
- **D3 — several batches at once** (`ginc`: today Animate and Add act on every included batch of the session). Keep a "several batches" mode
  in the map, or make Animate / Add act on the selected batch only, with "Animate every batch" in the project menu. Recommendation: the second.
- **D4 — "take out of this view"** (`gbdrop`, browser-only). With server-side projects it is mostly `hunpack`. Recommendation: retire it.
- **D5 — the rail of four** with Settings / Team / Trash / Watch folders under the avatar. Recommendation: yes.
- **D6 — the Chat preview** (`#/chat`) leaves the rail and lives on the pack ("Try it in a chat"). Recommendation: yes.
- **D7 — merge the AI chat and the Studio?** (Haitham, 2026-10-10.) Recommendation: **two interfaces, one workspace, one project.** Keep them
  separate as interfaces (`CLAUDE.md` "Structure": the chat is the LangGraph agent with memory, the Studio is explicit and deterministic, never
  collapsed into one prompt), but stop them being two apps: both are tabs of Create, both open the **same project map** (a chat's batches are
  already Studio batches: `agent/tools.py` works through the Studio's own engine), and the Studio gets an optional **"Ask Mirsal" side panel**
  bound to the selected node ("make number 3 laugh", "two more videos of this sheet"), which is the same agent and the same session, not a
  second chat. One chat history per project, reachable from both tabs. Built after phase 7, only if Haitham agrees; until then the tabs share the
  project map and the journey bar.

## 8. Risks

- **One global scope**: a new top-level name or `ACT.<name>` that collides kills a script or silently replaces an action. Prefix every name; the
  inventory test and `tests/test_js.py` catch clashes.
- **`generate.js` is 850 dense lines** redrawn by a timer (`tick`): no entrance animations on anything redrawn by polling
  (`docs/design.md` 3.2); keep `glast` / `tick(true)` semantics.
- **Roles**: owner-only and staff-only controls (`gopenfolder`, the prepared chip, Import pack, watch folders, health) keep their gates.
- **Pre-existing failures** (`plan.md` Step 3: `tests.test_js` StudioActionTests ×3 + 1 error) are noted, not chased, unless a phase touches them.

## 9. For the outside reviewer

Check, against the code on this branch: (1) is any action, screen or route in `docs/ui_inventory.md` missing from §4 or given a home that cannot
do what it does today; (2) does §2's tree match the data (`pipeline._packs`, `flow/groups.py`, `result.json` `video_sheets`); (3) does any phase
break rule 10's override on a surface; (4) is §6 the smallest backend that avoids logic in the browser; (5) is the phase order safe (each phase
leaves a working app); (6) anything in `docs/architecture.md` that is wrong.
