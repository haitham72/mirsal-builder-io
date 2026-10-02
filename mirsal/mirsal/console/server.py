"""Lifecycle Console server: stdlib http.server + one index.html. Binds 127.0.0.1. One background job at a time."""
from __future__ import annotations

import json
import mimetypes
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .. import export, gates, higgsfield, jobs, llm, model_catalog, prompter, sources, styles, tasks, telegram, usage, watch
from .. import pipeline as pl
from ..library import Library, LibraryError, cutout, decode_image, png_bytes
from ..engine.config import EngineConfig
from ..video_project import MAX_UPLOAD, Projects, decode_overlays
from ..writer_lock import WriterLock
from . import placeholders

UI = Path(__file__).parent
INDEX = UI / "index.html"            # the desktop builder: one page, one stdlib server, no build step
UI_FILES = {"studio.css": "text/css", "app.js": "text/javascript", "generate.js": "text/javascript", "history.js": "text/javascript", "telegram.js": "text/javascript", "packs.js": "text/javascript", "editor.js": "text/javascript", "animate.js": "text/javascript", "chat.js": "text/javascript", "agent.js": "text/javascript", "agent.css": "text/css", "prepare.js": "text/javascript", "live.js": "text/javascript", "composer.js": "text/javascript", "fonts/InterVariable.woff2": "font/woff2"}


