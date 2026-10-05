# HTTP route inventory: stdlib migration baseline

Stage 0 groundwork, 2026-10-04. Source: the current `console/server.py` dispatch and guards, `console/openapi.py`, `runtime/users.py`, `runtime/events.py`, and the named contract suites. No server, provider or real output was run for this inventory. This is the source behavior to preserve during the authorized local FastAPI migration; deployment remains paused. Freeze the final particle acceptance state before taking byte-comparison fixtures.

An OpenAPI `object` is deliberately open, not evidence of a closed body schema. The operation details and dispatch supplements below are part of each row. Schema names are expanded in the appendix. Fields with `?` are optional; defaults shown are the dispatch defaults. Domain records may contain additional stored fields, including future-compatible fields. Preserve them and their JSON order: no filtering, default insertion or coercion beyond what the current functions already do. This inventory is a source audit, not a claim that every success/error variant has a runtime fixture.

## Shared transport contract

- Only GET and POST are implemented. Unsupported methods, including HEAD/OPTIONS/PUT/PATCH/DELETE, currently receive JSON 501 `{"error":"Unsupported method ('METHOD')"}` through BaseHTTPRequestHandler; they do not pass `_guard`. Unknown authenticated permitted routes receive 404 `{"error":"no such route"}`. Unauthorized unknown routes can receive 401/403 first.
- Every `/api/...` operation also has the `/api/v1/...` alias, rewritten before guards, dispatch and access logging. There is no currently served `/openapi.json`, `/docs`, `/redoc`, `/healthz`, `/readyz` or `/auth/...` in this engine server; hosted gateway routes are separate paused infrastructure.
- JSON uses `json.dumps(obj, ensure_ascii=False)` with ordinary spaces, original dict order and UTF-8 encoding, `Content-Type: application/json; charset=utf-8`, `Content-Length`, and `Cache-Control: no-store`. Raw/file responses use their recorded content types instead. A new compact JSON serializer changes bytes.
- Every response has `X-API-Version: 1.0.0` and `X-Request-Id`. Incoming IDs match `[A-Za-z0-9._-]{1,64}`, otherwise a fresh 16-character UUID hex prefix is used. Unsupported-method responses also receive these headers. Access logging is off unless `MIRSAL_ACCESS_LOG` is truthy; JSON lines omit query strings and include `ts,request_id,method,path,status,ms,user,via,generation_id?,session_id?`.
- Guard order today: assign request ID / normalize version prefix → exact Host/port → unsafe Origin/Sec-Fetch-Site → identify user → authorize → token-user rate limit → set `pipeline.OWNER` → dispatch/body read → reset owner. Guard errors occur before consuming a body.
- Exact allowed Host values are lowercased `127.0.0.1:PORT`, `localhost:PORT`, `[::1]:PORT`; others produce 403 `unexpected Host header`. For unsafe methods, a present Origin must be an exact `http://` allowed host, otherwise 403 `cross-origin request refused`. Sec-Fetch-Site must be `same-origin` or `none` (missing defaults same-origin), otherwise 403 `cross-site request refused`. There are no engine CORS response headers or preflight handler.
- Authentication remains `UserStore.authenticate_gateway` (valid configured secret + loopback peer + external subject), then `UserStore.authenticate(Authorization, Sec-Fetch-Site == "same-origin")`. Bearer token is checked first; same-origin then becomes implicit owner. No accounts/environment token/secret means open implicit owner. Static UI and signed-link GET exceptions are below. This server does not read a cookie; the hosted gateway does. Missing required auth is 401 `an API token is required (Authorization: Bearer <token>)`.
- Owners manage the app; Library reads, pack routes and /lib media are scoped to their own packs too. Members receive 403 `this account cannot do that (owner only)` outside the table below. A stranger's ownable batch/chat/job/file produces 404 `not found` or the existing store-specific not-found wording, not a disclosure. Member chat stores are scoped to their user. `can_spend` checks remain inside the live/paid core flow.
- Existing rate limits apply only to `via=token`: per-user read/write windows, read default3000/minute, write240/minute, env overrides `MIRSAL_RATE_READ`/`WRITE`, nonpositive disables. Open/page/gateway users, `/api/health...` and paths ending `/events` are exempt. Response429 is `{"error":"too many requests: wait N s"}`, `Retry-After:N`, no-store. There is no hashed-IP engine limiter.
- Empty/missing JSON bodies become `{}`. Content-Type is not checked before JSON parsing. Unknown fields ordinarily remain passive/ignored by dispatch; strings/type conversions/errors belong to current functions. Bad JSON and caught ValueError/KeyError/TypeError produce400 `{"error":"bad request: <exception>"}`. Domain errors retain their existing code and exact `{"error":str(error)}`. Vision consent produces409 with `consent_required:true`. Unexpected exceptions produce500 `{"error":"internal error","request_id":ID}`, with scrubbed detail only on stderr. Never add raw FastAPI422 or default405 bodies.
- No multipart parser exists in this server. Upload endpoints consume raw bytes; `_raw` defaults40MiB, reference15MiB and video/project300MiB. `Content-Length` over a cap produces413 `file too large`; missing length means empty bytes. Preserve raw upload behavior instead of silently changing to multipart-only.
- Pagination applies only to GET generations/jobs/chat sessions: no limit/offset keeps legacy unpaged shape; either parameter adds `total,limit,offset`, defaults500/0, limits1–500 and offset>=0. Bad bounds produce400 `limit must be 1-500 and offset 0 or more`. `jobs?status=` filters first; `search?q=`, `history?offset=&limit=` and `usage?limit=` retain their own helpers/defaults.

## Idempotency and streaming

`Console.idem(scope,key,fn)` remains the only transactional implementation: empty key runs normally; nonempty key stripped/hashed, locked30s, cache then durable Postgres lookup, first successful answer retained24h; replay adds `idempotent:true`. Exact scopes: `generation:USER`, `generation-task:USER`, `live:sheet:USER`, `live:video:USER`, `chat:SESSION`. A held key produces409 `a request with this Idempotency-Key is still running`. No particle/action route acquires a new idempotency scope as part of HTTP migration.

GET generation events is the only HTTP SSE route. The agent itself runs a background turn; clients poll sessions rather than a second LangGraph SSE endpoint. Generation SSE status200, `text/event-stream; charset=utf-8`, no-store, `X-Accel-Buffering:no`, `Connection:close`; first bytes `retry: 3000\n\n`. Replay chooses nonempty query `after`, else `Last-Event-ID`, else `0-0`. Calls `runtime.events.read(gid,last)`, yields `id: ID\nevent: NAME\ndata: JSON\n\n` (`ensure_ascii=False`, `default=str`), stops on pack_complete/generation_failed or600seconds, and ignores disconnected clients. The legacy keepalive is `: ping\n\n` every25 idle polls at0.2seconds (about5seconds); the migration spec explicitly requests15seconds, an identified timing change rather than existing behavior. Event names: generation_started, sheet_generated, sticker_processing, sticker_ready, sticker_failed, animation_started, animation_ready, video_sheet_ready, review_decided, pack_complete, generation_failed.

## Operation table

Auth labels refer to the shared guard above; “owner / own batch/job/chat” includes all owners. Every row includes `/api/v1` when its path starts `/api/`. SSE is marked in the last column. Additional normal-status branches override stale hand-written OpenAPI statuses where dispatch differs.


