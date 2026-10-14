# Person references, edits that reuse the parent prompt, undo (2026-10-03)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

Code: `agent/resolver.py` (`PERSON_REF`, `LAST_PERSON`, `beyond`, `UNDO_RX`), `agent/editroute.py` (`delta_of`, `add_to_label`, `fresh_take`, the `like` clause), `Agent.n_edit` / `_person_edit` / `n_undo` / `_edge` in `agent/graph.py`, `flow/gates.regen_plan`;
guarded by `tests/test_chat_resolver_fixes.py` (every test is a sentence from the chat audit of 2026-10-02).

- **A person is the last subject, never a question.** `him / her / he / she / they` and `the guy / the man / the girl / the character / last guy` are the *character of the chat*. With a batch open, "make him wear winter coat", "make the guy wear a
  coat", "make the last guy happier" are edits of the sheet on screen (`editroute` case tweak: the parent's own prompt, the sheet as the picture, only that change), never a new plan. The batch is the focus; **"last guy" is the newest batch of the
  chat** (`ctx.latest`, which skips an undone one), not sticker 9 (`how = "person reference"`, no sticker). A bare reference ("him", "the guy", "last guy", "he looks sad") asks only WHAT to change, naming the batch it assumed
  ("I'll work on **Banana**, the batch we have open. What should I change about him?", with two chips), and moves the focus there. `him / her / he / she / they` also resolve to the clicked sticker where `it` did. With no batch open it
  is still a request ("make a coat for him").
- **`last` is an ordinal only as an ordinal**: "the last one", "last sticker", "last picture" (and "the one before last"). "last guy" / "the last batch" / "undo the last change" are not a sticker.
- **An edit reuses the parent's prompt and adds the change.** One slice drawn again as a 1x1 (`Agent.n_edit` for a selection, a bare number, "redo 3" and "make 5 like 2"; `_regen_slices` for "make number 3 happier") is `tools.slice_plan` = `gates.regen_plan(parent, index)`:
  the parent's style, key colour, cell label, motion and tags, in the `single_1x1` template **of the parent's own version** when it is 2 or later and the file exists (a v1 parent, or none recorded, gets the current version: v1's style line says
  "flat vector sticker illustration" whatever the batch was; a saved plan keeps its wording). `n_edit` appends the change to the cell's label (`pose 3, wear a hat`: the prompt is the parent's wording plus the one change), sends the parent's own picture
  of that sticker (`tools.slice_reference`: its cell of the sheet at the sheet's resolution; "make 5 like 2" sends sticker 2 through `reference_from_sticker`), with a clause that allows the change (`editroute.REF_CLAUSES`: `tweak`, and a new
  `like` clause; the default `prompter.REFERENCE_CLAUSE` "change only the expression and the pose" is untouched and no longer used by the chat, because it contradicts "add a hat"). The batch is made in the PARENT's style, not the chat's
  setting, and **with the parent's edge finish**: `outline_px` / `erode_px` are read from the parent (`tools.edge_of`), carried on the item, handed to `tools.create(outline=, erode=)`, to the job's request (`erode` is new there) and to
  `pipeline.start`, so the child looks like its parent and not like the defaults. A "redo 3" with no change named is a fresh take: the parent's prompt exactly, no picture. More than four stickers are cut to four **and the reply says so**.
- **The edit text keeps the person's words.** `editroute.delta_of` takes out only what the sentence points at (a number, an ordinal, `number 3`, `S3`, `G012/S3`, him / her / the guy, the verb in front of them, "like 2"): "make number 3 wear a hat" ->
  "wear a hat" (the old stripper removed a, the, like, and, but, i, it, one: "wear hat"), "I like 2 but make 5 happier" -> "happier".
- **Undo** (`UNDO`, `n_undo`): "undo", "revert", "roll back", "go back", "take it back" (whole message, a few filler words allowed; "go back to the previous one" and "undo 3" are not it). Scope, deliberately simple: **a plan still waiting for the go-ahead is
  dropped** (nothing was spent); otherwise **the newest refinement of this chat** (the newest pass that was made from another batch: an edit, a refinement, a redesign, another pass) is marked `undone` and the focus returns to the batch it came
  from, with that batch's card, so "it", "him" and "number 3" mean the earlier version again. Saying it twice walks back one refinement at a time; at the first version it says there is nothing to undo. Nothing is deleted and nothing is
  un-paid: the newer batch stays in History, and a sheet still being drawn is not stopped (the reply says so; when it arrives it does not take the focus, and `latest_pass` skips it). Feedback ("I hate 4"), approvals and settings are not refinements
  and are not undone by this. There is no "redo".
- **A number the batch does not have is said.** `resolver.beyond` finds "number 12", "make 12 happier", "#10", "S11" (and a bare "12" as the answer to "which one?") when the batch is smaller: "Banana has 9 stickers, so there is no number 12. Which one do you mean, 1 to 9?"
  (4 in a 2x2), with the question kept open for the next answer. "3x3", "G012", "make me 12 falcon stickers" are not sticker numbers.
- **"Don't ask me about vision again" is not about spending.** The "ask before spending" rule needs "don't ask" / "stop asking" NOT followed by about / regarding / whether / if / for. With "vision" in the sentence the chat stops asking the one-time vision
  question in this chat (`vision_asked`), leaves the vision choice itself undecided, leaves "ask before spending" on, and says all three.
