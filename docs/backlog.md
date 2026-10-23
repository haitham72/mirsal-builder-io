# Backlog: what is still open to build, by area

**Last synchronized: 2026-10-23 · implementation baseline `27009185` on `main`.** Pricing implementation and branch consolidation are complete. The highest-priority delivery gaps are the receiving CMS's JSON handling, super-like representation, stored-price verification, zero-count success validation and cooldown recovery.

**This is a tracker, not a log** (`CLAUDE.md` rule 7). An entry is deleted the moment it is built and recorded as architecture in the doc of its area; history lives in git. Implemented behavior lives in the owning area doc; what needs a person is in [Owner decisions](#owner-decisions) below (referenced as **W#**). Build only what you are asked (rule 2).

Status words: **open** (can be built now) · **needs Haitham** (a verdict first, W#) · **needs a paid test** (money first, W#) · **parked** (paused on purpose, do not touch).

## API delivery (`docs/api-integration.md`)

- Verify the live receiving CMS stores the intended name/price, and confirm its currency, monetary range/precision and omitted/free behavior. Pack persistence, UI controls, both API servers/aliases, queued snapshots, chat export and multipart `Price` are implemented and locally verified ([pricing evidence](../DELIVERY_CHECKLIST.md#pricing-verification-2026-10-23)); only receiving-system confirmation remains. **open**.
- Connect reaction JSON exports to the final API: the app's pack exporter currently refuses JSON (409), while direct CMS simulator/Lottie/super-like requests report success with zero inserts, even with paired thumbnails. Reconcile the supplied required `ContentType` with the app's current omission (accepted for the animated smoke), and resolve the receiving JSON contract before claiming delivery. **open**.
- Define the final API/client representation of super-like reactions: `ContentType: super_like` is rejected; allowed values are `emoji` and `emoji_reaction`. Sending the saved super-like JSON under `emoji_reaction` also reported zero inserts. **open**.
- Validate delivered asset counts in export outcomes; a 2xx/`Success: true` response with zero inserted/updated assets must not become a false success message. **open**.
- Handle collection upload cooldowns using the CMS's `retryAfterSeconds` response (429); the current export worker marks the request failed. [Smoke results](../DELIVERY_CHECKLIST.md#smoke-test-results-2026-10-23). **open**.

## Visual design (`docs/design.md`)

- Remaining app-audit scope: UX-07 unbuilt; UX-10 built, verdict open; AR-02/03/04, DOC-01, QA-01 verdicts open (full audit in git history). Implemented phone editing/Save, keyboard controls/labels, frame focus and ownership fixes are recorded in [design](design.md). **open / needs Haitham** (W1).
- Unverified app states: loaded artwork and Prepare video, busy/error states, route-wide keyboard/menu/destructive combinations, LAN roles, all Settings/Help substates and opened/hover states. The empty Creative/Predefined pill report remains unconfirmed. Use the [unified checklist](../DELIVERY_CHECKLIST.md); completed empty-workspace/theme/width sweeps are evidence, not outstanding reruns. **open**.

- Real tile art for the twelve style presets: the swatches are abstract placeholders; drop `<id>.png` into `console/assets/styles/`. **needs Haitham** (the art).
- Inline `style="font-size:..."` in the scripts is still off the type scale. **open**.
- Haitham's eyes on every screen. **needs Haitham** (W1).

## Particles and the welcome modal (`docs/design.md`, `docs/architecture.md` "Reactions")
- **Animated sprites on their own.** A stand-alone set (the Studio's Particles choice, the chat's "on their own") draws still sprites only: the Kling path (`/more {mode: video}`) builds an effect from a pack's stickers and refuses a set no sticker owns. It needs an effect without a pack. **open**

- A real paid run of the AI-drawn particle sheet from the screen, to see how a real Nano Banana particle sheet cuts (the price and the job path are tested on the fake CLI). **needs a paid test** (W2).
- Separate Telegram effect/download delivery. **needs Haitham** (per-emoji motion is settled: docs/architecture.md "Reactions").
- Burst creation, many packs from one liked sheet (P14; proposal in git history). **needs Haitham** (W27).
- Particle sets are not part of the trash purge yet (a deleted set waits in `out/trash/particles/`). **open**.
- `DEFAULT_SPRITE_PX` 100 vs 200. **needs Haitham** (W21).
- A preview of the would-be sticker in the video-sheet override dialog. **open**.
- Optional Lottie Pre-run, Time scale, silhouette feasibility and blend modes require an owner decision and unchanged-default proof before implementation. **needs Haitham**.
- Older batches with no keyed/raw sheet on disk are not rebuilt when a slice of an animation edit merges back into the sheet (`rebuild_sheet` returns null; nothing breaks). **open, low**.
- Rule for all of it: effect checks are warnings with "use it anyway"; only Telegram's own limits may block.

## Chat and the agent (`docs/architecture.md`)

Remaining leads from the older chat audit follow. Checkpoint/profile implementation is now in durable turns (`docs/architecture.md` "Chat and the agent"); all five later memory findings are fixed. Reproduce old leads against current source before treating them as confirmed current defects.

1. **Short-message resolution.** "more like this" with a click redoes the clicked sticker; Arabic / Arabizi edit commands become new plans; "the first two" / "the rest" / "them all" resolve to one sticker; "make 5 same as 2" also redoes 2; "redo 3 of the previous batch" edits the current batch; a model-picked sticker is not confirmed; "I loved the last batch" records feedback on the last sticker. **open** (Arabic: also W32).
2. **Remaining context and feedback limits.** The rule classifier takes booleans, but the model classifier receives profile, last question, held plan, rendered structured summary and a compact focus fence. `summary_structured()` provides direct memory access. The CHAT prose fence still caps at 2,000 characters, so newer subject details/narrative can be omitted; focus recovery when a fresh generation has no saved sticker selection still needs current reproduction (checkpoint recovery now searches the same generation); the latest pass can be a job with no generation ("animate" says nothing to animate; a FAILED job stays in the summary); subject keys come from the deterministic expander ("falcon" / "falcon stickers" / "a falcon dancing" are three subjects, Arabic collapses to one subject "sticker"); "another" appends the old "Avoid..." text each time (the REQUEST fence cuts at 600 chars, so new preferences are cut first) and the built-in planner pastes that chat wording and the word "sticker" into the Subject line; feedback is consumed while planning and leaks across subjects; "I like 2 and hate 3" records 3 as liked. **open**.
3. **Remaining state/storage leads requiring current reproduction.** Settings edits during a turn; Redis lease expiry/restart behavior; delete-during-turn and session ID reuse; initial job/card linkage across interruptions; preserving typed input on 409/network refusal; polling a removed generation; full-session polling and Postgres write volume. Check these against the implemented checkpoints/resume boundary rather than assuming the pre-checkpointer behavior. A complete profile dual-write audit also remains open; taste votes are still JSON-only. **open / revalidate**.
4. **Smaller.** "continue with a dragon pack instead" at a creator gate approves the pack; the model's intent is trusted unchecked; a down model can cost up to 45 s per call; `ai: True` is hardcoded in another / edit / retry; the edit trace and stored pass show the stub, not the prompt sent. **open**.
5. **Gaps from the browser look**: an empty "New chat" created by clicking a setting other than stage with no chat open (W22); a chat edit of an animated sticker opens Prepare; "undo" has no "redo"; a bare "the last one" / "wear a hat" with no person and no focus still plans a new batch (W23). **needs Haitham**.

6. **The Telegram chat** (`services/tg_chat.py`, 2026-10-09): a picture sent to the bot is not read yet (it says so); single sheet cells, the editor and
   the gap slider stay in the browser; never run against the real bot (W51). **open**.
7. **The claim ledger behind Next batch** (`generation/claims.py`, migration 012, built and tested, not wired): "unclaimed" is still derived from the
   batches (`tasks.session_state`), not from the ledger. Wire `claim_next` for a pack request and "generate more", `mark_requested` when the sheet job
   is created, `link_generation` when its batch exists; the loser of a double click reads the winner's row; `ClaimError` text as the answer. Source:
   the export architecture §9-§10.7 (full text in git history). **open**.
8. **A local-model judge run** (no human labels, Haitham 2026-10-07): run `mirsal/local_eval/run.py run` on the current local pick (free), compare
   with the 2026-10-05 baseline (usable rate, median latency, UNJUDGED count), a two-model disagreement re-check, one dated block in
   `docs/architecture.md` ("Measurements"). **open**.

Other open items:

- Chat interaction proposal (conversational state, conditional decisions, stage slider, target resolution, plan confirmations; built slice in `docs/architecture.md`, decision tables + acceptance checks pending; full text in git history). **needs Haitham**.

- Creator recovery at every external side effect is not proven: checkpoints and tagged video-job lookup cover the lost-animation-pointer window, but initial sheet/session linkage and pack creation can still be interrupted between durable writes. A tagged REQUESTED job not yet scheduled may need Queue recovery. **open**; live crash validation belongs with W6.

- A liked-subject signal for the taste memory. **open**.
- Transformation templates: Arabic / Arabizi detection, more lexicons beside `banana.py` (pizza, avocado, ...), and your labelled resolver examples (structured evaluation data when supplied) to check the detector against. **needs Haitham** (W15, W32).
- Annotation: copy the AI caption (`sticker.caption`, `vision/transcribe.py`) into `stickers.annotation` and the pool's `search_text` (so "the one waving a flag" finds it), and `build_context(HIGH)` with the real images. **open**.
- The 40-utterance resolver eval (>= 95% exact ids). **needs Haitham** (W15).
- Selective regeneration as ONE sheet: several edited stickers are one 1x1 generation each (at most 4, and the reply says so); "keep 1-4 and redo 5-9 as one 2x2 / 3x3" (one paid sheet instead of N) and the `inherited_from` carry-over rows are not built. **open**.
- There is no terminal `mirsal chat`. The reducer's model summary has only run against fakes. **open, low**.
- A real chat -> Create run and a creator run against the real Higgsfield and a real bot. **needs a paid test** (W6).

## Engine and Studio (`docs/architecture.md`)

- **Short export codes** (exports stop emitting `G###`): registry `out/export_codes.json` + allocator (random 4, check, retry) at claim time, lazy
  backfill at the first export, `export_names` id = the code, the manifest carries both ids, a Postgres column. Source: the export architecture §9-§10.7 (full text in git history). **open**.
- **The exporter's bank picker** (Studio export dialog): a bank choice per `unresolved` cell, recorded and reversible. The library update API and resolver diagnostics are built; the picker screen and generation-cell choice route remain open. **open**.
- **In-batch versions, the rest**: a switcher to look at an earlier animation clip without re-cutting, the Postgres mirror of picks and versions,
  export naming per version (`revision`). **open**.
- `batch_import_inputs.py` at the repo root does not run (it calls `pl.Config.default()` / `pl.Pace.default()`, which do not exist, prints characters
  cp1252 cannot encode, ignores its arguments and would import a folder twice). Fix it before anyone runs it against the real `out/`. **open**.

- **Repeatable browser smoke coverage:** turn the documented copied-data checks into maintained automation for issue colours, reversible overrides, history folds, captions and bulk move; unsampled combinations remain. Browser sweeps now exist in the acceptance/audit evidence, so this is automation maintenance rather than an absence of browser verification. **open**.
- **Remaining shared-code follow-ups:** Studio edge synchronization and other watcher consumers; range/segment/download/preview/cache presenters. T-024/025 concern saved-set/Emoji sliders; T-031/034/035 retain other download/preview/cache consumers. Revalidate old leads against current code; the five reviewed refactors and API/agent/UI folder redesign are implemented. **open**.
- A second request while the *pipeline* is busy gets 409 (the provider jobs have their own durable queue). `result.json` is read-modify-write under one in-process lock plus the cross-process writer lock: two request threads can still interleave inside one server (two processes are kept out by the writer lock; every file write is atomic: `tests/test_multiprocess.py`). **open, low**.
- Add a focused-tier profile for the trash purge / storage area (`README.md` "Test budget": the existing profiles do not cover it). **open**.

## Live generation (`docs/generation.md`)

- **Paid proof of the face preset**: one `generic emojis` sheet (v4 + core-v1), measure keying and the cut only (never open the media); if limbs
  persist, tighten the v4 clause once (new `_v5` files, never edit v4) and retry once; then one pack at the default gap. About 2 credits + one pack.
  **needs a paid test** (W50).

- S4 re-run with Kling `pro` and the default gap decision (`slot_fill`); remaining S7 outline decision (engine versus model-drawn). **needs a paid test** (W7).
- The vision judge's recovery is a recommendation (`vision/recovery.py`); nothing executes it. Executing means paid regenerations, so it needs a confirmation flow. **needs Haitham**.
- Original planner leftovers, ask before building: UAE content rules as a lint (no flags / emblems / text, no real people or rulers, the falcon is always a young brown saker falcon chick, Emirati dress, Commemoration Day solemn), English + Arabic Telegram search keywords per cell (0-20, 64 characters, English first), 4x4 and 16:9 sheets (`split_grid` handles 2x2 and 3x3), no trademarks in pack titles and tags. **needs Haitham**.
- The built-in prompt planner drops everything after `for / in / at / during / with / on` into the file name only (`prompter.SPLIT`: "spiderman in dubai" sends `Subject: spiderman`); the Generate prompt step makes it visible, a context-as-setting-line fix is open. **open**.
- The Generate prompt step: Enter, the non-live button, the cost of an OpenAI call made by the enhancer. **needs Haitham** (W16, W18, W19).
- The Higgsfield `wait` and the plan expander have timeouts (300 s create, `timeout_s + 60` wait, 60 s per model call); a *hung chat* was never reproduced, only a turn orphaned by a server restart (fixed). If "thinking" sticks again with a live server, capture the session's last step label: `out/sessions/S###.json` `messages[-1].steps`. **watch**.
- Stalled-job recovery has not run against the real Higgsfield (J022-J025). **needs a paid test** (W5).
- Per-chat paid parallelism and `MIRSAL_JOB_MODE=queue` have only run on the fake CLI. **needs a paid test** (W10).

## Batch groups (`docs/architecture.md`)

- **Suggest a family by meaning**: a batch whose subject/prompt embedding (local `nomic-embed-text`) is close to another family's (G103 "superhero in dubai" vs the Superhero Dubai family) shows one chip *"Looks like Superhero Dubai: Join?"* with **Join** / **Not related** (remembered, never asked again); moving a sticker into a pack whose stickers belong to another family asks the same. Never merges without a click. **open**.
- **Trace a batch to its request**: jobs carry no chat session (`J046-J048: session None`); record `origin {session, message}` and `intent` (the person's words) on jobs and batches, mirrored to Postgres, so a chat edit is linked both ways. **open**.

## Store and search (`docs/architecture.md`)

- 3B: the eval set and precision@5 >= 0.8; an Arabic / Arabizi query parser (a small model; deterministic patterns today); a search-result cache keyed by a `pool_version` counter (embeddings and plans are cached, hits are not); the gap flow shows no price. **needs Haitham** (W12).
- 3C: an `edge_quality` check (a soft alpha gradient, not a binary edge), `--subject N`, a stronger matte (BiRefNet, MIT) and SAM 2 click-to-refine, HEIC input (`pillow-heif`), `SOURCE_PHOTO` asset rows, optional paid AI motion (price first), a composites test (IoU >= 0.92). **needs Haitham** (W14).
- **3D text template stickers (not started).** A library of flashing template stickers with a text slot, CapCut-style: `mirsal/templates/<id>/template.json` (`id, version, tags {en[], ar[]}, occasion, mood, frames[1-4] {art | null, duration_ms, text_style}, slot {x,y,w,h,rotation,align,max_chars,font_id}`, optional `subject_slot` for a photo cutout), 30+ procedural starters (greetings, reactions, love, birthday, UAE occasions), text rendered by code (Cairo, OFL, covers Latin and Arabic; Pillow with raqm, fallback `arabic-reshaper` + `python-bidi`; never split a word), encoded as WEBM VP9 alpha and animated WebP (not GIF: 1-bit alpha), matched to the last chat message when it is <= 4 words / 24 characters (exact occasion tag, then the embedding, then generic), editing re-renders in under a second as a child generation. Tests: every template passes `template check`, Arabic joins, Telegram validators, "happy eid" ranks Eid templates first. **needs Haitham** (W39).
- **3E 3D parallax photos (not started).** A photo gets depth and tilts with the phone: embedded Portrait-HEIC depth first, else Depth Anything V2 **Small** (Apache-2.0; the larger ones are non-commercial) through onnxruntime, edge-aware guided filter, focal plane at the subject's median depth (the cutout), a self-contained WebGL viewer (`parallax.html`, gyroscope with the iOS permission tap, mouse fallback, reduced motion = static), optional `--layers 2|3` with inpainting, optional `--bake` loop video. On-device only; private assets. **needs Haitham** (W39).
- Library packs still live in `out/library/library.json` (the old plan moved them to `packs` / `pack_stickers`; wait for the app's pack curation). `reviews.trace_run_id` exists and nothing writes it. Per-video task rows. An S3-compatible store behind `AssetStore`. **open, low**.
- **Frozen constraints.** `python -m mirsal db check` reports a CHECK constraint, default or index that differs from what the files declare (a constraint created inside `IF NOT EXISTS` is frozen at its first version), but nothing upgrades one automatically: when it reports a drift, write the next numbered migration (`ALTER ... DROP CONSTRAINT / ADD CONSTRAINT`). A dimension change in `005_vectors.sql` clears stored vectors by necessity; `db migrate` says how many and that `pool reindex` refills them. **standing procedure**.
- The trash purge's SQL (`store/purge_rows.py`) has only run against a recording fake connection, never a real Postgres. **needs a run** (W4).
- Embeddings stay local and hardcoded (`services/embed.py` `EMBED_MODEL`, decided): no hosted embeddings, no swap of the embedding model (it would change the vector dimension and invalidate every stored vector in `005_vectors.sql`).

## API and production (`docs/api-integration.md`)

- Reference images per user, the Redis cache keys (`u:local`), moving accounts out of `out/users.json` (packs and the Library are per person since 2026-10-05, `docs/api-integration.md`). **open** (the office LAN).
- Per-job temp directories and retention policies; the Studio has no queue panel for DEAD rows yet (`mirsal queue status` shows them). **open**.
- **Contract polish:** a role-dependent shape for `GET /api/generations` (an owner also gets `health`, `paths`, `stale`); `GET /api/live/cost` answers `200 {"credits": null, "error"}` when a price is unknown (by design for the page, not a status code); camelCase leaks in a snake_case API (`updatedAt` in `media/video_project.py`, `packId` in `console/server.py`: the Studio reads them); the Host check needs the port in the header; no `Deprecation` policy yet; pagination is opt-in on three lists only (`/api/library`, `/api/tasks`, `/api/usage`, `/api/watch` still return everything); `415` for a wrong `Content-Type` is not built (W35). **open**.
- The regression suites (visual, chroma, transformation, conversation datasets) in one command. The metrics (`flow/metrics.py`) count what happened; what they mean for taste waits for the judge's calibration (W11). **open**.
- The parked React frontend `mirsal/web/`: retain or delete (W33). **needs Haitham**. Populated editor phone repairs are technical findings UX-01, not an owner acceptance gate.
- **Sticker export follow-up.** the export architecture §9–10 (full text in git history). **Open:** pack-intent resolver and chat/claim wiring, public generation short-code allocator and backfill, exporter bank picker UI and generation-cell choice endpoint, filename length/NFC checks, in-batch versions and custom presets. Current exports use `G###` and revision 1. **needs Haitham** (the go for this remaining scope; needs a W number).
- The retired History screen (`console/history.js`, `#/history`). **needs Haitham** (W34).
- Content safety, OpenAI calls without a plan card, `out/` in git, a backup command. **needs Haitham** (W18, W29, W30, W31).
- A native FastAPI rewrite of the legacy routes (today they run through the adapter over the original handler, byte-identical; `GET /api/openapi.json` is the baseline). After v1.0: it changes nothing a person sees. **open, low**.
- The office LAN runs on this PC: if it sleeps or restarts, everyone is offline (`serve --lan` says so on start). A machine that stays on, or a hosted server (paused), would remove this. **needs Haitham**.
- Public rate limiting and Google OAuth: **parked** (Haitham, 2026-10-02; the office LAN uses email + password instead, `docs/api-integration.md`). The engine's per-minute 429 (`console/server.py` `_wait`, 65/min keyed on user id + kind, `Retry-After`) stays as it is.

## Office LAN (`docs/api-integration.md`)

- **The admin role** manages people (Users > People, the bot's buttons via `admin_bot.apply`) and can take any pack off Trending (making a pack public is its maker's); everywhere else it is treated as a member. Whether an admin should also see everyone's batches is undecided. **needs Haitham**.
- The Telegram admin bot runs only with `serve --lan` and a configured bot; its cards have run against a fake Telegram only (`tests/test_accounts.py`). The first real sign-up is the live check. **needs a run**.
- Ticket drafts use the LOCAL model only (free); with no local model every ticket keeps its preset questions. **open, low**.
- `GET /api/chat/sessions/{id}/stream` sends the last message only; a turn that adds two messages at once is caught by the full read at `done`. **open, low**.

## Help & Support (`docs/architecture.md` "Chat and the agent")

- FAQ retrieval is measured on the seeds only (`docs/architecture.md` "Chat and the agent"). Still unmeasured, all agent-runnable on a scratch copy with the local 9B:
  - answers end to end: cited, nothing invented, latency;
  - real screenshots read by the vision model (the 30-case set has ten text descriptions, not images);
  - ranking over the combined FAQ + docs + notes corpus;
  - vector ranking through Postgres (the in-process check used the same embedder, not the HNSW index).
  **open**.
- On-topic questions the help does not cover ("Does Mirsal upload stickers to TikTok?", "print on a t-shirt") score 0.77-0.83 in vector mode, above `ENOUGH` 0.70 and above the lowest correct match (0.78), so no threshold separates them. The model step guards (it must cite, or say "not yet" with a feature request), but the no-model fallback (`support._fallback`) could quote a near-miss entry. Gate the fallback (for example the lexical and vector top hits must agree) and keep these as regression queries. **open**.
- Lexical mode (no Postgres or no embedder) ranks the right entry first on all 30 cases but is below `ENOUGH` 0.45 on three long, noisy queries: the 8 MB screenshot (0.363), Save vs Save as new (0.438), a member's missing Send to Telegram (0.426). Vector mode scores them 0.83-0.86. The threshold stays; this matters only when vector search is down. **open, low**.
- A pending account cannot open Help (`_member` refuses it like every member route), so a person waiting for approval cannot ask why. **open, low**.
- A Report (source `report`) shows in the staff Queue but has no conversation: the person sees the reply only as a notification and in its ticket. **open, low**.
- `serve --stdlib` has no Help routes (the old server goes after one release). **parked**.

## Testing

- Agent area inherits **322 tests / 4 failures / 9 errors**; triage existing failures with fakes. Current JS 390/390 and wrapper 18/18 are evidence, not outstanding reruns. **open**.

- `tests.test_batches.RemoveRoutes` fails now and then on Windows in teardown (a file still locked). **open**.

- `tests.test_golden` failed intermittently once under heavy load (another Python suite running at the same time): one test left the server busy (`409 busy`) for the next. It passes alone and as a suite on a quiet machine (FastAPI and stdlib alike). If it returns, make `GoldenPathTests.wait` also wait for `busy` to stay false for a moment before the next create. **watch**.

## Deployment: parked

Paused by Haitham on 2026-10-02: the prepared gateway, SQL, Docker and Render code stays inert. The old deployment plan and runbook remain in git history; restore them if deployment is explicitly resumed. Current [prepared hosting notes](api-integration.md#prepared-hosting-paused) and W40-W48 below retain the unresolved decisions. The implementation is consolidated in `main`; trimming duplicate documentation does not activate hosting. **Telegram never-twice** (`services/telegram.py` `fingerprint()`, `send(mode="once" | "replace" | "new_set")`, `tests/test_telegram.py::NeverTwice`) and the **library fingerprint** remain app functionality. `deploy/gateway/ratelimit.py` stays inert.

## Redesign

- **Settings > Spending (open, needs a route):** the redesign mockup shows the daily credit limit and "jobs at the same time" as controls; today they are `.env` only (`MIRSAL_DAILY_CREDITS`, `MIRSAL_PAID_PARALLEL`). Build an owner-only settings route that writes them (and `doctor` reports them) before the controls are drawn.


## Owner decisions

This section replaces the separate waiting file. **W#** references above retain the numbered items below. Each item needs a verdict, review or explicitly priced experiment. Preserve unanswered gates; delete an answered item when its decision is recorded in the owning area doc. Deployment items 40–48 stay parked. The documentation cleanup authorizes no paid calls or publishing.

### A. Eyes and money: things only a person can verify

**1. Review the app in your own browser.** Use the [app and API delivery checklist](../DELIVERY_CHECKLIST.md) on the real-data viewer :8770, desktop and phone, both themes; mutations use a disposable copy. Remaining verdicts: visual hierarchy, Effects/Reactions wording (F-31), films/artwork, editing/recovery usability and paid-quality/delivery checks where separately approved. `docs/backlog.md` lists the known defects (past audits in git history); automated technical checks are evidence, not your acceptance. Record the reviewed build; branch consolidation into `main` is already complete. Unblocks: owner visual acceptance.

**2. Run the approved paid check (6.5 credits).** Your go-ahead of 2026-10-03 (price shown, one attempt each) is still unused: one Kling 2x2 clip with the v2 prompt (4.5 credits; script pattern `kling_exp.py`; measure `key_is_seamless`, never open the media) and one drawn particle sheet (2.0) through the app's own route with `ref_clause`, to confirm the exact 2x2 cut. Recommendation: say "run it" once and a session runs both, measuring only. Unblocks: knowing whether the v2 video prompt and the particle-sheet cut work for real (`docs/architecture.md` "Reactions", `docs/backlog.md` particles).


**4. Do you accept the remaining purge decisions?** There is no packs table in Postgres (a pack purge is files + `library.json`); `reviews` stay and referenced rows become `status='PURGED'` tombstones; "delete all" skips shared-sticker items and lists refusals; deleted particle sets are not part of permanent purge yet. The particle rework already settles owner detachment: pack purge retains sets visibly rather than leaving pack assignments dangling. Recommendation: accept the remaining policies; the SQL in `store/purge_rows.py` has only a recording-fake check, so test it against scratch Postgres before relying on it. Unblocks: calling the trash purge done (`docs/architecture.md`).

**5. Press *Check · free* or *Continue · same ticket* on the four paid sheets J022-J025.** Their download failed on this PC's certificate store (`[ASN1: NOT_ENOUGH_DATA]`); the jobs are `FAILED` but hold their Higgsfield tickets, so about 8 credits are already paid for. Recommendation: after restarting the server, press the button on each in the Queue panel (no second charge); this is also the first real test of the recovery actions. Unblocks: the four sheets, and proof that `generation/recovery.py` works against the real Higgsfield.

**6. Do one real chat -> Create run, and one agentic-creator run, with you present.** Type a request in the AI chat and press Create (about 2 credits for a sheet); then a creator run (request to Telegram, *Images* or *Full video*) with a spare Telegram bot. Nothing in the chat has run against the real Higgsfield or a real bot, only against fakes and prepared sheets (`tests/test_creator_live.py`). Recommendation: do both on one afternoon, with "Ask before spending" on. Unblocks: confidence in the chat's Create path and the creator's Telegram step.

**7. Buy one real animated pack, and Kling `pro` at the default gap.** A real run (spends credits) to close S4: `python -m mirsal measure-cells` then shows the flagged share (first numbers: 0.74 gap = 5.6%, 0.80 = 88.9%, 0.84 = 44.4%). The remaining S7 choice is engine outline versus model-drawn outline; the new-plan grid default is already 2×2. Recommendation: one pack at the default gap, then decide. Unblocks: the default `slot_fill` gap and the S7 choice (`docs/backlog.md`, live generation).

**8. Look at the loop close.** `close_loop` was rewritten (`engine/video.py`): the head of a clip is the source untouched, the last 6 frames ease into frame 0; the animation cache version was bumped. Animating a batch again (from its stored video, no credits) makes new clips: do the first frames / the thumbnail show a ghost, and does the loop point visibly settle? Recommendation: check one batch; if you still dislike the "dissolve", make the generator close loops itself (first = last image, already requested when Loop is on). Unblocks: whether the generator or only the engine closes loops.

**9. Look at the welcome modal and Home.** First load of a session (the film opens over Home), and Home's "Watch the film": the fast-cut film (`console/assets/welcome/welcome.mp4`, Seedance 2.5 take 2, 105 credits; take 1 was rejected as too slow) and the four slides were checked with numbers only; are the on-screen words spelled right? Another take is a new price (one attempt each was approved). Home is reachable from the responsive rail. It now has two distinct sticker bands with welcome and supplied onboarding films; Dark / Light is in Settings → Appearance. Fake-data browser checks pass at 1440 / 900 / 390px, including film/card geometry and theme persistence; your visual verdict on the real media and wording remains open. Recommendation: look once on desktop and once narrow. Unblocks: closing the welcome review (`docs/design.md`).

**10. Try accounts, the worker queue and transformations for real.** So far they have run on fakes and synthetic sheets only: `python -m mirsal user add Amira` then `curl -H "Authorization: Bearer <token>" localhost:8789/api/me` and `/api/openapi.json` (an account sees only its own chats and batches, 404 for a stranger's, and cannot spend unless `--spend`); `MIRSAL_JOB_MODE=queue` with `python -m mirsal worker` and one real Create (about 2 credits; never unattended); `MIRSAL_PAID_PARALLEL` (default 3) at the first real parallel use; "dog as banana" and "dog as banana, no dancing" in the chat. Recommendation: do the curl and the transformation phrases now (free), the queue and parallel runs with your first real Create (item 6). Unblocks: the queue panel for DEAD rows and the transformation lexicons (`docs/backlog.md`).

**49. Review and publish the FAQ, then look at Help (2026-10-05).** The canonical 87 Help entries are in `faq/seed.json`. Imports create drafts unless explicitly published. The historical 66-entry import was draft-only; current publication state must be checked in Help → FAQ review. Only you decide what the help says.
1. The server owner starts or restarts the intended app from the venv to load current code.
2. Read each draft in Help > FAQ review, edit it where needed, and Publish (or Discard). A published entry answers people at once and is embedded for vector search.
3. Optionally, look at Help yourself: a member's question with a screenshot, No, a reply from Help > Queue (try Private once), Resolve.

Recommendation: publish the accounts, telegram and troubleshooting entries first; they answer the commonest questions. Unblocks: a support agent that answers from reviewed help; the word "verified" for Help.

### B. Calibration inputs only you can supply

**12. Write the pool search queries file.** A labelled pool-query dataset (not supplied yet): about 30 queries "{topic} doing {action}" (English, Arabic, Arabizi) with the sticker ids you consider right, plus at least 5 that must return nothing; `python -m mirsal pool search "..."` is then measured against it. Recommendation: write it from real searches you would do. Unblocks: precision@5 >= 0.8 and the Arabic / Arabizi query parser (`docs/backlog.md`, store and search).

**13. Confirm the softness threshold.** `python -m mirsal measure-sharpness` flags the 8 G002 animations (0.65 of their still's edge detail, about 1.3 px of blur) and none of the other 23; are those the soft ones, or which batch should it have flagged? Threshold `min_detail_vs_still` 0.75 (`engine/config.py`). Recommendation: check G002 by eye once. Unblocks: calling the threshold final.

**14. Judge the photo cutout edges.** `mirsal/out/photo/photo-upload.png` and 10+ real photos in `inputs/photos/` (git-ignored; include a few iPhone Portrait HEIC, which are not read yet). Recommendation: supply the photos. Unblocks: the HEIC input and the matte upgrade (BiRefNet, SAM 2) in `docs/backlog.md`.

**15. Compare the prompt text and give the resolver examples.** `python -m mirsal prompt lab` and `prompt lab --ai` (20 inputs, the AI on the local model) against the historical prompt samples in Git (`51f327b1:docs/inputs/prompt_samples.md`); and supply the labelled resolver utterances (the 40-utterance resolver eval, >= 95% exact ids) and your transformation examples (the detector was written from the one example "dog as banana"). Recommendation: send 40 real sentences, including Arabic and short ones. Unblocks: the resolver eval and the transformation lexicons.

### C. Product decisions in the Studio and the chat

**16. Does Enter in the Studio's prompt box open the Generate prompt step, or still start a paid sheet at once?** Today Enter spends at once with no price on screen (the old Generate button's credit chip is gone). Recommendation: Enter opens the free prompt step like the button; the paid click is the separate *Generate sheet*, which shows the price on its own line (rule 13). Unblocks: closing the price-visibility gap of the Generate prompt step (`docs/architecture.md`).

**18. OpenAI calls without a plan card.** The plan expander (`generation/expander.py`), the intent model (`agent/brain.py`) and pool embeddings (`services/embed.py`) call OpenAI when it is the provider, with no price and no go-ahead, which contradicts rule 13 as written. Recommendation: fold their cost into the plan card's estimate (or scope rule 13 to Higgsfield credits and add a monthly OpenAI budget); local models are free and unaffected. The Studio's AI enhancer now shows the engine and model next to the chip (Local free, Cloud one small OpenAI call) and the step says which one wrote the prompt, so the cloud call is visible; what stays open is whether it should also carry a price or a budget. Unblocks: the hosted-chat question (item 44) and any public user.

**19. A non-live Studio has no button for the prepared-sheet create path.** With Higgsfield not connected, the prepared-sheet path is reachable only by Enter and the suggestion chips. Add a visible button, or is that fine? Recommendation: add a labelled button (rule 6: a path that exists must be reachable by a control). Unblocks: a Studio that works without Higgsfield and an end to the Enter ambiguity in item 16.

**20. Studio menu point 3: which screen did you mean?** You asked that the settings block "must be the composer's"; it was NOT built because the Studio screen already mounts the composer's chips (`composerMount` removes the old *White outline* pills), so no lookalike exists on it. Was it the particle wizard? Recommendation: name the screen and Claude fixes that one. Unblocks: closing the Studio-menu item.

**21. `DEFAULT_SPRITE_PX` (`flow/effects.py`, now 100): change to 200?** Measured: a smaller sprite gives no latency gain (the engine already shrinks sprites) and 100 changes the 512 final by 9/255. Recommendation: 200 for render, keep 100 for preview. Unblocks: closing the particle-render default.

**22. An empty "New chat" is created when a setting other than stage is clicked with no chat open.** Intended (the setting needs a home), or should the setting wait until a chat exists? Recommendation: create the chat only on the first message and keep the setting in the bar meanwhile. Unblocks: the chat-list hygiene fix.

**23. Chat gaps the browser look left open: what should happen?** (a) A chat edit of an animated sticker opens Prepare (the still editor), not the animated editor; (b) "undo" has no "redo"; (c) a bare "the last one" / "wear a hat" with no person and no focus still plans a NEW batch. Recommendation: (a) open the animated editor, (b) add "redo" as the inverse of one undo, (c) ask "which one?" when a batch is open, otherwise plan. Unblocks: the three open lines in `docs/backlog.md` (agent and chat).

### D. Particle verdicts (nothing is built on a guess)

**27. Go for burst creation (P14), and its four questions.** Many packs from one liked sheet (burst creation, P14; proposal in git history): is the go given, and (1) is 6 lanes per burst the right cap (a setting?), (2) does each lane become its own pack automatically or a batch the person adds to a pack, (3) may the suggestions use the vision model on the sheet (with the one-time AI vision yes), (4) is `B###/Q###` acceptable as the lane id? Recommendation: build when explicitly authorized; answers 6, a batch (adding stays your click), yes with the one-time yes, yes. Unblocks: the whole burst-creation build.


### E. Repo, safety and housekeeping decisions (held questions: do not re-raise unless asked)

**29. Is `mirsal/out/` in git on purpose?** It has 3,480 tracked files as measured on 2026-10-21; source and runtime data remain mixed. SQLite checkpoint/profile files are ignored. Recommendation: if not, ignore `mirsal/out/`, `git rm -r --cached` it (history keeps the old blobs unless rewritten) and write the backup command of item 30; `cache/` and `sessions/` are the obvious first candidates either way. Unblocks: a clean `git status` after every run, and the public-repo scrub (item 45).

**30. A backup command for `out/`.** Should the app get `python -m mirsal backup` (zip of `out/` minus the cache)? Recommendation: yes, small and free. Unblocks: item 29.

**31. Content safety.** One batch returned a stereotyped, offensive depiction nobody asked for ("superman in dubai"); the vision judge scores quality only and the provider's filter did not catch it. Options: safety reasons in the judge (`OFFENSIVE_CONTENT`, `STEREOTYPE`, a changed judge prompt), a separate moderation call before / after generation, or showing the provider's flag. Recommendation: the provider flag shown first (free); any added judge reasons need an agent-prepared evaluation. Unblocks: the moderation policy any public API needs.

**32. Arabic prompts.** How should Arabic / Arabizi requests be handled (detection, planner, tags)? Recommendation: detect and pass through the local model, with your examples (item 15) as the test set. Unblocks: the Arabic edit commands and Arabic query parser in `docs/backlog.md`.

**33. Keep or delete the parked React gateway `mirsal/web/` (not served).** Recommendation: delete it, git keeps it; ask first (`docs/rules.md`, "Session guardrails"). Unblocks: a smaller tree and an unambiguous front end.

**34. Delete the retired History screen (`console/history.js`, `#/history`)?** It remains reachable as Watch folders, not conversation/batch history; the current audit finds collapsed phone rows (UX-09). Recommendation: retire it if no longer needed, otherwise repair the retained screen. Unblocks: legacy route disposition; no deletion or action retirement without your decision.

**35. Why `415` for a wrong `Content-Type` is not built, and whether to.** `curl -d` without a header would start failing. Recommendation: keep it unbuilt (the contract must not change by a byte). Unblocks: closing the item.


**39. Do you want the 3D text templates and the 3D parallax photos built at all?** Both are unstarted (`docs/backlog.md`, store and search 3D / 3E): CapCut-style flashing text-slot stickers with 30+ procedural starters, and photo depth with a gyroscope WebGL viewer. Recommendation: no for now; both are large and neither is on the golden path. Unblocks: deleting or scheduling two large backlog items.

**51. Retire the old AddCollection password, then try the Telegram chat for real.** Export to collection has reached the real CMS: on 2026-10-14
two packs ("Girl Emirati with hat", 9; "Generic Emojis", 10) were accepted by `emojicms.devinprocess.com` (`out/collection_exports.jsonl`). Still open: the
old password pasted in the former `docs/Api/AddCollection-API .md` is in git history (commit dd17f61, pushed), so change it on the CMS if that is not done yet (the
developer key in `mirsal/.env` replaces it); and the Telegram chat with `serve --lan` restarted (`/start`, `/model`, a request: real stickers, the album, a
creator run's edited message). Recommendation: both now, they cost nothing but a pack's credits. Unblocks: the backlog's Telegram chat items.

**50. The paid proof of the face preset** (about 2 credits + one pack): see the backlog, Live generation. Recommendation: yes, once. Unblocks: the v4
face clause.

### F. Parked: the deployment questions (plan in git history, former section 17; do not raise unless asked)

An answer restores `docs/deployment_plan.md` from git history and deletes the question here.

**40. Supabase Auth for Google, or our own OAuth client?** Recommendation: Supabase Auth (about 150 fewer lines we would own). Unblocks: Phase 1 (accounts).

**41. Render (suspend quota; is the worker free?) or an Oracle Always Free VM (ops)?** Recommendation: Render + Supabase + Upstash; the VM if the suspend is unwelcome; the engine never runs on Vercel. Unblocks: Phase 0 hosting files and Phase 6 launch.

**42. Is one shared Higgsfield account for all users acceptable to Higgsfield's terms?** Ask Higgsfield, not a technical detail. Recommendation: ask before any public user. Unblocks: per-person credits (Phase 2) and any public launch.

**43. One shared Telegram bot, or one bot token per user?** Recommendation: one shared bot to start (no encrypted-token column). Unblocks: Phase 4 and the `accounts` table shape.

**44. For the hosted chat: a hosted LLM provider with a monthly budget and a shown price, or self-hosted weights?** Recommendation: hosted with a budget, after item 18. Unblocks: Phase 5 (agent).

**45. Is `out/` untracked in the public repo, and is the pre-scrub history kept offline as the backup?** Recommendation: yes to both; rotate secrets first, rewrite history only on your explicit go, offline backup of the pre-scrub repository. Unblocks: the scrub runbook (`docs/deployment_plan.md` section 8) and item 29.

**46. Which IP retention: 7, 30 or 90 days?** Recommendation: 30 (abuse handling), `ip_hash` for counting. Unblocks: the `user_analysis` retention worker.

**47. Do the Studio's screens ship to the public deployment, or does the public API serve only the Mirsal app?** Recommendation: API only; the screens are a sandbox (rule 11). Unblocks: what the public gateway serves.

**48. Do the two new tables live in the same Supabase project as the mirror, or a separate one?** Recommendation: the same project, separate schema. Unblocks: the migration files.

Also parked, not a question: rate limiting, deployment and OAuth are paused (2026-10-02); the engine's per-minute 429 (`console/server.py` `_wait`) stays as it is; the gateway, SQL, Docker and Render files stay untouched until Haitham asks.
