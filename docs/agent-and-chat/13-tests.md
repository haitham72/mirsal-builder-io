# Tests

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

`tests/test_chat_interaction.py` (the reported description/display sequence, still evidence, consent, streamed deltas, replacement scope and unclear edits), `tests/test_agent.py` (plan, confirm, cancel, instant mode, memory, reducer, edits, ask, review, settings, search, errors, lock, follow-up answers, outside batches, bounded sessions, dead turns), `test_agent_resolver.py`, `test_agent_server.py`
(the whole chat through the real server on prepared sheets), `test_vision.py`, `test_cache.py` (memory and real Redis), `tests/js/agent.test.js` (node: `node --test tests/js/agent.test.js`), `test_llm_backend.py` (the backend choice, the Qwen prefill) and
`test_llm_local.py` (the local model against a FAKE OpenAI-compatible server on an ephemeral port: the model list and its cache, the `:N` suffix, the readiness probe, the empty-answer retry, the ledger, "answered by rules", the routes `GET /api/llm/models`, `POST /api/ai/backend {model}`, `GET /api/chat/agent`).
