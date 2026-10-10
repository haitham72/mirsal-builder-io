# Waiting for Haitham: the only list that needs a person

**This is a tracker, not a log** (`CLAUDE.md` rule 7, with `docs/backlog.md`). Every item here needs Haitham's eyes, a verdict or money; nothing in it can be settled by a session alone. Each item: the question in one sentence, the recommendation, and what it unblocks. **An answered item is deleted in the same step** it is recorded as architecture in the doc of its area (history lives in git). Items 1-39 are live; items 40-48 are **parked** (the deployment plan is paused: do not raise a parked or "held" item unless Haitham asks).

How a go-ahead works: a shown price plus "let's try" is that one experiment; "push everything" is one push of the work branch. No paid call without the price shown and a yes (`CLAUDE.md` rule 13). Every media judgement is made with Python metrics, never by opening the files (rule 9); Haitham's eyes are the exception this list asks for.

## A. Eyes and money: things only a person can verify

**1. Look at the rest of the app in your own browser.** Not yet looked at by you: (a) **the AI chat**: the engine pill (Auto / Local / Cloud), a greeting gets a greeting, the plan card with ONE price line and the go-ahead buttons, "this is bad" with a clicked sticker, "make G012/S3 happier", the editor round trip from the chat; (b) **the Library**: a pack screen, **Download .zip**, **Move N to…** and drag-to-move, Delete pack and the Trash card in Settings; (c) **the Studio's other tabs**: the animation verdict switch (take back / switch back), the Prompt tab's editable boxes and Reset, **AI captions** (asks for AI vision once), the variations strip on Superhero Dubai and the new Animation tab on a batch without animations; (d) `python -m mirsal metrics`, `db status` / `db check`. (e) **imports and personal packs** (2026-10-05, never seen in a browser): the composer's **Use my own sheet** and **Import from Higgsfield** (a duplicate opens what exists, Retry import), a member's own Library with Add to pack and no Telegram button, a pack's **Public** toggle, Trending's maker / views / uses and **Use in my workflow** as a copy; the Library's **+ > Import pack** (2026-10-08: a sheet, or a video on its own, cut and waiting in the Studio); and the 86 animations remade by `reloop` with the new loop end (backup `out/reloop-backups/20261005T065627Z`); **the chat's stages and batch follow-up** (2026-10-09, never seen in a browser): the stage pill left of Send and its popover (mouse and keyboard), a Prompt-stage plan with its sheet prompt and Edit, a plan card's "Batch 01 of 04", the follow-up chips Regenerate · Batch 02 · 03 · 04 after a batch is cut, and the same in Telegram (`/stage`, the buttons). Restart `python -m mirsal serve` from `mirsal/venv` first. Unblocks: the word "verified" (your own look; no test run is part of that bar, `docs/testing.md`).

**2. Run the approved paid check (6.5 credits).** Your go-ahead of 2026-10-03 (price shown, one attempt each) is still unused: one Kling 2x2 clip with the v2 prompt (4.5 credits; script pattern `kling_exp.py`; measure `key_is_seamless`, never open the media) and one drawn particle sheet (2.0) through the app's own route with `ref_clause`, to confirm the exact 2x2 cut. Recommendation: say "run it" once and a session runs both, measuring only. Unblocks: knowing whether the v2 video prompt and the particle-sheet cut work for real (`docs/effects.md`, `docs/backlog.md` particles).


**4. Do you accept the remaining purge decisions?** There is no packs table in Postgres (a pack purge is files + `library.json`); `reviews` stay and referenced rows become `status='PURGED'` tombstones; "delete all" skips shared-sticker items and lists refusals; deleted particle sets are not part of permanent purge yet. The particle rework already settles owner detachment: pack purge retains sets visibly rather than leaving pack assignments dangling. Recommendation: accept the remaining policies; the SQL in `store/purge_rows.py` has only a recording-fake check, so test it against scratch Postgres before relying on it. Unblocks: calling the trash purge done (`docs/engine-and-studio.md`, "Emptying the trash").

**5. Press *Check · free* or *Continue · same ticket* on the four paid sheets J022-J025.** Their download failed on this PC's certificate store (`[ASN1: NOT_ENOUGH_DATA]`); the jobs are `FAILED` but hold their Higgsfield tickets, so about 8 credits are already paid for. Recommendation: after restarting the server, press the button on each in the Queue panel (no second charge); this is also the first real test of the recovery actions. Unblocks: the four sheets, and proof that `generation/recovery.py` works against the real Higgsfield.

