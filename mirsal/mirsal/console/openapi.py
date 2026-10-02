"""The HTTP contract as an OpenAPI 3.1 document, served at GET /api/openapi.json and turned into TypeScript types by `python -m mirsal openapi --ts FILE`.

One table of routes, written by hand next to the server it describes. `tests/test_openapi.py` reads the server's source and fails when a route
exists in the server that this table does not describe (drift guard), so the spec cannot silently rot. Bodies and responses are typed where an
integrator needs them (chat, generations, review, judge, assets, health, jobs, live generation) and `object` where the Studio's own screens are
the only caller. Everything is JSON, `{"error": "..."}` on failure, ids everywhere, Bearer token optional (see docs/api.md)."""
from __future__ import annotations

VERSION = "1.0.0"

STR = {"type": "string"}
INT = {"type": "integer"}
NUM = {"type": "number"}
BOOL = {"type": "boolean"}
OBJ = {"type": "object", "additionalProperties": True}


def arr(x):
    return {"type": "array", "items": x}


def ref(n):
    return {"$ref": f"#/components/schemas/{n}"}


def obj(props: dict, required: list | None = None, extra: bool = False):
    d = {"type": "object", "properties": props, "additionalProperties": extra}
    if required:
        d["required"] = required
    return d


def nullable(x):
    return {"anyOf": [x, {"type": "null"}]}


