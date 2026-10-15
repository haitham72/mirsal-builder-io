# 5. Per screen

<sub>Part of [design.md](../design.md).</sub>

### Home (built 2026-10-10, `home.js`, `studio.css` `.hm-*`)

The first screen and the Mirsal logo's target: `#/home`, an empty hash, and the first start of each browser session (`hmFirstStart`, `sessionStorage`; entity deep links stay intact). The welcome film opens over it; pressing the logo on Home scrolls to the top and redraws. The page reads the caller's real library (`GET /api/library`) inside the shared shell, without a second column. Counts and search precede the hero (up to three real stickers, newest pack first), animation and particle feature cards, and four shortcuts: a clean AI chat, Studio, Import pack for the owner / From a photo for others, and Library.

**Made by you. Ready to express.** shows individual real stickers, newest packs first, with All / Animated / Static / With particles filters and search over pack names, sticker names and emoji. Each tile opens its pack and keeps its Telegram link. View all packs opens Library. Up to twenty-four stickers are divided into two distinct bands, each with at most two rows; a smaller collection uses only its available stickers.

Each band ends with a full-width film exactly one sticker row tall. The first uses `welcome.mp4` and opens the existing welcome modal; the second uses `onboarding.mp4` and opens the full video with native controls. Both use `object-fit:cover`, loop muted, and show a poster without autoplay under reduced motion. The supplied onboarding filename is lowercase; its poster was extracted locally at one second. Both films stay available for an empty library or filter result.

Two through six columns are chosen from the showcase's measured width at 560 / 780 / 1000 / 1220px thresholds. `ResizeObserver` re-slices the two bands as their container resizes; no sticker is repeated between bands. Filtering, searching and resizing replace only sticker tiles, preserving the mounted films. A shared CSS calculation sets card and film heights from container width, columns and gaps. How it works and the footer follow. The landing-page headline sizes remain scoped to `.hm`. Tests: `tests/js/home.test.js`; browser geometry is checked with fake media at 1440 / 900 / 390px in both themes.

### AI (`chat-core.js`, `chat-cards.js`, `chat-stage.js`, `agent.css`) — the reference, keep its character (built; styles added under the box)
- Keep: the cyan/glass/glow depth, the gradients, the hover and selection states on the chat list, the new-chat background.
- **Added (Haitham, 2026-10-02): the style tiles under the AI box**, smaller than the Studio's (46px swatches, 34px once a chat has messages), with chips for the style, grid and spending of the next sheet. Details in `docs/agent-and-chat.md`.
- Chat shares the root tokens and the standard rail (§3–4); its session list uses the shared second column.

### Library (built)

The Packs side panel lists newest-created packs first; a batch group takes the position of its newest pack while its assigned parent stays first within the group. Opening a pack preserves the panel’s scroll position through navigation and the subsequent library refresh. Entering a new search starts at the first matching result.

- **Reactions tab:** finished sets as box cards in a grid (`.ps-lib`; a click on the card itself opens or closes it, the opened card spans the row) plus **Create** (Predefined bank with finished/unclaimed states, build-one-or-batch with default-sprite previews and approve-to-collapse; or Stickers into the Studio). **My Stickers** is one box per pack (`.lib-pk`, the pack's name, count and Open pack) inside one selection area, so a drag box still crosses packs. **Trending** cards keep the like and comment count on the card's bottom-left, whatever the name's wrap (`.tr-meta` `margin-top:auto`). (Haitham, 2026-10-05.)
- **Sticker details** gains one field: **Edited outside the app** (file picker + Replace, Undo when there is a previous file): same dialog, existing `.fld`/`.row`/`.btn` classes, no new styles.
- **Rail:** identical to AI's, same scaling, same persistent position — this is the explicit ask.
- **Sticker library gets the same glow background as AI** so the two screens read as one app.
- Keep the rail's fonts, backgrounds, hovers and selection states **character-identical** to AI's. If a value differs between the two, AI wins.

### Studio (built)

Add to a pack uses the included generations currently in view, preserving each generation’s still/animation state. Its default destination is a pack already containing those generations, otherwise a new pack.

The project map and journey organize the batch's Prompt, Stickers, Motion, Particles and delivery views. The toolbar offers Stickers / Sheet / Both, background, size, Next batch and a compact menu. Each rejected picture keeps its override; a click opens the docked sticker panel (§9). Prepared batches have a staff-only chip and a zero-credit explanation; Make a new one uses the live price.

The composer uses the shared surface and tokens. Style presets are 84px wrapping tiles opened by the Style chip; picking closes the tiles and updates the chip. Selection uses a ring and check. Presets come from `generation/styles.py`; real art from `console/assets/styles/` wins, otherwise a deliberate abstract swatch is generated. The enhancer uses the shared engine/model rows. Feature ownership is listed in `docs/architecture.md` §6.

### Pack (built)

The header’s “…” menu is anchored to the action row, with its width bounded by that row. It opens within the main column when the header wraps, keeping Delete pack clear of the Packs sidebar. The decorative cover badge (`#pkgrid .cell .badge2`) never intercepts a click (`pointer-events:none`); position, text and z-order are unchanged. On a phone (≤760px) the sticker viewer's header gives the title/metadata its own full-width wrapping row, with prev/toggles/next on row two as 44px targets; desktop layout is unchanged.

### Chat (built)
- Rail and second column per §4. The conversation keeps AI's gradients and hover/selection; the header matches every other screen's header.

### Settings (built)

`settings.js` renders Appearance immediately, before awaiting system APIs. Its Dark / Light buttons persist only a browser preference and retain keyboard focus when switched. The completed page adds a sticky section bar built from a registry (`SET_SECTIONS`) and rebuilt after the auth/tickets/trash wrappers mount their cards, so it only offers mounted sections: Appearance · Account (LAN only) · System health · Prepared sheets (staff) · AI · Telegram · Tickets (where its card mounted) · Trash. Each item scrolls to its card. People are managed in Users; Settings keeps the signed-in account and a staff link to Users. The prepared-sheet preference remains subordinate to `MIRSAL_PREFER_PREPARED` when set.

### Help (built 2026-10-05, `support.js`, `.su-*`)
- **Its own section at the end of the rail** (icon `help`). A red dot (`.rdot`) shows on it while a notification is unread. Everyone has it.
- **The second column** is the person's issues (title, a state chip, time) and, below them, their notifications. A new question is the `+` in the header. Staff get three tabs at the top: My issues, Queue and FAQ review. Issue, queue and FAQ titles are native `button.crow` controls (full-width, 44px, visible focus), keeping their `suopen`/`suq`/`sufaq` actions and ids.
- **The stage** is one conversation: the person's messages on the right and the agent's and admin's on the left (the Chat's bubbles; an agent bubble in `--glass` / `--aline`, an admin bubble in `--pri-l`).
  - Under an answer sit the help entries it read, as small chips; an FAQ chip opens the entry.
  - Then one bar that says what can be done now: "Did this solve it?" Yes / No, Send to support, Attach a screenshot, Waiting for support, Support replied, or Resolved + Reopen.
  - The box at the bottom takes text and a screenshot (📎, or Ctrl+V).
  - The state chips are cyan (answered), amber (waiting), blue (replied) and green (resolved).
