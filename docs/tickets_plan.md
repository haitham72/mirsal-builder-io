# Tickets: an AI logger in Postgres instead of LangSmith

**Status: planned (Haitham, 2026-10-04), not built.** Built after the FastAPI migration and streaming chat (`office_lan_plan.md` §4, step 4), with its pydantic models written once in the new API layer. **LangSmith is retired**: it is a trace viewer for LLM developers, it sends data off the machine, and it cannot hold what the person meant or what should be fixed. `obs/trace.py` stays dormant (`MIRSAL_TRACE=none`) until this lands, then is removed with its docs.

Written for Haitham and the LLM sessions that build it.

## What a ticket is

Every report is one ticket, a row in Postgres:

| field | filled by |
|---|---|
| `what_happened`, `at` | automatically: the route, request id, batch / job / set / sticker ids, the error text, the last events of that batch or chat |
| `intent` | the person's own words (the chat message) or the screen action that led to it |
| `issue` | the AI logger classifies it (a closed list: wrong result, crash, stuck job, wrong count / duplicate, UI, slow, spend, other); the person confirms |
| `proposed_fix` | drafted by the AI logger with the **local** model (free, rule 13); a person edits it |
| `questions[]` | 2-4 choices + "something else", preset per issue type or generated and checked by pydantic; each answer stored |
| `status` | `open` → `answered` → `fixed` / `wont_fix`; `fixed_by` links the commit |
| `fingerprint` | the same failure (route + error class + normalised message) folds into one ticket with a count |

## How tickets open

- **Automatically** on a server error, a job that ends FAILED, a recovery that gives up, or a Telegram send refused. Never on a warning a person can get past (rule 10).
- **By hand:** a **Report** button on every batch, sticker, particle row and chat message, and the chat phrase "this is wrong". The report opens with the context already filled.
- The questions never block anyone: every one can be skipped, and the ticket stays useful without answers.

## Where they go

- `migrations/0NN_tickets.sql`: `tickets` and `ticket_answers`; Settings > Tickets lists them (filter: open, mine, by issue).
- The next LLM session reads open tickets instead of re-testing the app (`docs/testing.md`, the test budget). A ticket that needs code becomes an entry in `docs/backlog.md` (the trackers stay trackers, rule 7: tickets are what happened, the backlog is what to build).
- With the admin bot (`office_lan_plan.md` §2.4) a new ticket is one Telegram line with **Open**.

## Models (pydantic, in the API layer)

`Ticket`, `TicketQuestion` (`text`, `choices[2..4]`, `allow_other`), `TicketAnswer`, `TicketDraft` (what the local model returns: `issue`, `summary`, `proposed_fix`, `questions`), validated strictly; an invalid model answer falls back to the preset questions for that issue type, never to an error the person sees.
