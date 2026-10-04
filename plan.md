# Plan: to the finish line (v1.0)

What the next session does, in order. A step is removed from this file when it is done (its architecture goes into its area doc and `README.md`); when the last step is done this file is deleted. Haitham, 2026-10-04: "finalize the app completely … go to the finish line".

**Definition of finished:** colleagues in the office sign in on the LAN (HTTPS) with an `@nadi.ae` account Haitham approved (dashboard or Telegram), make stickers and particles in the Studio and the chat with their own 10 credits, share packs in a Trending gallery others can like, comment on and use, the chat streams its steps, every failure or report becomes a ticket, and the repository is tagged `v1.0` with docs that describe only what exists.

Each step: one commit (or one per sub-step), its doc updated in the same commit, the tests it earns under the test budget (`docs/testing.md`), pushed.

## 1. FastAPI + pydantic serving the app ([fastapi_plan.md](docs/fastapi_plan.md))

1. `console/app.py`: a FastAPI app on uvicorn that serves **every existing route through an adapter over the existing handler** (`console/server.py` `make_handler`), so every response is byte-identical; the one SSE route (generation events) is native. `python -m mirsal serve` starts it; `serve --stdlib` keeps the old server.
2. The contract suites run against both servers (`tests/__init__.py` `serve()` switch); `tests/test_api_contract.py`, `test_openapi.py`, `test_hardening.py` green on uvicorn.
3. `console/app_models.py`: the pydantic models for every NEW route (steps 2-6) live here; legacy routes keep their dict shapes behind the adapter (a native rewrite of legacy routes is not part of v1.0: it changes nothing a person sees).
4. `doctor` reports the web stack; `docs/api.md` and `README.md` say which server runs.

## 2. Streaming chat

`GET /api/chat/sessions/{id}/stream` (SSE: `step`, `card`, `message`, `done`; keep-alive, per-connection cap) from the steps the agent already records; `chat.js` / `agent.js` use `EventSource` with polling as the fallback. Done when a turn shows each step as it happens.

## 3. The ticket logger ([tickets_plan.md](docs/tickets_plan.md))

1. `migrations/010_tickets.sql`, `store/tickets.py`, pydantic `Ticket` / `TicketQuestion` / `TicketAnswer` / `TicketDraft`.
2. Automatic tickets (a 5xx, a FAILED job, a refused Telegram send; folded by fingerprint) and **Report** on batches, stickers, particle rows and chat messages; the local model drafts issue / summary / fix / questions (validated; preset questions as the fallback).
3. Settings > Tickets (list, answer the questions, status). LangSmith removed: `obs/trace.py`, its env lines, its docs.

## 4. Office accounts on the LAN ([office_lan_plan.md](docs/office_lan_plan.md) §2.1-§2.3, §2.6)

`serve --lan [--tls]`, email + password (`@nadi.ae`), *Waiting for approval*, the session cookie, Settings > People (approve, reject, roles, new password, edit, give credits), forgot password gated by Haitham, sign-in throttling.

## 5. The Telegram admin bot (office_lan_plan.md §2.4)

Long-poll `getUpdates`; cards with inline buttons for sign-up, credit request, password reset and new ticket; only Haitham's user id is obeyed; `/people`, `/user email`.

## 6. Credits per user (office_lan_plan.md §2.5)

10 on approval; reserve before a paid call, settle on the real cost, refund on failure; **Request credits** → Telegram card; nothing refills without Haitham.

## 7. Trending (office_lan_plan.md §2.7)

Shared packs in a Library tab, Higgsfield-style: like, comment, ordered by trending / new / most liked; **Use in my workflow** copies a shared pack into your own library for the Studio.

## 8. Finish

`docs/` describes only what exists (no plan files left except the paused `deployment_plan.md` and `burst_plan.md` waiting for W27); `README.md` is the index of the finished app; the trackers hold only what is still open; tag `v1.0` and push.

## Decisions this plan relies on

HTTPS on the LAN (`serve --lan` uses TLS); private work per person plus the Trending gallery for shared packs (Haitham, 2026-10-04).