| Method and exact path | Request | Success response/status | Auth | SSE |
| --- | --- | --- | --- | --- |
| `GET /api/chat/agent` | — | 200 object (open; operation detail) | owner / own chat | no |
| `GET /api/chat/sessions` | ?limit=1–500&offset>=0 optional | 200 {sessions?:[SessionSummary]} | owner / own chat | no |
| `POST /api/chat/sessions` | {title?:string, settings?:Settings} | 200 Session | owner / own chat | no |
| `GET /api/chat/sessions/{id}` | — | 200 Session | owner / own chat | no |
| `POST /api/chat/sessions/{id}/messages` | ChatSend | 202 Accepted | owner / own chat | no |
| `POST /api/chat/sessions/{id}/settings` | {grid?,ask_before_spending?,ai?,allow_vlm?,style_id?,creator?:{on?,scope?:images\|video,bypass?}}; unknown keys ignored | 200 {settings?:Settings} | owner / own chat | no |
| `POST /api/chat/sessions/{id}/delete` | none / see operation detail | 200 {deleted?:string} | owner / own chat | no |
| `GET /api/packs/{id}/stickers/{sid}/particle-preview` | — | 200 object (open; operation detail) | owner (member 403 in current role table) | no |
| `GET /api/generations/{id}/particles` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/particles/{id}/link` | object (open; operation detail) | 200 object (open; operation detail) | owner | no |
| `POST /api/particles/{id}/unlink` | object (open; operation detail) | 200 object (open; operation detail) | owner | no |
| `GET /api/particles` | — | 200 {sets?:[object (open; operation detail)]} | owner | no |
| `POST /api/particles` | ordered alternatives: from_stickers, from_generation, from_video, from_slices, from_effect, or new empty set; see durable-particle contract below | 201 object (open; operation detail) | owner | no |
| `GET /api/particles/deleted` | — | 200 {sets?:[object (open; operation detail)]} | owner | no |
| `GET /api/particles/{id}` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/particles/{id}` | object (open; operation detail) | 200 object (open; operation detail) | owner | no |
| `POST /api/particles/{id}/assign` | {packs?:[string]} | 200 object (open; operation detail) | owner | no |
| `POST /api/particles/{id}/unassign` | {packs?:[string]} | 200 object (open; operation detail) | owner | no |
| `POST /api/particles/{id}/duplicate` | object (open; operation detail) | 201 object (open; operation detail) | owner | no |
| `POST /api/particles/{id}/delete` | {confirm?:boolean} | 200 {ok?:boolean, id?:string, trashed?:boolean, was_in?:[string]} | owner | no |
| `POST /api/particles/{id}/restore` | none / see operation detail | 200 object (open; operation detail) | owner | no |
| `POST /api/particles/{id}/preview` | {pack_id?:string, preset?:string, params?:object (open; operation detail), size?:integer} | 200 object (open; operation detail) | owner | no |
| `POST /api/particles/{id}/render` | {pack_id?:string, preset?:string, params?:object (open; operation detail)} | 200 object (open; operation detail) | owner | no |
| `POST /api/particles/{id}/add` | {renders?:[string], pack_id?:string} | 200 {added?:[object (open; operation detail)], pack_id?:string} | owner | no |
| `POST /api/particles/{id}/more` | {mode?:string, prompt?:string, effect?:string, grid?:string, elements?:[string], estimate?:boolean, go?:boolean} | 200 estimate OR 409 {error,estimate} OR 202 job context (image/video shapes differ) | owner | no |
| `GET /api/effects` | — | 200 {effects?:[object (open; operation detail)]} | owner | no |
| `POST /api/effects` | {pack_id,sticker_ids?="all",mode?="video",grid?="2x2",note?,allow_vlm?} | 202 {id?:string, status?:string} | owner | no |
| `GET /api/effects/{id}` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/effects/{id}/analyse` | {allow_vlm?} | 202 {id?:string} | owner | no |
| `POST /api/effects/{id}/plan` | {group,elements?,subject?,style?,sprites?} | 200 object (open; operation detail) | owner | no |
| `POST /api/effects/{id}/estimate` | {group,elements?,subject?,grid?,model?,options?} | 200 object (open; operation detail) | owner | no |
| `POST /api/effects/{id}/video` | {group,elements?,subject?,grid?,model?,options?,go?,particle_target?} | 202 {job?:string, estimate?:['number', 'null']} | owner | no |
| `POST /api/effects/{id}/suggest` | {grid?,allow_vlm?} | 200 object (open; operation detail) | owner | no |
| `POST /api/effects/{id}/particles_estimate` | {grid?,elements?,group?,model?,options?,estimate?} | 200 object (open; operation detail) | owner | no |
| `POST /api/effects/{id}/particles` | {grid?,elements?,group?,model?,options?,estimate?,go?} | 202 {job?:string, task?:string, estimate?:['number', 'null'], id?:string, grid?:[integer]} | owner | no |
| `POST /api/effects/{id}/particles_pick` | {indexes} | 200 object (open; operation detail) | owner | no |
| `POST /api/effects/{id}/particles_recut` | object (open; operation detail) | 202 {id?:string, generation?:string} | owner | no |
| `POST /api/effects/{id}/preview` | {sticker_id,params?,size?=256} | 200 object (open; operation detail) | owner | no |
| `POST /api/effects/{id}/render` | {sticker_id,params?} | 200 object (open; operation detail) | owner | no |
| `POST /api/effects/{id}/add` | {results?,pack_id?,sticker_ids?} | 200 object (open; operation detail) | owner | no |
| `GET /api/me` | — | 200 Me | authenticated member | no |
| `GET /api/users` | — | 200 {users?:[User]} | owner | no |
| `POST /api/users` | UserCreate | 200 UserWithToken | owner | no |
| `POST /api/users/{id}/update` | UserUpdate | 200 {user?:User} | owner | no |
| `POST /api/users/{id}/disable` | none / see operation detail | 200 {user?:User} | owner | no |
| `POST /api/users/{id}/enable` | none / see operation detail | 200 {user?:User} | owner | no |
| `POST /api/users/{id}/rotate` | none / see operation detail | 200 UserWithToken | owner | no |
| `GET /api/generations` | ?limit=1–500&offset>=0 optional | 200 object (open; operation detail) | authenticated member | no |
| `POST /api/generations` | {prompt\|subject,variant?,outline?,erode?} OR {task,take?=0,outline?,erode?} | 202 GenerationCreated | authenticated member | no |
| `GET /api/generations/{id}` | — | 200 object (open; operation detail) | owner / own batch | no |
| `GET /api/generations/{id}/events` | ?after=ID; otherwise Last-Event-ID header | 200 Event | owner / own batch | yes |
| `GET /api/generations/{id}/files` | — | 200 object (open; operation detail) | owner | no |
| `GET /api/generations/{id}/edge_preview` | ?index=1&outline=0&erode=0&px=420 | 200 image/png bytes | owner / own batch | no |
| `GET /api/generations/{id}/sheet_preview` | ?fill=cfg.slot_fill (clamped0.5–0.92)&px=420 | 200 image/png bytes | owner / own batch | no |
| `GET /api/generations/{id}/history` | ?index=N optional | 200 object (open; operation detail) | owner / own batch | no |
| `POST /api/generations/{id}/more` | none / see operation detail | 202 {id?:integer} | owner / own batch | no |
| `POST /api/generations/{id}/regen` | {index:integer, subject?:string} | 202 {id?:integer} | owner / own batch | no |
| `POST /api/generations/{id}/review` | Review | 200 object (open; operation detail) | owner / own batch | no |
| `POST /api/generations/{id}/judge` | {allow_vlm:true,scope?:"anim"\|other(default still),force?} | 202 {id?:integer, scope?:string} | owner / own batch | no |
| `GET /api/generations/{id}/captions` | — | 200 object (open; operation detail) | owner / own batch | no |
| `POST /api/generations/{id}/captions` | {allow_vlm:boolean, force?:boolean} | 202 {id?:integer, force?:boolean} | owner / own batch | no |
| `POST /api/generations/{id}/video_sheet` | none / see operation detail | 200 object (open; operation detail) | owner / own batch | no |
| `POST /api/generations/{id}/quick_sheet` | none / see operation detail | 200 object (open; operation detail) | owner / own batch | no |
| `POST /api/generations/{id}/video_sheet/{aid}/video` | raw video bytes, <=300 MiB; ?name=video.mp4 | 202 {id:integer,sheet:string} | owner (role gate does not match nested path) | no |
| `POST /api/generations/{id}/allow` | {kind?:still/animation/video_sheet, sheet?:string, index?:integer or string, indexes?:[integer or string], all?:boolean, allow?:boolean} | 202 {id?:integer, kind?:string, indexes?:[integer or string], index?:integer or string, allow?:boolean} | owner / own batch | no |
| `GET /api/generations/removed` | — | 200 {batches:[{id,number,removed,by,subject}]} | owner | no |
| `POST /api/generations/{id}/remove` | none / see operation detail | 200 object (open; operation detail) | owner | no |
| `POST /api/generations/{id}/restore` | none / see operation detail | 200 object (open; operation detail) | owner | no |
| `POST /api/generations/{id}/drop` | {index:integer, dropped?:boolean} | 200 object (open; operation detail) | owner / own batch | no |
| `POST /api/generations/{id}/animate` | {scope?:string, index?:integer} | 200 {noop:true,message:"Already animated."} OR 202 {id,noop:false} | owner / own batch | no |
| `POST /api/generations/{id}/appearance` | {outline?:integer, erode?:integer, reslice?:boolean} | 200 object (open; operation detail) | owner / own batch | no |
| `POST /api/generations/{id}/edge` | {outline?:integer, erode?:integer, via?:string} | 202 {id?:integer} | owner / own batch | no |
| `POST /api/generations/{id}/reslice` | none / see operation detail | 202 {id?:integer} | owner / own batch | no |
| `POST /api/generations/{id}/recheck` | none / see operation detail | 200 boundary report object | owner / own batch | no |
| `POST /api/generations/{id}/edit` | {index,png:base64 or data URL} | 200 object (open; operation detail) | owner | no |
| `POST /api/generations/{id}/studio_edit` | {index,action?:"commit",overlays?} | 200 object (open; operation detail) | owner | no |
| `POST /api/generations/{id}/add` | {pack_id?,pack_name?,mode?,outline?,erode?,names?:{index:{name?,emoji?}}} | 200 object (open; operation detail) | owner | no |
| `POST /api/generations/{id}/pack_add` | {pack_id} | 200 object (open; operation detail) | owner | no |
| `POST /api/generations/{id}/recut_particles` | none / see operation detail | 202 {id?:integer} | owner | no |
| `POST /api/generations/{id}/recut` | none / see operation detail | 202 {id?:integer} | owner / own batch | no |
| `POST /api/generations/{id}/reveal` | none / see operation detail | 200 {opened?:string} | owner | no |
| `GET /api/history` | ?offset=0&limit=5 | 200 object (open; operation detail) | owner | no |
| `GET /api/inputs` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/live/cost` | {kind?,model?,options?,grid?,...} -> Console.live("cost", body) | 200 object (open; operation detail) | authenticated member | no |
| `POST /api/live/sheet` | LiveSheet | 200 LiveJob | authenticated member | no |
| `POST /api/live/video` | {generation,sheet?,model?,options?,loop?,video_prompt?,outline?,erode?,slot_fill?} -> Console.live("video", body) | 200 object (open; operation detail) | authenticated member | no |
| `POST /api/live/ref` | raw image bytes, <=15 MiB; ?name=ref.png | 200 object (open; operation detail) | authenticated member | no |
| `GET /api/jobs` | ?status=STATUS&limit=1–500&offset>=0 optional | 200 {jobs?:[Job]} | authenticated member | no |
| `POST /api/jobs` | {kind?="sheet",task?,generation?,request?={}} | 200 Job | owner | no |
| `GET /api/jobs/{id}` | — | 200 Job | owner / own requested job | no |
| `POST /api/jobs/{id}/claim` | {ticket} | 200 Job | owner | no |
| `POST /api/jobs/{id}/done` | {file,model?,cost?} | 200 Job | owner | no |
| `POST /api/jobs/{id}/fail` | {reason} | 200 Job | owner | no |
| `POST /api/jobs/{id}/requeue` | none / see operation detail | 200 Job | owner | no |
| `POST /api/jobs/{id}/check` | none / see operation detail | 200 Job | owner / own requested job | no |
| `POST /api/jobs/{id}/continue` | none / see operation detail | 200 Job | owner / own requested job | no |
| `POST /api/jobs/{id}/dismiss` | none | 200 Job | owner / own requested job | no |
| `POST /api/jobs/{id}/retry_estimate` | none / see operation detail | 200 {credits?:number, message?:string} | owner / own requested job | no |
| `POST /api/jobs/{id}/retry` | {go:boolean, estimate:number} | 200 Job | owner / own requested job | no |
| `GET /api/models` | — | 200 object (open; operation detail) | owner | no |
| `GET /api/higgsfield` | — | 200 object (open; operation detail) | owner | no |
| `GET /api/usage` | ?limit=100 | 200 object (open; operation detail) | owner | no |
| `GET /api/metrics` | — | 200 object (open; operation detail) | owner | no |
| `GET /api/ai` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/ai/backend` | object (open; operation detail) | 200 object (open; operation detail) | owner | no |
| `GET /api/llm/models` | — | 200 object (open; operation detail) | authenticated member | no |
| `GET /api/vision` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/plan` | {prompt?,grid?="3x3",style_id?="flat_vector",ai?,loop?} | 200 object (open; operation detail) | owner | no |
| `GET /api/tasks` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/tasks` | {prompt?,grid?="3x3",style_id?="flat_vector",ai?,loop?} | 200 object (open; operation detail) | owner | no |
| `GET /api/tasks/{id}` | — | 200 object (open; operation detail) | owner | no |
| `GET /api/inbox` | — | 200 object (open; operation detail) | owner | no |
| `GET /out/{path}` | — | 200 file bytes, guessed MIME; no Range handling | owner / own resolved batch file | no |
| `POST /api/assets/sign` | AssetSign | 200 AssetLink | authenticated member | no |
| `GET /api/assets/{token}` | — | 200 or206 file bytes, MIME + Range headers | signed link | no |
| `GET /api/library` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/packs` | {name?} | 200 object (open; operation detail) | owner | no |
| `POST /api/packs/{id}` | {name?, cover?, order?} | 200 object (open; operation detail) | owner | no |
| `POST /api/packs/{id}/delete` | none / see operation detail | 200 object (open; operation detail) | owner | no |
| `POST /api/packs/{id}/restore` | none / see operation detail | 200 object (open; operation detail) | owner | no |
| `POST /api/packs/{id}/stickers` | {from_generation:{id,index,kind?="static"}} | 200 object (open; operation detail) | owner | no |
| `POST /api/packs/{id}/render` | raw PNG bytes, <=40 MiB; ?name=sticker&emoji=🙂 | 200 object (open; operation detail) | owner | no |
| `POST /api/packs/{id}/stickers/{sid}` | {name?, emoji?} | 200 object (open; operation detail) | owner | no |
| `POST /api/packs/{id}/stickers/{sid}/animate` | {start?=0,end?=3,fps?=12,format?="webm",loop?=true,save?,name?} | 200 library result when save, otherwise encoded media + X-Animate | owner | no |
| `POST /api/packs/{id}/stickers/{sid}/move` | {to} | 200 object (open; operation detail) | owner | no |
| `POST /api/stickers/move` | {to,items:[{pack_id,id}]} | 200 object (open; operation detail) | owner | no |
| `POST /api/packs/{id}/stickers/{sid}/delete` | none / see operation detail | 200 object (open; operation detail) | owner | no |
| `POST /api/stickers/delete` | {items:[{pack_id,id}]} | 200 object (open; operation detail) | owner | no |
| `POST /api/cutout` | raw image bytes, <=40 MiB; ?method=auto | 200 image/png bytes + X-Cutout | owner | no |
| `POST /api/packs/{id}/telegram` | object (open; operation detail) | 200 object (open; operation detail) | owner | no |
| `GET /api/packs/{id}/telegram` | ?name=NAME optional | 200 object (open; operation detail) | owner | no |
| `GET /api/packs/{id}/stickers/{sid}/particles` | — | 200 object (open; operation detail) | member: empty response | no |
| `GET /api/packs/{id}/particles` | — | 200 {pack_id?:string, sets?:[object (open; operation detail)], bursts?:[object (open; operation detail)], counts?:object (open; operation detail)} | member: empty response | no |
| `GET /api/packs/{id}/export.zip` | — | 200 application/zip bytes + Content-Disposition | owner | no |
| `GET /api/packs/{id}/telegram.zip` | — | 200 application/zip bytes + Content-Disposition | owner | no |
| `GET /api/telegram` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/telegram/config` | {token?:string, user_id?:string} | 200 object (open; operation detail) | owner | no |
| `POST /api/telegram/disconnect` | none / see operation detail | 200 object (open; operation detail) | owner | no |
| `GET /api/projects` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/projects` | raw video/GIF bytes, <=300 MiB; ?name=video.mp4 | 200 object (open; operation detail) | owner | no |
| `GET /api/projects/{id}` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/projects/{id}` | project patch object; forwarded unchanged to Projects.update | 200 object (open; operation detail) | owner | no |
| `POST /api/projects/{id}/delete` | none / see operation detail | 200 object (open; operation detail) | owner | no |
| `POST /api/projects/{id}/render` | {format?="webm",overlays?,save?:{pack_id,name?,emoji?,replace?:{pack_id,sticker_id}}} | 200 encoded media + X-Render; with save: library sticker object + info | owner | no |
| `POST /api/projects/from_sticker` | {pack_id:string, sticker_id:string} | 200 object (open; operation detail) | owner | no |
| `GET /api/watch` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/watch/remove` | {number?,subject?} | 200 object (open; operation detail) | owner | no |
| `POST /api/watch/restore` | {id} | 200 object (open; operation detail) | owner | no |
| `POST /api/watch/purge` | {id} | 200 object (open; operation detail) | owner | no |
| `GET /api/trash` | — | 200 object (open; operation detail) | owner | no |
| `POST /api/trash/purge` | {type:batch/pack, id:string, confirm_shared?:boolean} | 200 task if finished; 202 task if running | owner | no |
| `POST /api/trash/purge_all` | {confirm:string} | 200 task if finished; 202 task if running | owner | no |
| `GET /api/trash/purges/{id}` | — | 200 object (open; operation detail) | owner | no |
| `GET /api/watch/thumb/{name}` | — | 200 image/jpeg bytes | owner | no |
| `GET /api/search` | ?q="" | 200 {results?:[object (open; operation detail)], via?:string} | authenticated member | no |
| `GET /api/health` | — | 200 Health | authenticated member | no |
| `GET /api/health/models` | — | 200 object (open; operation detail) | owner | no |
| `GET /api/health/storage` | — | 200 object (open; operation detail) | owner | no |
| `GET /api/openapi.json` | — | 200 object (open; operation detail) | authenticated member | no |

