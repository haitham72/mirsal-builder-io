# Phase 5 — Frontend, HTTP API, and Production Hardening

**Prerequisite:** Phase 4 exit (4A–4C) is met.

**Goal:** the product. A premium sticker-creation tool with two interfaces over one engine.
- **Creator Mode** has explicit controls, for users who know what they want.
- **Conversational Mode** takes natural-language direction, for iterating.

Both operate on the same structured state from Phase 4. The UI renders state; it never decides models, prompts or validation.

> It must feel like creative software, not a chatbot. Stickers dominate the screen; text is secondary.

> **Delivery (Haitham, 2026-10-01): the shipped product is the API (5A) and an integration into the existing Mirsal app, not a new front end.** The screens in this repo (the desktop builder in `mirsal/mirsal/console/`, the parked React gateway, and 5B below) are a **sandbox / proposal**: they drive and demonstrate the API and are the reference client. So 5B is "reference client + contract tests", and the work that must be right is 5A: stable, versioned JSON contracts (OpenAPI), ids for everything (generation, sticker, pack, job, studio edit), idempotency, auth, and the same behaviour the sandbox shows. Every feature gets its engine function and JSON shape first; the screen follows.

There are three checkpoints: **5A** HTTP API + workers, **5B** frontend, **5C** production hardening + export.

---

## 5A — HTTP API + workers

FastAPI over Phase 4's `run_turn` and the store. The API process **never runs media or model code**.

**Jobs:**
- Migration `009_jobs.sql`: a `jobs` table holds id, kind, status, attempt, max_attempts, started_at, timeout, error, and a dead-letter state after max attempts.
- One or more `mirsal worker` processes poll it (`SELECT … FOR UPDATE SKIP LOCKED`).
- A crashed media job can't take down the API. After a server restart, running jobs resume or fail cleanly from their Postgres state.
- **Redis (from Phase 4) is not the queue.** Postgres `jobs` stays durable. SSE reads the Phase 4 Redis event streams, with stream entry IDs as event IDs, so `Last-Event-ID` replay is native.
- **Idempotency:** `SET mirsal:u:{user}:idem:{key} NX EX 86400` → generation id. A Postgres unique constraint on the idempotency key (per user once `010` lands) is the durable backstop.

**Endpoints:**

```
POST  /api/sessions                         GET /api/sessions/{id}
POST  /api/sessions/{id}/messages           {text, selected_sticker_ids[]} → {interaction_id, generation_id?, status:"QUEUED"} immediately
POST  /api/generations                      Creator Mode {prompt, settings, reference_image?}; header Idempotency-Key → same key returns the existing job
GET   /api/generations/{id}                 full snapshot (for reconnect / cold load)
GET   /api/generations/{id}/events          SSE; sequential event ids; replay from Last-Event-ID
POST  /api/generations/{id}/animate
POST  /api/stickers/{id}/regenerate         POST /api/stickers/{id}/feedback
POST  /api/photos                           multipart photo → cutout sticker (3C)
POST  /api/text-stickers                    {text | last_message} → top matching templates, filled (3D)
POST  /api/text-stickers/{generation_id}    re-render with new text/template (free, instant)
GET   /api/templates                        template library (tags, occasions, previews)
POST  /api/depth                            photo → depth + layers + focal anchor (3E)
GET   /api/packs                            GET/PATCH /api/packs/{id}   (rename, reorder, remove, replace, set cover)
GET   /api/packs/{id}/export                zip, validated against the Telegram profile
GET   /api/health  /api/health/models  /api/health/storage
```

**Events:**
- `generation_started, concepts_created, sheet_generating, sheet_generated, sheet_rejected, sticker_processing, sticker_judging, sticker_ready, sticker_rejected, sticker_failed, review_requested, review_decided, video_sheet_ready, animation_started, animation_ready, animation_failed, pack_complete, generation_failed`.
- The review events carry the golden-path gate (`plan | still | video_sheet | anim | pack`, `Phase_01/README.md` 1F). The UI shows Approve / Reject at every open gate. `POST /api/generations/{id}/review {gate, decision, sticker_id?, note?}` resumes the Phase 4 `interrupt()`. Its rules are Phase 1's: Python blocks are final, and the gate order is enforced.
- Payload: `{event, generation_id, sticker_id, asset_id, index, asset_url}`.
- Generation continues if the browser disconnects.

**Reference image upload (Creator Mode):**
- Validate by **content** (not the declared MIME), extension, size and dimensions, and store the file as a `SOURCE` asset.
- `ImageGenerator.generate(reference=...)` (from Phase 2) receives the upload for image-to-image. The Phase 4 slots carry identity traits, and the judge scores `identity_match`.

