"""Tickets: every problem is one record of what happened, what the person meant, what the issue is and what should be fixed (docs/tickets_plan.md).
LangSmith is retired; this is where a failure or a Report goes.

The file store is the source of truth (`out/tickets/T###.json`, like `result.json`); Postgres mirrors it when it is up (`store/repo.py` `save_ticket`).
A ticket opens AUTOMATICALLY on a server error, a job that ends FAILED or a refused Telegram send (the same failure folds into one ticket by its
fingerprint, with a count), or BY HAND (Report on a batch, a sticker, a particle row, a chat message). The LOCAL model drafts the issue, a summary,
a proposed fix and 2-4 multiple-choice questions (free, rule 13); a draft that does not validate falls back to the preset questions of the issue, so the
person always gets questions and never an error. Questions never block anything: each can be skipped."""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from pathlib import Path

from ..runtime import atomic
from .ticket_models import ISSUES, TicketDraft, TicketQuestion

_LOCK = threading.RLock()
STATUSES = ("open", "answered", "replied", "fixed", "wont_fix")      # replied: an admin answered a support ticket and waits for the person (flow/support.py)

PRESET = {
    "wrong_result": [("What was wrong with the result?", ["the picture", "the animation", "the wrong sticker or batch", "the text or names"]),
                     ("What did you expect?", ["the same subject, better drawn", "a different pose or action", "what I asked for, word for word", "nothing: I clicked by mistake"])],
    "crash": [("What were you doing when it happened?", ["making a batch", "approving or rejecting", "particles", "chatting"]),
              ("Did it work when you tried again?", ["yes", "no", "I did not try again"])],
    "stuck_job": [("What did you see?", ["the spinner never ended", "it said failed", "credits were spent with no result", "nothing at all"]),
                  ("Was a price shown and accepted?", ["yes", "no", "I am not sure"])],
    "duplicate": [("What appears more than once?", ["a sticker", "a particle set", "a batch", "a pack"]),
                  ("Should the copies be merged or removed?", ["merged into one", "keep only the newest", "keep them all"])],
    "ui": [("Where is it?", ["Studio", "AI chat", "Library", "Settings"]),
           ("What is the problem?", ["something is hidden", "something is too big or too small", "a button does nothing", "it is confusing"])],
    "slow": [("What was slow?", ["a page opening", "a batch being made", "an animation", "the chat answering"]),
             ("How long did it take?", ["a few seconds", "about a minute", "several minutes", "it never finished"])],
    "spend": [("What happened to the credits?", ["spent with no result", "more than the price shown", "spent without asking", "I do not know"])],
    "other": [("How bad is it?", ["it blocks my work", "annoying, I can work around it", "just a note"])],
}


def tickets_dir(out: Path) -> Path:
    return Path(out) / "tickets"


def _path(out: Path, tid: str) -> Path:
    tid = str(tid).upper()
    if not re.fullmatch(r"T\d{3,}", tid):
        raise KeyError(f"no ticket {tid}")
    return tickets_dir(out) / f"{tid}.json"


def _next_id(out: Path) -> str:
    nums = [int(p.stem[1:]) for p in tickets_dir(out).glob("T[0-9]*.json") if p.stem[1:].isdigit()]
    return f"T{max(nums + [0]) + 1:03d}"


def read(out: Path, tid: str) -> dict:
    p = _path(out, tid)
    if not p.is_file():
        raise KeyError(f"no ticket {str(tid).upper()}")
    return json.loads(atomic.read_text(p))


def _write(out: Path, t: dict) -> dict:
    tickets_dir(out).mkdir(parents=True, exist_ok=True)
    t["updated"] = round(time.time(), 3)
    atomic.write_text(_path(out, t["id"]), json.dumps(t, indent=2, ensure_ascii=False))
    _mirror(out, t)
    return t


def _mirror(out: Path, t: dict) -> None:
    """Postgres keeps a copy when it is up (never raises: the file is the record)."""
    try:
        from ..store import sync
        sync.sync_ticket(out, t)
    except Exception:
        pass


