#!/usr/bin/env python3
"""Build the Mirsal Builder Excalidraw diagrams (01-07) from box/edge lists.

Regenerate:  python3 build.py
Validates every file after writing: unique ids, bindings point both ways,
no box-box overlap, per-file counts. See diagram-prompt.md for the look spec.
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).parent

BOX_W, BOX_H = 280, 110
COL_DX, ROW_DY = 360, 180
OX, OY = 80, 150  # origin of grid (col 0, row 0); title lives above

AREAS = {
    "screen": ("#e7f5ff", "#1971c2"),
    "engine": ("#ebfbee", "#2f9e44"),
    "ai": ("#f3f0ff", "#6741d9"),
    "paid": ("#fff4e6", "#e8590c"),
    "store": ("#f8f9fa", "#495057"),
    "gate": ("#fff9db", "#f08c00"),
    "check": ("#fff5f5", "#e03131"),
    "planned": ("#f1f3f5", "#868e96"),
}
FRAME_BG, FRAME_STROKE = "#f8f9fa", "#ced4da"
INK = "#1e1e1e"

_rng = random.Random(20261004)
_uid = 0


def nid(prefix):
    global _uid
    _uid += 1
    return f"{prefix}_{_uid:03d}"


def base_elem(eid, etype, x, y, w, h, stroke, bg, style="solid", roundness=None):
    return {
        "id": eid, "type": etype, "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": style,
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": roundness, "seed": _rng.randint(0, 2**31 - 1),
        "version": 1, "versionNonce": _rng.randint(0, 2**31 - 1),
        "isDeleted": False, "boundElements": [], "updated": 1,
        "link": None, "locked": False,
    }


def free_text(eid, x, y, w, h, s, size, align="left"):
    el = base_elem(eid, "text", x, y, w, h, INK, "transparent")
    el.update({
        "text": s, "originalText": s, "fontSize": size, "fontFamily": 5,
        "textAlign": align, "verticalAlign": "top", "lineHeight": 1.25,
        "autoResize": True, "containerId": None, "baseline": size,
    })
    return el


def make_box(key, col, row, area, title, subtitle):
    """A 280x110 rounded box with two bound texts (title 22, subtitle 16)."""
    bg, stroke = AREAS[area]
    style = "dashed" if area == "planned" else "solid"
    x, y = OX + col * COL_DX, OY + row * ROW_DY
    bid = f"box_{key}"
    box = base_elem(bid, "rectangle", x, y, BOX_W, BOX_H, stroke, bg,
                    style, roundness={"type": 3})
    t1 = base_elem(f"txt_{key}_t", "text", x + 10, y + 16, BOX_W - 20, 40,
                   INK, "transparent")
    t1.update({
        "text": title, "originalText": title, "fontSize": 22, "fontFamily": 5,
        "textAlign": "center", "verticalAlign": "middle", "lineHeight": 1.25,
        "autoResize": True, "containerId": bid, "baseline": 22,
    })
    t2 = base_elem(f"txt_{key}_s", "text", x + 10, y + 62, BOX_W - 20, 36,
                   INK, "transparent")
    t2.update({
        "text": subtitle, "originalText": subtitle, "fontSize": 16,
        "fontFamily": 5, "textAlign": "center", "verticalAlign": "middle",
        "lineHeight": 1.25, "autoResize": True, "containerId": bid,
        "baseline": 16,
    })
    box["boundElements"] = [{"type": "text", "id": t1["id"]},
                            {"type": "text", "id": t2["id"]}]
    return box, t1, t2


def box_anchor(box, other, start=True):
    """The point facing the other box: the side middle for a neighbour on the
    same row (left or right), else the bottom middle (start) / top middle (end),
    so every inter-row arrow runs downward."""
    same_row = abs((box["y"] + BOX_H / 2) - (other["y"] + BOX_H / 2)) < 1
    if same_row:
        if other["x"] > box["x"]:
            return (box["x"] + BOX_W, box["y"] + BOX_H / 2)
        return (box["x"], box["y"] + BOX_H / 2)
    if start:
        return (box["x"] + BOX_W / 2, box["y"] + BOX_H)
    return (box["x"] + BOX_W / 2, box["y"])


ARROW_STYLE = {
    "fwd": (INK, "solid", None),
    "back": ("#e03131", "solid", -100),
    "advise": ("#f08c00", "solid", None),
    "side": (INK, "solid", 80),
    "skip": (INK, "solid", -80),
    "return": (INK, "solid", -100),
    "deny": ("#e03131", "solid", None),
    "fallback": ("#868e96", "dashed", None),
}


def make_arrow(key, boxes, frm, to, label, kind="fwd"):
    b1, b2 = boxes[frm], boxes[to]
    (x1, y1), (x2, y2) = box_anchor(b1, b2, True), box_anchor(b2, b1, False)
    dx, dy = x2 - x1, y2 - y1
    color, style, arch = ARROW_STYLE[kind]
    aid = f"arr_{key}"
    if arch is not None:
        mx, my = dx / 2, arch  # curved arrows arch away from the straight line
        pts = [[0, 0], [mx, my], [dx, dy]]
        lx, ly = x1 + mx, y1 + my - 12
    else:
        pts = [[0, 0], [dx, dy]]
        lx, ly = x1 + dx / 2 - 75, y1 + dy / 2 - 12
    ar = base_elem(aid, "arrow", x1, y1, 0, 0, color, "transparent",
                   roundness={"type": 2})
    ar.update({
        "points": pts,
        "startBinding": {"elementId": b1["id"], "focus": 0, "gap": 8},
        "endBinding": {"elementId": b2["id"], "focus": 0, "gap": 8},
        "startArrowhead": None, "endArrowhead": "arrow",
    })
    lab = base_elem(f"lab_{key}", "text", lx, ly, 150, 24, color,
                    "transparent")
    lab.update({
        "text": label, "originalText": label, "fontSize": 15, "fontFamily": 5,
        "textAlign": "center", "verticalAlign": "middle", "lineHeight": 1.25,
        "autoResize": True, "containerId": aid, "baseline": 15,
    })
    ar["boundElements"] = [{"type": "text", "id": lab["id"]}]
    b1["boundElements"].append({"type": "arrow", "id": aid})
    b2["boundElements"].append({"type": "arrow", "id": aid})
    return ar, lab


def make_frame(key, c0, r0, c1, r1, label):
    x = OX + c0 * COL_DX - 24
    y = OY + r0 * ROW_DY - 64
    w = (c1 - c0) * COL_DX + BOX_W + 48
    h = (r1 - r0) * ROW_DY + BOX_H + 84
    fr = base_elem(f"frame_{key}", "rectangle", x, y, w, h,
                   FRAME_STROKE, FRAME_BG, roundness={"type": 3})
    fr["strokeWidth"] = 1
    return fr, free_text(f"frlab_{key}", x + 12, y + 10, w - 24, 30,
                         label, 20)


def build_file(name, title, boxes_spec, edges_spec, frames_spec, legend):
    boxes, texts = {}, []
    for key, col, row, area, t, sub in boxes_spec:
        box, t1, t2 = make_box(key, col, row, area, t, sub)
        boxes[key] = box
        texts += [t1, t2]
    arrows, labels = [], []
    for i, (frm, to, label, kind) in enumerate(edges_spec):
        ar, lab = make_arrow(f"{name}_{i}", boxes, frm, to, label, kind)
        arrows += [ar]
        labels += [lab]
    frames = []
    for key, c0, r0, c1, r1, label in frames_spec:
        fr, fl = make_frame(key, c0, r0, c1, r1, label)
        frames += [fr, fl]
    max_x = max(b["x"] + b["width"] for b in boxes.values())
    max_y = max(b["y"] + b["height"] for b in boxes.values())
    legend_box = base_elem(f"legend_{name}", "rectangle", max_x - 340,
                           max_y + 40, 340, 40 + 22 * len(legend),
                           "#868e96", "#f1f3f5", roundness={"type": 3})
    ltext = "\n".join(legend)
    lt = base_elem(f"legend_{name}_t", "text", max_x - 330, max_y + 50,
                   320, 22 * len(legend), INK, "transparent")
    lt.update({
        "text": ltext, "originalText": ltext, "fontSize": 14, "fontFamily": 5,
        "textAlign": "left", "verticalAlign": "top", "lineHeight": 1.25,
        "autoResize": True, "containerId": legend_box["id"], "baseline": 14,
    })
    legend_box["boundElements"] = [{"type": "text", "id": lt["id"]}]
    elements = ([free_text(f"title_{name}", OX, 40, 900, 50, title, 36)]
                + frames + list(boxes.values()) + texts + arrows + labels
                + [legend_box, lt])
    doc = {"type": "excalidraw", "version": 2,
           "source": "https://excalidraw.com", "elements": elements,
           "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20},
           "files": {}}
    path = HERE / f"{name}.excalidraw"
    path.write_text(json.dumps(doc, indent=1) + "\n")
    return path, doc


LEGEND = ["🟦 screens  🟩 engine / flow  🟪 AI / agent",
          "🟧 paid providers  ⬜ storage  🟨 human gates",
          "🟥 blocks / checks  → flow  ⇠ use it anyway"]

LEGENDS = {
    "03-ai-chat-turn": LEGEND + ["⇢ dashed grey = polling fallback"],
    "07-office": ["👑 owner: everything · admin: people · member: own work + Trending",
                  "🟦 screens  🟩 jobs  🟨 gates  🟧 Telegram  ⬜ storage",
                  "→ flow  ⇠ tap / return path"],
}


DIAGRAMS = {
    "01-overview": (
        "Mirsal Builder at a glance",
        [
            ("chat", 0, 0, "screen", "💬 AI chat", "memory, agent, cards"),
            ("studio", 1, 0, "screen", "🎨 Studio", "explicit controls, gates"),
            ("library", 2, 0, "screen", "📚 Library", "packs, search, send"),
            ("create", 3, 0, "screen", "➕ Create", "photo or text sticker"),
            ("settings", 4, 0, "screen", "🔧 Settings · 👥 Users", "paths, keys · people, usage"),
            ("adapter", 1, 1, "engine", "🔁 adapter", "old routes, same bytes"),
            ("fastapi", 2, 1, "engine", "🚀 FastAPI", "uvicorn, same JSON bytes"),
            ("native", 3, 1, "engine", "🧩 native routes", "stream, tickets, accounts, Trending"),
            ("tickets", 4, 1, "engine", "🎫 tickets", "errors + Reports, AI draft"),
            ("accounts", 5, 1, "store", "🔐 accounts", "@nadi.ae, sessions, roles"),
            ("engine", 0, 2, "engine", "⚙️ engine", "pure, no I/O"),
            ("flow", 1, 2, "engine", "🚦 flow", "pipeline, gates G1–G5"),
            ("gen", 2, 2, "engine", "💰 generation", "Higgsfield jobs, credits"),
            ("agent", 3, 2, "ai", "🧠 agent", "LangGraph over Studio fns"),
            ("store", 4, 2, "store", "🗄️ store", "Postgres mirror, pool"),
            ("svc", 5, 2, "engine", "🔌 services", "llm, embed, telegram"),
            ("banana", 0, 3, "paid", "🍌 Nano Banana", "sheets, 2k image"),
            ("kling", 1, 3, "paid", "🎬 Kling v3.0", "video, pro, 3 s"),
            ("lmstudio", 2, 3, "ai", "🤖 LM Studio", "chat, vision, free"),
            ("openai", 3, 3, "paid", "✨ OpenAI", "enhancer fallback"),
            ("pg", 4, 3, "store", "🗄️ Postgres", "rows mirror out/"),
            ("redis", 5, 3, "store", "⚡ Redis", "disposable cache"),
            ("tg", 6, 3, "paid", "✈️ Telegram", "packs go out"),
            ("adminbot", 7, 3, "paid", "🛡️ admin bot", "Haitham's taps only"),
            ("out", 8, 3, "store", "📁 out/", "source of truth"),
        ],
        [
            ("chat", "fastapi", "JSON", "fwd"), ("studio", "fastapi", "JSON", "fwd"),
            ("library", "fastapi", "JSON", "fwd"), ("create", "fastapi", "JSON", "fwd"),
            ("settings", "fastapi", "JSON", "fwd"),
            ("settings", "accounts", "People", "fwd"),
            ("fastapi", "adapter", "old routes", "fwd"),
            ("fastapi", "native", "new routes", "fwd"),
            ("adapter", "engine", "calls", "fwd"), ("adapter", "flow", "calls", "fwd"),
            ("adapter", "gen", "calls", "fwd"), ("adapter", "agent", "calls", "fwd"),
            ("adapter", "store", "calls", "fwd"), ("adapter", "svc", "calls", "fwd"),
            ("native", "tickets", "ticket routes", "fwd"),
            ("native", "agent", "chat stream", "fwd"),
            ("tickets", "store", "ticket rows", "fwd"),
            ("accounts", "adminbot", "cards out", "fwd"),
            ("adminbot", "accounts", "taps in", "return"),
            ("flow", "engine", "runs", "fwd"),
            ("agent", "gen", "tools", "fwd"),
            ("gen", "banana", "sheet job", "fwd"),
            ("gen", "kling", "video job", "fwd"),
            ("agent", "lmstudio", "chat, vision", "fwd"),
            ("gen", "openai", "enhancer", "fwd"),
            ("store", "pg", "mirrors", "fwd"),
            ("store", "redis", "caches", "fwd"),
            ("engine", "out", "writes", "fwd"),
            ("svc", "tg", "sends pack", "fwd"),
        ],
        [("screens", 0, 0, 4, 0, "Screens"),
         ("app", 0, 1, 5, 2, "App (FastAPI + engine)"),
         ("outside", 0, 3, 8, 3, "Outside world")],
    ),
    "02-golden-path": (
        "How a sticker pack is made",
        [
            ("req", 0, 0, "screen", "📝 request", "text, image, chat"),
            ("plan", 1, 0, "gate", "✅ G1 plan", "1–5 tags, margin"),
            ("sheet", 2, 0, "paid", "🍌 sheet", "Nano Banana, 2k"),
            ("cuts", 3, 0, "engine", "✂️ cuts + checks", "Python blocks bad cells"),
            ("stills", 4, 0, "gate", "✅ G2 stills", "you approve"),
            ("vsheet", 5, 0, "gate", "✅ G3 video sheet", "approved stickers only"),
            ("kling", 5, 1, "paid", "🎬 Kling video", "v3.0 pro"),
            ("fcheck", 4, 1, "check", "🛑 frame check", "every frame boundary"),
            ("anims", 3, 1, "gate", "✅ G4 animations", "you approve"),
            ("pack", 2, 1, "gate", "✅ G5 pack", "G2 AND G4"),
            ("tg", 1, 1, "paid", "✈️ Telegram", "set goes out"),
            ("verifier", 0, 1, "check", "🛑 verifier", "44 checks, 9 stages"),
            ("regen", 6, 0, "engine", "🔁 regen 1×1", "same engine again"),
        ],
        [
            ("req", "plan", "plan", "fwd"),
            ("plan", "sheet", "prompt", "fwd"),
            ("sheet", "cuts", "grid cut", "fwd"),
            ("cuts", "stills", "stills", "fwd"),
            ("stills", "vsheet", "approved", "fwd"),
            ("vsheet", "kling", "video job", "fwd"),
            ("kling", "fcheck", "frames", "fwd"),
            ("fcheck", "anims", "animations", "fwd"),
            ("anims", "pack", "pack", "fwd"),
            ("pack", "tg", "send", "fwd"),
            ("cuts", "stills", "Use it anyway", "back"),
            ("fcheck", "anims", "Use it anyway", "back"),
            ("stills", "regen", "reject → regen", "fwd"),
            ("regen", "stills", "new S#", "back"),
            ("verifier", "cuts", "checks", "advise"),
            ("verifier", "fcheck", "checks", "advise"),
        ],
        [("path", 0, 0, 6, 1, "Golden path (gates need a human)")],
    ),
    "03-ai-chat-turn": (
        "What happens when someone types in the chat",
        [
            ("msg", 0, 0, "screen", "💬 message", "text + selected stickers"),
            ("resolver", 1, 0, "ai", "🎯 resolver", "deterministic rules first"),
            ("memory", 1, 1, "ai", "🧠 memory", "subjects, taste, focus"),
            ("nodes", 2, 0, "ai", "🧠 LangGraph", "understand → intent → finish"),
            ("tools", 3, 0, "ai", "⚙️ tools", "plan, create, animate, review"),
            ("studiofns", 4, 0, "engine", "🎨 Studio fns", "same engine calls"),
            ("price", 5, 0, "gate", "💳 price card", "Create / Not yet"),
            ("steps", 5, 1, "store", "📋 step trace", "steps as they happen"),
            ("reply", 4, 1, "screen", "💬 reply + cards", "carousel, chips"),
            ("stream", 6, 1, "engine", "📡 /stream", "turn events, then done"),
            ("sessions", 3, 1, "store", "💾 sessions", "files, Postgres, Redis"),
            ("vision", 2, 1, "ai", "👁️ vision judge", "pre-review, never approves"),
        ],
        [
            ("msg", "resolver", "text", "fwd"),
            ("resolver", "memory", "reads memory", "fwd"),
            ("resolver", "nodes", "intent", "fwd"),
            ("nodes", "tools", "intent node", "fwd"),
            ("tools", "studiofns", "same functions", "fwd"),
            ("studiofns", "price", "estimate", "fwd"),
            ("price", "steps", "go-ahead", "fwd"),
            ("steps", "stream", "turn events", "fwd"),
            ("stream", "reply", "SSE stream", "side"),
            ("reply", "stream", "polling fallback", "fallback"),
            ("reply", "sessions", "writes back", "fwd"),
            ("reply", "memory", "feedback, taste", "return"),
            ("nodes", "vision", "pre-review", "fwd"),
            ("vision", "steps", "reasons", "advise"),
        ],
        [("turn", 0, 0, 6, 1, "One turn (spend needs a go-ahead)")],
    ),
    "04-paid-generation": (
        "A paid job end to end",
        [
            ("price", 0, 0, "gate", "💳 price shown", "quote first, always"),
            ("go", 1, 0, "gate", "🙋 go-ahead", "your click spends"),
            ("credits", 2, 0, "gate", "💳 your credits", "check, reserve · 402 short"),
            ("ticket", 3, 0, "store", "🎫 ticket first", "jobs, tasks, Postgres"),
            ("cli", 4, 0, "paid", "🍌 Higgsfield CLI", "create, no wait"),
            ("wait", 5, 0, "paid", "⏳ wait + fetch", "download result"),
            ("batch", 6, 0, "engine", "📦 batch", "stills, attach, slice"),
            ("settle", 7, 0, "engine", "⚖️ settle", "real cost replaces reserve"),
            ("idem", 1, 1, "store", "🔑 idempotency", "same key, first answer"),
            ("req", 2, 1, "check", "📨 Request credits", "ask Haitham, nothing auto"),
            ("cap", 3, 1, "check", "🛑 daily cap", "refused before spend"),
            ("recovery", 4, 1, "engine", "🛟 recovery", "check, continue, retry"),
            ("parallel", 5, 1, "engine", "🔀 3 in flight", "parallel, cap counts"),
            ("ledger", 7, 1, "store", "📒 ledger", "every call a line"),
        ],
        [
            ("price", "go", "quote", "fwd"),
            ("go", "credits", "reserve", "fwd"),
            ("go", "ticket", "owner: no balance", "skip"),
            ("go", "idem", "key per click", "fwd"),
            ("credits", "ticket", "ticket first", "fwd"),
            ("credits", "req", "402 · Request credits", "deny"),
            ("credits", "cap", "also daily cap", "fwd"),
            ("ticket", "cli", "job id", "fwd"),
            ("cli", "wait", "provider works", "fwd"),
            ("wait", "batch", "follow-up", "fwd"),
            ("ticket", "parallel", "≤ 3 waiters", "fwd"),
            ("batch", "settle", "job ended", "fwd"),
            ("settle", "ledger", "ledger line", "fwd"),
            ("cap", "ticket", "counts in-flight", "back"),
            ("recovery", "ticket", "same ticket, free", "back"),
            ("recovery", "price", "Retry · SPENDS", "back"),
        ],
        [("job", 0, 0, 7, 1, "Ticket first: a crash never pays twice")],
    ),
    "05-particles": (
        "Particles for a sticker",
        [
            ("sticker", 0, 0, "screen", "📎 sticker", "library owns the set"),
            ("newver", 1, 0, "engine", "🆕 New version", "draft row, enters editor"),
            ("src_self", 2, 0, "engine", "✂️ Sprites from sticker", "free, slices you pick"),
            ("src_ai", 2, 1, "paid", "🍌 AI image sprites", "Nano Banana, priced quote"),
            ("src_kling", 2, 2, "paid", "🎬 Kling animated", "text-only, from scratch"),
            ("sim", 3, 2, "engine", "✨ simulator", "Energy Float Swirl Size"),
            ("save", 4, 2, "store", "💾 Save", "draft becomes next row"),
            ("render", 5, 2, "engine", "🎞️ Render", "512 WEBM, Telegram limits"),
            ("add", 6, 2, "gate", "📦 Add to pack", "burst affirmed, In pack ✓"),
            ("saveas", 4, 3, "store", "🧬 Save as new", "same sprites, edited motion"),
            ("rows", 5, 3, "store", "🗂️ rows v1, v2…", "oldest first, under sticker"),
            ("echo", 3, 3, "ai", "📣 Echo test", "free preview in chat"),
        ],
        [
            ("sticker", "newver", "opens draft", "fwd"),
            ("newver", "src_self", "pick a source", "fwd"),
            ("newver", "src_ai", "pick a source", "fwd"),
            ("newver", "src_kling", "pick a source", "fwd"),
            ("src_self", "sim", "sprites in", "fwd"),
            ("src_ai", "sim", "sprites in", "fwd"),
            ("src_kling", "sim", "clips in", "fwd"),
            ("sim", "save", "tune, then save", "fwd"),
            ("sim", "echo", "preview, free", "fwd"),
            ("save", "render", "render it", "fwd"),
            ("save", "saveas", "reopen, slow down", "fwd"),
            ("save", "rows", "row lives here", "fwd"),
            ("saveas", "rows", "new row, same art", "fwd"),
            ("render", "add", "affirm in pack", "fwd"),
        ],
        [("sources", 2, 0, 2, 2, "Three equal sources"),
         ("rowsfr", 4, 2, 6, 3, "Rows, render, pack")],
    ),
    "06-data": (
        "Where things live",
        [
            ("batches", 0, 0, "store", "📦 batches G###", "result.json, slices, sheets"),
            ("library", 1, 0, "store", "📚 library", "packs, files, pool source"),
            ("particles", 2, 0, "store", "✨ particle sets P###", "owned by stickers, rows"),
            ("jobsf", 3, 0, "store", "🎫 jobs J### + tasks", "ticket first, ledger lines"),
            ("sessionsf", 4, 0, "store", "💬 chats S###", "sessions, memory, feedback"),
            ("ticketsf", 5, 0, "store", "🎫 tickets T###", "files, git-ignored"),
            ("usersf", 6, 0, "store", "👥 users.json", "hashes, sessions, roles"),
            ("trendf", 7, 0, "store", "📈 trending.json", "shares, likes, comments"),
            ("trash", 0, 1, "store", "🗑️ trash", "removed batches, packs, sets"),
            ("pg_gen", 1, 1, "store", "🗄️ generations", "plan, owner, group, relation"),
            ("pg_stickers", 2, 1, "store", "🏷️ stickers + index", "tags, vectors, pool"),
            ("pg_tasks", 3, 1, "store", "🔗 tasks + jobs", "external id join"),
            ("pg_sess", 4, 1, "store", "💬 sessions table", "chats, feedback, refs"),
            ("reqf", 6, 1, "store", "📨 account_requests", "signup, password, credits"),
            ("groups", 1, 2, "store", "🧬 batch groups", "root + variations family"),
            ("pg_reviews", 2, 2, "store", "✅ reviews", "every decision a row"),
            ("redis", 3, 2, "store", "⚡ Redis cache", "disposable, hot copies"),
            ("pg_calls", 4, 2, "store", "📒 model_calls", "every call and cost"),
            ("pg_tickets", 5, 2, "store", "🎫 tickets table", "mirror of the files"),
        ],
        [
            ("batches", "trash", "Remove → trash", "fwd"),
            ("batches", "pg_gen", "result.json mirrors", "fwd"),
            ("library", "particles", "owns sets", "fwd"),
            ("library", "pg_stickers", "approved indexed", "fwd"),
            ("jobsf", "pg_tasks", "ticket + cost", "fwd"),
            ("sessionsf", "pg_sess", "chat rows", "fwd"),
            ("pg_gen", "groups", "group_id family", "fwd"),
            ("pg_gen", "pg_reviews", "history → rows", "fwd"),
            ("pg_stickers", "redis", "vec cache", "fwd"),
            ("pg_sess", "redis", "hot copy", "fwd"),
            ("pg_tasks", "pg_calls", "ledger mirrors", "fwd"),
            ("pg_sess", "pg_calls", "ledger lines", "fwd"),
            ("ticketsf", "pg_tickets", "mirror", "fwd"),
            ("usersf", "reqf", "their requests", "fwd"),
            ("usersf", "trendf", "likes + comments", "fwd"),
            ("usersf", "pg_sess", "owns chats", "fwd"),
        ],
        [("files", 0, 0, 7, 0, "files — out/ is truth, some git-ignored"),
         ("pg", 1, 1, 4, 2, "Postgres mirrors it"),
         ("acct", 5, 1, 6, 2, "accounts, tickets, gallery")],
    ),
    "07-office": (
        "The office LAN",
        [
            ("colleague", 0, 0, "screen", "👩‍💼 colleague", "from their own machine"),
            ("signup", 1, 0, "screen", "🔐 sign up", "HTTPS, @nadi.ae"),
            ("waiting", 2, 0, "gate", "⏳ Waiting approval", "pending, nothing else works"),
            ("forgot", 0, 1, "screen", "🔑 forgot password", "new password via Haitham"),
            ("tgcard", 2, 1, "paid", "✈️ Telegram admin", "Approve · Reject · Admin"),
            ("people", 3, 1, "screen", "👥 Users > People", "approve, edit, credits, usage"),
            ("approved", 3, 2, "gate", "✅ approved", "10 credits, own work"),
            ("credits", 4, 2, "engine", "💳 paid job", "reserve, settle, refund"),
            ("reqcredits", 5, 2, "screen", "📨 Request credits", "nothing refills on its own"),
            ("trending", 4, 3, "screen", "📈 Trending gallery", "share, like, comment"),
            ("useflow", 5, 3, "store", "🧰 Use in workflow", "copy, or cover as reference"),
        ],
        [
            ("colleague", "signup", "joins", "fwd"),
            ("signup", "waiting", "applies", "fwd"),
            ("waiting", "tgcard", "card goes out", "fwd"),
            ("waiting", "people", "or dashboard", "fwd"),
            ("forgot", "tgcard", "reset card", "fwd"),
            ("tgcard", "approved", "tap Approve", "fwd"),
            ("people", "approved", "same apply", "fwd"),
            ("approved", "credits", "approved: 10 credits", "fwd"),
            ("credits", "reqcredits", "402 · Request", "fwd"),
            ("reqcredits", "tgcard", "Approve +10 · Ignore", "return"),
            ("credits", "trending", "Share", "fwd"),
            ("trending", "useflow", "copy to library", "fwd"),
        ],
        [("office", 0, 0, 5, 3, "Office LAN — built end to end")],
    ),
}


def validate(doc):
    errors = []
    els = doc["elements"]
    ids = [e["id"] for e in els]
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids")
    by_id = {e["id"]: e for e in els}
    for e in els:
        if e.get("containerId"):
            t = by_id.get(e["containerId"])
            if t is None:
                errors.append(f"{e['id']}: container {e['containerId']} missing")
            elif not any(b.get("id") == e["id"] for b in t["boundElements"]):
                errors.append(f"{e['id']}: target lists it not back")
        for end in ("startBinding", "endBinding"):
            b = e.get(end)
            if b:
                t = by_id.get(b["elementId"])
                if t is None:
                    errors.append(f"{e['id']}: {end} missing")
                elif not any(x.get("id") == e["id"]
                             for x in t["boundElements"]):
                    errors.append(f"{e['id']}: {end} not listed back")
    boxes = [e for e in els if e["id"].startswith("box_")]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if (a["x"] < b["x"] + b["width"] and b["x"] < a["x"] + a["width"]
                    and a["y"] < b["y"] + b["height"]
                    and b["y"] < a["y"] + a["height"]):
                errors.append(f"overlap: {a['id']} x {b['id']}")
    narrows = sum(1 for e in els if e["type"] == "arrow")
    return errors, len(boxes), narrows


def main():
    ok = True
    for name, (title, bs, es, fs) in DIAGRAMS.items():
        path, doc = build_file(name, title, bs, es, fs, LEGENDS.get(name, LEGEND))
        errors, nboxes, narrows = validate(doc)
        status = "OK" if not errors else f"FAIL {errors}"
        print(f"{path.name}: boxes={nboxes} arrows={narrows} {status}")
        ok = ok and not errors
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
