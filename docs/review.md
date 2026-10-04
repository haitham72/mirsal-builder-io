# Seeded review of Mirsal Builder (single baseline; latest audit 2026-10-04, `fix/review-gaps` @ `6fd4d06`, dirty)

> This is the ONE review file an auditing LLM reads. It consolidates the
> 2026-10-02 audit (with its triage and status-a-day-later table, preserved in
> the appendix) and the 2026-10-03 code audit, and the 2026-10-04 review below
> (§§1-8 live body). History lives in git. A new audit does not create a dated
> file: it reads this file, re-verifies every claim and finding against the
> code, updates the tables in place, and appends a dated entry to the log at
> the end (§9) recording what changed (NEW / fixed / confirmed / refuted).
>
> Method note (owner-directed, 2026-10-03, kept 2026-10-04): a code audit plus
> the approval tests only. The long suites stay off (`mirsal test slow` and full
> `unittest discover` are retired and were never run). 2026-10-04 ran the gated
> approval set on the owner's "do it" (~2 min, inside the 10-minute review
> budget). No provider was reached, no secret opened, no media opened to judge
> it. Branch reviewed: `fix/review-gaps` at `6fd4d06` (dirty: the other
> session's gap fixes in flight — `agent/*`, `console/server.py`,
> `services/llm.py`, docs, plus untracked `tests/test_review_gaps.py`; and this
> review's own `review-prompt.md` maintenance edit).

## 1. Verdict

**Ship with changes — the spine holds and the approval tests are green, but money still has holes and the reviewed state is not committed.** The engine core holds: 44 verifier checks confirmed by running code, ticket-before-wait and price-before-click true on the sheet path, vision `FAIL_CLOSED` true, and the agent/chat core now verifies end to end (spend gating, structured memory, creator crash-resume, edit router, consent-as-state). The three things that decide it: (1) **money is not double-spend safe off the sheet path** — particle/effect routes take no `Idempotency-Key` so a double-click pays twice (BLOCKER, carried from 10-03), and a crash between `hf.create` and `claim` leaves a paid-but-unticketed provider job (HIGH); (2) **the reviewed tree is dirty** — the gap fixes under review (`creator checkpoint`, `creator_job` resume, `summary_structured`, brain focus, LLM budget split, G3 `allow_sheet`) live only in uncommitted edits on `fix/review-gaps`: land them or drop them before any release claim, and the per-surface G3 buttons still need a browser look; (3) **concurrency writes still race** — `allow_animations`, `build_sheet`/`slice_video` and long slicers write unserialized, so parallel human clicks can lose a decision (HIGH, carried). Nothing here says the architecture is wrong; the sonnet report's 10 "gaps" triage to 3 real-and-now-fixed-in-tree, 4 already-built, 2 operator/held items and 1 rejected (§9). Do not call anything verified until the §0 browser look (P1-P13 + particle screens + creator) is done on a scratch copy of `out/`.

## 2. What was run

2026-10-03 (code audit only, per owner):

```
git log --oneline -15 ; git rev-parse --abbrev-ref HEAD ; git rev-parse HEAD ; git status --short  → better_ui/ux, d49ab39, ~36 M + 4 new (job-recovery.js, recovery.py + tests) [RAN]
./venv/bin/python -c "from mirsal.engine import verify; ..."  → 44 total {sheet:6 still:12 slot:3 anim:13 video_sheet:2 video:4 pack:1 telegram:2 telegram_set:1}; OVERRIDABLE still:(blank_cell,foreground,inside_cell,no_spill,holes) animation:(inside_slot,cross_slot,loop_seam) [RAN]
grep -rn "psycopg|redis|langgraph|fastapi|pydantic|openai|anthropic" mirsal/mirsal/engine/  → NO HITS [RAN]
grep -c "read_result|write_result" + grep "@serialized" / grep "ACT\." / grep "data-act" / git ls-files mirsal/out | wc -l  → pipeline:49 gates:39 server:17; 5 fns serialized; 282 ACT defined / 276 data-act used / 0 used-without-handler; out/ 1464 tracked files [RAN]
./venv/bin/python -c "from mirsal.console import openapi; ..."  → 149 ops / 137 paths [RAN]
```

Deliberately not run (owner instruction): `python -m mirsal doctor`, `python -m unittest discover -s tests -t .`, `node --test tests/js/*.test.js`, `python -m tests.test_js`, `mirsal test fast/area/slow`, any spare-port server. Reference counts (~1025 Python / 151 node / 18 test_js) are CANNOT TELL here.

2026-10-02 (for the record; the only suite run to date): `doctor` ready; verifier count 44; `unittest discover` ~350 tests with 2 FAIL; `node --test agent.test.js` 9 pass; spare-port server not attempted (suite hung on `test_jobs` past 5 min).

2026-10-04 (approval tests, owner answered "do it"; `fix/review-gaps` @ `6fd4d06`, dirty as above):

```
doctor  → ready; 1 WARN (migration 011_user_profiles.sql not applied: `python -m mirsal db migrate`); Higgsfield live (3082.12 credits) but tests pin fakes [RAN]
test fast  → 72 ran, 0 skipped, PASS in 12.7s [RAN]
node --test tests/js/*.test.js  → 265 pass, 0 fail [RAN]
tests.test_js  → 18 pass in 0.2s [RAN]
test focused (default profile)  → 22 ran, 0 skipped, PASS in 84.4s (golden gate first) [RAN]
```

Total test time ~2 min, inside the 10-minute review budget. Slow tier + full `unittest discover` never run (retired, never requested). Static counts, not runs: 1239 Python `def test` methods across 99 files (grep), 292 `test(` blocks across 33 node files (grep; runner reports 265), 164 route tuples in `openapi.py` (grep), verifier 44 (ran). The 2026-10-03 reference figures (~1025 Python / 151 node / 149 ops) are stale: the suite, the node tests and the routes all grew.

## 3. Claims C0-C26 (live contract; re-verify every audit)

| # | Verdict | Standing | One-line evidence |
|---|---|---|---|
| C0 44 checks + OVERRIDABLE exact | PARTLY [RAN] | drift NEW 10-04 | catalogue sums to 44 `engine/verify.py:101-109`; but OVERRIDABLE has a third key `video_sheet:(no_outline_on_sheet,video_specs,layout_match)` `verify.py:30-38` that the claim and the docs do not mention (N11) |
| C1 judgement-block allow-able on every surface | PARTLY [READ] | improved 10-04, still open | still/anim allow+waive+reversible `flow/gates.py:335-336,511,635,658`; G3 `allow_sheet` now exists in code `gates.py:477` (was F10); per-surface buttons + bulk empty-state unverified (N-findings) |
| C2 sheet layout never stops sheet | VERIFIED [READ] | confirmed 10-04 | `SHEET_FATAL={sheet_decodes}` / `SHEET_PROCEED={grid_detected,sheet_size}` `flow/pipeline.py:432-433`; layout→WARN per sticker `:468-472`; `background_is_key` one-click `recut` `:507-509` |
| C3 vision never changes review.*, FAIL_CLOSED | VERIFIED [READ] | confirmed 10-04 | `vision/judge.py:398` writes `judge/judge_anim` + hist only; `FAIL_CLOSED` `:90-92`; `JudgeError→UNJUDGED` `:312-315` |
| C4 agent never spends w/o go-ahead; yes scoped | VERIFIED [READ] | strengthened 10-04 | whole-message yes `agent/resolver.py:255-273`; spend gated `graph.py:467-468`, `tools.py:43-45,183,310,464`; the pending-clear asymmetry is a plan-loss bug, not a spend hole (N6) |
| C5 particles/bursts priced; cap counts in-flight; ticket first | PARTLY [READ] | confirmed open 10-04 | price-first + inflight + ticket `generation/jobs.py:373,467,469`; BUT particle/effect routes take no idem key (N1), `approved_cost` only on Retry (N3), `_inflight` undercounts (N17) |
| C6 engine import-clean; test would catch | PARTLY [RAN+READ] | weakness persists 10-04 | code clean today (grep NO HITS for psycopg/redis/langgraph/fastapi/pydantic/starlette/uvicorn); test `tests/test_store.py:220-224` imports 2 of 13 engine modules, 6 names (N10) |
| C7 append-only history; S# stable; put refuses overwrite | PARTLY [READ] | confirmed 10-04 | `hist` append-only `flow/pipeline.py:401-404`; S# by position; `put` refuses different bytes `store/assets.py:66-72`; BUT `sheet_fixed` still write-only (N7) |
| C8 one writer of result.json | PARTLY [RAN+READ] | admitted gap, widened 10-04 | `_IO_LOCK` + `@serialized` on some fns; BUT `allow_animations`, `build_sheet`, `slice_video`, `reanimate_prepared` unserialized; ~110 RMW sites (`pipeline:50 gates:42 server:18`) |
| C9 foreign page cannot drive server; /out/ cannot escape; member isolation | PARTLY [READ] | guards real, vectors untested 10-04 | `_foreign`/`_who`/`_authorize` + `/out/` resolve-check `console/server.py:739,757,777,1177`; ADS/short-name/drive forms untested (LOW) |
| C10 secrets never returned/logged; trace sends no media/paths | PARTLY [READ] | gaps persist 10-04 | token/key scrub on main paths; BUT ticket `context` stored unscrubbed, Telegram URL embeds raw token in transport errors (LOWs) |
| C11 idempotency incl. concurrent | PARTLY [READ] | confirmed 10-04 | sequential replay true `server.py:496-519`; concurrent dup → 409 "still running", not first answer |
| C12 Redis disposable; fallback same semantics | PARTLY [READ] | overstatement persists 10-04 | fallback exists `runtime/cache.py:67`; memory semantics per-process, lock TTL 300s diverges without Redis |
| C13 memory structured not history | VERIFIED [READ] | strengthened 10-04 | subjects/feedback/focus + `summary_structured`/`focus_context` on disk `agent/memory.py:332-350`; TEMPORARY consumed once; `_cap`/`reduce` never drop ids; `context()` has zero callers (N8, docs wart not data bug) |
| C14 model text never trusted as HTML/instruction | VERIFIED [READ] | confirmed 10-04 | `esc`+`md` `console/agent.js:6-8,156`; `DATA_RULE`+`fence()` `services/llm.py:61-72`; intent/number whitelists `agent/brain.py:160-166` |
| C15 verifier crash→BLOCK verifier_error; fixtures | VERIFIED [RAN] | confirmed 10-04 | `except→BLOCK verifier_error` never waived `engine/verify.py:159-186,129,153`; thresholds with measured comments `engine/config.py:44-60`; `holes` WARN-vs-BLOCK severity lie is a catalogue wart (N12) |
| C16 migrations re-runnable, never wipe | PARTLY [READ] | new wart 10-04 | re-runnable `001_init.sql:2`, `005_vectors.sql:5`; BUT 005 upgrade path does `USING NULL`, wiping stored vectors |
| C17 pool never returns closest junk; search_text never filename | VERIFIED [READ] | confirmed 10-04 | gate + no-filename text + split subject/action vectors `store/pool.py:68,171,187,215` |
| C18 creator can always get past a block | VERIFIED [READ] | hardened 10-04 | `_stop_blocked` + `allowable` `agent/creator.py:77-92`; checkpoint + `creator_job` resume wired `:124-163,219-235`, `graph.py:510-511`; `waiting` card without picture is the remaining wart (N9) |
| C19 particle model matches plan | VERIFIED [READ] | confirmed 10-04 | sticker-owned sets, one row/version per set, explicit save, append-only more, trash/restore `flow/particle_sets.py:902,1274,1312,1329,1398,1416` |
| C20 cropped sprites not stickers; edit rebuilds one sheet same S# | PARTLY [READ] | confirmed 10-04 | crop true; pack-add refusal + `sheet_fixed` S# carry not proven on read surfaces; recut never reads `sheet_fixed` (N7) |
| C21 edit router classifies before generating | VERIFIED [READ] | confirmed 10-04 | redesign/action/tweak/editor + unsupported + `REF_CLAUSES` `agent/editroute.py:119-153,157-190`; 400px min said aloud; no-target tweak → whole-sheet, documented `docs/agent-and-chat.md:377-382` |
| C22 vision consent is state never turn | VERIFIED [READ] | confirmed 10-04 | `set_vision` no message/card/turn `agent/memory.py:323-330`; first-answer Create + glowing switch `graph.py:1789-1810`; toggle silent |
| C23 one click one meaning; sheet never opens; id never in name | VERIFIED [READ] | confirmed 10-04 | one `ACT.gcell` via `cellOp` (`generate.js:93,692`); `issueSvg` rects only `data-act=gcell` `:139-151`; id separate copy chip |
| C24 no dead stubs; guard covers handlers | PARTLY [READ+RAN] | narrowed 10-04 | 0 used-without-handler on disk; BUT permanent disabled search input in `chat.js:14` (dead stub); guard proves button→handler only |
| C25 doctor is the single check, every area extends it | PARTLY [READ+RAN] | confirmed 10-04 | `doctor` ready 10-04 (1 WARN: migration 011); particle-sets/recovery/effects/tickets uncovered |
| C26 API contract stable + honestly documented | PARTLY [READ] | confirmed 10-04 | 164 route tuples served (grep); drift vs `docs/api.md` / `http_route_inventory.md` not diffed; FastAPI adapter boundary holds, native routes do ad-hoc role checks (LOW) |

## 4. Findings (most severe first; cap 25)

### N1 — Particle/effect double-spend: no Idempotency-Key [BLOCKER, READ]
Where: `mirsal/mirsal/console/server.py:496,1613,1645,1699,1729`; contrast chat/live/generations which are wrapped. What: `more`, effects video/particles take 409-price but no key; two rapid `go:true` clicks / two tabs mint two `jobs.create` and `fulfil` charges per job. Standing: CONFIRMED still open (10-03 F1). Fix: wrap particle/effect creations in `c.idem()` with scope `f"particles:{kind}:{plan-id}:{digest(...)}"`. Pin: two same-key `more/go` assert one job.
(Note for the fixer: the other session's in-flight diff does not touch this.)

### N2 — Crash between `hf.create` and `claim` loses a paid ticket [HIGH, READ]
Where: `mirsal/mirsal/generation/jobs.py:469-470`. What: provider job exists and will charge, file has no `external_task_id`, only path is a fresh paid `retry`. Standing: CONFIRMED still open (10-03 F5). Fix: write a `creating` marker before `hf.create`, clear at `claim`; reconcile surfaces markers older than N min. Pin: fake `create` dying pre-claim → marker exposed, re-`fulfil` refuses silent re-create.

### N3 — Shown price can drift before the charge; only Retry pinned [HIGH, READ]
Where: quote `console/server.py:383`-area live paths never set `approved_cost`; guard `generation/jobs.py:464` fires only when retry set it (`generation/recovery.py:109`). What: provider reprice between estimate and `go:true` charges an unapproved number. Standing: CONFIRMED still open (10-03 F6). Fix: store quote as `approved_cost` at go-time on ALL paid paths. Pin: live job with changed estimate → 409, zero `create`.

### N4 — `allow_animations` unserialized; concurrent allows lose one [HIGH, READ]
Where: `mirsal/mirsal/flow/gates.py:658` vs serialised `:105,476,634,934`. What: concurrent still+anim allows interleave RMW; second write drops first. Standing: CONFIRMED still open (10-03 F7). Fix: add `@pl.serialized` to `allow_animations` (+`allow_cells`). Pin: two-thread still+anim test asserting both overrides survive.

### N5 — `build_sheet` / `slice_video` / `reanimate_prepared` unserialized [HIGH, READ]
Where: `mirsal/mirsal/flow/gates.py:247,789,710`. What: multi-step read/write without `@serialized`; same lost-update window as N4 for G3/G4, plus long slicers overwrite mid-slice human reviews (10-03 F8). Standing: CONFIRMED, widened 10-04. Fix: add `@pl.serialized`, or hold `_IO_LOCK` for the job / re-read+merge per cell write. Pin: start `slice_video` on fakes, inject `review` mid-run, assert survival.

### N6 — `n_confirm` clears pending before success; failed non-create loses plan [HIGH, READ]
Where: `mirsal/mirsal/agent/graph.py:583` vs create/multi keep-plan branches. What: refused/failed animate (creator/describe/particles/batch too) loses the plan the person approved. Standing: CONFIRMED still open (10-03 F15). Fix: clear-after-success for all, restore on ToolError. Pin: FakeTools animate raises → pending retained.

### N7 — `sheet_fixed` is write-only; later recut silently reverts edits [MEDIUM, READ]
Where: writer `flow/pipeline.py:852-880`; readers `recut`/`recut_cells`/`run_stills` read `sheet_copy`/grid rects only. What: "Cut it anyway"/recut after a Studio edit reverts to the unedited sheet. Standing: CONFIRMED still open (10-03 F13). Fix: `recut`/`recut_cells` prefer `sheet_fixed` when present + `source.sheet_from` history, or refuse recut-after-edit with 409. Pin: edit S1 → recut → edited pixels survive, S# unchanged.

### N8 — `SessionStore.context()` has zero callers; HIGH path never runs [MEDIUM, RAN]
Where: `mirsal/mirsal/agent/memory.py:387` (grep: no callers). What: docstring claims it is "what a model sees", but nothing calls it — the HIGH/prompts lineage path is dead documentation. Standing: NEW 10-04. Fix: call it from the brain path or delete it and fix the docstring. Pin: assert `brain.classify` receives the HIGH focus card, or assert the method is gone.

### N9 — Creator `waiting` card carries no picture [MEDIUM, READ]
Where: `mirsal/mirsal/agent/graph.py:521-535,478-494`. What: `_creator_say` attaches the generation carousel only on `stopped` non-error; G2/G4 approval (`waiting`) asks without pictures in-message. Standing: CONFIRMED still open (10-03 F24). Fix: append the generation card for `waiting` at approve gates too. Pin: waiting creator message contains a generation card.

### N10 — Engine boundary test would not catch a violation [MEDIUM, READ+RAN]
Where: `mirsal/tests/test_store.py:220-224` (same shape `test_engine.py:82-86`). What: imports only 2 of 13 engine modules, checks 6 names (misses starlette/uvicorn/openai/model clients). A banned import in grid/config/chroma would pass. Standing: CONFIRMED still open (10-03 F20). Fix: subprocess-import every `mirsal.engine.*`, assert full banned list. Pin: synthetic `import fastapi` in grid.py fails red/green.

### N11 — OVERRIDABLE third key undocumented; C0 claim stale [MEDIUM, READ]
Where: `mirsal/mirsal/engine/verify.py:30-38` vs C0 row and `docs/engine-and-studio.md`. What: `video_sheet:(no_outline_on_sheet,video_specs,layout_match)` exists in code (the in-flight G3 fix) but the claim says still+animation only. Standing: NEW 10-04 (fix in dirty tree, docs not updated). Fix: update C0 + area doc, or remove the key. Pin: assert `set(OVERRIDABLE)=={still,animation,video_sheet}`.

### N12 — `holes` registered WARN but returns BLOCK [MEDIUM, READ]
Where: `mirsal/mirsal/engine/verify.py:359,365-366`. What: catalogue severity lies; `_blocks`/allow logic downstream depends on stored severity. Standing: NEW 10-04. Fix: register as BLOCK with dynamic downgrade, or split `holes`/`holes_severe`. Pin: fixture asserts the BLOCK case has severity BLOCK.

### N13 — Ticket fingerprint folds unrelated failures [MEDIUM, READ]
Where: `mirsal/mirsal/flow/tickets.py:82-85,100-115`. What: blanks digits/hex/quotes, ignores user/batch — two batches failing with the same message share one ticket and `count++` loses identity. Standing: NEW 10-04. Fix: include issue+user in the fingerprint, or keep per-occurrence list. Pin: two batches, same message → two tickets or both ids in context.

### N14 — Migration 005 upgrade wipes stored vectors [MEDIUM, READ]
Where: `mirsal/migrations/005_vectors.sql:10-12` (`USING NULL` + `embed_model='none'`). What: re-runnable, but first-apply over seeded vectors clears them; `pool reindex` refills only if run. Standing: NEW 10-04. Fix: cast/keep values, backfill only NULLs. Pin: apply 005 over seeded vectors → retained.

### N15 — Tracing/ticket sinks bypass `safe()` [MEDIUM, READ]
Where: `mirsal/mirsal/obs/trace.py` `end()`/`feedback()` ship `error`/`comment` raw; `flow/tickets.py:102,135` stores `context` dict unscrubbed. What: a pasted path / wrapped OSError leaves the machine in a ticket or trace. Standing: CONFIRMED, widened to tickets 10-04 (10-03 F12). Fix: `safe()` both sinks + scrub context values / drop path keys. Pin: report with absolute path → stored ticket shows `<path>/`.

### N16 — Concurrent identical Idempotency-Keys get 409, not the first answer [MEDIUM, READ]
Where: `mirsal/mirsal/console/server.py:496-519`. What: second caller must special-case 409; the claim promises the first answer. Standing: CONFIRMED still open (10-03 F11). Fix: document 409-then-replay, or park waiter until winner finishes. Pin: two threads, same key, slow fn → one run, identical bodies.

### N17 — `_inflight` undercounts the daily cap [MEDIUM, READ]
Where: `mirsal/mirsal/generation/jobs.py:373-384`. What: counts only CLAIMED/TIMEOUT with ticket + `cost_estimate`; REQUESTED/enqueued and `estimate=None` jobs are invisible to the cap. Standing: NEW 10-04. Fix: count reserved/estimate at enqueue too. Pin: N enqueued jobs → cap sees all.

### N18 — `_slot` semaphore is per-process; queue workers exceed `paid_parallel` [MEDIUM, READ+INFER]
Where: `mirsal/mirsal/generation/jobs.py:329,388`. What: file-lock covers creation but not the wait slots, so N queue workers can wait more than `paid_parallel` jobs at once. Standing: NEW 10-04 [INFER for the cross-process interleaving; confirm with two workers]. Fix: shared slot count, or force 1-wide creation in queue mode. Pin: two workers, parallel=1 → second gets JobBusy.

### N19 — Docs contradict code on sheet-cell open [MEDIUM, READ]
Where: `docs/design.md:217,223` ("opens the tile") vs `:249` ("never opens") vs code (never-opens, `generate.js:139-151`). Standing: CONFIRMED still open (10-03 F23). Fix: delete one rule, keep the code one. Pin: `grep -n "opens the tile" docs/design.md` hits once.

### N20 — Permanent dead search input in chat [MEDIUM, READ]
Where: `mirsal/mirsal/console/chat.js:14` (`<input type=search ... disabled>`). What: a permanently disabled control with no backend violates C24. Standing: NEW 10-04. Fix: wire to chat-list filter or delete it. Pin: `test_js.py` asserts no disabled search input in `chat.js`.

### N21 — Polling/video element leaks [MEDIUM, READ]
Where: `live.js:179,180,186,190,262,280`, `particles.js:159`, `history.js:35` (~8 global `setInterval` never cleared); `generate.js:186` vs `:194` (`gbdrop` does not clear `PVS` videos, `pvEnsure :29-31` leaks one hidden `<video>` per dropped batch). Standing: NEW 10-04. Fix: gate intervals on route/`document.hidden`, clear on route change; clear `PVS` in `gbdrop`. Pin: no-op-when-hidden assert; video-count-after-drop assert.

Fixed since 10-03 (do not re-raise): F4 `/ui/job-recovery.js` servability (`UI_FILES server.py:33` now lists it [RAN]); F10 G3 allow in code (`allow_sheet gates.py:477`, OVERRIDABLE `video_sheet`, `test_sheet_allow` + untracked `test_review_gaps.py` in tree — per-surface buttons still need the browser look).

Carried without re-verification 10-04 (not findings of this audit, still open): READY-but-unapproved reaches pack/Telegram (F2); edit keeps APPROVED verdict (F3); settings route without session lock (F9); focus.stickers seeding (F16); 5-min lock outliving dead server (F17); `max(id)+1` chat reuse (F18); sharpness WARN-only (F21); `DUP_SIM` dead constant (F22).

## 5. What is solid (protect from "cleanups")

- Verifier single-table design (`OVERRIDABLE` vs `TECHNICAL`, `verifier_error` never waived) + `SHEET_PROCEED` cut-anyway + one-click `recut`.
- Ticket-first (`jobs.py:5-6,408-409`), priced-plan-card + whole-message yes (`resolver.py:255-273`), `_may_spend` 403 (`tools.py:43-45`), `FAIL_CLOSED` judge, `put`-refuses-overwrite, `ON CONFLICT DO NOTHING` history.
- Waiver single-path (`verify._apply_waiver` + `animation_verdict` + `gates._remember/_restore/_materialize`, `ok=False` + WARN "(allowed by you)").
- 409-busy discipline (`paid_parallel` default 3 with wait outside lock, idempotent retry same replacement).
- `assets._clean`, atomic temp-file writes, `WriterLock` cross-process, `esc()` posture + `DATA_RULE`/`fence()`.
- Particle-set model itself (sticker-owned, one row/version per set, append-only settle, trash+restore same id, FAILED-iff-Telegram-limit).
- NEW 10-04, in the dirty tree (land them, do not "clean" them): creator `checkpoint` + `creator_job` resume, `summary_structured`/`focus_context`, brain focus fence, LLM auto budget-split, G3 `allow_sheet` + OVERRIDABLE `video_sheet`, interrupt trace note.
- The 10-minute approval loop itself (`doctor` + `fast` + node + `test_js` + one `focused`): green 10-04 in ~2 min, and the retired tiers staying retired.

## 6. Missing: tests, docs, features a v1 needs that nobody listed

- Tests: same-key concurrent idem; G3-allow per-surface buttons; READY+PENDING→pack 409; approve→edit→reset; settings-vs-turn race; `hf.create`→crash marker; price-drift 409; evil-path table (ADS/drive/short-name); ticket-context scrub; `sheet_fixed`-preferred-by-recut; engine-boundary red/green; focus-fence S7-S9 survival; 2x2 bulk-review size. The five to name: (1) particle double-click billing, (2) pack/Telegram gate on `review`, (3) edit resets verdict, (4) creating-marker reconcile, (5) price-approved-at-click enforced at `fulfil`.
- LOW one-liners 10-04: `unsupported()` misses number-words ("three packs"); bulk-review hardcodes batch size 9; `delete` takes no session lock; `n_animate` quotes static "8 credits"; focus fence truncates to 3 items; native routes do ad-hoc role checks instead of `_authorize`; Telegram URL embeds raw token in transport errors; ticket drafts local-only; `store/idem.py` degrades silently without Postgres; auto tickets (`user=None`) invisible to members; inline `font-size` off token scale (self-admitted in backlog); creator bulk-pair empty-state undocumented; burst `add` has no use-anyway for warning-level FAILED.
- Docs: `docs/design.md` §9 (sheet-open contradiction + bulk-pair empty state); C0 claim vs OVERRIDABLE third key; `context()` docstring vs zero callers; `docs/api.md` allow `kind` incl. `video_sheet` + `/api/v1` alias + tracing headers.
- Features: trash purge; particle Telegram delivery; burst creation only after Haitham §6 answers; backup command for `out/`; Arabic prompt handling; `Deprecation` header policy.

## 7. Decisions challenged (standing; do not re-raise until asked)

- Paused deployment + OAuth: respected. The FastAPI migration is DONE (`console/app.py` adapter, byte-identical) — judge the boundary, not the decision.
- "Never open media to judge it": respected. Leaves welcome-film spelling, tile art, loop-dissolve ghost, softness threshold to Haitham's eyes; numbers don't replace the browser look.
- OpenAI-without-plan-card + content-safety + `out/`-in-git: held questions, recorded only to keep the ledger honest.
- "Make it happier" no-sticker → whole-sheet tweak: defensible (bare mood = sheet-level direction), documented (`docs/agent-and-chat.md:377-382`).
- "Screens are a sandbox" (rule 11): right call; risk is logic leaking into `console/` — enforce by lint, not by review repetition.
- Particle separator auto-removal (sonnet GAP 8): REJECTED — numpy grey-line interpolation risks destroying cells and breaks rule 9; keep cut-again-as-particles / editor path. Do not build.
- Vision `calibrate.py` (sonnet GAP 5/10): NOT a code task — it needs 30 human labels first (W11). Do not build unasked.

## 8. The ten changes first, in order

1. Wrap particle/effect paid routes in `c.idem()` (N1) — S.
2. `creating` marker + reconcile; `approved_cost` on every sheet/video job + enforce at `fulfil` (N2+N3) — M.
3. `@pl.serialized` on `allow_animations`/`allow_cells`/`build_sheet`/`slice_video`/`reanimate_prepared`, or hold `_IO_LOCK` in long slicers (N4+N5) — S/M.
4. Clear-pending-after-success for all confirm paths (N6); session lock around settings route (carried F9) — S.
5. Land the dirty tree: creator checkpoint/`creator_job`, `summary_structured`, brain focus, LLM budget split, G3 `allow_sheet` + per-surface buttons + bulk + docs (N11, N9) — M. One commit per phase, explicit paths.
6. `recut`/`recut_cells` prefer `sheet_fixed` (+ `sheet_from` history) or downgrade docs (N7) — S/M.
7. `safe()` at `trace.end`/`feedback` + scrub ticket context + token out of Telegram URLs (N15) — S.
8. Evil-path rejections + Windows-gated table; fix `design.md` §9 contradiction; wire or delete chat search (N19+N20) — S.
9. Fix 005 upgrade to keep vectors; include user/batch in ticket fingerprint; `recut`-side C0/docs update for `video_sheet` (N14+N13+N11) — S.
10. Engine-boundary red/green test; doctor lines for particles/tickets/recovery; seed `focus.stickers` from latest gen (N10, carried F25/F16) — S/M.

## Appendix A — 2026-10-02 triage ledger (preserved; statuses resolved 10-03)

| 10-02 item | Triage verdict | Standing now |
|---|---|---|
| F1 OpenAI without price | real, Haitham's decision | still a held decision (HANDOFF) |
| F2 `result.json` race | real, fixed (`pipeline.serialized`) | fixed; wider unserialized instances found 10-03 (F7/F8) |
| F3 `test_jobs.py` hangs | not reproduced | suite runs; one ordering flake recorded in HANDOFF |
| F4 ResourceWarnings | real, cosmetic | open |
| F5/F6/F13 stray text | false (fragments not in files) | closed |
| F7 no content-safety reason | real, decision | still held (HANDOFF) |
| F8 health returns Redis URL | false | closed |
| F9 members list every job | false (route filters by user) | closed for the single route; list scope stays LOW-open |
| F10 409-vs-404 timing | false | closed |
| F11 no `Deprecation` header | real, policy | open (contract polish) |
| F12 double click on Generate | cosmetic (idem-key harmless) | closed on sheet path; particle paths are the live variant (F1) |
| 10-02 top-10 recs 1-10 | 1,4 done; 2,6,7 still decisions; 3,5 not reproduced; 8 superseded (CLAUDE.md is the index); 9,10 open | see §6/§8 for what remains |

## 9. Audit log (append a dated entry per audit; never rewrite history)

- **2026-10-02** (`c67dea1`): first full audit. Verdict: ship with changes. 44 checks confirmed; suite ~350 tests 2 FAIL; 13 findings (F1-F13); triage above.
- **2026-10-03** (`d49ab39`, `better_ui/ux`, dirty): code audit only, no suites run (owner instruction). 6 parallel read-only tracks; claims extended C0-C26; 25 findings + one-liners (this file's §§3-4). Prompt updated with subagent split (§3.5) and gated long tests; glossary headers added to HANDOFF/plan/README.
- **2026-10-04** (`6fd4d06`, `fix/review-gaps`, dirty): audit + approval tests (owner said "do it"; ~2 min, inside the 10-minute review budget). 4 parallel read-only tracks (engine / agent-chat-vision / money+API+data / frontend-docs) + reviewer RAN probes. Verdict delta: C4→VERIFIED, C13/C18 strengthened, C0→PARTLY (video_sheet key drift), C16→PARTLY (005 wipe); fixed: F4 servability, F10 in code (surfaces pending); still open: N1 BLOCKER + N2-N6 HIGH. Triaged the sonnet report (`report-claude-3.5-sonnet.md`): 3 of its 10 gaps were real and are fixed in the dirty tree (creator checkpoint, brain focus, structured summary), 4 were already built (timeout-resume UI, LLM fallback shape, trace persistence shape, multi-ref roles), 2 are operator/held items (judge calibration W11, no model-built traits), 1 rejected (separator auto-removal). Prompt maintained in the same session: FastAPI-migration-done updates, grown-code file lists (97 Python test files, 33 node files, 164 routes), 10-minute approval-test budget with stop-rules, stale counts refreshed. Test totals: doctor ready (1 WARN: migration 011), fast 72 PASS, node 265 PASS, test_js 18 PASS, focused-default 22 PASS.
