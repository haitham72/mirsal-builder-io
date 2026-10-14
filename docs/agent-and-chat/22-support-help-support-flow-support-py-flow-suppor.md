# Support (Help & Support; `flow/support.py`, `flow/support_kb.py`, `flow/faq.py`, `flow/notifications.py`, `console/support.js`; 2026-10-05)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

Help is where a person describes a problem in their own words. The support agent answers from what is documented, and a person takes over when that is not enough. It is a deterministic loop around ONE model call. It is not LangGraph: every step can be tested with fakes.

1. **The turn.** The person writes, and may attach or paste (Ctrl+V) a screenshot. A screenshot is validated (PNG, JPEG or WebP under 8 MB), re-encoded as PNG at 1600 px at most, and stored in `out/support/C###/img-N.png`. It is read by the **local** vision model (`VISION_MODEL`, else the local chat model; `VISION_BASE_URL` optional; the person's own upload is the consent). Every call is logged as `SUPPORT_SEE` in `model_calls.jsonl`. What it saw is kept on the message for staff only.
2. **Retrieval** (`support_kb.search`):
   - Everyone gets **published** FAQ entries first, then the repo's `docs/`. The trackers, plans and developer notes (`INTERNAL_DOCS`, `*_plan.md`: kind `note`) answer the owner and admins only.
   - The owner and admins also get **code**, but only when the best FAQ/doc/note hit is under `ENOUGH` (vector 0.70, lexical 0.45; nomic scores loosely related sections 0.6-0.7, measured on this repo's index).
   - The repo is `MIRSAL_SUPPORT_REPO` in `mirsal/.env` (the repository root, or its inner `mirsal/`). When it is unset, only the FAQ is searched.
   - `mirsal support reindex` (or POST `/api/support/reindex`) cuts `docs/**/*.md` into heading sections and `mirsal/mirsal/**`, `migrations/` into blocks. Secrets are scrubbed (`obs/scrub.scrub_secrets`). `.env`, `opencode.json`, `telegram-id.md`, `out/`, `docs/inputs/`, virtual envs and dot-folders are never read.
   - The record is `out/support/index.json`, with a sha256 per file, so an unchanged file is never cut or embedded again.
   - With Postgres and the **local** nomic model up, the vectors go to `support_chunks` and `faq.vec` (migration 011). Otherwise the search is lexical (idf-weighted word overlap) over the same files. There is no hosted embedding fallback, so nothing is paid.
   - An FAQ entry is found by its question, its answer, its `screen` and its `looks_like` (what the problem looks like on screen; `faq.search_text`), so the vision model's description of a screenshot finds the entry.
3. **The answer.** The **local** model (`MIRSAL_SUPPORT_MODEL`, else the local chat model), always local whatever the person picked (rule 13), receives the numbered sources, this person's **memory**, the screenshot's description and the last turns, all fenced as data. It answers JSON `{reply, cites, need}`.
   - A reply is shown only when its cites point to what was retrieved. A cite to anything else, or a solution with no cite, becomes "I could not find this documented" plus Send to support. It never invents a fix.
   - `need: clarify` (one short question) and `need: screenshot` need no cite.
   - A small model that ignores the JSON format and writes plain text ending in `[1] [2]` is read as that text with those cites (`support._parse`).
   - With the model down, the best FAQ entry is quoted word for word, but only when it is a real match. Doc sections are written for developers and are never quoted raw. Otherwise support is offered.
4. **Memory** (`support.memory`): the person's earlier conversations (title, how each ended, what was read) and the tickets the system holds for them, failures caught on their requests included. Only this person's, newest first, at most ten lines.
5. **"Did this solve it?"** Yes closes the conversation. No, or **Send to support**, escalates **once**:
   - One ticket per conversation (`tickets.open_support`, source `support`): the person's words, the transcript, what the vision model saw, what was tried, their earlier problems. It has no multiple-choice questions.
   - One Telegram ping to the admin with a link (`admin_bot.notify_support`). The link is `MIRSAL_APP_URL`, else this machine's LAN address, then `/#/help/C###`.
   - The ticket keeps `pinged[<event>:T###] = {ok, at, tries}`. A refused ping never loses the ticket: the admin bot's loop runs `support.retry_pings` every five minutes, up to six tries. A ping that was sent is never sent again.
6. **The admin** (Help > Queue): Reply versus Reply and resolve.
   - **Reply** (`support.admin_reply`) adds a thread line (a retried request with the same `client_id` adds nothing) and sets the ticket to `replied`, the conversation to `admin_replied`, plus one notification `reply:T###:n`. It never closes anything.
   - **Resolve** closes both and notifies once per resolution (`resolved:T###:<reopenings>`). It then proposes an FAQ entry in the background (`faq.propose_from_ticket`, below).
   - The person can write back: the ticket goes to `open` and the conversation to `awaiting_admin`. They can also **Reopen** a resolved issue, which opens the ticket and sends one more ping, `reopenN`.
7. **Notifications** (`out/notifications/<user>.json`, mirrored): one per event key, so retries never notify twice. The rail's Help item shows a red dot while one is unread (read every 30 s). Opening the conversation marks its notifications read.
8. **The FAQ** (`out/faq/F###.json`, mirrored with the vector of its published text):
   - Statuses are `draft` (never an answer), `published` or `archived`.
   - A proposal for a published entry waits as `pending`. Publishing it keeps the replaced text in `revisions`, and `provenance` lists the tickets and seed files an entry came from.
   - `propose_from_ticket` first searches the published entries, so a known question becomes a revision, not a twin (`DUPLICATE`: vector 0.80, lexical 0.60). The local model writes the reusable solution; when it is down, the admin's own resolution words are used. Everything kept is scrubbed (`obs/scrub.scrub_personal`: e-mails, record ids, uuids, paths, secrets, the people's names).
   - Admins review in Help > FAQ review: the published text beside the proposal, edit, publish, discard, archive.
   - **Seed entries** are Markdown files: `faq/<category>/<slug>.md`, with a `---` header holding `title`, `question`, `category`, `tags`, `screen` and `looks_like`, and the answer as the body. `mirsal support import-faq --repo <folder>` makes each one a draft. Unchanged files are skipped; a changed file updates its draft, or proposes a revision of its published entry. `--publish` publishes them at once, but only on purpose. The 87 seeds were written by a second model from a prompt now in git history; its handoff with every entry's sources is `mirsal/local_eval/faq-handoff.md`.

**The real cases (Haitham, 2026-10-05).**
- **Your activity as sources** (`support.activity`): the person's own newest jobs (and any of theirs named in the text, like J058 or G104) and batches are numbered sources beside the FAQ and docs, marked `(activity)`. Another person's ids are ignored.
  - A job is described as: kind, model, how long ago, "still being made at Higgsfield" / finished / failed (the error) / timed out (still checkable for free), its Higgsfield task id, its batch, and "usually takes about N minutes" (the median of the last 20 finished jobs of that kind, by model when there are 3 or more: `typical_minutes`).
  - A batch is described as: how many stickers were accepted, each blocked one with its reason, and that a judgement block has its own "Use it anyway" on the tile.
- **Action buttons** come from what an answer cited, never from the model's words (`support._actions`): "Open G104 in the Studio".
- **Watches**: an answer that cites a running job watches it. `support.check_watches` runs whenever the person's notifications are read (every 30 s) or a conversation opens, so no background thread is needed. It then:
  - says once that the job finished ("it is in batch G104", with the button) or did not (with Send to support);
  - notifies `update:C###:J###`;
  - resolves the conversation when the job simply arrived.
- **Request kinds**: the model may set `request: feature` (the app cannot do it yet) or `access` (only an admin can give it: a token, a password, credits).
  - The person then gets **Request this feature** or **Ask the admin** instead of Send to support. A grounded answer also offers "Suggest a feature instead".
  - `escalate(kind)` files the ticket with issue `feature` / `access` (`flow/ticket_models.ISSUES`), its own message to the person, its own ping text ("asks for a feature") and a chip in the Queue.
- **Private replies** (`admin_reply(private=True)`; the Queue's "Private" checkbox): a token or a password lives only in the person's conversation file.
  - The ticket thread, the Postgres copy (`support._redacted`), the notification ("Support sent you a private message"), the ping, every model's input and the FAQ proposal get `[a private message]`. Staff see that it was sent, not what.
  - The person sees it masked, with Reveal, Copy and "I saved it, forget it", which erases the text from the record (`support.forget`).

**Privacy and trust.** A person sees only their own conversations, notifications and tickets; anything else is a 404. A member's ticket view drops the internal fields. Staff see a conversation once it reached a ticket. Nothing a person writes, nothing retrieved and nothing the vision model says can authorize an action: the routes check roles (`docs/api.md` "Help & Support"). The stdlib server (`serve --stdlib`) has no Help routes.

**Measured so far.** The local vision pre-review on stickers (`mirsal/local_eval/`: Qwen 3.5 9B, 30 stickers, 25 parsed verdicts, about 10 s each). One live check of support on a scratch copy (2026-10-05):
- The index is 172 files: 305 doc, 193 staff-note and 1,273 code sections, all embedded by the local nomic model, with searches at 2-3 s.
- `qwen3.5-4b` ignored the JSON format (hence `_parse`) and gave one wrong cause for the grey loop frame.
- `qwen/qwen3.5-9b` answered "make a pack public" correctly in 10.5 s, read a screenshot of the welcome slide and matched it to the welcome modal in 27.7 s, but answered the loop seam from the verifier section instead of the reloop fix.

Developer docs alone answer poorly, so the FAQ seeds matter.

**The seed FAQ (2026-10-05).** 66 entries in 12 categories (`faq/`; 45 with `screen` / `looks_like`), written and source-checked by a second model from `docs/` and the code. Its handoff, with every entry's sources, is `mirsal/local_eval/faq-handoff.md`; the 30 cases are `mirsal/local_eval/faq/questions.json` (ten direct questions, ten screenshot descriptions, ten paraphrases from the local 9B).
- Import is idempotent: 66 created, then 66 unchanged.
- A draft never answers.
- On a temp copy with the entries published (FAQ only, Postgres off):
  - **lexical**: the right entry first 30/30, confident 27/30;
  - **semantic** (the local nomic embedder, cosine in-process, no database): right first and confident 30/30, lowest correct score 0.781.
- Ten unrelated questions: none confident lexically, but 2/10 confident in vector mode (TikTok 0.825, t-shirt printing 0.768). Those are on-topic questions the help does not answer (`mirsal/local_eval/faq/semantic-check.json`; open items in `docs/backlog.md`).
- All 87 seeds are in the real app as drafts, waiting for review (`docs/waiting-for-haitham.md` 49).
- **End to end (2026-10-05)**: the FAQ agent's 26 case chains (62 turns, `mirsal/local_eval/faq/cases.json`, synthetic jobs and batches) were run against `support.ask` with `qwen/qwen3.5-9b`, FAQ vectors in-process and the real doc index read-only (no database write). The first run passed 53/62 by the automatic check. Read reply by reply, 5 of the 9 failures were correct grounded "no" answers (TikTok, WhatsApp, another person's job: nothing leaked) and 4 were real misses. Two instruction rules fixed those four: a visible problem with no source asks for a screenshot; a request the admin must fulfil (a password, a token, access) gets `request: access`. After that, every failing chain behaved correctly on re-run. Median answer time 9-17 s.
