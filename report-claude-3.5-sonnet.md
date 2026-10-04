# Mirsal v1.0 — reconciled review status

Updated 2026-10-04 against the current working tree. This replaces the conflicting gap list and speculative patches in the Sonnet report with the code status checked across both supplied reviews. It does not declare production readiness.

| Claim | Current status | Evidence / limit |
| --- | --- | --- |
| Creator runs orphan on crash | Narrow recovery gap fixed | `agent/creator.advance` checkpoints each step; `graph.creator_tick` supplies persistence. Video jobs carry an internal `creator_run` tag; `ConsoleTools.creator_job` recovers a lost pointer; `on_job` saves the pointer before scheduling. Poll-driven restart and ticket-first already existed. Other crash windows remain tracked. |
| Brain has no multi-turn context | Original claim stale; compact focus added | `_route_context` already supplied profile, last question, held plan and structured-state summary. `Brain.classify` now also receives a small separate focus fence with id/grid/style and up to three sticker keys. CHAT prose remains capped. |
| Timeout jobs have no resume UI | Stale; already built | `console/job-recovery.js` Continue → `/api/jobs/{id}/continue` → `generation/recovery.continue_job` → `jobs.resume`/fulfil. W5 is real-provider validation. |
| Memory is text-only | Stored-memory claim false; convenience accessor added | Sessions already contained structured subjects/passes/likes/focus/preferences. `summary_structured()` now returns a detached dictionary, without parsing the rendered prose. |
| LLM has no ordered fallback/timeout | Partly stale; Auto budget split added | `llm.resolve`, `note_failure` and same-call Auto failover already existed. Eligible local attempts now use at most 15 seconds when cloud is usable; fallback uses the remaining total timeout. Explicit providers/Local choice keep their full timeout; `Brain._ask` remains an explicit-provider 45-second call. |
| Chat trace is lost on restart | Stale; interruption wording/note fixed | `Trace._add` already saved each step. Interrupted messages keep those steps and gain a note directing the person to the Queue. The false "nothing was spent" promise is removed from restart handling. |
| Traits are regex-fragile | Small deterministic extension | Anime and less-cartoony requests join the fixed vocabulary; two matching interactions are still required. No model-based extraction or inferred lasting preference was introduced. |
| Separator lines need automatic removal | Rejected suggestion | Keep explicit recut-as-particles/editor cleanup. White/grey detection plus row interpolation would damage light artwork; no engine pixel-removal pass was added. |
| Multi-reference roles are absent | Partly stale; explicit role wording added | Tweak/action/redesign and reference clauses already existed. Numbered role references now retain ordered per-image role instructions; source numbers do not become edit targets. Single STYLE-reference behaviour stays compatible. |
| Judge calibration is missing | Operator work remains open | The judge remains pre-review only. W11 needs 30 human labels; no labels were fabricated, no model was called, and no `vision/calibrate.py` or `mirsal judge calibrate` command was added. |

## Validation and limits

`tests.test_review_gaps`: 12 targeted checks passed in 0.704 seconds. A subsequent single integration check of reference-role routing to the priced plan passed in 0.390 seconds after that route was corrected. Checks use fakes/mocks and temporary files; no paid providers, real media processing, slow tier or full discovery were run.

The recovery checks simulate a process stopping after animation creation and after a step transition, recover a tagged job with a missing session pointer, and verify the durable job tag exists before scheduling. They do not prove end-to-end recovery against live Higgsfield, Redis or Telegram. A REQUESTED job left before scheduling may need Queue recovery. Initial sheet/session linkage and pack creation still have crash windows; see `docs/backlog.md`.

No LangGraph checkpointer, storage redesign, per-chat model selection, automatic timeout retry, paid validation, public deployment or OAuth work is included. Real-provider checks remain W5/W6; calibration remains W11. The review baseline is `main` at `6fd4d06`; these fixes are prepared on `fix/review-gaps` for merging back through a PR.

For the implementation details use `docs/agent-and-chat.md`; for the existing recovery controls use `docs/operator.md`; for remaining work use `docs/backlog.md` and `docs/waiting-for-haitham.md`. Earlier report effort estimates and production-ready declarations were unsupported and are removed.
