# Office LAN: accounts, approval, credits and the admin bot

**Steps 4-6 of [`plan.md`](../plan.md)**, after the ticket logger: sign-in, sessions and admin routes are FastAPI dependencies and pydantic models, and its notifications reuse the ticket logger's Telegram channel. The app stays on this PC and office colleagues reach it over the local network; public hosting (`deployment_plan.md`) stays paused.

Read first: `CLAUDE.md`, `docs/fastapi_plan.md`, `docs/tickets_plan.md`, `runtime/users.py`, `services/telegram.py`, `generation/jobs.py`, `docs/api.md` ("Accounts").

## 0. What Haitham asked (his words, condensed)

1. Expose the localhost server on the office network so clients join from their own machines.
2. Accounts are emails on `@nadi.ae`, pre-approved by Haitham, with pre-generated passwords. There is **no SMTP**.
3. Signing up in onboarding shows **"Waiting for approval"**. Haitham approves from a new **admin dashboard**, or sends the password back by hand.
4. Haitham gets a **Telegram notification on the Mirsal bot** (the one already used to test packs) with **Approve / Reject / Admin role**; tapping a button updates the server and shows the email used.
5. **Credits:** every approved user gets 10, all spent through Haitham's Higgsfield account. **Never refilled** until Haitham approves a request in Telegram, which shows the name and **Approve / Reject / Ignore**.
6. **Forgot password:** automated by the server, but gated by Haitham's approval. A user's details can be changed both in the dashboard and in Telegram.

## 1. Builds on

`runtime/users.py` (accounts, roles, hashed tokens; `out/users.json`), the Host / Origin guards and `_authorize` in `console/server.py`, the per-user rate limiter (`_wait`), `generation/jobs.py` (the price check and the paid queue), `services/telegram.py` (the Mirsal bot, which only sends today) and the paid-call ledger (`out/model_calls.jsonl`, Postgres `model_calls`). Extend them; do not rebuild them.

## 2. The design

### 2.1 Reaching the server from the office

- `python -m mirsal serve --lan` binds `0.0.0.0` (default stays `127.0.0.1`) and prints the address to share (`http://192.168.x.y:8770`).
- The Host allow-list gains the machine's own LAN addresses and an optional `MIRSAL_LAN_HOSTS` list; any other Host is still 403. Origin checks accept the same set. CORS stays closed (same-origin only).
- **HTTPS on the LAN (recommended).** Passwords over plain HTTP can be read by anyone on the same Wi-Fi. `serve --lan --tls` uses a locally issued certificate (`mkcert`, installed once on each office machine), so this stays local with no CDN or cloud service. Without TLS the sign-in page shows a one-line warning. Decision: W49.
- `/out/` media stays behind the existing signed-link and ownership checks; nothing becomes public by being on the LAN.

### 2.2 Accounts: email + password, two ways in

