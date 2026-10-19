# Browser action inventory — generated 2026-10-19

Source `64d8b8a4` on `redesign-ui-ux`; regenerated from current `console/*.js`.
**514 action names / 515 definitions**, in 36 action-bearing scripts
(40 first-party scripts total); **17 screen names / 22 renderer assignments**;
**183 named browser API route patterns**. Patterns are not a count of server endpoints.
`ggo` is intentionally replaced. Renderer extensions are not separate screens.

The baseline still guards disappearance/retirement. A missing drawn button can
be a programmatic/form/key action, not dead code. Route attribution follows
helpers two calls deep and excludes redraw helpers; it is static reference.

## Screens

| Screen | Script |
|---|---|
| `animate` | `animate.js` |
| `settings` | `auth.js` |
| `agent` | `chat-core.js` |
| `chat` | `chat.js` |
| `create` | `editor.js` |
| `editor` | `editor.js` |
| `export` | `editor.js` |
| `effects` | `effects.js` |
| `history` | `history.js` |
| `home` | `home.js` |
| `library` | `library.js` |
| `generate` | `live.js` |
| `pack` | `packs.js` |
| `effects` | `particles.js` |
| `prepare` | `prepare.js` |
| `reactions` | `reactions.js` |
| `settings` | `settings.js` |
| `generate` | `studio-core.js` |
| `help` | `support.js` |
| `settings` | `tickets.js` |
| `settings` | `trash.js` |
| `users` | `users.js` |

## Actions

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

### `app.js` (12)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `dlgx` | 141 | app.js, auth.js, editor.js, home.js, imports.js, library.js, live.js, packs.js, particles.js, prepare.js, studio-animate.js, studio-prompt.js, support.js, telegram.js, tickets.js, trash.js, trending.js | none (browser only) |
| `askok` | 158 | app.js | none (browser only) |
| `copyid` | 165 | chat-cards.js, studio-panel.js | none (browser only) |
| `cfok` | 183 | app.js | none (browser only) |
| `pk` | 197 | app.js | none (browser only) |
| `pknew` | 202 | app.js | `/api/packs` |
| `c2tog` | 318 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `nav` | 320 | animate.js, app.js, auth.js, chat.js, editor.js, home.js, library.js, packs.js, prepare.js, tickets.js | none (browser only) |
| `railcreate` | 328 | home.js | none (browser only) |
| `rme` | 343 | app.js | none (browser only) |
| `thmtoggle` | 352 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `rtrash` | 397 | app.js | none (browser only) |

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
| `agstage` | 98 | agent.js | none (browser only) |
| `agsetact` | 106 | chat-stage.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agstagepick` | 107 | agent.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings`<br>`/api/prefs` |
| `agstyle` | 185 | chat-stage.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agstyles` | 192 | chat-stage.js | none (browser only) |
| `agsetask` | 196 | chat-stage.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |
| `agbe` | 197 | chat-stage.js | `/api/ai`<br>`/api/ai/backend` |
| `agcr` | 313 | chat-stage.js | `/api/chat/sessions`<br>`/api/chat/sessions/{}/settings` |

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

### `composer.js` (14)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `cpmenu` | 65 | composer.js | none (browser only) |
| `cpadd` | 76 | composer.js | none (browser only) |
| `cprefx` | 77 | composer.js | `/api/live/ref` |
| `cppart` | 89 | composer.js | none (browser only) |
| `cpactions` | 113 | composer.js | none (browser only) |
| `cpgrid` | 114 | composer.js | none (browser only) |
| `cploop` | 115 | composer.js | none (browser only) |
| `cpai` | 116 | composer.js | `/api/ai` |
| `cpstroke` | 117 | composer.js | none (browser only) |
| `cpstrokeset` | 118 | composer.js | none (browser only) |
| `cpstyles` | 125 | composer.js | none (browser only) |
| `cpstylepick` | 126 | composer.js | none (browser only) |
| `ggo` | 133 | (no `data-act` button: called from code, a key, or a form) | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video`<br>`/api/prepared/match` |
| `gnewlive` | 146 | studio-core.js | `/api/jobs`<br>`/api/live/cost`<br>`/api/live/sheet`<br>`/api/live/video` |

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

