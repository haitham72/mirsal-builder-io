"""The AI chat in Telegram (Haitham, 2026-10-09: "can the Telegram bot NOW be exactly like the AI chat"). The same bot as the admin cards
(services/admin_bot.py polls it); every message that is not an admin command is a turn of the SAME agent the web chat runs (`Console.chat_send`, its
memory, its cards, its creator runs). Telegram is only another screen on it: nothing here decides anything the agent does not.

- **Who:** open to everyone for now. Haitham's own Telegram id is the owner; anyone else gets a Mirsal member account of their own, created at the first
  message with 0 credits (an account without a balance would spend without limit), and Haitham gets a card (+10 credits / Disable). They see only their own work.
- **A chat** is one session per Telegram chat (`/new` starts another). It starts on Nano Banana 2 for sheets, Grok Imagine 1.5 Lite for videos, gpt-4o for
  the AI and the Glossy style (`DEFAULTS`); `/model` changes them with native Telegram buttons, minimally.
- **Questions are native cards:** every chip of a reply (Create it · N credits, Not yet, Animate ...) is an inline button; a paid step is a button that states
  its price, so nothing spends until it is tapped (rule 13). A tap is the same action the web chat's chip sends.
- **What comes back:** the reply text, the sheet's stickers as one album, every finished animation as a REAL Telegram sticker, and every sticker or animation
  Python blocked as its own message with the picture, the reason in words and **Use it anyway** (rule 10: a rejection is never a dead end); a creator run is one
  message that is edited as its steps move, with Stop while it runs.
State lives in `out/telegram_chats.json` (people, the chat -> session map, what was already sent, the button keys). Never raises into the poller."""
from __future__ import annotations

import html
import json
import re
import secrets
import threading
import time
from pathlib import Path

from . import telegram

DEFAULTS = {"image": "nano_banana_flash", "video": "grok_video_v15_lite", "ai": "gpt-4o"}
DEFAULT_STYLE = "glossy_3d"
AI_MODELS = ("gpt-4o", "gpt-4.1-mini", "gpt-4.1")
FOLLOW_S = 4 * 3600           # the longest a chat is followed after its last turn (a creator run can take a while)
_LOCK = threading.RLock()
_FOLLOW: dict = {}            # chat id -> the thread following it


# ---------- state ----------
def _path(out: Path) -> Path:
    return Path(out) / "telegram_chats.json"