**6. Do one real chat -> Create run, and one agentic-creator run, with you present.** Type a request in the AI chat and press Create (about 2 credits for a sheet); then a creator run (request to Telegram, *Images* or *Full video*) with a spare Telegram bot. Nothing in the chat has run against the real Higgsfield or a real bot, only against fakes and prepared sheets (`tests/test_creator_live.py`). Recommendation: do both on one afternoon, with "Ask before spending" on. Unblocks: confidence in the chat's Create path and the creator's Telegram step.

**7. Buy one real animated pack, and Kling `pro` at the default gap.** A real run (spends credits) to close S4: `python -m mirsal measure-cells` then shows the flagged share (first numbers: 0.74 gap = 5.6%, 0.80 = 88.9%, 0.84 = 44.4%). Also the S7 decisions: one 3x3 sheet vs single stickers, the engine's outline vs a model-drawn one. Recommendation: one pack at the default gap, then decide. Unblocks: the default `slot_fill` gap and the S7 choice (`docs/backlog.md`, live generation).

**8. Look at the loop close.** `close_loop` was rewritten (`engine/video.py`): the head of a clip is the source untouched, the last 6 frames ease into frame 0; the animation cache version was bumped. Animating a batch again (from its stored video, no credits) makes new clips: do the first frames / the thumbnail show a ghost, and does the loop point visibly settle? Recommendation: check one batch; if you still dislike the "dissolve", make the generator close loops itself (first = last image, already requested when Loop is on). Unblocks: whether the generator or only the engine closes loops.

**9. Look at the welcome modal and Home.** First load of a session (the film opens over Home), and Home's "Watch the film": the fast-cut film (`console/assets/welcome/welcome.mp4`, Seedance 2.5 take 2, 105 credits; take 1 was rejected as too slow) and the four slides were checked with numbers only; are the on-screen words spelled right? Another take is a new price (one attempt each was approved). Note the rail logo is hidden under 760 px, so on a phone only the first-load opening exists, and Home is reachable only at launch (the narrow bottom rail has no Home; it is also 430 px wide on a 390 px phone, wider than the screen on every section). Recommendation: look once on desktop and once narrow. Unblocks: closing `docs/onboarding.md`.

