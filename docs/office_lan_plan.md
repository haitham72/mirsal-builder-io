# Office LAN: what is still open

**Step 1 of [`plan.md`](../plan.md).** Accounts on the LAN, sign-in, approval, Settings > People, forgot password and the Telegram admin bot exist (their contract is `api.md`, "Office accounts on the LAN"). What remains: the Trending gallery. Read first: `runtime/users.py` (`charge`), `flow/people.py`, `services/admin_bot.py`, `generation/jobs.py`, `media/library.py`.

## The design

### 2.7 What each person sees: own work + a Trending gallery (Haitham, 2026-10-04)

- A member's batches, chats, jobs and particles are **private** (today's ownership checks).
- **Trending** (a Library tab, Higgsfield-style): packs their owners chose to **Share**. Everyone can **like** and **comment**; the gallery is ordered by recent likes and comments (a simple score with a time decay, recomputed on read), with *New* and *Most liked* as the other two orders. A comment is plain text, owner and admin can delete it.
- **Use in my workflow**: on a shared pack, copies it into the viewer's own library as a new pack (files copied, `source.shared_from` recorded), ready for the Studio (add stickers, particles, a new batch in its style). The original stays the owner's; nothing is shared back unless they Share it.
- Data: `shared_packs (pack_id, owner, shared_at)`, `pack_likes (pack_id, user_id, at)`, `pack_comments (id, pack_id, user_id, text, at, deleted)`; routes `POST /api/packs/{id}/share|unshare|like|unlike|comments|use`, `GET /api/trending?order=trending|new|liked`.

## Steps

1. **Trending** (2.7). Done when one colleague uses another's shared pack in their own Studio.

## Risks

- **Higgsfield's terms** for one paid account used by several people (W42, now relevant for the office, not just a public launch).
- **Plain HTTP on shared Wi-Fi** would expose passwords and session cookies: `--lan` runs with TLS (decided 2026-10-04).
- **The PC is the server:** if it sleeps or restarts, everyone is offline. `serve --lan` says so on start, and *Settings > People* shows who is signed in before a restart.
- **The bot is an admin channel:** only Haitham's user id is obeyed. A leaked bot token lets someone *send* as the bot, never approve (approvals are checked against Haitham's id); revoke and replace it in Settings.
