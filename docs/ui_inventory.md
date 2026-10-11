# docs/ui_inventory.md — everything the browser sandbox can do (generated)

Generated from `console/*.js` on 2026-10-11 after the console feature split and theme/Home additions. Regenerate when actions move. The wiring is in `docs/architecture.md` §6; the redesign action map remains in `docs/redesign_plan.md` §4.

**446 actions** (447 definitions; `ggo` in studio-core.js is deliberately replaced by composer.js), in 34 scripts; **16 screens** (21 `RENDER` definitions); **157 named server routes**.

`tests/data/ui_baseline.json` and `tests/test_ui_inventory.py` prevent actions, screens or routes disappearing without a recorded rename or authorized retirement. The feature split changes no baseline entries.

Each action row names its source, line, scripts drawing its button and routes its code or helpers may call (two calls deep, excluding redraw helpers). `{}` represents an id. A button can also be invoked from code, a key or a form.

## Screens (`RENDER.<screen>`)

| screen | script |
|---|---|
| `animate` | animate.js |
| `settings` | auth.js |
| `agent` | chat-core.js |
| `chat` | chat.js |
| `create` | editor.js |
| `editor` | editor.js |
| `export` | editor.js |
| `effects` | effects.js |
| `history` | history.js |
| `home` | home.js |
| `library` | library.js |
| `generate` | live.js |
| `pack` | packs.js |
| `effects` | particles.js |
| `prepare` | prepare.js |
| `settings` | settings.js |
| `generate` | studio-core.js |
| `help` | support.js |
| `settings` | tickets.js |
| `settings` | trash.js |
| `users` | users.js |

## Server routes the page names

