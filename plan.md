# Plan (Haitham, 2026-10-05): A. particles on their own, then B. packs per person + Trending

## A. Particles from a request, without a sticker (first)

Haitham: Create's "Particle effects" is broken: remove it. The Studio gets a **Particles** choice before the AI enhancer; "create particles for lipsticks and ribbons" routes to particles and brings particles back on their own: a set with no sticker (a stand-alone set, `owner: []`), fully usable and exportable.

A1. **Engine.** `particle_sets.from_request(text, grid, mode)`: the elements named in the request (deterministic: "for/of X, Y and Z", singular, at most the grid's cells; `effect_prompts.lint_plan` rules), a stand-alone set with `plan {subject, elements, style}`; `POST /api/particles/from-request`. Price and sheet through the existing `/more` (estimate, then go), so the sheet is a particle batch `G###` (`kind: particles`) feeding the set.
A2. **Studio.** A **Particles** chip before the AI enhancer: on, the prompt is a particle request; Generate prompt shows the elements and the price, Generate makes the sheet. The particle batch opens on its set: sprites, simulator, render, download, Add to pack.
A3. **Earlier batches.** A particle badge, top-right, on particle batches (`kind: particles`).
A4. **Create.** Remove the "Particle effects" button (old E### effects stay readable).
A5. **Telegram.** A burst is a video sticker (WEBM VP9 alpha, 512 px, <= 3 s, <= 256 KB); a stand-alone set's bursts go to Telegram as a pack of bursts ("Make a pack of these bursts"), or into an existing pack. Document what Telegram accepts (no particle format exists in the Bot API).
A6. **AI chat.** "particles for X" with no target: the agent asks "for which pack?" with chips (the packs, "the last pack {name}", "on their own"), and on their own runs A1.
A7. Docs: `docs/particles.md` (stand-alone sets reverse "There is no standalone particle pack"), `docs/api.md`, `docs/agent-and-chat.md`, `docs/design.md`; tests.

## B. Packs per person, public packs, Trending by attention

Closes `docs/backlog.md` "A Library of their own for members". Decisions (Haitham, 2026-10-05): each person's Library shows only their own packs (the owner too); a pack's maker makes it public or private, the owner and admins can also take any pack off Trending; members do not send to Telegram yet; views count by attention relative to the other public packs.

1. **Pack owner.** `media/library.py`: a pack carries `owner` (the creator's id; the owner role is always `local`; a pack without one is `local`'s). `snapshot(owner=...)` lists only that person's packs and stickers. `create_pack(name, owner)`.
2. **Server guard.** `console/server.py` `_authorize`: a member may `GET /api/library`, `POST /api/packs` (create) and every `/api/packs/{pid}/...` route of a pack they own, except the Telegram ones (`/telegram`, `/telegram.zip`); `/lib/<file>` only for a sticker of their own pack; `add_from_generation` only from a batch they can see. Another person's pack answers 404.
3. **Library for members.** The rail shows Library to members (their packs, Recent, My Stickers, Trending tab); the Studio's Add to pack works for them; no Telegram button for members.
4. **Public = in Trending.** `flow/trending.py`: `share` / `unshare` by the pack's maker, or the owner / an admin; listing shows `by` (name), `mine`, `views`. "Use in my workflow" copies the pack into the viewer's own library (owner = the viewer) and counts a use.
5. **Views by attention.** `POST /api/trending/{pid}/view` when a pack is opened: at most one per person per day, never the maker. Score = likes 3 + comments 2 + uses 4 + 2 × view index, each fading (half life 5 days); view index = this pack's faded views ÷ (all public packs' faded views ÷ their count), so 1.0 is an average pack.
6. **Screens.** Pack page: a "Public" switch for its maker (and owner/admin); Trending cards show views, maker; the opened pack shows views and uses.
7. **Docs and trackers.** `docs/api.md` (Library per person, Trending), `docs/design.md`, `docs/backlog.md` (delete the item), `README.md` row; tests: `tests/test_trending.py`, library owner filter, guard.
