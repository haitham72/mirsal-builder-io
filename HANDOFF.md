# HANDOFF: where to start

A pointer plus the session state. Read `CLAUDE.md`, `README.md`, then:

| you need | read |
|---|---|
| a verdict, eyes or money from Haitham (numbered, with a recommendation and what each unblocks) | [`docs/waiting-for-haitham.md`](docs/waiting-for-haitham.md) |
| open work to build, by area, with a status per item | [`docs/backlog.md`](docs/backlog.md) |
| glossary, guardrails, how to run this checkout, the test budget, the browser recipe, quirks | [`docs/dev-notes.md`](docs/dev-notes.md), [`docs/testing.md`](docs/testing.md) |
| the plans for open work (scratchpads: deleted once built, the architecture then lives in the area doc) | [`docs/fastapi_plan.md`](docs/fastapi_plan.md), [`docs/tickets_plan.md`](docs/tickets_plan.md), [`docs/office_lan_plan.md`](docs/office_lan_plan.md), [`docs/burst_plan.md`](docs/burst_plan.md) (waits for W27), [`docs/deployment_plan.md`](docs/deployment_plan.md) (paused) |
| the architecture of what is built | the other files of `docs/` (routing table in `CLAUDE.md`) |

## The work, in order (Haitham, 2026-10-04)

1. **FastAPI + pydantic**, in its stages, byte-compatible, `serve --stdlib` kept for one release: [`docs/fastapi_plan.md`](docs/fastapi_plan.md), acceptance = an empty diff against [`docs/http_route_inventory.md`](docs/http_route_inventory.md). **Next.** `fastapi`, `pydantic`, `uvicorn` are in `mirsal/requirements.txt` and installed in `mirsal/venv`.
2. **Streaming chat** (SSE of the agent's steps): [`docs/fastapi_plan.md`](docs/fastapi_plan.md), "After the migration".
3. **The ticket logger** in Postgres; LangSmith retired: [`docs/tickets_plan.md`](docs/tickets_plan.md).
4. **The office LAN**: accounts, Settings > People, the Telegram admin bot, 10 credits per user: [`docs/office_lan_plan.md`](docs/office_lan_plan.md). W49-W50 first.
5. Then the rest of [`docs/backlog.md`](docs/backlog.md) by area (groups: suggest by meaning, trace a batch to its chat; the chat audit items; contract polish).

## Session state (2026-10-04)

- Everything is committed and pushed on `better_ui/ux` (one commit per phase; runtime `out/` in its own snapshot commit; `out/backups/` stays local and git-ignored). Haitham authorized "comment commit push sync" after each phase.
- Built and accepted by Haitham in the browser today: particle rows, the three particle sources with Kling, the Size slider, Removed batches with Remove / Remove all, batch groups with the variations strip above the steps, the Animation tab as a create view, the Style chip, the compact AI enhancer strip, the motion language.
- **Test budget (`docs/testing.md`, first section):** one narrow run per change; what passed stays valid; docs-only changes run nothing; Python tests one at a time; browser checks on a scratch copy and a spare port (`:8795` is held by an old scratch server from an earlier session; use another), never the live `:8770`.
- Haitham restarts `:8770` himself to see changes (the Studio warns when it runs older code than the files on disk).