`/api`, `/api/ai`, `/api/ai/backend`, `/api/auth`, `/api/auth/credits`, `/api/auth/forgot`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`, `/api/auth/password`, `/api/auth/signup`, `/api/chat/*`, `/api/chat/agent`, `/api/chat/sessions`, `/api/chat/sessions/{}/delete`, `/api/chat/sessions/{}/messages`, `/api/chat/sessions/{}/settings`, `/api/collection`, `/api/cutout`, `/api/effects`, `/api/effects/{}/add`, `/api/effects/{}/estimate`, `/api/effects/{}/particles`, `/api/effects/{}/particles_estimate`, `/api/effects/{}/particles_pick`, `/api/effects/{}/plan`, `/api/effects/{}/suggest`, `/api/effects/{}/video`, `/api/faq`, `/api/faq/{}/{}`, `/api/generations`, `/api/generations/${+String(id).replace(/\D/g,`, `/api/generations/removed`, `/api/generations/{}/add`, `/api/generations/{}/allow`, `/api/generations/{}/animate`, `/api/generations/{}/drop`, `/api/generations/{}/edge`, `/api/generations/{}/edge_preview`, `/api/generations/{}/edit`, `/api/generations/{}/export-collection`, `/api/generations/{}/export.zip`, `/api/generations/{}/family`, `/api/generations/{}/join`, `/api/generations/{}/leave`, `/api/generations/{}/map`, `/api/generations/{}/pack`, `/api/generations/{}/particles`, `/api/generations/{}/pick`, `/api/generations/{}/pick_video`, `/api/generations/{}/quick_sheet`, `/api/generations/{}/recheck`, `/api/generations/{}/recut`, `/api/generations/{}/remove`, `/api/generations/{}/remove_video`, `/api/generations/{}/replace`, `/api/generations/{}/restore`, `/api/generations/{}/reveal`, `/api/generations/{}/sheet_preview`, `/api/generations/{}/studio_edit`, `/api/generations/{}/video_sheet/{}/video`, `/api/higgsfield`, `/api/higgsfield/history`, `/api/higgsfield/import`, `/api/history`, `/api/import`, `/api/imports/candidates`, `/api/inputs`, `/api/jobs`, `/api/jobs/{}/dismiss`, `/api/jobs/{}/retry`, `/api/jobs/{}/retry_estimate`, `/api/jobs/{}/{}`, `/api/library`, `/api/live/cost`, `/api/live/ref`, `/api/live/sheet`, `/api/live/video`, `/api/llm/models`, `/api/models`, `/api/notifications`, `/api/packs`, `/api/packs/{}/delete`, `/api/packs/{}/export-collection`, `/api/packs/{}/export.zip`, `/api/packs/{}/merge`, `/api/packs/{}/particles`, `/api/packs/{}/render`, `/api/packs/{}/restore`, `/api/packs/{}/stickers/{}`, `/api/packs/{}/stickers/{}/animate`, `/api/packs/{}/stickers/{}/delete`, `/api/packs/{}/stickers/{}/move`, `/api/packs/{}/stickers/{}/particle-preview`, `/api/packs/{}/stickers/{}/particles`, `/api/packs/{}/stickers/{}/replace`, `/api/packs/{}/telegram`, `/api/packs/{}/telegram.zip`, `/api/particles`, `/api/particles/deleted`, `/api/particles/{}`, `/api/particles/{}/add`, `/api/particles/{}/delete`, `/api/particles/{}/duplicate`, `/api/particles/{}/link`, `/api/particles/{}/more`, `/api/particles/{}/preview`, `/api/particles/{}/render`, `/api/particles/{}/restore`, `/api/particles/{}/save-as-new`, `/api/particles/{}/unlink`, `/api/people`, `/api/plan`, `/api/plan/more`, `/api/plan/next`, `/api/prefs`, `/api/prepared/match`, `/api/prepared/setting`, `/api/projects`, `/api/projects/from_sticker`, `/api/projects/{}/delete`, `/api/projects/{}/render`, `/api/stickers/delete`, `/api/stickers/move`, `/api/support/ask`, `/api/support/conversations`, `/api/support/conversations/{}/{}`, `/api/support/queue`, `/api/support/tickets`, `/api/tasks`, `/api/telegram`, `/api/telegram/config`, `/api/telegram/disconnect`, `/api/tickets`, `/api/tickets/{}/answer`, `/api/tickets/{}/reply`, `/api/tickets/{}/resolve`, `/api/tickets/{}/status`, `/api/trash`, `/api/trash/purge`, `/api/trash/purge_all`, `/api/trash/purges`, `/api/trending`, `/api/trending/{}/${on`, `/api/trending/{}/comments`, `/api/trending/{}/comments/{}/delete`, `/api/trending/{}/file/{}`, `/api/trending/{}/unshare`, `/api/trending/{}/use`, `/api/usage`, `/api/users`, `/api/users/me`, `/api/users/overview`, `/api/watch`, `/api/watch/purge`, `/api/watch/remove`, `/api/watch/restore`

## Actions by script

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

### `app.js` (11)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `dlgx` | 123 | app.js, auth.js, editor.js, home.js, imports.js, library.js, live.js, packs.js, particles.js, prepare.js, studio-animate.js, studio-prompt.js, support.js, telegram.js, tickets.js, trash.js, trending.js | none (browser only) |
| `askok` | 140 | app.js | none (browser only) |
| `copyid` | 147 | chat-cards.js, studio-panel.js | none (browser only) |
| `cfok` | 165 | app.js | none (browser only) |
| `pk` | 179 | app.js | none (browser only) |
| `pknew` | 184 | app.js | `/api/packs` |
| `c2tog` | 298 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `nav` | 300 | animate.js, app.js, auth.js, chat.js, editor.js, home.js, library.js, packs.js, prepare.js, tickets.js | none (browser only) |
| `rme` | 305 | app.js | none (browser only) |
| `thmtoggle` | 314 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `rtrash` | 346 | app.js | none (browser only) |

### `auth.js` (12)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `aumode` | 57 | auth.js | none (browser only) |
| `ausignin` | 58 | auth.js | `/api/auth/login` |
| `ausignup` | 59 | auth.js | `/api/auth/me`<br>`/api/auth/signup` |
| `auforgot` | 60 | auth.js | `/api/auth/forgot` |
| `auchange` | 61 | auth.js | `/api/auth/me`<br>`/api/auth/password` |
| `aukeep` | 64 | auth.js | none (browser only) |
| `aulogout` | 65 | app.js, auth.js | `/api/auth/logout` |
| `aucreditask` | 66 | auth.js, composer.js | `/api/auth/credits` |
| `auadd` | 70 | auth.js | `/api/people` |
| `aupeople` | 72 | auth.js | `/api/people` |
| `aucredits` | 75 | auth.js | `/api/people` |
| `auignore` | 76 | auth.js | `/api/people` |

### `chat-core.js` (18)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `agcar` | 427 | chat-cards.js | none (browser only) |
| `agtile` | 431 | chat-cards.js | none (browser only) |
| `agsel` | 440 | chat-core.js | none (browser only) |
| `agchip` | 455 | chat-cards.js, chat-core.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/messages` |
| `agfill` | 456 | chat-cards.js | none (browser only) |
| `agedit` | 463 | chat-cards.js | `/api/generations`<br>`/api/generations/{}/studio_edit` |
| `agsetting` | 466 | chat-cards.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agaction` | 474 | chat-cards.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/messages` |
| `agcut` | 490 | chat-cards.js | `/api/chat/sessions`<br>`/api/generations/{}/recut` |
| `aganimal` | 497 | chat-cards.js | `/api/chat/sessions`<br>`/api/generations/{}/animate` |
| `agretry` | 506 | chat-cards.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/messages` |
| `agtrace` | 507 | chat-cards.js | none (browser only) |
| `agstep` | 513 | chat-cards.js | none (browser only) |
| `agstudio` | 519 | chat-cards.js | none (browser only) |
| `agallow` | 527 | chat-cards.js | `/api/chat/sessions`<br>`/api/generations/{}/allow` |
| `agallowall` | 541 | chat-cards.js, chat-core.js | `/api/chat/sessions`<br>`/api/generations/{}/allow` |
| `agnew` | 588 | chat-core.js | none (browser only) |
| `agopen` | 603 | chat-core.js | none (browser only) |

### `chat-stage.js` (13)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `agdel` | 4 | chat-core.js | `/api/chat/sessions/{}/delete` |
| `agset` | 17 | chat-core.js | `/api/models` |
| `agengine` | 29 | chat-core.js | none (browser only) |
| `agsetgrid` | 40 | (no `data-act` button: called from code, a key, or a form) | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `aggridtoggle` | 41 | chat-stage.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agstage` | 89 | agent.js | none (browser only) |
| `agsetact` | 97 | chat-stage.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agstagepick` | 98 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings`<br>`/api/prefs` |
| `agstyle` | 176 | chat-stage.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agstyles` | 183 | chat-stage.js | none (browser only) |
| `agsetask` | 187 | chat-stage.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agbe` | 188 | chat-stage.js | `/api/ai`<br>`/api/ai/backend` |
| `agcr` | 300 | chat-stage.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |

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

### `composer.js` (13)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `cpmenu` | 65 | composer.js | none (browser only) |
| `cpadd` | 76 | composer.js | none (browser only) |
| `cprefx` | 77 | composer.js | `/api/live/ref` |
| `cppart` | 89 | composer.js | none (browser only) |
| `cpactions` | 112 | composer.js | none (browser only) |
| `cploop` | 113 | composer.js | none (browser only) |
| `cpai` | 114 | composer.js | `/api/ai` |
| `cpstroke` | 115 | composer.js | none (browser only) |
| `cpstrokeset` | 116 | composer.js | none (browser only) |
| `cpstyles` | 123 | composer.js | none (browser only) |
| `cpstylepick` | 124 | composer.js | none (browser only) |
| `ggo` | 131 | (no `data-act` button: called from code, a key, or a form) | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video`<br>`/api/prepared/match` |
| `gnewlive` | 144 | studio-core.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video` |

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

### `history.js` (5)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `hsopen` | 25 | history.js | none (browser only) |
| `hgen` | 26 | history.js | `/api/generations` |
| `hremove` | 28 | history.js | `/api/watch`<br>`/api/watch/remove` |
| `hrestore` | 32 | history.js | `/api/watch`<br>`/api/watch/restore` |
| `hpurge` | 33 | history.js | `/api/watch`<br>`/api/watch/purge` |

### `home.js` (5)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `hmfilter` | 72 | home.js | none (browser only) |
| `hmai` | 75 | home.js | none (browser only) |
| `hmfilm` | 77 | home.js | none (browser only) |
| `hmonboarding` | 78 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `home` | 80 | app.js | none (browser only) |

### `imports.js` (9)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `impopen` | 28 | imports.js | `/api/higgsfield/import`<br>`/api/import`<br>`/api/imports/candidates` |
| `impackopen` | 30 | home.js, library.js | none (browser only) |
| `impupload` | 31 | imports.js | `/api/imports/candidates` |
| `impchoose` | 36 | imports.js | none (browser only) |
| `impnew` | 37 | imports.js | none (browser only) |
| `impretry` | 38 | imports.js | `/api/higgsfield/history`<br>`/api/higgsfield/import`<br>`/api/import`<br>`/api/imports/candidates` |
| `imphistory` | 39 | imports.js | `/api/higgsfield/history`<br>`/api/higgsfield/import`<br>`/api/import`<br>`/api/imports/candidates` |
| `imphf` | 40 | imports.js | none (browser only) |
| `impbatch` | 44 | imports.js | `/api/import` |

### `job-recovery.js` (4)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `jrrefresh` | 30 | (no `data-act` button: called from code, a key, or a form) | `/api/generations`<br>`/api/jobs`<br>`/api/jobs/{}/dismiss` |
| `jrcheck` | 32 | (no `data-act` button: called from code, a key, or a form) | `/api/generations`<br>`/api/jobs`<br>`/api/jobs/{}/{}` |
| `jrcontinue` | 33 | (no `data-act` button: called from code, a key, or a form) | `/api/generations`<br>`/api/jobs`<br>`/api/jobs/{}/{}` |
| `jrretry` | 34 | (no `data-act` button: called from code, a key, or a form) | `/api/jobs`<br>`/api/jobs/{}/dismiss`<br>`/api/jobs/{}/retry`<br>`/api/jobs/{}/retry_estimate` |

### `library.js` (12)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `lsel` | 57 | library.js, packs.js | none (browser only) |
| `lselall` | 64 | library.js | none (browser only) |
| `lselnone` | 72 | library.js | none (browser only) |
| `lselmove` | 97 | library.js | `/api/stickers/move` |
| `lseldel` | 101 | library.js | `/api/stickers/delete` |
| `libtab` | 312 | library.js | none (browser only) |
| `pkmerge` | 317 | app.js | `/api/packs/{}/merge` |
| `pkgrp` | 335 | app.js | none (browser only) |
| `seeall` | 342 | library.js | none (browser only) |
| `openpack` | 405 | app.js, home.js, library.js | none (browser only) |
| `newpack` | 409 | app.js | none (browser only) |
| `newpackname` | 416 | library.js | `/api/packs` |

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
| `lcopen` | 123 | library.js | none (browser only) |
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
| `agpscope` | 379 | chat-cards.js | `/api/particles` |
| `agpopen` | 380 | chat-cards.js | `/api/particles`<br>`/api/particles/{}/preview` |
| `agpapprove` | 381 | chat-cards.js | `/api/generations` |
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

### `settings.js` (3)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `setgo` | 41 | settings.js | none (browser only) |
| `prepset` | 46 | settings.js | `/api/prepared/setting` |
| `thmset` | 53 | settings.js, theme.js | none (browser only) |

### `sheet-recovery.js` (1)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `ssallow` | 16 | sheet-recovery.js | `/api/chat/sessions`<br>`/api/generations/{}/allow` |

### `studio-animate.js` (13)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `ganmo` | 30 | studio-animate.js | none (browser only) |
| `ganimate` | 41 | studio-core.js | `/api/generations/{}/animate`<br>`/api/prefs` |
| `gadd` | 79 | particles.js, studio-core.js | none (browser only) |
| `pwgo` | 181 | studio-animate.js | `/api/generations/{}/add`<br>`/api/packs` |
| `gopenpack` | 243 | studio-core.js | none (browser only) |
| `gvideo` | 249 | studio-animate.js, studio-core.js | `/api/generations/{}/quick_sheet` |
| `gpickvideo` | 318 | studio-animate.js | none (browser only) |
| `gsheetapprove` | 323 | studio-animate.js | `/api/generations/{}/quick_sheet` |
| `gvclose` | 331 | studio-animate.js | none (browser only) |
| `gcopyprompt` | 336 | studio-animate.js | none (browser only) |
| `openstudio` | 375 | particles.js | `/api/generations` |
| `lcstudioedit` | 387 | packs.js | `/api/generations`<br>`/api/generations/{}/studio_edit` |
| `lcopenstudio` | 393 | packs.js | none (browser only) |

### `studio-core.js` (13)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `goutline` | 295 | studio-core.js | none (browser only) |
| `ggo` | 353 | (no `data-act` button: called from code, a key, or a form) | `/api/generations`<br>`/api/particles`<br>`/api/particles/{}/more` |
| `gmore` | 372 | (no `data-act` button: called from code, a key, or a form) | `/api/generations` |
| `gnext` | 393 | projmap.js, studio-core.js | `/api/live/cost`<br>`/api/plan/next` |
| `gbdrop` | 430 | studio-core.js | none (browser only) |
| `ginc` | 439 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `ggen` | 475 | projmap.js, studio-core.js | none (browser only) |
| `gmain` | 486 | projmap.js, studio-core.js | `/api/generations/{}/pick` |
| `gdel` | 497 | projmap.js, studio-core.js | `/api/generations/{}/family`<br>`/api/generations/{}/particles`<br>`/api/generations/{}/remove`<br>`/api/history` |
| `gcutany` | 676 | studio-core.js | `/api/generations/{}/recut` |
| `gretrysheet` | 684 | studio-core.js | `/api/generations` |
| `greqgo` | 692 | studio-core.js | `/api/generations` |
| `gopenfolder` | 757 | studio-core.js | `/api/generations/{}/reveal` |

### `studio-panel.js` (6)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `gmall` | 96 | studio-panel.js | none (browser only) |
| `gmtab` | 101 | studio-panel.js | none (browser only) |
| `gopen` | 106 | studio-tiles.js | none (browser only) |
| `gmclose` | 112 | studio-panel.js | none (browser only) |
| `gstep` | 118 | studio-panel.js | none (browser only) |
| `gedit` | 126 | studio-panel.js | `/api/generations`<br>`/api/generations/{}/studio_edit` |

### `studio-prompt.js` (23)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `pgresheet` | 87 | studio-prompt.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video` |
| `pgredo` | 117 | studio-prompt.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video`<br>`/api/prefs` |
| `pgreset` | 163 | studio-animate.js, studio-prompt.js, studio-sheet.js | none (browser only) |
| `gdnb` | 246 | studio-prompt.js | none (browser only) |
| `gdtab` | 288 | composer.js, studio-prompt.js | none (browser only) |
| `gddiscard` | 299 | studio-prompt.js | none (browser only) |
| `gdpriceretry` | 306 | studio-prompt.js | `/api/live/cost` |
| `gprompt` | 322 | composer.js, studio-core.js | `/api/particles`<br>`/api/particles/{}/more`<br>`/api/plan` |
| `gpromptfree` | 324 | studio-prompt.js | `/api/plan` |
| `gdsheet` | 404 | studio-prompt.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video`<br>`/api/plan/more` |
| `pgsheet` | 495 | projmap.js, studio-prompt.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video` |
| `pgvideo` | 512 | studio-prompt.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video`<br>`/api/prefs` |
| `ggroup` | 529 | projmap.js, studio-core.js | none (browser only) |
| `ggroupgo` | 539 | studio-prompt.js | `/api/generations/{}/join`<br>`/api/generations/{}/particles`<br>`/api/history` |
| `grm` | 544 | studio-core.js | `/api/generations/removed`<br>`/api/generations/{}/particles`<br>`/api/generations/{}/remove`<br>`/api/history` |
| `gstagego` | 588 | studio-prompt.js | `/api/prefs` |
| `gscreen` | 598 | studio-core.js | none (browser only) |
| `gvmode` | 605 | studio-core.js | none (browser only) |
| `gtab` | 612 | particles.js, projmap.js, studio-core.js | none (browser only) |
| `ghiggs` | 620 | studio-core.js | `/api/plan` |
| `hcopy` | 638 | studio-prompt.js | none (browser only) |
| `hgenop` | 647 | studio-prompt.js | `/api/jobs` |
| `hreserve` | 675 | studio-prompt.js | `/api/tasks` |

### `studio-sheet.js` (10)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `gapick` | 189 | projmap.js, studio-sheet.js | `/api/generations/{}/pick_video` |
| `garm` | 201 | projmap.js, studio-sheet.js | `/api/generations/{}/remove_video` |
| `gvsheet` | 231 | studio-sheet.js | none (browser only) |
| `gaclose` | 236 | studio-sheet.js | none (browser only) |
| `gptog` | 379 | studio-sheet.js | none (browser only) |
| `gshk` | 386 | studio-sheet.js | none (browser only) |
| `gsheet` | 395 | studio-sheet.js | none (browser only) |
| `gsview` | 439 | studio-sheet.js | none (browser only) |
| `gstog` | 444 | studio-sheet.js | none (browser only) |
| `gsclose` | 449 | studio-sheet.js | none (browser only) |

### `studio-tiles.js` (5)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `ganimslice` | 279 | studio-tiles.js | `/api/generations/{}/animate` |
| `greplace` | 295 | studio-panel.js | none (browser only) |
| `grepundo` | 330 | studio-panel.js | `/api/generations/{}/replace` |
| `gcell` | 413 | studio-tiles.js | `/api/generations/{}/allow`<br>`/api/generations/{}/drop` |
| `gallowall` | 437 | studio-tiles.js | `/api/generations/{}/allow` |

### `support.js` (26)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `sutab` | 101 | support.js | none (browser only) |
| `sunew` | 102 | support.js | none (browser only) |
| `suopen` | 103 | support.js | none (browser only) |
| `sunote` | 104 | support.js | none (browser only) |
| `sushot` | 105 | support.js | none (browser only) |
| `sushotx` | 106 | support.js | none (browser only) |
| `suask` | 107 | support.js | `/api/support/ask`<br>`/api/support/conversations` |
| `sureq` | 113 | support.js | `/api/support/conversations`<br>`/api/support/conversations/{}/{}` |
| `supriv` | 114 | support.js | none (browser only) |
| `sucopy` | 115 | support.js | none (browser only) |
| `suforget` | 116 | support.js | `/api/support/conversations`<br>`/api/support/conversations/{}/{}` |
| `sugo` | 117 | support.js | `/api/generations` |
| `susolved` | 119 | support.js | `/api/support/conversations`<br>`/api/support/conversations/{}/{}` |
| `suunsolved` | 120 | support.js | `/api/support/conversations`<br>`/api/support/conversations/{}/{}` |
| `suesc` | 121 | support.js | `/api/support/conversations`<br>`/api/support/conversations/{}/{}` |
| `sureopen` | 122 | support.js | `/api/support/conversations`<br>`/api/support/conversations/{}/{}` |
| `sucite` | 123 | support.js | `/api/faq` |
| `suq` | 125 | support.js | none (browser only) |
| `sureply` | 127 | support.js | `/api/support/queue`<br>`/api/support/tickets`<br>`/api/tickets/{}/reply` |
| `suresolve` | 129 | support.js | `/api/support/queue`<br>`/api/support/tickets`<br>`/api/tickets/{}/resolve` |
| `sufaq` | 131 | support.js | none (browser only) |
| `sufall` | 132 | support.js | `/api/faq` |
| `sufsave` | 134 | support.js | `/api/faq`<br>`/api/faq/{}/{}` |
| `sufpub` | 135 | support.js | `/api/faq`<br>`/api/faq/{}/{}` |
| `sufdisc` | 136 | support.js | `/api/faq`<br>`/api/faq/{}/{}` |
| `sufarch` | 137 | support.js | `/api/faq`<br>`/api/faq/{}/{}` |

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
| `tkopen` | 36 | tickets.js | `/api/tickets` |
| `tkfilter` | 37 | tickets.js | `/api/tickets` |
| `tkans` | 41 | tickets.js | `/api/tickets`<br>`/api/tickets/{}/answer` |
| `tkother` | 42 | tickets.js | `/api/tickets`<br>`/api/tickets/{}/answer` |
| `tkstatus` | 43 | tickets.js | `/api/tickets`<br>`/api/tickets/{}/status` |
| `tkreport` | 44 | chat-core.js, packs.js, projmap.js, studio-core.js, studio-sheet.js, tickets.js | none (browser only) |
| `tksend` | 45 | tickets.js | `/api/tickets` |
| `tkrefresh` | 49 | tickets.js | `/api/tickets` |

### `trash.js` (5)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `trrestore` | 54 | trash.js | `/api/generations/${+String(id).replace(/\D/g,`<br>`/api/packs/{}/restore`<br>`/api/trash` |
| `trpurge` | 56 | trash.js | `/api/trash`<br>`/api/trash/purge`<br>`/api/trash/purges` |
| `trpurgeall` | 57 | trash.js | none (browser only) |
| `trpurgeallgo` | 60 | trash.js | `/api/trash`<br>`/api/trash/purge`<br>`/api/trash/purge_all`<br>`/api/trash/purges` |
| `trrefresh` | 62 | trash.js | `/api/trash` |

### `trending.js` (8)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `trorder` | 31 | trending.js | `/api/trending` |
| `tropen` | 32 | trending.js | `/api/trending` |
| `trlike` | 33 | trending.js | `/api/trending`<br>`/api/trending/{}/${on` |
| `trcomment` | 35 | trending.js | `/api/trending`<br>`/api/trending/{}/comments` |
| `truncomment` | 37 | trending.js | `/api/trending`<br>`/api/trending/{}/comments/{}/delete` |
| `truse` | 38 | trending.js | `/api/trending/{}/use` |
| `trunshare` | 42 | trending.js | `/api/trending`<br>`/api/trending/{}/unshare` |
| `trshare` | 43 | trending.js | `/api/trending`<br>`/api/trending/{}/${on` |

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
