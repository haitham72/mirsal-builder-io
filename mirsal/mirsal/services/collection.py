"""Export a pack (or one Studio batch) to the AddCollection API, an external emoji CMS (`docs/Api/AddCollection-API .md`).

`POST {base}/api/v1/Upload/AddCollection`, multipart/form-data, HTTP Basic:
- `CollectionName` (the pack's name), `Description` (optional),
- `Media` repeated once per file (`.webm` animated, `.png` / `.webp` static),
- `MediaMetadata`: ONE JSON string, an array of `{emoji_utf, tags}` paired with `Media` BY INDEX (never by file name).

What is sent is exactly what Download .zip holds, in the same order: `Library.export_zip` (a pack) and `batches.export_zip` (a batch) choose the
stickers (accepted, animated where ready) and resolve each one's emoji and action tags; their `manifest.json` is read back here, so the two exports
can never disagree. `emoji_utf` is the asset's first grapheme cluster, `tags` its action tokens joined by `_` (`laugh_rofl_lmao`).

Configuration lives in the environment only (`.env`), never in a file in the repo: `MIRSAL_COLLECTION_API_URL` (default the CMS below) and
`MIRSAL_COLLECTION_API_CREDENTIALS` (base64 of `user:password`, or `user:password` itself, which is encoded here). Every export, ok or not, is a line in
`out/collection_exports.jsonl` (who, what, how many, the answer's status), never the credentials. Stdlib only; tests talk to a fake server."""
from __future__ import annotations

import base64
import io
import json
import os
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

DEFAULT_URL = "https://emojicms.devinprocess.com"
ENDPOINT = "/api/v1/Upload/AddCollection"
TIMEOUT = 120
MIME = {".webm": "video/webm", ".png": "image/png", ".webp": "image/webp"}


class CollectionError(Exception):
    def __init__(self, message: str, code: int = 400, detail=None):
        super().__init__(message)
        self.code = code
        self.detail = detail


def base_url() -> str:
    return (os.environ.get("MIRSAL_COLLECTION_API_URL") or DEFAULT_URL).strip().rstrip("/")


def credentials() -> str | None:
    """The Basic token: base64 of `user:password`. A value holding `:` is the pair itself (base64 never contains `:`)."""
    v = (os.environ.get("MIRSAL_COLLECTION_API_CREDENTIALS") or "").strip()
    if not v:
        return None
    return base64.b64encode(v.encode("utf-8")).decode("ascii") if ":" in v else v


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
            items.append({"filename": name, "mime": MIME[ext], "data": z.read(name), "emoji_utf": a.get("emoji") or "🙂",
                          "tags": tags_of(a) or tags_of({"tags": [a.get("action")]}) or "sticker"})      # never an empty tags string
    if not items:
        raise CollectionError("nothing to send: no accepted sticker", 409)
    return man.get("pack") or {}, items


def content_subtype(items: list[dict]) -> str:
    """The collection's media type for the CMS: `webm` for animated stickers (and for a mix), else the stills' own type (`png` / `webp`)."""
    kinds = {Path(it["filename"]).suffix.lower().lstrip(".") for it in items}
    return kinds.pop() if len(kinds) == 1 else "webm"


def multipart(name: str, description: str, items: list[dict]) -> tuple[bytes, str]:
    """The form body and its Content-Type (with the boundary). Media parts in order, then MediaMetadata as one JSON string of the same length."""
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
    field("MediaMetadata", json.dumps([{"emoji_utf": it["emoji_utf"], "tags": it["tags"]} for it in items], ensure_ascii=False))
    buf.write(f"--{boundary}--\r\n".encode())
    return buf.getvalue(), f"multipart/form-data; boundary={boundary}"


def post(name: str, description: str, items: list[dict]) -> dict:
    """Send one collection. {ok, status, response}; the answer's body is JSON when it is JSON, else its text (an HTML error page)."""
    token = credentials()
    if not token:
        raise CollectionError("The collection API is not set up: put MIRSAL_COLLECTION_API_CREDENTIALS in .env and restart the server", 503)
    body, ctype = multipart(name, description, items)
    req = urllib.request.Request(base_url() + ENDPOINT, data=body, method="POST",
                                 headers={"Content-Type": ctype, "Authorization": f"Basic {token}", "Accept": "application/json"})
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


def reason(status: int, res) -> str:
    """The refusal in words: the CMS's `message`, else an ASP.NET validation answer (`title` + each field's errors), else its text, else the status."""
    if isinstance(res, dict):
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
    title = " ".join(str(name or pack.get("title") or pack.get("slug") or "Mirsal stickers").split())[:120]
    desc = " ".join(str(description or "").split())[:2000] or title      # the CMS may require a description: an empty one is the collection's name
    row = {"at": round(time.time(), 3), "by": by, "what": what, "collection": title, "count": len(items), "url": base_url()}
    try:
        r = post(title, desc, items)
    except CollectionError as e:
        from ..runtime import activity
        activity.say(f'export "{title}" ({what}) failed: {e}', error=True)
        _log(out, {**row, "ok": False, "error": str(e)})
        raise
    res = r["response"]
    err = None if r["ok"] else reason(r["status"], res)
    from ..runtime import activity
    activity.say(f'exported "{title}" ({what}): {len(items)} stickers' if r["ok"] else f'export "{title}" ({what}) refused {r["status"]}: {err}', error=not r["ok"])
    _log(out, {**row, "ok": r["ok"], "status": r["status"], **({"error": err, "response": res if isinstance(res, dict) else str(res)[:1000]} if err else {})})
    return {"ok": r["ok"], "status": r["status"], "collection": title, "count": len(items), "response": res, **({"error": err} if err else {})}
