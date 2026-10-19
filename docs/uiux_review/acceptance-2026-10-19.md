# Redesign engineering acceptance — 2026-10-19

Branch `redesign-ui-ux`; server `http://127.0.0.1:8797/`. Slider revision
`8d0a1d65`; reaction fix `6d9d1ecf`; extended checks `37fd9781`; final hover
assets `5b6814df`. Task-owned server only; restarted between code phases.

Fresh `%TEMP%/mirsal-final-acceptance-3khccysq/outcopy`: only the named G146
artwork folder copied. G156 is a 36-frame synthetic imported 3×3 video.
P001 and one emoji Lottie were created by free deterministic local endpoints.
A synthetic saved Chat was seeded with 600 messages and bounded to 400 by the
normal store. No real chats, jobs, accounts, library, secrets or configuration
were copied. All providers disabled; no sends, collection exports or deployment.

[Machine evidence](acceptance-2026-10-19.json) contains request/status assertions.

## Slider matrix

Every cell passed: native drag/readout, pending values through poll redraw, one
reslice request on release, unchanged release with zero POSTs, and Reset
`position(offset:null,reslice:false)` then `video_size(scale:null,reslice:true)`
with one reslice. Writer-idle waits separate checks. A separate quick-second-edit
run observed real 409 retries and eventual success in every cell.

| Fixture | Width | Theme | Result | Busy retries | Screenshot |
|---|---|---|---|---:|---|
| G146 | 1440 | dark | pass | 7 | [slider-G146-desktop-dark.png](redesign-shots/slider-G146-desktop-dark.png) |
| G146 | 1440 | light | pass | 6 | [slider-G146-desktop-light.png](redesign-shots/slider-G146-desktop-light.png) |
| G146 | 390 | dark | pass | 6 | [slider-G146-phone-dark.png](redesign-shots/slider-G146-phone-dark.png) |
| G146 | 390 | light | pass | 6 | [slider-G146-phone-light.png](redesign-shots/slider-G146-phone-light.png) |
| G156 | 1440 | dark | pass | 4 | [slider-G156-desktop-dark.png](redesign-shots/slider-G156-desktop-dark.png) |
| G156 | 1440 | light | pass | 3 | [slider-G156-desktop-light.png](redesign-shots/slider-G156-desktop-light.png) |
| G156 | 390 | dark | pass | 2 | [slider-G156-phone-dark.png](redesign-shots/slider-G156-phone-dark.png) |
| G156 | 390 | light | pass | 2 | [slider-G156-phone-light.png](redesign-shots/slider-G156-phone-light.png) |

An initial run tried Reset before G146 finished: busy responses were
expected. The final matrix waits for the writer; retry behavior is tested
separately. Phone automation re-queries controls after polling redraws.

## Reaction matrix

Real clicks on all three tabs on both Create and Library, state shared both
directions, keyboard focus/Enter activation, and exact server set-id equality.
Four endpoints returned 200 with nonempty data: sets 1, bank 1898, created
Lotties 1, source Lottie files 4. Final reaction runs had no page/console errors
or failed HTTP responses.

| Width | Theme | Tab | Create screenshot | Library screenshot |
|---|---|---|---|---|
| 1440 | dark | emoji | [reactions-emoji-desktop-dark.png](redesign-shots/reactions-emoji-desktop-dark.png) | [library-reactions-emoji-desktop-dark.png](redesign-shots/library-reactions-emoji-desktop-dark.png) |
| 1440 | dark | lottie | [reactions-lottie-desktop-dark.png](redesign-shots/reactions-lottie-desktop-dark.png) | [library-reactions-lottie-desktop-dark.png](redesign-shots/library-reactions-lottie-desktop-dark.png) |
| 1440 | dark | packs | [reactions-packs-desktop-dark.png](redesign-shots/reactions-packs-desktop-dark.png) | [library-reactions-packs-desktop-dark.png](redesign-shots/library-reactions-packs-desktop-dark.png) |
| 1440 | light | emoji | [reactions-emoji-desktop-light.png](redesign-shots/reactions-emoji-desktop-light.png) | [library-reactions-emoji-desktop-light.png](redesign-shots/library-reactions-emoji-desktop-light.png) |
| 1440 | light | lottie | [reactions-lottie-desktop-light.png](redesign-shots/reactions-lottie-desktop-light.png) | [library-reactions-lottie-desktop-light.png](redesign-shots/library-reactions-lottie-desktop-light.png) |
| 1440 | light | packs | [reactions-packs-desktop-light.png](redesign-shots/reactions-packs-desktop-light.png) | [library-reactions-packs-desktop-light.png](redesign-shots/library-reactions-packs-desktop-light.png) |
| 390 | dark | emoji | [reactions-emoji-phone-dark.png](redesign-shots/reactions-emoji-phone-dark.png) | [library-reactions-emoji-phone-dark.png](redesign-shots/library-reactions-emoji-phone-dark.png) |
| 390 | dark | lottie | [reactions-lottie-phone-dark.png](redesign-shots/reactions-lottie-phone-dark.png) | [library-reactions-lottie-phone-dark.png](redesign-shots/library-reactions-lottie-phone-dark.png) |
| 390 | dark | packs | [reactions-packs-phone-dark.png](redesign-shots/reactions-packs-phone-dark.png) | [library-reactions-packs-phone-dark.png](redesign-shots/library-reactions-packs-phone-dark.png) |
| 390 | light | emoji | [reactions-emoji-phone-light.png](redesign-shots/reactions-emoji-phone-light.png) | [library-reactions-emoji-phone-light.png](redesign-shots/library-reactions-emoji-phone-light.png) |
| 390 | light | lottie | [reactions-lottie-phone-light.png](redesign-shots/reactions-lottie-phone-light.png) | [library-reactions-lottie-phone-light.png](redesign-shots/library-reactions-lottie-phone-light.png) |
| 390 | light | packs | [reactions-packs-phone-light.png](redesign-shots/reactions-packs-phone-light.png) | [library-reactions-packs-phone-light.png](redesign-shots/library-reactions-packs-phone-light.png) |

