# Tickets (native FastAPI; `flow/tickets.py`, docs/store-and-search.md "Tickets")

<sub>Part of [api.md](../api.md).</sub>

* `GET /api/tickets?status=` -> `{tickets: [...]}` (the owner sees every ticket, a member their own); `GET /api/tickets/{id}` -> the whole ticket (404 for another member's).
* `POST /api/tickets {text, target?: {kind: generation | sticker | particle_set | chat | pack | other, id?, sticker?}}` -> `201` the ticket (a Report: the person's words plus what happened around the target).
* `POST /api/tickets/{id}/answer {question, question_text?, choice? | text?}` (`question_text`, the question as the page showed it, wins over the index: the local model's draft may replace the preset questions while the page is open, and an answer to a shown question is kept against its own text; an unplaceable one answers 400 "the questions changed while you were reading" and the screen reloads them); `POST /api/tickets/{id}/status {status: open | answered | fixed | wont_fix, fixed_by?}` (owner).
* A body that does not match answers `400 {"error": "bad request: ..."}` (never FastAPI's 422). Every native answer carries `X-API-Version` and `X-Request-Id` like the rest.