Table: 158 documented operations. Additional static/source routes are enumerated separately below.

## Operation details from the existing schema table

- **`GET /api/chat/agent`** — Which model runs the assistant and the vision judge, what is available (the local model by a real probe, with the reason when it cannot answer) and `agent_status` {fallback, reason}: true when the chat is on its rules only
- **`GET /api/chat/sessions`** — List chats, newest first
- **`POST /api/chat/sessions`** — Create a chat
- **`GET /api/chat/sessions/{id}`** — A whole chat for display: messages with steps and cards (generation cards carry their live stickers), memory summary
- **`POST /api/chat/sessions/{id}/messages`** — Send a message or a button action; the turn runs in the background (409 while the last one runs). Idempotency-Key supported
- **`POST /api/chat/sessions/{id}/settings`** — Grid, Ask-before-spending and style (unknown keys are ignored; an unknown style is a 400)
- **`POST /api/chat/sessions/{id}/delete`** — Delete a chat (its stickers stay)
- **`GET /api/packs/{id}/stickers/{sid}/particle-preview`** — Free Echo reaction for this sticker: newest own linked set, persisted motion and sizing. Returns {set, motion, url, params, preset} or {set:null,url:null}; no unrelated-set fallback. Members receive the empty answer
- **`GET /api/generations/{id}/particles`** — READY batch cells: {generation, cells:[{index,link,sticker,offer_approve,sets,affirmed}]}
- **`POST /api/particles/{id}/link`** — Link owner stickers {sticker_ids:[ids or owner records]}; free, no copies
- **`POST /api/particles/{id}/unlink`** — Unlink owner stickers {sticker_ids:[ids]}; set and cells stay
- **`GET /api/particles`** — Every particle set that is not in the trash, newest first: {sets: [{id, name, created, user, kind, elements[], packs[], used_in[{id, name}], cells[], picked[], n_cells, n_picked, renders, credits, drawing, sheets[]}]}. Sticker-owned sets include owner[], source.kind/job, credits, affirmed_in[], detached; packs[] is derived read-only (docs/particles.md)
- **`POST /api/particles`** — Recovery {from_stickers:[library sticker ids],parent_pack_id,owners?,name?,target?} keeps originals and links tight sprites to the parent pack stickers. Owners {owners:[{pack_id,sticker_id}]} replace deprecated packs input. Imports accept target:P### to append; video imports are idempotent by effect/result id. ALSO {from_video:E###,picked?:[source cell indices]} keeps animated clips/frame timelines and keyed posters, {from_slices:[{generation,index}],target?:P###} copies selected slices (target appends). ALSO {from_generation: G###, name?, packs?, picked?} -> 201: the cells of a batch that was CUT AS PARTICLES become a set, as TIGHT sprites (cropped out of the keyed sheet, never 512 px stickers); a batch cut as stickers is a 409 with the way out (POST /api/generations/{id}/recut_particles), a missing one a 404. Save what a run drew as a DURABLE set: {from_effect: E###, name?, packs?: [ids], picked?: [cells]} (the effect's own pack by default) -> 201 the set. Without `from_effect` it makes an empty stand-alone set: {name?, elements?, packs?, kind?: drawn|stickers|video}. Free
- **`GET /api/particles/deleted`** — The trash, newest deleted first: {sets: [{id, name, created, kind, elements[], packs[], used_in[{id, name, missing?}], cells[] (urls into out/trash/particles/), picked[], n_cells, n_picked, credits, deleted: true, trashed: true, deleted_at}]}. Restore any of them with POST /api/particles/{id}/restore, long after the delete. Owner only
- **`GET /api/particles/{id}`** — One set with its cells as /out/ urls, `used_in` the pack names, `sheets[]` (the sheets drawn for it by Generate more: {n, job, generation, grid, elements, status: REQUESTED|DRAWN|DONE|FAILED|NO_CELLS, estimate, cost, appended[], skipped[], error}), `drawing` (a sheet is on its way), `trashed: false`. A read also appends the cells of a sheet that was cut since the last one
- **`POST /api/particles/{id}`** — Rename, re-pick cells, persist the default motion including sprite_px/scale or link owners through deprecated packs: {name?, elements?, packs?, picked?: [cells], motion?: {preset, params}}. Unpicking never deletes a file (generate more appends). Empty `picked` is a 400
- **`POST /api/particles/{id}/assign`** — Deprecated one-release alias: link the stickers of packs {packs: [ids]}: a list edit, no file is copied; 404 for a pack that does not exist
- **`POST /api/particles/{id}/unassign`** — Deprecated one-release alias: unlink the stickers of packs {packs: [ids]}; the set and its cells STAY
- **`POST /api/particles/{id}/duplicate`** — An independent branch under a new id with the same sticker owners, saved motion, images and clip timelines; copied render affirmations are cleared ({name?}) -> 201
- **`POST /api/particles/{id}/delete`** — Move the set to out/trash/particles/ (nothing is destroyed). A set assigned to packs is REFUSED with 409 and the pack names unless {confirm: true}
- **`POST /api/particles/{id}/restore`** — Put a deleted set back, same id and packs; 409 when that id is taken again
- **`POST /api/particles/{id}/preview`** — The burst of the set's PICKED cells as a small looping WebP, rendered by the same engine as the final file (free; cached by what it was made from): {pack_id?, preset?: burst | fountain | vortex | rain | confetti (default: the set's own motion, else burst), params?: {magnitude, gravity, vortex, count, spin, seed, ..., sprite_px?: 32-512, scale?: 1-4} (strict: 400 for an unknown key), size?: 64-512}. -> {url, file, params, preset, sprites, source: cells | stickers, pack_id}. A set of kind `stickers` bursts the pack's own stickers; a drawn set with no cell yet is a 409
- **`POST /api/particles/{id}/render`** — The final 512 px WebM of the burst FOR A PACK, judged and stored under out/particles/P###/renders/R###.webm with its checks: {pack_id (default: the set's only pack; 400 when it is in several), preset?, params?}. -> {id, set, pack_id, preset, params, status, bytes, url, checks[], warnings[], blocks[], metrics, added_to}. Stored whatever the checks say: ONLY Telegram's own limits make it FAILED (and a failed one is kept); every other check is a warning the person decides on
- **`POST /api/particles/{id}/add`** — Put rendered bursts into a pack as animated stickers tagged with the pack's emoji (commonest first, at most 20): {renders?: [R###] (default: every READY burst rendered for that pack that is not in a pack yet), pack_id?}. -> {added: [{sticker, name, render}], pack_id}. This click is the person's approval (history APPROVE). A FAILED render (a Telegram limit) is a 409; a warning never stops it; the same burst in the same pack twice is a 409
- **`POST /api/particles/{id}/more`** — Add more with explicit mode:drawn|image|video|stickers (defaults to original source), prompt and grid. Video uses Kling quote/go and appends animated clips; quote returns effect context to resend as effect on go. Other modes draw a sheet for the set and APPEND its cut cells (numbered after the last cell, picked; nothing existing is deleted, overwritten or re-picked). {grid?: 2x2 | 3x3, elements?: [the particles to draw; default the set's own, at most the sheet's cells], estimate?: true -> 200 the free quote (prompt, picks, credits, model), go?: true}; 409 with the estimate unless `go: true` (the click is the go-ahead); 202 {job, task, estimate, id, grid}. A set made by hand (no run behind it) can gain cells this way. 400 with the reason when there is nothing to draw
- **`GET /api/effects`** — Effects, newest last: id, pack, mode, status, counts
- **`POST /api/effects`** — Start an effect for a pack: {pack_id, sticker_ids | "all", mode: video | sim, grid: 2x2 | 3x3, note?, allow_vlm?}; the analysis runs in the background (poll the record)
- **`GET /api/effects/{id}`** — One effect: stickers, groups (subject, pieces, screen colour, motion presets, sprites), the particle set (set: {grid, elements, options, source, by, status: SUGGESTED | REQUESTED | DRAWN, job?, generation?, picked}), video jobs, results with their checks, history
- **`POST /api/effects/{id}/analyse`** — Read the stickers again (allow_vlm: true lets a vision model look at the pictures; otherwise the built-in table answers)
- **`POST /api/effects/{id}/plan`** — Edit a group: {group, elements?, subject?, style?, sprites?: "own" | {generation: N, picked?: [cells]}}; linted (400 with the reason)
- **`POST /api/effects/{id}/estimate`** — The text-only video of a group before anything is spent: prompt, screen colour, cells, credits, model (free)
- **`POST /api/effects/{id}/video`** — Start the text-only Kling video of a group; 409 with the estimate unless go: true (the click is the go-ahead)
- **`POST /api/effects/{id}/suggest`** — Candidate particles for the ONE set of the whole effect: {grid?: 2x2 | 3x3, allow_vlm?}; the vision model looks at one picture (the master sheet of the batch the stickers were cut from, else a contact sheet of the stickers) only with allow_vlm: true, else the built-in table answers. Answer: {options: [8-12 short names], n (cells of the grid), grid, source: {kind: batch | contact, generation?}, by: vlm | table, model?, notes}; stored in effect.set
- **`POST /api/effects/{id}/particles_estimate`** — The ONE AI-drawn sheet of particles for the whole effect before anything is spent: {grid?: 2x2 | 3x3, elements: [the person's picks, 1..rows*cols; fewer are cycled as variants]}; the prompt, the cells, screen colour, credits, model (free). Replaces pieces_estimate (kept as an alias; `group` there means that group's pieces)
- **`POST /api/effects/{id}/particles`** — Draw the particle sheet (an ordinary sheet job, outline 0, one sheet for the whole effect): {grid?, elements, go}; 409 with the estimate unless go: true. The batch is a particle batch (kind: particles: exact equal cells, no sticker rule blocks a cell, warnings only); when it is cut every group's sprites are {generation, picked} and effect.set is REQUESTED then DRAWN. Replaces pieces (kept as an alias)
- **`POST /api/effects/{id}/particles_pick`** — Which cells of the drawn sheet are the particles: {indexes: [cell numbers]}; sets effect.set.picked and every group's sprites.picked; a cell with warnings can be picked, a cell with no picture cannot (400); recorded in the history (actor you)
- **`POST /api/effects/{id}/particles_recut`** — Cut the set's drawn sheet again as a particle sheet (a sheet drawn before batches knew they were particles, e.g. one read as 3x3 with cells blocked): exact equal cells, warnings only, free, from the stored sheet; 409 when nothing is drawn, a cell was already decided or the batch already is a particle batch. Answer 202 {id, generation}
- **`POST /api/effects/{id}/preview`** — The simulated burst of a sticker as a small looping WebP: {sticker_id, params: {gravity, magnitude, vortex, count, ..., sprite_px?: 32-512 (default 100), scale?: 1-4 (default 1)}, size?} (free); the sprites are fitted into sprite_px x scale px before simulating, invalid -> 400
- **`POST /api/effects/{id}/render`** — Render the final 512 px WebM of a sticker's burst and judge it (params as for preview, incl. sprite_px and scale); stored whatever the checks say (only a Telegram limit makes it FAILED)
- **`POST /api/effects/{id}/add`** — Add results to the pack as animated stickers tagged with their source emoji: {results?, pack_id?, sticker_ids?: only for these source stickers}; the click is the person's decision
- **`GET /api/me`** — Who the server thinks you are and what you may do
- **`GET /api/users`** — Accounts (owner only; never a token)
- **`POST /api/users`** — Create an account; its token is returned once (owner only)
- **`POST /api/users/{id}/update`** — Change the name, the role or the right to spend (owner only)
- **`POST /api/users/{id}/disable`** — Stop a token at once (owner only)
- **`POST /api/users/{id}/enable`** — Let a disabled account back in (owner only)
- **`POST /api/users/{id}/rotate`** — A new token; the old one stops working (owner only)
- **`GET /api/generations`** — Every batch (newest first) with the server's state
- **`POST /api/generations`** — Start a batch from a prepared sheet, or run a reserved task. Idempotency-Key supported
- **`GET /api/generations/{id}`** — The full snapshot: result.json plus events
- **`GET /api/generations/{id}/events`** — Server-sent events (Last-Event-ID or ?after= replays what was missed)
- **`GET /api/generations/{id}/files`** — Where the batch's files are
- **`GET /api/generations/{id}/edge_preview`** — One sticker with a stroke / trim, rendered on the fly (image/png)
- **`GET /api/generations/{id}/sheet_preview`** — The video sheet at a given fill (image/png)
- **`GET /api/generations/{id}/history`** — Every sticker's generation history, folded: {generation_id, stickers: [{id, index, key, name, status, review, lines, shown, last, stages: [{stage, count, last, lines}]}]}, decisions grouped by stage in the order they happened, newest line first; ?index=N for one sticker
- **`POST /api/generations/{id}/more`** — The next prepared variation of the same subject
- **`POST /api/generations/{id}/regen`** — Regenerate one sticker as a 1x1 child batch
- **`POST /api/generations/{id}/review`** — A human decision at a gate (Python's blocks are final)
- **`POST /api/generations/{id}/judge`** — The vision model pre-reviews the stickers (history lines only). Needs allow_vlm: true in the body (409 with consent_required otherwise): AI vision is the person's yes, asked once
- **`GET /api/generations/{id}/captions`** — The stored AI caption of every cell of the sheet (grid read from result.json, 2x2 or 3x3): {generation_id, grid, cells: [{index, row, col, png, caption, text_visible, verdict, reasons, model}], missing, ready}. Read-only: no model, no consent
- **`POST /api/generations/{id}/captions`** — Write the missing AI captions in the background (a model call per cell). Needs allow_vlm: true (409 with consent_required otherwise); {force?} captions again
- **`POST /api/generations/{id}/video_sheet`** — Build the video sheet from the approved stills
- **`POST /api/generations/{id}/quick_sheet`** — Approve the kept stills, build and approve the video sheet (one click)
- **`POST /api/generations/{id}/video_sheet/{aid}/video`** — Attach a returned video (raw body) to a video sheet and slice it
- **`POST /api/generations/{id}/allow`** — "Use it anyway": allow, or take back (allow: false), a video sheet (kind: video_sheet; sheet A#), a sticker (kind: still) or an animation (kind: animation, the default) that Python blocked as a judgement call: a character touching its cell, a hole, a slot or a loop. Telegram's own limits (format, size, codec) and a cell with no picture stay final (409 with the reason). Pick the stickers with index, indexes or all; the permission is recorded on the sticker and its history and kept by every later cut. Answers {id, kind, indexes, index, allow}; GET /api/generations/{id} carries `allow` (what can be allowed now)
- **`GET /api/generations/removed`** — The batches in the trash, newest first: {batches: [{id, number, removed, by, subject}]} (owner only)
- **`POST /api/generations/{id}/remove`** — Move a batch to out/trash/batches (nothing is deleted); 409 in words while a job for it is in flight. Returns {id, number, removed, by}
- **`POST /api/generations/{id}/restore`** — Put a removed batch back under the same name; 409 if a batch with that number exists now. Returns {id, number, restored}
- **`POST /api/generations/{id}/drop`** — Drop or restore a sticker from the set
- **`POST /api/generations/{id}/animate`** — Animate a prepared video (no provider)
- **`POST /api/generations/{id}/appearance`** — Set the outline / trim of the batch
- **`POST /api/generations/{id}/edge`** — Apply or undo an edge snapshot
- **`POST /api/generations/{id}/reslice`** — Re-cut the animations from the stored video with the current edge
- **`POST /api/generations/{id}/recheck`** — Run the border check on animations made before it existed
- **`POST /api/generations/{id}/edit`** — Save an edited still in place
- **`POST /api/generations/{id}/studio_edit`** — Layered edit of a sticker and its animation (open / commit)
- **`POST /api/generations/{id}/add`** — Add the approved stickers to a pack
- **`POST /api/generations/{id}/pack_add`** — Add chosen stickers to a pack
- **`POST /api/generations/{id}/recut_particles`** — A sheet of particles that was cut as stickers (a layout read from gutters, sticker rules on every cell, 512 px canvases) is cut again AS PARTICLES from the stored sheet, free: exact equal cells, no sticker rule blocks a cell. 409 when it already is a particle batch or a sticker was decided
- **`POST /api/generations/{id}/recut`** — "Cut it anyway": cut a batch whose sheet was stopped, from the stored sheet, free (409 once a sticker was decided)
- **`POST /api/generations/{id}/reveal`** — Open the batch's folder in the file manager
- **`GET /api/history`** — Every batch, the most recently edited first, a page at a time (?offset, ?limit): {items: [{id, generation_id, prompt, created, edited, stage, error, ready, animated, grid: [rows, cols], cells: [{index, row, col, png, status, animated}], outline_px}], more, total}. The grid is the sheet's own (2x2 or 3x3, read from result.json) so a card can draw it as it was cut
- **`GET /api/inputs`** — The prepared sheets found in the watch folders
- **`POST /api/live/cost`** — Price one call of a model (a quote, free)
- **`POST /api/live/sheet`** — Reserve a task (the G1 approval) and start the sheet job; spends credits. Idempotency-Key supported
- **`POST /api/live/video`** — Start the Kling job for a built video sheet; spends credits. Idempotency-Key supported. Optional video_prompt (max 6000) is sent verbatim
- **`POST /api/live/ref`** — Store a reference image (raw body, ?name=)
- **`GET /api/jobs`** — Jobs for the operator, newest first
- **`POST /api/jobs`** — Create a job file
- **`GET /api/jobs/{id}`** — One job (the page polls it while waiting)
- **`POST /api/jobs/{id}/claim`** — Operator (owner only): store the provider ticket BEFORE waiting {ticket}
- **`POST /api/jobs/{id}/done`** — Operator (owner only): attach the finished file {file, model, cost?}
- **`POST /api/jobs/{id}/fail`** — Operator (owner only): mark the job failed {reason}
- **`POST /api/jobs/{id}/requeue`** — Operator (owner only): a TIMEOUT / FAILED job asks again; a job that holds a provider ticket waits for the same provider job (no second charge)
- **`POST /api/jobs/{id}/check`** — One free read-only provider get; completed results are downloaded and reconciled by the same ticket. Human history records DIVERGENCE when local FAILED/TIMEOUT disagrees
- **`POST /api/jobs/{id}/continue`** — Continue a stalled job on its stored ticket via jobs.resume; never creates a paid request. 409 without a ticket or while already waiting
- **`POST /api/jobs/{id}/dismiss`** — Take a finished or failed job off the queue for good, for every browser (dismissed: {at, by}); the job itself stays. 409 while it is still running
- **`POST /api/jobs/{id}/retry_estimate`** — Quote a new paid Retry; {credits, message}. Creates no provider request
- **`POST /api/jobs/{id}/retry`** — Explicit PAID re-request of a FAILED/TIMEOUT job; requires a current quoted estimate and go: true. Repeated requests return the same replacement job
- **`GET /api/models`** — Curated models, every other Higgsfield model, and the style presets
- **`GET /api/higgsfield`** — Is the CLI there, the balance, today's spend (never a credential)
- **`GET /api/usage`** — The model-call ledger rolled up
- **`GET /api/metrics`** — Quality and timing numbers over every batch (owner only): time to the first sticker, approval rates at the two gates, the regeneration rate, per-batch lines
- **`GET /api/ai`** — Is a language model available (never the key): the active backend, the person's choice and what is available
- **`POST /api/ai/backend`** — Choose the AI backend {backend: auto | local | cloud} and/or the local model {model: an id GET /api/llm/models lists; any other is a 400 that carries the list} (owner only; auto keeps a working backend and only a failed call switches it)
- **`GET /api/llm/models`** — The local server's chat models ({models: [{id, loaded: null | bool}], current, preference, chosen, configured, ok, why}): the one in use, and whether it can ANSWER (a real probe, cached), with the plain reason when not
- **`GET /api/vision`** — The vision judge: model and policy
- **`POST /api/plan`** — Preview a plan; nothing is reserved
- **`GET /api/tasks`** — Reserved tasks
- **`POST /api/tasks`** — Reserve a task (the G1 approval)
- **`GET /api/tasks/{id}`** — One task
- **`GET /api/inbox`** — The Inbox state: tasks and watch folders
- **`GET /out/{path}`** — A generated file (the path is resolved, then checked against the root)
- **`POST /api/assets/sign`** — A signed, expiring link to one file under out/
- **`GET /api/assets/{token}`** — Serve a signed link until it expires (403 when forged or expired)
- **`GET /api/library`** — Packs, recent stickers, totals
- **`POST /api/packs`** — Create a pack
- **`POST /api/packs/{id}`** — Rename, reorder or set the cover of a pack
- **`POST /api/packs/{id}/delete`** — Delete a pack: SOFT, it goes to the trash with its stickers and files untouched (GET /api/trash lists it). Returns {ok, id, trashed, name, stickers}
- **`POST /api/packs/{id}/restore`** — Put a deleted pack back from the trash under the same id, stickers and cover untouched (404 when it is not in the trash). Returns {ok, id, restored, name, stickers}
- **`POST /api/packs/{id}/stickers`** — Add a sticker to a pack
- **`POST /api/packs/{id}/render`** — Save the editor's 512x512 canvas as a sticker (raw PNG body)
- **`POST /api/packs/{id}/stickers/{sid}`** — Update a sticker
- **`POST /api/packs/{id}/stickers/{sid}/animate`** — Animate a library sticker
- **`POST /api/packs/{id}/stickers/{sid}/move`** — Move one sticker into another pack: {to}
- **`POST /api/stickers/move`** — Bulk move into one pack, all or nothing: {to, items: [{pack_id, id}]} -> {moved, skipped, to}
- **`POST /api/packs/{id}/stickers/{sid}/delete`** — Remove a sticker
- **`POST /api/stickers/delete`** — Bulk delete: [{pack_id, id}]
- **`POST /api/cutout`** — A photo (raw body) becomes a cut-out PNG; X-Cutout header describes the method
- **`POST /api/packs/{id}/telegram`** — Create the pack on Telegram, or add what is new. Body {name?, mode?}: mode once (default: the same content is never sent twice, the earlier export is returned with already=true and Telegram is not called), replace (send on purpose) or new_set (a second numbered set); every send is recorded
- **`GET /api/packs/{id}/telegram`** — Dry run: what would be created and every problem
- **`GET /api/packs/{id}/stickers/{sid}/particles`** — The particles of one sticker, newest first: {sticker, pack_id, created: [{effect, result, mode, status, bytes, warnings, url, added_to (the library's word), shared, cell?, usable, missing}], saved: [library stickers made from them, any pack], effects: [ids], can_make}; a member gets it empty
- **`GET /api/packs/{id}/particles`** — The pack's particle studio in one read: {pack_id, sets[] (the sets assigned to it, cards as in GET /api/particles), bursts[] (every burst rendered for it, with its warnings and whether it is in the pack), counts: {sticker id: {created, saved}}} (docs/particles.md sections 5-6); a member gets {}
- **`GET /api/packs/{id}/export.zip`** — Download the pack: every sticker file (.webm animated, .png / .webp static, the engine's file names) and a manifest.json (application/zip)
- **`GET /api/packs/{id}/telegram.zip`** — No-credentials fallback: the files for @stickers (application/zip)
- **`GET /api/telegram`** — Connected or not and which bot (never the token)
- **`POST /api/telegram/config`** — Save the bot token and user id
- **`POST /api/telegram/disconnect`** — Forget the token
- **`GET /api/projects`** — Video / GIF projects
- **`POST /api/projects`** — Import a video or GIF (raw body, ?name=)
- **`GET /api/projects/{id}`** — One project
- **`POST /api/projects/{id}`** — Update a project (autosave)
- **`POST /api/projects/{id}/delete`** — Delete a project
- **`POST /api/projects/{id}/render`** — Render a project to WebM / WebP / GIF
- **`POST /api/projects/from_sticker`** — Open an animated sticker as a project
- **`GET /api/watch`** — The watch folders side by side, plus the trash
- **`POST /api/watch/remove`** — Move a folder pair to the trash
- **`POST /api/watch/restore`** — Restore a folder pair under its own names
- **`POST /api/watch/purge`** — Delete a trashed pair for good
- **`GET /api/trash`** — Everything in the trash with exactly what a purge would remove (owner only): {batches: [{type: 'batch', id, number, subject, removed, by, stickers, content, files_total, bytes, files: [{path, bytes}] (first 40; files_truncated), db: {available, reason?, stickers, indexed, shared_in_pool, vectors, assets, events, video_sheets, reviews_kept, tasks_kept}, copies_in_packs: [{id, name, stickers, trashed}] (they stay), shared: {pool, packs}, in_flight[], needs_confirm, confirm_words, blocked}], packs: [{type: 'pack', id, name, deleted, by, stickers, files: [{sticker, name, file, bytes, missing, shared}], files_total, bytes, shared: [{sticker, name, file, also_in: [{id, name, trashed}]}], from_batches[], particle_sets[], needs_confirm, confirm_words, blocked}], totals, purge_all: {count, phrase, skipped[]}, database, purge (the last purge task or null), record (the last 20 ledger lines)}
- **`POST /api/trash/purge`** — Delete ONE trashed batch or pack for good: {type: batch|pack, id, confirm_shared?}. Refused 404 when it is not in the trash, 409 in words while a job is in flight or a purge is running, and 409 naming the packs (or the shared pool) until {confirm_shared: true} when it shares a sticker file with another pack or has stickers in the shared pool. Runs in its own thread: 200 + the finished task, or 202 + the running task to poll at GET /api/trash/purges/{id}. Idempotent: an interrupted purge is run again; an item purged before answers 200 with {already: true}
- **`POST /api/trash/purge_all`** — Delete everything in the trash that needs no confirmation of its own: {confirm: 'purge N'} where N is the count GET /api/trash gives in purge_all (409 in words when the typed phrase or the count no longer matches the trash). Items that share stickers or have a job in flight are skipped and listed in `refused`, in words. Same 200 / 202 answer as purge; nothing to delete is a 200 with nothing_to_do
- **`GET /api/trash/purges/{id}`** — The progress of a purge: {id, status: running|done|failed|interrupted, total, done, items[], results[], refused[], error, by, started, finished}
- **`GET /api/watch/thumb/{name}`** — A cached thumbnail of a sheet folder (image/jpeg)
- **`GET /api/search`** — Search stickers (Postgres when up, else files); ?q=
- **`GET /api/health`** — Every dependency reports itself; nothing raises
- **`GET /api/health/models`** — Language, vision and tracing status
- **`GET /api/health/storage`** — The out/ folder: free space, generations, who holds the writer lock
- **`GET /api/openapi.json`** — This document

## Static/source routes outside the OpenAPI operation table

| Method/path | Authentication | Response and guard |
| --- | --- | --- |
| GET `/` | public static exception |200 index.html bytes, text/html UTF-8, no-store |
| GET `/ui/{file}` | public static exception |200 only for exact `UI_FILES` allowlist; guessed listed CSS/JS/font content type, UTF-8 appended except fonts; unlisted name reaches404 no such route. Do not expose arbitrary console files through a mount |
| GET `/assets/welcome/{name}` | public static exception |200/206 only for `placeholders.WELCOME` regex names and real welcome files; Range supported;404 not found |
| GET `/assets/{kind}/{name}` | public static exception |200 `placeholders.find(kind,name)` bytes/type; nonmatching names404 not found |
| GET `/src/{gid}/video` | owner or owned source batch |200/206 only the prepared video path recorded in that generation's source; missing file404 not found |
| GET `/src/{gid}/clip/{index}` | owner or owned source batch |200/206 only source.clips[index].webm; missing file404 not found |
| GET `/lib/{path}` | owner |resolved containment under library/files,400 forbidden path if outside;404 not found if absent;200/206 media, Range supported |
| GET `/proj/{id}/f/{frame}` | owner |integer frame path through Projects.frame_path,200/206 PNG; nonnumeric/malformed404 not found |
| GET `/proj/{id}/mask/{frame}.png` | owner |integer mask path through Projects.mask_path,200/206 PNG; malformed404 not found |

`/out/{path}` resolves percent-decoded path against resolved out root; requires root in resolved file.parents. Traversal/absolute paths/symlinks leaving the root produce400 `forbidden path`. A symlink that stays inside out is not categorically rejected by existing containment. Owners can read an existing resolved out file; member authorization first applies `_out_batch` to the resolved file, denies nonbatch paths with403 and other owners' batches404. Owner reads do not independently exclude users.json/telegram.json; member reads do. This source detail must not silently be changed by a broad mount. Unlike `_file`, out responses currently do not support Range.

`_file` returns Accept-Ranges:bytes; a bytes range returns206 with Content-Range and sliced data (including suffix ranges). Do not substitute stricter Range416 behavior without a contract decision. ZIP exports set Content-Disposition attachment with the computed filename. Project render/cutout/sticker animation expose X-Render/X-Cutout/X-Animate only on their raw response branches.

## Durable particles and exact override contracts

POST `/api/particles` dispatch order is significant: truthy `from_stickers`, then `from_generation`, `from_video`, `from_slices`, `from_effect`, then empty create. Shared optional fields `owners:[sticker-id or {sticker_id,pack_id?}]`, `name`, `target`; generation/effect/empty also accept deprecated `packs`. Recovery requires `parent_pack_id` and source library IDs; owners are destination stickers, not automatically the sources. `from_video` adds optional `picked` source cell indices and imports explicitly in video mode. `from_slices:[{generation,index}]` copies selected static slices; target appends. Empty creation accepts `kind:drawn|stickers|video`, `elements`, name/owners/packs. Imported cell JSON additively includes static poster `url`, animated `clip_url`, `type`, `fps`, `frames`, `duration`; clips/timelines preserve internal motion. Set responses retain `owner`, derived `packs`, `detached`, `source.kind/job/jobs`, credits, cells, picked, motion, renders, affirmed_in, drawing/sheets/notes/history.

POST `/api/particles/{id}/more` mode explicitly selects `video|drawn|image|stickers` or defaults source kind. Video quotes return effect context (`effect`) for the go request and use `group,grid,elements,subject,model,options,go,particle_target` through effects. Image flow uses `grid,elements,model,options,estimate,go` through more_plan/_price_sheet/live. Both quote first; missing CLI503, missing price409, no paid consent409 carrying estimate, disabled/cannot-spend403. Existing source-specific job contexts differ; preserve them instead of forcing one closed response.

POST `/api/generations/{id}/allow`: `kind` default animation; still/animation picks `index` integer, `indexes` list or truthy `all`; `allow` defaults true and is bool-converted. `video_sheet` accepts `sheet` or `index` as A# string, `indexes` strings or all. Response202 `{id,kind,indexes,index:indexes[0],allow}`. Exact errors include `kind must be 'still' or 'animation'`, `index (a sticker number), indexes (a list) or all is required`, `sheet (A#), indexes (a list of A#) or all is required`,409 `There is nothing to allow.` / `Nothing was allowed in this batch.`; technical/check errors remain gate-specific. Generation snapshots retain `waived` and per-sticker `allow.{still,animation}.{can,allowed,undo,why,final}` plus video-sheet override data without model filtering. A rejected picture's warning and reversible override remain engine data.

Member pack-particles read branches intentionally return `{}` for pack and `{sticker,created:[],saved:[],effects:[],can_make:false}` for sticker. At the inventory reading checkpoint, the particle-preview handler also returns `{set:null,url:null}` for members but its role map rejects that path first; reconcile this in the particle phase before freezing the migration baseline.

## Spec conflicts and migration risks requiring an explicit compatibility decision

These are observed differences, not proposed redesigns:

1. `runtime.events.list` named by the spec does not exist; actual API is `events.read`. SSE keepalive currently5seconds versus specified15; agent HTTP is polling, not SSE.
2. Engine auth has no cookie support; the cookie belongs to paused hosted gateway. Preserve existing gateway authentication too, although the migration's short auth paragraph omits it.
3. TrustedHost's default validation ignores the legacy exact port whitelist and produces different400/plain-text failures. CORSMiddleware can add preflight behavior and refuse requests before the recorded JSON guards. Preserve Host/Origin/Sec-Fetch-Site wording/status/order before body reads.
4. Spec's per-hashed-IP limiter and middleware reordering are additions: current limiter is token/user only after authentication and authorization. Rate-limit activation is still paused. This must be reconciled without enabling new infrastructure behavior.
5. StaticFiles normally exposes directories differently and supplies Range/cache/404 behavior absent from `/out` or UI allowlist. Existing containment allows symlinks staying inside root; spec's blanket symlink rejection differs. `/lib`, `/proj`, `/src`, thumbnail and signed routes also need their existing gates, not just the three named mounts.
6. `tests/__init__.py::serve` does not exist. Named suites import `console.server.serve` directly. Its `block=False` contract returns `(server, Console)` and tests use `server_address`, `serve_forever`, `shutdown`, `server_close`, `release_writer`. Both transports need this seam to remain testable during one-release A/B.
7. Several hand-schema statuses/shapes already drift: video attachment200 documented/202 actual, recheck202 documented/200 actual, animate202 documented/200 noop branch, removed-batches respNone/documented success actually JSON, project render may JSON on save. Source dispatch is the baseline; no-route probes alone do not catch these.
8. The hand schema requires JSON request bodies and strict known fields where current dispatch accepts an empty body, ignores unknown fields, accepts aliases or bool/string conversions. Review index may be A#; Judge schema omits required consent; Settings schema omits creator/allow_vlm. Raw uploads are not multipart. Pydantic validation must preserve these existing cases and exact400/409 errors, not introduce422/filter data.
9. Response-model filtering, added defaults and compact JSONResponse serialization change exact bytes. Existing response records are often open stored dictionaries; the typed migration must preserve all fields and ordering.
10. Agent `State` is already `TypedDict(total=False)`, not an untyped plain dict. Typing payloads must not alter graph state, routing or multi-turn behavior (explicit scope exclusion).
11. Deployment §3.3–3.5 includes hosted mandatory DB/Redis/storage, containers and a second machine, all beyond authorized local migration. Keep those paused. `Console` construction/writer lock and close semantics must survive local lifespan; do not claim hosted readiness from HTTP migration tests.

## Schema appendix (existing hand-written reference, not additional validation)

The complete component shapes below are copied from the current schema definitions so this inventory survives replacement of `console/openapi.py`. Dispatch-specific supplements above take precedence wherever the old document is incomplete.

### Error

```json
{
  "type": "object",
  "properties": {
    "error": {
      "type": "string"
    }
  },
  "additionalProperties": false,
  "required": [
    "error"
  ]
}
```

### Settings

```json
{
  "type": "object",
  "properties": {
    "grid": {
      "type": "string",
      "enum": [
        "3x3",
        "2x2"
      ]
    },
    "style_id": {
      "type": "string"
    },
    "ask_before_spending": {
      "type": "boolean"
    },
    "ai": {
      "type": "boolean"
    }
  },
  "additionalProperties": false
}
```

### Step

```json
{
  "type": "object",
  "properties": {
    "kind": {
      "type": "string",
      "enum": [
        "task",
        "step",
        "note",
        "final"
      ]
    },
    "label": {
      "type": "string"
    },
    "detail": {
      "anyOf": [
        {
          "type": "object",
          "properties": {
            "lines": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "additionalProperties": true
        },
        {
          "type": "null"
        }
      ]
    },
    "status": {
      "type": "string",
      "enum": [
        "running",
        "done",
        "error"
      ]
    },
    "ts": {
      "type": "number"
    }
  },
  "additionalProperties": false,
  "required": [
    "kind",
    "label"
  ]
}
```

### Sticker

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "G012/S3"
    },
    "index": {
      "type": "integer"
    },
    "key": {
      "type": "string"
    },
    "name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "emoji": {
      "anyOf": [
        {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        {
          "type": "null"
        }
      ]
    },
    "status": {
      "type": "string"
    },
    "reason": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "still": {
      "type": "string"
    },
    "anim": {
      "type": "string"
    },
    "anim_status": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "png": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "webm": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "additionalProperties": true,
  "required": [
    "id",
    "index"
  ]
}
```

### GenerationCard

```json
{
  "type": "object",
  "properties": {
    "generation": {
      "type": "string"
    },
    "stage": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "error": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "prompt": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "parent": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "video_sheets": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string"
          },
          "picture": {
            "type": "string"
          },
          "status": {
            "type": "string"
          }
        },
        "additionalProperties": true
      }
    },
    "stickers": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Sticker"
      }
    }
  },
  "additionalProperties": true,
  "required": [
    "generation"
  ]
}
```

### Card

```json
{
  "type": "object",
  "properties": {
    "type": {
      "type": "string",
      "enum": [
        "plan",
        "generation",
        "stickers"
      ]
    },
    "generation": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "job": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "subject": {
      "type": "string"
    },
    "job_status": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "data": {
      "$ref": "#/components/schemas/GenerationCard"
    }
  },
  "additionalProperties": true,
  "required": [
    "type"
  ]
}
```

### Chip

```json
{
  "type": "object",
  "properties": {
    "label": {
      "type": "string"
    },
    "text": {
      "type": "string"
    },
    "action": {
      "type": "string",
      "enum": [
        "confirm",
        "cancel"
      ]
    }
  },
  "additionalProperties": false,
  "required": [
    "label"
  ]
}
```

### Message

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "role": {
      "type": "string",
      "enum": [
        "user",
        "assistant"
      ]
    },
    "text": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": [
        "working",
        "done",
        "error"
      ]
    },
    "steps": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Step"
      }
    },
    "cards": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Card"
      }
    },
    "chips": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Chip"
      }
    },
    "ts": {
      "type": "number"
    }
  },
  "additionalProperties": true,
  "required": [
    "id",
    "role",
    "text"
  ]
}
```

