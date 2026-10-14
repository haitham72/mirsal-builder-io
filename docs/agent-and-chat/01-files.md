# Files

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

Paths below are relative to the repository root.

| file | job |
|---|---|
| `mirsal/agent/memory.py` | `SessionStore`: sessions in `out/sessions/S###.json` (files first, mirrored to Postgres, hot copy in Redis), the per-subject summary, feedback, traits, the reducer, `context(level)` |
| `mirsal/agent/resolver.py` | **deterministic first**: numbers, `#3`, ordinals, lists, ranges, exclusions, `G012/S3`, "it / that one", "previous" (the parent in this branch), a semantic word match, "make 5 like 2", role references; the intent rules (`classify`) and `settings_from` |
| `mirsal/agent/brain.py` | the small model: classify what the rules are unsure of, pick a sticker the words do not name, answer a question from the structured state, write the narrative summary. Schema-checked, one repair round, every call in `out/model_calls.jsonl`; failure = the deterministic answer |
| `mirsal/agent/tools.py` | `ConsoleTools` (the real engine) and `FakeTools` (tests): `plan` (Redis planner cache), `estimate`, `create`, `more`, `animate`, `review`, `search`, `generation`, `reference_from_sticker`, `describe` |
| `mirsal/agent/graph.py` | the LangGraph state machine, the step trace, `Agent.prepare / execute / run_turn`, `hydrate` (the session as the page shows it) |
| `mirsal/console/agent.js`, `chat-core.js`, `chat-cards.js`, `chat-stage.js`, `agent.css` | pure `AIU` helpers; chat sessions/turns; cards/carousels; stage/settings controls. Factories receive the private core state and callbacks; load order is in `docs/architecture.md` §6. |
| `mirsal/runtime/cache.py`, `mirsal/runtime/events.py` | Redis (see below) |
| `mirsal/vision/` | the vision judge, stored captions and selected-still descriptions |
