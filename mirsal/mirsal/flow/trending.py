"""Trending (docs/api.md, Office accounts on the LAN, Haitham 2026-10-04: "higgsfield 'trending' style … liked and commented, and use pack in your workflow"):
packs the owner or an admin chose to Share, in a Library tab everyone signed in can open, like and comment on, ordered three ways:
- `trending`: likes (3 points), comments (2) and the share itself (4), each fading with age (half of its weight after about 5 days), recomputed on read;
- `new`: the most recently shared first; `liked`: the most likes first.
`use` puts a shared pack into the viewer's workflow: the owner (who has the library) gets a copy as a new pack (files copied, `source.shared_from`);
anyone else gets the pack's subject as a prompt and its cover as a reference picture for a batch of their own (members have no library yet).
The state is `out/trending.json` (git-ignored: people's names and words)."""
from __future__ import annotations

import json
import math
import threading
import time
from pathlib import Path

from ..runtime import atomic

_LOCK = threading.RLock()
HALF_LIFE_DAYS = 5.0


class TrendingError(Exception):
    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code


def _path(out: Path) -> Path:
    return Path(out) / "trending.json"


def _read(out: Path) -> dict:
    try:
        d = json.loads(atomic.read_text(_path(out)))
    except (OSError, ValueError):
        d = {}
    return {"shared": d.get("shared", {}), "likes": d.get("likes", {}), "comments": d.get("comments", {})}


def _write(out: Path, d: dict) -> None:
    Path(out).mkdir(parents=True, exist_ok=True)
    atomic.write_text(_path(out), json.dumps(d, indent=1, ensure_ascii=False))


def _pack(lib, pid: str) -> dict:
    with lib.lock:
        db = lib._load()
    p = next((x for x in db.get("packs", []) if x["id"] == pid), None)
    if p is None:
        raise TrendingError("no such pack", 404)
    return p


def share(out: Path, lib, pid: str, by: str) -> dict:
    _pack(lib, pid)
    with _LOCK:
        d = _read(out)
        d["shared"].setdefault(pid, {"by": by, "at": round(time.time(), 3)})
        _write(out, d)
    return d["shared"][pid]


def unshare(out: Path, pid: str) -> None:
    with _LOCK:
        d = _read(out)
        d["shared"].pop(pid, None)
        _write(out, d)


def _shared(d: dict, pid: str) -> None:
    if pid not in d["shared"]:
        raise TrendingError("this pack is not shared", 404)


def like(out: Path, pid: str, uid: str, on: bool = True) -> int:
    with _LOCK:
        d = _read(out)
        _shared(d, pid)
        rows = [x for x in d["likes"].get(pid, []) if x["user"] != uid]
        if on:
            rows.append({"user": uid, "at": round(time.time(), 3)})
        d["likes"][pid] = rows
        _write(out, d)
    return len(rows)


def comment(out: Path, pid: str, uid: str, name: str, text: str) -> dict:
    text = " ".join(str(text or "").split())[:500]
    if not text:
        raise TrendingError("write something first")
    with _LOCK:
        d = _read(out)
        _shared(d, pid)
        rows = d["comments"].setdefault(pid, [])
        c = {"id": f"C{sum(len(v) for v in d['comments'].values()) + 1:04d}", "user": uid, "name": str(name or uid)[:60], "text": text,
             "at": round(time.time(), 3), "deleted": False}
        rows.append(c)
        _write(out, d)
    return c


def delete_comment(out: Path, pid: str, cid: str, uid: str, role: str) -> None:
    with _LOCK:
        d = _read(out)
        c = next((x for x in d["comments"].get(pid, []) if x["id"] == cid), None)
        if c is None:
            raise TrendingError("no such comment", 404)
        if c["user"] != uid and role not in ("owner", "admin"):
            raise TrendingError("only its writer, an admin or the owner can delete a comment", 403)
        c["deleted"] = True
        _write(out, d)


def _w(at: float, now: float) -> float:
    return math.exp(-math.log(2) * max(0.0, now - (now if at is None else float(at))) / (HALF_LIFE_DAYS * 86400))