### `effects.js` (22)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `fxback` | 48 | effects.js | none (browser only) |
| `fxdgrid` | 151 | effects.js | none (browser only) |
| `fxdretry` | 152 | effects.js | `/api/effects/{}/suggest` |
| `fxdchip` | 153 | effects.js | `/api/effects/{}/particles_estimate` |
| `fxdadd` | 157 | effects.js | `/api/effects/{}/particles_estimate` |
| `fxddraw` | 159 | effects.js, particles.js | `/api/effects`<br>`/api/effects/{}/particles`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `fxdredo` | 162 | effects.js | none (browser only) |
| `fxdcancel` | 163 | effects.js | none (browser only) |
| `fxdchange` | 164 | effects.js | none (browser only) |
| `fxdcell` | 165 | effects.js | none (browser only) |
| `fxdall` | 166 | effects.js | none (browser only) |
| `fxduse` | 167 | effects.js | `/api/effects`<br>`/api/effects/{}/particles_pick`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `fxprice` | 204 | effects.js, particles.js | `/api/effects/{}/estimate` |
| `fxdelpiece` | 208 | effects.js | `/api/effects`<br>`/api/effects/{}/plan`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `fxaddpiece` | 210 | effects.js | `/api/effects/{}/plan` |
| `fxvideo` | 211 | effects.js, particles.js | `/api/effects`<br>`/api/effects/{}/video`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `fxpick` | 220 | effects.js | none (browser only) |
| `fxpickall` | 221 | effects.js | none (browser only) |
| `fxadd` | 222 | effects.js | `/api/effects`<br>`/api/effects/{}/add`<br>`/api/generations`<br>`/api/generations/{}/particles`<br>`/api/jobs`<br>`/api/particles` |
| `fxopenset` | 240 | effects.js | `/api/particles/{}/preview` |
| `fxuseset` | 248 | effects.js | `/api/particles` |
| `psusesave` | 249 | (no `data-act` button: called from code, a key, or a form) | `/api/particles` |

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

### `imports.js` (19)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `newphoto` | 15 | app.js | none (browser only) |
| `newphotosticker` | 16 | imports.js | none (browser only) |
| `impemojis` | 18 | imports.js | none (browser only) |
| `newvideo` | 19 | app.js | none (browser only) |
| `impopen` | 35 | imports.js | `/api/higgsfield/import`<br>`/api/import`<br>`/api/imports/candidates` |
| `impackopen` | 37 | home.js, library.js | none (browser only) |
| `impupload` | 38 | imports.js | `/api/imports/candidates` |
| `impchoose` | 43 | imports.js | none (browser only) |
| `impexisting` | 44 | imports.js | none (browser only) |
| `impreimport` | 45 | imports.js | none (browser only) |
| `impnew` | 46 | imports.js | none (browser only) |
| `impretry` | 47 | imports.js | `/api/higgsfield/history`<br>`/api/higgsfield/import`<br>`/api/import`<br>`/api/imports/candidates` |
| `imphistory` | 48 | imports.js | `/api/higgsfield/history`<br>`/api/higgsfield/import`<br>`/api/import`<br>`/api/imports/candidates` |
| `imphf` | 49 | imports.js | none (browser only) |
| `impbatch` | 69 | imports.js | none (browser only) |
| `impbatchgo` | 72 | imports.js | `/api/import` |
| `impdetected` | 73 | imports.js | `/api/import` |
| `impgrid` | 74 | imports.js | `/api/import` |
| `impagain` | 75 | imports.js | `/api/import` |

### `job-recovery.js` (4)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `jrrefresh` | 30 | (no `data-act` button: called from code, a key, or a form) | `/api/generations`<br>`/api/jobs`<br>`/api/jobs/{}/dismiss` |
| `jrcheck` | 32 | (no `data-act` button: called from code, a key, or a form) | `/api/generations`<br>`/api/jobs`<br>`/api/jobs/{}/{}` |
| `jrcontinue` | 33 | (no `data-act` button: called from code, a key, or a form) | `/api/generations`<br>`/api/jobs`<br>`/api/jobs/{}/{}` |
| `jrretry` | 34 | (no `data-act` button: called from code, a key, or a form) | `/api/jobs`<br>`/api/jobs/{}/dismiss`<br>`/api/jobs/{}/retry`<br>`/api/jobs/{}/retry_estimate` |

