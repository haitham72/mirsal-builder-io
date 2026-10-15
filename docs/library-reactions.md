# Reaction effects tabs: Emoji style | Lottie style | Packs (2026-10-15)

Haitham: `#/reactions` looked completely different from Sticker Library › Reactions, and nothing connected them. First fix was a bridge (two links + the made list in the Library); then Haitham asked for the merge instead: `#/reactions` now has three sub-tabs, **Emoji Style | Lottie Style | Packs**, where Packs is the Library's Reactions dumped as is. The bridge links are gone with it — there is nothing left to bridge to.

## How it is implemented

One tab state, three views, no new route or engine function. Emoji Style and Lottie Style render exactly as before.

- Tab state: `RXS.tab` (`mirsal/mirsal/console/reactions.js`, `'emoji' | 'lottie' | 'packs'`, kept in the browser as `rx.tab`; an unknown value falls back to Emoji style). The style bar (`rxStyleBar`, `mirsal/mirsal/console/lottiestyle.js`, shared by all three views) offers all three through the one `ACT.rxstyle` action (`{s}` + redraw).
- Packs view: `rxHtml` renders `spLibHtml()` (`mirsal/mirsal/console/particles.js`) verbatim — the same sets list, bank Create flow, and "Made in Reaction effects" section the Library shows. `rxDraw` triggers `spLibSync()` on that tab; `RENDER.reactions` returns after the draw (the style-specific loaders only run for their own tab). `spLibRefresh` (`particles.js`) also redraws `#/reactions` when it is the current route, so bank builds, approvals and previews arriving late repaint the tab like they repaint the Library.
- Data, unchanged: `/api/particles` (sets), `/api/particles/bank` (finished/unclaimed), `/api/particles/emoji-lottie` (created Lotties, newest first, capped at 24 in the list).

## Deliberately not changed

- The bank's `finished`/`unclaimed` states still mean "a covering set holds a READY render" (`reaction/13-12-library-create-flow-2026-10-13.md`).
- A created Lottie is web-only (glyph embedded); packs hold stickers and bursts, so there is still no "add to pack" for it — Download is the way out.
- One action kept (`rxstyle`, extended with `packs`); the bridge's `rxgolib` never reached the baseline and is deleted. No `renamed`/`retired` entries needed. No new CSS classes.

## Tests

`mirsal/tests/js/rxlib_bridge.test.js` (3 tests, `node --test tests/js`): the style bar carries the bridge and lands on the Reactions tab; the Library list shows the made section with working download links back and forth; the empty library still shows it. Neighbours green: `reactions.test.js`, `particles.test.js` (52/52 with the new file). Python gate: `tests/test_ui_inventory.py` (the new action is inventoried, nothing lost).

## Open

- Browser acceptance (own server, copied `out/`, providers off): make a Lottie in Reaction effects → open Library › Reactions → the card is there with its preview → Download works; both links; dark/light; ≤760 px.
- Known pre-existing failure nearby, not caused by this work: `tests/js/lottiestyle.test.js` "the grid lists every dropped file…" expects the old `<b>Motion` group; the screen has the Particular groups since the Lottie-style build. It waits with the other stale js tests for the redesign branch.