def score(d: dict, pid: str, now: float | None = None) -> float:
    now = now or time.time()
    s = 4 * _w(d["shared"][pid]["at"], now)
    s += sum(3 * _w(x["at"], now) for x in d["likes"].get(pid, []))
    s += sum(2 * _w(x["at"], now) for x in d["comments"].get(pid, []) if not x.get("deleted"))
    return round(s, 4)


def listing(out: Path, lib, viewer: str, order: str = "trending") -> list[dict]:
    if order not in ("trending", "new", "liked"):
        raise TrendingError("order must be trending, new or liked")
    d = _read(out)
    with lib.lock:
        db = lib._load()
    packs = {p["id"]: p for p in db.get("packs", [])}
    rows = []
    for pid, sh in d["shared"].items():
        p = packs.get(pid)
        if not p:
            continue
        likes = d["likes"].get(pid, [])
        cover = next((s for s in p["stickers"] if s["id"] == p.get("cover")), (p["stickers"] or [None])[0])
        rows.append({"pack_id": pid, "name": p["name"], "stickers": len(p["stickers"]), "shared_at": sh["at"], "shared_by": sh["by"],
                     "likes": len(likes), "liked": any(x["user"] == viewer for x in likes),
                     "comments": sum(1 for c in d["comments"].get(pid, []) if not c.get("deleted")),
                     "cover": {"id": cover["id"], "type": cover.get("type")} if cover else None, "score": score(d, pid)})
    key = {"trending": lambda r: (-r["score"], -r["shared_at"]), "new": lambda r: -r["shared_at"], "liked": lambda r: (-r["likes"], -r["score"])}[order]
    return sorted(rows, key=key)


def detail(out: Path, lib, pid: str, viewer: str) -> dict:
    d = _read(out)
    _shared(d, pid)
    p = _pack(lib, pid)
    likes = d["likes"].get(pid, [])
    return {"pack_id": pid, "name": p["name"], "shared_at": d["shared"][pid]["at"], "likes": len(likes), "liked": any(x["user"] == viewer for x in likes),
            "stickers": [{"id": s["id"], "name": s.get("name"), "emoji": s.get("emoji"), "type": s.get("type")} for s in p["stickers"]],
            "comments": [c for c in d["comments"].get(pid, []) if not c.get("deleted")]}


def file_of(out: Path, lib, pid: str, sid: str) -> Path:
    """A sticker file of a SHARED pack (anyone signed in may see it; an unshared pack's files stay the owner's)."""
    _shared(_read(out), pid)
    from ..media.library import LibraryError
    try:
        f, _ = lib.sticker_path(pid, sid)
    except LibraryError as e:
        raise TrendingError(str(e), 404)
    return f


def copy_pack(out: Path, lib, pid: str, by: str) -> dict:
    """Use in my workflow (the owner): a copy of the shared pack in the library, every file copied, the source recorded."""
    _shared(_read(out), pid)
    src = _pack(lib, pid)
    new = lib.create_pack(f"{src['name']} (from Trending)")
    for s in src["stickers"]:
        f = lib.files / s["file"]
        if f.is_file():
            lib.add_bytes(new["id"], f.read_bytes(), f.suffix.lstrip("."), s.get("name") or "sticker", s.get("type") or "static", s.get("emoji") or "🙂",
                          source={**(s.get("source") or {}), "shared_from": pid, "shared_sticker": s["id"]}, w=s.get("w") or 512, h=s.get("h") or 512)
    return {"pack_id": new["id"], "name": new["name"]}


def as_request(out: Path, lib, pid: str) -> tuple[str, bytes | None, str]:
    """Use in my workflow (anyone without a library): the prompt to start from and the cover's picture as a reference (a still; an animated cover has none)."""
    _shared(_read(out), pid)
    p = _pack(lib, pid)
    still = next((s for s in p["stickers"] if s.get("type") != "animated" and (lib.files / s["file"]).is_file()), None)
    data = (lib.files / still["file"]).read_bytes() if still else None
    return p["name"], data, (still["file"].rsplit("/", 1)[-1] if still else "")