### SessionSummary

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "title": {
      "type": "string"
    },
    "updated": {
      "type": "number"
    },
    "created": {
      "type": "number"
    },
    "subjects": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "turns": {
      "type": "integer"
    },
    "focus": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "additionalProperties": false,
  "required": [
    "id"
  ]
}
```

### Session

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "user": {
      "type": "string"
    },
    "title": {
      "type": "string"
    },
    "settings": {
      "$ref": "#/components/schemas/Settings"
    },
    "focus": {
      "type": "object",
      "properties": {
        "generation": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ]
        },
        "stickers": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "additionalProperties": false
    },
    "subjects": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": true
      }
    },
    "preferences": {
      "type": "object",
      "additionalProperties": true
    },
    "feedback": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": true
      }
    },
    "interactions": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": true
      }
    },
    "pending": {
      "anyOf": [
        {
          "type": "object",
          "additionalProperties": true
        },
        {
          "type": "null"
        }
      ]
    },
    "messages": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/Message"
      }
    },
    "working": {
      "type": "boolean"
    },
    "summary_text": {
      "type": "string"
    }
  },
  "additionalProperties": true,
  "required": [
    "id"
  ]
}
```

### ChatSend

```json
{
  "type": "object",
  "properties": {
    "text": {
      "type": "string"
    },
    "selected": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "action": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "enum": [
            "confirm",
            "cancel"
          ]
        }
      },
      "additionalProperties": false,
      "required": [
        "type"
      ]
    }
  },
  "additionalProperties": false
}
```

