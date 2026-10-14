# Conversation quality pass (2026-10-02, from the six reviews)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

Rules, in `agent/resolver.py` and `agent/graph.py`; guarded by `tests/test_chat_quality.py` (every test is a sentence that went wrong):

- **The plan you approve is the plan that runs.** `pending["plan"]` holds the plan the card showed (`graph.compact_plan`: template, slots, cells, without the prompts); `tools.create(..., base_plan=plan)` hands it to
  `Console.live("sheet", body, base_plan=...)` (in-process only, an HTTP body can never carry one) and `tasks.plan_again` rebuilds the prompts from it. Before, Create planned the request a second time (temperature 0.8) and
  the batch had none of the card's stickers. A refused start keeps the plan (`n_confirm` clears `pending` only after the start succeeded).
- **A go-ahead is a whole message from a closed list** (`is_yes`, `is_no`: "yes", "yes please", "ok", "sounds good", "yalla", "تمام", "👍" / "no", "nah", "not now", "لا"). "create a dragon pack", "yes make it red", "start over"
  are new requests; a new plan says it replaced the one it was holding ("nothing was spent on it").
- **Acknowledgements are small talk** (`is_ack`: "ok", "nice", "thanks bro", "👍"), answered by kind (`smalltalk_kind`: thanks, bye, ack, hello). A bare attribute with a batch open ("bigger", "same but red", "happier") is an edit of
  what is open (it asks which sticker), never a new subject. "how much?" is a price question. "can you make me a falcon?" is a request. A long description with nothing to point back at is a request; nonsense still goes to the model.
- **References**: "S3" is sticker 3; `last` is sticker 9 (the batch's last: 4 in a 2x2) only as "last one / sticker / image" ("the one before last" is 8; "last guy", "the last batch", "undo the last change" are not a sticker, and `tests/test_chat_resolver_fixes.py` pins each); a count in a request
  ("make me 4 falcon stickers") is not a sticker number; "make him / her / the guy / all of them / everything + a change or an item to wear" is an edit of what is open.
- **A decision is never guessed**: an approve / reject sentence with a negation ("don't approve 3") decides nothing and asks; a decision on several stickers ("approve all but 5 and 6", "reject everything") is a pending
  `review` the person confirms; one explicit sticker still acts at once.
- **Focus follows the newest batch that has stickers**: when a job resolves to a generation (`memory.refresh`) it becomes the focus; `latest_pass(with_generation=True)` skips jobs that are running or failed.
