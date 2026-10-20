# Contract

<sub>Part of [api.md](../api.md).</sub>

`GET /api/openapi.json` is the machine-readable contract (OpenAPI 3.1; `api/openapi.py` is the single hand-written table; `console/openapi.py` is a compatibility import). `tests/test_openapi.py` guards it **both ways**: it fails when a route exists in the
server that the table does not describe, and it calls every documented operation on a scratch server and fails when one answers `no such route`. `python -m mirsal openapi [--json FILE] [--ts FILE]` writes it and TypeScript types for the app.