### Accepted

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "message": {
      "type": "string"
    },
    "idempotent": {
      "type": "boolean"
    }
  },
  "additionalProperties": true,
  "required": [
    "id"
  ]
}
```

### GenerationCreate

```json
{
  "type": "object",
  "properties": {
    "prompt": {
      "type": "string"
    },
    "variant": {
      "type": "integer"
    },
    "outline": {
      "type": "integer"
    },
    "erode": {
      "type": "integer"
    }
  },
  "additionalProperties": false,
  "required": [
    "prompt"
  ]
}
```

### GenerationCreated

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "integer"
    },
    "idempotent": {
      "type": "boolean"
    }
  },
  "additionalProperties": false,
  "required": [
    "id"
  ]
}
```

### Review

```json
{
  "type": "object",
  "properties": {
    "gate": {
      "type": "string",
      "enum": [
        "plan",
        "still",
        "video_sheet",
        "anim",
        "pack"
      ]
    },
    "decision": {
      "type": "string",
      "enum": [
        "APPROVE",
        "REJECT"
      ]
    },
    "index": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ]
    },
    "note": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "additionalProperties": false,
  "required": [
    "gate",
    "decision"
  ]
}
```

### Judge

```json
{
  "type": "object",
  "properties": {
    "scope": {
      "type": "string",
      "enum": [
        "still",
        "anim"
      ]
    },
    "force": {
      "type": "boolean"
    }
  },
  "additionalProperties": false
}
```

