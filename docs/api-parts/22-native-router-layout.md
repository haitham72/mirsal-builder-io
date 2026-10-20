# Native HTTP structure (2026-10-20)

`mirsal/api/app.py` constructs the app and owns uvicorn lifecycle. Native routes
are grouped under `api/routers/`: imports, accounts, reactions, generations,
users, trending, tickets, collection, support and chat. Each `build_router`
receives an explicit `RequestContext`; mutable throttling and reindex state
remain private to that app instance.

`api/dependencies.py` owns JSON/body handling, caller identification, member/admin
checks, public-route guards and session cookies. It delegates identity checks to
the original handler's guard sequence. Domain routers retain their original
roles, visibility checks, error codes, JSON shapes and versioned aliases.

`api/legacy_adapter.py` owns the byte-stream bridge and is registered last.
`console/server.py` remains the stdlib handler and domain compatibility dispatcher;
its implementation is not duplicated in native routers. Range and file streams
continue through the same handler.

`api/schemas/` groups request/response models by domain. Ticket domain models
remain in `flow/ticket_models.py`. `api/openapi.py` is the single contract table.
`console/app.py`, `console/app_models.py` and `console/openapi.py` remain import
facades for existing callers.

Validation: all 92 route decorators retained; static free-name check found no
unresolved module dependencies. Account, Lottie routes, Chat stream and OpenAPI:
15 tests passed. Import, Support and Trending route classes: 5 passed. Users
dashboard, collection role contract and contract shape: 9 passed. The broad
route-miss probe logged domain errors for synthetic missing objects; the import
validation and Support dependencies it exposed were corrected and their focused
route classes passed. No providers or external sends were used.
