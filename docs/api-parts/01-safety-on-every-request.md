# Safety on every request

<sub>Part of [api.md](../api.md).</sub>

- **Host / Origin guard**: the Host header must be this server's own (`127.0.0.1`, `localhost`, `[::1]` with its port), and on anything that is not a read a browser-sent
  `Origin` must be its own and `Sec-Fetch-Site` must not be cross-site. A web page the owner visits cannot POST to the server; a client that sends no `Origin` (curl, the
  tests, the CLI) passes. Refusals are `403`.
- **Accounts** (below): with no account and no `MIRSAL_API_TOKEN` the local sandbox is open exactly as before; once one account exists every caller that is not the Studio's own
  page must send `Authorization: Bearer <token>` (`401` otherwise).
- **Rate limits**: a token holder gets 240 writes and 3000 reads a minute (`MIRSAL_RATE_WRITE`, `MIRSAL_RATE_READ`; `0` switches one off); over it the answer is `429` with `Retry-After`
  (seconds). Health checks and event streams are exempt, and the open sandbox and the owner's own page are never limited (the Studio polls a lot). Counters live in Redis (or in memory
  without it), one per user, per minute.
- **Versioning and tracing**: every route is also served under `/api/v1/...` (pin it before anything changes); every answer carries `X-API-Version` (the OpenAPI document's version) and `X-Request-Id` (your own `X-Request-Id`, when it is 1-64 of `A-Za-z0-9._-`, is echoed; otherwise a fresh one). An internal `500` includes the `request_id`, and the console line carries it. `MIRSAL_ACCESS_LOG=1` prints one JSON line per request on the server's stderr (`ts, request_id, method, path, status, ms, user, via, generation_id?, session_id?`; never the query string).
- **Pagination** is opt-in: `GET /api/generations`, `/api/jobs` and `/api/chat/sessions` take `?limit=1-500&offset=N` and then add `{total, limit, offset}`; without either, the whole list comes back as before (`400` for a bad value; an offset past the end is an empty page). A `429` is `Cache-Control: no-store`. The event stream starts with `retry: 3000`.
- **One writer of `result.json`** per `out/` across processes (`.writer.lock`): the server and the CLI commands that write results refuse to run together.
- **Idempotency**: `POST /api/generations` (both forms), `POST /api/live/sheet | video` (the routes that spend credits) and `POST /api/chat/sessions/{id}/messages` accept `Idempotency-Key`; the same key within 24 h
  returns the first answer with `"idempotent": true` and runs nothing again. Without a key nothing is compared. The cache (Redis, or memory when it is down) answers first; the answer is also kept for 24 h in Postgres (`idempotency_keys`, migration 008, `store/idem.py`: the key hashed, scoped by route and caller, the first answer wins), so a restart without Redis does not forget it. Like every write-through it only works for the real `out/` and never blocks the request.
- **AI vision needs consent in the request**: `POST .../judge` and `POST .../captions` answer `409 {error, consent_required: true}` and send nothing unless the body carries `allow_vlm: true` (the person's yes, asked once: `vision/consent.py`). Reading stored captions needs none. The chat session setting is `allow_vlm` (`null` until asked).
- Errors are `{"error": "..."}` with the HTTP status that says why (400 bad input, 401, 403, 404, 409 busy or wrong state, 413 too large, 503 provider missing), **always JSON**: an unexpected exception is a `500 {"error": "internal error"}` (the detail goes to the server console with absolute paths scrubbed, never into the answer), an unsupported method is a JSON `501`, and a URL the server does not serve is `404 {"error": "no such route"}` (a missing batch, pack or job says so in its own words).
