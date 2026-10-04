# Run Mirsal

## Once (setup)

macOS:

```
cd mirsal
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env            # keys and options
```

Windows: `python -m venv .venv`, then `.venv\Scripts\pip install -r requirements.txt`, and use `.venv\Scripts\python` instead of `venv/bin/python` below. Always use this venv (the Anaconda base env has a broken numpy).

## Every day: just you

Stop any server already running (Ctrl+C in its window), then:

```
cd mirsal
venv/bin/python -m mirsal serve
```

Open **http://127.0.0.1:8770**. You are the owner; there is no sign-in on this PC.

## With office colleagues

Make the HTTPS certificate once: [certificate-guide.md](certificate-guide.md). Then:

```
venv/bin/python -m mirsal serve --lan
```

It prints the address to share (for example `https://192.168.1.66:8770`). Colleagues sign up with their `@nadi.ae` email and wait for your approval in **Settings > People** or in Telegram. This PC must stay on while they work.

To try it without a certificate: `serve --lan --no-tls` (plain HTTP; it warns).

## Optional

| what | command |
|---|---|
| Postgres + Redis (Docker Desktop running) | `venv/bin/python -m mirsal db up` (the app works without them) |
| health check | `venv/bin/python -m mirsal doctor` |
| Telegram approvals | Settings > Telegram: bot token + your user id; with `--lan` the bot sends you a card per sign-up, credit or password request |
| another port | `serve --port 8789` |
| the old server (one release) | `serve --stdlib` |
| tests | `docs/testing.md` (the test budget: one narrow run per change) |

Everything the app writes goes to `mirsal/out/`. Prepared sheets (optional) go in `inputs/Images_gen/img-NNN-<subject>/` and `inputs/videos_gen/vid-NNN-<subject>/` (folder names are final).

The docs are updated, committed and pushed as `ea42b10`. A new session can now pick up without re-deriving anything:

| What the session reads | What it now finds |
|---|---|
| `CLAUDE.md` → `HANDOFF.md` | the rules and routing table; HANDOFF is an empty save point ("nothing in progress, v1.0 tagged") |
| `run.md`, `certificate-guide.md` | how to run it, alone or for the office, and the HTTPS set-up |
| `docs/engine-and-studio.md` (Layout) | a file map that includes the new server, the new modules and the new `out/` files (git-ignored ones marked), and states that pydantic is used only in the web layer, never the engine |
| `docs/api.md` | the contract for every route, including the new ones: chat stream, office accounts, credits, Trending, tickets |
| `docs/dev-notes.md` (session prompt) | "Built, do not redo" now lists everything up to v1.0, so nothing gets rebuilt |
| `docs/backlog.md` | what's still open, including this round's honest gaps: |
| | • members have no Library of their own yet |
| | • the admin role is still undecided |
| | • the Telegram bot has only been tested against a fake Telegram, not your real bot |
| | • ticket drafts work only with the local model running |
| | • the chat stream sends only the last message |
| | • the golden tests were flaky once under heavy load |
| `docs/testing.md` | the test budget, plus a table of which test file guards each v1.0 feature |
| `docs/waiting-for-haitham.md` | only the decisions that need you |

The code is commented as it was written. Each new module (`console/app.py`, `flow/tickets.py`, `flow/trending.py`, `flow/people.py`, `services/admin_bot.py`, `runtime/net.py`) opens with a description of what it does and why.

Everything is pushed on `better_ui/ux`, tagged `v1.0`. The only uncommitted folder is `docs/diagrams/`, which is waiting for the other LLM's update.