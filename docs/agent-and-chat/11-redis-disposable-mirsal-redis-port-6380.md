# Redis (disposable; `mirsal-redis`, port 6380)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

Everything here can be rebuilt from files and Postgres; `FLUSHALL` costs cache misses plus the short-lived state below. With Redis down, `mirsal/runtime/cache.py` runs the same calls in the process's memory (rate-limit windows, session locks and the SSE replay then live only until the server restarts; idempotency answers are also kept in Postgres for 24 h, `store/idem.py`).
`REDIS_URL` is deliberately **not** read (the shared `.env` may hold another project's); use `MIRSAL_REDIS_URL`. Keys are `mirsal:u:{user}:...` with `user = local`.

| use | key | TTL |
|---|---|---|
| event stream per generation | `events:G###` (stream; the entry id is the SSE event id) | 24 h, capped at 1000 |
| session lock (one turn at a time) | `lock:session:S###` | 5 min |
| session hot copy | `session:S###` | 1 h |
| planner cache | `plan:{sha(normalised request, grid, style, ai, template versions, model)}` | 7 d |
| vision verdicts | `vlm:judge:{asset sha}:{model}:{judge version}:{context}` | 30 d |
| embeddings | `pool:vec:{sha(kind, text)}:{model}` | 30 d |
| idempotency | `idem:{scope}:{sha(key)}` | 24 h |

The planner key never merges a semantic difference ("dog as banana" and "dog with bananas" are different keys; a plan the AI failed to expand is not cached).
`mirsal doctor` shows the Redis engine; `GET /api/health` reports every dependency.