def fingerprint(source: str, what: str, where: str = "") -> str:
    """The same failure, whatever its numbers: digits, hex ids and quoted values are blanked so G104 and G105 failing the same way fold together."""
    norm = re.sub(r"[0-9a-f]{8,}|\d+|'[^']*'|\"[^\"]*\"", "#", f"{source}|{where}|{what}".lower())
    return hashlib.sha1(norm.encode()).hexdigest()[:16]


def _preset(issue: str) -> list[dict]:
    return [TicketQuestion(text=q, choices=c).model_dump() for q, c in PRESET.get(issue, PRESET["other"])]


def _new(out: Path, *, source: str, issue: str, what: str, intent: str, context: dict, user: str | None, fp: str | None) -> dict:
    t = {"id": _next_id(out), "source": source, "at": round(time.time(), 3), "user": user, "status": "open", "issue": issue if issue in ISSUES else "other",
         "what_happened": what[:2000], "intent": intent[:2000], "context": context, "summary": what[:300], "proposed_fix": "", "questions": _preset(issue),
         "answers": [], "drafted_by": "preset", "fingerprint": fp, "count": 1, "last_at": round(time.time(), 3), "fixed_by": None, "history": []}
    t["history"].append({"ts": t["at"], "actor": user or "python", "decision": "OPEN", "source": source})
    return t


def open_auto(out: Path, *, source: str, issue: str, what: str, where: str = "", context: dict | None = None, user: str | None = None, draft: bool = True) -> dict:
    """A failure seen by the server. An OPEN ticket with the same fingerprint gets one more occurrence instead of a new ticket."""
    from ..obs.scrub import scrub_paths
    what = scrub_paths(str(what))
    fp = fingerprint(source, what, where)
    with _LOCK:
        for p in sorted(tickets_dir(out).glob("T[0-9]*.json"), reverse=True):
            try:
                t = json.loads(atomic.read_text(p))
            except (OSError, ValueError):
                continue
            if t.get("fingerprint") == fp and t.get("status") in ("open", "answered"):
                t["count"] = int(t.get("count") or 1) + 1
                t["last_at"] = round(time.time(), 3)
                t["history"].append({"ts": t["last_at"], "actor": "python", "decision": "AGAIN", "context": context or {}})
                return _write(out, t)
        t = _write(out, _new(out, source=source, issue=issue, what=what, intent="", context={"where": where, **(context or {})}, user=user, fp=fp))
    _tell(out, t)
    if draft:
        _draft_later(out, t["id"])
    return t


def report(out: Path, *, user: str, text: str, target: dict | None = None, draft: bool = True) -> dict:
    """A person's Report: their words are the intent; what happened is gathered from the target (a batch's last events, a chat's last turn, a set's state)."""
    target = target or {}
    ctx = gather(out, target)
    with _LOCK:
        t = _write(out, _new(out, source="report", issue="other", what=ctx.pop("_what", "") or text, intent=text, context={"target": target, **ctx}, user=user, fp=None))
    _tell(out, t)
    if draft:
        _draft_later(out, t["id"])
    return t


def open_support(out: Path, *, user: str, text: str, context: dict, draft: bool = True, issue: str = "other") -> dict:
    """The ticket of one support conversation (flow/support.py, which pings the admin itself, once): the person's words, the transcript and their
    recent problems as context, no multiple-choice questions (the conversation already asked them)."""
    with _LOCK:
        t = _new(out, source="support", issue=issue, what=text, intent=text, context=context, user=user, fp=None)
        t["questions"], t["conversation"], t["thread"] = [], context.get("conversation"), []
        t = _write(out, t)
    if draft:
        _draft_later(out, t["id"])
    return t


