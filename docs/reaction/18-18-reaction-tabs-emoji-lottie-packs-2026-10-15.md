# 18. Reaction tabs: Emoji Style | Lottie Style | Packs (2026-10-15)

<sub>Part of [reaction.md](../reaction.md).</sub>

`#/reactions` and Library › Reactions show the same three tabs, **Emoji Style | Lottie Style | Packs**, from the one tab state — so work made in Reaction effects is visible in the Library, and the Library's sets are one tab away from the authoring screen.

## How it is implemented

One tab state, three views, no new route or engine function. Emoji Style and Lottie Style render exactly as before, on both screens.

- Tab state: `RXS.tab` (`mirsal/mirsal/console/reactions.js`, `'emoji' | 'lottie' | 'packs'`, kept in the browser as `rx.tab`; an unknown value falls back to Emoji style). The switch (`rxStyleBar`, `mirsal/mirsal/console/lottiestyle.js`) offers all three through the one `ACT.rxstyle` action (`{s}` + redraw of the current route: `RENDER.reactions()` on `#/reactions`, `spLibRefresh()` → `RENDER.library()` in the Library).
- `#/reactions`: `rxHtml` renders the tab's view; `rxDraw` triggers `spLibSync()` on Packs and returns (style loaders only run for their own tab).
- Library › Reactions: `spLibHtml()` (`mirsal/mirsal/console/particles.js`) renders the same bar (`spRxTabs`) plus the tab's view — its own sets/bank/made content on Packs, the `#/reactions` renderers (`rxLibHtml`, `rxEditor`, `rxPick`, `rxHpHtml`, `lsHtml`) on the style tabs. `spRxTabSync` loads what the shown tab needs (bank / Lottie files, once each) and refreshes; without `reactions.js` every `typeof` guard falls back to the dumped list, so older callers never break.
- Refresh: `spLibRefresh` also redraws `#/reactions` when it is the current route, so bank builds, approvals and previews arriving late repaint both screens.
- Packs includes the Library's tab bar exactly once. The 2026-10-19 interactive
  sweep found Create prepending a second bar; a failing/passing VM regression
  now requires one `role=tablist` on that view.
- "Made in Reaction effects" (`spMadeHtml`): every created Lottie (`GET /api/particles/emoji-lottie`), newest first, preview image, token + preset, Download of the stored file, capped at 24. Data, unchanged: `/api/particles` (sets), `/api/particles/bank` (finished/unclaimed).

## Deliberately not changed

- The bank's `finished`/`unclaimed` states still mean "a covering set holds a READY render" (`reaction/13-12-library-create-flow-2026-10-13.md`).
- A created Lottie is web-only (glyph embedded); packs hold stickers and bursts, so there is still no "add to pack" for it — Download is the way out.
- This branch keeps the import duplicate-choice dialogs (`again`): the no-duplicate-check removal from `main` was deliberately not ported.
- One action kept (`rxstyle`, extended with `packs`); no removed/renamed action, so `tests/data/ui_baseline.json` needs no entry. No new CSS classes.