- **Staff**:
  - The Queue shows the ticket over the person's conversation, with the screenshots and "Vision model saw" in a wash box. Reply keeps it open; "Reply and resolve" closes it, and the line under the buttons says so.
  - FAQ review shows the published text in a grey box above the proposal's fields, then Save edits, Discard, Publish and Archive.
- Settings keeps one card: for a member, a link to Help; for the owner, the caught failures (Tickets) with a link to the support queue.

### Users (built 2026-10-04, `users.js`)
- **Its own section, Team in the avatar menu** (§4.2; it was a rail item until 2026-10-11), because People in Settings was a cramped list of one-liners with no usage. The **second column is the roster** (a list, so §4.3 applies): an avatar initial, the name, role · status · credits spent · batches, with two rows of filter chips (status, role); the selected person is the `.on` row, the chart icon in its header returns to everyone.
- **The stage** shows the totals (stat tiles, two 30-day bar charts, worked-vs-failed jobs, then People management: add, requests, approve, roles, passwords, credits, Answered lately) or one person: the management card (`AUV.requests` + `AUV.person`), stat tiles, the two charts, jobs with cost against estimate (a cost over its estimate in `--run`), the ledger (folded), and their work by family with prompts (folded) and 64px thumbnails linking to the WEBM when animated.
- **The graphs are hand-drawn SVG** (`UV.bars`, `UV.split`): one rect per day on `--pri` (spend) and `--ai` (batches), an empty day a 1px hairline, the day and value in each bar's title; worked / failed is one split bar in `--ok` / `--bad`. No chart library (rule 8). Stat tiles use the glass depth (`--glass`, `--aline`) like AI.
- **A member** has no Team in the avatar menu (Haitham, 2026-10-05: Users is for the owner and admins). Their own page, **My usage** (their numbers only, no management card), opens from the **My usage** button in Settings, on the "Signed in as" card.

---

Dialog Escape closes the top shared dialog through its dismissal callback and stops propagation to the underlying viewer. A welcome overlay above it retains priority. Retime therefore settles cancellation for Escape as well as backdrop and explicit Cancel.

### Studio reference (redesign)

An existing project starts with New request and Edge folded behind native summaries. New request stays open for an empty session/draft. Composer model/style remain primary choices; Options groups Stroke/Loop/Grid/Reactions/AI settings, and Prompt engine is a separate disclosure. Batch identity/version controls, import/tools and Motion have separate rows. Generation and folder/removal actions remain available in labelled menus; reversible picture recovery stays outside those menus. The current stage retains its one primary action in the bottom bar. All layout uses the shared semantic tokens; phone controls wrap without page overflow.

### Saved reactions and pack flow (redesign)

Saved-set names/previews are native open buttons; metadata appears on hover, keyboard focus or expansion. Zero spend omits the cost line. Attach and Open and save remain visible; Duplicate/Rename/Delete use Set options. Manage stickers discloses the attachment/unlink list. Motion shows the selected preset with Change; one Advanced section summarizes count, spin and resolution and includes Erosion. Open and save uses an explicit Save as a new row and never overwrites the original. Packs always show the sticker grid/selection first, then added reactions and the Reaction studio. pktab is retired per Haitham’s item6; all section controls remain. Eligible Library pack cards open their source batches directly in Studio.
