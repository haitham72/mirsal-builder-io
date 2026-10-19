# Structure and naming review — 2026-10-19

Scope: read-only follow-up to redesign acceptance. These are proposed extractions,
not changes included in the redesign fixes. Counts below are nonblank lines.

The existing `engine`, `agent`, `flow`, `generation`, `media`, `runtime`, `services`,
`store` and `vision` boundaries are useful. Keep the deterministic engine isolated.
The largest structural problem is that `console` combines HTTP transport, the
legacy adapter, application state and frontend assets in one flat directory.

| Priority | Current files | Proposed boundary | Reason / migration gate |
|---|---|---|---|
| 1 | `console/server.py` (~2304), `console/app.py` (~1128) | `api/app.py`, `api/dependencies.py`, `api/routers/{chat,generations,imports,reactions,packs,settings}.py`, `api/legacy_adapter.py` | Extract native routes by domain, with common guards/dependencies. Retain adapter responses, Host/Origin/auth/roles/rate limits, streaming and Range semantics until each route has parity evidence. |
| 1 | `agent/graph.py` (~2502) | graph construction + checkpoint lifecycle + intent-specific node modules | Replay policy belongs in one small lifecycle module. Nodes should delegate to existing tools/flow; preserve gates, confirmation and cancellation semantics. |
| 2 | `console/studio-core.js` (~1026), `chat-core.js` (~770), `particles.js` (~495) | feature folders for Studio, Chat and Reactions; shared request/lifecycle/preview modules | Separate controllers, state and renderers. First complete T-024/025/031/034/035 watcher, cache and presenter extractions; moving files alone leaves shared-global coupling intact. |
| 2 | `console/app_models.py`, `console/openapi.py` | `api/schemas/` per domain + one contract registry | Name HTTP request/response schemas explicitly; distinguish them from domain models and LLM/provider models. Preserve route inventory and OpenAPI parity. |
| 3 | flat `console/*.css`, scripts, fonts and vendor assets | `web/{features,shared,styles,assets,vendor}` | Update `UI_FILES`, load order, inventory tests and local serving together. Avoid a new framework or bundler merely to move files. |
| 3 | `docs/Api/`, space-bearing filenames, `obs`, `tg_chat.py` | consistent documentation paths; optionally `observability`, `telegram_chat.py` | Cosmetic changes have lower value. Update links/import strings and keep compatibility shims where required. |

For HTTP endpoints, use **`api/routers/`** and domain names; reserve **routing**
for intent/navigation dispatch where that describes the actual responsibility.
FastAPI documents this modular `APIRouter` pattern in its
[larger applications guide](https://fastapi.tiangolo.com/tutorial/bigger-applications/).
There is no single mandatory industry-wide directory tree. Python modules should
use short lowercase names, with underscores when useful, per
[PEP 8](https://peps.python.org/pep-0008/#package-and-module-names).

Do not mechanically rename `flow` to `services`: orchestration and external
provider clients have different roles here. Do not rename `/api/particles` or
stored `particles` paths during a folder cleanup; these are compatibility
contracts even though the product label is Reactions. Keep the duplicate-choice
import router, Resize semantics and separate Emoji/Lottie export contracts.

Suggested order: route/schema extraction → graph lifecycle/nodes → shared UI
lifecycle/presenters → feature asset folders → cosmetic names and documentation.
Each phase needs explicit paths, its narrow contract regressions and updated
route/import inventories. None requires a merge, deployment or paid call.

Photo decision: **keep** `Custom_emojis/Original_emojis/rashed 02.jpg` as the
existing source photo (about 2.8 MB). It is input provenance, not generated
runtime output. A future source-assets folder move can clarify that ownership;
do not rewrite history or add/re-encode media in this acceptance phase.
