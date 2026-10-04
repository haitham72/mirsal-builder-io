# Testing: which tier, and when

> **Retired by Haitham, 2026-10-03: the slow tier is never run and never requested.** (Haitham: "this suite test must be stopped and never requested again, it is a joke of a test".) No agent runs it, no doc requires it, nothing is gated on it, and full `unittest discover` is also retired: never run or requested. The routine loop is `mirsal test fast`, `mirsal test focused`, `mirsal test area <module>`, the node tests and `python -m tests.test_js`. An old command remaining in code is not authorization to run it. It was Tier 3 and a "required media gate"; it existed to prove the Telegram rejection limits end to end, and that role is gone.

## The test budget (Haitham, 2026-10-04: overrides anything below that asks for more)

Tests are a small part of a session, not most of it. These tests have passed hundreds of times; re-running them proves nothing new.

1. **One run per change, the narrowest one.** Run the single test you wrote or touched by name (`venv/bin/python -m unittest tests.test_x.Class.test_y`). If you need more, run the one command the changed file maps to (`mirsal test area <module>`; for console `*.js`/`*.css`: `python -m tests.test_js` plus that script's own `tests/js/<name>.test.js`). Never stack fast + area + focused + node + openapi for one change.
2. **A pass stays valid.** A test that passed in this session, or at the last commit, is not run again unless a file it covers changed since. Do not re-run "to be sure", before a commit, after a doc edit, or at the start of a session to "check the baseline".
3. **Docs, trackers, comments, prose: zero tests.**
4. **`focused` is never automatic.** Run it at most once, at the end of a phase that changed gate, recovery or video-sheet code, or when Haitham asks. Never per edit and never "because the change is a route".
5. **A failure outside your change:** report it in one line (`still unknown:`) and keep working. Do not open a fix-and-rerun loop on a suite you did not touch.
6. **Browser checks:** once at the end of a phase, on a scratch copy; never after each edit.
7. **If testing is taking more time than building, stop testing and continue the task.** Say what is still unknown instead.

The map from a changed file to the tests that could be affected is **code**, not prose:
`mirsal/test_tiers.py` (`MODULE_TESTS`, `FOCUSED_PROFILES`, `FAST_TESTS`; `SLOW_MODULES` stays only for the retired command), reached through
`python -m mirsal test <tier>`. It refuses to guess: an area it does not know fails and
prints the keys it does know. This file is the **policy** — which tier a change earns, and
what makes a tier mandatory rather than optional.

## The map has two layers, and the difference matters

1. **Hand-picked areas** (`MODULE_TESTS`) — the six where judgement was applied: which specific
   *classes* matter, not merely which files mention it. These win.
2. **A derived floor** (`derived_map()`) — every other module, mapped to the test files that
   **import it directly**, parsed from the tests' own ASTs, so it is true as tests are added.
   157 areas today: `engine/config` reaches 32 test modules, `generation/higgsfield` 9,
   `agent/tools` 6, `store/pool` 1.

**The derived layer is a floor, never a ceiling.** It sees direct imports only, so a test that
reaches production code over HTTP without importing it is **invisible to it** — that is exactly
why layer 1 exists. Read a derived area as *"these tests certainly touch this file"*, never as
*"nothing else does"*. A module no test imports maps to nothing, and the correct answer there
is to ask, not to run the suite.

## The rule

> **Run what `mirsal test` says a changed file earns. If it maps to nothing, run nothing.**

Verification is a function of **blast radius**, not of caution. Most changes are a chip, a
string, one function: their whole test plan is under a second. The full suite is not a gate
and full discovery is retired: never run or requested.

Two clauses make this enforceable rather than aspirational:

1. **Uncertainty is not a reason to run a bigger suite (and the slow tier is retired).** It is a reason to run the cheapest
   tier that touches the file, and to *say what is still unknown* in the report. Without this
   clause the rule has a hole exactly the size of over-testing.
2. **A green run that skipped something must never read as green.** `mirsal test` prints the
   count it ran *and* the count it skipped. If you cannot tell what was verified,
   it was not verified. (`doctor` no longer asks for a slow-tier run: its line says the tier is retired.)

## The tiers

| tier | command | cost | what it is |
|---|---|---|---|
| fast | `python -m mirsal test fast` | **9s** (72 tests, measured 2026-10-03) | a small deterministic smoke set. **It does not verify the app** and never says so |
| focused | `python -m mirsal test focused [animation\|recovery\|video-sheet]` | **86s measured**; the exact golden gate dominates | 22 Python regression cases by default, including the full node suite as one wrapper; narrower named profiles print their actual count |
| area | `python -m mirsal test area engine/video` | seconds–a minute | exactly the classes that import what you changed |
| ~~slow~~ | ~~`python -m mirsal test slow`~~ | ~15–20 min | **RETIRED (Haitham, 2026-10-03).** Never run, never requested; a remaining legacy command must not be run |
| ~~all~~ | ~~`python -m unittest discover -s tests -t .`~~ | ~17 min | **RETIRED (Haitham, 2026-10-03).** Never run or requested; coverage remains available through mapped/named tests |

The six modules the retired slow tier ran (`tests.test_golden`, `test_effect_video`,
`test_allow_still`, `test_anim_speed`, `test_engine`, `test_verify`) are still ordinary test
modules: they run through `mirsal test area <module>`, named modules or `focused` whenever a
changed file maps to them. Only the "mandatory gate" and the doctor freshness stamp are retired.

**Python runs ALONE** (Haitham's current instruction). Parallel runs can collide and return `409 busy`; never start a second Python test run while another is active.

**Focused tier (Haitham approved, 2026-10-03).** This is an explicit, reviewed regression selection, not deleted coverage or the first 20 tests of a larger suite. The default runs 22 cases: the exact item-0 golden test first, six stored-verdict/crash/waiver regressions, six recovery tests, seven video-sheet/creator/HTTP tests, the allow-body contract test and the node-suite wrapper. Every named profile includes the exact golden gate and stops on its first failure. No green claim is possible if that gate fails. Counts include the node wrapper once, not each of its individual JS cases. Add a relevant profile for a new area rather than assuming these cases cover unrelated purge/storage work.

Focused success is not a claim that the whole app was tested: the report says what it ran and what is still unknown. There is no freshness stamp any more. Focused is never automatic (budget rule 4).

## Which run a change earns (one, per the budget above)

| trigger | the one run |
|---|---|
| docs, trackers, comments, prose | nothing |
| a fix or a new behavior | the one test you wrote, by name |
| any other Python change | `mirsal test area <module>` of the changed file; if it maps to nothing, nothing |
| a change to a route, a request body or a response | `tests.test_openapi` (the drift guard) and the test of that route, by name |
| a change to `console/*.css` or `*.js` | `python -m tests.test_js` (0.2s) and that script's own node file |
| end of a phase that changed gate, recovery or video-sheet code | `mirsal test focused [profile]`, once |
| before a commit, a push, a browser look or a Telegram send | nothing extra: what already passed stays valid |
| before anyone says the app is "verified" | Haitham's own browser look (`docs/waiting-for-haitham.md`, item 1); no test run is part of that bar |

## The rule that ends a change

Every change states its boundary in one line before it is called done:

```
changed console/agent.css  ->  tests.test_js (0.2s)
guards every data-act has a handler, agent.css namespacing, the shell rules.
A CSS selector cannot reach the encoder, the pipeline, the database or the contract.
```

That line is the checkable artefact: Haitham can agree or refuse the boundary in five
seconds, instead of discovering the cost afterwards. If an agent cannot finish that sentence,
the scope is not understood yet.

## Test files added on 2026-10-03 (mapped/named modules; node files in `tests/js`)

| file | what it guards | tier it belongs to |
|---|---|---|
| `tests/test_verify_fixtures.py` | the PASS / FAIL fixture table over `verify.CATALOGUE`: every one of the 44 checks has a case that passes and a case that fails (a check never seen to fail proves nothing); `tests/test_verify_gaps.py` is the ratchet that names unnamed checks | the named module or derived area of `engine/verify` |
| `tests/test_purge.py` | the trash purge: Delete pack is soft, `GET /api/trash` shows exactly what a purge removes, the shared-sticker refusals, "delete all" and its typed phrase, idempotent re-run (`flow/purge.py`, `store/purge_rows.py`) | the named module or derived area of `flow/purge` (not in a focused profile yet: add one before relying on it) |
| `tests/test_chat_resolver_fixes.py` | the chat resolver and edits: a bare person reference is the last subject, `last` is an ordinal only as an ordinal, an edit reuses the parent prompt, undo, "number 12 in a batch of 9", "don't ask me about vision again" | the named module or derived area of `agent/resolver` |
| `tests/test_job_recovery.py`, `tests/test_sheet_allow.py` | stalled-job recovery and the G3 video-sheet override | the focused profiles `recovery` and `video-sheet` where they are named there; otherwise the named module/mapped area |
| `tests/js/trash.test.js`, `job_recovery.test.js`, `sheet_recovery.test.js`, `sheet_size_chip.test.js`, `prompt_step.test.js` | the pure builders of the console scripts of the same names | `python -m tests.test_js` + the node suite |

## Test files added for v1.0 (2026-10-04)

| file | what it guards |
|---|---|
| `tests/test_chat_stream.py` | the chat SSE route: turn events then done, the session route's access |
| `tests/test_tickets.py` | fingerprint folding, Report context, answers, the model draft validated, the routes, a 500 opens a ticket |
| `tests/test_accounts.py` | sign-up / approval / sessions / LAN owner rule, the admin bot's taps (fake Telegram), the routes |
| `tests/test_credits.py` | reserve, settle on the real cost, refund on failure, 402 when short |
| `tests/test_trending.py` | share, likes, comments, orders, private files, Use in my workflow, the routes |
| `tests/test_groups.py`, `tests/test_particle_rows.py` | batch families; particle rows, adopt, drawn sheets |
| `tests/js/tickets.test.js`, `auth.test.js`, `anim_create.test.js` | the screens' pure builders |

The contract suites (`test_api_contract`, `test_openapi`, `test_hardening`, `test_live`) run on FastAPI by default; `MIRSAL_SERVER=stdlib` runs them on the old server.

## Worked scenarios

**A button layout, a chip, a CSS rule.** Blast radius: the shell guards. Run
`python -m tests.test_js` — 18 tests, 0.17s, and it genuinely catches the two real risks
(a `data-act` with no handler, a colliding class name). **Not** the suite: a selector cannot
reach the encoder.

**A new `data-act` in the chat.** Same, plus the node suite (159 tests, ~2s), because
`tests/test_js.py` guards the shared `ACT` object and duplicate top-level `const`s across the
console scripts.

**`mirsal/mirsal/generation/jobs.py`.** Blast radius: the spend path. `mirsal test area
generation/jobs` — and note `engine.config` is imported by 31 test classes, so a change to
`engine/config.py` is the widest in the repo and earns `area` on nearly everything.

**`mirsal/mirsal/engine/video.py`.** The encoder. `area engine/video` maps to 12 classes;
that is the tier it earns (the slow tier is retired).

**"Hi."** No file changed, nothing maps, **nothing runs**. This is the case the rule exists
for.

**A docs-only edit.** No test. Say so in the report rather than running something to look
diligent.

## What is NOT verified by watching the app work

Haitham has seen an encode finish in seconds in the live app. That proves a file was
produced. It does **not** prove the file is ≤256 KB, ≤3 s, ≤30 fps, VP9 with real alpha, no
audio, or that the loop seam closes. Those are Telegram's rejection criteria; the verifier (`engine/verify.py`) checks them on
every file at runtime, and a clip can encode in two seconds and still be refused on upload.
"Verified" means Haitham's own browser look; the retired slow tier is no part of it.

## Reporting

```
changed <file(s)>  ->  <tier / command> (<count> tests, <seconds>)
not run: <tier> because <reason>
still unknown: <the thing nobody checked>
```

The third line is what keeps clause 1 honest. A report that never has one is hiding an
assumption.
