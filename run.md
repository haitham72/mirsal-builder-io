# Run Mirsal

Windows, PowerShell. Every command runs from the **repository root** unless it says `cd mirsal` first. Always call `.\.venv\Scripts\python.exe -m ...` (with `.exe`): bare `python`/`pip` in this shell can resolve to another interpreter and poison the venv. (macOS: the venv is `mirsal/venv`, the commands are `venv/bin/python -m ...`.)

## New PC (once, in this order)

### 1. Get the code and the venv

```powershell
git clone https://github.com/haitham72/mirsal-builder-io.git
cd mirsal-builder-io\mirsal
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. The settings file

Copy `mirsal\.env.example` to `mirsal\.env` (git-ignored, it never goes to git) and fill in what you use. The defaults work for the database and Redis. Bring any keys over from the old PC by hand.

### 3. Postgres and Redis

Start Docker Desktop, then:

```powershell
.\.venv\Scripts\python.exe -m mirsal db up
```

It starts `mirsal-db` (port 5434) and `mirsal-redis` (port 6380), creating them the first time, and prepares the tables. The app also works without them. If `mirsal-db` already exists, never delete it to "fix" anything: its data is in the volume `mirsal_pgdata`.

### 4. Check everything

```powershell
.\.venv\Scripts\python.exe -m mirsal doctor
```

### 5. Only if colleagues will use it: the HTTPS certificate

`serve --lan` refuses to start without `mirsal/out/tls/cert.pem` and `key.pem`.

1. Install mkcert, in an **administrator** shell: `choco install mkcert` or `winget install -e --id FiloSottile.mkcert` (skip if `mkcert -help` already works).
2. Trust the local authority on this PC (Windows asks you to confirm, click Yes):

   ```powershell
   mkcert -install
   ```

3. Find this PC's address: `ipconfig`, the Wi-Fi "IPv4 Address" (ignore the `vEthernet` ones). On 2026-10-05 it was `192.168.41.242`.
4. Make the certificate, from the repository root, with that address:

   ```powershell
   mkdir mirsal\out\tls -Force
   mkcert -cert-file mirsal/out/tls/cert.pem -key-file mirsal/out/tls/key.pem 192.168.41.242 localhost 127.0.0.1
   ```

5. On each colleague's machine (once): copy `rootCA.pem` from the folder `mkcert -CAROOT` prints (here `C:\Users\h.ibrahim\AppData\Local\mkcert`). Double-click it, choose Install Certificate, then Local Machine, then **Trusted Root Certification Authorities**. Never copy `rootCA-key.pem`.

Details: [certificate-guide.md](certificate-guide.md).

## Every day

### 1. Start Docker Desktop

Then `.\.venv\Scripts\python.exe -m mirsal db up` (from `mirsal`; quick when they are already up).

### 2. Start Mirsal

One of the two:

| who uses it        | command (from `mirsal`)                            | open                                                                                                 |
| ------------------ | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| only you           | `.\.venv\Scripts\python.exe -m mirsal serve`       | <http://127.0.0.1:8770>                                                                              |
| you and colleagues | `.\.venv\Scripts\python.exe -m mirsal serve --lan` | you: <https://localhost:8770>; colleagues: the address it prints, e.g. <https://192.168.41.242:8770> |

You are the owner on this PC: no sign-in. Leave the window open; Ctrl+C in it stops the server. After pulling new code, restart it and hard-refresh the browser (Ctrl+F5).

**With colleagues:** they sign up with their `@nadi.ae` or `@cpd.gov.ae` email and wait for your approval in **Users > People** (or the Telegram card). This PC must stay on while they work. When you add someone yourself, send them the password shown once: at their first sign-in they choose their own, or keep the given one for now.

**If the Wi-Fi address changed** (the start-up line shows a new one): repeat step 5.4 of "New PC" with the new address and restart. Colleagues' machines keep working. Without a certificate, `serve --lan --no-tls` runs plain HTTP (passwords cross the network unencrypted).

## Settings you may change

**Allowed email domains.** `@nadi.ae` and `@cpd.gov.ae` can sign up out of the box. To change the list, put one line in `mirsal/.env` (the full list, comma-separated) and restart `serve --lan`:

```text
MIRSAL_EMAIL_DOMAIN=nadi.ae,cpd.gov.ae,dubai.gov.ae
```

The line replaces the default, so keep the domains you still want in it. An empty value (`MIRSAL_EMAIL_DOMAIN=`) lets any email sign up; everyone still waits for your approval. Accounts made earlier keep working whatever the list says.

| what                         | how                                                                                                                          |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Telegram approvals           | Settings > Telegram: bot token + your user id; with `--lan` the bot sends you a card per sign-up, credit or password request |
| another port                 | `serve --port 8789`                                                                                                          |
| the old server (one release) | `serve --stdlib`                                                                                                             |
| tests                        | `docs/testing.md` (the test budget: one narrow run per change)                                                               |

Everything the app writes goes to `mirsal/out/`. Prepared sheets (optional) go in `inputs/Images_gen/img-NNN-<subject>/` and `inputs/videos_gen/vid-NNN-<subject>/` (folder names are final).

## Look inside the database

**In VS Code** (Microsoft PostgreSQL extension). The main page has no port box, so use the **Connection String** tab:

```text
postgresql://mirsal:PASSWORD@localhost:5434/mirsal
```

Replace `PASSWORD` with the part between `mirsal:` and `@localhost` in the `MIRSAL_DATABASE_URL=` line of `mirsal/.env` (`mirsal_local` if you never set one). Or use **Parameters**:

| field               | value                                                 |
| ------------------- | ----------------------------------------------------- |
| Server name         | `localhost`                                           |
| Authentication Type | Password                                              |
| User name           | `mirsal`                                              |
| Password            | from `mirsal/.env`, as above                          |
| Database name       | `mirsal`                                              |
| Connection Name     | `Mirsal` (anything you like)                          |
| **Advanced → Port** | **`5434`** (it defaults to 5432, which won't connect) |

Click **Test Connection**, then **Save & Connect**. Expand **Mirsal → Databases → mirsal → Schemas → public → Tables**. Right-click **interactions** and choose "Select Top 1000" to see every chat turn; **sessions** lists the chats.

**From the terminal**, a SQL prompt inside the container:

```powershell
docker exec -it mirsal-db psql -U mirsal mirsal
```

```sql
select user_message, assistant_message from interactions order by created_at desc limit 20;
```

Type `\q` to leave.

If neither connects: Docker Desktop must be running and `docker ps` must list `mirsal-db` with `0.0.0.0:5434->5432`; if not, run `db up`.