class Console:
    def __init__(self, out: Path, inp: Path, pace: float = 0.0, cfg: EngineConfig | None = None):
        self.out, self.inp, self.pace, self.cfg = out, inp, pace, cfg or EngineConfig()
        self._writer = WriterLock(out, "mirsal serve").acquire()   # one writer of result.json per out/ (raises WriterBusy)
        self.lock = threading.Lock()   # held while a job runs
        self.started, self._stale_checked, self._stale = time.time(), 0.0, False
        self._health = None
        self.lib = Library(out)
        self.projects = Projects(out, self.cfg)
        self._acct = (0.0, None)
        self._jobs = []
        threading.Thread(target=self._warm_models, daemon=True).start()

    def release_writer(self) -> None:
        self._writer.release()

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

    def stale(self, root: Path | None = None) -> bool:
        """True when a Python file of this program was changed after this server started: Python reads code once, so this process is then running
        older code than the files on disk (the page itself is read from disk on every load, so it can be newer than the backend)."""
        now = time.time()
        if now - self._stale_checked > 3:
            self._stale_checked = now
            root = root or Path(__file__).resolve().parents[1]
            self._stale = any(f.stat().st_mtime > self.started for f in root.rglob("*.py") if "__pycache__" not in f.parts)
        return self._stale

    # ---------- Higgsfield: live generation (account, models, jobs fulfilled by the CLI) ----------
    def _warm_models(self) -> None:
        try:
            export.sync_all(self.out)
        except Exception:
            pass
        try:
            model_catalog.set_dump(higgsfield.load_models(self.out))
        except Exception:
            pass

    def hf_account(self) -> dict:
        now = time.time()
        if self._acct[1] is not None and now - self._acct[0] < 6:
            return self._acct[1]
        if not higgsfield.available():
            d = {"available": False, "error": "The Higgsfield CLI is not installed (npm i -g @higgsfield/cli, then higgsfield auth login)."}
        else:
            try:
                d = dict(higgsfield.account(), available=True)
            except higgsfield.HiggsError as e:
                d = {"available": True, "error": str(e)}
        d["spent_today"] = usage.spent_today(self.out)
        self._acct = (now, d)
        return d

    def fulfil_async(self, jid: str, after=None) -> None:
        def run():
            try:
                jobs.fulfil(self.out, jid, on_done=after)
            except Exception as e:                       # fulfil handles provider errors itself; this is a last net
                try:
                    jobs.fail(self.out, jid, f"unexpected: {e}")
                except Exception:
                    pass
            finally:
                self._acct = (0.0, None)                 # the balance changed: the next read asks Higgsfield again
                export.sync_recent(self.out)
        t = threading.Thread(target=run, daemon=True)
        self._jobs = [x for x in self._jobs if x.is_alive()] + [t]
        t.start()

    def wait_jobs(self, timeout: float = 60.0) -> None:
        """Wait for the background provider jobs (tests call this before they unplug their fake CLI)."""
        end = time.time() + timeout
        for t in list(self._jobs):
            t.join(max(0.0, end - time.time()))
        while self.lock.locked() and time.time() < end:          # the pipeline step that a finished job started (stills, slicing) too
            time.sleep(0.1)

    def _submit_when_free(self, fn, tries: int = 600) -> None:
        for _ in range(tries):
            try:
                return self.submit(fn)
            except pl.PipelineError:
                time.sleep(1)
        raise pl.PipelineError("the pipeline stayed busy for 10 minutes", 409)

    def start_from_job(self, job: dict) -> None:
        """A sheet job is DONE: run the unchanged stills run on the returned sheet, exactly as for a prepared sheet (the app never writes into the watch folders)."""
        t = tasks.read_task(self.out, job["task"])
        sheet = self.out / job["result"]["file"]
        pick = sources.Pick(subject=tasks.subject_of(t["plan"]), subject_id=t["id"], variant=1, n_variants=1, sheet=sheet, video=None)
        outline = (job.get("request") or {}).get("outline")
        req = job.get("request") or {}
        parent = req.get("parent")                         # a chat edit: the new batch is a child of the one it improves (lineage, never a copy)
        gid = pl.start(t["prompt"], self.out, self.inp, pick=pick, task=t, outline=int(outline) if outline is not None else None,
                       parent=int(str(parent).lstrip("G")) if parent else None, regen_of=req.get("regen_of") or None)
        tasks.link_generation(self.out, t["id"], gid)
        jobs.attach_generation(self.out, job["id"], gid)
        self._submit_when_free(lambda: pl.run_stills(self.out, gid, self.cfg, self.pace))

    def save_ref(self, data: bytes, name: str) -> dict:
        """Store an uploaded reference image as out/refs/R###.<ext> (a real image, at most 15 MB); the sheet job then lists it, so the run is reproducible."""
        import io
        from PIL import Image, UnidentifiedImageError
        try:
            im = Image.open(io.BytesIO(data))
            im.verify()
            fmt, size = (im.format or "").lower(), Image.open(io.BytesIO(data)).size
        except (UnidentifiedImageError, OSError, ValueError):
            raise pl.PipelineError("That file is not an image I can read (use PNG, JPG or WebP).", 400)
        ext = {"png": ".png", "jpeg": ".jpg", "webp": ".webp"}.get(fmt)
        if not ext:
            raise pl.PipelineError("Reference images must be PNG, JPG or WebP.", 400)
        d = self.out / "refs"
        d.mkdir(parents=True, exist_ok=True)
        n = max([int(f.stem[1:]) for f in d.glob("R*.*") if f.stem[1:].isdigit()] or [0]) + 1
        f = d / f"R{n:03d}{ext}"
        f.write_bytes(data)
        return {"id": f"R{n:03d}", "file": f"refs/{f.name}", "url": f"/out/refs/{f.name}", "width": size[0], "height": size[1], "bytes": len(data), "name": Path(name).name[:80]}

    def ref_files(self, ids) -> list[str]:
        out = []
        for i in ids or []:
            f = next(iter(sorted((self.out / "refs").glob(f"{str(i)}.*"))), None) if str(i).startswith("R") and str(i)[1:].isdigit() else None
            if not f:
                raise pl.PipelineError(f"No reference image {i}", 400)
            out.append(f"refs/{f.name}")
        if len(out) > 4:
            raise pl.PipelineError("Use at most 4 reference images.", 400)
        return out

    def _commit_edge_locked(self, gid: int, outline, erode, via: str = "apply") -> bool:
        """Make a stroke/trim real for the whole batch and SAVE A SNAPSHOT of it (result.json edge_history). The stills are re-rendered, the animations are re-cut from the
        stored video (or re-animated from a prepared one). The caller holds the pipeline lock. No-op when the batch already has exactly this edge."""
        res = pl.read_result(self.out, gid)
        was_o, was_e = res.get("outline_px", 0), res.get("erode_px", 0)
        o = was_o if outline is None else int(outline)
        e = was_e if erode is None else int(erode)
        if (o, e) == (was_o, was_e):
            return False
        pl.set_appearance(self.out, gid, self.cfg, o, e)
        res = pl.read_result(self.out, gid)
        hist = res.get("edge_history") or [{"outline": was_o, "erode": was_e, "ts": res.get("created"), "via": "initial"}]
        res["edge_history"] = hist + [{"outline": o, "erode": e, "ts": round(time.time(), 3), "via": via}]
        pl.write_result(self.out, gid, res)
        cfg = pl.cfg_for(res, self.cfg)
        if any(v["status"] == "SLICED" and v.get("video") for v in res["video_sheets"]):
            gates.reslice(self.out, gid, cfg, self.pace)
        elif res["source"].get("has_video") and any(st.get("anim_status") == "STALE" for st in res["stickers"]):
            pl.run_animate(self.out, gid, cfg, "pack", None, self.pace)
        export.sync_recent(self.out)
        return True

    def commit_edge(self, gid: int, outline, erode, via: str) -> bool:
        """The automatic moments an edge chosen in the Studio becomes real: when the video is generated from the image (via 'video') and when the stickers go into a pack
        (via 'pack'). Until then the sliders only preview."""
        if outline is None and erode is None:
            return False
        if not self.lock.acquire(blocking=False):
            raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
        try:
            return self._commit_edge_locked(gid, outline, erode, via)
        finally:
            self.lock.release()

    def video_prompt_for(self, gid: int, aid: str, loop: bool = False) -> str:
        """The Kling prompt for the sheet that was actually built: per-sticker motions for the approved slots only (empty slots get no motion)."""
        res = pl.read_result(self.out, gid)
        entry = gates.sheet_of(res, aid)
        try:
            plan = json.loads((pl.gen_dir(self.out, gid) / "prompts.json").read_text(encoding="utf-8"))
            slots = json.loads(json.dumps(plan["slots"]))
            slots["loop"] = bool(loop)                    # the choice made when the video is sent wins over the one saved with the plan
            slots["key_colour"] = res.get("key_colour") or "green"      # the screen the video sheet really has (blue only when the sheet came back blue)
            keep = set(entry["slots"])
            slots["cells"] = [c for c in slots["cells"] if c["pos"] in keep]
            if slots["cells"] and plan.get("template_id"):
                from .. import prompter
                return prompter.render_plan(slots, plan["template_id"], plan.get("template_version", 2))["video_prompt"]
        except (OSError, ValueError, KeyError):
            pass
        return entry.get("video_prompt") or res.get("video_prompt") or ""

    def attach_video_from_job(self, job: dict) -> None:
        req = job.get("request") or {}
        gid = int(str(job["generation"]).lstrip("G"))
        data = (self.out / job["result"]["file"]).read_bytes()
        gates.attach_video(self.out, gid, req["sheet"], data, f"{job['id']}.mp4")
        self._submit_when_free(lambda: gates.slice_video(self.out, gid, req["sheet"], self.cfg, self.pace))

    def live(self, what, body):
        """Live generation through the Higgsfield CLI. `cost` estimates, `sheet` reserves a task (the G1 approval) and starts the sheet job,
        `video` starts the Kling job for a built video sheet. The job runs in the background; the page polls /api/jobs/<id>."""
        if what not in ("cost", "sheet", "video"):
            raise pl.PipelineError("not found", 404)
        if not higgsfield.available():
            raise pl.PipelineError("The Higgsfield CLI is not installed (npm i -g @higgsfield/cli, then higgsfield auth login).", 503)
        kind = "video" if what == "video" or body.get("kind") == "video" else "image"
        try:
            model, params = model_catalog.resolve(kind, body.get("model"), body.get("options"))
            if what == "cost":
                try:
                    return {"credits": higgsfield.cost(model, params, "x"), "model": model, "params": params}
                except higgsfield.HiggsError as e:
                    return {"credits": None, "error": str(e), "model": model, "params": params}
            if what == "sheet":
                refs = self.ref_files(body.get("refs"))
                if refs and not model_catalog.find("image", model).get("refs"):
                    raise pl.PipelineError(f"{model_catalog.find('image', model)['label']} does not take reference images: pick another model or remove them.", 400)
                t = tasks.reserve(self.out, self.inp, body.get("prompt", ""), body.get("grid", "3x3"), body.get("style_id", "flat_vector"), bool(body.get("ai")), bool(body.get("loop")))
                prompt = t["plan"]["sheet_prompt"] + ("\n" + prompter.REFERENCE_CLAUSE if refs else "")
                est = higgsfield.cost(model, params, prompt, **({"image_references": [str(self.out / r) for r in refs]} if refs else {}))
                job = jobs.create(self.out, "sheet", task=t["id"], request={
                    "model": model, "options": body.get("options") or {}, "prompt": prompt, "label": t["prompt"], "refs": refs,
                    "outline": int(body["outline"]) if body.get("outline") is not None else None,
                "parent": body.get("parent") or None, "regen_of": body.get("regen_of") or None})
                self.fulfil_async(job["id"], after=self.start_from_job)
                return {"job": job["id"], "task": t["id"], "estimate": est, "model": model, "params": params,
                        "expanded_by": t["plan"].get("expanded_by"), "expand_error": t["plan"].get("expand_error")}
            gid = int(body["generation"])
            self.commit_edge(gid, body.get("outline"), body.get("erode"), "video")             # the edge chosen in the Studio becomes real here
            aid = str(body.get("sheet") or "")
            fill = None if body.get("slot_fill") is None else min(0.92, max(0.5, float(body["slot_fill"])))
            loop = bool(body.get("loop"))
            if not aid:                      # one click: approve the kept stills, build the video sheet and approve it (the click is the decision), as "Make a video" did
                if self.lock.locked():
                    raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                from dataclasses import replace as _replace
                cfg_v = self.cfg if fill is None else _replace(self.cfg, slot_fill=fill)
                cur = gates.active_sheet(pl.read_result(self.out, gid))
                if cur and cur["status"] in ("BUILT", "APPROVED") and not cur.get("video") and fill is not None \
                        and abs(float(cur.get("slot_fill") or self.cfg.slot_fill) - fill) > 0.004:      # the gap was changed: a new sheet, the old one is rejected (never deleted)
                    gates.review(self.out, gid, "video_sheet", "REJECT", cur["id"], "gap changed before sending")
                aid = gates.quick_sheet(self.out, gid, cfg_v)["sheet"]
            res = pl.read_result(self.out, gid)
            entry = gates.sheet_of(res, aid)
            if entry.get("status") not in ("APPROVED", "VIDEO_BLOCKED"):
                raise pl.PipelineError(f"{aid} is {entry.get('status')}: approve the video sheet (G3) first, a human decides before anything is sent to be animated "
                                       "(a sheet that already has its video sliced cannot be animated again).", 409)
            start = pl.gen_dir(self.out, gid) / entry["file"]
            est = higgsfield.cost(model, params, "x", start_image=str(start))
            job = jobs.create(self.out, "video", task=res.get("task"), generation=f"G{gid:03d}", request={
                "model": model, "options": body.get("options") or {}, "prompt": self.video_prompt_for(gid, aid, loop),
                "start_image": str(start), "sheet": aid, "label": res.get("prompt", ""), "loop": loop})
            self.fulfil_async(job["id"], after=self.attach_video_from_job)
            return {"job": job["id"], "estimate": est, "model": model, "params": params}
        except (higgsfield.HiggsError, jobs.JobError, model_catalog.CatalogError) as e:
            raise pl.PipelineError(str(e), getattr(e, "code", 400))

    def idem(self, scope: str, key, fn):
        """Idempotency (Phase 5A): the same Idempotency-Key within 24 h returns the first answer and runs nothing again. The key is scoped
        (a generation create and a chat message never collide) and held under a lock while the first request runs. No key: just run."""
        key = str(key or "").strip()
        if not key:
            return fn()
        from .. import cache as cachemod
        cc = cachemod.default()
        ck = cc.key("idem", scope, cachemod.digest(key))
        try:
            with cc.lock("idem:" + ck, 30_000):
                hit = cc.get(ck, "idem")
                if hit is not None:
                    return dict(hit, idempotent=True)
                r = fn()
                cc.set(ck, r, 24 * 3600)
                return r
        except cachemod.Busy:
            raise pl.PipelineError("a request with this Idempotency-Key is still running", 409)

    # ---------- the agentic chat (Phase 4): sessions with memory, the graph over this same engine ----------
    def chat_parts(self):
        from ..agent import graph as ag
        from ..agent.brain import Brain
        from ..agent.memory import SessionStore
        from ..agent.tools import ConsoleTools
        store = SessionStore(self.out)
        tools = ConsoleTools(self)
        return store, tools, ag.Agent(store, tools, Brain(out=self.out)), ag

    def chat_send(self, sid: str, body: dict) -> dict:
        """Start one turn in the background and answer at once: the page polls the session and sees the steps as they are written."""
        store, tools, agent, _ = self.chat_parts()
        text = str(body.get("text") or "")
        action = body.get("action") if isinstance(body.get("action"), dict) else None
        if not text.strip() and not action:
            raise pl.PipelineError("say something first")
        turn = agent.prepare(sid, text, [str(x) for x in (body.get("selected") or [])], action)      # 409 when the last message is still running
        t = threading.Thread(target=agent.execute, args=(turn,), daemon=True)
        self._chat_threads = [x for x in getattr(self, "_chat_threads", []) if x.is_alive()] + [t]
        t.start()
        return {"id": sid, "message": turn.msg["id"]}

    def wait_chat(self, timeout: float = 60.0) -> None:
        end = time.time() + timeout
        for t in list(getattr(self, "_chat_threads", [])):
            t.join(max(0.0, end - time.time()))

    def submit(self, fn) -> None:
        if not self.lock.acquire(blocking=False):
            raise pl.PipelineError("busy", 409)

        def run():
            try:
                fn()
            finally:
                self.lock.release()
                export.sync_recent(self.out)
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

        def _sse(self, gid: int, after: str):
            """Server-sent events for one generation from the Redis stream (replay after Last-Event-ID, a ping every ~5 s, ends at pack_complete /
            generation_failed or after 10 minutes). The generation keeps running when the browser goes away."""
            from .. import events
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            end, idle, last = time.time() + 600, 0, after
            try:
                while time.time() < end:
                    rows = events.read(gid, last)
                    if rows:
                        for sid, payload in rows:
                            self.wfile.write(events.sse_frame(sid, payload))
                            last = sid
                        self.wfile.flush()
                        idle = 0
                        if any(p.get("event") in events.TERMINAL for _, p in rows):
                            return
                    else:
                        idle += 1
                        if idle % 25 == 0:
                            self.wfile.write(b": ping\n\n")
                            self.wfile.flush()
                        time.sleep(0.2)
            except (BrokenPipeError, ConnectionResetError, OSError):
                return

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

        def _foreign(self) -> str | None:
            """Why this request must not be served, or None. The server binds 127.0.0.1 only, but a page the owner visits can still
            POST to it from the browser (trash, the Telegram config, bulk delete) and a DNS-rebinding page can read it: so the Host
            must be our own and a browser-sent Origin on anything that is not a read must be our own too. A client that sends no
            Origin (curl, the tests, the CLI) passes; a browser always sends one on a cross-origin POST."""
            port = self.server.server_address[1]
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
            if (self.headers.get("Host") or "").lower() not in hosts:
                return "unexpected Host header"
            if self.command in ("GET", "HEAD", "OPTIONS"):
                return None
            origin = self.headers.get("Origin")
            if origin is not None and origin.lower() not in {f"http://{h}" for h in hosts}:
                return "cross-origin request refused"
            if (self.headers.get("Sec-Fetch-Site") or "same-origin") not in ("same-origin", "none"):
                return "cross-site request refused"
            return None

        def _unauth(self) -> bool:
            """MIRSAL_API_TOKEN (Phase 5C): when it is set, a caller that is not this server's own page (a browser sends Sec-Fetch-Site: same-origin
            for the Studio) must send `Authorization: Bearer <token>`. Unset = the local sandbox behaves as before."""
            import hmac
            import os as _os
            tok = _os.environ.get("MIRSAL_API_TOKEN", "")
            if not tok or self.headers.get("Sec-Fetch-Site") == "same-origin":
                return False
            auth = self.headers.get("Authorization") or ""
            got = auth[7:] if auth.startswith("Bearer ") else ""
            return not hmac.compare_digest(got.encode(), tok.encode())

        def _guard(self, fn):
            why = self._foreign()
            if why:
                return self._json(403, {"error": why})
            if self._unauth():
                return self._json(401, {"error": "an API token is required (Authorization: Bearer <token>)"})
            try:
                fn()
            except (pl.PipelineError, LibraryError, watch.WatchError, telegram.TelegramError) as e:
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
            gp = path.strip("/").split("/")
            if len(gp) == 4 and gp[:2] == ["api", "generations"] and gp[3] == "events" and gp[2].isdigit():      # SSE: stream ids are the event ids
                q = parse_qs(urlparse(self.path).query)
                return self._sse(int(gp[2]), (q.get("after", [""])[0] or self.headers.get("Last-Event-ID") or "0-0"))
            if path.startswith("/api/assets/") and len(gp) == 3:        # a short-lived signed link (see POST /api/assets/sign)
                from ..store.assets import AssetError, LocalAssetStore
                try:
                    store = LocalAssetStore(c.out)
                    f = store.path(store.verify(gp[2]))
                except AssetError as e:
                    return self._json(e.code, {"error": str(e)})
                if not f.is_file():
                    return self._json(404, {"error": "no such asset"})
                return self._file(f)
            if path == "/api/telegram":      # connected or not and which bot: never the token
                return self._json(200, telegram.status(c.out))
            if path.startswith("/api/packs/") and path.endswith("/telegram"):          # dry run: what would be created, every problem
                st = telegram.status(c.out)
                name = parse_qs(urlparse(self.path).query).get("name", [None])[0]
                return self._json(200, dict(telegram.plan(c.lib, path.split("/")[3], st["bot"], name, c.cfg), status=st))
            if path.startswith("/api/packs/") and path.endswith("/telegram.zip"):      # no-credentials fallback: files for @stickers
                data, name = telegram.zip_for_stickers_bot(c.lib, path.split("/")[3])
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Content-Disposition", f'attachment; filename="{name}-for-stickers-bot.zip"')
                self.end_headers()
                self.wfile.write(data)
                return
            if path == "/api/watch":       # History: the real watch folders, image and video side by side, plus the trash
                return self._json(200, {"images": str(c.inp / "Images_gen"), "videos": str(c.inp / "videos_gen"),
                                        "rows": watch.list_rows(c.inp, c.out, pl.generations_by_folder(c.out)), "trash": watch.list_trash(c.out)})
            if path.startswith("/api/watch/thumb/"):
                f = watch.thumb_path(c.inp, c.out, path.rsplit("/", 1)[1])
                return self._send(200, f.read_bytes(), "image/jpeg")
            if path == "/api/tasks":
                return self._json(200, {"tasks": tasks.list_tasks(c.out)})
            if path.startswith("/api/tasks/"):
                return self._json(200, tasks.read_task(c.out, path.rsplit("/", 1)[1]))
            if path == "/api/inbox":
                return self._json(200, tasks.inbox(c.out, c.inp))
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
            if path == "/api/ai":          # is the model available (never the key)
                return self._json(200, llm.status())
            if path == "/api/chat/agent":     # which model runs the chat, and whether the vision judge is up
                from ..agent import brain as _brain
                return self._json(200, {"agent": _brain.target(), "vision": __import__("mirsal.vision.judge", fromlist=["status"]).status(),
                                        "live": higgsfield.available()})
            if path == "/api/chat/sessions":
                return self._json(200, {"sessions": c.chat_parts()[0].list()})
            if path.startswith("/api/chat/sessions/") and len(path.strip("/").split("/")) == 4:
                from ..agent.memory import SessionError as _SE
                store, tools, _agent, ag = c.chat_parts()
                try:
                    return self._json(200, ag.hydrate(store, tools, store.load(path.rsplit("/", 1)[1])))
                except _SE as e:
                    raise pl.PipelineError(str(e), e.code)
            if path in ("/api/health", "/api/health/models", "/api/health/storage"):     # what is this app connected to, and is it healthy
                from .. import health as _h
                if path.endswith("/models"):
                    return self._json(200, _h.models())
                if path.endswith("/storage"):
                    return self._json(200, _h.storage(c.out))
                return self._json(200, _h.snapshot(c.out))
            if path == "/api/vision":        # the vision judge: which model, which policy
                from ..vision import judge as _vj
                return self._json(200, _vj.status())
            if path == "/api/search":
                q = parse_qs(urlparse(self.path).query).get("q", [""])[0]
                try:  # Phase 3A: Postgres search when serving the real out/ with the database up, else files
                    from ..store import db as _db, repo as _repo, sync as _sync
                    import os as _os
                    if _sync.is_default_out(c.out) and _os.environ.get("MIRSAL_DB_WRITE", "") not in ("0", "no", "off", "false") and _db.available():
                        with _db.connect() as _c:
                            rows = _repo.search(_c, q)
                        return self._json(200, {"results": [{
                            "generation": r["generation_id"], "id": int(r["generation_id"][1:]),
                            "index": r["idx"], "key": r["key"], "tags": r["tags"], "name": r["name"],
                            "task_slug": r["task_slug"], "status": r["status"], "reason": None,
                            "review": {"still": r["still_review"], "anim": r["anim_review"]},
                            "anim_status": r["animation_status"], "png": r["png"] or "", "webm": r["webm"] or "",
                            "emoji": "".join(r["emoji"]), "final": r["still_review"] == "APPROVED" and (
                                r["animation_status"] == "NOT_REQUESTED" or r["anim_review"] == "APPROVED"),
                            "via": "postgres"} for r in rows], "via": "postgres"})
                except Exception:
                    pass
                return self._json(200, {"results": gates.search(c.out, q), "via": "files"})
            if path == "/api/inputs":
                return self._json(200, {"inputs": pl.list_inputs(c.inp)})
            if path.startswith("/api/generations/") and path.endswith("/files"):         # where this batch's files are (the named folder for copy and paste)
                gid = int(path.split("/")[3])
                res = pl.read_result(c.out, gid)
                pk = export.package_dir(c.out, res)
                return self._json(200, {"package": str(pk) if pk and pk.is_dir() else None, "stickers": str(pl.gen_dir(c.out, gid) / "slices"), "batch": str(pl.gen_dir(c.out, gid))})
            if path.startswith("/api/generations/") and path.endswith("/edge_preview"):         # ONE sticker with a stroke/trim, rendered on the fly (a preview, never stored)
                q = parse_qs(urlparse(self.path).query)
                png = pl.edge_preview(c.out, int(path.split("/")[3]), int(q.get("index", ["1"])[0]), int(q.get("outline", ["0"])[0]), int(q.get("erode", ["0"])[0]), int(q.get("px", ["420"])[0]))
                return self._send(200, png, "image/png")
            if path.startswith("/api/generations/") and path.endswith("/sheet_preview"):      # the video sheet at a given fill, small and not stored
                q = parse_qs(urlparse(self.path).query)
                fill = min(0.92, max(0.5, float(q.get("fill", [c.cfg.slot_fill])[0])))
                png = gates.preview_sheet(c.out, int(path.split("/")[3]), c.cfg, fill, int(q.get("px", ["420"])[0]))
                return self._send(200, png, "image/png")
            if path == "/api/history":              # the Studio's persistent history of batches, a page at a time
                q = parse_qs(urlparse(self.path).query)
                return self._json(200, pl.history(c.out, int(q.get("offset", ["0"])[0]), int(q.get("limit", ["5"])[0])))
            if path == "/api/higgsfield":          # is the CLI there, the balance, today's spend (never a credential)
                return self._json(200, c.hf_account())
            if path == "/api/models":              # the selector: curated models + every other Higgsfield model, and the style presets
                return self._json(200, dict(model_catalog.catalog(), styles=styles.PRESETS, default_style=styles.DEFAULT, slot_fill=c.cfg.slot_fill))
            if path == "/api/usage":
                return self._json(200, usage.summary(c.out, int(parse_qs(urlparse(self.path).query).get("limit", ["100"])[0])))
            if path.startswith("/assets/"):
                parts = path.strip("/").split("/")
                a = placeholders.find(parts[1], parts[2]) if len(parts) == 3 else None
                if not a:
                    raise pl.PipelineError("not found", 404)
                return self._send(200, a[0], a[1])
            if path == "/api/jobs":      # S2: jobs for the operator (Generate page polls while waiting)
                st = parse_qs(urlparse(self.path).query).get("status", [None])[0]
                return self._json(200, {"jobs": jobs.list(c.out, st), "typical": usage.typical(c.out)})
            if path.startswith("/api/jobs/") and len(path.strip("/").split("/")) == 3:
                try:
                    return self._json(200, jobs.read(c.out, path.strip("/").split("/")[2]))
                except jobs.JobError as e:
                    raise pl.PipelineError(str(e), e.code)
            if path == "/api/generations":
                return self._json(200, {"busy": c.lock.locked(), "health": c.health(), "paths": {"input": str(c.inp), "out": str(c.out)}, "stale": c.stale(), "generations": pl.summary(c.out)})
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
                if sv and sv.get("replace"):            # the project of a pack sticker: put the result back into that sticker
                    rp = sv["replace"]
                    return self._json(200, dict(lib.replace_file(rp["pack_id"], rp["sticker_id"], data, "webm"), info=info))
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
            elif len(parts) == 4 and parts[3] == "telegram":     # create the pack on Telegram (or add what is new to it)
                self._json(200, telegram.send(c.out, lib, parts[2], (self._body().get("name") or None), c.cfg))
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

        def _post_video(self, gid, aid, query):
            """Raw video body, attached to video sheet A<n> (not matched by filename); slicing runs as the background job."""
            if c.lock.locked():
                raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
            data = self._raw(MAX_UPLOAD)
            gates.attach_video(c.out, gid, aid, data, query.get("name", ["video.mp4"])[0])
            c.submit(lambda: gates.slice_video(c.out, gid, aid, c.cfg, c.pace))
            return self._json(202, {"id": gid, "sheet": aid})

        def _live(self, what, body):
            return c.live(what, body)

        def _post(self):
            u = urlparse(self.path)
            path = unquote(u.path)
            if path.startswith("/api/projects"):
                return self._post_projects(path, parse_qs(u.query))
            if path.startswith("/api/cutout") or path.startswith("/api/packs"):
                if self._post_library(path, parse_qs(u.query)):
                    return
                raise pl.PipelineError("not found", 404)
            if path == "/api/live/ref":          # a reference image for the next sheet (raw body, ?name=file.png)
                return self._json(200, c.save_ref(self._raw(15 * 1024 * 1024), parse_qs(u.query).get("name", ["ref.png"])[0]))
            parts = path.strip("/").split("/")
            if len(parts) == 6 and parts[:2] == ["api", "generations"] and parts[3:4] == ["video_sheet"] and parts[5] == "video":
                return self._post_video(int(parts[2]), parts[4], parse_qs(u.query))
            body = self._body()
            if path == "/api/telegram/config":
                return self._json(200, telegram.save_config(c.out, str(body.get("token", "")), str(body.get("user_id", ""))))
            if path == "/api/telegram/disconnect":
                return self._json(200, telegram.disconnect(c.out))
            if path == "/api/stickers/delete":      # bulk delete from the library: [{pack_id, id}, ...]
                return self._json(200, {"deleted": c.lib.delete_stickers([x for x in body.get("items", []) if isinstance(x, dict)])})
            if path == "/api/watch/remove":      # to the trash, never straight to nothing
                return self._json(200, watch.remove(c.inp, c.out, str(body.get("number", "")), str(body.get("subject", ""))))
            if path == "/api/watch/restore":
                return self._json(200, watch.restore(c.inp, c.out, str(body.get("id", ""))))
            if path == "/api/watch/purge":
                return self._json(200, watch.purge(c.out, str(body.get("id", ""))))
            if path == "/api/plan":      # preview only: nothing is reserved
                return self._json(200, tasks.preview(body.get("prompt", ""), body.get("grid", "3x3"), body.get("style_id", "flat_vector"), bool(body.get("ai")), bool(body.get("loop"))))
            if path == "/api/tasks":     # reserve: the next folder names + out/tasks/<NNN>.json (this is the G1 approval)
                return self._json(200, tasks.reserve(c.out, c.inp, body.get("prompt", ""), body.get("grid", "3x3"), body.get("style_id", "flat_vector"), bool(body.get("ai")), bool(body.get("loop"))))
            if path.startswith("/api/chat/sessions"):
                from ..agent.memory import SessionError as _SE
                cp = path.strip("/").split("/")
                store = c.chat_parts()[0]
                try:
                    if cp == ["api", "chat", "sessions"]:
                        return self._json(200, store.create(body.get("title"), body.get("settings") if isinstance(body.get("settings"), dict) else None))
                    if len(cp) == 5 and cp[4] == "messages":
                        return self._json(202, c.idem("chat:" + cp[3], self.headers.get("Idempotency-Key"), lambda: c.chat_send(cp[3], body)))
                    if len(cp) == 5 and cp[4] == "settings":
                        sess = store.load(cp[3])
                        allowed = {"grid": ("2x2", "3x3"), "ask_before_spending": (True, False), "ai": (True, False)}
                        for k, v in body.items():
                            if k in allowed and v in allowed[k]:
                                sess["settings"][k] = v
                            elif k == "style_id" and isinstance(v, str):
                                sess["settings"][k] = v
                        store.save(sess)
                        return self._json(200, {"settings": sess["settings"]})
                    if len(cp) == 5 and cp[4] == "delete":
                        store.delete(cp[3])
                        return self._json(200, {"deleted": cp[3]})
                except _SE as e:
                    raise pl.PipelineError(str(e), e.code)
                raise pl.PipelineError("not found", 404)
            if path.startswith("/api/live/"):
                return self._json(200, self._live(path.rsplit("/", 1)[1], body))
            if path == "/api/jobs":      # S2: the Generate page creates a sheet job ("Generate it"), the operator fulfils it
                try:
                    return self._json(200, jobs.create(c.out, str(body.get("kind", "sheet")),
                                                       task=body.get("task"), generation=body.get("generation"),
                                                       request=body.get("request") or {}))
                except jobs.JobError as e:
                    raise pl.PipelineError(str(e), e.code)
            jp = path.strip("/").split("/")
            if len(jp) == 4 and jp[:2] == ["api", "jobs"]:
                try:
                    act = jp[3]
                    if act == "claim":
                        return self._json(200, jobs.claim(c.out, jp[2], str(body.get("ticket", ""))))
                    if act == "done":
                        return self._json(200, jobs.done(c.out, jp[2], str(body.get("file", "")),
                                                         str(body.get("model", "")), body.get("cost")))
                    if act == "fail":
                        return self._json(200, jobs.fail(c.out, jp[2], str(body.get("reason", ""))))
                    if act == "requeue":
                        return self._json(200, jobs.requeue(c.out, jp[2]))
                    if act == "retry":           # a human retry: same Higgsfield job when it has a ticket (no second charge), else a fresh request
                        job = jobs.resume(c.out, jp[2])
                        c.fulfil_async(job["id"], after=c.start_from_job if job["kind"] == "sheet" else c.attach_video_from_job if job["kind"] == "video" else None)
                        return self._json(200, job)
                except jobs.JobError as e:
                    raise pl.PipelineError(str(e), e.code)
                raise pl.PipelineError("not found", 404)
            if path == "/api/generations" and body.get("task"):      # Run: a generation linked to its reserved task
                if c.lock.locked():
                    raise pl.PipelineError("busy", 409)
                t = tasks.read_task(c.out, body["task"])
                gid = pl.start(t["prompt"], c.out, c.inp, pick=tasks.pick_for_task(c.inp, t, int(body.get("take", 0))), task=t,
                               outline=int(body["outline"]) if body.get("outline") is not None else None,
                               erode=int(body["erode"]) if body.get("erode") is not None else None)
                tasks.link_generation(c.out, t["id"], gid)
                c.submit(lambda: pl.run_stills(c.out, gid, c.cfg, c.pace))
                return self._json(202, {"id": gid})
            if path == "/api/assets/sign":      # {key, ttl?}: a signed, expiring link to one file under out/ (never a path the page invents)
                from ..store.assets import AssetError, LocalAssetStore
                store = LocalAssetStore(c.out)
                try:
                    key = str(body.get("key") or "")
                    if not store.exists(key):
                        raise AssetError("no such asset", 404)
                    ttl = max(5, min(int(body.get("ttl", 300)), 3600))
                    return self._json(200, {"url": store.url(key, ttl), "expires_in": ttl})
                except AssetError as e:
                    raise pl.PipelineError(str(e), e.code)
            if path == "/api/generations":
                prompt = str(body.get("prompt", "")).strip() or str(body.get("subject", "")).replace("_", " ").strip()
                if not prompt:
                    raise pl.PipelineError("prompt required")

                def create():
                    if c.lock.locked():
                        raise pl.PipelineError("busy", 409)
                    gid = pl.start(prompt, c.out, c.inp, int(body["variant"]) if body.get("variant") else None,
                                   outline=int(body["outline"]) if body.get("outline") is not None else None,
                                   erode=int(body["erode"]) if body.get("erode") is not None else None)
                    pl.approve_plan(c.out, gid, "approved by pressing Generate")
                    c.submit(lambda: pl.run_stills(c.out, gid, c.cfg, c.pace))
                    return {"id": gid}
                return self._json(202, c.idem("generation", self.headers.get("Idempotency-Key"), create))
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[:2] == ["api", "generations"]:
                gid = int(parts[2])
                if parts[3] == "more":
                    if c.lock.locked():
                        raise pl.PipelineError("busy", 409)
                    new = pl.more(c.out, c.inp, gid)
                    c.submit(lambda: pl.run_stills(c.out, new, c.cfg, c.pace))
                    return self._json(202, {"id": new})
                if parts[3] == "review":
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    return self._json(200, gates.review(c.out, gid, str(body.get("gate", "")), str(body.get("decision", "")), body.get("index"), body.get("note")))
                if parts[3] == "appearance":
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    res_ = pl.set_appearance(
                        c.out, gid, c.cfg,
                        int(body["outline"]) if body.get("outline") is not None else None,
                        int(body["erode"]) if body.get("erode") is not None else None)
                    export.sync_recent(c.out)
                    if body.get("reslice") and any(v["status"] == "SLICED" and v.get("video") for v in pl.read_result(c.out, gid)["video_sheets"]):
                        c.submit(lambda: gates.reslice(c.out, gid, pl.cfg_for(pl.read_result(c.out, gid), c.cfg), c.pace))
                        res_["resliced"] = True
                    return self._json(200, res_)
                if parts[3] == "reveal":         # open the batch's named folder in the file manager (a path the server computed, never one sent by the page)
                    import os as _os, subprocess as _sp, sys as _sys
                    res = pl.read_result(c.out, gid)
                    pk = export.package_dir(c.out, res)
                    target = pk if pk and pk.is_dir() else pl.gen_dir(c.out, gid) / "slices"
                    if _sys.platform == "win32":
                        _os.startfile(str(target))
                    else:
                        _sp.Popen(["open" if _sys.platform == "darwin" else "xdg-open", str(target)])
                    return self._json(200, {"opened": str(target)})
                if parts[3] == "allow":          # a human allows (or takes back) an animation Python blocked for leaving or crossing its slot
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    allow = bool(body.get("allow", True))
                    idx = gates.allowable(pl.read_result(c.out, gid), allow) if body.get("all") else [int(body["index"])]
                    if not idx:
                        raise pl.PipelineError("There is nothing to allow." if allow else "Nothing was allowed in this batch.", 409)
                    for i in idx:
                        gates.check_allow(c.out, gid, i, allow)
                    c.submit(lambda: gates.allow_animations(c.out, gid, idx, allow, pl.cfg_for(pl.read_result(c.out, gid), c.cfg), c.pace))
                    return self._json(202, {"id": gid, "indexes": idx, "index": idx[0], "allow": allow})
                if parts[3] == "edge":           # Apply / Undo: save a snapshot of the edge and apply it to the whole batch (in the background)
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    o, e = body.get("outline"), body.get("erode")
                    if o is None and e is None:
                        raise pl.PipelineError("outline or erode required")
                    via = "undo" if body.get("via") == "undo" else "apply"
                    c.submit(lambda: c._commit_edge_locked(gid, o, e, via))
                    return self._json(202, {"id": gid})
                if parts[3] == "reslice":        # apply the batch's current edge to the animations again, from the stored video (no credits)
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    c.submit(lambda: gates.reslice(c.out, gid, pl.cfg_for(pl.read_result(c.out, gid), c.cfg), c.pace))
                    return self._json(202, {"id": gid})
                if parts[3] == "video_sheet":
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    return self._json(200, gates.build_sheet(c.out, gid, c.cfg))
                if parts[3] == "regen":
                    if c.lock.locked():
                        raise pl.PipelineError("busy", 409)
                    new = pl.regen(c.out, c.inp, gid, int(body["index"]), body.get("subject"))
                    c.submit(lambda: pl.run_stills(c.out, new, c.cfg, c.pace))
                    return self._json(202, {"id": new})
                if parts[3] == "judge":          # the vision model pre-reviews the stickers (S6): history lines only, a human still decides
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    from ..vision import judge as _vj
                    if _vj.status()["provider"] == "none":
                        raise pl.PipelineError("No vision backend: start LM Studio (MIRSAL_LOCAL_URL) or set OPENAI_API_KEY.", 409)
                    scope = "anim" if body.get("scope") == "anim" else "still"
                    c.submit(lambda: _vj.judge_generation(c.out, gid, scope, force=bool(body.get("force"))))
                    return self._json(202, {"id": gid, "scope": scope})
                if parts[3] == "quick_sheet":
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    return self._json(200, gates.quick_sheet(c.out, gid, c.cfg))
                if parts[3] == "recheck":    # judge animations made before the border check existed (decode + key only)
                    if not c.lock.acquire(blocking=False):
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    try:
                        return self._json(200, pl.recheck_bounds(c.out, gid, c.cfg))
                    finally:
                        c.lock.release()
                if parts[3] == "studio_edit":    # layered edit of a sticker with an animation: open (-> project id) / commit (-> image + animation updated)
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    if body.get("action") == "commit":
                        return self._json(200, pl.studio_edit_commit(c.out, gid, int(body["index"]), c.projects, decode_overlays(body.get("overlays")), c.cfg, c.lib))
                    return self._json(200, pl.studio_edit_open(c.out, gid, int(body["index"]), c.projects, c.cfg))
                if parts[3] == "edit":       # the sticker editor, opened from Generate: save the still in place
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    import base64
                    png = base64.b64decode(str(body.get("png", "")).split(",", 1)[-1] or b"")
                    return self._json(200, pl.edit_still(c.out, gid, int(body["index"]), png, c.cfg, c.lib))
                if parts[3] == "drop":
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    return self._json(200, gates.drop(c.out, gid, int(body["index"]), bool(body.get("dropped", True))))
                if parts[3] == "add":
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    c.commit_edge(gid, body.get("outline"), body.get("erode"), "pack")        # the edge chosen in the Studio becomes real here
                    return self._json(200, gates.quick_add(c.out, gid, c.lib, body.get("pack_id"), body.get("pack_name"), "replace" if body.get("mode") == "replace" else "add",
                                                   {str(k): v for k, v in (body.get("names") or {}).items() if isinstance(v, dict)}))
                if parts[3] == "pack_add":
                    return self._json(200, c.lib.add_final(c.out, str(body["pack_id"]), gid))
                if parts[3] == "animate":
                    scope, index = body.get("scope", "pack"), body.get("index")
                    index = int(index) if index is not None else None
                    res = pl.check_animate(c.out, gid, scope, index)
                    wanted = [index] if scope == "slice" else [s["index"] for s in res["stickers"] if s["status"] == "READY" and s["review"]["still"] != "REJECTED"]
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
