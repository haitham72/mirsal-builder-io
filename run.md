# Run Mirsal

Both platforms use `mirsal/.venv`, created locally on each machine. Virtual environments are not committed or shared between Windows and macOS. Use the environment's Python directly; activation is optional.

## macOS (Terminal / zsh)

### New Mac (once)

Install Python 3 and Docker Desktop, then start Docker Desktop. From a fresh checkout:

```bash
git clone https://github.com/haitham72/mirsal-builder-io.git
cd mirsal-builder-io/mirsal
python3 -m venv .venv
source ./.venv/bin/activate
./.venv/bin/python -m pip install -r requirements.txt
cp -n .env.example .env
```

For an existing checkout, start in its `mirsal/` directory and run from `python3 -m venv .venv` onward. If `.venv` is missing, this creates it. `cp -n` preserves an existing `.env`.

Fill your keys into `mirsal/.env`, then:

```bash
./.venv/bin/python -m mirsal db up
./.venv/bin/python -m mirsal doctor
```

### Start the server on this Mac

Run these commands from the project's `mirsal/` directory (the folder containing `requirements.txt` and `.venv`). If you are at the repository root, run `cd mirsal` first. If your prompt already ends in `mirsal`, stay there.

With Docker Desktop running:

```bash
./.venv/bin/python -m mirsal db up
./.venv/bin/python -m mirsal serve
```

Open <http://127.0.0.1:8770>. This serves only this Mac and needs no certificate.

**While editing the code**, add `--reload` (works with or without `--lan`): `./.venv/bin/python -m mirsal serve --reload` or `serve --lan --reload`. The server restarts by itself whenever a `.py` file under `mirsal/mirsal/` is saved; the screens' files (`.js`, `.css`) need only a browser reload (Cmd+Shift+R), never a restart. A restart stops whatever the server was doing at that moment, so do not save Python files while a sheet or video is being made. On Windows the same flag: `.\.venv\Scripts\python.exe -m mirsal serve --lan --reload`.

### Serve colleagues on the LAN: HTTPS setup (once)

`serve --lan` requires `out/tls/cert.pem` and `out/tls/key.pem`. If Terminal says `command not found: mkcert`, install it first. With Homebrew installed:

```bash
brew install mkcert
mkcert -install
```

Find your current Wi-Fi IPv4 address in System Settings → Wi-Fi → Details → TCP/IP. From the same `mirsal/` directory, set `LAN_IP` to that address (replace the example address below):

```bash
LAN_IP=192.168.41.242
mkdir -p out/tls
mkcert -cert-file out/tls/cert.pem -key-file out/tls/key.pem "$LAN_IP" localhost 127.0.0.1
```

The paths are `out/tls`, because you are already inside `mirsal/`.

Use `mkcert -CAROOT` to locate `rootCA.pem`; install that certificate on each colleague's computer as a trusted root (Keychain Access on macOS, Local Machine → Trusted Root Certification Authorities on Windows). Never copy `rootCA-key.pem`.

### Start the LAN server each day

With Docker Desktop running, from `mirsal/`:

```bash
./.venv/bin/python -m mirsal db up
./.venv/bin/python -m mirsal serve --lan
```

You: <https://localhost:8770>. Colleagues on the same network: `https://YOUR_WIFI_IP:8770` (replace `YOUR_WIFI_IP` with the address used for the certificate).

If the Wi-Fi address changes, rerun the certificate commands with the new `LAN_IP`, then restart the server. Stop with **Control+C** (on a Mac it is Control, not Command; the server ends within about 3 seconds and prints `Stopped.`). After a pull, restart and reload the browser.

## Windows (PowerShell)

From the repository root, use `.\.venv\Scripts\python.exe` once inside `mirsal/`.

### New PC (once)

```powershell
git clone https://github.com/haitham72/mirsal-builder-io.git
cd mirsal-builder-io\mirsal
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe -m mirsal db up
.\.venv\Scripts\python.exe -m mirsal doctor
```

Fill your keys into `mirsal\.env`. Docker Desktop must be running for `db up`.

### HTTPS for colleagues (once)

Administrator shell:

```powershell
choco install mkcert
mkcert -install
```

Normal shell, repository root (`ipconfig` → Wi-Fi IPv4; it was `192.168.41.242`):

```powershell
mkdir mirsal\out\tls -Force
mkcert -cert-file mirsal/out/tls/cert.pem -key-file mirsal/out/tls/key.pem 192.168.41.242 localhost 127.0.0.1
```

Each colleague's PC: install `C:\Users\h.ibrahim\AppData\Local\mkcert\rootCA.pem` → Local Machine → Trusted Root Certification Authorities. Never copy `rootCA-key.pem`.

### Every day

#### Windows (PowerShell)
```powershell
cd mirsal
.\.venv\Scripts\python.exe -m mirsal db up
.\.venv\Scripts\python.exe -m mirsal serve --lan
```
#### Mac (Terminal / zsh)

```bash
cd mirsal
./.venv/bin/python -m mirsal db up
./.venv/bin/python -m mirsal serve --lan
```

- You: <https://localhost:8770>
- Colleagues: <https://192.168.41.242:8770>
- Only you, no LAN: `serve` instead of `serve --lan` → <http://127.0.0.1:8770>
- Wi-Fi address changed: rerun the `mkcert -cert-file` line, restart.
- Stop: **Control+C** in the terminal (Ctrl+C on Windows; on a Mac it is Control, not Command). It ends within about 3 seconds and prints `Stopped.`. After a pull: restart, then Ctrl+F5 (Cmd+Shift+R on a Mac) in the browser.

## Settings (`mirsal/.env`, both platforms; restart after)

```text
MIRSAL_EMAIL_DOMAIN=nadi.ae,cpd.gov.ae
```

Allowed sign-up domains (the full list). Empty = any domain.

## Database

```sh
docker exec -it mirsal-db psql -U mirsal mirsal
```

```sql
select user_message, assistant_message from interactions order by created_at desc limit 20;
```

`\q` to leave. VS Code PostgreSQL extension, Connection String:

```text
postgresql://mirsal:PASSWORD@localhost:5434/mirsal
```

`PASSWORD`: from `MIRSAL_DATABASE_URL` in `mirsal/.env` (default `mirsal_local`).

Never delete the `mirsal-db` container: its data is in the volume `mirsal_pgdata`. More: [certificate-guide.md](certificate-guide.md), `docs/dev-notes.md`.
