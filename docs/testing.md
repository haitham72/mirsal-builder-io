# Testing: which tier, and when

The map from a changed file to the tests that could be affected is **code**, not prose:
`mirsal/test_tiers.py` (`MODULE_TESTS`, `SLOW_MODULES`, `FAST_TESTS`), reached through
`python -m mirsal test <tier>`. It refuses to guess: an area it does not know fails and
prints the keys it does know. This file is the **policy** — which tier a change earns, and
what makes a tier mandatory rather than optional.

## The rule

> **Run what `mirsal test` says a changed file earns. If it maps to nothing, run nothing.**

Verification is a function of **blast radius**, not of caution. Most changes are a chip, a
string, one function: their whole test plan is under a second. The full suite is a
**milestone**, deliberately scheduled — not the default answer to "am I done?".

Two clauses make this enforceable rather than aspirational:

1. **Uncertainty is not a reason to run the slow tier.** It is a reason to run the cheapest
   tier that touches the file, and to *say what is still unknown* in the report. Without this
   clause the rule has a hole exactly the size of over-testing.
2. **A green run that skipped something must never read as green.** `mirsal test` prints the
   count it ran *and* the count it skipped; `doctor` reports whether the slow tier has been
   run since the last change under `mirsal/engine/`. If you cannot tell what was verified,
   it was not verified.

## The tiers

| tier | command | cost | what it is |
|---|---|---|---|
| fast | `python -m mirsal test fast` | **9s** (72 tests, measured 2026-10-03) | a small deterministic smoke set. **It does not verify the app** and never says so |
| area | `python -m mirsal test area engine/video` | seconds–a minute | exactly the classes that import what you changed |
| slow | `python -m mirsal test slow` | ~15–20 min | the six media modules: the golden path and the encoder |
| all | `python -m unittest discover -s tests -t .` | ~17 min | unchanged; tier 3 is an **addition**, never a removal |

The slow tier is `tests.test_golden`, `test_effect_video`, `test_allow_still`,
`test_anim_speed`, `test_engine`, `test_verify` — every test in those modules, so a test added
to one of them is picked up automatically.

**The slow tier runs ALONE.** Parallel runs collide on shared resources and return `409 busy`.
Everything else may be run alongside other work.

## When each tier is mandatory

| trigger | tier |
|---|---|
| any edit at all | fast |
| a change under `mirsal/engine/` (any file) | area, **and** slow before committing |
| a change to a route, a request body or a response | area + `tests.test_openapi` |
| before the browser look | slow |
| before anyone says the app is "verified" | slow, **and** the browser look |
| before a pack is sent to Telegram | slow |
| a change to `console/*.css` or `*.js` | `python -m tests.test_js` (18 tests, 0.2s) |

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

**`mirsal/mirsal/engine/video.py`.** The encoder. `area engine/video` maps to 12 classes,
and the slow tier is mandatory before committing.

**"Hi."** No file changed, nothing maps, **nothing runs**. This is the case the rule exists
for.

**A docs-only edit.** No test. Say so in the report rather than running something to look
diligent.

## What is NOT verified by watching the app work

Haitham has seen an encode finish in seconds in the live app. That proves a file was
produced. It does **not** prove the file is ≤256 KB, ≤3 s, ≤30 fps, VP9 with real alpha, no
audio, or that the loop seam closes. Those are Telegram's rejection criteria, they are checked
**only** in the slow tier, and a clip can encode in two seconds and still be refused on
upload. A browser look and the slow tier together are what "verified" means — neither alone.

## Reporting

```
changed <file(s)>  ->  <tier / command> (<count> tests, <seconds>)
not run: <tier> because <reason>
still unknown: <the thing nobody checked>
```

The third line is what keeps clause 1 honest. A report that never has one is hiding an
assumption.