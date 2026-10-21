"""Export a pack (or one Studio batch) to the Mirsal Creator API's "Submit a Pack for Approval", an external emoji CMS (`docs/api-integration.md`).

`POST {base}/api/v1/Upload/AddCollection`, multipart/form-data, `Authorization: Bearer <developer key>` (an `sk-...` key from the CMS's Developer Keys page):
- `CollectionName` (the pack's name, at most 40 characters), `Description` (required, at most 160; the collection's name when none is given),
- `ContentSubType` (`webm` for animated packs),
- `Media` repeated once per file (`.webm` animated, `.png` / `.webp` static),
- `MediaThumbnails` repeated once per file, a PNG paired with `Media` by index (a `.png` as it is, a `.webp` converted, a `.webm`'s
  grey silhouette: the same bytes as the Download .zip's `{stem}_grey.png`, `media/grey.py` from the animation's first visible frame),
- `MediaMetadata`: ONE JSON string, an array of `{emoji_utf, tags}` paired with `Media` BY INDEX (never by file name).

What is sent is exactly what Download .zip holds, in the same order: `Library.export_zip` (a pack) and `batches.export_zip` (a batch) choose the
stickers (accepted, animated where ready) and resolve each one's emoji and action tags; their `manifest.json` is read back here, so the two exports
can never disagree. `emoji_utf` is the asset's first grapheme cluster, `tags` its action tokens joined by `_` (`laugh_rofl_lmao`).

Configuration lives in the environment only (`.env`), never in a file in the repo: `MIRSAL_COLLECTION_API_URL` (default the CMS below) and
`MIRSAL_COLLECTION_API_CREDENTIALS` (the `sk-...` developer key, sent as `Authorization: Bearer`; a legacy `user:password` or its base64 still sends HTTP Basic).
The answer is `{Success, Result, ErrorMessages}`: a 200 with `Success: false` is a refusal too; 401 means the key is missing, invalid or expired. Every export, ok or not, is a line in
`out/collection_exports.jsonl` (who, what, how many, the answer's status), never the credentials. Stdlib only; tests talk to a fake server.

The routes never wait for the CMS (re-encoding and uploading a pack can take minutes): `enqueue` refuses at once what can be refused at once,
answers an export id `X…`, and ONE worker thread sends the queued exports in order (`queued` -> `preparing` -> `sending` -> `done` | `failed`).
Each export's state is `out/collection_exports/<id>.json`; one this process no longer runs (the server restarted) reads as failed. Its sender
gets a notification with the outcome (`flow/notifications`, kind `update`)."""
from __future__ import annotations

import base64
import io
import json
import os
import queue
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

# Default URL for the emoji CMS
DEFAULT_URL = "https://emojicms.ehub.ae"
ENDPOINT = "/api/v1/Upload/AddCollection"
TIMEOUT = 120
NAME_MAX = 40            # the API's limits (docs/api-integration.md): checked here, so a refusal is a sentence before anything is uploaded
DESCRIPTION_MAX = 160
MIME = {".webm": "video/webm", ".png": "image/png", ".webp": "image/webp"}


class CollectionError(Exception):
    def __init__(self, message: str, code: int = 400, detail=None):
        super().__init__(message)
        self.code = code
        self.detail = detail


def base_url() -> str:
    return (os.environ.get("MIRSAL_COLLECTION_API_URL") or DEFAULT_URL).strip().rstrip("/")


def credentials() -> str | None:
    """The raw configured value: an `sk-...` API key, `user:password`, or its base64 (base64 never contains `:`)."""
    v = (os.environ.get("MIRSAL_COLLECTION_API_CREDENTIALS") or "").strip()
    return v or None


def auth_header() -> str | None:
    """`Authorization` value for the CMS: `Bearer <key>` for an `sk-...` API key, else HTTP Basic (a `user:password`
    value is encoded here; a value without `:` is already base64, as before)."""
    v = credentials()
    if not v:
        return None
    if v.startswith("sk-"):
        return f"Bearer {v}"
    return f"Basic {base64.b64encode(v.encode('utf-8')).decode('ascii') if ':' in v else v}"


def status() -> dict:
    """For /api/collection and `doctor`: where it would send, and whether credentials are set (never their value)."""
    return {"configured": bool(credentials()), "url": base_url()}


def tags_of(asset: dict) -> str:
    """`laugh_rofl_lmao`: the asset's action tokens (the manifest's `tags` minus the emoji itself), lowercase, `_`-joined, no repeats."""
    out = []
    for t in asset.get("tags") or []:
        t = "".join(ch for ch in str(t).lower().replace("-", "_").replace(" ", "_") if ch.isascii() and (ch.isalnum() or ch == "_")).strip("_")
        for w in filter(None, t.split("_")):
            if w not in out:
                out.append(w)
    return "_".join(out)