**Packs vs generations:** a generation is a creative event, and a pack is a user-curated collection.
- Migration `008_packs.sql`: `packs` (id, session_id, name, cover_sticker_id, created_at) and `pack_stickers` (pack_id, sticker_id, position, active, created_at).
- Each generation auto-creates a pack.
- Reorder, remove and replace change `pack_stickers` only. They never delete assets or touch generation history.
- A pack is complete when every requested sticker is terminal and ≥1 is approved. Zero approved after the maximum attempts means `GENERATION_FAILED`, with a useful reason.

**Seed from Phase 1:** the Lifecycle Console's API is the starting point, not a throwaway. Mapping: `GET /api/generations` -> same; `GET /api/generations/{id}` -> same (snapshot = `result.json` + events); `POST /api/generations {prompt}` -> same, plus `Idempotency-Key`; `POST .../more` -> a `parent_id` generation via the messages endpoint; `POST .../animate {scope: pack|slice, index}` -> same body; `GET /out/<path>` -> `asset_url` served through the `AssetStore`. The single background thread + `409 busy` becomes the `jobs` table; polling becomes SSE.

**Types:** generate TypeScript types from the OpenAPI schema; nothing is hand-copied.

**5A exit:**
- [ ] The integration test sees S1's `sticker_ready` before S9 finishes.
- [ ] The same Idempotency-Key creates no duplicate generation.
- [ ] Killing a worker mid-job gives a retry, or dead-letter after the max.
- [ ] Disconnect → reconnect with Last-Event-ID replays missed events.
- [ ] Health endpoints report each dependency.

---

## 5B — Frontend (Vite + React + TypeScript)

**Brought forward (2026-10-01):** the stack, the app shell and the Inbox / Generate / gates / video-sheet / history screens are built in Phase 1 Part G (`mirsal/web/`). 5B **extends** that app: Conversational mode, sessions, SSE in place of polling, the remaining Part D/E ports if any are left on `/legacy`, and mobile. It does not start a second frontend.

**Layout:**
- A generation workspace where the stickers dominate, on a checkerboard so transparency is visible.
- Tiles fill in progressively, each with its status: generating / processing / judging / ✓ / rejected / failed.

**Start from the Phase 1 desktop builder (Parts D and E), do not redesign.** Part E adds the Video / GIF Prepare screen (`prepare.js`) and `video_project.py`; its mobile form is MOBILE_08 of `ref/mirsal_sticker_builder_architecture.md` section 21: preview and timeline stay pinned, the control area scrolls beneath, progressive disclosure per section 21.13. `mirsal/console/` already has the desktop shell from `ref/Mirsal-Builder.jpg` (rail, Library, Create, Editor with layers/inspector/undo, Pack manager, Save/Export) with a `compose()` render, a `library.py` API and `.wastickers` export (README, "Desktop Sticker Builder"). 5B ports those screens to React/TypeScript component-for-component: `StickerProject`/`StickerLayer` types from the spec (`ref/mirsal_sticker_builder_architecture_design.md`, section 4), the same `data-act` actions become store actions, the same endpoints become 5A routes (`/api/packs`, `/api/cutout`, ...). The editor's pixel logic (outline, erase/restore, snapshots) is the reference behaviour to keep. Expandable to **mobile** here (5C or a 5B sub-step): the spec's MOBILE_01-07 screens sit on the same project model; the desktop-only pieces are the three-panel editor layout and drag-reorder.

**Review surface (port from the Phase 1 Lifecycle Console; these were proven with Haitham):**
- the 7-stage stepper with per-stage timing and detail;
- raw sheet with the 3x3 overlay, keyed sheet, and per-slice **raw crop with bounding box next to the 512 slice**;
- the background toggle (checker / light / dark / wallpaper), because a white outline vanishes on light and pops on dark;
- per-check chips (`no_spill`, `inside_cell`, ...), metrics, and `Video -> this slice` / `Video -> full pack`.
Ship it as a `LifecycleInspector` panel (debug + real progress UI), not something rewritten from scratch.

**One-click photo -> sticker** (5A `POST /api/photos` + 5B button) is the Phase 3C matting keyer behind an upload box: rembg-class model on the server, the user sees the same Lifecycle stepper, the same slice modal and the same validators. No green screen is ever required from the user.

**Slice modal:** port the console's carousel (arrows, keyboard, thumbnail strip, raw-vs-sticker-vs-video panes, checks, keying recovery log) as the sticker detail view.