def gather(out: Path, target: dict) -> dict:
    """What happened around the target, read from the file store (never a provider)."""
    out, kind, ident = Path(out), target.get("kind"), str(target.get("id") or "")
    ctx: dict = {}
    try:
        if kind in ("generation", "sticker") and ident:
            gid = int(ident.upper().lstrip("G"))
            from . import pipeline
            r = pipeline.read_result(out, gid)
            ctx["batch"] = {"id": r["generation_id"], "prompt": r.get("prompt"), "stage": r.get("stage"), "error": r.get("error")}
            ev = pipeline.gen_dir(out, gid) / "events.jsonl"
            if ev.is_file():
                ctx["last_events"] = [json.loads(x) for x in ev.read_text(encoding="utf-8").splitlines()[-12:] if x.strip()]
            if kind == "sticker" and target.get("sticker"):
                i = int(str(target["sticker"]).upper().lstrip("S"))
                st = next((s for s in r["stickers"] if s["index"] == i), None)
                if st:
                    ctx["sticker"] = {k: st.get(k) for k in ("index", "key", "status", "reason", "anim_status")}
                    ctx["_what"] = f"{r['generation_id']}/S{i}: {st.get('status')}" + (f" ({st.get('reason')})" if st.get("reason") else "")
        elif kind == "particle_set" and ident:
            from . import particle_sets
            s = particle_sets.read(out, ident)
            ctx["particle_set"] = {"id": s["id"], "name": s.get("name"), "kind": (s.get("source") or {}).get("kind"), "cells": len(s.get("cells") or []),
                                   "renders": [{k: r.get(k) for k in ("id", "status", "warnings")} for r in s.get("renders") or []][-5:]}
        elif kind == "chat" and ident:
            p = out / "sessions" / f"{ident.upper()}.json"
            if p.is_file():
                s = json.loads(atomic.read_text(p))
                ctx["chat"] = [{"role": m.get("role"), "text": str(m.get("text") or "")[:400], "steps": [str(x.get("label") or x.get("text") or "")[:80] for x in (m.get("steps") or [])][-8:]}
                               for m in (s.get("messages") or [])[-4:]]
    except Exception as e:                      # gathering must never stop a report
        ctx["gather_error"] = str(e)[:200]
    return ctx


_SYSTEM = ("You file bug tickets for a sticker-making app. Answer ONLY with a JSON object: "
           '{"issue": one of ' + json.dumps(list(ISSUES)) + ', "summary": one sentence, "proposed_fix": one or two sentences for the developer, '
           '"questions": 2 to 3 objects {"text": a short question to the person, "choices": 2 to 4 short answers}}. Plain words, no markdown.')


def draft(out: Path, tid: str) -> dict:
    """Ask the LOCAL model (free) for the issue, a summary, a fix and the questions; keep the preset when it is down or its answer does not validate."""
    t = read(out, tid)
    try:
        from ..services import llm
        if llm.provider() != "local":
            raise RuntimeError("the local model is not the chosen engine")
        user_msg = llm.fence("TICKET", json.dumps({"what_happened": t["what_happened"], "intent": t["intent"], "context": t["context"]}, ensure_ascii=False)[:6000])
        text, meta = llm.complete(_SYSTEM, user_msg, provider_="local", max_tokens=700, timeout=45, temperature=0.2, json_mode=True)
        d = TicketDraft.model_validate(llm.extract_json(text))
    except Exception as e:
        with _LOCK:
            t = read(out, tid)
            t["draft_error"] = str(e)[:200]
            return _write(out, t)
    with _LOCK:
        t = read(out, tid)
        t.update(issue=d.issue, summary=d.summary, proposed_fix=d.proposed_fix, drafted_by=meta.get("model") or "local")
        if t.get("source") == "support":
            pass                                                     # a support ticket keeps its conversation, not questions
        elif d.questions and not t["answers"]:
            t["questions"] = [q.model_dump() for q in d.questions]
        elif not t["answers"]:
            t["questions"] = _preset(d.issue)
        t.pop("draft_error", None)
        return _write(out, t)


def _tell(out: Path, t: dict) -> None:
    """On the office LAN a new ticket is one line in Haitham's Telegram bot (services/admin_bot.py), in the background: a report never waits for Telegram."""
    import os
    if os.environ.get("MIRSAL_LAN", "").strip() not in ("1", "true", "yes", "on"):
        return
    from ..services import admin_bot
    threading.Thread(target=lambda: _safe(admin_bot.notify_ticket, out, t), daemon=True).start()