## Extended checks and findings

All four width/theme states passed a delayed real GET (1.8 seconds), navigation
away while pending, return with no stuck loading state and preserved Packs tab.
A 400-message saved synthetic history retained its scroll offset and message
count over polling. All 15 Emoji preset cards and 4 Lottie sources were hovered;
all five motion groups, Motion/Size/Advanced, the four Lottie source editors
and Emitter/Particle/Physics/Morph/Aux disclosures were opened. Set detail and
options menus were opened. No JavaScript exceptions.

Frame editor: all four width/theme states opened the real G146 preview, moved
the frame scrubber and Grid control, remained in the viewport and cancelled
with zero position/video-size POSTs. Screenshots:

- [1440 / dark frame](redesign-shots/frame-1440-dark.png), [Emoji editor](redesign-shots/extended-emoji-1440-dark.png), [Lottie editor](redesign-shots/extended-lottie-1440-dark.png), [Chat](redesign-shots/extended-chat-1440-dark.png).
- [1440 / light frame](redesign-shots/frame-1440-light.png), [Emoji editor](redesign-shots/extended-emoji-1440-light.png), [Lottie editor](redesign-shots/extended-lottie-1440-light.png), [Chat](redesign-shots/extended-chat-1440-light.png).
- [390 / dark frame](redesign-shots/frame-390-dark.png), [Emoji editor](redesign-shots/extended-emoji-390-dark.png), [Lottie editor](redesign-shots/extended-lottie-390-dark.png), [Chat](redesign-shots/extended-chat-390-dark.png).
- [390 / light frame](redesign-shots/frame-390-light.png), [Emoji editor](redesign-shots/extended-emoji-390-light.png), [Lottie editor](redesign-shots/extended-lottie-390-light.png), [Chat](redesign-shots/extended-chat-390-light.png).

Two real findings were fixed with failing→passing regressions:

- Duplicate tab bar on Create › Packs: VM assertion 2→1; full reaction matrix passed after the fix.
- Selected dark tab hover contrast: browser computed 1.26:1→13.24:1; light remains 5.17:1 at both widths.

Opening the empty synthetic set attempted only a free price estimate
(`estimate:true`), which returned 503 because Higgsfield is disabled. No `go`
request was sent. One first-cell delay hook raced an existing refresh; it was
rerun with an idle precondition and passed. These are documented environment /
harness observations, not product regressions.

Exhaustive coverage of every possible populated editor/menu remains open:
saved sets with populated cells and multiple owners, nonempty pack-specific
Manage-stickers/Save-as-new dialogs, and route-wide keyboard/menu combinations
were not exhaustively exercised in this fixture. Keep that bounded follow-up
in plan.md; paid-model quality and owner visual verdicts remain separate.

## Tests and compatibility

- Agent area: historical 322 / 5 failures / 10 errors → 322 / 4 failures / 9 errors, equal to isolated base. Remaining failures are listed in the memory review.
- Seven targeted checkpoint/profile tests passed in their narrow runs; fake Telegram turn/cleanup failed with WinError 32 then passed.
- Node JS: 389/389; Python console wrapper: 18/18. Stale rxedit assertion is replaced by current preset/tab wiring.
- GUIDE.md reconciled from main; docs/library-reactions.md points to the canonical redesign contract. No merge.
- Duplicate-choice imports, grid-mismatch consent, Resize, reversible decisions and separate Emoji/Lottie export contracts preserved.
- Keep the existing source photo `Custom_emojis/Original_emojis/rashed 02.jpg`; see [structure review](../structure-review.md). No media/history rewrite.

## Final follow-up save point

Server restarted at `60b1529d`, `http://127.0.0.1:8797/`. Fresh browser/API checks
confirm 2×2 Studio/Chat/plan defaults and four independent spatial action lines;
G146/G156 stay 3×3 with nine cells. Agent remains 322 / 4 failures / 9 errors.
Node JS is now 390/390; Python console wrapper 18/18. Its sandbox Node child
timed out at 120 seconds; the approved outside-sandbox retry passed in 2.349s.

Broad exhaustive populated-dialog/menu work remains explicit in plan.md; no
new paid-model quality claim or owner verdict was made.
