# 6. Earlier batches — the redesign (built 2026-10-02)

<sub>Part of [design.md](../design.md).</sub>

**Marks and choices (2026-10-05).** A particle batch (`kind: particles`) carries the **particles mark** top-right of its row (`.lv-pbadge`): particles no sticker owns, still usable and exportable. The composer has a **Particles** switch before the AI enhancer (docs/reaction.md section 8). The Library's Packs column shows a batch group as one row led by its **parent pack** (Add to a pack > **Assign as parent**, `lead_at`; else the group's first pack) with a fold that stays as the person leaves it; Add to a pack preselects the pack that already holds the batch, so animations upgrade it instead of making a second pack; a second pack made before that folds back with **Merge into parent** on its row (`POST /api/packs/{id}/merge`). **Dragging a pack row onto another makes it a sub-pack there** (Haitham, 2026-10-12: sub-packs, never a merge that loses which is which): nothing moves, the target becomes the group's parent, and the sub-pack's row carries **Take out** to stand alone again (`POST /api/packs/{id} {parent}`).

**Built, then simplified the same day (Haitham: showing several batches at once in the Studio is not good).** `live.js` (`histCol`, `histRow`, `drawHist`, `ACT.hopen`), `app.js` (`COL2`, `drawCol2`), `studio.css` (`.lv-hrow`, `.c2n`). Where it differs from the plan below:

- The column lists the batches on **Studio and Create** (both are list-bearing; the list is the same in the same place). Library, Pack, Chat and AI keep their own lists; Settings and the full-screen tools (editor, export, prepare, animate) have no column, because they have no list.
- **A click on a batch presents that batch, and only that batch** (`ACT.hopen`, the same action as the credits pill's recent batches): the Studio's session becomes exactly that one batch and the Studio shows its own view of it, from any screen. The stacked open cards, their open-set, their localStorage key and the per-card copy of the header, views, bar and element ids (`studioFor`, `CT`, `gcardview`, `scopeGens`, the `pfx` ids) are deleted. Under the view, the batch's own per-sticker history and AI captions stay (one block per batch of the session, which is one unless Create more was used).
- **No button, but still paged underneath.** `GET /api/history` caps a page at 50 because it reads one `result.json` per batch; the column asks for the next page by itself when it is scrolled near the end. Page 1 is read again every 10 s while Studio or Create shows, merged over what is loaded, and the column redraws only when something changed.
- A row is marked **on** when it is the batch the Studio presents.
- The grid thumbnail is 26px per cell (a 3x3 is 84px wide) so a row stays a row.

**Plan as first written (kept for the reasoning; the bullets above win where they differ):**

**Today** (`live.js:340-343`, styles `studio.css:348-375`): a block *inside the Create/live screen* (`#ghist`), titled "Earlier batches", a
**vertical stack of horizontal rows** (`.lv-hlist` is already `flex-direction:column`; each `.lv-hitem` is a row: grid on the left, `.lv-hmeta` on the
right, caret at the end), paginated by a **"Load more"** button (`.lv-hmore`).

**Target** (Haitham's ask): every previous generation lives in a **persistent left column, in the same position and at the same scale as the AI and Library
columns**, listed vertically, each entry showing its **3×3 grid, its name and its info**. No "Load more" — the column scrolls.

1. It moves out of the Create screen's body into the shared second column, so it is reachable from every screen and always in the same place.
2. One vertical list, **no pagination.** `GET /api/history` is paged today; the column asks for the full set and virtualises or caps the render (a few hundred
   cards at most) rather than paginating.
3. Each row keeps what it has — `histGrid` (the sheet's own grid via the `--c` custom property, `lv-hnoimg` checkerboard for a cell with no picture) and
   the meta line (`G###`, ready count, animated count, edited time) — but is styled as a **column entry**: grid on top or leading, name and info beneath,
   the same hover / selected / focus states as the AI chat list.
4. ~~A row opens the batch as a stacked card, several at once~~ — dropped: a row presents the one batch in the Studio (see the built note above).
5. A batch that is currently working, or that was just edited, keeps re-reading while it is visible.

**Do not confuse this with `history.js`.** That file is the **watch-folder** screen (`#/history`: `inputs/Images_gen` + `videos_gen`, Remove/Restore). It is a
different thing, it is already a vertical list, `docs/waiting-for-haitham.md` (W34) notes nothing in the rail opens it and it once shadowed this very handler. Decide separately
whether to delete it; do not fold it into this column.

---