SCHEMAS = {
    "Error": obj({"error": STR}, ["error"]),
    "Settings": obj({"grid": {"type": "string", "enum": ["3x3", "2x2"]}, "style_id": STR, "ask_before_spending": BOOL, "ai": BOOL}),
    "Step": obj({"kind": {"type": "string", "enum": ["task", "step", "note", "final"]}, "label": STR, "detail": nullable(obj({"lines": arr(STR)}, extra=True)),
                 "status": {"type": "string", "enum": ["running", "done", "error"]}, "ts": NUM}, ["kind", "label"]),
    "Sticker": obj({"id": {"type": "string", "description": "G012/S3"}, "index": INT, "key": STR, "name": nullable(STR), "emoji": nullable(arr(STR)),
                    "status": STR, "reason": nullable(STR), "still": STR, "anim": STR, "anim_status": nullable(STR), "png": nullable(STR), "webm": nullable(STR)}, ["id", "index"], True),
    "GenerationCard": obj({"generation": STR, "stage": nullable(STR), "error": nullable(STR), "prompt": nullable(STR), "parent": nullable(STR),
                           "stickers": arr(ref("Sticker"))}, ["generation"], True),
    "Card": obj({"type": {"type": "string", "enum": ["plan", "generation", "stickers"]}, "generation": nullable(STR), "job": nullable(STR), "subject": STR,
                 "job_status": nullable(STR), "data": ref("GenerationCard")}, ["type"], True),
    "Chip": obj({"label": STR, "text": STR, "action": {"type": "string", "enum": ["confirm", "cancel"]}}, ["label"]),
    "Message": obj({"id": STR, "role": {"type": "string", "enum": ["user", "assistant"]}, "text": STR, "status": {"type": "string", "enum": ["working", "done", "error"]},
                    "steps": arr(ref("Step")), "cards": arr(ref("Card")), "chips": arr(ref("Chip")), "ts": NUM}, ["id", "role", "text"], True),
    "SessionSummary": obj({"id": STR, "title": STR, "updated": NUM, "created": NUM, "subjects": arr(STR), "turns": INT, "focus": nullable(STR)}, ["id"]),
    "Session": obj({"id": STR, "user": STR, "title": STR, "settings": ref("Settings"), "focus": obj({"generation": nullable(STR), "stickers": arr(STR)}),
                    "subjects": arr(OBJ), "preferences": OBJ, "feedback": arr(OBJ), "interactions": arr(OBJ), "pending": nullable(OBJ),
                    "messages": arr(ref("Message")), "working": BOOL, "summary_text": STR}, ["id"], True),
    "ChatSend": obj({"text": STR, "selected": arr(STR), "action": obj({"type": {"type": "string", "enum": ["confirm", "cancel"]}}, ["type"])}),
    "Accepted": obj({"id": STR, "message": STR, "idempotent": BOOL}, ["id"], True),
    "GenerationCreate": obj({"prompt": STR, "variant": INT, "outline": INT, "erode": INT}, ["prompt"]),
    "GenerationCreated": obj({"id": INT, "idempotent": BOOL}, ["id"]),
    "Review": obj({"gate": {"type": "string", "enum": ["plan", "still", "video_sheet", "anim", "pack"]}, "decision": {"type": "string", "enum": ["APPROVE", "REJECT"]},
                   "index": nullable(INT), "note": nullable(STR)}, ["gate", "decision"]),
    "Judge": obj({"scope": {"type": "string", "enum": ["still", "anim"]}, "force": BOOL}),
    "Event": obj({"event": STR, "generation_id": STR, "stage": nullable(STR), "status": nullable(STR), "ts": nullable(NUM), "ms": nullable(INT), "actor": nullable(STR),
                  "decision": nullable(STR), "gate": nullable(STR), "index": nullable(INT), "sticker_id": nullable(STR), "asset_url": nullable(STR),
                  "trace_run_id": nullable(STR)}, ["event", "generation_id"]),
    "AssetSign": obj({"key": {"type": "string", "description": "a path under out/, e.g. G002/slices/x.png"}, "ttl": {"type": "integer", "minimum": 5, "maximum": 3600}}, ["key"]),
    "AssetLink": obj({"url": STR, "expires_in": INT}, ["url", "expires_in"]),
    "Health": obj({"ok": BOOL, "database": OBJ, "redis": OBJ, "models": OBJ, "providers": OBJ, "storage": OBJ, "warnings": arr(STR), "ms": INT}, ["ok"], True),
    "Job": obj({"id": STR, "kind": {"type": "string", "enum": ["sheet", "video", "single"]}, "status": {"type": "string", "enum": ["REQUESTED", "CLAIMED", "DONE", "FAILED", "TIMEOUT"]},
                "external_task_id": nullable(STR), "generation": nullable(STR), "model": nullable(STR), "cost": nullable(NUM), "error": nullable(STR)}, ["id", "kind", "status"], True),
    "LiveSheet": obj({"prompt": STR, "grid": STR, "style_id": STR, "ai": BOOL, "refs": arr(STR), "model": STR, "options": OBJ, "outline": INT, "parent": STR, "regen_of": STR,
                          "from_generation": INT, "sheet_prompt": {"type": "string", "maxLength": 6000, "description": "the prompt exactly as written (the Prompt tab); with from_generation the new sheet keeps that batch's cells and tags"}}, ["prompt"]),
    "LiveJob": obj({"job": STR, "task": STR, "estimate": nullable(NUM), "model": STR}, ["job"], True),
    "User": obj({"id": STR, "name": STR, "role": {"type": "string", "enum": ["owner", "member"]}, "can_spend": BOOL, "created": NUM, "disabled": BOOL}, ["id", "name", "role"]),
    "UserCreate": obj({"name": STR, "role": {"type": "string", "enum": ["owner", "member"]}, "can_spend": BOOL}, ["name"]),
    "UserUpdate": obj({"name": STR, "role": {"type": "string", "enum": ["owner", "member"]}, "can_spend": BOOL}),
    "UserWithToken": obj({"user": {"$ref": "#/components/schemas/User"}, "token": {"type": "string", "description": "shown once; only its SHA-256 is stored"}}, ["user", "token"]),
    "Me": obj({"id": STR, "name": nullable(STR), "role": {"type": "string", "enum": ["owner", "member"]}, "can_spend": BOOL,
               "via": {"type": "string", "enum": ["token", "page", "open"]}}, ["id", "role"]),
    "PoolHit": obj({"id": STR, "key": STR, "png": nullable(STR), "emoji": nullable(STR)}),
}

ERR = {"description": "error", "content": {"application/json": {"schema": ref("Error")}}}

