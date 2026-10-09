"""Haitham's admin channel in the Mirsal Telegram bot (docs/api.md, Office accounts on the LAN): the bot already configured in Settings (token + Haitham's user id,
`out/telegram.json`) sends a card for every account request and every new ticket, and Haitham answers with one tap. The server long-polls `getUpdates` in
one background thread, so no public webhook or open port is needed. Only callbacks and messages from Haitham's own user id are obeyed; everything else is
ignored. A tap edits the card to its outcome, so a second tap does nothing.

`apply()` is the ONE way an account is changed, from Users > People and from the bot alike: it changes the account and closes the requests it answers."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

from . import telegram

_POLL: dict = {}


def apply(c, uid: str, action: str, by: str, *, role=None, credits=None, name=None, email=None, request_id: str | None = None) -> tuple[dict, str | None]:
    """approve | reject | admin | member | disable | enable | password | edit | credits | ignore -> (the account, a new password when one was made).
    The requests this answers are closed with who decided."""
    from ..flow import people as pp
    if action == "ignore":
        if not request_id:
            raise ValueError("ignore needs the request")
        pp.close(c.out, request_id, "ignored", by)
        return c.users.get(uid) or {}, None
    if action == "credits" and credits is None:
        credits = 10                                     # the card's "Approve +10"
    act = {"admin": ("role", "admin"), "member": ("role", "member")}.get(action, (action, role))
    u, pw = c.users.decide(uid, act[0], role=act[1], credits=credits, name=name, email=email)
    closes = {"approve": ("signup", "approved"), "reject": ("signup", "rejected"), "password": ("password", "approved"), "credits": ("credits", "approved")}.get(action)
    if closes:
        for r in pp.waiting(c.out, uid):
            if r["kind"] == closes[0]:
                pp.close(c.out, r["id"], closes[1], by)
    return u, pw


# ---------- cards ----------
def _cfg(out: Path) -> dict | None:
    if os.environ.get("MIRSAL_ADMIN_BOT", "1").strip() in ("0", "false", "no", "off"):
        return None
    cfg = telegram.load_config(out)
    return cfg if cfg.get("token") and cfg.get("user_id") else None


def _kb(rows) -> dict:
    return {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row] for row in rows]}


def _request_card(r: dict) -> tuple[str, dict]:
    who = f"{r.get('name') or ''} <{r.get('email') or ''}>"
    if r["kind"] == "signup":
        return f"New sign-up: {who}", _kb([[("Approve", f"a:{r['id']}:approve"), ("Reject", f"a:{r['id']}:reject"), ("Admin role", f"a:{r['id']}:admin")]])
    if r["kind"] == "credits":
        n = r.get("wanted")                              # the amount the person asked for (people._wanted); the default 10 stays one tap away
        give = [(f"Approve +{n}", f"a:{r['id']}:credits:{n}"), ("Give 10", f"a:{r['id']}:credits")] if n and n != 10 else [("Approve +10", f"a:{r['id']}:credits")]
        return (f"Credit request: {who}" + (f" asks for {n}" if n else "") + (f"\nReason: {r['reason']}" if r.get("reason") else ""),
                _kb([give + [("Reject", f"a:{r['id']}:ignore"), ("Ignore", f"a:{r['id']}:ignore")]]))
    return f"Forgot password: {who}", _kb([[("Send new password", f"a:{r['id']}:password"), ("Ignore", f"a:{r['id']}:ignore")]])


def _send(out: Path, text: str, markup: dict | None = None) -> dict | None:
    cfg = _cfg(out)
    if not cfg:
        return None
    fields = {"chat_id": cfg["user_id"], "text": text[:4000]}
    if markup:
        fields["reply_markup"] = markup
    return telegram._call(cfg["token"], "sendMessage", fields, timeout=20)


def notify_request(out: Path, r: dict) -> None:
    text, kb = _request_card(r)
    try:
        m = _send(out, text, kb)
        if m:
            from ..flow import people as pp
            pp.update(out, r["id"], telegram_message_id=m.get("message_id"))
    except Exception:
        pass


def notify_ticket(out: Path, t: dict) -> None:
    try:
        _send(out, f"Ticket {t['id']} ({t.get('source')}): {str(t.get('summary') or t.get('what_happened') or '')[:300]}\nSettings > Tickets")
    except Exception:
        pass


def notify_support(out: Path, text: str) -> bool:
    """A support escalation (flow/support.py): True only when Telegram took the message, so a failure is retried and never lost."""
    return bool(_send(out, text))


# ---------- the loop: Haitham's taps and commands ----------
def handle_update(c, upd: dict) -> None:
    """One update from getUpdates. The admin cards and commands (/people, /user, a tap on a request or person card) obey only Haitham's user id; every
    other message and every chat button, from anyone, is the AI chat (services/tg_chat.py)."""
    cfg = _cfg(c.out)
    if not cfg:
        return
    from . import tg_chat
    cq = upd.get("callback_query")
    msg = upd.get("message")
    sender = str(((cq or msg or {}).get("from") or {}).get("id") or "")
    admin = sender == str(cfg["user_id"])
    if cq:
        if str(cq.get("data") or "").startswith("c:"):
            tg_chat.on_tap(c, cfg, cq)
        elif admin:
            _on_tap(c, cfg, cq)
    elif msg:
        text = str(msg.get("text") or "").strip()
        if admin and text.split(" ")[0].split("@")[0] in ("/people", "/user"):
            _on_command(c, cfg, text)
        elif (msg.get("chat") or {}).get("type", "private") == "private":     # the chat answers people one to one, never in a group
            tg_chat.on_message(c, cfg, msg)


def _on_tap(c, cfg: dict, cq: dict) -> None:
    from ..flow import people as pp
    from ..runtime.users import UserError
    data = str(cq.get("data") or "")
    note = "done"
    try:
        kind, ident, action = data.split(":", 2)
        if kind == "a":                                  # a request card
            r = pp.get(c.out, ident)
            if r["status"] != "waiting":
                note = f"already {r['status']}"
            else:
                action, _, amount = action.partition(":")  # credits:7 = approve the 7 asked for; plain credits = the default 10
                n = int(amount) if amount.isdigit() and 1 <= int(amount) <= 10000 else None
                if amount and n is None:
                    raise ValueError(f"bad amount {amount}")
                u, pw = apply(c, r["user"], action, "telegram", request_id=r["id"], credits=n)
                if action == "admin":                    # Admin role on a sign-up also approves it
                    u, _ = apply(c, r["user"], "approve", "telegram")
                note = {"approve": "approved", "reject": "rejected", "admin": "approved as admin", "credits": f"+{n or 10} credits", "password": "new password sent",
                        "ignore": "ignored"}.get(action, action)
                if pw:
                    telegram._call(cfg["token"], "sendMessage", {"chat_id": cfg["user_id"], "text": f"New password for {u.get('email')}: {pw}\n(They change it at the next sign-in. Delete this message once you sent it.)"}, timeout=20)
        elif kind == "u":                                # a person card from /user
            u, pw = apply(c, ident, action, "telegram")
            note = action + ("d" if action in ("disable", "enable") else "")
            if pw:
                telegram._call(cfg["token"], "sendMessage", {"chat_id": cfg["user_id"], "text": f"New password for {u.get('email')}: {pw}\n(Delete this message once you sent it.)"}, timeout=20)
    except (KeyError, ValueError, UserError) as e:
        note = f"could not: {e}"
    try:
        telegram._call(cfg["token"], "answerCallbackQuery", {"callback_query_id": cq["id"], "text": note[:180]}, timeout=20)
        m = cq.get("message") or {}
        if m.get("message_id"):
            telegram._call(cfg["token"], "editMessageText", {"chat_id": m["chat"]["id"], "message_id": m["message_id"],
                                                             "text": f"{m.get('text', '')}\n→ {note}"[:4000]}, timeout=20)
    except Exception:
        pass


def _on_command(c, cfg: dict, text: str) -> None:
    from ..flow import people as pp
    if text.startswith("/people"):
        rows = pp.waiting(c.out)
        if not rows:
            _send(c.out, "Nothing is waiting.")
        for r in rows[:20]:
            t, kb = _request_card(r)
            _send(c.out, t, kb)
    elif text.startswith("/user"):
        email = text[5:].strip()
        u = c.users.by_email(email)
        if not u:
            _send(c.out, f"No account for {email or '(no email)'}. Use /user name@nadi.ae")
            return
        p = c.users.public(u)
        _send(c.out, f"{p.get('name')} <{p.get('email')}> · {p.get('role')} · {p.get('status')} · {p.get('credits_left', 0)} credits left",
              _kb([[("Make admin", f"u:{p['id']}:admin"), ("Make member", f"u:{p['id']}:member")],
                   [("Disable", f"u:{p['id']}:disable"), ("Enable", f"u:{p['id']}:enable"), ("New password", f"u:{p['id']}:password")]]))
    else:
        _send(c.out, "/people: what is waiting · /user name@nadi.ae: one person · anything else: the AI chat")


def start(c) -> None:
    """The long-poll thread (one per server). Off unless the server runs on the LAN with the bot configured; MIRSAL_ADMIN_BOT=0 turns it off."""
    if not getattr(c, "lan", False) or not _cfg(c.out) or _POLL.get("thread"):
        return

    def loop():
        offset, retried = 0, 0.0
        while not _POLL.get("stop"):
            if time.time() - retried > 300:                              # support pings that Telegram refused earlier go out again
                retried = time.time()
                try:
                    from ..flow import support
                    support.retry_pings(c.out)
                except Exception:
                    pass
            cfg = _cfg(c.out)
            if not cfg:
                time.sleep(30)
                continue
            try:
                ups = telegram._call(cfg["token"], "getUpdates", {"offset": offset, "timeout": 25, "allowed_updates": ["message", "callback_query"]}, timeout=40)
            except Exception:
                time.sleep(10)
                continue
            for u in ups or []:
                offset = max(offset, int(u.get("update_id", 0)) + 1)
                try:
                    handle_update(c, u)
                except Exception:
                    pass

    _POLL["thread"] = threading.Thread(target=loop, daemon=True, name="mirsal-admin-bot")
    _POLL["thread"].start()
