# 9. Every rejected picture carries its own override (2026-10-03)

<sub>Part of [design.md](../design.md).</sub>

`CLAUDE.md` rule 10: a rejected picture is never a dead end and never a bare word. This is the design half of that rule.

- **One control, wherever the picture is.** A rejected sticker shows the picture, one plain sentence, and `Use it anyway` / `Take it back` **on that picture** — the Studio tile, a cell of the left sheet, the chat tile. Not a separate panel, not a dialog: the button is on the thing it decides about.
- **The sheet is clickable.** The left sheet already draws every cell's rectangle, cut lines, index and issue mark, so a rejected cell must be as clickable as its tile: a full-cell hit area, `pointer-events` on the mark, the same hover and tooltip, the same `aria` treatment. Clicking allows or takes back; clicking elsewhere on the cell opens the tile.
- **One bulk control per batch, per kind**, above the grid: `Use all anyway (N)` / `Take all back (N)`, N counting what is allow-able **now** (never everything). Same pair on the chat's creator card.
- **The locked issue colours carry the meaning** and are not repainted: a Python-rejected sticker is red, hatched when it is not in the set, solid with a check when it was allowed by the person. An override that has been given reads "allowed by you", not "ok" — the record is visible.
- **A technical block says why and offers nothing.** When Telegram's own limits (format, size, codec) or an empty cell stop something, the sentence names the limit and no allow button appears: that is a rule, not a dead end, and it must read as one.
- **The picture is never hidden by the verdict.** A vision-model rejection dims nothing and hides nothing; the sticker stays in the carousel with its reasons listed, whatever the run does next.
- **A rejected cell wears the locked marks, in red**: hatched and faded while it is not in the set, solid with a check once a person allowed it. The hatch and the fade are the record, so an override is visible on the sheet without opening anything.
- **The sheet's cells are hit areas** (built 2026-10-03, `better_ui/ux`): allow-able cells carry the allow click (still or animation, per stage), any other cell opens the tile, and an allowed cell that can be taken back carries that click instead. The hover names the plain-words reason, plus the final sentence when nothing can be allowed. Every hit rect is `tabindex`/`role="button"` with an `aria-label`, and Enter or Space presses it (a rect answers neither key by itself). Unmarked cells get an invisible hit rect, visible on hover.
- **The chat tile carries the same button per kind**, and the creator's card carries the bulk pair per kind with honest counts. **A blocked chat tile is never dimmed**: hatched red while it is not in the set, a solid red wash with a check once a person allowed it, and "allowed by you" reads as a visible record. No button ever appears without the server's word on it.

---
