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
