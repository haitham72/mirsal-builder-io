# Help & Support (native FastAPI; `flow/support.py`, `flow/faq.py`, `flow/notifications.py`; docs/agent-and-chat.md "Support")

<sub>Part of [api.md](../api.md).</sub>

Every route also answers under `/api/v1/`. A body that does not match answers `400 {"error": "bad request: ..."}`. Another person's conversation, ticket, screenshot or notification answers `404`, and a staff-only route answers a member `403`. Staff means the owner and admins. Every model call here is local and free.
* `POST /api/support/ask {text, conversation?, image?, client_id?}` -> the conversation.
  - `image` is base64 or a `data:` URL, under 8 MB.
  - A conversation waiting for support routes the text to its ticket.
  - The last agent message carries `cites [{kind: faq | doc | code, id, title, path?}]`, `need` (`none | clarify | screenshot`), `grounded`, and `offer` (nothing documented: offer support).
  - A repeated `client_id` is a no-op.
* `GET /api/support/conversations` -> `{conversations: [{id, title, status, ticket, updated}], unread}`. Status is one of `answered | awaiting_admin | admin_replied | resolved`.
* `GET /api/support/conversations/{id}` -> the conversation, and marks its notifications read. Members never see `seen` (what the vision model saw), `mode` or code cites.
* `GET /api/support/conversations/{id}/images/{img-N.png}` -> the screenshot.
* `POST /api/support/conversations/{id}/feedback {solved}`: true closes it, false escalates.
* `POST /api/support/conversations/{id}/escalate {kind?: problem | feature | access}`: one ticket and one ping, however often it is called. The ticket's issue is `feature` / `access` for those kinds.
* `POST /api/support/conversations/{id}/forget {message}`: the person erases a private message's text (a token they saved).
* An agent message may carry `request` (`feature | access`), `actions [{kind: open_batch, id, label}]` (from what it cited), and cites of `kind: activity` (the person's own jobs and batches). A private admin message carries `private: true`; anyone other than its person gets the text `[a private message]`.
* Reading `GET /api/notifications` or a conversation first runs the person's job watches: a finished job adds a message and an `update` notification.
* `POST /api/support/conversations/{id}/reply {text, client_id?}`: to the admin, after escalation.
* `POST /api/support/conversations/{id}/reopen {text?}`.
* `GET /api/notifications` -> `{notifications: [{id, key, kind: reply | resolved, at, text, ticket, conversation, read}], unread}`; `POST /api/notifications/read {ids? | conversation? | {}}`.
* Staff:
  - `GET /api/support/queue?status=active | all | <status>` -> `{tickets: [... name, title, conversation, messages, faq, pinged]}`.
  - `GET /api/support/tickets/{id}` -> `{ticket, conversation}`.
  - `POST /api/tickets/{id}/reply {text, client_id?, private?}`: the ticket stays open (`replied`). `private` keeps the text in the person's conversation only (never in the ticket, Postgres, the notification or the FAQ).
  - `POST /api/tickets/{id}/resolve {text?, client_id?}`: closes, notifies once, proposes an FAQ entry.
* `GET /api/faq` -> the published entries. Staff can add `?status=pending | draft | archived | all`.
* `GET /api/faq/{id}` -> for everyone, the published text only (404 while it is a draft); for staff, the whole record.
* Staff: `POST /api/faq/{id}/edit {title?, question?, answer?}`, `/publish`, `/discard`, `/archive`.
* Staff: `GET /api/support/status` (repo, indexed files, sections, vectors, embedder, last reindex); `POST /api/support/reindex` -> `202`, in the background.
* `GET /api/tickets/{id}`: a member gets their own ticket without the internal fields (context, fingerprint, proposed fix, who drafted it). Admins also see `support` tickets and Reports.
