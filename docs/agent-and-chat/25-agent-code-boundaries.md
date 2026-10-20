# Agent code boundaries (2026-10-20)

`agent/graph.py` is the compatibility facade and state owner: store, tools, brain,
cache, graph and thread-local replay flag. It composes behavior-only intent
classes; these classes have no constructors or separate mutable state.

`agent/lifecycle/` owns:

- `turn.py`: serializable Turn, graph State and visible Trace.
- `checkpoints.py`: process-owned SQLite connections, locking and reference counts.
- `runner.py`: per-session turn locks, execute/finally release and safe replay.
- `builder.py`: graph topology and queue dispatch.

`agent/nodes/` groups understanding, creation/confirmation, batch follow-ups,
creator runs, Reactions, edits, delivery/review and conversation handlers.
`shared.py` contains presentation constants and pure plan helpers. Handlers
continue to delegate media, spend and gate decisions to existing tools/flow.

All 112 Agent methods and three class constants are retained. 107 method bodies
are unchanged apart from relative imports; the other five delegate construction,
dispatch and connection ownership to the extracted modules. Imports of
`graph.Agent`, `graph.Turn`, `graph.Trace`, `graph.State`, `graph.STYLE_NAMES`
and `graph.compact_plan` remain valid, including old checkpoint class paths.

Validation: five checkpoint/replay regressions pass. The representative creation,
edit/review and settings/safety selection passes 20 of 21. The second-message
locking test also fails against the saved pre-refactor implementation; it is a
baseline issue, not treated as a passing check. No provider or Telegram calls.
The required focused recovery profile also passes all 14 selected tests, with
zero skipped.