def items_from_zip(data: bytes) -> tuple[dict, list[dict]]:
    """(the manifest's pack, [{filename, mime, data, emoji_utf, tags}]) in the manifest's order: Media[i] <-> MediaMetadata[i]."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        man = json.loads(z.read("manifest.json").decode("utf-8"))
        items = []
        for a in man.get("assets") or []:
            name = a["filename"]
            ext = Path(name).suffix.lower()
            if ext not in MIME:
                raise CollectionError(f"{name}: only .webm, .png and .webp stickers can be sent", 409)
            data = z.read(name)
            items.append({"filename": name, "mime": MIME[ext], "data": data, "thumb": thumbnail(name, data), "emoji_utf": a.get("emoji") or "🙂",
                          "tags": tags_of(a) or tags_of({"tags": [a.get("action")]}) or "sticker"})      # never an empty tags string
    if not items:
        raise CollectionError("nothing to send: no accepted sticker", 409)
    return man.get("pack") or {}, items


def thumbnail(name: str, data: bytes) -> bytes:
    """One PNG with alpha for `MediaThumbnails`: a `.png` as it is, a `.webp` converted, a `.webm`'s grey silhouette (Haitham,
    2026-10-15: the CMS shows this PNG at `user_media/Emoji_Assets/{emoji}.png`, so it is the same grey as the Download .zip's
    `{stem}_grey.png`, not the animation's first frame in full colour). An unreadable video refuses the export, as before."""
    ext = Path(name).suffix.lower()
    if ext == ".png":
        return data
    try:
        from PIL import Image
        if ext == ".webm":
            import tempfile
            from ..engine import ffmpeg as ff
            from ..media import grey as _grey
            with tempfile.TemporaryDirectory() as d:
                f = Path(d) / "clip.webm"
                f.write_bytes(data)
                a = _grey.alpha_of(None, f)
                if a is None:
                    info = ff.probe(f, vp9_native=True)          # raise the decode error below, like the first frame used to
                    a = ff.decode_full(f, info["width"], info["height"], 1, None)[0][..., 3]
                return _grey.grey_png(a)
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=True)
        return buf.getvalue()
    except CollectionError:
        raise
    except Exception as e:
        raise CollectionError(f"{name}: its thumbnail could not be made ({e})", 409)


def content_subtype(items: list[dict]) -> str:
    """The collection's media type for the CMS: `webm` for animated stickers (and for a mix), else the stills' own type (`png` / `webp`)."""
    kinds = {Path(it["filename"]).suffix.lower().lstrip(".") for it in items}
    return kinds.pop() if len(kinds) == 1 else "webm"