### `library.js` (13)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `lsel` | 57 | library.js, packs.js | none (browser only) |
| `lselall` | 64 | library.js | none (browser only) |
| `lselnone` | 72 | library.js | none (browser only) |
| `lselmove` | 97 | library.js | `/api/stickers/move` |
| `lseldel` | 101 | library.js | `/api/stickers/delete` |
| `libtab` | 312 | library.js | none (browser only) |
| `pkmerge` | 317 | app.js | `/api/packs/{}/merge` |
| `pkunnest` | 335 | app.js | `/api/packs/{}` |
| `pkgrp` | 345 | app.js | none (browser only) |
| `seeall` | 352 | library.js | none (browser only) |
| `openpack` | 423 | app.js, home.js, library.js | none (browser only) |
| `newpack` | 427 | app.js | none (browser only) |
| `newpackname` | 434 | library.js | `/api/packs` |

### `live.js` (20)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `lusage` | 29 | composer.js | `/api/higgsfield`<br>`/api/usage` |
| `lstyle` | 51 | live.js | none (browser only) |
| `lmodels` | 55 | composer.js, live.js | none (browser only) |
| `lmpick` | 68 | live.js | none (browser only) |
| `lmdone` | 69 | live.js | none (browser only) |
| `qtoggle` | 160 | live.js | none (browser only) |
| `qretry` | 165 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `qcopy` | 166 | live.js | none (browser only) |
| `ljdismiss` | 167 | live.js | `/api/jobs/{}/dismiss` |
| `egapply` | 256 | live.js | `/api/generations/{}/edge` |
| `egundo` | 260 | live.js | `/api/generations/{}/edge` |
| `vlmyes` | 295 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `hunpack` | 323 | live.js, projmap.js | `/api/generations/{}/pack`<br>`/api/generations/{}/particles`<br>`/api/history` |
| `hopenpack` | 324 | live.js | `/api/generations/{}/particles` |
| `hleave` | 328 | projmap.js | `/api/generations/{}/leave`<br>`/api/generations/{}/particles`<br>`/api/history` |
| `gpurge` | 353 | live.js | `/api/generations/removed`<br>`/api/trash/purge`<br>`/api/trash/purges` |
| `gpurgeall` | 357 | live.js | `/api/trash` |
| `gpurgeallgo` | 361 | live.js | `/api/generations/removed`<br>`/api/trash/purge_all`<br>`/api/trash/purges` |
| `grestore` | 363 | live.js | `/api/generations/removed`<br>`/api/generations/{}/particles`<br>`/api/generations/{}/restore`<br>`/api/history` |
| `hopen` | 374 | composer.js, live.js | `/api/generations/{}/particles`<br>`/api/particles` |