### Event

```json
{
  "type": "object",
  "properties": {
    "event": {
      "type": "string"
    },
    "generation_id": {
      "type": "string"
    },
    "stage": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "status": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "ts": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ]
    },
    "ms": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ]
    },
    "actor": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "decision": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "gate": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "index": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ]
    },
    "sticker_id": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "asset_url": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "trace_run_id": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "additionalProperties": false,
  "required": [
    "event",
    "generation_id"
  ]
}
```

### AssetSign

```json
{
  "type": "object",
  "properties": {
    "key": {
      "type": "string",
      "description": "a path under out/, e.g. G002/slices/x.png"
    },
    "ttl": {
      "type": "integer",
      "minimum": 5,
      "maximum": 3600
    }
  },
  "additionalProperties": false,
  "required": [
    "key"
  ]
}
```

### AssetLink

```json
{
  "type": "object",
  "properties": {
    "url": {
      "type": "string"
    },
    "expires_in": {
      "type": "integer"
    }
  },
  "additionalProperties": false,
  "required": [
    "url",
    "expires_in"
  ]
}
```

### Health

```json
{
  "type": "object",
  "properties": {
    "ok": {
      "type": "boolean"
    },
    "database": {
      "type": "object",
      "additionalProperties": true
    },
    "redis": {
      "type": "object",
      "additionalProperties": true
    },
    "models": {
      "type": "object",
      "additionalProperties": true
    },
    "providers": {
      "type": "object",
      "additionalProperties": true
    },
    "storage": {
      "type": "object",
      "additionalProperties": true
    },
    "warnings": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "ms": {
      "type": "integer"
    }
  },
  "additionalProperties": true,
  "required": [
    "ok"
  ]
}
```

