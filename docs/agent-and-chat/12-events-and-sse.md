# Events and SSE

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

`pipeline.emit` writes `events.jsonl` (the record) and publishes the same event under the Phase 5 names: `generation_started, sheet_generated, sticker_processing,
sticker_ready / sticker_failed (one per sticker as it is cut, with `asset_url`), animation_started, animation_ready, video_sheet_ready, review_decided, pack_complete,
generation_failed`. `GET /api/generations/{id}/events` streams them (`text/event-stream`, replay from `Last-Event-ID` or `?after=`, a ping every few seconds, ends at a terminal
event or after 10 minutes). The generation continues when the browser goes away.

**The chat turn streams too.** `GET /api/chat/sessions/{id}/stream` (native FastAPI, `console/app.py`; models `ChatTurnEvent` / `ChatDoneEvent` in `console/app_models.py`) sends `event: turn` with the turn in progress (`{working, count, message}`: the last message with its growing step trace and cards) each time it changes, then `event: done`; a comment every 15 s, ends after 10 minutes. Access is the session route's own: the stream reads the session through the original handler with the caller's headers, so Host, sign-in, roles and ownership answer exactly the same. The page (`agent.js` `startStream`) listens while a turn works and reads the whole session once at `done`; polling stays as the fallback (no `EventSource`, a dropped stream) and for what keeps running after the turn (jobs, live cards).