**Creator Mode:**
- Prompt, reference upload, style, and an animation toggle.
- **Advanced:** duration (≤3 s), FPS (≤30), chroma (auto/green/blue), subject scale, style strength, reference strength.
- A single **Generate** button. The user should know exactly what will happen.

**Conversational Mode:**
- A chat panel beside the grid, with compact settings chips (`9 stickers · 3 s · 30 FPS · Glossy`) and a settings drawer. Changing a setting in the UI updates `session.settings`, and the conversation sees it.
- **Tap to select stickers.** The selection is sent as `selected_sticker_ids`, and "make these happier" uses it.
- **Priority:** explicit selection > explicit reference in the text > current focus > inference.
- Opening a sticker sets the focus, so "make it happier" targets it.

**Search (the Phase 3 pool, Redis-cached):** a search box in the sticker panel ("falcon dancing") shows pool hits instantly. Gap tiles are labelled "Generate N more · ~$X" and never spend without that tap.

**Photo cutout (3C):** camera/upload → tap the subject → outline (None / White / Color / Die-cut) → send or export.

**Text stickers (3D):** when the last message is ≤ `N` words, the sticker panel shows a "your message as a sticker" row: that text already filled into the best-matching flashing templates, like WhatsApp's version with a real library. Tap to send, or edit the text and re-render instantly. There is a template browser by occasion and mood, and templates with a subject slot can take a 3C cutout.

**Parallax photos (3E):** the 3E viewer becomes a component. Images shown in the app (and chat previews) tilt in 3D with the phone, with a tap-to-allow for iOS motion permission, a static fallback, and a toggle. HTTPS in production already satisfies iOS's motion rule.

**Pack library:** one horizontal row per pack, showing cover, name, sticker count and date. A topic view groups the pool by normalized topic (one row per topic, with up to 5 previews), as in the old build's PackBrowser.

**Pack detail:**
- The grid, with actions: regenerate, delete, replace, animate, reorder (drag), rename, set cover.
- A rejected tile shows **Regenerate**, with a simple user-facing reason. The internal reason is shown to admins only.

**Sticker detail:**
- Image, animation, concept, generation, and a history tree (original → regenerated → adapted).
- Image and animation are separate assets; "make number 2 bounce instead" re-animates S2 only.

**Errors:**
- The user never sees internals ("VLLM node failed"). They see "Some stickers couldn't be made. Your other stickers are ready."
- Retry, regenerate and continue are offered where they apply.

**Debug page** (admin only) shows:
- request, intent, resolved references, transformation and slots, prompts;
- master sheet, validator report, judge output;
- animation validation and lineage.

**Rule:** no dead controls. Every visible control is wired end-to-end.

**Design:** load the `frontend-design` skill before building. The feel is a premium creative tool, not a template dashboard and not a chat app.

**5B exit:**
- [ ] Creator and Conversational modes produce the same generation for the same structured request.
- [ ] Select S2 + S7 → "make these more energetic" → G(n+1) regenerates only S2 and S7.
- [ ] Reorder, remove and set cover don't alter generation rows.
- [ ] Refreshing mid-generation restores the exact state.
- [ ] Haitham completes the full Definition of Done flow below in the browser.

---

## 5C — Production hardening + export

**Restricted network:** the frontend build must work offline: commit `package-lock.json`, vendor the npm cache (`npm ci --offline`), and no runtime CDN or web-font fetches (the Phase 1 console already sets that rule).

**Security:**
- Every request is authenticated.
- Migration `010_users.sql`: a `users` table, plus `user_id NOT NULL` on `sessions`, `generations` and `packs`. Existing rows are backfilled to one local user. Stickers and assets inherit ownership through their generation.
- Sessions, generations, stickers and assets are authorized against `user_id`, so user A can never reach user B's asset. Redis keys switch from `u:local` to the real `user_id`, so no cache hit crosses users.
- **Pool scope:** search returns `shared = true` stickers plus the viewer's own. A sticker from an uploaded reference image is `shared = false` and never visible to anyone else.
- Assets are served through short-lived **signed URLs**, never a raw static folder or storage credentials.
- The frontend never supplies filesystem paths.
- Source uploads may be private, so access control applies to every object.

**Observability:**
- Structured JSON logs carry `request_id, session_id, interaction_id, generation_id`. Log IDs, keys, hashes and metadata, **never image bytes**.
- **Timing metrics:** LLM, image, processing, VLM, animation and storage latency; total time; **time to first sticker**.
- **Quality metrics:** sheet and sticker approval rates, Python vs VLM rejection rates, average retries, animation failure rate, resolver accuracy, user regeneration rate, and positive/negative feedback rates.
- Don't optimize approval rate alone. A system that accepts everything can still be boring, so track regeneration frequency and explicit feedback.