# (method, path, tag, summary, request schema | None, response schema | None, status)
ROUTES = [
    # --- chat
    ("GET", "/api/chat/agent", "Chat", "Which model runs the assistant and the vision judge", None, OBJ, 200),
    ("GET", "/api/chat/sessions", "Chat", "List chats, newest first", None, obj({"sessions": arr(ref("SessionSummary"))}), 200),
    ("POST", "/api/chat/sessions", "Chat", "Create a chat", obj({"title": STR, "settings": ref("Settings")}), ref("Session"), 200),
    ("GET", "/api/chat/sessions/{id}", "Chat", "A whole chat for display: messages with steps and cards (generation cards carry their live stickers), memory summary", None, ref("Session"), 200),
    ("POST", "/api/chat/sessions/{id}/messages", "Chat", "Send a message or a button action; the turn runs in the background (409 while the last one runs). Idempotency-Key supported", ref("ChatSend"), ref("Accepted"), 202),
    ("POST", "/api/chat/sessions/{id}/settings", "Chat", "Grid, Ask-before-spending and style (unknown keys are ignored; an unknown style is a 400)", ref("Settings"), obj({"settings": ref("Settings")}), 200),
    ("POST", "/api/chat/sessions/{id}/delete", "Chat", "Delete a chat (its stickers stay)", None, obj({"deleted": STR}), 200),
    # --- accounts
    ("GET", "/api/me", "Accounts", "Who the server thinks you are and what you may do", None, ref("Me"), 200),
    ("GET", "/api/users", "Accounts", "Accounts (owner only; never a token)", None, obj({"users": arr(ref("User"))}), 200),
    ("POST", "/api/users", "Accounts", "Create an account; its token is returned once (owner only)", ref("UserCreate"), ref("UserWithToken"), 200),
    ("POST", "/api/users/{id}/update", "Accounts", "Change the name, the role or the right to spend (owner only)", ref("UserUpdate"), obj({"user": ref("User")}), 200),
    ("POST", "/api/users/{id}/disable", "Accounts", "Stop a token at once (owner only)", None, obj({"user": ref("User")}), 200),
    ("POST", "/api/users/{id}/enable", "Accounts", "Let a disabled account back in (owner only)", None, obj({"user": ref("User")}), 200),
    ("POST", "/api/users/{id}/rotate", "Accounts", "A new token; the old one stops working (owner only)", None, ref("UserWithToken"), 200),
    # --- generations
    ("GET", "/api/generations", "Generations", "Every batch (newest first) with the server's state", None, OBJ, 200),
    ("POST", "/api/generations", "Generations", "Start a batch from a prepared sheet, or run a reserved task. Idempotency-Key supported", ref("GenerationCreate"), ref("GenerationCreated"), 202),
    ("GET", "/api/generations/{id}", "Generations", "The full snapshot: result.json plus events", None, OBJ, 200),
    ("GET", "/api/generations/{id}/events", "Generations", "Server-sent events (Last-Event-ID or ?after= replays what was missed)", None, ref("Event"), 200),
    ("GET", "/api/generations/{id}/files", "Generations", "Where the batch's files are", None, OBJ, 200),
    ("GET", "/api/generations/{id}/edge_preview", "Generations", "One sticker with a stroke / trim, rendered on the fly (image/png)", None, None, 200),
    ("GET", "/api/generations/{id}/sheet_preview", "Generations", "The video sheet at a given fill (image/png)", None, None, 200),
    ("GET", "/api/generations/{id}/history", "Generations", "Every sticker's generation history, folded: {generation_id, stickers: [{id, index, key, name, status, review, lines, shown, last, stages: [{stage, count, last, lines}]}]}, decisions grouped by stage in the order they happened, newest line first; ?index=N for one sticker", None, OBJ, 200),
    ("POST", "/api/generations/{id}/more", "Generations", "The next prepared variation of the same subject", None, obj({"id": INT}), 202),
    ("POST", "/api/generations/{id}/regen", "Generations", "Regenerate one sticker as a 1x1 child batch", obj({"index": INT, "subject": STR}, ["index"]), obj({"id": INT}), 202),
    ("POST", "/api/generations/{id}/review", "Gates", "A human decision at a gate (Python's blocks are final)", ref("Review"), OBJ, 200),
    ("POST", "/api/generations/{id}/judge", "Gates", "The vision model pre-reviews the stickers (history lines only). Needs allow_vlm: true in the body (409 with consent_required otherwise): AI vision is the person's yes, asked once", ref("Judge"), obj({"id": INT, "scope": STR}), 202),
    ("GET", "/api/generations/{id}/captions", "Gates", "The stored AI caption of every cell of the sheet (grid read from result.json, 2x2 or 3x3): {generation_id, grid, cells: [{index, row, col, png, caption, text_visible, verdict, reasons, model}], missing, ready}. Read-only: no model, no consent", None, OBJ, 200),
    ("POST", "/api/generations/{id}/captions", "Gates", "Write the missing AI captions in the background (a model call per cell). Needs allow_vlm: true (409 with consent_required otherwise); {force?} captions again", obj({"allow_vlm": BOOL, "force": BOOL}, ["allow_vlm"]), obj({"id": INT, "force": BOOL}), 202),
    ("POST", "/api/generations/{id}/video_sheet", "Gates", "Build the video sheet from the approved stills", None, OBJ, 200),
    ("POST", "/api/generations/{id}/quick_sheet", "Gates", "Approve the kept stills, build and approve the video sheet (one click)", None, OBJ, 200),
    ("POST", "/api/generations/{id}/video_sheet/{aid}/video", "Gates", "Attach a returned video (raw body) to a video sheet and slice it", None, OBJ, 200),
    ("POST", "/api/generations/{id}/allow", "Gates", "Allow, or take back, an animation Python blocked for leaving or crossing its slot", obj({"index": INT, "all": BOOL, "allow": BOOL}), OBJ, 202),
    ("POST", "/api/generations/{id}/drop", "Gates", "Drop or restore a sticker from the set", obj({"index": INT, "dropped": BOOL}, ["index"]), OBJ, 200),
    ("POST", "/api/generations/{id}/animate", "Generations", "Animate a prepared video (no provider)", obj({"scope": STR, "index": INT}), OBJ, 202),
    ("POST", "/api/generations/{id}/appearance", "Generations", "Set the outline / trim of the batch", obj({"outline": INT, "erode": INT, "reslice": BOOL}), OBJ, 200),
    ("POST", "/api/generations/{id}/edge", "Generations", "Apply or undo an edge snapshot", obj({"outline": INT, "erode": INT, "via": STR}), obj({"id": INT}), 202),
    ("POST", "/api/generations/{id}/reslice", "Generations", "Re-cut the animations from the stored video with the current edge", None, obj({"id": INT}), 202),
    ("POST", "/api/generations/{id}/recheck", "Generations", "Run the border check on animations made before it existed", None, OBJ, 202),
    ("POST", "/api/generations/{id}/edit", "Generations", "Save an edited still in place", OBJ, OBJ, 200),
    ("POST", "/api/generations/{id}/studio_edit", "Generations", "Layered edit of a sticker and its animation (open / commit)", OBJ, OBJ, 200),
    ("POST", "/api/generations/{id}/add", "Packs", "Add the approved stickers to a pack", OBJ, OBJ, 200),
    ("POST", "/api/generations/{id}/pack_add", "Packs", "Add chosen stickers to a pack", OBJ, OBJ, 200),
    ("POST", "/api/generations/{id}/reveal", "Generations", "Open the batch's folder in the file manager", None, obj({"opened": STR}), 200),
    ("GET", "/api/history", "Generations", "Every batch, the most recently edited first, a page at a time (?offset, ?limit): {items: [{id, generation_id, prompt, created, edited, stage, error, ready, animated, grid: [rows, cols], cells: [{index, row, col, png, status, animated}], outline_px}], more, total}. The grid is the sheet's own (2x2 or 3x3, read from result.json) so a card can draw it as it was cut", None, OBJ, 200),
    ("GET", "/api/inputs", "Generations", "The prepared sheets found in the watch folders", None, OBJ, 200),
    # --- live generation
    ("POST", "/api/live/cost", "Live generation", "Price one call of a model (a quote, free)", OBJ, OBJ, 200),
    ("POST", "/api/live/sheet", "Live generation", "Reserve a task (the G1 approval) and start the sheet job; spends credits. Idempotency-Key supported", ref("LiveSheet"), ref("LiveJob"), 200),
    ("POST", "/api/live/video", "Live generation", "Start the Kling job for a built video sheet; spends credits. Idempotency-Key supported. Optional video_prompt (max 6000) is sent verbatim", OBJ, OBJ, 200),
    ("POST", "/api/live/ref", "Live generation", "Store a reference image (raw body, ?name=)", None, OBJ, 200),
    ("GET", "/api/jobs", "Live generation", "Jobs for the operator, newest first", None, obj({"jobs": arr(ref("Job"))}), 200),
    ("POST", "/api/jobs", "Live generation", "Create a job file", OBJ, ref("Job"), 200),
    ("GET", "/api/jobs/{id}", "Live generation", "One job (the page polls it while waiting)", None, ref("Job"), 200),
    ("POST", "/api/jobs/{id}/claim", "Live generation", "Operator (owner only): store the provider ticket BEFORE waiting {ticket}", OBJ, ref("Job"), 200),
    ("POST", "/api/jobs/{id}/done", "Live generation", "Operator (owner only): attach the finished file {file, model, cost?}", OBJ, ref("Job"), 200),
    ("POST", "/api/jobs/{id}/fail", "Live generation", "Operator (owner only): mark the job failed {reason}", OBJ, ref("Job"), 200),
    ("POST", "/api/jobs/{id}/requeue", "Live generation", "Operator (owner only): a TIMEOUT / FAILED job asks again; a job that holds a provider ticket waits for the same provider job (no second charge)", None, ref("Job"), 200),
    ("POST", "/api/jobs/{id}/retry", "Live generation", "A human retry of a FAILED / TIMEOUT job: the same provider job when it has a ticket, else a fresh request (owner only)", None, ref("Job"), 200),
    ("GET", "/api/models", "Live generation", "Curated models, every other Higgsfield model, and the style presets", None, OBJ, 200),
    ("GET", "/api/higgsfield", "Live generation", "Is the CLI there, the balance, today's spend (never a credential)", None, OBJ, 200),
    ("GET", "/api/usage", "Live generation", "The model-call ledger rolled up", None, OBJ, 200),
    ("GET", "/api/metrics", "Generations", "Quality and timing numbers over every batch (owner only): time to the first sticker, approval rates at the two gates, the regeneration rate, per-batch lines", None, OBJ, 200),
    ("GET", "/api/ai", "Live generation", "Is a language model available (never the key): the active backend, the person's choice and what is available", None, OBJ, 200),
    ("POST", "/api/ai/backend", "Live generation", "Choose the AI backend: {backend: auto | local | cloud} (owner only; auto keeps a working one and only a failed call switches it)", OBJ, OBJ, 200),
    ("GET", "/api/vision", "Gates", "The vision judge: model and policy", None, OBJ, 200),
    ("POST", "/api/plan", "Live generation", "Preview a plan; nothing is reserved", OBJ, OBJ, 200),
    ("GET", "/api/tasks", "Live generation", "Reserved tasks", None, OBJ, 200),
    ("POST", "/api/tasks", "Live generation", "Reserve a task (the G1 approval)", OBJ, OBJ, 200),
    ("GET", "/api/tasks/{id}", "Live generation", "One task", None, OBJ, 200),
    ("GET", "/api/inbox", "Live generation", "The Inbox state: tasks and watch folders", None, OBJ, 200),
    # --- files and signed links
    ("GET", "/out/{path}", "Files", "A generated file (the path is resolved, then checked against the root)", None, None, 200),
    ("POST", "/api/assets/sign", "Files", "A signed, expiring link to one file under out/", ref("AssetSign"), ref("AssetLink"), 200),
    ("GET", "/api/assets/{token}", "Files", "Serve a signed link until it expires (403 when forged or expired)", None, None, 200),
    # --- library and packs
    ("GET", "/api/library", "Library", "Packs, recent stickers, totals", None, OBJ, 200),
    ("POST", "/api/packs", "Library", "Create a pack", OBJ, OBJ, 200),
    ("POST", "/api/packs/{id}", "Library", "Rename, reorder or set the cover of a pack", OBJ, OBJ, 200),
    ("POST", "/api/packs/{id}/delete", "Library", "Delete a pack", None, OBJ, 200),
    ("POST", "/api/packs/{id}/stickers", "Library", "Add a sticker to a pack", OBJ, OBJ, 200),
    ("POST", "/api/packs/{id}/render", "Library", "Save the editor's 512x512 canvas as a sticker (raw PNG body)", None, OBJ, 200),
    ("POST", "/api/packs/{id}/stickers/{sid}", "Library", "Update a sticker", OBJ, OBJ, 200),
    ("POST", "/api/packs/{id}/stickers/{sid}/animate", "Library", "Animate a library sticker", OBJ, OBJ, 200),
    ("POST", "/api/packs/{id}/stickers/{sid}/move", "Library", "Move one sticker into another pack: {to}", OBJ, OBJ, 200),
    ("POST", "/api/stickers/move", "Library", "Bulk move into one pack, all or nothing: {to, items: [{pack_id, id}]} -> {moved, skipped, to}", OBJ, OBJ, 200),
    ("POST", "/api/packs/{id}/stickers/{sid}/delete", "Library", "Remove a sticker", None, OBJ, 200),
    ("POST", "/api/stickers/delete", "Library", "Bulk delete: [{pack_id, id}]", OBJ, OBJ, 200),
    ("POST", "/api/cutout", "Library", "A photo (raw body) becomes a cut-out PNG; X-Cutout header describes the method", None, None, 200),
    ("POST", "/api/packs/{id}/telegram", "Telegram", "Create the pack on Telegram, or add what is new. Body {name?, mode?}: mode once (default: the same content is never sent twice, the earlier export is returned with already=true and Telegram is not called), replace (send on purpose) or new_set (a second numbered set); every send is recorded", OBJ, OBJ, 200),
    ("GET", "/api/packs/{id}/telegram", "Telegram", "Dry run: what would be created and every problem", None, OBJ, 200),
    ("GET", "/api/packs/{id}/export.zip", "Library", "Download the pack: every sticker file (.webm animated, .png / .webp static, the engine's file names) and a manifest.json (application/zip)", None, None, 200),
    ("GET", "/api/packs/{id}/telegram.zip", "Telegram", "No-credentials fallback: the files for @stickers (application/zip)", None, None, 200),
    ("GET", "/api/telegram", "Telegram", "Connected or not and which bot (never the token)", None, OBJ, 200),
    ("POST", "/api/telegram/config", "Telegram", "Save the bot token and user id", obj({"token": STR, "user_id": STR}), OBJ, 200),
    ("POST", "/api/telegram/disconnect", "Telegram", "Forget the token", None, OBJ, 200),
    # --- projects (video / GIF)
    ("GET", "/api/projects", "Projects", "Video / GIF projects", None, OBJ, 200),
    ("POST", "/api/projects", "Projects", "Import a video or GIF (raw body, ?name=)", None, OBJ, 200),
    ("GET", "/api/projects/{id}", "Projects", "One project", None, OBJ, 200),
    ("POST", "/api/projects/{id}", "Projects", "Update a project (autosave)", OBJ, OBJ, 200),
    ("POST", "/api/projects/{id}/delete", "Projects", "Delete a project", None, OBJ, 200),
    ("POST", "/api/projects/{id}/render", "Projects", "Render a project to WebM / WebP / GIF", OBJ, None, 200),
    ("POST", "/api/projects/from_sticker", "Projects", "Open an animated sticker as a project", obj({"pack_id": STR, "sticker_id": STR}, ["pack_id", "sticker_id"]), OBJ, 200),
    # --- watch folders, search, health
    ("GET", "/api/watch", "Inputs", "The watch folders side by side, plus the trash", None, OBJ, 200),
    ("POST", "/api/watch/remove", "Inputs", "Move a folder pair to the trash", OBJ, OBJ, 200),
    ("POST", "/api/watch/restore", "Inputs", "Restore a folder pair under its own names", OBJ, OBJ, 200),
    ("POST", "/api/watch/purge", "Inputs", "Delete a trashed pair for good", OBJ, OBJ, 200),
    ("GET", "/api/watch/thumb/{name}", "Inputs", "A cached thumbnail of a sheet folder (image/jpeg)", None, None, 200),
    ("GET", "/api/search", "Search", "Search stickers (Postgres when up, else files); ?q=", None, obj({"results": arr(OBJ), "via": STR}), 200),
    ("GET", "/api/health", "System", "Every dependency reports itself; nothing raises", None, ref("Health"), 200),
    ("GET", "/api/health/models", "System", "Language, vision and tracing status", None, OBJ, 200),
    ("GET", "/api/health/storage", "System", "The out/ folder: free space, generations, who holds the writer lock", None, OBJ, 200),
    ("GET", "/api/openapi.json", "System", "This document", None, OBJ, 200),
]