### Job

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "kind": {
      "type": "string",
      "enum": [
        "sheet",
        "video",
        "single"
      ]
    },
    "status": {
      "type": "string",
      "enum": [
        "REQUESTED",
        "CLAIMED",
        "DONE",
        "FAILED",
        "TIMEOUT"
      ]
    },
    "external_task_id": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "generation": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "model": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "cost": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ]
    },
    "error": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "provider_check": {
      "type": "object",
      "properties": {
        "status": {
          "type": "string"
        },
        "checked_at": {
          "type": "number"
        },
        "classification": {
          "type": "string"
        },
        "message": {
          "type": "string"
        }
      },
      "additionalProperties": false
    },
    "history": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": true
      }
    },
    "retry_of": {
      "type": "string"
    },
    "retried_as": {
      "type": "string"
    }
  },
  "additionalProperties": true,
  "required": [
    "id",
    "kind",
    "status"
  ]
}
```

### LiveSheet

```json
{
  "type": "object",
  "properties": {
    "prompt": {
      "type": "string"
    },
    "grid": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    },
    "ai": {
      "type": "boolean"
    },
    "refs": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "model": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "outline": {
      "type": "integer"
    },
    "erode": {
      "type": "integer"
    },
    "parent": {
      "type": "string"
    },
    "regen_of": {
      "type": "string"
    },
    "from_generation": {
      "type": "integer"
    },
    "sheet_prompt": {
      "type": "string",
      "maxLength": 6000,
      "description": "the prompt exactly as written (the Prompt tab); with from_generation the new sheet keeps that batch's cells and tags"
    },
    "plan": {
      "type": "object",
      "description": "the plan Generate prompt (`POST /api/plan`) returned, sent back so the batch keeps the cells, tags and emoji the person saw (an AI-written draft costs no second model call). Untrusted: only slots.cells (pos, label, tags, emoji, motion), slots.subject_description and slots.key_colour are read, re-linted and the prompts rebuilt from the template; max 64 KB, exactly one cell per grid slot, not together with from_generation; an invalid plan is a 400 in words; left out, the request is planned as before",
      "additionalProperties": true
    }
  },
  "additionalProperties": false,
  "required": [
    "prompt"
  ]
}
```

### LiveJob

```json
{
  "type": "object",
  "properties": {
    "job": {
      "type": "string"
    },
    "task": {
      "type": "string"
    },
    "estimate": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ]
    },
    "model": {
      "type": "string"
    }
  },
  "additionalProperties": true,
  "required": [
    "job"
  ]
}
```

### User

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "role": {
      "type": "string",
      "enum": [
        "owner",
        "member"
      ]
    },
    "can_spend": {
      "type": "boolean"
    },
    "created": {
      "type": "number"
    },
    "disabled": {
      "type": "boolean"
    }
  },
  "additionalProperties": false,
  "required": [
    "id",
    "name",
    "role"
  ]
}
```

