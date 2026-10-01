"""Lifecycle Console server: stdlib http.server + one index.html. Binds 127.0.0.1. One background job at a time."""
from __future__ import annotations

import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .. import pipeline as pl
from ..library import Library, LibraryError, cutout, decode_image, png_bytes
from ..engine.config import EngineConfig
from ..video_project import MAX_UPLOAD, Projects, decode_overlays

UI = Path(__file__).parent
INDEX = UI / "index.html"
UI_FILES = {"studio.css": "text/css", "app.js": "text/javascript", "packs.js": "text/javascript", "editor.js": "text/javascript", "animate.js": "text/javascript", "chat.js": "text/javascript", "prepare.js": "text/javascript", "fonts/InterVariable.woff2": "font/woff2"}


class Console:
    def __init__(self, out: Path, inp: Path, pace: float = 0.0, cfg: EngineConfig | None = None):
        self.out, self.inp, self.pace, self.cfg = out, inp, pace, cfg or EngineConfig()
        self.lock = threading.Lock()   # held while a job runs
        self._health = None
        self.lib = Library(out)
        self.projects = Projects(out, self.cfg)

    def health(self) -> dict:
        """Can the final WEBM be encoded here? (live preview never needs ffmpeg)"""
        if self._health is None:
            try:
                from ..engine import ffmpeg as ff
                exe = ff.ffmpeg_exe()
                from .. import matte
                self._health = {"ffmpeg": exe, "vp9": bool(ff._has_vp9(exe)), "matte": matte.status()}
            except Exception as e:
                self._health = {"ffmpeg": None, "vp9": False, "error": str(e)}
        return self._health

    def submit(self, fn) -> None:
        if not self.lock.acquire(blocking=False):
            raise pl.PipelineError("busy", 409)

        def run():
            try:
                fn()
            finally:
                self.lock.release()
        threading.Thread(target=run, daemon=True).start()


