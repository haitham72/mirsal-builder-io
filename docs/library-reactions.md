# Library ↔ Reaction effects bridge (built 2026-10-15)

Haitham: `#/reactions` looked completely different from Sticker Library › Reactions, and nothing connected them. It was true: the backend served every created Lottie reaction (`GET /api/particles/emoji-lottie`), but **no screen read it** — work made in Reaction effects was invisible everywhere else, and neither screen linked to the other.

## What connects them now

Two links and one list. No new route, no new engine function, no storage change: the bridge only reads the existing API and navigates (rule 11: the contract already existed; the screens came second).

| direction | where | what |
|---|---|---|
| Reactions → Library | `rxStyleBar` (`mirsal/mirsal/console/lottiestyle.js`, shared by Emoji and Lottie style) | "Library Reactions" button (`ACT.rxgolib`, `mirsal/mirsal/console/reactions.js`): sets `LIBTAB='particles'` (the `let` in `app.js`) and goes to `#/library` |
| Library → Reactions | `spLibHead` (`mirsal/mirsal/console/particles.js`) | "Reaction effects" anchor to `#/reactions`, beside Create/Back |
| Library shows the made work | `spMadeHtml` / `spMadeCard` (`particles.js`), rendered inside `spLibHtml` | "Made in Reaction effects": every created Lottie, newest first (the server sorts), preview image, token + preset, Download of the stored file, capped at 24 |

Loading: `spMadeSync` (`particles.js`) fetches `GET /api/particles/emoji-lottie` once per page (`SPL.made`, same pattern as `spLibSync`/`spBankSync`; `spLibRefresh` redraws on arrival, `spSetsForget` clears it). States: still loading → section absent (sets spinner shows); loaded empty → "none yet" with the link back — including on the otherwise-empty "No reaction sets yet" card, so the bridge is visible before anything exists.

## Deliberately not changed

- The bank's `finished`/`unclaimed` states still mean "a covering set holds a READY render" (`reaction/13-12-library-create-flow-2026-10-13.md`): created Lotties don't alter the Create flow.
- Presets, the editor, and pack attach are untouched. A created Lottie is web-only (glyph embedded); packs hold stickers and bursts, so there is no "add to pack" for it — Download is the way out, as before.
- Additions only: one new action (`rxgolib`), no removed/renamed action, so `tests/data/ui_baseline.json` needs no entry. No new CSS classes (reuses `ps-libh`/`ps-lib`/`ps-card`).

## Tests

`mirsal/tests/js/rxlib_bridge.test.js` (3 tests, `node --test tests/js`): the style bar carries the bridge and lands on the Reactions tab; the Library list shows the made section with working download links back and forth; the empty library still shows it. Neighbours green: `reactions.test.js`, `particles.test.js` (52/52 with the new file). Python gate: `tests/test_ui_inventory.py` (the new action is inventoried, nothing lost).

## Open

- Browser acceptance (own server, copied `out/`, providers off): make a Lottie in Reaction effects → open Library › Reactions → the card is there with its preview → Download works; both links; dark/light; ≤760 px.
- Known pre-existing failure nearby, not caused by this work: `tests/js/lottiestyle.test.js` "the grid lists every dropped file…" expects the old `<b>Motion` group; the screen has the Particular groups since the Lottie-style build. It waits with the other stale js tests for the redesign branch.
