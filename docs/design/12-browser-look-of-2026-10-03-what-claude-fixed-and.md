# Browser look of 2026-10-03 (what Claude fixed, and what is still Haitham's eyes)

<sub>Part of [design.md](../design.md).</sub>

P1-P13 and the particle screens were walked in a headless Chromium (Playwright from `mirsal/venv`) on a scratch copy of `out/` (recipe: `docs/dev-notes.md`); Haitham has not looked (`docs/waiting-for-haitham.md` W1). What the walk found and fixed, as rules:

* **A console script must be in `UI_FILES` (`console/server.py`) and in `index.html` in load order.** `sheet-recovery.js` and `job-recovery.js` were missing from `UI_FILES` (the page got a 404 it swallowed, so the recovery controls never drew); `trash.js` loads before the Settings card needs it, so the Trash card draws on first open.
* **Particle entry never guesses an unrelated pack or saved run.** Sticker, batch and pack actions pass explicit target scope; Library asks for the target first. Approve as a pack returns to that batch's editor. Continue is explicit and restricted to matching scope. New set rejects stale async replies. The burst maker lights the chosen preset, then the set default, then `burst`.
* **A blocked animation keeps its finished clip**, dimmed (`.gt.nx`), with the reason and the *Use it anyway* button laid over it (`gblockover`).
* **The key-colour header says the truth**: "Blue screen" / "Green screen" (and "Blue screen & cuts") follows `key_colour`, never a fixed word.
* **Generate prompt gives visible feedback**: the pre-batch Prompt step scrolls into view when it opens, and the button is disabled while the free planner runs.
* **The editor's Save tooltip names where it returns** (the AI or the Studio) when opened from the chat.
* **The Trash card lists a batch by its subject** as well as its number.
* **The bulk "Use all anyway (N)" / "Take all back (N)" buttons are guarded while the re-cut runs**: they disable, read "Cutting again...", and a second click is ignored instead of answering `409 busy`.
* **Remove batch leaves no empty edge strip** (the bordered bar is emptied and loses its class when no batch is open).
* **The Queue pill reserves room at the foot of every screen** (`body.hasq`), so it no longer overlaps the Create button.

Still open from the walk (not fixed, all in `docs/waiting-for-haitham.md`): an empty "New chat" made by a setting click (W22), a chat edit of an animated sticker opening Prepare, "undo" with no "redo", and a bare "the last one" with no person planning a new batch (W23).
