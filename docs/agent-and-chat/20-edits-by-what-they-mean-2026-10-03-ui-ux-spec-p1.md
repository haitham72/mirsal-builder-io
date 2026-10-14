# Edits by what they mean (2026-10-03, UI/UX spec P11-P13)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

`agent/editroute.py` (pure, rules only) reads every request about what is open into exactly one of: **the editor**, or a regeneration of one of three kinds. The intent is `EDIT_ROUTE` (`Agent.n_editroute`); "many packs of the same character" is `UNSUPPORTED` and says so (the next feature is `docs/burst_plan.md`).

| the person means | examples | what is sent |
|---|---|---|
| **editor**: a transformation or a cleaning of one slice | rotate, flip, crop, remove the lines, add a text | nothing is generated or spent: *"Sure — want me to boot up the editor for you?"* and a chip that opens the editor on that slice at once. Save returns **to the AI** (`E.back.to`), the tile shows the new picture |
| **(a) tweak**: I like the image, change a detail | move its hand, make him cry, her blonde, a hijab on cell 4, remove the skyline, make it cartoonish, cuter | the **sheet** as the picture + the parent's own saved prompt + only that change (`ref_clause`) |
| **(b) action**: same image, new action | "now make him play football" | the **sheet** as the picture; every cell's action becomes the new one, the poses stay; the shape stays |
| **(c) redesign**: same subject and actions, new design | "make him iron man", "now make it as a lemon" | **no picture**; the parent's prompt with the subject replaced everywhere (description, keys, first tags); the actions are kept |

Before a generation edit, `Brain.edit_meaning` reads the full request, including every clause, and returns a schema-checked tweak/action/redesign or a focused clarification. Low-confidence interpretations ask; when the model is unavailable, `editroute.clear_change` accepts narrow known changes and asks for unclear ones. "Replace 2 with a cat" uses S2 as the source, preserves its action and plans one cell; replacement words cannot compete with source words during target resolution. "Replace it with a cat" uses a resolved focused sticker. Missing targets and number-to-number replacements ask rather than guessing. Mixed unknown clauses cannot be silently dropped from a generation edit.

A pronoun ("him", "it") in the older general edit flow is the character, so the whole sheet; a number, an id or a clicked sticker is one **slice**, drawn alone as a 1x1 from its own cell of the parent's plan (`tools.slice_plan`), with only that slice as the picture (`tools.slice_reference`: its cell cut out
of the sheet at the sheet's resolution; scaled up only under the 400 px minimum, and the reply says which: *"S3 is 682 px, over the 400 px minimum, so it is sent as it is"*). The sheet is the batch in focus, and after an edit from the Studio or the AI it is the **fixed sheet** (`tools.sheet_reference`).
The new batch is saved under the turn's subject (`iron man`), so the next turn's "make him cry" is about it, never about a subject made of the sentence's words. Ambiguous sentences ask nothing they can answer from the plan; sentences naming a subject of the chat ("make the cherries more cartoonish") stay with the
older refine flow. The classifier's table of examples is `tests/test_agent.py::EditRouteClassifier`. The broader conditional interaction rules, including separate clarification/plan state and attribute replacements, are proposed in [chat-interaction-proposal.md](../chat-interaction-proposal.md); they are not all implemented.
