# Run Mirsal

PowerShell, from the repository root. Always `.\.venv\Scripts\python.exe` (never bare `python`).

## New PC (once)

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

## Every day

```powershell
cd mirsal
.\.venv\Scripts\python.exe -m mirsal db up
.\.venv\Scripts\python.exe -m mirsal serve --lan
```

- You: <https://localhost:8770>
- Colleagues: <https://192.168.41.242:8770>
- Only you, no LAN: `serve` instead of `serve --lan` → <http://127.0.0.1:8770>
- Wi-Fi address changed: rerun the `mkcert -cert-file` line, restart.
- Stop: Ctrl+C. After a pull: restart, then Ctrl+F5 in the browser.

## Settings (`mirsal\.env`, restart after)

```text
MIRSAL_EMAIL_DOMAIN=nadi.ae,cpd.gov.ae
```

Allowed sign-up domains (the full list). Empty = any domain.

## Database

```powershell
docker exec -it mirsal-db psql -U mirsal mirsal
```

```sql
select user_message, assistant_message from interactions order by created_at desc limit 20;
```

`\q` to leave. VS Code PostgreSQL extension, Connection String:

```text
postgresql://mirsal:PASSWORD@localhost:5434/mirsal
```

`PASSWORD`: from `MIRSAL_DATABASE_URL` in `mirsal\.env` (default `mirsal_local`).

Never delete the `mirsal-db` container: its data is in the volume `mirsal_pgdata`. More: [certificate-guide.md](certificate-guide.md), `docs/dev-notes.md`.
