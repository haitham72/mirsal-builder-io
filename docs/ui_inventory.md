# docs/ui_inventory.md — everything the browser sandbox can do (generated)

**Generated** by `python -m mirsal.console.inventory` from `mirsal/mirsal/console/*.js` on 2026-10-11 (branch `edit-design`), after redesign phase 9 (Settings).
Do not edit by hand: regenerate it when the console changes. How the sandbox is wired: `docs/architecture.md` §6. What the redesign does with each
Studio action: `docs/redesign_plan.md` §4.

**438 actions** (439 definitions: `ggo` is defined in generate.js and replaced by composer.js) in 26 scripts, **16 screens** (21 `RENDER` lines: some scripts wrap another's screen), **155 server routes** named by the page.
The baseline of the three lists is `mirsal/tests/data/ui_baseline.json`; `tests/test_ui_inventory.py` fails when one of them disappears without a
`renamed` (old -> new) or `retired` (with Haitham's approval) entry there.

How to read a row: **action** is `ACT.<name>`; **button drawn in** is every script whose markup carries `data-act=<name>` (none: the action is
called from code, a key, a form, or an `onchange`); **server routes** are the `/api/...` paths in the action's own code and in the helpers it
calls (two calls deep, not into the helpers that only redraw a screen), with `{}` for an id. A route listed is one the action **may** call.

## Screens (`RENDER.<screen>`)

| screen | script |
|---|---|
| `agent` | agent.js |
| `animate` | animate.js |
| `library` | app.js |
| `settings` | app.js |
| `settings` | auth.js |
| `chat` | chat.js |
| `create` | editor.js |
| `editor` | editor.js |
| `export` | editor.js |
| `effects` | effects.js |
| `generate` | generate.js |
| `history` | history.js |
| `home` | home.js |
| `generate` | live.js |
| `pack` | packs.js |
| `effects` | particles.js |
| `prepare` | prepare.js |
| `help` | support.js |
| `settings` | tickets.js |
| `settings` | trash.js |
| `users` | users.js |

## Server routes the page names

`/api` · `/api/ai` · `/api/ai/backend` · `/api/auth` · `/api/auth/credits` · `/api/auth/forgot` · `/api/auth/login` · `/api/auth/logout` · `/api/auth/me` · `/api/auth/password` · `/api/auth/signup` · `/api/chat/*` · `/api/chat/agent` · `/api/chat/sessions` · `/api/chat/sessions/{}/delete` · `/api/chat/sessions/{}/messages` · `/api/chat/sessions/{}/settings` · `/api/collection` · `/api/cutout` · `/api/effects` · `/api/effects/{}/add` · `/api/effects/{}/estimate` · `/api/effects/{}/particles` · `/api/effects/{}/particles_estimate` · `/api/effects/{}/particles_pick` · `/api/effects/{}/plan` · `/api/effects/{}/suggest` · `/api/effects/{}/video` · `/api/faq` · `/api/faq/{}/{}` · `/api/generations` · `/api/generations/${+String(id).replace(/\D/g,` · `/api/generations/removed` · `/api/generations/{}/add` · `/api/generations/{}/allow` · `/api/generations/{}/animate` · `/api/generations/{}/drop` · `/api/generations/{}/edge` · `/api/generations/{}/edge_preview` · `/api/generations/{}/edit` · `/api/generations/{}/export-collection` · `/api/generations/{}/export.zip` · `/api/generations/{}/family` · `/api/generations/{}/join` · `/api/generations/{}/leave` · `/api/generations/{}/pack` · `/api/generations/{}/particles` · `/api/generations/{}/pick` · `/api/generations/{}/pick_video` · `/api/generations/{}/quick_sheet` · `/api/generations/{}/recheck` · `/api/generations/{}/recut` · `/api/generations/{}/remove` · `/api/generations/{}/remove_video` · `/api/generations/{}/replace` · `/api/generations/{}/restore` · `/api/generations/{}/reveal` · `/api/generations/{}/sheet_preview` · `/api/generations/{}/studio_edit` · `/api/generations/{}/video_sheet/{}/video` · `/api/higgsfield` · `/api/higgsfield/history` · `/api/higgsfield/import` · `/api/history` · `/api/import` · `/api/imports/candidates` · `/api/inputs` · `/api/jobs` · `/api/jobs/{}/dismiss` · `/api/jobs/{}/retry` · `/api/jobs/{}/retry_estimate` · `/api/jobs/{}/{}` · `/api/library` · `/api/live/cost` · `/api/live/ref` · `/api/live/sheet` · `/api/live/video` · `/api/llm/models` · `/api/models` · `/api/notifications` · `/api/packs` · `/api/packs/{}/delete` · `/api/packs/{}/export-collection` · `/api/packs/{}/export.zip` · `/api/packs/{}/merge` · `/api/packs/{}/particles` · `/api/packs/{}/render` · `/api/packs/{}/restore` · `/api/packs/{}/stickers/{}` · `/api/packs/{}/stickers/{}/animate` · `/api/packs/{}/stickers/{}/delete` · `/api/packs/{}/stickers/{}/move` · `/api/packs/{}/stickers/{}/particle-preview` · `/api/packs/{}/stickers/{}/particles` · `/api/packs/{}/stickers/{}/replace` · `/api/packs/{}/telegram` · `/api/packs/{}/telegram.zip` · `/api/particles` · `/api/particles/deleted` · `/api/particles/{}` · `/api/particles/{}/add` · `/api/particles/{}/delete` · `/api/particles/{}/duplicate` · `/api/particles/{}/link` · `/api/particles/{}/more` · `/api/particles/{}/preview` · `/api/particles/{}/render` · `/api/particles/{}/restore` · `/api/particles/{}/save-as-new` · `/api/particles/{}/unlink` · `/api/people` · `/api/plan` · `/api/plan/more` · `/api/plan/next` · `/api/prepared/match` · `/api/prepared/setting` · `/api/projects` · `/api/projects/from_sticker` · `/api/projects/{}/delete` · `/api/projects/{}/render` · `/api/stickers/delete` · `/api/stickers/move` · `/api/support/ask` · `/api/support/conversations` · `/api/support/conversations/{}/{}` · `/api/support/queue` · `/api/support/tickets` · `/api/tasks` · `/api/telegram` · `/api/telegram/config` · `/api/telegram/disconnect` · `/api/tickets` · `/api/tickets/{}/answer` · `/api/tickets/{}/reply` · `/api/tickets/{}/resolve` · `/api/tickets/{}/status` · `/api/trash` · `/api/trash/purge` · `/api/trash/purge_all` · `/api/trash/purges` · `/api/trending` · `/api/trending/{}/${on` · `/api/trending/{}/comments` · `/api/trending/{}/comments/{}/delete` · `/api/trending/{}/file/{}` · `/api/trending/{}/unshare` · `/api/trending/{}/use` · `/api/usage` · `/api/users` · `/api/users/me` · `/api/users/overview` · `/api/watch` · `/api/watch/purge` · `/api/watch/remove` · `/api/watch/restore`

## Actions by script

### `agent.js` (29)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `agcar` | 313 | agent.js | none (browser only) |
| `agtile` | 314 | agent.js | none (browser only) |
| `agsel` | 317 | agent.js | none (browser only) |
| `agchip` | 321 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/messages` |
| `agfill` | 322 | agent.js | none (browser only) |
| `agedit` | 323 | agent.js | `/api/generations`<br>`/api/generations/{}/studio_edit` |
| `agsetting` | 324 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agaction` | 325 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/messages` |
| `agcut` | 326 | agent.js | `/api/chat/sessions`<br>`/api/generations/{}/recut` |
| `aganimal` | 327 | agent.js | `/api/chat/sessions`<br>`/api/generations/{}/animate` |
| `agretry` | 328 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/messages` |
| `agtrace` | 329 | agent.js | none (browser only) |
| `agstep` | 330 | agent.js | none (browser only) |
| `agstudio` | 331 | agent.js | none (browser only) |
| `agallow` | 332 | agent.js | `/api/chat/sessions`<br>`/api/generations/{}/allow` |
| `agallowall` | 337 | agent.js | `/api/chat/sessions`<br>`/api/generations/{}/allow` |
| `agnew` | 347 | agent.js | none (browser only) |
| `agopen` | 348 | agent.js | none (browser only) |
| `agdel` | 349 | agent.js | `/api/chat/sessions/{}/delete` |
| `agset` | 350 | agent.js | none (browser only) |
| `agsetgrid` | 351 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `aggridtoggle` | 353 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agstage` | 366 | agent.js | `/api/models` |
| `agstagepick` | 369 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agstyle` | 387 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agstyles` | 388 | agent.js | none (browser only) |
| `agsetask` | 389 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agbe` | 390 | agent.js | `/api/ai`<br>`/api/ai/backend` |
| `agcr` | 419 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |

### `animate.js` (8)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `antab` | 46 | animate.js | none (browser only) |
| `anseek` | 47 | animate.js | none (browser only) |
| `anplay` | 48 | animate.js | none (browser only) |
| `anjump` | 49 | animate.js | none (browser only) |
| `anstep` | 50 | animate.js | none (browser only) |
| `anback` | 51 | animate.js | none (browser only) |
| `anexport` | 70 | animate.js | `/api/packs/{}/stickers/{}/animate` |
| `ansave` | 70 | animate.js | `/api/packs/{}/stickers/{}/animate` |

### `app.js` (24)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `dlgx` | 44 | app.js, auth.js, editor.js, generate.js, imports.js, live.js, packs.js, particles.js, prepare.js, support.js, telegram.js, tickets.js, trash.js, trending.js | none (browser only) |
| `askok` | 47 | app.js | none (browser only) |
| `copyid` | 49 | agent.js, generate.js | none (browser only) |
| `cfok` | 51 | app.js | none (browser only) |
| `pk` | 56 | app.js | none (browser only) |
| `pknew` | 57 | app.js | `/api/packs` |
| `c2tog` | 97 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `nav` | 98 | animate.js, app.js, auth.js, chat.js, editor.js, home.js, packs.js, prepare.js, tickets.js | none (browser only) |
| `rme` | 99 | app.js | none (browser only) |
| `rtrash` | 106 | app.js | none (browser only) |
| `lsel` | 138 | app.js, packs.js | none (browser only) |
| `lselall` | 139 | app.js | none (browser only) |
| `lselnone` | 140 | app.js | none (browser only) |
| `lselmove` | 146 | app.js | `/api/stickers/move` |
| `lseldel` | 147 | app.js | `/api/stickers/delete` |
| `libtab` | 193 | app.js | none (browser only) |
| `pkmerge` | 194 | app.js | `/api/packs/{}/merge` |
| `pkgrp` | 198 | app.js | none (browser only) |
| `seeall` | 199 | app.js | none (browser only) |
| `openpack` | 220 | app.js, home.js | none (browser only) |
| `newpack` | 221 | app.js | none (browser only) |
| `newpackname` | 222 | app.js | `/api/packs` |
| `setgo` | 235 | app.js | none (browser only) |
| `prepset` | 236 | app.js | `/api/prepared/setting` |

### `auth.js` (12)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `aumode` | 57 | auth.js | `/api`<br>`/api/auth`<br>`/api/auth/credits`<br>`/api/auth/forgot`<br>`/api/auth/login`<br>`/api/auth/logout`<br>`/api/auth/password`<br>`/api/auth/signup`<br>`/api/people` |
| `ausignin` | 58 | auth.js | `/api`<br>`/api/auth`<br>`/api/auth/credits`<br>`/api/auth/forgot`<br>`/api/auth/login`<br>`/api/auth/logout`<br>`/api/auth/password`<br>`/api/auth/signup`<br>`/api/people` |
| `ausignup` | 59 | auth.js | `/api`<br>`/api/auth`<br>`/api/auth/credits`<br>`/api/auth/forgot`<br>`/api/auth/logout`<br>`/api/auth/password`<br>`/api/auth/signup`<br>`/api/people` |
| `auforgot` | 60 | auth.js | `/api`<br>`/api/auth`<br>`/api/auth/credits`<br>`/api/auth/forgot`<br>`/api/auth/logout`<br>`/api/auth/password`<br>`/api/people` |
| `auchange` | 61 | auth.js | `/api`<br>`/api/auth`<br>`/api/auth/credits`<br>`/api/auth/logout`<br>`/api/auth/password`<br>`/api/people` |
| `aukeep` | 64 | auth.js | `/api`<br>`/api/auth`<br>`/api/auth/credits`<br>`/api/auth/logout`<br>`/api/people` |
| `aulogout` | 65 | app.js, auth.js | `/api`<br>`/api/auth`<br>`/api/auth/credits`<br>`/api/auth/logout`<br>`/api/people` |
| `aucreditask` | 66 | auth.js, composer.js | `/api`<br>`/api/auth`<br>`/api/auth/credits`<br>`/api/people` |
| `auadd` | 70 | auth.js | `/api`<br>`/api/auth`<br>`/api/people` |
| `aupeople` | 72 | auth.js | `/api`<br>`/api/auth`<br>`/api/people` |
| `aucredits` | 75 | auth.js | `/api`<br>`/api/auth`<br>`/api/people` |
| `auignore` | 76 | auth.js | `/api`<br>`/api/auth`<br>`/api/people` |

### `chat.js` (9)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `chsend` | 74 | chat.js | `/api/packs/{}/stickers/{}/particle-preview` |
| `chtray` | 75 | chat.js | none (browser only) |
| `chpack` | 75 | chat.js | none (browser only) |
| `chem` | 76 | chat.js | none (browser only) |
| `chpick` | 81 | chat.js | `/api/packs/{}/stickers/{}/particle-preview` |
| `chreplay` | 82 | chat.js | `/api/packs/{}/stickers/{}/particle-preview` |
| `chlike` | 84 | chat.js | `/api/packs/{}/stickers/{}/particle-preview` |
| `chview` | 86 | chat.js | none (browser only) |
| `chclear` | 88 | chat.js | none (browser only) |

### `composer.js` (12)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `cpmenu` | 63 | composer.js | none (browser only) |
| `cpadd` | 74 | composer.js | none (browser only) |
| `cprefx` | 75 | composer.js | `/api/live/ref` |
| `cppart` | 87 | composer.js | none (browser only) |
| `cploop` | 109 | composer.js | none (browser only) |
| `cpai` | 110 | composer.js | `/api/ai` |
| `cpstroke` | 111 | composer.js | none (browser only) |
| `cpstrokeset` | 112 | composer.js | none (browser only) |
| `cpstyles` | 119 | composer.js | none (browser only) |
| `cpstylepick` | 120 | composer.js | none (browser only) |
| `ggo` | 127 | (no `data-act` button: called from code, a key, or a form) | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video`<br>`/api/prepared/match` |
| `gnewlive` | 140 | generate.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video` |

### `editor.js` (27)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `pickfile` | 92 | editor.js | none (browser only) |
| `newtext` | 92 | editor.js | none (browser only) |
| `cleartarget` | 92 | editor.js | `/api/generations` |
| `editrecent` | 93 | editor.js | none (browser only) |
| `histgo` | 118 | editor.js | none (browser only) |
| `edback` | 147 | editor.js | none (browser only) |
| `edundo` | 147 | editor.js | none (browser only) |
| `edredo` | 147 | editor.js | none (browser only) |
| `edtool` | 149 | editor.js | none (browser only) |
| `laysel` | 150 | editor.js | none (browser only) |
| `layvis` | 151 | editor.js | none (browser only) |
| `laylock` | 152 | editor.js | none (browser only) |
| `layup` | 154 | editor.js | none (browser only) |
| `laydown` | 154 | editor.js | none (browser only) |
| `laydel` | 155 | editor.js | none (browser only) |
| `laydup` | 156 | editor.js | none (browser only) |
| `addtext` | 157 | editor.js | none (browser only) |
| `addemoji` | 157 | editor.js | none (browser only) |
| `resetsub` | 158 | editor.js | none (browser only) |
| `adjreset` | 159 | editor.js | none (browser only) |
| `recut` | 160 | editor.js | `/api/cutout` |
| `edsave` | 199 | editor.js | `/api/generations/{}/edit` |
| `exback` | 219 | editor.js | none (browser only) |
| `xsave` | 220 | editor.js | `/api/packs`<br>`/api/packs/{}/render` |
| `xdl` | 224 | editor.js | none (browser only) |
| `xopen` | 225 | editor.js | none (browser only) |
| `xmore` | 225 | editor.js | none (browser only) |

### `effects.js` (29)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `fxback` | 45 | effects.js | none (browser only) |
| `fxpack` | 79 | effects.js | none (browser only) |
| `fxst` | 80 | effects.js | none (browser only) |
| `fxall` | 81 | effects.js | none (browser only) |
| `fxmode` | 82 | effects.js | none (browser only) |
| `fxgrid` | 83 | effects.js | none (browser only) |
| `fxgo` | 84 | effects.js | `/api/effects` |
| `fxnovlm` | 88 | effects.js | `/api/effects` |
| `fxdgrid` | 176 | effects.js | none (browser only) |
| `fxdretry` | 177 | effects.js | `/api/effects/{}/suggest` |
| `fxdchip` | 178 | effects.js | `/api/effects/{}/particles_estimate` |
| `fxdadd` | 182 | effects.js | `/api/effects/{}/particles_estimate` |
| `fxddraw` | 184 | effects.js, particles.js | `/api/effects`<br>`/api/effects/{}/particles`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `fxdredo` | 187 | effects.js | none (browser only) |
| `fxdcancel` | 188 | effects.js | none (browser only) |
| `fxdchange` | 189 | effects.js | none (browser only) |
| `fxdcell` | 190 | effects.js | none (browser only) |
| `fxdall` | 191 | effects.js | none (browser only) |
| `fxduse` | 192 | effects.js | `/api/effects`<br>`/api/effects/{}/particles_pick`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `fxprice` | 229 | effects.js, particles.js | `/api/effects/{}/estimate` |
| `fxdelpiece` | 233 | effects.js | `/api/effects`<br>`/api/effects/{}/plan`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `fxaddpiece` | 235 | effects.js | `/api/effects/{}/plan` |
| `fxvideo` | 236 | effects.js, particles.js | `/api/effects`<br>`/api/effects/{}/video`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `fxpick` | 245 | effects.js | none (browser only) |
| `fxpickall` | 246 | effects.js | none (browser only) |
| `fxadd` | 247 | effects.js | `/api/effects`<br>`/api/effects/{}/add`<br>`/api/generations`<br>`/api/generations/{}/particles`<br>`/api/jobs`<br>`/api/particles` |
| `fxopenset` | 265 | effects.js | `/api/particles/{}/preview` |
| `fxuseset` | 273 | effects.js | `/api/particles` |
| `psusesave` | 274 | (no `data-act` button: called from code, a key, or a form) | `/api/particles` |

### `generate.js` (68)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `goutline` | 182 | generate.js | none (browser only) |
| `ggo` | 195 | (no `data-act` button: called from code, a key, or a form) | `/api/generations`<br>`/api/particles`<br>`/api/particles/{}/more` |
| `gmore` | 197 | (no `data-act` button: called from code, a key, or a form) | `/api/generations` |
| `gnext` | 204 | generate.js, projmap.js | `/api/live/cost`<br>`/api/plan/next` |
| `gbdrop` | 213 | generate.js | none (browser only) |
| `ginc` | 214 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `ganimslice` | 233 | generate.js | `/api/generations/{}/animate` |
| `greplace` | 235 | generate.js | none (browser only) |
| `grepundo` | 239 | generate.js | `/api/generations/{}/replace` |
| `ggen` | 245 | generate.js, projmap.js | none (browser only) |
| `gmain` | 246 | generate.js, projmap.js | `/api/generations/{}/pick` |
| `gdel` | 248 | generate.js, projmap.js | `/api/generations/{}/family`<br>`/api/generations/{}/particles`<br>`/api/generations/{}/remove`<br>`/api/history` |
| `ganmo` | 332 | generate.js | none (browser only) |
| `gcutany` | 345 | generate.js | `/api/generations/{}/recut` |
| `gretrysheet` | 346 | generate.js | `/api/generations` |
| `greqgo` | 347 | generate.js | `/api/generations` |
| `gopenfolder` | 367 | generate.js | `/api/generations/{}/reveal` |
| `pgresheet` | 406 | generate.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video` |
| `pgredo` | 412 | generate.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video` |
| `pgreset` | 424 | generate.js | none (browser only) |
| `gdnb` | 446 | generate.js | none (browser only) |
| `gdtab` | 454 | composer.js, generate.js | none (browser only) |
| `gddiscard` | 455 | generate.js | none (browser only) |
| `gdpriceretry` | 456 | generate.js | `/api/live/cost` |
| `gprompt` | 459 | composer.js, generate.js | `/api/particles`<br>`/api/particles/{}/more`<br>`/api/plan` |
| `gpromptfree` | 460 | generate.js | `/api/plan` |
| `gdsheet` | 479 | generate.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video`<br>`/api/plan/more` |
| `pgsheet` | 498 | generate.js, projmap.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video` |
| `pgvideo` | 501 | generate.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video` |
| `ggroup` | 507 | generate.js, projmap.js | none (browser only) |
| `ggroupgo` | 510 | generate.js | `/api/generations/{}/join`<br>`/api/generations/{}/particles`<br>`/api/history` |
| `grm` | 511 | generate.js | `/api/generations/removed`<br>`/api/generations/{}/particles`<br>`/api/generations/{}/remove`<br>`/api/history` |
| `gvmode` | 515 | generate.js | none (browser only) |
| `gtab` | 516 | generate.js, particles.js, projmap.js | none (browser only) |
| `ganimate` | 520 | generate.js | `/api/generations/{}/animate` |
| `gadd` | 528 | generate.js, particles.js | none (browser only) |
| `pwgo` | 567 | generate.js | `/api/generations/{}/add`<br>`/api/packs` |
| `gopenpack` | 581 | generate.js | none (browser only) |
| `gvideo` | 584 | generate.js | `/api/generations/{}/quick_sheet` |
| `gpickvideo` | 597 | generate.js | none (browser only) |
| `gsheetapprove` | 598 | generate.js | `/api/generations/{}/quick_sheet` |
| `gvclose` | 599 | generate.js | none (browser only) |
| `gcopyprompt` | 600 | generate.js | none (browser only) |
| `gapick` | 639 | generate.js, projmap.js | `/api/generations/{}/pick_video` |
| `garm` | 641 | generate.js, projmap.js | `/api/generations/{}/remove_video` |
| `gvsheet` | 651 | generate.js | none (browser only) |
| `gaclose` | 652 | generate.js | none (browser only) |
| `gptog` | 715 | generate.js | none (browser only) |
| `gshk` | 716 | generate.js | none (browser only) |
| `gsheet` | 717 | generate.js | none (browser only) |
| `gsview` | 732 | generate.js | none (browser only) |
| `gstog` | 733 | generate.js | none (browser only) |
| `gsclose` | 734 | generate.js | none (browser only) |
| `ghiggs` | 737 | generate.js | `/api/plan` |
| `hcopy` | 743 | generate.js | none (browser only) |
| `hgenop` | 744 | generate.js | `/api/jobs` |
| `hreserve` | 752 | generate.js | `/api/tasks` |
| `gmall` | 783 | generate.js | none (browser only) |
| `gmtab` | 784 | generate.js | none (browser only) |
| `gopen` | 785 | generate.js | none (browser only) |
| `gmclose` | 786 | generate.js | none (browser only) |
| `gstep` | 787 | generate.js | none (browser only) |
| `gedit` | 788 | generate.js | `/api/generations`<br>`/api/generations/{}/studio_edit` |
| `openstudio` | 813 | particles.js | `/api/generations` |
| `lcstudioedit` | 815 | packs.js | `/api/generations`<br>`/api/generations/{}/studio_edit` |
| `lcopenstudio` | 816 | packs.js | none (browser only) |
| `gcell` | 847 | generate.js | `/api/generations/{}/allow`<br>`/api/generations/{}/drop` |
| `gallowall` | 857 | generate.js | `/api/generations/{}/allow` |

### `history.js` (5)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `hsopen` | 25 | history.js | none (browser only) |
| `hgen` | 26 | history.js | `/api/generations` |
| `hremove` | 28 | history.js | `/api/watch`<br>`/api/watch/remove` |
| `hrestore` | 32 | history.js | `/api/watch`<br>`/api/watch/restore` |
| `hpurge` | 33 | history.js | `/api/watch`<br>`/api/watch/purge` |

### `home.js` (4)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `hmfilter` | 55 | home.js | none (browser only) |
| `hmai` | 58 | home.js | none (browser only) |
| `hmfilm` | 60 | home.js | none (browser only) |
| `home` | 62 | app.js | none (browser only) |

### `imports.js` (9)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `impopen` | 28 | imports.js | `/api/higgsfield/history`<br>`/api/import`<br>`/api/imports/candidates` |
| `impackopen` | 30 | app.js, home.js | `/api/higgsfield/history`<br>`/api/import`<br>`/api/imports/candidates` |
| `impupload` | 31 | imports.js | `/api/higgsfield/history`<br>`/api/import`<br>`/api/imports/candidates` |
| `impchoose` | 36 | imports.js | `/api/higgsfield/history`<br>`/api/import` |
| `impnew` | 37 | imports.js | `/api/higgsfield/history`<br>`/api/import` |
| `impretry` | 38 | imports.js | `/api/higgsfield/history`<br>`/api/import` |
| `imphistory` | 39 | imports.js | `/api/higgsfield/history`<br>`/api/import` |
| `imphf` | 40 | imports.js | `/api/import` |
| `impbatch` | 44 | imports.js | `/api/import` |

### `job-recovery.js` (4)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `jrrefresh` | 30 | (no `data-act` button: called from code, a key, or a form) | `/api/jobs`<br>`/api/jobs/{}/dismiss`<br>`/api/jobs/{}/retry`<br>`/api/jobs/{}/retry_estimate`<br>`/api/jobs/{}/{}` |
| `jrcheck` | 32 | (no `data-act` button: called from code, a key, or a form) | `/api/jobs`<br>`/api/jobs/{}/dismiss`<br>`/api/jobs/{}/retry`<br>`/api/jobs/{}/retry_estimate` |
| `jrcontinue` | 33 | (no `data-act` button: called from code, a key, or a form) | `/api/jobs`<br>`/api/jobs/{}/dismiss`<br>`/api/jobs/{}/retry`<br>`/api/jobs/{}/retry_estimate` |
| `jrretry` | 34 | (no `data-act` button: called from code, a key, or a form) | `/api/jobs`<br>`/api/jobs/{}/dismiss`<br>`/api/jobs/{}/retry`<br>`/api/jobs/{}/retry_estimate` |

### `live.js` (20)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `lusage` | 27 | composer.js | `/api/higgsfield`<br>`/api/usage` |
| `lstyle` | 49 | live.js | none (browser only) |
| `lmodels` | 53 | composer.js, live.js | none (browser only) |
| `lmpick` | 66 | live.js | none (browser only) |
| `lmdone` | 67 | live.js | none (browser only) |
| `qtoggle` | 158 | live.js | none (browser only) |
| `qretry` | 163 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `qcopy` | 164 | live.js | none (browser only) |
| `ljdismiss` | 165 | live.js | `/api/jobs/{}/dismiss` |
| `egapply` | 255 | live.js | `/api/generations/{}/edge` |
| `egundo` | 259 | live.js | `/api/generations/{}/edge` |
| `vlmyes` | 294 | effects.js | none (browser only) |
| `hunpack` | 322 | live.js, projmap.js | `/api/generations/{}/pack`<br>`/api/generations/{}/particles`<br>`/api/history` |
| `hopenpack` | 323 | live.js | `/api/generations/{}/particles` |
| `hleave` | 327 | projmap.js | `/api/generations/{}/leave`<br>`/api/generations/{}/particles`<br>`/api/history` |
| `gpurge` | 352 | live.js | `/api/generations/removed`<br>`/api/trash/purge`<br>`/api/trash/purges` |
| `gpurgeall` | 356 | live.js | `/api/trash` |
| `gpurgeallgo` | 360 | live.js | `/api/generations/removed`<br>`/api/trash/purge_all`<br>`/api/trash/purges` |
| `grestore` | 362 | live.js | `/api/generations/removed`<br>`/api/generations/{}/particles`<br>`/api/generations/{}/restore`<br>`/api/history` |
| `hopen` | 373 | composer.js, live.js | `/api/generations/{}/particles`<br>`/api/particles` |

### `packs.js` (36)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `pktab` | 6 | packs.js | none (browser only) |
| `colopen` | 37 | packs.js | `/api/collection` |
| `colsend` | 43 | packs.js | `/api/generations/{}/export-collection`<br>`/api/packs/{}/export-collection` |
| `pkadd` | 51 | packs.js | none (browser only) |
| `pkrename` | 52 | packs.js | `/api/packs` |
| `pkdel` | 57 | packs.js | `/api/packs/{}/delete` |
| `stanim` | 58 | packs.js | none (browser only) |
| `stcover` | 59 | packs.js | `/api/packs` |
| `stdel` | 60 | packs.js | `/api/packs/{}/stickers/{}/delete` |
| `stedit` | 61 | packs.js | `/api/generations`<br>`/api/generations/{}/studio_edit`<br>`/api/projects/from_sticker` |
| `stview` | 63 | packs.js | none (browser only) |
| `stname` | 64 | packs.js | none (browser only) |
| `strep` | 69 | packs.js | `/api/packs/{}/stickers/{}/replace` |
| `strepone` | 78 | packs.js | `/api/packs/{}/stickers/{}/replace` |
| `strepall` | 80 | packs.js | `/api/packs/{}/stickers/{}/replace` |
| `strepundo` | 82 | packs.js | `/api/packs/{}/stickers/{}/replace` |
| `stsave` | 83 | packs.js | `/api/packs/{}/stickers/{}` |
| `pkpreview` | 84 | packs.js | none (browser only) |
| `pvbg` | 87 | packs.js | none (browser only) |
| `lcsend` | 122 | packs.js | none (browser only) |
| `lcopen` | 123 | app.js | none (browser only) |
| `lcclose` | 123 | packs.js | none (browser only) |
| `lcprev` | 123 | packs.js | none (browser only) |
| `lcnext` | 123 | packs.js | none (browser only) |
| `lcgo` | 124 | packs.js | none (browser only) |
| `lcbg` | 124 | packs.js | none (browser only) |
| `lcpack` | 125 | packs.js | none (browser only) |
| `lcedit` | 126 | packs.js | `/api/projects/from_sticker` |
| `lctimeline` | 127 | packs.js | none (browser only) |
| `lcmove` | 128 | packs.js | `/api/packs/{}/stickers/{}/move` |
| `ptmake` | 185 | packs.js | none (browser only) |
| `ptrunsim` | 186 | packs.js | `/api/effects`<br>`/api/effects/{}/estimate`<br>`/api/effects/{}/particles_estimate`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `ptopen` | 187 | packs.js | none (browser only) |
| `ptsaved` | 188 | packs.js | none (browser only) |
| `ptadd` | 189 | packs.js | `/api/effects/{}/add`<br>`/api/generations/{}/particles`<br>`/api/packs/{}/stickers/{}/particles` |
| `psshow` | 218 | packs.js | `/api/particles`<br>`/api/particles/{}/preview` |

### `particles.js` (54)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `spcontinue` | 29 | particles.js | `/api/effects`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `spscope` | 30 | particles.js | none (browser only) |
| `spapprove` | 32 | particles.js | none (browser only) |
| `sppack` | 62 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `spkind` | 63 | particles.js | none (browser only) |
| `spgrid` | 64 | particles.js | none (browser only) |
| `spst` | 65 | particles.js | none (browser only) |
| `spall` | 67 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `spstart` | 69 | particles.js | `/api/effects`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles`<br>`/api/particles/{}/preview` |
| `spnovlm` | 70 | (no `data-act` button: called from code, a key, or a form) | `/api/effects`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles`<br>`/api/particles/{}/preview` |
| `spreset` | 77 | particles.js | none (browser only) |
| `spimportretry` | 100 | particles.js | `/api/effects/{}/estimate`<br>`/api/effects/{}/particles_estimate`<br>`/api/particles` |
| `spprice` | 101 | particles.js | `/api/effects/{}/estimate`<br>`/api/effects/{}/particles_estimate`<br>`/api/particles` |
| `spfresh` | 114 | particles.js | none (browser only) |
| `spopen` | 136 | particles.js | none (browser only) |
| `spmake` | 138 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `psopen` | 210 | particles.js | `/api/particles`<br>`/api/particles/{}/more`<br>`/api/particles/{}/preview` |
| `psassign` | 213 | particles.js | none (browser only) |
| `psassignsave` | 215 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/link`<br>`/api/particles/{}/unlink` |
| `psunassign` | 218 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/unlink` |
| `psdup` | 219 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/duplicate` |
| `psrename` | 220 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}` |
| `psdel` | 221 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/delete` |
| `psrestore` | 227 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/restore` |
| `pspickcell` | 228 | particles.js | none (browser only) |
| `pspickcancel` | 231 | particles.js | none (browser only) |
| `pspicksave` | 232 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}`<br>`/api/particles/{}/preview` |
| `psmoremode` | 267 | particles.js | `/api/particles/{}/more` |
| `psmoreprice` | 268 | particles.js | `/api/particles/{}/more` |
| `psmoreexisting` | 269 | particles.js | none (browser only) |
| `psmoregrid` | 275 | particles.js | `/api/particles/{}/more` |
| `psmorechip` | 276 | (no `data-act` button: called from code, a key, or a form) | `/api/particles/{}/more` |
| `psmoreadd` | 281 | (no `data-act` button: called from code, a key, or a form) | `/api/particles/{}/more` |
| `psmoredraw` | 283 | particles.js | `/api/effects`<br>`/api/generations`<br>`/api/jobs`<br>`/api/packs/{}/particles`<br>`/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/more` |
| `psbnewpack` | 309 | particles.js | `/api/particles/{}/add` |
| `psbpreset` | 344 | particles.js | `/api/particles/{}/preview` |
| `psbshuffle` | 345 | particles.js | `/api/particles/{}/preview` |
| `psbsave` | 353 | particles.js | `/api/packs/{}/stickers/{}/particles`<br>`/api/particles/{}` |
| `psbsaveas` | 354 | particles.js | `/api/packs/{}/stickers/{}/particles`<br>`/api/particles/{}/preview`<br>`/api/particles/{}/save-as-new` |
| `pschat` | 355 | particles.js | `/api/particles/{}` |
| `psbrender` | 357 | particles.js | `/api/packs/{}/particles`<br>`/api/particles`<br>`/api/particles/{}/render` |
| `psbadd` | 361 | packs.js, particles.js | `/api/packs/{}/particles`<br>`/api/particles`<br>`/api/particles/{}/add` |
| `pspickset` | 373 | particles.js | `/api/particles/{}/link`<br>`/api/particles/{}/preview` |
| `psmakepack` | 375 | packs.js | none (browser only) |
| `pspickpack` | 376 | packs.js | none (browser only) |
| `pspackassign` | 377 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `agpscope` | 379 | agent.js | `/api/particles` |
| `agpopen` | 380 | agent.js | `/api/particles`<br>`/api/particles/{}/preview` |
| `agpapprove` | 381 | agent.js | `/api/generations` |
| `psrecover` | 383 | packs.js | none (browser only) |
| `psrecovercreate` | 384 | particles.js | none (browser only) |
| `psrecovergo` | 386 | particles.js | `/api/particles`<br>`/api/particles/{}/preview` |
| `ptcancel` | 403 | particles.js | `/api/particles/{}/delete` |
| `ptgo` | 404 | particles.js | `/api/history`<br>`/api/particles`<br>`/api/particles/{}/more`<br>`/api/particles/{}/preview` |

### `prepare.js` (24)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `anproject` | 18 | animate.js | `/api/projects/from_sticker` |
| `openproj` | 19 | editor.js | none (browser only) |
| `delproj` | 20 | editor.js | `/api/generations`<br>`/api/projects/{}/delete` |
| `pundo` | 69 | prepare.js | none (browser only) |
| `predo` | 69 | prepare.js | none (browser only) |
| `ptool` | 148 | prepare.js | none (browser only) |
| `pplay` | 148 | prepare.js | none (browser only) |
| `pstep` | 149 | prepare.js | none (browser only) |
| `psel` | 150 | prepare.js | none (browser only) |
| `pvis` | 151 | prepare.js | none (browser only) |
| `plock` | 151 | prepare.js | none (browser only) |
| `pdel` | 152 | prepare.js | none (browser only) |
| `pt` | 153 | prepare.js | none (browser only) |
| `paddtext` | 156 | prepare.js | none (browser only) |
| `paddemoji` | 157 | prepare.js | none (browser only) |
| `paddstk` | 157 | prepare.js | none (browser only) |
| `pbgretry` | 158 | prepare.js | `/api/projects` |
| `pbgskip` | 159 | prepare.js | `/api/projects` |
| `prender` | 200 | prepare.js | `/api/projects`<br>`/api/projects/{}/render` |
| `psavepack` | 200 | prepare.js | `/api/projects`<br>`/api/projects/{}/render` |
| `pstudiosave` | 203 | prepare.js | `/api/generations/{}/studio_edit`<br>`/api/projects` |
| `ppackreplace` | 207 | prepare.js | `/api/projects`<br>`/api/projects/{}/render` |
| `pstudioback` | 212 | prepare.js | none (browser only) |
| `ppackback` | 212 | prepare.js | none (browser only) |

### `projmap.js` (2)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `pmlist` | 49 | projmap.js | `/api/generations/removed`<br>`/api/history` |
| `pmopen` | 51 | projmap.js | `/api/generations/removed`<br>`/api/generations/{}/particles`<br>`/api/history` |

### `sheet-recovery.js` (1)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `ssallow` | 16 | sheet-recovery.js | `/api/chat/sessions`<br>`/api/generations/{}/allow` |

### `support.js` (26)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `sutab` | 101 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/ask`<br>`/api/support/conversations/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `sunew` | 102 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/ask`<br>`/api/support/conversations/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `suopen` | 103 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/ask`<br>`/api/support/conversations/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `sunote` | 104 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/ask`<br>`/api/support/conversations/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `sushot` | 105 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/ask`<br>`/api/support/conversations/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `sushotx` | 106 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/ask`<br>`/api/support/conversations/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `suask` | 107 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/ask`<br>`/api/support/conversations/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `sureq` | 113 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `supriv` | 114 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `sucopy` | 115 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `suforget` | 116 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `sugo` | 117 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/generations`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `susolved` | 119 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `suunsolved` | 120 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `suesc` | 121 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `sureopen` | 122 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `sucite` | 123 | support.js | `/api/faq`<br>`/api/faq/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `suq` | 125 | support.js | `/api/faq/{}/{}`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `sureply` | 127 | support.js | `/api/faq/{}/{}`<br>`/api/tickets/{}/reply`<br>`/api/tickets/{}/resolve` |
| `suresolve` | 129 | support.js | `/api/faq/{}/{}`<br>`/api/tickets/{}/resolve` |
| `sufaq` | 131 | support.js | `/api/faq/{}/{}` |
| `sufall` | 132 | support.js | `/api/faq/{}/{}` |
| `sufsave` | 134 | support.js | none (browser only) |
| `sufpub` | 135 | support.js | none (browser only) |
| `sufdisc` | 136 | support.js | none (browser only) |
| `sufarch` | 137 | support.js | none (browser only) |

### `telegram.js` (5)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `tgsend` | 41 | packs.js | `/api/packs/{}/telegram`<br>`/api/packs/{}/telegram.zip` |
| `tgconnect` | 42 | telegram.js | `/api/packs/{}/telegram`<br>`/api/packs/{}/telegram.zip`<br>`/api/telegram/config` |
| `tgdisconnect` | 45 | telegram.js | `/api/telegram/disconnect` |
| `tgcopy` | 46 | telegram.js | none (browser only) |
| `tgsettings` | 53 | telegram.js | `/api/packs/{}/telegram.zip` |

### `tickets.js` (8)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `tkopen` | 36 | tickets.js | `/api/tickets`<br>`/api/tickets/{}/answer`<br>`/api/tickets/{}/status` |
| `tkfilter` | 37 | tickets.js | `/api/tickets`<br>`/api/tickets/{}/answer`<br>`/api/tickets/{}/status` |
| `tkans` | 41 | tickets.js | `/api/tickets`<br>`/api/tickets/{}/answer`<br>`/api/tickets/{}/status` |
| `tkother` | 42 | tickets.js | `/api/tickets`<br>`/api/tickets/{}/answer`<br>`/api/tickets/{}/status` |
| `tkstatus` | 43 | tickets.js | `/api/tickets`<br>`/api/tickets/{}/status` |
| `tkreport` | 44 | agent.js, generate.js, packs.js, projmap.js, tickets.js | `/api/tickets` |
| `tksend` | 45 | tickets.js | `/api/tickets` |
| `tkrefresh` | 49 | tickets.js | none (browser only) |

### `trash.js` (5)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `trrestore` | 54 | trash.js | `/api/generations/${+String(id).replace(/\D/g,`<br>`/api/packs/{}/restore`<br>`/api/trash/purge`<br>`/api/trash/purge_all` |
| `trpurge` | 56 | trash.js | `/api/trash/purge`<br>`/api/trash/purge_all` |
| `trpurgeall` | 57 | trash.js | `/api/trash/purge_all` |
| `trpurgeallgo` | 60 | trash.js | `/api/trash/purge_all` |
| `trrefresh` | 62 | trash.js | none (browser only) |

### `trending.js` (8)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `trorder` | 31 | trending.js | `/api/trending/{}/${on`<br>`/api/trending/{}/comments`<br>`/api/trending/{}/comments/{}/delete`<br>`/api/trending/{}/unshare`<br>`/api/trending/{}/use` |
| `tropen` | 32 | trending.js | `/api/trending/{}/${on`<br>`/api/trending/{}/comments`<br>`/api/trending/{}/comments/{}/delete`<br>`/api/trending/{}/unshare`<br>`/api/trending/{}/use` |
| `trlike` | 33 | trending.js | `/api/trending/{}/${on`<br>`/api/trending/{}/comments`<br>`/api/trending/{}/comments/{}/delete`<br>`/api/trending/{}/unshare`<br>`/api/trending/{}/use` |
| `trcomment` | 35 | trending.js | `/api/trending/{}/${on`<br>`/api/trending/{}/comments`<br>`/api/trending/{}/comments/{}/delete`<br>`/api/trending/{}/unshare`<br>`/api/trending/{}/use` |
| `truncomment` | 37 | trending.js | `/api/trending/{}/${on`<br>`/api/trending/{}/comments/{}/delete`<br>`/api/trending/{}/unshare`<br>`/api/trending/{}/use` |
| `truse` | 38 | trending.js | `/api/trending/{}/${on`<br>`/api/trending/{}/unshare`<br>`/api/trending/{}/use` |
| `trunshare` | 42 | trending.js | `/api/trending/{}/${on`<br>`/api/trending/{}/unshare` |
| `trshare` | 43 | trending.js | `/api/trending/{}/${on` |

### `users.js` (3)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `usopen` | 64 | users.js | none (browser only) |
| `usall` | 65 | users.js | none (browser only) |
| `usfilter` | 66 | users.js | none (browser only) |

### `welcome.js` (7)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `wlclose` | 62 | welcome.js | none (browser only) |
| `wlnext` | 62 | welcome.js | none (browser only) |
| `wlprev` | 62 | welcome.js | none (browser only) |
| `wlgoto` | 63 | welcome.js | none (browser only) |
| `wlgo` | 64 | welcome.js | none (browser only) |
| `wlplay` | 65 | welcome.js | none (browser only) |
| `wlsound` | 66 | welcome.js | none (browser only) |
