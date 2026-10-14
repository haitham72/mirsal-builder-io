# Layout

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

```
inputs/                                   Haitham's hand-edited watch folders (the app only READS; never renames); formerly Phase_01/
  Images_gen/img-NNN-<subject>/<sheet>.jpg        one folder per variant; NNN = variant folder number
  videos_gen/vid-NNN-<subject>/<video>.mp4        the 3x3 video of the same NNN
  videos_gen/vid-NNN-<subject>/slices/{quicktime,webm}/<any name> (n).<ext>   pre-sliced transparent clips, n = grid cell 1..9
tools/tracker/tracker.py                  optional generation tracker (filenames only)
mirsal/                                   the app
  requirements.txt  docker-compose.yml  .env.example  migrations/*.sql  tests/  out/ (what git tracks of it: below)  web/ (a parked React gateway, not served)
  mirsal/                                 the Python package: cli.py and one folder per concern
    engine/         PURE: numpy / OpenCV / Pillow / ffmpeg only (config, chroma, grid, render, sheet, video, ffmpeg, verify, video_sheet)
    flow/           the golden path: pipeline.py (the lifecycle, events, result.json + reviews, history, video_sheets), gates.py (the review gates G1-G5, the video sheet, the returned-video slicing),
                    groups.py (batch families: root + variations), particle_sets.py + effects.py (particle rows owned by stickers; the older E### runs), purge.py (the trash purge),
                    tickets.py + ticket_models.py (problems as tickets, pydantic draft/answers), people.py (account requests), trending.py (shared packs: likes, comments, use),
                    sources.py (the prepared-sheet scanner, never opens media), watch.py (History: the watch folders, Remove -> trash -> Restore), sticker_history.py (a sticker's decisions grouped by stage, for the Studio's folded history), measure.py
    generation/     live generation (docs/generation.md): prompter.py (task text -> slot JSON -> prompts from prompts/templates/*.txt, versioned), expander.py (subject -> the full named set by a model:
                    lint, one repair, built-in sets as fallback), emotions.py + styles.py (the emotion bank, the style presets), tasks.py (the Inbox: plan preview, task reserve, out/tasks/NNN.json),
                    higgsfield.py + model_catalog.py + jobs.py + jobqueue.py + usage.py + model_calls.py (the CLI, jobs as files and their durable queue, credits, the ledger)
    services/       the outside world: llm.py (chat-completions client for LM Studio and OpenAI, text and images), embed.py (local embeddings), telegram.py (Send to Telegram, stdlib only),
                    admin_bot.py (Haitham's Telegram admin cards and the long-poll loop; `apply()` is the one way an account is changed)
    runtime/        cache.py + events.py (Redis, disposable, and the per-generation event stream), health.py, writer_lock.py, paths.py, net.py (this PC's LAN names),
                    users.py (tokens, office accounts: scrypt passwords, sessions, roles owner/admin/member, status, credits `charge`)
    media/          library.py (packs, saved stickers, bulk move / delete), video_project.py (video / GIF projects), matte.py (optional AI cutout, onnxruntime)
    store/          Postgres: db, repo, sync (write-through), assets (AssetStore), pool.py (the sticker pool)  (docs/store-and-search.md)
    agent/          the chat: memory, resolver, brain, tools, LangGraph graph (docs/agent-and-chat.md)       vision/   the vision judge and bounded recovery       obs/scrub.py   file paths kept out of free text
    transformations/  prompts/  models/      built-in transformation templates (dog as banana) · prompt template text files · the cutout model weights
    console/        app.py (THE server: FastAPI on uvicorn; every existing route through an adapter over server.py's handler, byte-identical; native routes for the chat stream, tickets,
                    accounts/People and Trending), app_models.py (pydantic models of the native routes), server.py (Console + the original handler: guards, routes, `serve()`; `--stdlib` runs it alone),
                    openapi.py (the hand-written route list served as /api/openapi.json) + the screens: index.html, studio.css, agent.css, app.js (shell, Library, Settings), agent.js (the AI chat),
                    studio-core.js, studio-tiles.js, studio-sheet.js, studio-prompt.js, studio-animate.js, studio-panel.js, live.js, composer.js, telegram.js, packs.js, editor.js, chat.js, prepare.js, animate.js, history.js, effects.js, particles.js, trash.js, sheet-recovery.js,
                    job-recovery.js, welcome.js, tickets.js (Settings > Tickets, Report), auth.js (sign-in, Waiting for approval, the People builders), users.js (the Users section: roster, usage, People), trending.js (the Trending tab)
  out/G001/...      results        out/library/  library.json + files/<img|vid>-NNN-<pack>-<sticker>.<ext>        out/sessions/  chats        out/jobs/  out/tasks/  model_calls.jsonl
  out/particles/P###  out/effects/E###  out/trash/  out/tickets/T###.json*  out/trending.json*  out/users.json*  out/auth_sessions.json*  out/account_requests.json*  out/tls/*   (* git-ignored)
```

The engine is plain dicts, dataclasses and JSON; it never imports pydantic or FastAPI (rule 3). Pydantic lives only at the HTTP edge (`console/app_models.py`) and in the ticket shapes (`flow/ticket_models.py`).

**What git tracks of `out/`.** Haitham committed the real generations, the library, the jobs and the ledger on purpose (a private repository: they are the product's data and the backup), so `out/` is NOT git-ignored as a whole. What is ignored, and must never be committed: `out/users.json` (every account's token digest), `out/.asset_secret` (the signed-link key), `out/telegram.json`, the writer / paid lock files and `*.log` in `out/`. Whether the rest should leave git (and be backed up by a command instead) is a decision for Haitham (`docs/waiting-for-haitham.md` W29, W30).