**Recovery & hygiene:**
- Per-job temp directories are auto-cleaned.
- Master sheets are kept for debugging and reproducibility.
- There are separate retention policies for source uploads, generated assets, temp files, master sheets and animations.
- An asset is never marked READY until persistence is confirmed.

**Telegram export:**
- **Per-sticker file:** the zip bundle uses the WEBM if the animation is READY, otherwise the PNG/WEBP.
- **The Telegram profile is validated:**
  - static: PNG/WEBP, one side 512 px, transparent, ≤512 KB;
  - video: WEBM VP9 + alpha, one side 512 px, ≤30 FPS, ≤3 s, ≤256 KB, no audio, **seamless loop** (`loop_seam` under the maximum);
  - tags: 1–20 emoji per sticker with the most fitting first, and 0–20 **English + Arabic keywords** (≤64 characters total).
- **Pack thumbnail:** 100×100, either static PNG/WEBP ≤128 KB or WEBM ≤32 KB, rendered from the cover sticker.
- **Pack metadata:** title ≤64 characters; set short name ends in `_by_<botname>` (letters, digits, underscores); max **120 stickers** per pack; order is controllable. Lint for trademarks: no Genmoji, Apple, Pixar or Disney in the title or keywords.
- **Optional Bot API push** when a bot token is configured:
  - `uploadStickerFile` → `createNewStickerSet` returns a `t.me/addstickers/…` link;
  - **"generate more" adds to the same set** (`addStickerToSet`) instead of creating a new one, until the 120 cap;
  - `setStickerPositionInSet` controls order and `setStickerSetThumbnail` sets the icon;
  - rate limits are handled with 429 `retry_after` back-off.

  Telegram accepting the set is the only true compatibility test.
- **Out of scope:** Telegram custom emoji (100×100). This product makes high-quality animated stickers, not emoji.

**Regression suite** (runs on every pipeline, model, prompt or template change):
- **Visual dataset:** people, animals, objects, food, Arabic text/context, green subjects, complex silhouettes.
- **Chroma dataset:** watermelon, green shirt, green animal, green object, blue object, mixed colours.
- **Transformation dataset:** dog as banana, cat as strawberry, car as teddy bear, camel as cupcake.
- **Conversation dataset:** "make it like #3", "make second happier", "I hate 4", "keep 2 and 7", "use the first cherry", "go back to the banana generation".

**5C exit:**
- [ ] The auth/authorization tests pass, including cross-user denial.
- [ ] Signed URLs expire.
- [ ] Metrics are visible for 20 real runs.
- [ ] The regression suite runs in one command, and its results are stored.
- [ ] An exported pack validates. (With a bot token: it installs and plays in Telegram.)

---

## Definition of Done (the whole system)

**A user can:**
- create a pack and upload a reference image;
- get partial results live and animate them;
- browse history and reference old generations and specific stickers;
- give mixed feedback, regenerate single stickers, and adapt one sticker's style or pose into another;
- change settings conversationally;
- curate and export packs.

**The transformation rules hold:**
- "Make my dog as banana stickers" yields the persistent roles dancing / shocked / squashed banana, dog-banana, and action + dog-banana, plus creative extras.
- "Make number 5 like number 4" resolves exact IDs.
- "dog as banana" ≠ "dog with banana".
- "no dancing" overrides the template.

**The system rules hold:**
- After a restart, every generation is still addressable.
- "Make it like G47/S4" fetches the real asset.
- No model receives the entire history by default.
- Every generation can answer where it came from, what it referenced, which sticker was used, and what changed.

**Naming holds:** every stored and exported file is `<media>-<NNN>-<task_slug>-<key>.<ext>` with a unique, filesystem-safe stem (Windows-safe).

**Assets meet the specs:**
- Every final PNG: 512×512, valid alpha, correct scale, no chroma, no boundary contamination.
- Every animation: correct duration and FPS, valid encoding and frames, safe boundaries, consistent identity.
- The first sticker appears before all nine finish.
- One bad sticker never destroys eight good ones.
- No history is overwritten.

**The system contract.** At any point the system can answer:
- who requested this, in which session and generation, and for which sticker;
- what the original request was;
- the assigned concept, the active template, and the prompt;
- which model, which references, and what Python validated;
- what the judge said, what the user liked and rejected;
- the parent generation, the assets, and what can be regenerated independently.

If it can't, it isn't done.
