# Backlog: what is still open to build, by area

**This is a tracker, not a log** (`CLAUDE.md` rule 7, together with [`waiting-for-haitham.md`](waiting-for-haitham.md)). An entry is deleted the moment it is built and recorded as architecture in the doc of its area; history lives in git. Everything built is in the other files of `docs/`; what needs a person is in `waiting-for-haitham.md` (referred to below as **W#**, the item number). Build only what you are asked (rule 2).

Status words: **open** (can be built now) · **needs Haitham** (a verdict first, W#) · **needs a paid test** (money first, W#) · **parked** (paused on purpose, do not touch).

## Visual design (`docs/design.md`)

- Real tile art for the twelve style presets: the swatches are abstract placeholders; drop `<id>.png` into `console/assets/styles/`. **needs Haitham** (the art).
- Inline `style="font-size:..."` in the scripts is still off the type scale. **open**.
- Haitham's eyes on every screen. **needs Haitham** (W1).

## Particles and the welcome modal (`docs/effects.md` section 8, `docs/particles_plan.md`, `docs/onboarding.md`)

- A real paid run of the AI-drawn particle sheet from the screen, to see how a real Nano Banana particle sheet cuts (the price and the job path are tested on the fake CLI). **needs a paid test** (W2).
- Telegram delivery of a burst (phase 5). **needs Haitham** (W24, W25, W26).
- Burst creation, many packs from one liked sheet (P14; `docs/burst_plan.md`). **needs Haitham** (W27).
- The legacy per-sticker burst badge (`ptBadge`). **needs Haitham** (W28).
- Particle sets are not part of the trash purge yet (a deleted set waits in `out/trash/particles/`). **open**.
- `DEFAULT_SPRITE_PX` 100 vs 200. **needs Haitham** (W21).
- A preview of the would-be sticker in the video-sheet override dialog (the G3 override itself is built). **open**.
- Older batches with no keyed/raw sheet on disk are not rebuilt when a slice of an animation edit merges back into the sheet (`rebuild_sheet` returns null; nothing breaks). **open, low**.
- Rule for all of it: effect checks are warnings with "use it anyway"; only Telegram's own limits may block.

## Chat and the agent (`docs/agent-and-chat.md`)

Still open from the chat audit of 2026-10-02 and the browser look of 2026-10-03, in order of harm:

1. **Short-message resolution.** "more like this" with a click redoes the clicked sticker; Arabic / Arabizi edit commands become new plans; "the first two" / "the rest" / "them all" resolve to one sticker; "make 5 same as 2" also redoes 2; "redo 3 of the previous batch" edits the current batch; a model-picked sticker is not confirmed; "I loved the last batch" records feedback on the last sticker. **open** (Arabic: also W32).
2. **Context is lost every turn.** `classify` gets only booleans; no past message, plan card or parent prompt reaches the model (every brain call is one system + user pair; `SessionStore.context()` has no caller); the summary is trimmed from the END so the newest subjects / Focus drop first; a fresh paid batch leaves `focus.stickers` empty (`graph.py`), so "it / make number 3 happier" can target the OLD batch; the latest pass can be a job with no generation ("animate" says nothing to animate; a FAILED job stays in the summary); subject keys come from the deterministic expander ("falcon" / "falcon stickers" / "a falcon dancing" are three subjects, Arabic collapses to one subject "sticker"); "another" appends the old "Avoid..." text each time (the REQUEST fence cuts at 600 chars, so new preferences are cut first) and the built-in planner pastes that chat wording and the word "sticker" into the Subject line; feedback is consumed while planning and leaks across subjects; "I like 2 and hate 3" records 3 as liked. **open**.
3. **State and storage.** There is no LangGraph checkpointer or thread id: `out/sessions/S###.json` is the only memory (the Redis `session:S###` copy and most of the Postgres mirror are never read). The settings route (`server.py`) takes no session lock, so a toggle made mid-turn is overwritten by the turn's next save (ask-before-spending turned ON mid-turn reverts to OFF and creates without asking). The session lock (5 min, `cache.py`) outlives a dead server with real Redis, so the chat stays "Thinking" and new messages get 409 for up to 5 minutes, and a turn longer than 5 min loses a user message. Delete during a running turn resurrects the chat; `create` reuses `max(id)+1` after deleting the newest chat, which drops the new chat's rows in Postgres (`ON CONFLICT DO NOTHING`); `n_confirm` clears `pending` before `tools.create`; the generation card is attached only at the final save, so "nothing was spent" can be false after a restart; a typed message is cleared before the send and lost when it is refused (409 / network); a card for a removed batch makes the page poll forever; every poll downloads the whole session (~600 KB at the caps) and builds a new Agent; one `save_session` is ~900 Postgres statements at the caps, run on every trace step. **open**.
4. **Smaller.** "continue with a dragon pack instead" at a creator gate approves the pack; the model's intent is trusted unchecked; a down model can cost up to 45 s per call; `ai: True` is hardcoded in another / edit / retry; the edit trace and stored pass show the stub, not the prompt sent. **open**.
5. **Gaps from the browser look**: an empty "New chat" created by clicking a setting with no chat open (W22); a chat edit of an animated sticker opens Prepare; "undo" has no "redo"; a bare "the last one" / "wear a hat" with no person and no focus still plans a new batch (W23). **needs Haitham**.

Other open items:

- A liked-subject signal for the taste memory. **open**.
- The model pick is process-wide, not per chat (`POST /api/ai/backend`). **needs Haitham** (W37).
- Transformation templates: Arabic / Arabizi detection, more lexicons beside `banana.py` (pizza, avocado, ...), and your examples in `docs/inputs/resolver_utterances.md` to check the detector against. **needs Haitham** (W15, W32).
- Annotation: copy the AI caption (`sticker.caption`, `vision/transcribe.py`) into `stickers.annotation` and the pool's `search_text` (so "the one waving a flag" finds it), and `build_context(HIGH)` with the real images. **open**.
- Multi-reference: "make 5 like 2" sends sticker 2 as a reference; the other roles (pose, expression, ...) are recorded (`generation_references`) but not yet worded into prompts. **open**.
- The 40-utterance resolver eval (>= 95% exact ids). **needs Haitham** (W15).
- Selective regeneration as ONE sheet: several edited stickers are one 1x1 generation each (at most 4, and the reply says so); "keep 1-4 and redo 5-9 as one 2x2 / 3x3" (one paid sheet instead of N) and the `inherited_from` carry-over rows are not built. **open**.
- The chat polls; streaming the agent's steps over SSE is not built. There is no terminal `mirsal chat`. The reducer's model summary has only run against fakes. **open, low**.
- A real chat -> Create run and a creator run against the real Higgsfield and a real bot. **needs a paid test** (W6).

## Engine and Studio (`docs/engine-and-studio.md`)

- The Studio's JavaScript has node tests on the pure builders (`tests/js`) but no browser smoke test: add one for issue colours, Include anyway, the history folds, the AI captions panel and the bulk move (checked by hand in Chromium on a scratch copy of `out/`; `tests/test_js.py` only guards the shared `ACT` names, that every button has a handler and the shell rules). **open**.
- A second request while the *pipeline* is busy gets 409 (the provider jobs have their own durable queue). `result.json` is read-modify-write under one in-process lock plus the cross-process writer lock: two request threads can still interleave inside one server (two processes are kept out by the writer lock; every file write is atomic: `tests/test_multiprocess.py`). **open, low**.
- Add a focused-tier profile for the trash purge / storage area (`docs/testing.md`: the existing profiles do not cover it). **open**.

## Live generation (`docs/generation.md`, `docs/higgsfield.md`, `docs/operator.md`)

- S4 re-run with Kling `pro` and the default gap decision (`slot_fill`); S7 decisions (one 3x3 sheet vs single stickers; the engine's outline vs a model-drawn one). **needs a paid test** (W7).
- The vision judge's recovery is a recommendation (`vision/recovery.py`); nothing executes it. Executing means paid regenerations, so it needs a confirmation flow. **needs Haitham**.
- Original planner leftovers, ask before building: UAE content rules as a lint (no flags / emblems / text, no real people or rulers, the falcon is always a young brown saker falcon chick, Emirati dress, Commemoration Day solemn), English + Arabic Telegram search keywords per cell (0-20, 64 characters, English first), 4x4 and 16:9 sheets (`split_grid` handles 2x2 and 3x3), no trademarks in pack titles and tags, whether the animation sheet should default to 2x2 (2.25x the pixels per sticker). **needs Haitham**.
- The built-in prompt planner drops everything after `for / in / at / during / with / on` into the file name only (`prompter.SPLIT`: "spiderman in dubai" sends `Subject: spiderman`); the Generate prompt step makes it visible, a context-as-setting-line fix is open. **open**.
- The Generate prompt step: Enter, the non-live button, the cost of an OpenAI call made by the enhancer. **needs Haitham** (W16, W18, W19).
- The Higgsfield `wait` and the plan expander have timeouts (300 s create, `timeout_s + 60` wait, 60 s per model call); a *hung chat* was never reproduced, only a turn orphaned by a server restart (fixed). If "thinking" sticks again with a live server, capture the session's last step label: `out/sessions/S###.json` `messages[-1].steps`. **watch**.
- The daily credit cap must never block the owner (`fulfil()` takes no user). **needs Haitham** (W36).
- Stalled-job recovery has not run against the real Higgsfield (J022-J025). **needs a paid test** (W5).
- Per-chat paid parallelism and `MIRSAL_JOB_MODE=queue` have only run on the fake CLI. **needs a paid test** (W10).

## Store and search (`docs/store-and-search.md`)

- 3B: the eval set and precision@5 >= 0.8; an Arabic / Arabizi query parser (a small model; deterministic patterns today); a search-result cache keyed by a `pool_version` counter (embeddings and plans are cached, hits are not); the gap flow shows no price. **needs Haitham** (W12).
- 3C: an `edge_quality` check (a soft alpha gradient, not a binary edge), `--subject N`, a stronger matte (BiRefNet, MIT) and SAM 2 click-to-refine, HEIC input (`pillow-heif`), `SOURCE_PHOTO` asset rows, optional paid AI motion (price first), a composites test (IoU >= 0.92). **needs Haitham** (W14).
- **3D text template stickers (not started).** A library of flashing template stickers with a text slot, CapCut-style: `mirsal/templates/<id>/template.json` (`id, version, tags {en[], ar[]}, occasion, mood, frames[1-4] {art | null, duration_ms, text_style}, slot {x,y,w,h,rotation,align,max_chars,font_id}`, optional `subject_slot` for a photo cutout), 30+ procedural starters (greetings, reactions, love, birthday, UAE occasions), text rendered by code (Cairo, OFL, covers Latin and Arabic; Pillow with raqm, fallback `arabic-reshaper` + `python-bidi`; never split a word), encoded as WEBM VP9 alpha and animated WebP (not GIF: 1-bit alpha), matched to the last chat message when it is <= 4 words / 24 characters (exact occasion tag, then the embedding, then generic), editing re-renders in under a second as a child generation. Tests: every template passes `template check`, Arabic joins, Telegram validators, "happy eid" ranks Eid templates first. **needs Haitham** (W39).
- **3E 3D parallax photos (not started).** A photo gets depth and tilts with the phone: embedded Portrait-HEIC depth first, else Depth Anything V2 **Small** (Apache-2.0; the larger ones are non-commercial) through onnxruntime, edge-aware guided filter, focal plane at the subject's median depth (the cutout), a self-contained WebGL viewer (`parallax.html`, gyroscope with the iOS permission tap, mouse fallback, reduced motion = static), optional `--layers 2|3` with inpainting, optional `--bake` loop video. On-device only; private assets. **needs Haitham** (W39).
- Library packs still live in `out/library/library.json` (the old plan moved them to `packs` / `pack_stickers`; wait for the app's pack curation). `reviews.trace_run_id` exists and nothing writes it. Per-video task rows. An S3-compatible store behind `AssetStore`. **open, low**.
- **Frozen constraints.** `python -m mirsal db check` reports a CHECK constraint, default or index that differs from what the files declare (a constraint created inside `IF NOT EXISTS` is frozen at its first version), but nothing upgrades one automatically: when it reports a drift, write the next numbered migration (`ALTER ... DROP CONSTRAINT / ADD CONSTRAINT`). A dimension change in `005_vectors.sql` clears stored vectors by necessity; `db migrate` says how many and that `pool reindex` refills them. **standing procedure**.
- The trash purge's SQL (`store/purge_rows.py`) has only run against a recording fake connection, never a real Postgres. **needs a run** (W4).
- Embeddings stay local and hardcoded (`services/embed.py` `EMBED_MODEL`, decided): no hosted embeddings, no swap of the embedding model (it would change the vector dimension and invalidate every stored vector in `005_vectors.sql`).

## API and production (`docs/api.md`)

- Accounts are built (owner / member) and are enough for now: one local user, no OAuth, no sign-in screen. Held for later, not to be started: packs and the library per user, reference images, the Redis cache keys (`u:local`), a browser login, moving accounts out of `out/users.json`. **parked**.
- Per-job temp directories and retention policies; the Studio has no queue panel for DEAD rows yet (`mirsal queue status` shows them). **open**.
- **Contract polish:** a role-dependent shape for `GET /api/generations` (an owner also gets `health`, `paths`, `stale`); `GET /api/live/cost` answers `200 {"credits": null, "error"}` when a price is unknown (by design for the page, not a status code); camelCase leaks in a snake_case API (`updatedAt` in `media/video_project.py`, `packId` in `console/server.py`: the Studio reads them); the Host check needs the port in the header; no `Deprecation` policy yet; pagination is opt-in on three lists only (`/api/library`, `/api/tasks`, `/api/usage`, `/api/watch` still return everything); `415` for a wrong `Content-Type` is not built (W35). **open**.
- The regression suites (visual, chroma, transformation, conversation datasets) in one command. The metrics (`flow/metrics.py`) count what happened; what they mean for taste waits for the judge's calibration (W11). **open**.
- The React frontend `mirsal/web/`: extend or delete (W33); the editor's mobile screens. **needs Haitham**.
- The retired History screen (`console/history.js`, `#/history`). **needs Haitham** (W34).
- Content safety, OpenAI calls without a plan card, `out/` in git, a backup command. **needs Haitham** (W18, W29, W30, W31).
- The FastAPI + pydantic migration: **parked**, spec in [`fastapi_plan.md`](fastapi_plan.md), un-pausing is W38.
- Rate limiting and OAuth: **parked** (Haitham, 2026-10-02). The engine's per-minute 429 (`console/server.py` `_wait`, 65/min keyed on user id + kind, `Retry-After`) stays as it is.

## Deployment (branch `deployment`): parked

Paused by Haitham on 2026-10-02: nothing here is worked on, extended, turned on or deleted until he asks. The reasoning, phases, runbook and open questions are in [`deployment_plan.md`](deployment_plan.md); the prepared files are `deploy/` (map: `deploy/README.md`); the questions are W40-W48. Branches (2026-10-03): `deployment` holds the build and `better_ui/ux` branches from it; `merge/generate-advanced` is retired. Of the prepared slice, only **Telegram never-twice** (`services/telegram.py` `fingerprint()`, `send(mode="once" | "replace" | "new_set")`, `tests/test_telegram.py::NeverTwice`) and the **library fingerprint** are app work worth keeping; the gateway, SQL, Docker and Render files stay untouched. `deploy/gateway/ratelimit.py` stays inert.