def _draft_later(out: Path, tid: str) -> None:
    threading.Thread(target=lambda: _safe(draft, out, tid), daemon=True, name=f"ticket-draft-{tid}").start()


def _safe(fn, *a):
    try:
        fn(*a)
    except Exception:
        pass


def answer(out: Path, tid: str, question: int, choice: str | None = None, text: str | None = None, user: str = "local") -> dict:
    with _LOCK:
        t = read(out, tid)
        if not 0 <= question < len(t["questions"]):
            raise ValueError(f"no question {question} on {t['id']}")
        q = t["questions"][question]
        if choice is not None and choice not in q["choices"]:
            raise ValueError("that is not one of the choices")
        if choice is None and not (text or "").strip():
            raise ValueError("choose an answer or write one")
        t["answers"] = [a for a in t["answers"] if a["question"] != question] + [{"question": question, "choice": choice, "text": (text or "").strip() or None, "by": user,
                                                                               "ts": round(time.time(), 3)}]
        if t["status"] == "open" and len(t["answers"]) >= len(t["questions"]):
            t["status"] = "answered"
        t["history"].append({"ts": round(time.time(), 3), "actor": user, "decision": "ANSWER", "question": question})
        return _write(out, t)


def set_status(out: Path, tid: str, status: str, fixed_by: str | None = None, user: str = "local") -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {', '.join(STATUSES)}")
    with _LOCK:
        t = read(out, tid)
        t["status"], t["fixed_by"] = status, (fixed_by or t.get("fixed_by"))
        t["history"].append({"ts": round(time.time(), 3), "actor": user, "decision": status.upper(), "fixed_by": fixed_by})
        return _write(out, t)


def listing(out: Path, *, status: str | None = None, user: str | None = None) -> list[dict]:
    """Newest first; `user` keeps only that person's own reports and the automatic tickets of their requests."""
    rows = []
    for p in sorted(tickets_dir(out).glob("T[0-9]*.json"), reverse=True):
        try:
            t = json.loads(atomic.read_text(p))
        except (OSError, ValueError):
            continue
        if status and t.get("status") != status:
            continue
        if user and t.get("user") != user:
            continue
        rows.append({k: t.get(k) for k in ("id", "source", "at", "last_at", "user", "status", "issue", "summary", "count", "fixed_by")}
                    | {"open_questions": max(0, len(t.get("questions") or []) - len(t.get("answers") or []))})
    return rows


def patch(out: Path, tid: str, by: str, decision: str, **fields) -> dict:
    """Set a few fields and record why, in one locked write (the support flow's links: conversation, faq, pinged)."""
    with _LOCK:
        t = read(out, tid)
        t.update(fields)
        t["history"].append({"ts": round(time.time(), 3), "actor": by, "decision": decision, **{k: v for k, v in fields.items() if isinstance(v, (str, int, bool)) or v is None}})
        return _write(out, t)


def add_message(out: Path, tid: str, role: str, by: str, text: str, client_id: str | None = None) -> tuple[dict, dict]:
    """One line of the ticket's thread (`role`: admin or user). A retried request with the same `client_id` adds nothing and returns the first line."""
    if role not in ("admin", "user"):
        raise ValueError("role must be admin or user")
    text = str(text or "").strip()
    if not text:
        raise ValueError("write something first")
    with _LOCK:
        t = read(out, tid)
        thread = t.setdefault("thread", [])
        if client_id:
            old = next((m for m in thread if m.get("client_id") == client_id), None)
            if old:
                return t, old
        m = {"n": len(thread) + 1, "role": role, "by": by, "text": text[:4000], "ts": round(time.time(), 3), "client_id": client_id}
        thread.append(m)
        t["history"].append({"ts": m["ts"], "actor": by, "decision": "REPLY" if role == "admin" else "USER_REPLY", "n": m["n"]})
        return _write(out, t), m