def _params(path: str) -> list:
    import re
    return [{"name": n, "in": "path", "required": True, "schema": STR} for n in re.findall(r"\{(\w+)\}", path)]


def build(server_url: str = "http://127.0.0.1:8770") -> dict:
    paths: dict = {}
    for method, path, tag, summary, req, resp, status in ROUTES:
        op: dict = {"tags": [tag], "summary": summary, "operationId": method.lower() + "_" + path.strip("/").replace("/", "_").replace("{", "").replace("}", "").replace(".", "_").replace("-", "_"),
                    "responses": {str(status): {"description": "ok"}, "400": ERR, "401": ERR, "403": ERR, "404": ERR, "409": ERR, "429": ERR, "500": ERR}}
        if resp is not None:
            ctype = "text/event-stream" if path.endswith("/events") else "application/json"
            op["responses"][str(status)]["content"] = {ctype: {"schema": resp}}
        if req is not None:
            op["requestBody"] = {"required": True, "content": {"application/json": {"schema": req}}}
        params = _params(path)
        if method == "GET" and path in ("/api/generations", "/api/jobs", "/api/chat/sessions"):
            params += [{"name": "limit", "in": "query", "required": False, "schema": INT, "description": "1-500: page the list; the answer then adds total, limit, offset"},
                       {"name": "offset", "in": "query", "required": False, "schema": INT, "description": "how many to skip (0 or more)"}]
        if method == "POST" and ("messages" in path or path in ("/api/generations", "/api/live/sheet", "/api/live/video")):
            params.append({"name": "Idempotency-Key", "in": "header", "required": False, "schema": STR,
                           "description": "the same key within 24 h returns the first answer and runs nothing again"})
        if path.endswith("/events"):
            params.append({"name": "Last-Event-ID", "in": "header", "required": False, "schema": STR})
        if params:
            op["parameters"] = params
        paths.setdefault(path, {})[method.lower()] = op
    return {"openapi": "3.1.0",
            "info": {"title": "Mirsal Builder API", "version": VERSION,
                     "description": "High-quality animated stickers: chats, generations, gates, live generation, library, Telegram. Everything is JSON addressable by id (G012, G012/S3, J004, S002). "
                                    "See docs/api.md for the safety rules (Host/Origin guard, accounts and Bearer tokens, per-minute limits (429 + Retry-After), idempotency keys, signed links). "
                                    "Every route is also served under /api/v1/...; every answer carries X-API-Version and X-Request-Id (send your own X-Request-Id to trace a call); "
                                    "list routes take ?limit=1-500&offset=N (opt-in) and then report {total, limit, offset}."},
            "servers": [{"url": server_url}],
            "components": {"schemas": SCHEMAS, "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}}},
            "security": [{}, {"bearerAuth": []}],
            "paths": paths}


# ---- TypeScript types from the component schemas (no npm: a small generator, so nothing is hand-copied) ----
def _ts(s: dict, indent: int = 0) -> str:
    if "$ref" in s:
        return s["$ref"].rsplit("/", 1)[1]
    if "anyOf" in s:
        return " | ".join(_ts(x, indent) for x in s["anyOf"])
    t = s.get("type")
    if "enum" in s:
        return " | ".join(f'"{v}"' for v in s["enum"])
    if t == "string":
        return "string"
    if t in ("integer", "number"):
        return "number"
    if t == "boolean":
        return "boolean"
    if t == "null":
        return "null"
    if t == "array":
        inner = _ts(s["items"], indent)
        return f"({inner})[]" if "|" in inner else f"{inner}[]"
    if t == "object":
        props = s.get("properties")
        if not props:
            return "Record<string, unknown>"
        req = set(s.get("required", []))
        pad = "  " * (indent + 1)
        lines = [f"{pad}{k}{'' if k in req else '?'}: {_ts(v, indent + 1)};" for k, v in props.items()]
        if s.get("additionalProperties") is True:
            lines.append(f"{pad}[key: string]: unknown;")
        return "{\n" + "\n".join(lines) + "\n" + "  " * indent + "}"
    return "unknown"


def typescript(spec: dict | None = None) -> str:
    spec = spec or build()
    out = ["// Generated by `python -m mirsal openapi --ts`: do not edit. Source: mirsal/mirsal/console/openapi.py", ""]
    for name, sch in spec["components"]["schemas"].items():
        out.append(f"export interface {name} {_ts(sch)}" if sch.get("type") == "object" and sch.get("properties") else f"export type {name} = {_ts(sch)};")
        out.append("")
    out.append("export const routes = " + _routes_literal(spec) + " as const;")
    return "\n".join(out) + "\n"


def _routes_literal(spec: dict) -> str:
    import json
    items = {f"{m.upper()} {p}": op["operationId"] for p, ops in spec["paths"].items() for m, op in ops.items()}
    return json.dumps(items, indent=2)
