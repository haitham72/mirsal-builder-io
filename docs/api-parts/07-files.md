# Files

<sub>Part of [api.md](../api.md).</sub>

- `GET /out/{path}` serves a generated file. The path is resolved first (`..`, `%2e%2e` and links included) and everything is decided on the RESOLVED file: it must stay inside `out/`, and a member may read it only when it lies inside a batch folder they own (`out/users.json` or `out/telegram.json` are never reachable, however the URL is spelled).
- **Signed links**: `POST /api/assets/sign {key, ttl?}` (a path under `out/` such as `G002/slices/….png`, ttl 5-3600 s) returns `{url, expires_in}`; `GET /api/assets/{token}`
  serves it until it expires. The token is an HMAC over key, user and expiry; an edited token is `403`.
