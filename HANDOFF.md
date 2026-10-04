# HANDOFF: where everything moved

This file used to be the whole tracker. It is now a pointer, so that nothing here is lost and nothing here needs a person to merge. Read `CLAUDE.md`, `README.md`, then:

| you need | read |
|---|---|
| a verdict, eyes or money from Haitham (numbered, with a recommendation and what each unblocks) | [`docs/waiting-for-haitham.md`](docs/waiting-for-haitham.md) |
| open work to build, by area, with a status per item | [`docs/backlog.md`](docs/backlog.md) |
| glossary, guardrails (do freely / ask first / never), locked decisions, how to run this checkout, the test tiers, the browser recipe, quirks | [`docs/dev-notes.md`](docs/dev-notes.md) |
| the FastAPI + pydantic spec, authorized after particles | [`docs/fastapi_plan.md`](docs/fastapi_plan.md) |
| the paused deployment plan (hosting, OAuth, credits, scrub runbook, its nine questions) | [`docs/deployment_plan.md`](docs/deployment_plan.md) |
| the architecture of what is built | the other files of `docs/` (routing table in `CLAUDE.md`) |

The trackers are `docs/waiting-for-haitham.md` and `docs/backlog.md` (`CLAUDE.md` rule 7): an entry is deleted the moment it is implemented and documented.

## Session state (2026-10-04)

- Work is committed and pushed on `better_ui/ux` phase by phase (Haitham: "comment commit push sync", 2026-10-04). Stage explicit paths; secrets and runtime changes in real `out/` never enter code commits.
- **Particle rows are built (2026-10-04):** every saved version of a sticker's particles is one row under it (v1, v2...); entering Particles always starts a new version from three equal cards (sticker sprites, AI image sprites, Kling from scratch); Save / Save as new / Add to pack per row (`docs/particles_plan.md` §3 and §5). Older runs were adopted on the real out (`python -m mirsal particles adopt`; backup `mirsal/out/backups/particle-rows-2026-10-04/`): the Batman Lego Kling take (E002) is row v2 of sticker `1e01c5a6` and renders READY from its 4 animated sprites (90 frames each). Still open in particles: the trash purge of particle sets and the items in `docs/backlog.md`; then FastAPI (`docs/fastapi_plan.md`).
- Acceptance follows already-created artifact paths in scratch out, with free recut/import/recovery and simulator/Add checks. Temporal fixtures supplement that proof. No fresh paid generation for acceptance.
- **Order of work (Haitham, 2026-10-04):** (1) variations = batch groups, built (`30c463a`); (2) FastAPI + pydantic in its stages, **next** (`docs/fastapi_plan.md`; `fastapi`, `pydantic`, `uvicorn` are in requirements and installed in `mirsal/venv`); (3) streaming chat; (4) the ticket logger, LangSmith retired (`docs/tickets_plan.md`); (5-7) the office LAN, the Telegram admin bot and per-user credits (`docs/office_lan_plan.md`, W49-W50 first). Public deployment and Google OAuth stay paused.
- Also built 2026-10-04: particle sheets G100/G101/G106/G109 are rows under their stickers and out of Earlier batches; the batch Particles section is one list of versions; Removed batches has Remove / Remove all (files + database rows).
- **Test budget (Haitham, 2026-10-04): spend the session building, not re-testing.** One run per change, the narrowest (the test you wrote, by name, else `mirsal test area <module>`); what passed stays valid until its files change, so do not re-run a baseline at session start or before a commit; docs-only edits run nothing; `focused` at most once per phase. Full rule: the first section of `docs/testing.md`. Slow tier and full `unittest discover` stay retired. Python tests run serially. Browser checks once per phase on scratch out and a spare port, never live :8770.
- Haitham's own browser verdict and the previously approved paid measurement are still open in the trackers; no doc calls the app personally verified.
