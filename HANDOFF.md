# HANDOFF: where everything moved

This file used to be the whole tracker. It is now a pointer, so that nothing here is lost and nothing here needs a person to merge. Read `CLAUDE.md`, `README.md`, then:

| you need | read |
|---|---|
| a verdict, eyes or money from Haitham (numbered, with a recommendation and what each unblocks) | [`docs/waiting-for-haitham.md`](docs/waiting-for-haitham.md) |
| open work to build, by area, with a status per item | [`docs/backlog.md`](docs/backlog.md) |
| glossary, guardrails (do freely / ask first / never), locked decisions, how to run this checkout, the test tiers, the browser recipe, quirks | [`docs/dev-notes.md`](docs/dev-notes.md) |
| the paused FastAPI + pydantic spec | [`docs/fastapi_plan.md`](docs/fastapi_plan.md) |
| the paused deployment plan (hosting, OAuth, credits, scrub runbook, its nine questions) | [`docs/deployment_plan.md`](docs/deployment_plan.md) |
| the architecture of what is built | the other files of `docs/` (routing table in `CLAUDE.md`) |

The trackers are `docs/waiting-for-haitham.md` and `docs/backlog.md` (`CLAUDE.md` rule 7): an entry is deleted the moment it is implemented and documented.

## Session state (2026-10-03)

- Tests: the full suite `Ran 1139 ... OK (skipped=12)` in the latest run, node 197/197, `tests.test_js` 18 OK. The slow tier (Tier 3) is retired by Haitham (2026-10-03): never run, never requested; the routine loop is `mirsal test fast` / `focused` / `area <module>`, node and `tests.test_js` (`docs/testing.md`).
- Nothing is committed. The working tree holds the whole 2026-10-03 body of work (verdict replay, stalled-job recovery, G3 overrides, the trash purge, the Generate prompt step, the chat resolver fixes, the verifier fixture table, the browser fixes and this documentation reorganisation) for Haitham's review (W3).
- The browser look of P1-P13 and the particle screens was done by Claude in a headless Chromium on a scratch copy of `out/`; Haitham has not looked (W1).
- The FastAPI migration was NOT done: it is not simple and the plan says wait (W38, `docs/fastapi_plan.md`).
- The paid 6.5-credit check was NOT run (W2).
