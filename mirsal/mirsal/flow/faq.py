"""The shared FAQ (docs/agent-and-chat.md "Support"): what the support agent may answer from, written from resolved tickets and published by an admin.

`out/faq/F###.json` is the record, mirrored to Postgres with the vector of its PUBLISHED text (migration 011). An entry is `draft` (never an answer),
`published` (an answer), or `archived`. A proposal for an entry that is already published is kept beside it as `pending` and only replaces the published
text when an admin publishes it; the text it replaced goes to `revisions`, so every published version is kept. `provenance` lists the tickets and
conversations an entry came from.

`propose_from_ticket` runs when a ticket is resolved: it looks for a published entry that already answers the question first (so the same fix becomes
a new revision of that entry, not a second entry), asks the LOCAL model (free) to write the reusable solution, falls back to the admin's own resolution
words when the model is down, and scrubs names, e-mails, ids, paths and secrets from everything it keeps. Text from a ticket or a person is data only."""
from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path

from ..runtime import atomic

_LOCK = threading.RLock()
STATUSES = ("draft", "published", "archived")
DUPLICATE = {"vector": 0.80, "lexical": 0.60}        # a published entry this close to the new question gets a revision instead of a twin


class FAQError(Exception):
    code = 400

    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code


def faq_dir(out: Path) -> Path:
    return Path(out) / "faq"


def _path(out: Path, fid: str) -> Path:
    fid = str(fid).upper()
    if not re.fullmatch(r"F\d{3,}", fid):
        raise KeyError(f"no FAQ entry {fid}")
    return faq_dir(out) / f"{fid}.json"


def _next_id(out: Path) -> str:
    nums = [int(p.stem[1:]) for p in faq_dir(out).glob("F[0-9]*.json") if p.stem[1:].isdigit()]
    return f"F{max(nums + [0]) + 1:03d}"


def read(out: Path, fid: str) -> dict:
    p = _path(out, fid)
    if not p.is_file():
        raise KeyError(f"no FAQ entry {str(fid).upper()}")
    return json.loads(atomic.read_text(p))


def _write(out: Path, f: dict, reindex: bool = False) -> dict:
    faq_dir(out).mkdir(parents=True, exist_ok=True)
    f["updated"] = round(time.time(), 3)
    atomic.write_text(_path(out, f["id"]), json.dumps(f, indent=2, ensure_ascii=False))
    if reindex:
        index(out, f)
    else:
        _mirror(out, f, None, None)
    return f


def _mirror(out: Path, f: dict, vec, model) -> None:
    try:
        from ..store import sync
        sync.sync_support(out, "faq", f, vec, model)
    except Exception:
        pass


def index(out: Path, f: dict, embedder="auto") -> bool:
    """Mirror the entry and, when it is published and the local model is up, its vector (cached by text, so publishing again costs nothing)."""
    vec, model = None, None
    from . import support_kb
    if f.get("status") == "published" and support_kb._pg(out):                   # a vector only matters where Postgres searches
        emb = support_kb._embedder(out) if embedder == "auto" else embedder
        if emb is not None:
            try:
                vec = emb([search_text(f)], "document")[0]
                model = getattr(emb, "model", "local")
            except Exception:
                vec = None
    _mirror(out, f, vec, model)
    return vec is not None


def search_text(f: dict) -> str:
    """What an entry is found by: its question and answer, and where it happens and what it looks like on screen (so the vision model's description of a
    person's screenshot finds the entry even when the person cannot name the problem)."""
    parts = [f.get("title") or "", f"Q: {f.get('question') or ''}", f"A: {f.get('answer') or ''}"]
    if f.get("screen"):
        parts.append(f"Screen: {f['screen']}")
    if f.get("looks_like"):
        parts.append(f"Looks like: {f['looks_like']}")
    return "\n".join(parts)


def _clean(text, limit: int, names=()) -> str:
    from ..obs.scrub import scrub_personal
    return scrub_personal(str(text or "").strip(), names)[:limit]


def public(f: dict) -> dict:
    """What anyone may read: the published text only (a draft or a pending proposal never leaves the admin's screen)."""
    if f.get("status") != "published":
        raise KeyError(f"no FAQ entry {f.get('id')}")
    return {k: f.get(k) for k in ("id", "title", "question", "answer", "screen", "looks_like", "revision", "updated")}


def listing(out: Path, status: str | None = None) -> list[dict]:
    rows = []
    for p in sorted(faq_dir(out).glob("F[0-9]*.json")):
        try:
            f = json.loads(atomic.read_text(p))
        except (OSError, ValueError):
            continue
        if status == "pending":
            if not (f.get("status") == "draft" or f.get("pending")):
                continue
        elif status and f.get("status") != status:
            continue
        rows.append({k: f.get(k) for k in ("id", "status", "title", "question", "revision", "updated", "category")} | {"pending": bool(f.get("pending")),
                                                                                                         "provenance": f.get("provenance") or []})
    return rows


def _event(f: dict, by: str, decision: str, **extra) -> None:
    f.setdefault("history", []).append({"ts": round(time.time(), 3), "actor": by, "decision": decision, **extra})


