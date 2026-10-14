# 4. The shell — rules that hold on every screen

<sub>Part of [design.md](../design.md).</sub>

1. **The rail is one fixed element in one place.** Same width, same position, same order, on all sections. Its width is a token; it does not change
   shape per route. Keep the icon-over-label form (`app.js`) — it is legible at 72px.
2. **The rail has four items** (Haitham, 2026-10-11, `docs/redesign_plan.md` D5), declared in `RAIL` (`app.js`): **Home, Create, Library, Help**, under the
   Mirsal logo, then the credits chip (`live.js`) and **the avatar** (`.rme`, the person's initials) at the bottom. The avatar opens `#rmenu`: **Settings &
   health**, **Team** (`#/users`, owner and admins), **Trash** (Settings' Trash card, `ACT.rtrash`), **Watch folders** (`#/history`, the owner) and **Sign out**
   (a signed-in person on the LAN); It remains open after its avatar is redrawn; Escape, a second avatar click or a click outside closes it. `RAILOF` says which item a screen lights: the Create screens (`agent`, `generate`,
   `create`, `effects`, `editor`, `export`, `prepare`) light Create, `pack` / `animate` / `chat` light Library, `settings` / `users` / `history` light the
   avatar. Every old hash still opens. **Create opens the tab used last** (`CTAB`: Chat or Studio), **always new and empty on both sides** (Haitham, 2026-10-14; `ACT.railcreate`, also Home's Sticker Studio tile): the Studio forgets the last session's batches (it used to reopen the last batch and its green-screen sheet) AND the chat starts a new conversation, whichever tab opens, so switching to the other tab is new too; Earlier batches, the chat list and Open in Studio still reopen earlier work, and the Chat | Studio tabs keep the current project.
   **Create's tabs** (`#ctabs`, `drawCtabs`, D7): above `agent`, `generate`, `create` and `effects`, a segmented **Chat | Studio** control and a **+ New** menu
   (a `<details>`) with **From a photo** (`#/create`) and **Reaction effects** (`#/reactions`); the full-screen tools have none. `#/effects` stays the Studio's particle editor (reached from a sticker, a batch or a pack). The chat preview (`#/chat`) is
   reached from the pack and the Library's sticker viewer (D6).
   **Reaction effects** (`#/reactions`, its own screen and file `reactions.js`, prefix `rx`, `studio.css` `.rx-*`; Haitham, 2026-10-13: "minimal small emojis",
   "do not do a lot of thumbnail cards", "search and show a couple of rows only, and only the created each in a proper designed simple card"). Three parts:
   (1) a search box with a one-line hint ("Pick an emoji: it flies as itself.") and **two rows** of small emoji glyphs (`.rx-grid`, 44 px tiles, no names; `rxClip` counts the grid's columns and hides every tile past the
   second row, so a search narrows the rows rather than growing them); pointing at a glyph plays its reaction from its right edge, 64 px (the burst's origin on the edge; the glyph stays visible). **Select several** (a toggle beside the search) turns clicks into ticks (a check on the tile) and shows one bar (`.rx-many`): the count and the ticked glyphs, **Look** (Each emoji's own / Preset NN), Delete that preset, **Create N reactions**, Clear. (2) The picked emoji in
   ONE editor card (`.rx-ed`): its reaction looping in a 220 px stage (`.rx-stage`) beside the emoji, its motion sentence,
   then two groups, each with a heading and **Reset** (`.rx-groups`, `.rx-grp`, `.rx-gh`; side by side when wide): **Simulation** (**Motion**, a select with **its own · <preset>** first, then Speed, Gravity, Swirl, Rotation, Amount, Spread: the motion's own values until moved, `…` before the server answers) and **Shape**: **Size** (×1), **Size variation** (the motion's own until moved, shown as a percent), **Size in**, **Size out**, **Hue** (`.rx-sl`; 0.4 s, 0.4 s, 25°; one line says Hue 0 keeps the emoji's own colours) and **Create reaction**.
   (3) **Your reactions**: only what was created, newest first, one simple card each (`.rx-card`: the loop on a square stage, the emoji + name, motion · how long ago (the L### id is the tooltip),
   **Lottie** (download) and **Edit** (reopens the editor with that card's options)); nothing else from the bank is ever a card. No pack picker, no sticker
   grid, no `<video>`, no Kling, no Generate more. Every stage (editor and cards) shows the emoji faintly at its centre under the loop (`.rx-ghost`), because a loop starts and ends empty: a stage is never a blank box. On a phone, **Create reaction** (with **Save preset** beside it) stays on screen (`.rx-foot`, sticky above the tab bar) while the sliders scroll.
3. **A persistent second column on every screen that has a list** — Library, Chat, AI for sure, and **Studio and Create** because both have real lists
   (Studio: the batches; Create: the pack/prepared sheets). `COL2` and `drawCol2()` (`app.js`) select the routes with lists; the shared column scrolls and can collapse, becoming a drawer below 900px.
4. **Same geometry everywhere:** same gutters, same card radius, same header height, same place the page title sits. If a screen needs to break the
   pattern for a real reason, the reason goes in this file.
5. **Responsive navigation is shared across routes.** The desktop rail scrolls when needed; below 760px every screen uses the same bottom bar. The second column uses the shared drawer below 900px.

---
