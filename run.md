# Run Mirsal

Pick what you need — nothing here depends on the section above it.

## Once: set up the venv

```powershell
cd D:\Vscode\mirsal-builder\mirsal
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m mirsal doctor
```

## Every day: run it

```powershell
cd D:\Vscode\mirsal-builder\mirsal
.\.venv\Scripts\python.exe -m mirsal serve
```

Open **http://127.0.0.1:8770**. You are the owner; there is no sign-in on this PC. Leave the window open; stop with Ctrl+C in that window (that stops only this server).

## Once: the HTTPS certificate (before `--lan`)

`serve --lan` refuses to start without `mirsal/out/tls/cert.pem` and `key.pem`. Make them once.

1. **Install mkcert** (skip if `mkcert -help` already works; on this PC it does, via Chocolatey). In an **administrator** shell: `choco install mkcert` or `winget install -e --id FiloSottile.mkcert`.
2. **Trust the local authority on this PC** (once; Windows asks you to confirm, click Yes):

   ```powershell
   mkcert -install
   ```

3. **Find this PC's address:** `ipconfig`, the Wi-Fi "IPv4 Address" (2026-10-05 it was `192.168.41.242`; ignore the `vEthernet` ones).
4. **Make the certificate** from the repository root, with that address:

   ```powershell
   mkdir mirsal\out\tls -Force
   mkcert -cert-file mirsal/out/tls/cert.pem -key-file mirsal/out/tls/key.pem 192.168.41.242 localhost 127.0.0.1
   ```

5. **Each colleague's machine (once):** copy `rootCA.pem` from the folder `mkcert -CAROOT` prints (here `C:\Users\h.ibrahim\AppData\Local\mkcert`). Double-click it, choose Install Certificate, then Local Machine, then **Trusted Root Certification Authorities**. Never copy `rootCA-key.pem`.

**If the address changes** (Wi-Fi gives a new one), repeat step 4 with the new address and restart. The colleagues' machines keep working. `mirsal/out/tls/` is git-ignored. Details: [certificate-guide.md](certificate-guide.md).

## With office colleagues

```powershell
cd D:\Vscode\mirsal-builder\mirsal
.\.venv\Scripts\python.exe -m mirsal serve --lan
```

You use **https://localhost:8770** (owner, no sign-in, no warning). Colleagues open **https://192.168.41.242:8770** (the address it prints), sign up with their `@nadi.ae` or `@cpd.gov.ae` email, and wait for your approval in **Users > People** (or the Telegram card). This PC must stay on while they work. Without a certificate: `serve --lan --no-tls` (plain HTTP; passwords cross the network unencrypted).

### Allow another email domain

`@nadi.ae` and `@cpd.gov.ae` can sign up out of the box. To change the list, add one line to `mirsal/.env` (the full list, comma-separated), then restart `serve --lan`:

```
MIRSAL_EMAIL_DOMAIN=nadi.ae,cpd.gov.ae,dubai.gov.ae
```

The line replaces the default, so keep the domains you still want in it. The sign-in card and the start-up line then name the new list. An empty value (`MIRSAL_EMAIL_DOMAIN=`) lets any email sign up; everyone still waits for your approval. Accounts made earlier keep working whatever the list says.

Always invoke `.\.venv\Scripts\python.exe -m ...` (with `.exe`): bare `python`/`pip` in this shell can resolve to another interpreter and poison the venv.

## Optional

| what                                      | command                                                                                                                      |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Postgres + Redis (Docker Desktop running) | `.\.venv\Scripts\python.exe -m mirsal db up` (the app works without them)                                                    |
| health check                              | `.\.venv\Scripts\python.exe -m mirsal doctor`                                                                                |
| Telegram approvals                        | Settings > Telegram: bot token + your user id; with `--lan` the bot sends you a card per sign-up, credit or password request |
| another port                              | `serve --port 8789`                                                                                                          |
| the old server (one release)              | `serve --stdlib`                                                                                                             |
| tests                                     | `docs/testing.md` (the test budget: one narrow run per change)                                                               |

Everything the app writes goes to `mirsal/out/`. Prepared sheets (optional) go in `inputs/Images_gen/img-NNN-<subject>/` and `inputs/videos_gen/vid-NNN-<subject>/` (folder names are final).

That's the Microsoft PostgreSQL extension's form. It has no port box on the main page, so the easiest way is the **Connection String** tab:

```


postgresql://mirsal:PASSWORD@localhost:5434/mirsal
```

Replace `PASSWORD` with the one in the `MIRSAL_DATABASE_URL=` line of `mirsal/.env` (line 12): it's the part between `mirsal:` and `@localhost`. I'm not printing it here because it's a secret. If you never set one, it's `mirsal_local`.

If you'd rather use **Parameters**, fill in:

| field               | value                                                 |
| ------------------- | ----------------------------------------------------- |
| Server name         | `localhost`                                           |
| Authentication Type | Password                                              |
| User name           | `mirsal`                                              |
| Password            | from `mirsal/.env`, as above                          |
| Database name       | `mirsal`                                              |
| Connection Name     | `Mirsal` (anything you like)                          |
| **Advanced → Port** | **`5434`** (it defaults to 5432, which won't connect) |

Click **Test Connection**, then **Save & Connect**. In the tree, expand **Mirsal → Databases → mirsal → Schemas → public → Tables**. Right-click **interactions** and choose "Select Top 1000" to see every chat turn. **sessions** lists the chats.

If the test fails, check that Docker Desktop is running and that `mirsal-db` is up: `docker ps` should list it with `0.0.0.0:5434->5432`.

## select chat

select user_message, assistant_message from interactions order by created_at desc limit 20;

## using docker

opens a SQL prompt inside the database container:

docker exec -it mirsal-db psql -U mirsal mirsal
Then type, for example:

select user_message, assistant_message from interactions order by created_at desc limit 20;
Type \q to leave.