def propose(out: Path, *, title: str, question: str, answer: str, by: str, provenance: dict | None = None, target: str | None = None, names=()) -> dict:
    """A new draft, or (with `target`, a published entry) a pending revision of it. Everything kept is scrubbed."""
    prop = {"title": _clean(title, 120, names), "question": _clean(question, 600, names), "answer": _clean(answer, 4000, names)}
    if not prop["question"] or not prop["answer"]:
        raise FAQError("an FAQ entry needs a question and an answer")
    prov = [provenance] if provenance else []
    with _LOCK:
        if target:
            f = read(out, target)
            if f.get("status") == "published":
                f["pending"] = {**prop, "by": by, "at": round(time.time(), 3), "provenance": prov}
                f["provenance"] = (f.get("provenance") or []) + prov
                _event(f, by, "PROPOSE_REVISION", **(provenance or {}))
                return _write(out, f)
        f = {"id": _next_id(out), "status": "draft", **prop, "revision": 0, "revisions": [], "pending": None, "provenance": prov,
             "created": round(time.time(), 3), "history": []}
        _event(f, by, "PROPOSE", **(provenance or {}))
        return _write(out, f)


def edit(out: Path, fid: str, by: str, *, title=None, question=None, answer=None) -> dict:
    """An admin's edit: of the pending proposal when there is one, of the draft, or (on a published entry) a new pending proposal."""
    with _LOCK:
        f = read(out, fid)
        if f.get("status") == "archived":
            raise FAQError("an archived entry cannot be edited: publish a new one", 409)
        changes = {k: v for k, v in (("title", title), ("question", question), ("answer", answer)) if v is not None}
        changes = {k: _clean(v, {"title": 120, "question": 600, "answer": 4000}[k]) for k, v in changes.items()}
        if f.get("pending") is not None:
            f["pending"].update(changes)
        elif f.get("status") == "draft":
            f.update(changes)
        else:
            f["pending"] = {**{k: f.get(k) for k in ("title", "question", "answer")}, **changes, "by": by, "at": round(time.time(), 3), "provenance": []}
        _event(f, by, "EDIT", fields=sorted(changes))
        return _write(out, f)


def publish(out: Path, fid: str, by: str) -> dict:
    """Make the draft (or the pending revision) the published answer; the text it replaces is kept in `revisions`. Publishing twice changes nothing."""
    with _LOCK:
        f = read(out, fid)
        if f.get("status") == "archived":
            raise FAQError("an archived entry cannot be published", 409)
        if f.get("status") == "published" and not f.get("pending"):
            return f
        if f.get("pending"):
            p = f["pending"]
            if f.get("status") == "published":
                f.setdefault("revisions", []).append({k: f.get(k) for k in ("title", "question", "answer", "revision")} | {"replaced_at": round(time.time(), 3)})
            f.update(title=p.get("title") or f.get("title"), question=p.get("question") or f.get("question"), answer=p.get("answer") or f.get("answer"))
            f["pending"] = None
        if not (f.get("question") and f.get("answer")):
            raise FAQError("an FAQ entry needs a question and an answer")
        f["status"] = "published"
        f["revision"] = int(f.get("revision") or 0) + 1
        f["published_at"], f["published_by"] = round(time.time(), 3), by
        _event(f, by, "PUBLISH", revision=f["revision"])
        return _write(out, f, reindex=True)


def discard(out: Path, fid: str, by: str) -> dict:
    """Drop the pending proposal; a draft without a published text is archived."""
    with _LOCK:
        f = read(out, fid)
        if f.get("pending"):
            f["pending"] = None
        elif f.get("status") == "draft":
            f["status"] = "archived"
        _event(f, by, "DISCARD")
        return _write(out, f, reindex=True)


def archive(out: Path, fid: str, by: str) -> dict:
    with _LOCK:
        f = read(out, fid)
        f["status"] = "archived"
        _event(f, by, "ARCHIVE")
        return _write(out, f, reindex=True)


_SYSTEM = ("You write one entry of a help FAQ for a sticker-making app from a resolved support ticket. Write the REUSABLE solution for anyone with the same "
           "problem: no names, no e-mail addresses, no ids, no file paths, nothing about this one person. Answer ONLY with a JSON object "
           '{"title": at most 10 words, "question": the problem as a user would ask it, "answer": the solution in 2 to 6 plain sentences}. '
           "Use only what the ticket says; if it does not contain a solution, answer {\"answer\": \"\"}.")


