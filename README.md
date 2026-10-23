# Mirsal Builder

**Updated 2026-10-23.** The product is the API; Studio and AI chat are its sandboxes. All implementation branches were merged into `main` at `27009185`. Pricing is implemented and locally verified. Live CMS JSON delivery, stored-price readback, zero-count success handling and cooldown recovery remain open.

New requests default to **2×2 / four stickers**. Explicit and imported 3×3 grids remain supported. The current video catalog default is **Kling 3.0**; the requested Kling 4.0 default is pending verification. The existing animated pack sent as `test` reported four inserted assets. See the [delivery checklist](DELIVERY_CHECKLIST.md) for evidence and acceptance scope.

## Documentation: ten files

| File | Purpose |
|---|---|
| [README.md](README.md) | Start, run, office LAN and documentation index |
| [CLAUDE.md](CLAUDE.md) | Agent instructions and routing |
| [DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md) | One acceptance checklist and dated delivery evidence |
| [Architecture](docs/architecture.md) | Engine, Studio/chat, storage, reactions and measurements |
| [API](docs/api-integration.md) | HTTP contract, accounts, collection pricing and receiving CMS |
| [Generation](docs/generation.md) | Prompts, provider jobs, model defaults and credits |
| [Design](docs/design.md) | Screens, themes, accessibility and browser acceptance tools |
| [Rules](docs/rules.md) | Locked behavior, gates, spending and engineering guardrails |
| [Backlog](docs/backlog.md) | Engineering work and numbered owner decisions in one tracker |
| [Film kit](Motion%20Graphics/README.md) | Separate motion-graphics source and rendering instructions |

The repository has a budget of **10 maintained Markdown files**. Update the file that owns the topic; do not create plans, handoffs, duplicate guides or Markdown evaluation snapshots. Superseded material is available in Git history before this consolidation (baseline `51f327b1`). The 87 Help answers are application data in `faq/seed.json`; the Lottie MIT notice is retained verbatim as `mirsal/mirsal/console/ui/vendor/lottie-LICENSE`.

## Running locally

Use Python 3.11–3.13, a local `mirsal/.venv`, ffmpeg and Docker Desktop for the Postgres mirror (`mirsal-db`, port 5434) and Redis. Virtual environments and `.env` are local to each machine. Run the following from the repository root for first setup.

Windows PowerShell:

```powershell
cd mirsal
py -3 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# Fill keys in .env, then, with Docker Desktop running:
& .\.venv\Scripts\python.exe -m mirsal db up
& .\.venv\Scripts\python.exe -m mirsal doctor
& .\.venv\Scripts\python.exe -m mirsal serve
```

macOS Terminal:

```bash
cd mirsal
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
cp -n .env.example .env
# Fill keys in .env, then, with Docker Desktop running:
./.venv/bin/python -m mirsal db up
./.venv/bin/python -m mirsal doctor
./.venv/bin/python -m mirsal serve
```

For daily use, run only `db up` and `serve` from `mirsal/` with the platform's venv Python. Open <http://127.0.0.1:8770>. Stop with Ctrl+C. After pulling, the server owner restarts from the venv and hard-refreshes the browser. Use `--reload` only on your own development server; a restart interrupts in-flight work. Automation must use a disposable `MIRSAL_OUT` and a separate port, never the real-data :8770 server. `serve --stdlib` retains the legacy server for one release.

## Office LAN

Office sharing uses `serve --lan` over HTTPS. Public hosting and Google OAuth remain paused. Install mkcert once: `choco install mkcert` in an administrator shell on Windows, or `brew install mkcert` on macOS; then run `mkcert -install` on the host. Find the host's current Wi-Fi IPv4 address (`ipconfig` on Windows, network settings on macOS).

From the repository root on Windows, replace the example IP:

```powershell
New-Item -ItemType Directory -Force mirsal/out/tls
mkcert -cert-file mirsal/out/tls/cert.pem -key-file mirsal/out/tls/key.pem 192.168.1.66 localhost 127.0.0.1
cd mirsal
& .\.venv\Scripts\python.exe -m mirsal serve --lan
```

On macOS, from `mirsal/`:

```bash
mkdir -p out/tls
mkcert -cert-file out/tls/cert.pem -key-file out/tls/key.pem 192.168.1.66 localhost 127.0.0.1
./.venv/bin/python -m mirsal serve --lan
```

Colleagues open `https://<host-ip>:8770`. Run `mkcert -CAROOT` on the host and distribute only `rootCA.pem`; install it as a trusted root on each colleague's computer (Keychain Access on macOS; Local Machine → Trusted Root Certification Authorities on Windows). Keep `rootCA-key.pem` on the host. If the address changes, regenerate the host certificate and restart. A certificate warning means the client trust or host name/address needs correction. `--no-tls` uses plain HTTP and is unsuitable for office passwords.

Users sign up with a domain allowed by `MIRSAL_EMAIL_DOMAIN` (default `nadi.ae,cpd.gov.ae`) and await approval in Users → People. Accounts, role boundaries and credits are described in the [API guide](docs/api-integration.md#office-lan).

## Settings and delivery

Set provider keys only in `mirsal/.env`, then restart. `OPENAI_API_KEY` authenticates official OpenAI; `NARAROUTER_API_KEY` and `MIRSAL_CLOUD_URL` configure Nararouter. The built-in cloud choice is `openai:gpt-6-luna` with high reasoning; saved user/global choices and explicit environment settings take precedence. Local chat uses the configured local server's listed model and a real readiness probe. Full routing and vision fallback behavior are in [architecture](docs/architecture.md).

**Pack → Edit price** saves the collection price. **Export to collection** allows an override for one export: blank omits, `0` means free. Currency and live stored-price behavior remain unconfirmed. Configure `MIRSAL_COLLECTION_API_URL` and `MIRSAL_COLLECTION_API_CREDENTIALS` in `.env`; the [API guide](docs/api-integration.md#export-to-collection-the-mirsal-creator-cms) owns the complete contract.

Import Help data from `mirsal/` with your venv Python:

```text
python -m mirsal support import-faq --json
```

The command reads repository `faq/seed.json` and creates drafts; repeat imports are idempotent. Existing seed identities, approvals and revisions are preserved. Review/publish in Help → FAQ review. `--publish` is an explicit publishing choice. `--repo` accepts a bundle or a legacy Markdown folder. No live FAQ publishing occurs as part of documentation consolidation.

## Development and verification

- Work on `main`; check the current branch before every commit. Commit explicit paths, never secrets or a blind `git add -A`. Superseded source documents can be recovered with `git show 51f327b1:<path>`.
- Run the narrowest relevant check once (`mirsal test fast`, `focused` or `area <module>`); zero application tests for documentation-only changes. Full `unittest discover` is retired. Use the venv, not Anaconda's base Python.
- Tests and scratch servers set `MIRSAL_NO_REAL_CLI=1`, `MIRSAL_LLM_PROVIDER=none`, `MIRSAL_VISION_PROVIDER=none`, `MIRSAL_DB_WRITE=0` and a temporary `MIRSAL_OUT`. They never call real providers. Paid calls require a shown price and consent.
- Files are primary state; Postgres mirrors them. Never touch ports 5433/5436/5437 or another project's environment settings. `python -m mirsal doctor` is the health check; `db check` reports drift without silently changing constraints.
- Keep private inputs, keys, accounts and runtime scratch artifacts out of commits. Browser evidence belongs in ignored `output/playwright/`. Preserve the watch-folder and output naming rules in [rules](docs/rules.md).
