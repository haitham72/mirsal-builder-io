# Hosted mode (branch `deployment`)

<sub>Part of [api.md](../api.md).</sub>

With `MIRSAL_GATEWAY_SECRET` set (32+ characters) the engine listens on loopback and trusts exactly one front door, `deploy/gateway` (FastAPI): a request that carries `X-Mirsal-Gateway-Secret`, comes from loopback and names a well-formed `X-Mirsal-Subject` is that person, a `member` created on
first sight; every other request needs an API token as before (`runtime/users.py`). The gateway verifies the Google sign-in (a Supabase JWT, `Authorization: Bearer` or the `mirsal_session` cookie set by `POST /auth/session`), adds `GET /healthz`, `GET /readyz`, `GET /auth/config`, `GET /auth/me`,
`POST /auth/session`, `POST /auth/logout`, and passes everything else through unchanged (this contract, SSE included). It answers `401` without a valid sign-in, `429` with `Retry-After` over the rate limit (paid routes have their own, lower one), `403` for a cross-origin POST, `400` for an unknown Host.
Telegram: `POST /api/packs/{id}/telegram {name?, mode?, retime?}` (`retime`: videos shorter than 3 s go up with their same frames played over 3 s; the stored files are untouched), `mode` = `once` (default), `replace` or `new_set`; a pack whose exact content was already sent answers `already: true` with the earlier sets and never calls Telegram.