def _load(out: Path) -> dict:
    try:
        d = json.loads(_path(out).read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(out: Path, d: dict) -> None:
    from ..runtime import atomic
    atomic.write_text(_path(out), json.dumps(d, ensure_ascii=False, indent=1))


def _chat(out: Path, chat_id) -> dict:
    with _LOCK:
        return dict((_load(out).get("chats") or {}).get(str(chat_id)) or {})


def _put_chat(out: Path, chat_id, **fields) -> dict:
    with _LOCK:
        d = _load(out)
        ch = d.setdefault("chats", {}).setdefault(str(chat_id), {})
        ch.update(fields)
        _save(out, d)
        return dict(ch)


def _mark_sent(out: Path, chat_id, key: str) -> bool:
    """True the first time `key` is marked for this chat: one part is sent once, whatever the polling does."""
    with _LOCK:
        d = _load(out)
        ch = d.setdefault("chats", {}).setdefault(str(chat_id), {})
        sent = ch.setdefault("sent", [])
        if key in sent:
            return False
        sent.append(key)
        del sent[:-2000]
        _save(out, d)
        return True


def _key(out: Path, chat_id, action: dict) -> str:
    """A short button key for an action (Telegram's callback_data holds 64 bytes): the action itself stays here."""
    with _LOCK:
        d = _load(out)
        ch = d.setdefault("chats", {}).setdefault(str(chat_id), {})
        keys = ch.setdefault("keys", {})
        k = secrets.token_hex(5)
        keys[k] = action
        if len(keys) > 500:
            for old in list(keys)[:-500]:
                keys.pop(old, None)
        _save(out, d)
        return k


# ---------- who is writing ----------
def person(c, cfg: dict, frm: dict) -> dict | None:
    """The Mirsal account behind a Telegram user: Haitham's id is the owner; anyone else gets their own member account at the first message (0 credits,
    Haitham is told). None for a disabled account."""
    from ..runtime.users import LOCAL
    tid = str(frm.get("id") or "")
    if not tid:
        return None
    if tid == str(cfg.get("user_id")):
        return LOCAL
    with _LOCK:
        d = _load(c.out)
        uid = ((d.get("people") or {}).get(tid) or {}).get("user")
        u = c.users.get(uid) if uid else None
        if not u:
            name = " ".join(x for x in (frm.get("first_name"), frm.get("last_name")) if x).strip() or frm.get("username") or f"Telegram {tid}"
            pub, _token = c.users.create(f"{name[:48]} (Telegram)", "member", True)
            c.users.decide(pub["id"], "credits", credits=0)           # a balance of 0: spending waits for credits from Haitham
            d.setdefault("people", {})[tid] = {"user": pub["id"], "name": name, "username": frm.get("username"), "at": round(time.time(), 3)}
            _save(c.out, d)
            u = c.users.get(pub["id"])
            from . import admin_bot
            try:
                admin_bot._send(c.out, f"New Telegram user: {name}{' @' + frm['username'] if frm.get('username') else ''} started chatting with the bot "
                                       f"(account {pub['id']}, 0 credits: they can talk, not spend).",
                                admin_bot._kb([[("Give +10 credits", f"u:{pub['id']}:credits"), ("Disable", f"u:{pub['id']}:disable")]]))
            except Exception:
                pass
    if not u or u.get("disabled"):
        return None
    return c.users.public(u)


def _store(c, user: dict):
    return c.chat_parts(user)[0]


def session_of(c, user: dict, chat_id, fresh: bool = False) -> str:
    """The chat's session; a new one starts on the Telegram defaults (Glossy, Nano Banana 2, Grok Lite, gpt-4o, the Emojis stage)."""
    ch = _chat(c.out, chat_id)
    store = _store(c, user)
    if ch.get("sid") and not fresh and ch.get("user") == user["id"]:
        try:
            store.load(ch["sid"])
            return ch["sid"]
        except Exception:
            pass
    s = store.create("Telegram", {"style_id": DEFAULT_STYLE, "models": dict(DEFAULTS), "stage": "emojis"})
    _put_chat(c.out, chat_id, sid=s["id"], user=user["id"])
    return s["id"]


# ---------- sending ----------
def _tok(c) -> str:
    return telegram.load_config(c.out)["token"]


def _md(text: str) -> str:
    """The agent's light markdown (**bold**, `code`) as Telegram HTML."""
    t = html.escape(str(text or ""), quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", t)


def _kb(rows) -> dict | None:
    rows = [r for r in rows if r]
    return {"inline_keyboard": rows} if rows else None


def say(c, chat_id, text: str, rows=None, **extra) -> dict | None:
    fields = {"chat_id": chat_id, "text": _md(text)[:4000] or "…", "parse_mode": "HTML", **extra}
    kb = _kb(rows or [])
    if kb:
        fields["reply_markup"] = kb
    return telegram._call(_tok(c), "sendMessage", fields, timeout=30)


def _file(c, url: str | None) -> Path | None:
    """`/out/G121/slices/x.png?e=…` -> the file on disk (through the batch's labelled folder)."""
    from ..flow import pipeline as pl
    m = re.match(r"^/out/G(\d+)/([^?]+)", str(url or ""))
    if not m:
        return None
    try:
        f = pl.gen_dir(c.out, int(m.group(1))) / m.group(2)
    except Exception:
        return None
    return f if f.is_file() else None


def _send_file(c, chat_id, method: str, field: str, f: Path, mime: str, caption: str | None = None, rows=None, **extra) -> dict | None:
    fields = {"chat_id": chat_id, **extra}
    if caption:
        fields.update(caption=_md(caption)[:1000], parse_mode="HTML")
    kb = _kb(rows or [])
    if kb:
        fields["reply_markup"] = kb
    return telegram._call(_tok(c), method, fields, {field: (f.name, f.read_bytes(), mime)}, timeout=120)


def _album(c, chat_id, files: list[Path], caption: str) -> None:
    for i in range(0, len(files), 10):
        part = files[i:i + 10]
        if len(part) == 1:
            _send_file(c, chat_id, "sendPhoto", "photo", part[0], "image/png", caption if i == 0 else None)
            continue
        media = [{"type": "photo", "media": f"attach://p{k}", **({"caption": caption[:1000]} if i == 0 and k == 0 else {})} for k in range(len(part))]
        telegram._call(_tok(c), "sendMediaGroup", {"chat_id": chat_id, "media": media},
                       {f"p{k}": (f.name, f.read_bytes(), "image/png") for k, f in enumerate(part)}, timeout=120)


# ---------- one reply, as Telegram parts ----------
def _chip_rows(c, chat_id, m: dict) -> list:
    rows = []
    for ch in m.get("chips") or []:
        if ch.get("setting"):
            k, v = next(iter(ch["setting"].items()))
            act = {"t": "setting", "set": {k: v if v is not None else True}}
        elif ch.get("action"):
            act = {"t": "action", "a": {k: ch[k] for k in ("generation", "indexes", "to") if ch.get(k) is not None} | {"type": ch["action"]}}
        elif ch.get("editor") or ch.get("fill"):
            continue                                       # the sticker editor is a browser screen; "Edit" fills the web chat's box (here the person just types)
        else:
            act = {"t": "text", "text": ch.get("text") or ch.get("label")}
        rows.append([{"text": str(ch.get("label") or "…")[:60], "callback_data": "c:" + _key(c.out, chat_id, act)}])
    return rows


def _plan_lines(card: dict) -> str:
    if card.get("type") == "plan":
        price = "free (no provider call)" if card.get("free") else f"{card.get('estimate')} credits"
        return f"\n\n<b>{html.escape(str(card.get('subject')))}</b>: {card.get('count')} stickers · {card.get('grid')} · {html.escape(str(card.get('style')))} · {price}" + \
               (f"\n{html.escape(str((card.get('batch') or {}).get('text')))}" if card.get("batch") else "") + \
               (f"\n{html.escape(', '.join(card.get('names') or [])[:600])}" if card.get("names") else "")
    if card.get("type") == "multi":
        items = "\n".join(f"• {html.escape(str(i.get('subject')))}: {i.get('count')} stickers" for i in card.get("items") or [])
        return f"\n\n<b>{html.escape(str(card.get('title')))}</b>\n{items}\nAll together: {card.get('estimate')} credits"
    return ""


def _gen_parts(c, chat_id, card: dict) -> bool:
    """Send what a generation card holds now (each part once). True while it is still working (the follower keeps polling)."""
    gid, data = card.get("generation"), card.get("data") or {}
    if card.get("job_status") in ("FAILED", "TIMEOUT"):
        if _mark_sent(c.out, chat_id, f"job:{card.get('job')}:fail"):
            say(c, chat_id, f"The {'sheet' if not gid else 'video'} job {card.get('job')} {card['job_status'].lower()}: {card.get('job_error') or 'no reason given'}. Nothing more is spent; ask again when you want.")
        return False
    if not gid or not data:
        return card.get("job_status") not in ("DONE",) or not gid
    st, allow = data.get("stickers") or [], data.get("allow") or {}
    if data.get("problem"):
        p = data["problem"]
        if _mark_sent(c.out, chat_id, f"{gid}:problem"):
            rows = []
            if p.get("cut_anyway"):
                rows.append([{"text": "Cut it anyway · free", "callback_data": "c:" + _key(c.out, chat_id, {"t": "recut", "g": gid})}])
            rows.append([{"text": f"Try the sheet again · {p.get('retry_estimate') or '?'} credits", "callback_data": "c:" + _key(c.out, chat_id, {"t": "action", "a": {"type": "retry_sheet", "generation": gid}})}])
            say(c, chat_id, f"**{p.get('title')}**\n{p.get('why')}\n{p.get('fix')}", rows)
        return False
    if not st or any(s.get("status") == "PENDING" for s in st):
        return True
    if _mark_sent(c.out, chat_id, f"{gid}:stills"):
        ok = [f for s in st if s.get("status") == "READY" and s.get("still") != "REJECTED" for f in [_file(c, s.get("png"))] if f]
        if ok:
            _album(c, chat_id, ok, f"{gid} · {len(ok)} sticker{'s' if len(ok) != 1 else ''} ready")
    for s in st:                                           # rule 10: every blocked still is shown with its reason and its override
        a = allow.get("still") or {}
        if s.get("status") == "FAILED" or s.get("still") == "REJECTED":
            if _mark_sent(c.out, chat_id, f"{gid}:S{s['index']}:still"):
                _blocked(c, chat_id, gid, s, "still", a)
    animating = any(s.get("anim_status") in ("PROCESSING", "PENDING", "RUNNING") for s in st)
    done = [s for s in st if s.get("anim_status") == "READY"]
    if done and not animating:
        cut = next((v["id"] for v in reversed(data.get("video_sheets") or []) if v.get("status") == "SLICED"), "A")
        for s in done:
            a = allow.get("animation") or {}
            blocked = s.get("anim") in ("REJECTED", "BLOCKED")
            if not _mark_sent(c.out, chat_id, f"{gid}:{cut}:S{s['index']}:anim:{'blocked' if blocked else 'ok'}"):      # allowed later: it then arrives as a sticker
                continue
            f = _file(c, s.get("webm"))
            if f and not blocked:
                emoji = s.get("emoji") if isinstance(s.get("emoji"), str) else "".join(s.get("emoji") or []) or "🙂"
                try:
                    _send_file(c, chat_id, "sendSticker", "sticker", f, "video/webm", emoji=emoji[:16])
                except telegram.TelegramError:
                    _send_file(c, chat_id, "sendAnimation", "animation", f, "video/webm", f"{gid}/S{s['index']}")
            elif blocked:
                _blocked(c, chat_id, gid, s, "animation", a)
    for s in st:
        if s.get("anim_status") == "FAILED" and _mark_sent(c.out, chat_id, f"{gid}:S{s['index']}:animfail"):
            _blocked(c, chat_id, gid, s, "animation", allow.get("animation") or {})
    return animating


def _blocked(c, chat_id, gid: str, s: dict, kind: str, a: dict) -> None:
    """One sticker or animation Python blocked: the picture, the reason in words, and Use it anyway when it may be allowed (else why it cannot)."""
    i = s["index"]
    why = (a.get("why") or {}).get(str(i)) or (a.get("why") or {}).get(i) or s.get("anim_reason" if kind == "animation" else "reason") or "blocked"
    final = (a.get("final") or {}).get(str(i)) or (a.get("final") or {}).get(i)
    rows = []
    if i in (a.get("can") or []):
        rows.append([{"text": "Use it anyway", "callback_data": "c:" + _key(c.out, chat_id, {"t": "allow", "g": gid, "i": i, "kind": kind, "allow": True})}])
    text = f"{gid}/S{i} · {'animation' if kind == 'animation' else 'sticker'} blocked: {str(why).replace('_', ' ')}" + (f"\n{final}" if final and not rows else "")
    f = _file(c, s.get("png"))
    if f:
        _send_file(c, chat_id, "sendPhoto", "photo", f, "image/png", text, rows)
    else:
        say(c, chat_id, text, rows)


def _run_part(c, chat_id, run: dict) -> bool:
    """A creator run: one message, edited as its steps move. True while it runs."""
    steps = "\n".join(f"{'✅' if s.get('state') == 'done' else '⏳' if s.get('state') in ('running', 'current') else '⛔' if s.get('state') in ('failed', 'stopped') else '▫️'} {s.get('label')}"
                      for s in run.get("steps") or [])
    st = {"running": "Working…", "waiting": "Waiting for you", "done": "Animated" if run.get("end") == "animation" else "On Telegram", "failed": "Failed"}.get(run.get("status"), "Stopped")
    why = (run.get("stop") or run.get("waiting") or {}).get("why")
    text = f"<b>{html.escape(str(run.get('subject') or 'Pack'))}</b> · {st}\n{html.escape(steps)}" + (f"\n{html.escape(str(why))}" if why else "")
    rows = [[{"text": "Stop", "callback_data": "c:" + _key(c.out, chat_id, {"t": "action", "a": {"type": "creator_stop"}})}]] if run.get("status") == "running" else []
    ch = _chat(c.out, chat_id)
    runs = ch.get("runs") or {}
    cur = runs.get(run["id"]) or {}
    if cur.get("text") == text:
        return run.get("status") == "running"
    tok = _tok(c)
    try:
        if cur.get("message_id"):
            telegram._call(tok, "editMessageText", {"chat_id": chat_id, "message_id": cur["message_id"], "text": text[:4000], "parse_mode": "HTML",
                                                    **({"reply_markup": {"inline_keyboard": rows}} if rows else {"reply_markup": {"inline_keyboard": []}})}, timeout=30)
            mid = cur["message_id"]
        else:
            m = telegram._call(tok, "sendMessage", {"chat_id": chat_id, "text": text[:4000], "parse_mode": "HTML", **({"reply_markup": {"inline_keyboard": rows}} if rows else {})}, timeout=30)
            mid = m.get("message_id")
    except telegram.TelegramError:
        return run.get("status") == "running"
    runs[run["id"]] = {"message_id": mid, "text": text}
    _put_chat(c.out, chat_id, runs=runs)
    return run.get("status") in ("running",)


def render(c, chat_id, user: dict, sid: str) -> bool:
    """Send every part of the session that was not sent yet. True while something is still working (a turn, a sheet, an animation, a creator run)."""
    from ..agent import graph as ag
    store, tools, _agent, _ = c.chat_parts(user, sid)
    try:
        _agent.batch_followup(sid)                         # the batches are cut: the follow-up card arrives as buttons (Regenerate · Batch 02 · 03 · 04)
    except Exception:
        pass
    sess = ag.hydrate(store, tools, store.load(sid))
    busy = bool(sess.get("working"))
    run = sess.get("creator_run") or {}
    if run.get("status") == "running":
        c.drive_creator(user, sid)                         # a restarted server picks the run up again, as the web chat's poll does
    last_user = max([i for i, m in enumerate(sess["messages"]) if m.get("role") == "user"] or [-1])
    for m in sess["messages"][max(0, last_user - 6):]:
        if m.get("role") == "user":
            continue
        if m.get("status") == "working":
            busy = True
            continue
        cards = m.get("cards") or []
        if _mark_sent(c.out, chat_id, f"{sid}:{m['id']}:text"):
            text = _md(m.get("text") or "") + "".join(_plan_lines(cd) for cd in cards)
            fields = {"chat_id": chat_id, "text": (text or "…")[:4000], "parse_mode": "HTML"}
            kb = _kb(_chip_rows(c, chat_id, m))
            if kb:
                fields["reply_markup"] = kb
            telegram._call(_tok(c), "sendMessage", fields, timeout=30)
        for cd in cards:
            if cd.get("type") == "generation":
                busy = _gen_parts(c, chat_id, cd) or busy
            elif cd.get("type") == "creator" and cd.get("run"):
                busy = _run_part(c, chat_id, cd["run"]) or busy
            elif cd.get("type") == "stickers" and _mark_sent(c.out, chat_id, f"{sid}:{m['id']}:found"):
                files = [f for s in cd.get("stickers") or [] for f in [_file(c, s.get("png"))] if f]
                if files:
                    _album(c, chat_id, files[:20], f"{len(cd.get('stickers') or [])} found")
    return busy


def follow(c, chat_id, user: dict, sid: str) -> None:
    """Follow one chat in the background until nothing is working any more (one thread per chat; a new turn restarts it)."""
    old = _FOLLOW.get(str(chat_id))
    if old and old.is_alive():
        _FOLLOW[str(chat_id) + ":again"] = True
        return

    def loop():
        end, idle = time.time() + FOLLOW_S, 0
        while time.time() < end:
            try:
                busy = render(c, chat_id, user, sid)
            except Exception as e:
                from ..runtime import activity
                activity.say(f"Telegram chat {chat_id}: {type(e).__name__}: {e}", error=True)
                busy = True
            if _FOLLOW.pop(str(chat_id) + ":again", None):
                idle = 0
                continue
            idle = 0 if busy else idle + 1
            if idle >= 3:
                break
            if busy:
                try:
                    telegram._call(_tok(c), "sendChatAction", {"chat_id": chat_id, "action": "typing"}, timeout=10)
                except Exception:
                    pass
            time.sleep(2.0)
        _FOLLOW.pop(str(chat_id), None)
    t = threading.Thread(target=loop, daemon=True, name=f"mirsal-tg-{chat_id}")
    _FOLLOW[str(chat_id)] = t
    t.start()


# ---------- the person's side ----------
def turn(c, chat_id, user: dict, text: str = "", action: dict | None = None) -> None:
    from ..agent.memory import SessionError
    from ..flow import pipeline as pl
    sid = session_of(c, user, chat_id)
    try:
        c.chat_send(sid, {"text": text, **({"action": action} if action else {})}, user)
    except (pl.PipelineError, SessionError) as e:
        say(c, chat_id, "Still working on your last message: wait for it, then send this again." if getattr(e, "code", 0) == 409 else str(e))
        return
    follow(c, chat_id, user, sid)


def _model_label(kind: str, mid: str | None) -> str:
    from ..agent import stages
    from ..generation import model_catalog as mc, styles
    if kind == "stage":
        return stages.INFO.get(mid or "", stages.INFO[stages.DEFAULT])["label"]
    if kind == "style":
        return next((s["label"] for s in styles.PRESETS if s["id"] == mid), mid or "?")
    if kind == "ai":
        return mid or "server default"
    try:
        return mc.find(kind, mid)["label"] if mid else "server default"
    except Exception:
        return mid or "?"


def models_card(c, chat_id, user: dict, message_id=None, open_: str | None = None) -> None:
    """/model: the chat's image model, video model, style, AI and stage on one card; a tap opens that list, a pick saves it and closes it. /stage opens the
    stage list directly (how far a new request goes: agent/stages.py)."""
    from ..agent import stages
    from ..generation import model_catalog as mc, styles
    store = _store(c, user)
    sid = session_of(c, user, chat_id)
    st = store.load(sid)["settings"]
    cur = {**DEFAULTS, **(st.get("models") or {})}
    cur["style"] = st.get("style_id") or DEFAULT_STYLE
    cur["stage"] = stages.of(st)
    btn = lambda text, act: {"text": text[:60], "callback_data": "c:" + _key(c.out, chat_id, act)}
    if open_ == "stage":
        rows = [[btn(("✓ " if k == cur["stage"] else "") + f"{v['label']} · {v['hint']}", {"t": "model", "kind": "stage", "id": k})] for k, v in stages.INFO.items()]
        rows.append([btn("‹ Back", {"t": "models"})])
        text = "How far a new request goes in this chat"
    elif open_:
        opts = ([(s["id"], s["label"]) for s in styles.PRESETS] if open_ == "style" else [(m, m) for m in AI_MODELS] if open_ == "ai"
                else [(m["id"], m["label"]) for m in mc.catalog()[open_]])
        rows = [[btn(("✓ " if i == cur.get(open_) else "") + l, {"t": "model", "kind": open_, "id": i}) for i, l in opts[k:k + 2]] for k in range(0, len(opts), 2)]
        rows.append([btn("‹ Back", {"t": "models"})])
        text = {"image": "Image model for this chat", "video": "Video model for this chat", "style": "Style for this chat", "ai": "AI model for this chat"}[open_]
    else:
        rows = [[btn(f"🖼 {_model_label('image', cur['image'])}", {"t": "models", "open": "image"}), btn(f"🎞 {_model_label('video', cur['video'])}", {"t": "models", "open": "video"})],
                [btn(f"🎨 {_model_label('style', cur['style'])}", {"t": "models", "open": "style"}), btn(f"🤖 {cur.get('ai') or 'default'}", {"t": "models", "open": "ai"})],
                [btn(f"🧭 {_model_label('stage', cur['stage'])}", {"t": "models", "open": "stage"})]]
        text = "This chat's models · tap one to change it"
    tok = _tok(c)
    if message_id:
        telegram._call(tok, "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": text, "reply_markup": {"inline_keyboard": rows}}, timeout=30)
    else:
        telegram._call(tok, "sendMessage", {"chat_id": chat_id, "text": text, "reply_markup": {"inline_keyboard": rows}}, timeout=30)


def set_model(c, user: dict, chat_id, kind: str, mid: str) -> None:
    from ..agent import stages
    from ..generation import model_catalog as mc, styles
    if kind == "stage":
        if not stages.valid(mid):
            raise ValueError("no such stage")
    elif kind == "style":
        if not any(s["id"] == mid for s in styles.PRESETS):
            raise ValueError("no such style")
    elif kind == "ai":
        if mid not in AI_MODELS:
            raise ValueError("no such AI model")
    elif kind not in ("image", "video") or not any(m["id"] == mid for m in mc.catalog()[kind]):
        raise ValueError("no such model")
    store = _store(c, user)
    s = store.load(session_of(c, user, chat_id))
    if kind == "style":
        s["settings"]["style_id"] = mid
    elif kind == "stage":
        s["settings"]["stage"] = mid
    else:
        s["settings"]["models"] = {**DEFAULTS, **(s["settings"].get("models") or {}), kind: mid}
    store.save(s)


HELP = ("Tell me what stickers you want, for example <b>a teddy bear for school</b>. I plan them, show the price, and make them when you tap the button.\n"
        "/model: the image model, video model, style, AI and stage of this chat\n/stage: how far a new request goes (Prompt, Emojis, Animation, Export)\n"
        "/new: start a new chat\n/help: this message")


def on_message(c, cfg: dict, msg: dict) -> None:
    chat_id = (msg.get("chat") or {}).get("id")
    user = person(c, cfg, msg.get("from") or {})
    if chat_id is None:
        return
    if not user:
        say(c, chat_id, "This account is disabled.")
        return
    text = str(msg.get("text") or msg.get("caption") or "").strip()
    cmd = text.split()[0].split("@")[0].lower() if text.startswith("/") else ""
    if cmd in ("/start", "/help"):
        session_of(c, user, chat_id)
        say(c, chat_id, ("Welcome to Mirsal.\n" if cmd == "/start" else "") + HELP)
        return
    if cmd == "/new":
        session_of(c, user, chat_id, fresh=True)
        say(c, chat_id, "A new chat. What should we make?")
        return
    if cmd == "/model":
        models_card(c, chat_id, user)
        return
    if cmd == "/stage":
        models_card(c, chat_id, user, open_="stage")
        return
    if msg.get("photo") or msg.get("document"):
        say(c, chat_id, "Pictures are not read in the Telegram chat yet: describe it in words, or attach it in the web chat.")
        if not text:
            return
    if not text:
        return
    turn(c, chat_id, user, text)


def on_tap(c, cfg: dict, cq: dict) -> None:
    from ..agent.tools import ToolError
    from ..flow import pipeline as pl
    m = cq.get("message") or {}
    chat_id = (m.get("chat") or {}).get("id")
    user = person(c, cfg, cq.get("from") or {})
    note = ""
    try:
        if not user or chat_id is None:
            raise ValueError("this account is disabled")
        ch = _chat(c.out, chat_id)
        act = (ch.get("keys") or {}).get(str(cq.get("data") or "")[2:])
        if not act:
            raise ValueError("this button is too old: ask again")
        t = act.get("t")
        if t in ("action", "text"):
            _clear(c, chat_id, m)
            turn(c, chat_id, user, act.get("text") or "", act.get("a") if t == "action" else None)
            note = "ok"
        elif t == "setting":
            store = _store(c, user)
            s = store.load(session_of(c, user, chat_id))
            for k, v in (act.get("set") or {}).items():
                if k == "allow_vlm":
                    store.set_vision(s, v)
                else:
                    s["settings"][k] = v
            store.save(s)
            _clear(c, chat_id, m)
            note = "saved"
        elif t == "allow":
            _, tools, _, _ = c.chat_parts(user, ch.get("sid"))
            tools.allow(act["g"], [int(act["i"])], act["kind"], bool(act["allow"]))
            back = {"t": "allow", "g": act["g"], "i": act["i"], "kind": act["kind"], "allow": not act["allow"]}
            telegram._call(_tok(c), "editMessageReplyMarkup", {"chat_id": chat_id, "message_id": m["message_id"], "reply_markup": {"inline_keyboard": [[
                {"text": "Take it back" if act["allow"] else "Use it anyway", "callback_data": "c:" + _key(c.out, chat_id, back)}]]}}, timeout=30)
            note = "used anyway: cutting it again" if act["allow"] else "taken back"
            follow(c, chat_id, user, ch.get("sid"))
        elif t == "recut":
            n = int(str(act["g"]).lstrip("G"))
            pl.recut_check(c.out, n)
            c.submit(lambda: pl.recut(c.out, n, c.cfg, c.pace, by=user["id"]))
            _clear(c, chat_id, m)
            note = "cutting the sheet"
            follow(c, chat_id, user, ch.get("sid"))
        elif t == "models":
            models_card(c, chat_id, user, m.get("message_id"), act.get("open"))
        elif t == "model":
            set_model(c, user, chat_id, act["kind"], act["id"])
            models_card(c, chat_id, user, m.get("message_id"))
            note = f"{_model_label(act['kind'], act['id'])}"
    except (ValueError, KeyError, ToolError, pl.PipelineError, telegram.TelegramError) as e:
        note = f"could not: {e}"
    try:
        telegram._call(_tok(c), "answerCallbackQuery", {"callback_query_id": cq["id"], **({"text": note[:180]} if note else {})}, timeout=20)
    except Exception:
        pass


def _clear(c, chat_id, m: dict) -> None:
    """A question answered: its buttons go, so a second tap cannot send it twice."""
    if m.get("message_id"):
        try:
            telegram._call(_tok(c), "editMessageReplyMarkup", {"chat_id": chat_id, "message_id": m["message_id"], "reply_markup": {"inline_keyboard": []}}, timeout=20)
        except Exception:
            pass