def multipart(name: str, description: str, items: list[dict]) -> tuple[bytes, str]:
    """The form body and its Content-Type (with the boundary). Media parts in order, MediaThumbnails in the same order, then MediaMetadata as one JSON string of the same length."""
    boundary = "----mirsal" + uuid.uuid4().hex
    buf = io.BytesIO()

    def field(key: str, value: str) -> None:
        buf.write(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        buf.write(value.encode("utf-8") + b"\r\n")

    field("CollectionName", name)
    field("Description", description)
    field("ContentSubType", content_subtype(items))       # required by the CMS (2026-10-09: "The ContentSubType field is required")
    for it in items:
        safe = it["filename"].replace('"', "").replace("\r", "").replace("\n", "")
        buf.write(f'--{boundary}\r\nContent-Disposition: form-data; name="Media"; filename="{safe}"\r\nContent-Type: {it["mime"]}\r\n\r\n'.encode("utf-8"))
        buf.write(it["data"] + b"\r\n")
    for it in items:                                       # the CMS's new field (2026-10-14): one PNG per Media part, by index
        thumb = Path(it["filename"].replace('"', "").replace("\r", "").replace("\n", "")).stem + ".png"
        buf.write(f'--{boundary}\r\nContent-Disposition: form-data; name="MediaThumbnails"; filename="{thumb}"\r\nContent-Type: image/png\r\n\r\n'.encode("utf-8"))
        buf.write(it["thumb"] + b"\r\n")
    field("MediaMetadata", json.dumps([{"emoji_utf": it["emoji_utf"], "tags": it["tags"]} for it in items], ensure_ascii=False))
    buf.write(f"--{boundary}--\r\n".encode())
    return buf.getvalue(), f"multipart/form-data; boundary={boundary}"


def post(name: str, description: str, items: list[dict]) -> dict:
    """Send one collection. {ok, status, response}; the answer's body is JSON when it is JSON, else its text (an HTML error page)."""
    auth = auth_header()
    if not auth:
        raise CollectionError("The collection API is not set up: put MIRSAL_COLLECTION_API_CREDENTIALS in .env and restart the server", 503)
    body, ctype = multipart(name, description, items)
    req = urllib.request.Request(base_url() + ENDPOINT, data=body, method="POST",
                                 headers={"Content-Type": ctype, "Authorization": auth, "Accept": "application/json"})
    ctx = None
    if req.full_url.startswith("https:"):
        from .telegram import _ssl_context        # the tolerant TLS context (a malformed Windows certificate must not stop a send)
        ctx = _ssl_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            st, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        st, raw = e.code, e.read()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise CollectionError(f"The collection API did not answer: {getattr(e, 'reason', e)}", 504)
    text = raw.decode("utf-8", "replace")
    try:
        answer = json.loads(text) if text.strip() else None
    except ValueError:
        answer = text[:2000]
    return {"ok": 200 <= st < 300, "status": st, "response": answer}


def _log(out: Path, row: dict) -> None:
    from ..runtime import atomic
    p = Path(out) / "collection_exports.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    old = p.read_text(encoding="utf-8") if p.is_file() else ""
    atomic.write_text(p, old + json.dumps(row, ensure_ascii=False) + "\n")


def accepted(status: int, res) -> bool:
    """The API took the pack: a 2xx whose JSON does not say `Success: false` (`{Success, Result, ErrorMessages}`; an older answer without `Success` counts by its status)."""
    if not 200 <= status < 300:
        return False
    return not (isinstance(res, dict) and res.get("Success", res.get("success", True)) is False)


def reason(status: int, res) -> str:
    """The refusal in words: 401 is the developer key; else the API's `ErrorMessages` (a list or a string), its `message`, an ASP.NET validation
    answer (`title` + each field's errors), its text, or the status."""
    if status == 401:
        return ("The collection API did not accept the developer key (missing, invalid or expired): generate a new key on its Developer Keys page, "
                "put it in MIRSAL_COLLECTION_API_CREDENTIALS in .env and restart the server")
    if isinstance(res, dict):
        em = res.get("ErrorMessages", res.get("errorMessages"))
        if isinstance(em, list) and any(em):
            return "; ".join(str(x) for x in em if x)[:500]
        if isinstance(em, str) and em.strip():
            return em.strip()[:500]
        if res.get("message"):
            return str(res["message"])[:500]
        errs = res.get("errors")
        if isinstance(errs, dict) and errs:
            parts = [f"{k}: {' '.join(map(str, v)) if isinstance(v, list) else v}" for k, v in errs.items()]
            return (str(res.get("title") or "Validation failed") + " " + "; ".join(parts))[:500]
        if res.get("title") or res.get("detail"):
            return " ".join(str(res[k]) for k in ("title", "detail") if res.get(k))[:500]
    if isinstance(res, str) and res.strip() and not res.lstrip().startswith("<"):
        return res.strip()[:500]
    return f"The collection API answered {status}"


def send(out: Path, what: str, zip_bytes: bytes, name: str | None, description: str = "", by: str = "human") -> dict:
    """Export the stickers of a Download .zip (`what`: `pack P…` or `G###`) as one collection. The answer:
    {ok, status, collection, count, response, error?}; a refusal by the CMS is an answer (ok false, its message), not an exception."""
    pack, items = items_from_zip(zip_bytes)
    title = " ".join(str(name or pack.get("title") or pack.get("slug") or "Mirsal stickers").split())
    desc = " ".join(str(description or "").split()) or title            # the API requires a description: an empty one is the collection's name
    row = {"at": round(time.time(), 3), "by": by, "what": what, "collection": title, "count": len(items), "url": base_url()}
    try:
        if len(title) > NAME_MAX:
            raise CollectionError(f"The collection name is {len(title)} characters; the collection API takes at most {NAME_MAX}. Shorten it and send again.", 400)
        if len(desc) > DESCRIPTION_MAX:
            raise CollectionError(f"The description is {len(desc)} characters; the collection API takes at most {DESCRIPTION_MAX}. Shorten it and send again.", 400)
        r = post(title, desc, items)
    except CollectionError as e:
        from ..runtime import activity
        activity.say(f'export "{title}" ({what}) failed: {e}', error=True)
        _log(out, {**row, "ok": False, "error": str(e)})
        raise
    res = r["response"]
    ok = accepted(r["status"], res)
    err = None if ok else reason(r["status"], res)
    from ..runtime import activity
    activity.say(f'exported "{title}" ({what}): {len(items)} stickers' if ok else f'export "{title}" ({what}) refused {r["status"]}: {err}', error=not ok)
    _log(out, {**row, "ok": ok, "status": r["status"], **({"error": err, "response": res if isinstance(res, dict) else str(res)[:1000]} if err else {})})
    result = res.get("Result", res.get("result")) if isinstance(res, dict) else None          # the created pack's details, as the API returns them
    return {"ok": ok, "status": r["status"], "collection": title, "count": len(items), "response": res, "result": result, **({"error": err} if err else {})}


# ---------- the queue: one export at a time in the background; each export's state is a file
FINAL = ("done", "failed")
_Q: queue.Queue = queue.Queue()
_LIVE: set = set()                 # the export ids this process will still run (queued or running)
_QLOCK = threading.Lock()
_WORKER: list = []


def _state_path(out: Path, xid: str) -> Path:
    return Path(out) / "collection_exports" / f"{xid}.json"


def _save(out: Path, st: dict) -> None:
    from ..runtime import atomic
    p = _state_path(out, st["id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    atomic.write_text(p, json.dumps(st, ensure_ascii=False, indent=1))


def check(name: str | None, description: str = "") -> None:
    """What is refused before anything is queued: a given name or description over the API's limits, and a missing developer key."""
    title = " ".join(str(name or "").split())
    desc = " ".join(str(description or "").split()) or title
    if len(title) > NAME_MAX:
        raise CollectionError(f"The collection name is {len(title)} characters; the collection API takes at most {NAME_MAX}. Shorten it and send again.", 400)
    if len(desc) > DESCRIPTION_MAX:
        raise CollectionError(f"The description is {len(desc)} characters; the collection API takes at most {DESCRIPTION_MAX}. Shorten it and send again.", 400)
    if not auth_header():
        raise CollectionError("The collection API is not set up: put MIRSAL_COLLECTION_API_CREDENTIALS in .env and restart the server", 503)


def enqueue(out: Path, what: str, make_zip, name: str | None, description: str = "", by: str = "human") -> dict:
    """Queue one export; `make_zip()` builds its Download .zip when its turn comes. Answers at once: {id, state: queued, position, …}."""
    check(name, description)
    xid = f"X{int(time.time() * 1000):x}{uuid.uuid4().hex[:4]}"
    st = {"id": xid, "what": what, "collection": " ".join(str(name or "").split()) or None, "by": by, "state": "queued", "at": round(time.time(), 3)}
    _save(out, st)
    with _QLOCK:
        _LIVE.add(xid)
        position = len(_LIVE)
        _Q.put((Path(out), xid, make_zip, name, description, by))
        if not _WORKER or not _WORKER[0].is_alive():
            _WORKER[:] = [threading.Thread(target=_work, name="collection-export", daemon=True)]
            _WORKER[0].start()
    return {**st, "position": position}


def export_state(out: Path, xid: str) -> dict | None:
    """The export's state, None when there is no such export. One an earlier server run left unfinished reads as failed."""
    if not re.fullmatch(r"X[0-9a-f]+", str(xid or "")):
        return None
    try:
        st = json.loads(_state_path(out, xid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    with _QLOCK:
        live = xid in _LIVE
    if st.get("state") not in FINAL and not live:
        st.update(state="failed", ok=False, error="The server restarted before this export was sent; send it again")
    return st


def _work() -> None:
    while True:
        out, xid, make_zip, name, description, by = _Q.get()
        st = export_state(out, xid) or {"id": xid, "by": by}
        try:
            st["state"] = "preparing"; _save(out, st)
            data = make_zip()
            st["state"] = "sending"; _save(out, st)
            st.update(send(out, st.get("what") or "", data, name, description, by))
            st["state"] = "done" if st["ok"] else "failed"
        except CollectionError as e:
            st.update(state="failed", ok=False, error=str(e), code=e.code)
        except Exception as e:                                     # never a silent stop: whatever broke is the export's answer
            st.update(state="failed", ok=False, error=f"The export broke: {e}")
        st["finished"] = round(time.time(), 3)
        try:
            _save(out, st)
        finally:
            with _QLOCK:
                _LIVE.discard(xid)
        _notify(out, st)


def _notify(out: Path, st: dict) -> None:
    """The outcome in the sender's notifications (once per export)."""
    if not st.get("by") or st["by"] == "human":
        return
    try:
        from ..flow import notifications as nt
        name = st.get("collection") or st.get("what") or "the pack"
        text = (f'Export to collection: "{name}" was sent ({st.get("count")} stickers)' if st["state"] == "done"
                else f'Export to collection: "{name}" was not sent: {st.get("error") or "unknown error"}')
        nt.add(out, st["by"], f"collection:{st['id']}", "update", text)
    except Exception:
        pass


def wait(timeout: float = 60.0) -> bool:
    """For tests: True once every queued export has finished."""
    end = time.time() + timeout
    while time.time() < end:
        with _QLOCK:
            if not _LIVE:
                return True
        time.sleep(0.05)
    return False
