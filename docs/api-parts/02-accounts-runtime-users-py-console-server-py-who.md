# Accounts (`runtime/users.py`, `console/server.py` `_who` / `_authorize`)

<sub>Part of [api.md](../api.md).</sub>

`mirsal user add NAME [--owner] [--spend] | list | disable ID | enable ID | rotate ID | allow-spend ID | deny-spend ID` (or the routes below) manages `out/users.json`. A token
(`mk_…`) is shown **once** and only its SHA-256 is stored; it is compared in constant time. Authentication stays on once any account exists, even a disabled one (disabling the
only account must never open the server: delete `out/users.json` on purpose to go back).

- **Who is calling**: a user token is that user (checked first, so a client cannot widen itself by also sending `Sec-Fetch-Site`); the Studio's own page (`Sec-Fetch-Site: same-origin`)
  and `MIRSAL_API_TOKEN` are the implicit owner `local`. The page's own files (`/`, `/ui/…`, `/assets/…`) and a signed link need no header: they hold no data / the link is the credential.
  *A reverse proxy in front of the server must strip `Sec-Fetch-Site` from outside requests*, because that header is what marks the page.
- **Roles**: an `owner` manages the app and sees all batches; Library reads and pack edits remain scoped to their own packs. A `member` reaches only the chat, search, `GET /api/me`, `GET /api/health` (not `/api/health/models` or `/api/health/storage`), the OpenAPI document and **what they own**: their chats, the
  batches they started (and those batches' files, events, jobs and links) and the actions on them (`review, more, regen, animate, video_sheet, quick_sheet, drop, allow, judge, appearance, keep_size, video_size,
  edge, reslice, recheck`). A stranger's chat, batch, job or file is **`404`** (never a `403` that says it exists). Members also reach their Library, their own pack routes, bulk sticker edits and batch Add. Everything else is owner-only (`403`): projects,
  Telegram, watch folders, tasks, usage and credits, the operator's job actions, `files` / `reveal` on a batch, and the user list.
- **Spending**: live generation (`POST /api/live/sheet | video`, and the chat's Create / Animate on the live path) needs `can_spend`, because it spends the owner's Higgsfield credits; the check
  comes before anything about the provider is revealed. A member never sees the owner's balance.
- **Ownership** is stamped on the batch at creation (`result.json` `owner`, `generations.owner`), on the chat (`sessions.user_id`) and on the job (`request.user`), so a sheet that comes back
  minutes later still belongs to whoever asked for it. A chat turn runs in a thread and acts as its user.

| route | |
|---|---|
| `GET /api/me` | `{id, name, role, can_spend, via}` for the caller (`via`: `token`, `page`, `open`) |
| `GET /api/users` · `POST /api/users {name, role?, can_spend?}` | owner only; the create answer is `{user, token}` (the only time the token is visible) |
| `POST /api/users/{id}/update {name?, role?, can_spend?}` · `disable` · `enable` · `rotate` | owner only; `rotate` answers `{user, token}` and the old token stops working at once |

Packs carry `owner`; a legacy pack without one belongs to `local`. `GET /api/library` filters packs, Recent and totals by the caller, including the owner. Pack routes and `/lib/` files of another person answer 404. Media files (`/lib/`, `/out/`, `/src/`, `/proj/`) carry an `ETag` and `Last-Modified` with `Cache-Control: private, no-cache` and answer `304` to a matching `If-None-Match`, so a pack of animated stickers reopens from the browser's cache (Range requests still answer 206). Merge, single/bulk moves and batch Add validate every destination pack; a member may add only a batch they can see. Telegram routes remain owner-only. Reference images (`out/refs/R###`, shared by id) are not per user yet.