### `lottiestyle.js` (11)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `rxstyle` | 121 | lottiestyle.js | none (browser only) |
| `lspick` | 124 | lottiestyle.js | `/api/particles/lottie-reactions/{}/preview` |
| `lstg` | 125 | lottiestyle.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview`<br>`/api/particles/lottie-reactions/{}/preview` |
| `lsmode` | 126 | lottiestyle.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview`<br>`/api/particles/lottie-reactions/{}/preview` |
| `lsclose` | 127 | lottiestyle.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview` |
| `lspreset` | 128 | lottiestyle.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview`<br>`/api/particles/lottie-reactions/{}/preview` |
| `lsseed` | 129 | lottiestyle.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview`<br>`/api/particles/lottie-reactions/{}/preview` |
| `lsreset` | 132 | lottiestyle.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview`<br>`/api/particles/lottie-reactions/{}/preview` |
| `lssave` | 133 | lottiestyle.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview`<br>`/api/particles/lottie-reactions/{}` |
| `lsdl` | 137 | lottiestyle.js | none (browser only) |
| `lszip` | 139 | lottiestyle.js | `/api/particles/lottie-reactions.zip` |

### `packs.js` (42)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `rtans` | 53 | packs.js | none (browser only) |
| `pkzip` | 56 | packs.js | `/api/packs/{}/export.zip`<br>`/api/packs/{}/short` |
| `colopen` | 60 | packs.js | `/api/collection`<br>`/api/packs/{}/short` |
| `colsend` | 69 | packs.js | `/api/collection/exports`<br>`/api/generations/{}/export-collection`<br>`/api/packs/{}/export-collection` |
| `libpackstudio` | 96 | library.js | `/api/generations` |
| `pkstudio` | 97 | packs.js | `/api/generations` |
| `pkgstudio` | 98 | packs.js | `/api/generations` |
| `pkgdel` | 99 | packs.js | `/api/stickers/delete` |
| `pkadd` | 104 | packs.js | none (browser only) |
| `pkrename` | 105 | packs.js | `/api/packs` |
| `pkdel` | 110 | packs.js | `/api/packs/{}/delete` |
| `stanim` | 111 | packs.js | none (browser only) |
| `stcover` | 112 | packs.js | `/api/packs` |
| `stdel` | 113 | packs.js | `/api/packs/{}/stickers/{}/delete` |
| `stedit` | 114 | packs.js | `/api/generations`<br>`/api/generations/{}/studio_edit`<br>`/api/projects/from_sticker` |
| `stview` | 116 | packs.js | none (browser only) |
| `stname` | 117 | packs.js | none (browser only) |
| `strep` | 122 | packs.js | `/api/packs/{}/stickers/{}/replace` |
| `strepone` | 131 | packs.js | `/api/packs/{}/stickers/{}/replace` |
| `strepall` | 133 | packs.js | `/api/packs/{}/stickers/{}/replace` |
| `strepundo` | 135 | packs.js | `/api/packs/{}/stickers/{}/replace` |
| `stsave` | 136 | packs.js | `/api/packs/{}/stickers/{}` |
| `pkpreview` | 137 | packs.js | none (browser only) |
| `pvbg` | 140 | packs.js | none (browser only) |
| `lcsend` | 187 | packs.js | none (browser only) |
| `lcopen` | 188 | library.js | none (browser only) |
| `lcclose` | 188 | packs.js | none (browser only) |
| `lcprev` | 188 | packs.js | none (browser only) |
| `lcnext` | 188 | packs.js | none (browser only) |
| `lcgo` | 189 | packs.js | none (browser only) |
| `lcbg` | 189 | packs.js | none (browser only) |
| `lcpack` | 190 | packs.js | none (browser only) |
| `lcedit` | 191 | packs.js | `/api/projects/from_sticker` |
| `lctimeline` | 192 | packs.js | none (browser only) |
| `lcmove` | 193 | packs.js | `/api/packs/{}/stickers/{}/move` |
| `ptmake` | 250 | packs.js | none (browser only) |
| `ptrunsim` | 251 | packs.js | `/api/effects`<br>`/api/effects/{}/estimate`<br>`/api/effects/{}/particles_estimate`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `ptopen` | 252 | packs.js | none (browser only) |
| `ptsaved` | 253 | packs.js | none (browser only) |
| `ptadd` | 254 | packs.js | `/api/effects/{}/add`<br>`/api/generations/{}/particles`<br>`/api/packs/{}/stickers/{}/particles` |
| `psshow` | 291 | packs.js | `/api/particles`<br>`/api/particles/{}/preview` |
| `psscope` | 294 | packs.js | `/api/packs/{}/reactions`<br>`/api/particles/emoji-motions` |

### `particles.js` (65)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `spcontinue` | 30 | particles.js | `/api/effects`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles` |
| `spscope` | 31 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `spapprove` | 33 | particles.js | none (browser only) |
| `sppack` | 63 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `spkind` | 64 | particles.js | none (browser only) |
| `spgrid` | 65 | particles.js | none (browser only) |
| `spst` | 66 | particles.js | none (browser only) |
| `spall` | 68 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `spstart` | 70 | particles.js | `/api/effects`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles`<br>`/api/particles/{}/preview` |
| `spnovlm` | 71 | (no `data-act` button: called from code, a key, or a form) | `/api/effects`<br>`/api/generations`<br>`/api/jobs`<br>`/api/particles`<br>`/api/particles/{}/preview` |
| `spreset` | 78 | particles.js | none (browser only) |
| `spimportretry` | 101 | particles.js | `/api/effects/{}/estimate`<br>`/api/effects/{}/particles_estimate`<br>`/api/particles` |
| `spprice` | 102 | particles.js | `/api/effects/{}/estimate`<br>`/api/effects/{}/particles_estimate`<br>`/api/particles` |
| `spfresh` | 115 | particles.js | none (browser only) |
| `spopen` | 137 | particles.js | none (browser only) |
| `spmake` | 139 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `roscreate` | 256 | particles.js | none (browser only) |
| `rosback` | 257 | particles.js | none (browser only) |
| `rosbank` | 258 | particles.js | `/api/particles/bank` |
| `rosstickers` | 259 | particles.js | none (browser only) |
| `rosscope` | 260 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `rosbankpick` | 261 | particles.js | none (browser only) |
| `rosbankbuild` | 262 | particles.js | `/api/particles`<br>`/api/particles/bank`<br>`/api/particles/deleted`<br>`/api/particles/{}/default-sprite`<br>`/api/particles/{}/preview` |
| `rosapprove` | 280 | particles.js | `/api/particles`<br>`/api/particles/bank`<br>`/api/particles/deleted`<br>`/api/particles/{}/render` |
| `rosapproveall` | 282 | particles.js | `/api/particles`<br>`/api/particles/bank`<br>`/api/particles/deleted`<br>`/api/particles/{}/render` |
| `psopen` | 300 | particles.js | `/api/particles`<br>`/api/particles/{}/more`<br>`/api/particles/{}/preview` |
| `psassign` | 303 | particles.js | none (browser only) |
| `psassignsave` | 305 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/link`<br>`/api/particles/{}/unlink` |
| `psunassign` | 308 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/unlink` |
| `psdup` | 309 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/duplicate` |
| `psrename` | 310 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}` |
| `psdel` | 311 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/delete` |
| `psrestore` | 317 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/restore` |
| `pspickcell` | 318 | particles.js | none (browser only) |
| `pspickcancel` | 321 | particles.js | none (browser only) |
| `pspicksave` | 322 | particles.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}`<br>`/api/particles/{}/preview` |
| `psmoremode` | 357 | particles.js | `/api/particles/{}/more` |
| `psmoreprice` | 358 | particles.js | `/api/particles/{}/more` |
| `psmoreexisting` | 359 | particles.js | none (browser only) |
| `psmoregrid` | 365 | particles.js | `/api/particles/{}/more` |
| `psmorechip` | 366 | (no `data-act` button: called from code, a key, or a form) | `/api/particles/{}/more` |
| `psmoreadd` | 371 | (no `data-act` button: called from code, a key, or a form) | `/api/particles/{}/more` |
| `psmoredraw` | 373 | particles.js | `/api/effects`<br>`/api/generations`<br>`/api/jobs`<br>`/api/packs/{}/particles`<br>`/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/{}/more` |
| `psbnewpack` | 399 | particles.js | `/api/particles/{}/add` |
| `psopennew` | 405 | particles.js | `/api/particles`<br>`/api/particles/{}/preview` |
| `psbpreset` | 435 | particles.js | `/api/particles/{}/preview` |
| `psbshuffle` | 436 | particles.js | `/api/particles/{}/preview` |
| `psbsave` | 444 | particles.js | `/api/packs/{}/stickers/{}/particles`<br>`/api/particles/{}` |
| `psbsaveas` | 445 | particles.js | `/api/packs/{}/stickers/{}/particles`<br>`/api/particles/{}/preview`<br>`/api/particles/{}/save-as-new` |
| `pschat` | 446 | particles.js | `/api/particles/{}` |
| `psbrender` | 448 | particles.js | `/api/packs/{}/particles`<br>`/api/particles`<br>`/api/particles/{}/render` |
| `psblottie` | 452 | particles.js | `/api/packs/{}/particles`<br>`/api/particles`<br>`/api/particles/{}/add`<br>`/api/particles/{}/export-lottie` |
| `psbadd` | 457 | packs.js, particles.js | none (browser only) |
| `pspickset` | 469 | particles.js | `/api/particles/{}/link`<br>`/api/particles/{}/preview` |
| `psmakepack` | 471 | packs.js | none (browser only) |
| `pspickpack` | 472 | packs.js | none (browser only) |
| `pspackassign` | 473 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `agpscope` | 475 | chat-cards.js | `/api/particles` |
| `agpopen` | 476 | chat-cards.js | `/api/particles`<br>`/api/particles/{}/preview` |
| `agpapprove` | 477 | chat-cards.js | `/api/generations` |
| `psrecover` | 479 | packs.js | none (browser only) |
| `psrecovercreate` | 480 | particles.js | none (browser only) |
| `psrecovergo` | 482 | particles.js | `/api/particles`<br>`/api/particles/{}/preview` |
| `ptcancel` | 499 | particles.js | `/api/particles/{}/delete` |
| `ptgo` | 500 | particles.js | `/api/history`<br>`/api/particles`<br>`/api/particles/{}/more`<br>`/api/particles/{}/preview` |

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

