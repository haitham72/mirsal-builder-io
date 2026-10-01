# Phase_04 — supporting material for `../phase_04.md`

Phase 4 adds LangGraph and creative intelligence: understanding which sticker the user means, feedback, "dog as banana" templates, annotation and memory, driven from a terminal chat. The spec is **`../phase_04.md`**. Prerequisite: the Phase 3 exit.

- **Haitham will add here (pending):**
  - `resolver_utterances.md`: 40 labelled chat lines → the exact sticker IDs they mean, for the ≥95% accuracy eval in 4A;
  - `transformation_examples.md`: requests like "dog as banana" with the concepts he expects.

  Build 4A/4B against the spec's own test cases until these arrive.
- **Redis starts here:** host port 6380 (6379 is another project's `cache-redis`). It is disposable; Postgres is the truth.
- **Gates:** Haitham reviews 4A, 4B and 4C separately, in order.