def make_handler(c: Console):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json"):
            b = body if isinstance(body, bytes) else body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b)

        def _file(self, f: Path):
            """Serve one file with Range support (browsers need it to seek/loop video)."""
            data = f.read_bytes()
            ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
            rng, code, hdr = self.headers.get("Range"), 200, {}
            if rng and rng.startswith("bytes="):
                a, _, b = rng[6:].partition("-")
                start = int(a) if a else max(0, len(data) - int(b))
                end = min(int(b), len(data) - 1) if a and b else len(data) - 1
                hdr["Content-Range"] = f"bytes {start}-{end}/{len(data)}"
                data, code = data[start:end + 1], 206
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Accept-Ranges", "bytes")
            for k, v in hdr.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

        def _raw(self, limit=40 * 1024 * 1024) -> bytes:
            n = int(self.headers.get("Content-Length") or 0)
            if n > limit:
                raise pl.PipelineError("file too large", 413)
            return self.rfile.read(n) if n else b""

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}") if n else {}

        def _guard(self, fn):
            try:
                fn()
            except (pl.PipelineError, LibraryError) as e:
                self._json(e.code, {"error": str(e)})
            except (ValueError, KeyError, TypeError) as e:
                self._json(400, {"error": f"bad request: {e}"})

        def do_GET(self):
            self._guard(self._get)

        def do_POST(self):
            self._guard(self._post)

        def _get(self):
            path = unquote(urlparse(self.path).path)
            if path == "/":
                return self._send(200, INDEX.read_bytes(), "text/html; charset=utf-8")
            if path.startswith("/ui/") and path[4:] in UI_FILES:
                ct = UI_FILES[path[4:]]
                return self._send(200, (UI / path[4:]).read_bytes(), ct if ct.startswith("font") else ct + "; charset=utf-8")
            if path == "/api/library":
                return self._json(200, c.lib.snapshot())
            if path == "/api/projects":
                return self._json(200, {"projects": c.projects.list()})
            if path.startswith("/api/projects/"):
                return self._json(200, c.projects.get(path.split("/")[3]))
            if path.startswith("/proj/"):
                parts = path.strip("/").split("/")          # /proj/<id>/f/<n>
                if len(parts) == 4 and parts[2] == "f" and parts[3].isdigit():
                    return self._file(c.projects.frame_path(parts[1], int(parts[3])))
                if len(parts) == 4 and parts[2] == "mask" and parts[3].endswith(".png") and parts[3][:-4].isdigit():
                    return self._file(c.projects.mask_path(parts[1], int(parts[3][:-4])))
                raise pl.PipelineError("not found", 404)
            if path.startswith("/lib/"):
                root = c.lib.files.resolve()
                f = (root / path[5:]).resolve()
                if root not in f.parents:
                    raise pl.PipelineError("forbidden path", 400)
                if not f.is_file():
                    raise pl.PipelineError("not found", 404)
                return self._file(f)
            if path.startswith("/api/packs/") and path.endswith("/export"):
                data, rep = c.lib.export_wastickers(path.split("/")[3], cfg=c.cfg)
                name = next(p["name"] for p in c.lib.snapshot()["packs"] if p["id"] == path.split("/")[3])
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Content-Disposition", f'attachment; filename="{name}.wastickers"')
                self.send_header("X-Export-Report", json.dumps(rep, ensure_ascii=True))
                self.end_headers()
                self.wfile.write(data)
                return
            if path == "/api/inputs":
                return self._json(200, {"inputs": pl.list_inputs(c.inp)})
            if path == "/api/generations":
                return self._json(200, {"busy": c.lock.locked(), "health": c.health(), "paths": {"input": str(c.inp), "out": str(c.out)}, "generations": pl.summary(c.out)})
            if path.startswith("/api/generations/"):
                gid = int(path.rsplit("/", 1)[1])
                st = pl.state(c.out, gid)
                st["busy"] = c.lock.locked()
                return self._json(200, st)
            if path.startswith("/src/"):
                # read-only view of the prepared watch-folder video for the live preview; only files recorded in result.json
                parts = path.strip("/").split("/")
                src = pl.state(c.out, int(parts[1]))["source"]
                if parts[2:] == ["video"] and src.get("video_path"):
                    f = Path(src["video_path"])
                elif len(parts) == 4 and parts[2] == "clip":
                    f = next((Path(p) for fmt, p in (src.get("clips", {}).get(parts[3]) or {}).items() if fmt == "webm"), None)
                else:
                    f = None
                if not f or not f.is_file():
                    raise pl.PipelineError("not found", 404)
                return self._file(f)
            if path.startswith("/out/"):
                root = c.out.resolve()
                f = (root / path[5:]).resolve()
                if root not in f.parents:
                    raise pl.PipelineError("forbidden path", 400)
                if not f.is_file():
                    raise pl.PipelineError("not found", 404)
                ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
                return self._send(200, f.read_bytes(), ctype)
            raise pl.PipelineError("not found", 404)

        def _post_projects(self, path, query):
            pr, lib = c.projects, c.lib
            parts = path.strip("/").split("/")
            if parts == ["api", "projects"]:                       # raw video / GIF upload
                return self._json(200, pr.create(self._raw(MAX_UPLOAD), query.get("name", ["video.mp4"])[0]))
            if parts == ["api", "projects", "from_sticker"]:       # an animated sticker becomes an editable project
                b = self._body()
                f, s = lib.sticker_path(b["pack_id"], b["sticker_id"])
                if s["type"] != "animated":
                    raise LibraryError("only animated stickers can be opened as a video project")
                return self._json(200, pr.create(f.read_bytes(), s["name"] + f.suffix))
            if len(parts) == 3:
                return self._json(200, pr.update(parts[2], self._body()))
            if len(parts) == 4 and parts[3] == "delete":
                pr.delete(parts[2]); return self._json(200, {"ok": True})
            if len(parts) == 4 and parts[3] == "render":
                b = self._body()
                fmt = b.get("format", "webm")
                if b.get("save") and fmt != "webm":
                    raise LibraryError("only WebM can be saved into a pack (Telegram-style animated sticker)")
                data, mime, ext, info = pr.render(parts[2], fmt, decode_overlays(b.get("overlays")))
                sv = b.get("save")
                if sv:
                    if ext != "webm":
                        raise LibraryError("only WebM can be saved into a pack (Telegram-style animated sticker)")
                    proj = pr.get(parts[2])
                    st = lib.add_bytes(sv["pack_id"], data, "webm", sv.get("name") or proj["name"], "animated", sv.get("emoji") or "🙂",
                                       {"project": parts[2]})
                    pr.update(parts[2], {"packId": sv["pack_id"]})
                    return self._json(200, dict(st, info=info))
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("X-Render", json.dumps(info))
                self.send_header("Access-Control-Expose-Headers", "X-Render")
                self.end_headers()
                self.wfile.write(data)
                return
            raise pl.PipelineError("not found", 404)

        def _post_library(self, path, query):
            lib = c.lib
            if path == "/api/cutout":
                rgba, info = cutout(decode_image(self._raw()), c.cfg, query.get("method", ["auto"])[0])
                b = png_bytes(rgba)
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(b)))
                self.send_header("X-Cutout", json.dumps(info))
                self.send_header("Access-Control-Expose-Headers", "X-Cutout")
                self.end_headers()
                self.wfile.write(b)
                return True
            parts = path.strip("/").split("/")
            if parts[:2] != ["api", "packs"]:
                return False
            if len(parts) == 2:
                self._json(200, lib.create_pack(self._body().get("name", "")))
            elif len(parts) == 3:
                b = self._body()
                self._json(200, lib.update_pack(parts[2], b.get("name"), b.get("cover"), b.get("order")))
            elif len(parts) == 4 and parts[3] == "delete":
                lib.delete_pack(parts[2]); self._json(200, {"ok": True})
            elif len(parts) == 4 and parts[3] == "stickers":
                b = self._body()
                g = b.get("from_generation") or {}
                self._json(200, lib.add_from_generation(c.out, parts[2], int(g["id"]), int(g["index"]), g.get("kind", "static")))
            elif len(parts) == 4 and parts[3] == "render":   # raw PNG body = the editor's 512x512 canvas
                self._json(200, lib.add_render(parts[2], self._raw(), query.get("name", ["sticker"])[0], query.get("emoji", ["🙂"])[0], c.cfg,
                                               {"editor": True}))
            elif len(parts) == 5 and parts[3] == "stickers":
                b = self._body()
                self._json(200, lib.rename_sticker(parts[2], parts[4], b.get("name"), b.get("emoji")))
            elif len(parts) == 6 and parts[3] == "stickers" and parts[5] == "animate":
                b = self._body()
                fmt = b.get("format", "webm")
                res = lib.animate(parts[2], parts[4], b.get("start", 0), b.get("end", 3), b.get("fps", 12), fmt, bool(b.get("loop", True)), c.cfg,
                                  bool(b.get("save")), str(b.get("name", "")))
                if isinstance(res, dict):
                    self._json(200, res)
                else:
                    data, mime, ext, info = res
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("X-Animate", json.dumps(info))
                    self.send_header("Access-Control-Expose-Headers", "X-Animate")
                    self.end_headers()
                    self.wfile.write(data)
            elif len(parts) == 6 and parts[3] == "stickers" and parts[5] == "move":
                self._json(200, lib.move_sticker(parts[2], parts[4], str(self._body().get("to", ""))))
            elif len(parts) == 6 and parts[3] == "stickers" and parts[5] == "delete":
                lib.delete_sticker(parts[2], parts[4]); self._json(200, {"ok": True})
            else:
                return False
            return True

        def _post(self):
            u = urlparse(self.path)
            path = unquote(u.path)
            if path.startswith("/api/projects"):
                return self._post_projects(path, parse_qs(u.query))
            if path.startswith("/api/cutout") or path.startswith("/api/packs"):
                if self._post_library(path, parse_qs(u.query)):
                    return
                raise pl.PipelineError("not found", 404)
            body = self._body()
            if path == "/api/generations":
                prompt = str(body.get("prompt", "")).strip() or str(body.get("subject", "")).replace("_", " ").strip()
                if not prompt:
                    raise pl.PipelineError("prompt required")
                if c.lock.locked():
                    raise pl.PipelineError("busy", 409)
                gid = pl.start(prompt, c.out, c.inp, int(body["variant"]) if body.get("variant") else None)
                c.submit(lambda: pl.run_stills(c.out, gid, c.cfg, c.pace))
                return self._json(202, {"id": gid})
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[:2] == ["api", "generations"]:
                gid = int(parts[2])
                if parts[3] == "more":
                    if c.lock.locked():
                        raise pl.PipelineError("busy", 409)
                    new = pl.more(c.out, c.inp, gid)
                    c.submit(lambda: pl.run_stills(c.out, new, c.cfg, c.pace))
                    return self._json(202, {"id": new})
                if parts[3] == "animate":
                    scope, index = body.get("scope", "pack"), body.get("index")
                    index = int(index) if index is not None else None
                    res = pl.check_animate(c.out, gid, scope, index)
                    wanted = [index] if scope == "slice" else [s["index"] for s in res["stickers"] if s["status"] == "READY"]
                    if all(res["stickers"][i - 1]["anim_status"] == "READY" for i in wanted):
                        return self._json(200, {"noop": True, "message": "Already animated."})
                    c.submit(lambda: pl.run_animate(c.out, gid, c.cfg, scope, index, c.pace))
                    return self._json(202, {"id": gid, "noop": False})
            raise pl.PipelineError("not found", 404)
    return H


def serve(out: Path, inp: Path, port: int = 8770, pace: float = 0.0, cfg=None, block: bool = True):
    c = Console(out, inp, pace, cfg)
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(c))
    if not block:
        return srv, c
    print(f"Mirsal console on http://127.0.0.1:{srv.server_address[1]}  (input: {inp}  out: {out})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
