# Events (SSE)

<sub>Part of [api.md](../api.md).</sub>

`GET /api/ai` (the active AI backend, the person's choice and what is available) · `POST /api/ai/backend {backend?: auto | local | cloud, model?: <id>}` (owner only; `model` is a qualified id listed by `GET /api/llm/models`; bare ids retain the legacy local contract, except Luna, which routes to official OpenAI. Unknown or unavailable ids return `400 {error, models: [...]}` and nothing is saved. An empty model clears saved local/cloud picks. Backend, local `model` and `cloud_model` are kept in `out/ai_backend.json`; a call with neither field is a 400; the answer is `GET /api/ai`'s) · `GET /api/generations/{id}/events` (`Last-Event-ID` or `?after=` to replay): `text/event-stream`, one frame per event, `id:` is the stream id.
Names: `generation_started, sheet_generated, sticker_processing, sticker_ready, sticker_failed, animation_started, animation_ready, video_sheet_ready, review_decided,
pack_complete, generation_failed`. Payload: `{event, generation_id, stage, status, ts, ms, actor?, decision?, gate?, index?, sticker_id?, asset_url?, trace_run_id?}`.