**10. Try accounts, the worker queue and transformations for real.** So far they have run on fakes and synthetic sheets only: `python -m mirsal user add Amira` then `curl -H "Authorization: Bearer <token>" localhost:8789/api/me` and `/api/openapi.json` (an account sees only its own chats and batches, 404 for a stranger's, and cannot spend unless `--spend`); `MIRSAL_JOB_MODE=queue` with `python -m mirsal worker` and one real Create (about 2 credits; never unattended); `MIRSAL_PAID_PARALLEL` (default 3) at the first real parallel use; "dog as banana" and "dog as banana, no dancing" in the chat. Recommendation: do the curl and the transformation phrases now (free), the queue and parallel runs with your first real Create (item 6). Unblocks: the queue panel for DEAD rows and the transformation lexicons (`docs/backlog.md`).

**49. Review and publish the FAQ, then look at Help (2026-10-05).** The 66 seed entries (`faq/`, 12 categories) are imported into the app as **drafts**. None is published, so the support agent does not answer from them yet: only you decide what the help says.
1. Start `serve --lan` (it is not running now). It loads the current code.
2. Read each draft in Help > FAQ review, edit it where needed, and Publish (or Discard). A published entry answers people at once and is embedded for vector search.
3. Optionally, look at Help yourself: a member's question with a screenshot, No, a reply from Help > Queue (try Private once), Resolve.

Recommendation: publish the accounts, telegram and troubleshooting entries first; they answer the commonest questions. Unblocks: a support agent that answers from reviewed help; the word "verified" for Help.

## B. Calibration inputs only you can supply

**12. Write the pool search queries file.** `docs/inputs/search_queries.md`: about 30 queries "{topic} doing {action}" (English, Arabic, Arabizi) with the sticker ids you consider right, plus at least 5 that must return nothing; `python -m mirsal pool search "..."` is then measured against it. Recommendation: write it from real searches you would do. Unblocks: precision@5 >= 0.8 and the Arabic / Arabizi query parser (`docs/backlog.md`, store and search).

**13. Confirm the softness threshold.** `python -m mirsal measure-sharpness` flags the 8 G002 animations (0.65 of their still's edge detail, about 1.3 px of blur) and none of the other 23; are those the soft ones, or which batch should it have flagged? Threshold `min_detail_vs_still` 0.75 (`engine/config.py`). Recommendation: check G002 by eye once. Unblocks: calling the threshold final.

**14. Judge the photo cutout edges.** `mirsal/out/photo/photo-upload.png` and 10+ real photos in `inputs/photos/` (git-ignored; include a few iPhone Portrait HEIC, which are not read yet). Recommendation: supply the photos. Unblocks: the HEIC input and the matte upgrade (BiRefNet, SAM 2) in `docs/backlog.md`.

**15. Compare the prompt text and give the resolver examples.** `python -m mirsal prompt lab` and `prompt lab --ai` (20 inputs, the AI on the local model) against `docs/inputs/prompt_samples.md`; and supply `docs/inputs/resolver_utterances.md` (the 40-utterance resolver eval, >= 95% exact ids) and your transformation examples (the detector was written from the one example "dog as banana"). Recommendation: send 40 real sentences, including Arabic and short ones. Unblocks: the resolver eval and the transformation lexicons.

## C. Product decisions in the Studio and the chat

**16. Does Enter in the Studio's prompt box open the Generate prompt step, or still start a paid sheet at once?** Today Enter spends at once with no price on screen (the old Generate button's credit chip is gone). Recommendation: Enter opens the free prompt step like the button; the paid click is the separate *Generate sheet*, which shows the price on its own line (rule 13). Unblocks: closing the price-visibility gap of the Generate prompt step (`docs/engine-and-studio.md`).

**18. OpenAI calls without a plan card.** The plan expander (`generation/expander.py`), the intent model (`agent/brain.py`) and pool embeddings (`services/embed.py`) call OpenAI when it is the provider, with no price and no go-ahead, which contradicts rule 13 as written. Recommendation: fold their cost into the plan card's estimate (or scope rule 13 to Higgsfield credits and add a monthly OpenAI budget); local models are free and unaffected. The Studio's AI enhancer now shows the engine and model next to the chip (Local free, Cloud one small OpenAI call) and the step says which one wrote the prompt, so the cloud call is visible; what stays open is whether it should also carry a price or a budget. Unblocks: the hosted-chat question (item 44) and any public user.

**19. A non-live Studio has no button for the prepared-sheet create path.** With Higgsfield not connected, the prepared-sheet path is reachable only by Enter and the suggestion chips. Add a visible button, or is that fine? Recommendation: add a labelled button (rule 6: a path that exists must be reachable by a control). Unblocks: a Studio that works without Higgsfield and an end to the Enter ambiguity in item 16.

**20. Studio menu point 3: which screen did you mean?** You asked that the settings block "must be the composer's"; it was NOT built because the Studio screen already mounts the composer's chips (`composerMount` removes the old *White outline* pills), so no lookalike exists on it. Was it the particle wizard? Recommendation: name the screen and Claude fixes that one. Unblocks: closing the Studio-menu item.

**21. `DEFAULT_SPRITE_PX` (`flow/effects.py`, now 100): change to 200?** Measured: a smaller sprite gives no latency gain (the engine already shrinks sprites) and 100 changes the 512 final by 9/255. Recommendation: 200 for render, keep 100 for preview. Unblocks: closing the particle-render default.

**22. An empty "New chat" is created when a setting is clicked with no chat open.** Intended (the setting needs a home), or should the setting wait until a chat exists? Recommendation: create the chat only on the first message and keep the setting in the bar meanwhile. Unblocks: the chat-list hygiene fix.

**23. Chat gaps the browser look left open: what should happen?** (a) A chat edit of an animated sticker opens Prepare (the still editor), not the animated editor; (b) "undo" has no "redo"; (c) a bare "the last one" / "wear a hat" with no person and no focus still plans a NEW batch. Recommendation: (a) open the animated editor, (b) add "redo" as the inverse of one undo, (c) ask "which one?" when a batch is open, otherwise plan. Unblocks: the three open lines in `docs/backlog.md` (agent and chat).

## D. Particle verdicts (nothing is built on a guess)

**25. Per-emoji motion or shared motion?** Sets belong to stickers, and ordinary animated-sticker delivery is settled. Should a pack use shared burst motion or different motion for each emoji? Recommendation: retain shared motion and presets until this is requested. Unblocks: an optional per-emoji motion design; it does not block the current simulator or Add to pack.

**27. Go for burst creation (P14), and its four questions.** Many packs from one liked sheet (`docs/burst_plan.md`): is the go given, and (1) is 6 lanes per burst the right cap (a setting?), (2) does each lane become its own pack automatically or a batch the person adds to a pack, (3) may the suggestions use the vision model on the sheet (with the one-time AI vision yes), (4) is `B###/Q###` acceptable as the lane id? Recommendation: build when explicitly authorized; answers 6, a batch (adding stays your click), yes with the one-time yes, yes. Unblocks: the whole burst-creation build.


## E. Repo, safety and housekeeping decisions (held questions: do not re-raise unless asked)

**29. Is `mirsal/out/` in git on purpose?** It is tracked (about 900 files: the real generations G001-G0xx, `library/`, `jobs/`, `export/`, `sessions/`, `model_calls.jsonl`, and 188 files of the animation `cache/`) because of the "uploading media" commits, and the docs say so. Recommendation: if not, ignore `mirsal/out/`, `git rm -r --cached` it (history keeps the old blobs unless rewritten) and write the backup command of item 30; `cache/` and `sessions/` are the obvious first candidates either way. Unblocks: a clean `git status` after every run, and the public-repo scrub (item 45).

**30. A backup command for `out/`.** Should the app get `python -m mirsal backup` (zip of `out/` minus the cache)? Recommendation: yes, small and free. Unblocks: item 29.

**31. Content safety.** One batch returned a stereotyped, offensive depiction nobody asked for ("superman in dubai"); the vision judge scores quality only and the provider's filter did not catch it. Options: safety reasons in the judge (`OFFENSIVE_CONTENT`, `STEREOTYPE`, a changed judge prompt), a separate moderation call before / after generation, or showing the provider's flag. Recommendation: the provider flag shown first (free); any added judge reasons need an agent-prepared evaluation. Unblocks: the moderation policy any public API needs.

**32. Arabic prompts.** How should Arabic / Arabizi requests be handled (detection, planner, tags)? Recommendation: detect and pass through the local model, with your examples (item 15) as the test set. Unblocks: the Arabic edit commands and Arabic query parser in `docs/backlog.md`.

**33. Keep or delete the parked React gateway `mirsal/web/` (not served).** Recommendation: delete it, git keeps it; ask first (`docs/dev-notes.md`, "Ask first"). Unblocks: a smaller tree and an unambiguous front end.

**34. Delete the retired History screen (`console/history.js`, `#/history`)?** Nothing in the rail opens it and it once shadowed the Earlier-batches handler. Recommendation: delete it. Unblocks: removing the duplicate `ACT` risk.

**35. Why `415` for a wrong `Content-Type` is not built, and whether to.** `curl -d` without a header would start failing. Recommendation: keep it unbuilt (the contract must not change by a byte). Unblocks: closing the item.

**36. The daily credit cap must never block the owner.** Decided in principle; the code cannot: `generation/jobs.py` `fulfil()` takes no user argument and `_daily_cap()` is a global env var. Observed 2026-10-02: J030 refused with `the daily credit cap (15) would be exceeded by this 2-credit call`; `mirsal/.env` here has `MIRSAL_DAILY_CREDITS=` empty (= no cap). Recommendation: build the exemption (pass the user through) before you set a cap or add a member who can spend. Unblocks: a cap that protects members without ever refusing you.

**37. Per-chat model pick (web chat).** A Telegram chat already has its own models (`/model`, `settings.models`, 2026-10-09). The model pick is process-wide (`POST /api/ai/backend {model}`, `out/ai_backend.json`). Do you want a per-chat model? Recommendation: no, keep it process-wide. Unblocks: closing the item.

**39. Do you want the 3D text templates and the 3D parallax photos built at all?** Both are unstarted (`docs/backlog.md`, store and search 3D / 3E): CapCut-style flashing text-slot stickers with 30+ procedural starters, and photo depth with a gyroscope WebGL viewer. Recommendation: no for now; both are large and neither is on the golden path. Unblocks: deleting or scheduling two large backlog items.

**49. Rotate the AddCollection credential, then try two things for real.** The credential pasted in `docs/Api/AddCollection-API .md` is in git
history (commit dd17f61, pushed): change that password and keep the new one only in `mirsal/.env` (`MIRSAL_COLLECTION_API_CREDENTIALS`). Then, with
`serve --lan` restarted: one Export to collection of a small pack, and the Telegram chat (`/start`, `/model`, a request: real stickers, the album, a
creator run's edited message). Recommendation: both now, they cost nothing but a pack's credits. Unblocks: the backlog's Telegram chat and export items.

**50. The paid proof of the face preset** (about 2 credits + one pack): see the backlog, Live generation. Recommendation: yes, once. Unblocks: the v4
face clause.

## F. Parked: the deployment questions (`docs/deployment_plan.md` section 17; do not raise unless asked)

An answer goes into `docs/deployment_plan.md` and deletes the question here.

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