### `reactions.js` (21)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `rxpick` | 258 | reactions.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview` |
| `rxmore` | 265 | reactions.js | none (browser only) |
| `rxmulti` | 268 | reactions.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview` |
| `rxselall` | 269 | reactions.js | none (browser only) |
| `rxclear` | 270 | reactions.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview` |
| `rxmany` | 272 | reactions.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview`<br>`/api/particles/reaction-handpicked`<br>`/api/particles/reaction-handpicked/assign`<br>`/api/particles/reaction-presets`<br>`/api/particles/reaction-presets/assign` |
| `rxpopen` | 282 | reactions.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview` |
| `rxpadd` | 284 | reactions.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview` |
| `rxsave` | 286 | reactions.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview`<br>`/api/particles/reaction-handpicked`<br>`/api/particles/reaction-presets`<br>`/api/particles/reaction-presets/{}` |
| `rxcreate` | 291 | reactions.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview`<br>`/api/particles/reaction-handpicked`<br>`/api/particles/reaction-presets` |
| `rxpdel` | 300 | reactions.js | `/api/particles/reaction-handpicked`<br>`/api/particles/reaction-presets`<br>`/api/particles/reaction-presets/delete` |
| `rxmdel` | 301 | reactions.js | `/api/particles/reaction-handpicked`<br>`/api/particles/reaction-presets`<br>`/api/particles/reaction-presets/delete` |
| `rxpremove` | 303 | reactions.js | `/api/particles/reaction-handpicked`<br>`/api/particles/reaction-presets`<br>`/api/particles/reaction-presets/delete` |
| `rxmotion` | 304 | reactions.js | `/api/particles/emoji-preview` |
| `rxpsel` | 306 | reactions.js | none (browser only) |
| `rxpselall` | 310 | reactions.js | none (browser only) |
| `rxpclear` | 311 | reactions.js | none (browser only) |
| `rxclose` | 327 | reactions.js | `/api/particles`<br>`/api/particles/deleted`<br>`/api/particles/emoji-preview` |
| `rxreset` | 328 | reactions.js | `/api/particles/emoji-preview` |
| `rxdl` | 330 | reactions.js | `/api/particles/reaction-presets/{}` |
| `rxzip` | 331 | reactions.js | `/api/particles/reaction-presets.zip` |

### `settings.js` (3)

| action | line | button drawn in | server routes (its code + its helpers, 2 deep) |
|---|---|---|---|
| `setgo` | 54 | settings.js | none (browser only) |
| `prepset` | 59 | settings.js | `/api/prepared/setting` |
| `thmset` | 66 | settings.js, theme.js | none (browser only) |

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
| `pwgo` | 182 | studio-animate.js | `/api/generations/{}/add`<br>`/api/packs` |
| `gopenpack` | 244 | studio-core.js | none (browser only) |
| `gvideo` | 250 | studio-animate.js, studio-core.js | `/api/generations/{}/quick_sheet` |
| `gpickvideo` | 319 | studio-animate.js | none (browser only) |
| `gsheetapprove` | 324 | studio-animate.js | `/api/generations/{}/quick_sheet` |
| `gvclose` | 332 | studio-animate.js | none (browser only) |
| `gcopyprompt` | 337 | studio-animate.js | none (browser only) |
| `openstudio` | 376 | particles.js | `/api/generations` |
| `lcstudioedit` | 388 | packs.js | `/api/generations`<br>`/api/generations/{}/studio_edit` |
| `lcopenstudio` | 394 | packs.js | none (browser only) |

### `studio-core.js` (26)

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
| `gcutany` | 675 | studio-core.js | `/api/generations/{}/recut` |
| `gretrysheet` | 683 | studio-core.js | `/api/generations` |
| `greqgo` | 691 | studio-core.js | `/api/generations` |
| `gopenfolder` | 756 | studio-core.js | `/api/generations/{}/reveal` |
| `vslopen` | 805 | studio-core.js | none (browser only) |
| `gvsize` | 886 | studio-core.js | `/api/generations/{}/anim_preview` |
| `gresize` | 891 | studio-core.js | `/api/generations/{}/anim_preview` |
| `vzedit` | 899 | studio-core.js | `/api/generations/{}/anim_preview` |
| `vzsize` | 900 | studio-core.js | `/api/generations/{}/anim_preview` |
| `vzmove` | 901 | studio-core.js | `/api/generations/{}/anim_preview` |
| `vzcentre` | 902 | studio-core.js | `/api/generations/{}/anim_preview` |
| `vzzero` | 907 | studio-core.js | `/api/generations/{}/anim_preview` |
| `vzgrid` | 908 | studio-core.js | `/api/generations/{}/anim_preview` |
| `vzapply` | 919 | (no `data-act` button: called from code, a key, or a form) | `/api/generations/{}/anim_preview`<br>`/api/generations/{}/position`<br>`/api/generations/{}/resize`<br>`/api/generations/{}/video_size` |
| `vzcancel` | 936 | (no `data-act` button: called from code, a key, or a form) | none (browser only) |
| `vslreset` | 990 | studio-core.js | `/api/generations/{}/position`<br>`/api/generations/{}/video_size` |
| `gzipdl` | 1011 | studio-core.js | `/api/generations/{}/export.zip` |

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
| `tgsend` | 42 | packs.js | `/api/packs/{}/short`<br>`/api/packs/{}/telegram`<br>`/api/packs/{}/telegram.zip` |
| `tgconnect` | 43 | telegram.js | `/api/packs/{}/short`<br>`/api/packs/{}/telegram`<br>`/api/packs/{}/telegram.zip`<br>`/api/telegram/config` |
| `tgdisconnect` | 46 | telegram.js | `/api/telegram/disconnect` |
| `tgcopy` | 47 | telegram.js | none (browser only) |
| `tgsettings` | 54 | telegram.js | `/api/packs/{}/telegram.zip` |

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
| `trorder` | 32 | trending.js | `/api/trending` |
| `tropen` | 33 | trending.js | `/api/trending` |
| `trlike` | 34 | trending.js | `/api/trending`<br>`/api/trending/{}/${on` |
| `trcomment` | 36 | trending.js | `/api/trending`<br>`/api/trending/{}/comments` |
| `truncomment` | 38 | trending.js | `/api/trending`<br>`/api/trending/{}/comments/{}/delete` |
| `truse` | 39 | trending.js | `/api/trending/{}/use` |
| `trunshare` | 43 | trending.js | `/api/trending`<br>`/api/trending/{}/unshare` |
| `trshare` | 44 | trending.js | `/api/trending`<br>`/api/trending/{}/${on` |

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