- **Pre-created by Haitham (the normal path):** in the admin dashboard, *Add people* takes emails (one per line, `@nadi.ae` only). Each gets a generated password (16 characters, `secrets`), **shown once** to Haitham to send by hand. Status: `active`.
- **Self sign-up in onboarding:** email (must end `@nadi.ae`), name and a chosen password. Status: `pending`; the screen shows **"Waiting for approval"** and nothing else works for that account. Haitham gets the Telegram card (§2.4).
- Passwords are hashed with `hashlib.scrypt` (stdlib, salted, per-user parameters; rule 8: no new dependency for this). A session is an HttpOnly, `SameSite=Strict` cookie (8 hours rolling; *Sign out* kills it). The existing bearer tokens stay for scripts and the API.
- Statuses: `pending` → `active` | `rejected`; `active` → `disabled` (by Haitham). Roles: `owner` (Haitham, exactly one), `admin` (may approve and edit people, never spends on another's behalf), `member`.
- Sign-in failures are throttled per email and per IP (the existing rate limiter, now switched on for these two routes only), and every failure answers the same words ("email or password is wrong") so emails cannot be probed.

### 2.3 The admin dashboard (Settings > People, owner and admin only)

One table: name, email, role, status, credits left / spent, last seen, requests waiting. Row actions: **Approve**, **Reject**, **Make admin** / **Make member**, **Disable**, **New password** (generated and shown once), **Edit** (name, email, role), **Give credits** (an amount, recorded). A *Waiting* filter at the top. Every action is a recorded line (who, when, what), the same audit rule as everywhere (rule 10's spirit: a person's click, reversible where it can be).

### 2.4 The Telegram admin bot

- The same bot and the same Haitham user id already in Settings (`out/telegram.json`). The server **long-polls** `getUpdates` in one background thread, so no public webhook or open port is needed. It answers **only** callback buttons and messages from Haitham's user id; everything else is ignored and logged.
- Cards it sends (each with inline buttons; a tap edits the card to show the outcome, so a second tap does nothing):

| event | card | buttons |
|---|---|---|
| sign-up | name, email, when | **Approve** · **Reject** · **Admin role** |
| credit request | name, email, credits spent / left, the reason they typed | **Approve +N** · **Reject** · **Ignore** |
| forgot password | name, email, when | **Send new password** · **Ignore** |
| new ticket (`tickets_plan.md`) | one line: what happened, to whom | **Open** (a link to the ticket on the dashboard) |

- **Send new password** generates one and sends it **to Haitham in the bot chat** (Telegram is Haitham's own channel) for him to pass on. The user must change it at the next sign-in. The password is never logged, never stored in clear, and the message tells Haitham to delete it once sent.
- Commands: `/people` (pending list with the same buttons), `/user email` (one person with Edit buttons: role, disable, new password). Editing in Telegram and in the dashboard call the same engine functions.

### 2.5 Credits per user

- On approval a user has **10 credits**. Before any paid call the job's estimate is checked against the user's balance (the same place the daily cap is checked today, `generation/jobs.py`). The credits are **reserved** when the job starts and **settled** on the real cost when it ends; a failed job gives them back. The ledger line and Postgres `model_calls` gain the user id.
- At 0 the paid buttons are off with one sentence and a **Request credits** button (a short reason, optional). That sends the Telegram card. **Nothing refills automatically**; only Haitham's tap (or the dashboard) adds credits.
- Rule 13 stays absolute: the price is shown first and a paid call needs the user's yes. The shared Higgsfield balance is shown only to the owner.
- Paid jobs from all users go through the existing queue (`jobs.paid_parallel()`, default 3 in flight), with at most one in flight per member, so one person cannot hold the queue.

### 2.6 Forgot password

*Forgot password* on the sign-in page takes the email and always answers the same sentence ("If this email has an account, Haitham will be asked"). It creates a reset request and the Telegram card. Haitham's tap generates the new password (§2.4). Nothing reaches the user by email; there is no SMTP.

### 2.7 What each person sees (decision: W50)

Recommendation: **their own work, plus shared packs Haitham publishes.** A member's batches, chats, jobs and particles are private to them (today's ownership checks); the library gets a *Shared* flag per pack so Haitham can give everyone a pack (the existing "packs and library per user" groundwork in `docs/backlog.md`). The alternative, one shared library for the whole office, is simpler but lets anyone delete anyone's packs.

## 3. Data

Additive migrations, mirrored from `out/users.json` (the file stays the source of truth on disk, like `result.json`):

- `010_accounts.sql`: `users` gains `email` (unique, lower-case), `name`, `password_hash`, `status`, `role` (+ `admin`), `credits_left`, `credits_spent`, `must_change_password`, `last_seen_at`.
- `011_requests.sql`: `account_requests (id, user_id, kind: signup|credits|password, status: waiting|approved|rejected|ignored, reason, decided_by, decided_at, telegram_message_id)`.
- `model_calls` gains `user_id` and `reserved`.
- Every admin action is a row in `account_requests` or an `audit` line; the ticket logger links to them.

## 4. Steps (each its own commit, its doc updated in the same step)

1. **Accounts on the LAN** (§2.1-§2.3, §2.6): `serve --lan [--tls]`, email + password, *Waiting for approval*, Settings > People, forgot password. Done when a colleague signs in from another machine.
2. **The Telegram admin bot** (§2.4). Done when approve / reject / role / new password work from the bot.
3. **Credits per user** (§2.5). Done when a member spends from 10 credits and can request more.

## 5. Risks

- **Higgsfield's terms** for one paid account used by several people (W42, now relevant for the office, not just a public launch).
- **Plain HTTP on shared Wi-Fi** exposes passwords and session cookies (W49).
- **The PC is the server:** if it sleeps or restarts, everyone is offline. `serve --lan` says so on start, and *Settings > People* shows who is signed in before a restart.
- **The bot is an admin channel:** only Haitham's user id is obeyed. A leaked bot token lets someone *send* as the bot, never approve (approvals are checked against Haitham's id); revoke and replace it in Settings.
