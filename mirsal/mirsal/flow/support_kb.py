"""What the support agent may read (docs/agent-and-chat.md "Support"): published FAQ entries, the repo's `docs/`, and, for the owner and admins only, its code.

The repo is the path in `MIRSAL_SUPPORT_REPO` (`mirsal/.env`; unset = the FAQ alone). `reindex` cuts `docs/**/*.md` into heading sections and the app's
source (`mirsal/mirsal/**`, `migrations/`) into blocks, keeps them in `out/support/index.json` (the record, with each file's sha256 so an unchanged file is
never cut or embedded again) and, when Postgres and the LOCAL embedding model are up, writes their 768-d vectors to `support_chunks` (migration 011).
Secrets are scrubbed before anything is kept; `.env`, `opencode.json`, `telegram-id.md`, `out/` and virtual envs are never read.

`search(query, audience)`: published FAQ first, then docs; code only when `audience == "staff"` AND the FAQ and docs were not enough. Vectors when they
can be used (only the local model embeds: no hosted provider, nothing paid), otherwise a lexical score over the same files, so support works without
Postgres. A draft FAQ entry is never a hit: the published text in its file is checked even when the database answers."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import threading
import time
from pathlib import Path

from ..runtime import atomic

REPO_VAR = "MIRSAL_SUPPORT_REPO"
ENOUGH = {"vector": 0.55, "lexical": 0.45}         # the best FAQ/doc hit at or above this answers; below it staff also get code
NEVER_NAMES = {".env", "opencode.json", "telegram-id.md", ".env.local"}
NEVER_PARTS = {"out", "venv", ".venv", "__pycache__", "node_modules", "dist", ".git", "inputs", "assets", "fonts"}
MAX_CHUNK = 1800
_LOCK = threading.RLock()
_CORPUS: dict = {"key": None, "docs": None}


class KBError(Exception):
    pass


# ---------- where ----------
def repo_root() -> Path | None:
    from ..services import llm
    llm._load_dotenv()
    v = (os.environ.get(REPO_VAR) or "").strip().strip('"')
    if not v:
        return None
    p = Path(v).expanduser()
    return p.resolve() if p.is_dir() else None


def _roots(repo: Path) -> tuple[list[Path], list[Path]]:
    """(doc roots, code roots): the repository root (docs/ beside mirsal/) or its inner `mirsal/` folder both work."""
    if (repo / "mirsal" / "mirsal").is_dir():
        return [repo / "docs"], [repo / "mirsal" / "mirsal", repo / "mirsal" / "migrations"]
    if (repo / "mirsal" / "__init__.py").is_file():
        return [repo.parent / "docs"], [repo / "mirsal", repo / "migrations"]
    return [repo / "docs"], []


def _allowed(p: Path, root: Path) -> bool:
    rel = p.relative_to(root).parts
    return p.name not in NEVER_NAMES and not any(x in NEVER_PARTS or x.startswith(".") for x in rel[:-1])


def _files(repo: Path) -> list[tuple[str, str, Path]]:
    """(kind, path relative to the repo, file) for every readable doc and source file."""
    docs, code = _roots(repo)
    found = []
    for r in docs:
        if r.is_dir():
            found += [("doc", f) for f in sorted(r.rglob("*.md")) if _allowed(f, r)]
    for r in code:
        if r.is_dir():
            found += [("code", f) for f in sorted(r.rglob("*")) if f.suffix in (".py", ".js", ".sql") and f.is_file() and _allowed(f, r)]
    base = repo.parent if not (repo / "mirsal" / "mirsal").is_dir() and (repo / "mirsal" / "__init__.py").is_file() else repo
    return [(k, f.resolve().relative_to(base.resolve()).as_posix(), f) for k, f in found]


# ---------- cutting ----------
def _split_long(heading: str, text: str) -> list[tuple[str, str]]:
    if len(text) <= MAX_CHUNK:
        return [(heading, text)]
    parts, cur = [], ""
    for para in re.split(r"\n\s*\n", text):
        para = para[:MAX_CHUNK]
        if cur and len(cur) + len(para) + 2 > MAX_CHUNK:
            parts.append(cur)
            cur = ""
        cur = (cur + "\n\n" + para).strip()
    if cur:
        parts.append(cur)
    return [(heading, p) for p in parts]


def cut_markdown(text: str) -> list[tuple[str, str]]:
    """(heading path, section text): one chunk per heading section, a long section split at its paragraphs."""
    out, trail, buf = [], [], []

    def flush():
        body = "\n".join(buf).strip()
        if body:
            out.extend(_split_long(" › ".join(trail), body))
        buf.clear()
    for line in text.splitlines():
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            flush()
            level = len(m.group(1))
            trail[:] = trail[:level - 1] + [m.group(2).strip()]
        buf.append(line)
    flush()
    return out


_CODE_START = re.compile(r"^(?:async def |def |class |# -{3,}|function |async function |ACT\.\w+\s*=|RENDER\.\w+\s*=|CREATE |-- )")


def cut_code(text: str) -> list[tuple[str, str]]:
    """(the block's first definition, its text): blocks begin at top-level definitions and grow to about 1200 characters; a long line is cut to 600."""
    out, buf, head = [], [], ""
    size = 0
    for line in text.splitlines():
        line = line[:600]
        if _CODE_START.match(line) and size >= 1200:
            out.append((head, "\n".join(buf)))
            buf, size, head = [], 0, ""
        if not head and _CODE_START.match(line):
            head = line.strip()[:80]
        buf.append(line)
        size += len(line) + 1
        if size >= MAX_CHUNK + 600:
            out.append((head, "\n".join(buf)))
            buf, size, head = [], 0, ""
    if "".join(buf).strip():
        out.append((head, "\n".join(buf)))
    return out


# ---------- the index ----------
def index_path(out: Path) -> Path:
    return Path(out) / "support" / "index.json"


def read_index(out: Path) -> dict:
    p = index_path(out)
    try:
        return json.loads(atomic.read_text(p)) if p.is_file() else {"files": {}}
    except (OSError, ValueError):
        return {"files": {}}


def _embedder(out: Path):
    """The LOCAL embedding model, or None (never the hosted fallback that services/embed.py would use)."""
    try:
        from ..services import embed, llm
        if not llm._local_allowed() or embed.backend()["provider"] != "local":     # tests pin MIRSAL_LLM_PROVIDER=none: no real LM Studio
            return None

        def run(texts: list, kind: str = "document") -> list:
            if embed.backend()["provider"] != "local":
                raise KBError("the local embedding model went away")
            return embed.embed(texts, kind=kind, out=out)
        run.model = embed.backend()["model"]
        return run
    except Exception:
        return None


def _pg(out: Path) -> bool:
    try:
        from ..store import db, sync
        return sync.enabled(out) and db.available()
    except Exception:
        return False


def reindex(out: Path, repo: Path | None = None, *, embedder="auto") -> dict:
    """Cut what changed, keep the index file, write vectors when Postgres and the local model are up. Safe to run again: unchanged files cost nothing."""
    from ..obs.scrub import scrub_secrets
    repo = Path(repo).resolve() if repo else repo_root()
    if repo is None:
        raise KBError(f"{REPO_VAR} is not set (or is not a folder): only the FAQ is searched")
    emb = _embedder(out) if embedder == "auto" else embedder
    pg = _pg(out)
    with _LOCK:
        idx = read_index(out)
        files = idx.get("files") or {}
        if idx.get("repo") != str(repo):
            files = {}
        seen, changed, embedded = set(), 0, 0
        for kind, rel, f in _files(repo):
            seen.add(rel)
            try:
                raw = f.read_bytes()
            except OSError:
                continue
            sha = hashlib.sha256(raw).hexdigest()
            ent = files.get(rel)
            fresh = not ent or ent.get("sha") != sha
            if fresh:
                text = raw.decode("utf-8", "replace")
                pieces = cut_markdown(text) if kind == "doc" else cut_code(text)
                ent = {"sha": sha, "kind": kind, "vec_model": None,
                       "chunks": [{"id": f"{kind}:{rel}#{i}", "heading": scrub_secrets(h), "text": scrub_secrets(t)} for i, (h, t) in enumerate(pieces)]}
                files[rel] = ent
                changed += 1
            want = emb is not None and pg and ent.get("vec_model") != getattr(emb, "model", None)
            if pg and (fresh or want):
                rows = [{"id": ch["id"], "kind": kind, "heading": ch["heading"], "text": ch["text"], "sha": sha} for ch in ent["chunks"]]
                vecs = None
                if want and rows:
                    try:
                        vecs = emb([f"{rel} {r['heading']}\n{r['text']}" for r in rows], "document")
                        ent["vec_model"] = getattr(emb, "model", "local")
                        embedded += len(rows)
                    except Exception:
                        vecs = None
                try:
                    from ..store import db, repo as rp
                    with db.connect() as c:
                        rp.replace_chunks(c, rel, rows, vecs, ent.get("vec_model"))
                except Exception:
                    ent["vec_model"] = None
        removed = [k for k in files if k not in seen]
        for k in removed:
            files.pop(k)
        if pg and removed:
            try:
                from ..store import db, repo as rp
                with db.connect() as c:
                    rp.drop_chunks(c, list(files))
            except Exception:
                pass
        idx = {"repo": str(repo), "at": round(time.time(), 3), "files": files}
        index_path(out).parent.mkdir(parents=True, exist_ok=True)
        atomic.write_text(index_path(out), json.dumps(idx, ensure_ascii=False))
        _CORPUS["key"] = None
    from . import faq
    faqs = 0
    for f in faq.listing(out, status="published"):
        faq.index(out, faq.read(out, f["id"]), embedder=emb)
        faqs += 1
    return {"repo": str(repo), "files": len(files), "changed": changed, "removed": len(removed), "embedded": embedded, "faq": faqs,
            "chunks": {k: sum(len(e["chunks"]) for e in files.values() if e["kind"] == k) for k in ("doc", "code")},
            "vectors": bool(pg and emb is not None), "postgres": pg, "embedder": getattr(emb, "model", None)}


def status(out: Path) -> dict:
    idx = read_index(out)
    files = idx.get("files") or {}
    pg_counts = None
    if _pg(out):
        try:
            from ..store import db, repo as rp
            with db.connect() as c:
                pg_counts = rp.chunk_count(c)
        except Exception:
            pg_counts = None
    emb = _embedder(out)
    repo = repo_root()
    return {"repo": str(repo) if repo else None, "repo_var": REPO_VAR, "indexed_repo": idx.get("repo"), "indexed_at": idx.get("at"), "files": len(files),
            "chunks": {k: sum(len(e["chunks"]) for e in files.values() if e["kind"] == k) for k in ("doc", "code")},
            "postgres": pg_counts, "embedder": getattr(emb, "model", None)}


# ---------- searching ----------
_WORD = re.compile(r"[a-z0-9][a-z0-9_]{2,}")
_STOP = set("the and for that this with from have has are was were you your not can but what when why how does did into out about there their they them then than which who will would should could also just more some any all one".split())


def _words(text: str) -> list[str]:
    return [w for w in _WORD.findall(str(text).lower()) if w not in _STOP]


def _faq_docs(out: Path) -> list[dict]:
    from . import faq
    rows = []
    for f in faq.listing(out, status="published"):
        e = faq.read(out, f["id"])
        rows.append({"kind": "faq", "id": e["id"], "title": e.get("title") or e.get("question") or e["id"], "text": faq.search_text(e).split("\n", 1)[1],
                     "path": None})
    return rows


def _chunk_docs(out: Path) -> list[dict]:
    rows = []
    for rel, ent in (read_index(out).get("files") or {}).items():
        for ch in ent.get("chunks") or []:
            rows.append({"kind": ent["kind"], "id": ch["id"], "title": rel + (f" › {ch['heading']}" if ch.get("heading") else ""), "text": ch["text"], "path": rel})
    return rows


def _corpus(out: Path) -> list[dict]:
    """Every searchable text with its words, rebuilt when the index or the FAQ folder changes."""
    from . import faq
    ip, fd = index_path(out), faq.faq_dir(out)
    key = (ip.stat().st_mtime if ip.is_file() else 0, max([p.stat().st_mtime for p in fd.glob("F*.json")] + [0]) if fd.is_dir() else 0, str(out))
    if _CORPUS["key"] != key:
        docs = _faq_docs(out) + _chunk_docs(out)
        for d in docs:
            d["_w"] = set(_words(d["title"] + " " + d["text"]))
            d["_t"] = set(_words(d["title"]))
        _CORPUS.update(key=key, docs=docs)
    return _CORPUS["docs"]


def _lexical(out: Path, query: str, kinds: set, k: int) -> list[dict]:
    q = list(dict.fromkeys(_words(query)))
    if not q:
        return []
    docs = [d for d in _corpus(out) if d["kind"] in kinds]
    allw = _corpus(out)
    n = max(1, len(allw))
    idf = {w: math.log(1 + n / (1 + sum(1 for d in allw if w in d["_w"]))) for w in q}
    total = sum(idf.values()) or 1.0
    hits = []
    for d in docs:
        s = sum(idf[w] for w in q if w in d["_w"]) / total
        s += 0.1 * sum(1 for w in q if w in d["_t"]) / len(q)
        if s > 0:
            hits.append({**{x: d[x] for x in ("kind", "id", "title", "text", "path")}, "score": round(min(1.0, s), 3)})
    return sorted(hits, key=lambda h: -h["score"])[:k]


def _vector(out: Path, qvec, kinds: set, k: int) -> list[dict]:
    from ..store import db, repo as rp
    from . import faq
    by = {d["id"]: d for d in _chunk_docs(out)}
    hits = []
    with db.connect() as c:
        if "faq" in kinds:
            for fid, s in rp.faq_near(c, qvec, k):
                try:
                    e = faq.read(out, fid)
                except KeyError:
                    continue
                if e.get("status") == "published":                       # the file decides, never a stale row
                    hits.append({"kind": "faq", "id": fid, "title": e.get("title") or fid, "text": faq.search_text(e).split("\n", 1)[1],
                                 "path": None, "score": round(s, 3)})
        ck = [x for x in ("doc", "code") if x in kinds]
        if ck:
            for cid, s in rp.chunks_near(c, qvec, ck, k):
                d = by.get(cid)
                if d:
                    hits.append({**{x: d[x] for x in ("kind", "id", "title", "text", "path")}, "score": round(s, 3)})
    return sorted(hits, key=lambda h: -h["score"])[:k]


def search(out: Path, query: str, audience: str = "member", k: int = 5) -> dict:
    """{mode, hits, enough, code_used}: FAQ and docs for everyone; code only for staff and only when FAQ and docs fell short."""
    query = str(query or "").strip()[:1000]
    if not query:
        return {"mode": "lexical", "hits": [], "enough": False, "code_used": False}
    mode, qvec = "lexical", None
    if _pg(out):
        emb = _embedder(out)
        if emb is not None:
            try:
                qvec = emb([query], "query")[0]
                mode = "vector"
            except Exception:
                qvec = None

    def find(kinds):
        if mode == "vector":
            try:
                return _vector(out, qvec, kinds, k)
            except Exception:
                pass
        return _lexical(out, query, kinds, k)
    hits = find({"faq", "doc"})
    if mode == "vector" and not hits:
        hits = _lexical(out, query, {"faq", "doc"}, k)
    best = max([h["score"] for h in hits] + [0.0])
    enough = best >= ENOUGH[mode]
    code_used = False
    if audience == "staff" and not enough:
        code = find({"code"})
        if code:
            hits += code[:4]
            code_used = True
    hits.sort(key=lambda h: (h["kind"] != "faq", -h["score"]))
    return {"mode": mode, "hits": hits, "enough": enough, "code_used": code_used}


def search_faq(out: Path, query: str, k: int = 3) -> tuple[list[dict], str]:
    """(published FAQ entries close to `query`, the search mode): the duplicate check before a new entry is proposed."""
    r = search(out, query, "member", k=k)
    return [h for h in r["hits"] if h["kind"] == "faq"], r["mode"]