def propose_from_ticket(out: Path, tid: str, by: str, complete=None) -> dict | None:
    """The FAQ proposal of one resolved ticket, once (the ticket keeps its id). None when there is nothing reusable to say."""
    from . import tickets as tk
    t = tk.read(out, tid)
    if t.get("faq"):
        try:
            return read(out, t["faq"])
        except KeyError:
            pass
    conv = None
    if t.get("conversation"):
        p = Path(out) / "support" / f"{t['conversation']}.json"
        if p.is_file():
            conv = json.loads(atomic.read_text(p))
    lines = []
    if conv:
        lines += [f"{m.get('role')}: {m.get('text')}" for m in conv.get("messages") or [] if m.get("text")]
    lines += [f"{m.get('role')}: {m.get('text')}" for m in t.get("thread") or [] if m.get("text")]
    resolution = next((m.get("text") for m in reversed(t.get("thread") or []) if m.get("role") == "admin" and m.get("text")), "") or ""
    question = (conv and next((m.get("text") for m in conv.get("messages") or [] if m.get("role") == "user"), None)) or t.get("intent") or t.get("summary") or ""
    names = [t.get("user"), (conv or {}).get("name")]
    title, answer = (t.get("summary") or question)[:80], resolution
    try:
        from ..services import llm
        ask = complete or (lambda s, u: llm.complete(s, u, provider_="local", max_tokens=600, timeout=60, temperature=0.2, json_mode=True))
        if complete is None and llm.provider() != "local":
            raise RuntimeError("the local model is not the chosen engine")
        text, _ = ask(_SYSTEM, llm.fence("TICKET", "\n".join(lines)[-6000:] or t.get("what_happened") or ""))
        d = llm.extract_json(text)
        if isinstance(d, dict) and str(d.get("answer") or "").strip():
            title, question, answer = str(d.get("title") or title), str(d.get("question") or question), str(d["answer"])
    except Exception:
        pass                                            # the admin's own resolution words stand in
    if not str(answer).strip() or not str(question).strip():
        return None
    from . import support_kb
    near, mode = support_kb.search_faq(out, question, k=1)
    target = near[0]["id"] if near and near[0]["score"] >= DUPLICATE[mode] else None
    f = propose(out, title=title, question=question, answer=answer, by=by, target=target, names=names,
                provenance={"ticket": t["id"], "conversation": t.get("conversation")})
    tk.patch(out, tid, by, "FAQ_PROPOSED", faq=f["id"])
    return f


# ---------- seed entries written as Markdown files (faq/<category>/<slug>.md; mirsal/local_eval/faq-seed-prompt.md says how they are written)
def parse_seed(text: str) -> dict:
    """A seed file: a `---` header of `key: value` lines (title, question, category, tags) and the answer as the body. ValueError when it is not one."""
    m = re.match(r"^\ufeff?---\s*\n(.*?)\n---\s*\n(.*)$", text.replace("\r\n", "\n"), re.S)
    if not m:
        raise ValueError("no --- header")
    head = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            head[k.strip().lower()] = v.strip().strip('"').strip("'")
    answer = m.group(2).strip()
    if not head.get("question") or not answer:
        raise ValueError("a seed needs a question and an answer")
    return {"title": head.get("title") or head["question"][:80], "question": head["question"], "answer": answer,
            "category": head.get("category") or "", "tags": [t.strip() for t in head.get("tags", "").strip("[]").split(",") if t.strip()],
            "screen": head.get("screen") or "", "looks_like": head.get("looks_like") or ""}


def import_seeds(out: Path, folder: Path, by: str = "local", publish: bool = False) -> dict:
    """Every `*.md` under `folder` becomes a draft (or, with `publish`, the owner's explicit choice, a published entry). Run again: an unchanged
    file changes nothing, a changed one updates its draft or proposes a revision of its published entry. Each entry remembers its seed path."""
    import hashlib
    folder = Path(folder)
    if not folder.is_dir():
        raise FAQError(f"no folder {folder}")
    by_seed = {}
    for row in listing(out):
        f = read(out, row["id"])
        if f.get("seed"):
            by_seed[f["seed"]["path"]] = f
    made, changed, same, bad = [], [], 0, []
    for p in sorted(folder.rglob("*.md")):
        rel = p.relative_to(folder).as_posix()
        raw = p.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        try:
            s = parse_seed(raw.decode("utf-8", "replace"))
        except ValueError as e:
            bad.append(f"{rel}: {e}")
            continue
        s["category"] = s["category"] or (rel.rsplit("/", 1)[0] if "/" in rel else "")
        old = by_seed.get(rel)
        if old and old["seed"].get("sha") == sha:
            same += 1
            continue
        if old and old.get("status") != "archived":
            f = propose(out, title=s["title"], question=s["question"], answer=s["answer"], by=by, target=old["id"], provenance={"seed": rel})                 if old.get("status") == "published" else edit(out, old["id"], by, title=s["title"], question=s["question"], answer=s["answer"])
            changed.append(f["id"])
        else:
            f = propose(out, title=s["title"], question=s["question"], answer=s["answer"], by=by, provenance={"seed": rel})
            made.append(f["id"])
        with _LOCK:
            f = read(out, f["id"])
            f["seed"], f["category"], f["tags"] = {"path": rel, "sha": sha}, s["category"], s["tags"]
            f["screen"], f["looks_like"] = _clean(s["screen"], 120), _clean(s["looks_like"], 600)       # what the problem LOOKS like: matched against a screenshot's description
            _write(out, f)
        if publish:
            publish_ = globals()["publish"]
            publish_(out, f["id"], by)
    return {"created": made, "updated": changed, "unchanged": same, "skipped": bad, "published": bool(publish)}