### UserCreate

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "role": {
      "type": "string",
      "enum": [
        "owner",
        "member"
      ]
    },
    "can_spend": {
      "type": "boolean"
    }
  },
  "additionalProperties": false,
  "required": [
    "name"
  ]
}
```

### UserUpdate

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "role": {
      "type": "string",
      "enum": [
        "owner",
        "member"
      ]
    },
    "can_spend": {
      "type": "boolean"
    }
  },
  "additionalProperties": false
}
```

### UserWithToken

```json
{
  "type": "object",
  "properties": {
    "user": {
      "$ref": "#/components/schemas/User"
    },
    "token": {
      "type": "string",
      "description": "shown once; only its SHA-256 is stored"
    }
  },
  "additionalProperties": false,
  "required": [
    "user",
    "token"
  ]
}
```

### Me

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "role": {
      "type": "string",
      "enum": [
        "owner",
        "member"
      ]
    },
    "can_spend": {
      "type": "boolean"
    },
    "via": {
      "type": "string",
      "enum": [
        "token",
        "page",
        "open"
      ]
    }
  },
  "additionalProperties": false,
  "required": [
    "id",
    "role"
  ]
}
```

### PoolHit

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "key": {
      "type": "string"
    },
    "png": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "emoji": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "additionalProperties": false
}
```


## Native imports and per-person packs (2026-10-05)

`console/app.py` handles POST `/api/import`, GET `/api/higgsfield/history`, and POST `/api/higgsfield/import` before the adapter, with pydantic request validation and owner-only access. The legacy handler delegates to the same flow functions for `serve --stdlib`. Import raw-body and duplicate/recovery contracts are in `api.md`; OpenAPI declares the binary request and query fields.

GET `/api/library` filters by caller; pack creation stamps owner. Existing pack/file routes check ownership, including the owner's account, and validate merge/move destinations and batch visibility. Members may Add to their own packs but cannot use Telegram routes. Trending native routes (also versioned) support maker sharing, maker/staff unsharing, `/view` with one UTC-day view per viewer, and `/use` returning an owned copy for all accounts. OpenAPI now includes the public-pack routes and relative attention fields.

## Help & Support (native, 2026-10-05)

`console/app.py` serves these before the adapter, with pydantic bodies (`app_models.py` `SupportAsk`, `SupportFeedback`, `SupportText`, `SupportReopen`, `TicketResolve`, `FaqEdit`, `NotificationsRead`) and `/api/v1/` aliases:
- for everyone signed in and approved: `/api/support/ask`, `/api/support/conversations[/{id}[/feedback|escalate|reply|reopen|images/{name}]]`, `/api/notifications[/read]`, GET `/api/faq[/{id}]`;
- for the owner and admins (`_staff`): `/api/support/queue`, `/api/support/tickets/{id}`, `/api/tickets/{id}/reply|resolve`, POST `/api/faq/{id}/edit|publish|discard|archive`, `/api/support/status|reindex`.

An unknown action on these families answers the route miss (`NO_ROUTE`). `serve --stdlib` does not serve them. The contract is in `api.md` "Help & Support"; OpenAPI describes every route.
