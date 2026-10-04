"""Lifecycle Console server: stdlib http.server + one index.html. Binds 127.0.0.1. One background job at a time."""
from __future__ import annotations

import contextvars
import json
import mimetypes
import os
import re
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from ..flow import batches, effects as fx_flow, gates, groups, metrics, particle_sets as fx_sets, purge, sources, sticker_history, watch
from ..generation import higgsfield, jobs, model_catalog, prompter, styles, tasks, usage
from ..services import llm, telegram
from ..vision import consent as vision_consent, transcribe
from ..flow import pipeline as pl
from ..media.library import Library, LibraryError, cutout, decode_image, png_bytes
from ..engine.config import EngineConfig
from ..runtime.users import LOCAL, UserError, UserStore
from ..store import idem as idem_store
from ..media.video_project import MAX_UPLOAD, Projects, decode_overlays
from ..runtime.writer_lock import WriterLock
from . import placeholders
from .openapi import VERSION as API_VERSION

UI = Path(__file__).parent
INDEX = UI / "index.html"            # the desktop builder: one page, one stdlib server, no build step
UI_FILES = {"studio.css": "text/css", "app.js": "text/javascript", "generate.js": "text/javascript", "history.js": "text/javascript", "telegram.js": "text/javascript", "packs.js": "text/javascript", "editor.js": "text/javascript", "animate.js": "text/javascript", "chat.js": "text/javascript", "agent.js": "text/javascript", "agent.css": "text/css", "prepare.js": "text/javascript", "effects.js": "text/javascript", "particles.js": "text/javascript", "welcome.js": "text/javascript", "live.js": "text/javascript", "composer.js": "text/javascript", "trash.js": "text/javascript", "tickets.js": "text/javascript", "auth.js": "text/javascript", "trending.js": "text/javascript", "sheet-recovery.js": "text/javascript", "job-recovery.js": "text/javascript", "fonts/InterVariable.woff2": "font/woff2"}


# What a `member` may reach (owners reach everything). Anything not listed here is owner-only: the library, packs, projects, Telegram, watch folders,
# usage and balance, tasks, the operator's job actions and the user list. Generation paths are checked for ownership too (a stranger's batch is a 404).
_GEN_PATH = re.compile(r"^/api/generations/(\d+)(?:/(\w+))?$")
NO_ROUTE = "no such route"                    # what a URL the server does not serve answers (a missing batch / pack / job says so in its own words); tests/test_openapi.py probes every documented route for it
_BATCH_DIR = re.compile(r"^G(\d+)(?:-[A-Za-z0-9_-]+)?$")       # a batch folder: the bare G110 of older batches or the labelled G111-dog_as_banana-... (runtime/names.folder)
_RID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_LOG_IDS = (re.compile(r"^/api/generations/(\d+)"), "generation_id", "G"), (re.compile(r"^/api/chat/sessions/(S\d+)"), "session_id", "")
_SRC_PATH = re.compile(r"^/src/(\d+)/")
_KEY_PATH = re.compile(r"^G(\d+)(?:-[A-Za-z0-9_-]+)?/")
MEMBER_GEN_POST = {"review", "more", "regen", "animate", "recut", "video_sheet", "quick_sheet", "drop", "allow", "judge", "captions", "appearance", "edge", "reslice", "recheck"}
MEMBER_GEN_GET = {"edge_preview", "sheet_preview", "events", "history", "captions"}
MEMBER_GET = {"/api/health", "/api/openapi.json", "/api/me", "/api/chat/agent", "/api/llm/models", "/api/search", "/api/generations", "/api/jobs"}
MEMBER_POST = {"/api/generations", "/api/assets/sign", "/api/live/cost", "/api/live/sheet", "/api/live/video", "/api/live/ref"}
RATE_DEFAULTS = {"r": 3000, "w": 240}                 # requests per minute per token holder (MIRSAL_RATE_READ / MIRSAL_RATE_WRITE; 0 = off)


def _out_batch(out: Path, path: str) -> int | None:
    """The generation number a `/out/...` URL lands in once resolved, or None when it lands outside every `G###/` folder (users.json, telegram.json, refs/)."""
    root = out.resolve()
    try:
        parts = pl.out_path(root, path[5:]).resolve().relative_to(root).parts
    except (ValueError, OSError):
        return None
    m = _BATCH_DIR.match(parts[0]) if len(parts) > 1 else None
    return int(m.group(1)) if m else None


class Console:
    def __init__(self, out: Path, inp: Path, pace: float = 0.0, cfg: EngineConfig | None = None):
        self.out, self.inp, self.pace, self.cfg = out, inp, pace, cfg or EngineConfig()
        self._writer = WriterLock(out, "mirsal serve").acquire()   # one writer of result.json per out/ (raises WriterBusy)
        self.lock = threading.Lock()   # held while a job runs
        self.started, self._stale_checked, self._stale = time.time(), 0.0, False
        self._health = None
        self.users = UserStore(out)
        self.lan = os.environ.get("MIRSAL_LAN", "").strip() in ("1", "true", "yes", "on")      # serve --lan: office colleagues reach this server (docs/api.md, Office accounts on the LAN)
        self.lan_names: set = set()
        if self.lan:
            from ..runtime import net
            self.lan_names = net.lan_names()
        self._ingest = None
        self._ingest_stop = threading.Event()
        self.lib = Library(out)
        self.projects = Projects(out, self.cfg)
        self._acct = (0.0, None)
        self._jobs = []
        threading.Thread(target=self._warm_models, daemon=True).start()
        from ..generation import jobqueue
        if jobqueue.mode(out) == "queue":                 # jobs a worker finished while the server was down are followed up now
            self._start_ingest()

    def release_writer(self) -> None:
        self._ingest_stop.set()
        self._writer.release()

    def visible(self, user: dict, gid: int) -> bool:
        """May this user see generation `gid`? An owner sees all; a member only what they own (and an unknown number is simply not theirs)."""
        if user.get("role") == "owner":
            return True
        try:
            return pl.read_result(self.out, int(gid)).get("owner", "local") == user["id"]
        except Exception:
            return False

    def actor(self) -> dict:
        """Who is acting on this thread (the request's user, or the job's/chat's user copied into the thread)."""
        return self.users.get(pl.current_owner()) or dict(LOCAL, id=pl.current_owner(), role="member", can_spend=False)

    def health(self) -> dict:
        """Can the final WEBM be encoded here? (live preview never needs ffmpeg)"""
        if self._health is None:
            try:
                from ..engine import ffmpeg as ff
                exe = ff.ffmpeg_exe()
                from ..media import matte
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

    # ---------- the durable queue (generation/jobqueue.py): in queue mode a worker process runs the job and this loop follows up on it ----------
    def _start_ingest(self) -> None:
        if self._ingest is not None and self._ingest.is_alive():
            return
        self._ingest_stop.clear()
        self._ingest = threading.Thread(target=self._ingest_loop, daemon=True)
        self._ingest.start()

    def _ingest_loop(self) -> None:
        from ..generation import jobqueue
        from ..store import db
        while not self._ingest_stop.is_set():
            try:
                with db.connect() as conn:
                    rows = jobqueue.take_ingest(conn)
                for r in rows:
                    self.follow_up(r["job_id"])
            except Exception:
                pass                                       # the database is away for a moment: try again next round
            self._ingest_stop.wait(2.0)

    def follow_up(self, jid: str) -> None:
        """What `fulfil(on_done=...)` does in thread mode, for a job a worker finished: a sheet starts the stills run, a video is attached and sliced. Exactly once per job."""
        from ..generation import jobqueue
        from ..store import db
        job = jobs.read(self.out, jid)
        after = {"sheet": self.start_from_job, "video": self.attach_video_from_job}.get(job["kind"])
        try:
            if after:
                after(job)
        except Exception as e:                             # the sheet is safe in out/jobs; say what did not follow
            jobs.update(self.out, jid, follow_up_error=str(e)[:300])
        finally:
            try:
                with db.connect() as conn:
                    jobqueue.mark_ingested(conn, jid)
            except Exception:
                pass
            self._acct = (0.0, None)

    def fulfil_async(self, jid: str, after=None) -> None:
        from ..generation import jobqueue
        if jobqueue.mode(self.out) == "queue":
            try:
                from ..store import db
                job = jobs.read(self.out, jid)
                with db.connect() as conn:
                    jobqueue.enqueue(conn, jid, job["kind"], (job.get("request") or {}).get("user") or "local")
                self._start_ingest()
                return
            except Exception:
                pass                                       # Postgres is unreachable right now: the thread way still works

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
        t = threading.Thread(target=run, daemon=True)
        self._jobs = [x for x in self._jobs if x.is_alive()] + [t]
        t.start()

    def job_followup(self, job):
        req = job.get("request") or {}
        effect = req.get("effect")
        if isinstance(effect, dict) and effect.get("id") and effect.get("group"):
            def finish(j):
                fx_flow.on_video_done(self.out, effect["id"], effect["group"], j, self.cfg)
                if effect.get("particle_target"):
                    fx_sets.set_from_effect(self.out, self.lib, effect["id"], mode="video", target=effect["particle_target"], user=req.get("user") or "local")
            return finish
        return self.start_from_job if job["kind"] == "sheet" else self.attach_video_from_job if job["kind"] == "video" and job.get("generation") else None

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
        parts = req.get("particles") or req.get("pieces")  # the sheet is the particle set of an effect (`pieces` is what older jobs called it) or *Generate more* of a saved set: a particle batch
        parts = parts if isinstance(parts, dict) and (parts.get("effect") or parts.get("set")) else None
        tok = pl.OWNER.set(req.get("user") or "local")     # the batch belongs to whoever asked for the sheet
        try:
            gid = pl.start(t["prompt"], self.out, self.inp, pick=pick, task=t, outline=int(outline) if outline is not None else None, erode=int(req["erode"]) if req.get("erode") is not None else None,
                           parent=int(str(parent).lstrip("G")) if parent else None, regen_of=req.get("regen_of") or None, kind="particles" if parts else None)
        finally:
            pl.OWNER.reset(tok)
        tasks.link_generation(self.out, t["id"], gid)
        jobs.attach_generation(self.out, job["id"], gid)
        set_id = str(parts["set"]) if parts and parts.get("set") else None
        if parts and parts.get("effect"):                  # thread mode and queue mode both run this
            try:
                fx_flow.link_particles(self.out, str(parts["effect"]), gid, job=job["id"], grid=t["plan"].get("grid"))
            except fx_flow.EffectError:                    # the effect was removed meanwhile: the batch is still a (particle) batch
                pass
        if set_id:
            try:
                fx_sets.link_more(self.out, set_id, job["id"], gid)
            except fx_sets.SetError:                       # the set went to the trash meanwhile: the batch is still a (particle) batch, the cells wait for a Restore
                set_id = None

        def cut():
            pl.run_stills(self.out, gid, self.cfg, self.pace)
            if set_id:                                     # the cells are cut: they join the set. A failure here is only a delay: every read of the set settles it again
                try:
                    fx_sets.settle(self.out, set_id)
                except Exception:
                    pass
        self._submit_when_free(cut)

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
                from ..generation import prompter
                return prompter.render_plan(slots, plan["template_id"], plan.get("template_version", 2))["video_prompt"]
        except (OSError, ValueError, KeyError):
            pass
        return entry.get("video_prompt") or res.get("video_prompt") or ""

    def attach_video_from_job(self, job: dict) -> None:
        req = job.get("request") or {}
        gid = int(str(job["generation"]).lstrip("G"))
        data = (self.out / job["result"]["file"]).read_bytes()
        gates.attach_video(self.out, gid, req["sheet"], data, f"{job['id']}.mp4", sent_prompt=req.get("prompt"), custom=bool(req.get("custom_prompt")))
        self._submit_when_free(lambda: gates.slice_video(self.out, gid, req["sheet"], self.cfg, self.pace))

    def plan_of(self, who: dict, ref) -> dict:
        """The saved plan (prompts.json) of a batch the caller may see, to start a new sheet from it with the same cells and tags."""
        try:
            gid = int(str(ref).lstrip("G"))
        except ValueError:
            raise pl.PipelineError("from_generation must be a batch number", 400)
        if not self.visible(who, gid):
            raise pl.PipelineError("No such batch", 404)
        try:
            return json.loads((pl.gen_dir(self.out, gid) / "prompts.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise pl.PipelineError("That batch has no saved plan to start from", 404)

    def live(self, what, body, base_plan=None, particles=None):
        """Live generation through the Higgsfield CLI. `cost` estimates, `sheet` reserves a task (the G1 approval) and starts the sheet job,
        `video` starts the Kling job for a built video sheet. The job runs in the background; the page polls /api/jobs/<id>.
        `particles` ({effect, elements}, in-process only, never from HTTP) marks a sheet as the particle set of an effect: the batch is a particle batch (exact equal cells, no sticker rule blocks a
        cell) and `start_from_job` links its cells to every group of the effect."""
        if what not in ("cost", "sheet", "video"):
            raise pl.PipelineError(NO_ROUTE, 404)
        who = self.actor()
        if what in ("sheet", "video"):                       # who may spend comes before anything about the provider is revealed
            if not who.get("can_spend") or who.get("disabled"):
                raise pl.PipelineError("This account cannot start paid generation (it spends the owner's credits). Ask the owner to allow it.", 403)
            if what == "video" and not self.visible(who, int(body["generation"])):
                raise pl.PipelineError("No such batch", 404)
        if not higgsfield.available():
            raise pl.PipelineError("The Higgsfield CLI is not installed (npm i -g @higgsfield/cli, then higgsfield auth login).", 503)
        kind = "video" if what == "video" or body.get("kind") == "video" else "image"
        try:
            custom = prompter.clean_custom(body.get("sheet_prompt" if what == "sheet" else "video_prompt"), "sheet prompt" if what == "sheet" else "video prompt")
        except ValueError as e:
            raise pl.PipelineError(str(e), 400)
        previewed = None
        if what == "sheet" and body.get("plan") is not None:      # the plan the person previewed on Generate prompt: untrusted, validated and rebuilt here, no model is asked
            if body.get("from_generation"):
                raise pl.PipelineError("Send either plan (the previewed one) or from_generation (a batch's own plan), not both", 400)
            style_id = body.get("style_id", "flat_vector")
            previewed = tasks.plan_from_preview(body["plan"], body.get("prompt", ""), body.get("grid", "3x3"), style_id if isinstance(style_id, str) else "", bool(body.get("loop")))
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
                base = base_plan or (self.plan_of(who, body["from_generation"]) if body.get("from_generation") else previewed)      # the plan the person approved on a card (in-process only, never from HTTP), or the Prompt tab: this batch's own plan, same cells and tags
                t = tasks.reserve(self.out, self.inp, body.get("prompt", ""), body.get("grid", "3x3"), body.get("style_id", "flat_vector"), bool(body.get("ai")), bool(body.get("loop")),
                                  base_plan=base, custom={"sheet_prompt": custom} if custom else None)
                try:
                    clause = prompter.clean_custom(body.get("ref_clause"), "reference clause") if refs else None     # what the attached picture is for (a tweak keeps the design, a new action keeps the shape)
                except ValueError as e:
                    raise pl.PipelineError(str(e), 400)
                prompt = t["plan"]["sheet_prompt"] + ("\n" + (clause or prompter.REFERENCE_CLAUSE) if refs else "")
                est = higgsfield.cost(model, params, prompt, **({"image_references": [str(self.out / r) for r in refs]} if refs else {}))
                reserved = self.reserve(who, est)
                job = jobs.create(self.out, "sheet", task=t["id"], request={
                    "model": model, "options": body.get("options") or {}, "prompt": prompt, "label": t["prompt"], "refs": refs,
                    "outline": int(body["outline"]) if body.get("outline") is not None else None, "erode": int(body["erode"]) if body.get("erode") is not None else None, "custom_prompt": bool(custom),
                    "parent": body.get("parent") or None, "regen_of": body.get("regen_of") or None, "user": who["id"], **({"reserved": reserved} if reserved else {}),
                    **({"particles": {k: str(particles[k]) for k in ("effect", "set") if particles.get(k)}} if particles else {})})
                if particles:                                      # before the job runs, so the page sees REQUESTED and the later link is never overwritten
                    if particles.get("effect"):
                        fx_flow.request_particles(self.out, str(particles["effect"]), job["id"], t["plan"]["grid"], particles.get("elements") or [], who["id"])
                    if particles.get("set"):
                        fx_sets.request_more(self.out, str(particles["set"]), job["id"], t["plan"]["grid"], particles.get("elements") or [], est, who["id"])
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
            reserved = self.reserve(who, est)
            job = jobs.create(self.out, "video", task=res.get("task"), generation=f"G{gid:03d}", request={
                "model": model, "options": body.get("options") or {}, "prompt": custom or self.video_prompt_for(gid, aid, loop), "custom_prompt": bool(custom),
                "start_image": str(start), "sheet": aid, "label": res.get("prompt", ""), "loop": loop, "user": who["id"], **({"reserved": reserved} if reserved else {})})
            self.fulfil_async(job["id"], after=self.attach_video_from_job)
            return {"job": job["id"], "estimate": est, "model": model, "params": params}
        except (higgsfield.HiggsError, jobs.JobError, model_catalog.CatalogError) as e:
            self._unreserve(who, locals().get("reserved"), locals().get("job"))
            raise pl.PipelineError(str(e), getattr(e, "code", 400))

    def reserve(self, who: dict, est) -> float | None:
        """Credits per person (docs/api.md, Office accounts on the LAN): an account with a balance pays from it. The price is checked BEFORE the job starts (an account
        without enough credits is refused in words, with the way to ask for more) and reserved; `jobs._settle` replaces it with the real cost when the job ends.
        The owner and token accounts without a balance spend as before (rule 13: the price was shown and accepted either way)."""
        u = self.users.get(who.get("id")) or {}
        if u.get("credits_left") is None or who.get("id") == "local":
            return None
        price = float(est or 0)
        if price > float(u["credits_left"]) + 1e-9:
            raise pl.PipelineError(f"Not enough credits: this costs {price:g}, you have {float(u['credits_left']):g} left. Ask for more in Settings (Request credits).", 402)
        self.users.charge(who["id"], price)
        return price

    def _unreserve(self, who: dict, reserved, job) -> None:
        """A reservation whose job was never created goes back at once (a created job settles itself in jobs._settle)."""
        if reserved and not job:
            self.users.charge(who["id"], -float(reserved))

    def idem(self, scope: str, key, fn):
        """Idempotency (Phase 5A): the same Idempotency-Key within 24 h returns the first answer and runs nothing again. The key is scoped
        (a generation create and a chat message never collide) and held under a lock while the first request runs. No key: just run."""
        key = str(key or "").strip()
        if not key:
            return fn()
        from ..runtime import cache as cachemod
        cc = cachemod.default()
        ck = cc.key("idem", scope, cachemod.digest(key))
        try:
            with cc.lock("idem:" + ck, 30_000):
                hit = cc.get(ck, "idem")
                if hit is None:
                    hit = idem_store.get(self.out, scope, key)           # the durable half: Postgres still knows a key the cache forgot (a restart without Redis)
                    if hit is not None:
                        cc.set(ck, hit, 24 * 3600)
                if hit is not None:
                    return dict(hit, idempotent=True)
                r = fn()
                cc.set(ck, r, 24 * 3600)
                idem_store.put(self.out, scope, key, r)
                return r
        except cachemod.Busy:
            raise pl.PipelineError("a request with this Idempotency-Key is still running", 409)

    # ---------- the agentic chat (Phase 4): sessions with memory, the graph over this same engine ----------
    def chat_parts(self, user: dict | None = None):
        """The chat of one user: an owner sees every chat, a member only their own (a stranger's chat is a 404)."""
        from ..agent import graph as ag
        from ..agent.brain import Brain
        from ..agent.memory import SessionStore
        from ..agent.tools import ConsoleTools
        user = user or LOCAL
        store = SessionStore(self.out, user=user["id"], see_all=user.get("role") == "owner")
        tools = ConsoleTools(self, user)
        return store, tools, ag.Agent(store, tools, Brain(out=self.out)), ag

    def chat_send(self, sid: str, body: dict, user: dict | None = None) -> dict:
        """Start one turn in the background and answer at once: the page polls the session and sees the steps as they are written."""
        user = user or LOCAL
        store, tools, agent, _ = self.chat_parts(user)
        text = str(body.get("text") or "")
        action = body.get("action") if isinstance(body.get("action"), dict) else None
        if not text.strip() and not action:
            raise pl.PipelineError("say something first")
        turn = agent.prepare(sid, text, [str(x) for x in (body.get("selected") or [])], action)      # 409 when the last message is still running
        ctx = contextvars.copy_context()                    # the turn runs in a thread: it must act as this user (batches it starts are theirs)
        ctx.run(pl.OWNER.set, user["id"])
        def run_turn():
            agent.execute(turn)
            self.drive_creator(user, sid)                 # a turn that started (or answered) a creator run hands it to the driver
        t = threading.Thread(target=ctx.run, args=(run_turn,), daemon=True)
        self._chat_threads = [x for x in getattr(self, "_chat_threads", []) if x.is_alive()] + [t]
        t.start()
        return {"id": sid, "message": turn.msg["id"]}

    def drive_creator(self, user: dict | None, sid: str, block: bool = False) -> None:
        """Keep advancing the session's creator run in a thread of its own until it stops, waits, ends or fails (one driver per session; a server restart resumes it on the next poll)."""
        user = user or LOCAL
        drivers = self.__dict__.setdefault("_drivers", set())
        if sid in drivers:
            return
        drivers.add(sid)
        _, _, agent, _ = self.chat_parts(user)
        ctx = contextvars.copy_context()
        ctx.run(pl.OWNER.set, user["id"])

        def loop():
            try:
                deadline = time.time() + 4 * 3600
                while time.time() < deadline:
                    st = agent.creator_tick(sid)
                    if st not in ("running", "busy"):
                        break
                    time.sleep(2.5 if not block else 0.05)
            except Exception as e:
                print(f"[mirsal] creator {sid}: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
            finally:
                drivers.discard(sid)
        if block:
            ctx.run(loop)
            return
        t = threading.Thread(target=ctx.run, args=(loop,), daemon=True)
        self._chat_threads = [x for x in getattr(self, "_chat_threads", []) if x.is_alive()] + [t]
        t.start()

    def kick_naming(self, user: dict | None, sess: dict) -> None:
        """Start `Agent.auto_name` for every batch of this chat that has finished stickers and was never looked at, when the person allowed AI vision. Cheap to call on every poll: it
        starts nothing unless there is such a batch, and never twice for one batch at a time."""
        if sess["settings"].get("allow_vlm") is not True:
            return
        user = user or LOCAL
        busy = self.__dict__.setdefault("_naming", set())
        named = set(sess.get("named") or [])
        for subj in sess.get("subjects") or []:
            for p in subj.get("passes") or []:
                gid = p.get("generation")
                if not gid or gid in named or (sess["id"], gid) in busy or not p.get("ready"):
                    continue
                busy.add((sess["id"], gid))
                _, _, agent, _ = self.chat_parts(user)
                ctx = contextvars.copy_context()
                ctx.run(pl.OWNER.set, user["id"])

                def run(agent=agent, sid=sess["id"], gid=gid):
                    try:
                        agent.auto_name(sid, gid)
                    except Exception as e:                           # a naming pass must never take the server down
                        print(f"[mirsal] naming pass {sid}/{gid}: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
                    finally:
                        busy.discard((sid, gid))
                t = threading.Thread(target=ctx.run, args=(run,), daemon=True)
                self._chat_threads = [x for x in getattr(self, "_chat_threads", []) if x.is_alive()] + [t]
                t.start()

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
        threading.Thread(target=run, daemon=True).start()


def make_handler(c: Console):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def end_headers(self):
            """Every answer, JSON or file or stream or error page, says which API version it came from and which request it answers (the id the console line carries too)."""
            self.send_header("X-API-Version", API_VERSION)
            self.send_header("X-Request-Id", getattr(self, "_rid", None) or uuid.uuid4().hex[:16])
            super().end_headers()

        def log_request(self, code="-", size="-"):
            """One JSON line per request on stderr when MIRSAL_ACCESS_LOG is on (off by default: the console stays quiet). The query string is never logged."""
            if os.environ.get("MIRSAL_ACCESS_LOG", "").lower() not in ("1", "true", "yes", "on"):
                return
            path = urlparse(self.path).path
            row = {"ts": round(time.time(), 3), "request_id": getattr(self, "_rid", None), "method": self.command, "path": path,
                   "status": int(code) if str(code).isdigit() else str(code), "ms": round((time.perf_counter() - getattr(self, "_t0", time.perf_counter())) * 1000, 1),
                   "user": (getattr(self, "user", None) or {}).get("id"), "via": (getattr(self, "user", None) or {}).get("via")}
            for rx, key, prefix in _LOG_IDS:
                m = rx.match(path)
                if m:
                    row[key] = prefix + (f"{int(m.group(1)):03d}" if prefix else m.group(1))
            print(json.dumps(row, ensure_ascii=False), file=sys.stderr, flush=True)

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
            from ..runtime import events
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            end, idle, last = time.time() + 600, 0, after
            try:
                self.wfile.write(b"retry: 3000\n\n")                 # the stream ends after 10 minutes: a browser's EventSource reconnects after 3 s and replays with Last-Event-ID
                self.wfile.flush()
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

        def _page(self, rows: list) -> tuple[list, dict]:
            """Opt-in pagination: `?limit=N&offset=M` slices a list route (limit 1-500) and the answer adds {total, limit, offset}. Without either the whole list comes back, exactly as before."""
            q = parse_qs(urlparse(self.path).query)
            if "limit" not in q and "offset" not in q:
                return rows, {}
            limit, offset = int(q.get("limit", ["500"])[0]), int(q.get("offset", ["0"])[0])
            if not 1 <= limit <= 500 or offset < 0:
                raise pl.PipelineError("limit must be 1-500 and offset 0 or more", 400)
            return rows[offset:offset + limit], {"total": len(rows), "limit": limit, "offset": offset}

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
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"} | {f"{n}:{port}" for n in c.lan_names}
            if (self.headers.get("Host") or "").lower() not in hosts:
                return "unexpected Host header"
            if self.command in ("GET", "HEAD", "OPTIONS"):
                return None
            origin = self.headers.get("Origin")
            if origin is not None and origin.lower() not in {f"{sch}://{h}" for h in hosts for sch in ("http", "https")}:
                return "cross-origin request refused"
            if (self.headers.get("Sec-Fetch-Site") or "same-origin") not in ("same-origin", "none"):
                return "cross-site request refused"
            return None

        def _who(self, path: str) -> dict | None:
            """The caller (runtime/users.py `authenticate`), or None for 401. The page's own files and a signed asset link carry no secret (the link IS the
            credential), so a browser can always open the Studio and an <img> can use a link."""
            if self.command == "GET" and (path == "/" or path.startswith("/ui/") or path.startswith("/assets/")):
                return dict(LOCAL, via="static")
            if self.command == "GET" and path.startswith("/api/assets/") and path.count("/") == 3:
                return dict(LOCAL, via="signed")
            gw = c.users.authenticate_gateway(self.headers.get("X-Mirsal-Gateway-Secret"), self.headers.get("X-Mirsal-Subject"), self.headers.get("X-Mirsal-Name"), self.client_address[0])
            if gw:                                                     # the hosted gateway vouches for this person (runtime/users.py); everything else is unchanged
                return gw
            from http.cookies import SimpleCookie
            jar = SimpleCookie()
            try:
                jar.load(self.headers.get("Cookie") or "")
            except Exception:
                pass
            sess = jar["mirsal_session"].value if "mirsal_session" in jar else None
            return c.users.authenticate(self.headers.get("Authorization"), self.headers.get("Sec-Fetch-Site") == "same-origin", session=sess,
                                        client_ip=self.client_address[0], lan=c.lan)

        def _authorize(self, user: dict, path: str):
            """None = allowed, else (status, body). Owners may do everything; a member reaches the chat, search, and what they own."""
            if user.get("role") == "owner":
                return None
            if user.get("status") == "pending":          # signed up, not approved yet: the page shows Waiting for approval and nothing else
                return 403, {"error": "waiting for approval"}
            post = self.command == "POST"
            deny, gone = (403, {"error": "this account cannot do that (owner only)"}), (404, {"error": "not found"})
            m = _GEN_PATH.match(path)
            if m:
                gid, act = int(m.group(1)), m.group(2)
                if (act not in MEMBER_GEN_POST) if post else (act is not None and act not in MEMBER_GEN_GET):
                    return deny
                return None if c.visible(user, gid) else gone
            if not post and path.startswith("/out/"):                    # authorise the file the URL RESOLVES to (`..` and symlinks included), never its prefix
                gid = _out_batch(c.out, path)
                return deny if gid is None else (None if c.visible(user, gid) else gone)
            m = None if post else _SRC_PATH.match(path)
            if m:
                return None if c.visible(user, int(m.group(1))) else gone
            if path.startswith("/api/chat/"):
                return None
            if (path in MEMBER_POST) if post else (path in MEMBER_GET):
                return None
            parts = path.strip("/").split("/")
            if post and len(parts) == 4 and parts[:2] == ["api", "jobs"] and parts[3] in ("check", "continue", "retry_estimate", "retry"):
                try:
                    return None if (jobs.read(c.out, parts[2]).get("request") or {}).get("user") == user["id"] else gone
                except jobs.JobError:
                    return gone
            if not post and parts[:2] == ["api", "packs"] and parts[-1] in ("particles", "particle-preview") and len(parts) in (4, 6):      # a member's particles answer is empty, not an error (the handler says so)
                return None
            if not post and len(parts) == 3 and parts[:2] == ["api", "jobs"]:          # one job: only the one this user asked for
                try:
                    return None if (jobs.read(c.out, parts[2]).get("request") or {}).get("user") == user["id"] else gone
                except Exception:
                    return gone
            return deny

        def _wait(self, user: dict, path: str) -> int:
            """Seconds to wait when this token holder is over its per-minute allowance, else 0. The open sandbox and the owner's own page are never
            limited (the Studio polls a lot); health checks and event streams are exempt too."""
            if user.get("via") != "token" or path.startswith("/api/health") or path.endswith("/events"):
                return 0
            kind = "w" if self.command == "POST" else "r"
            try:
                limit = int(os.environ.get("MIRSAL_RATE_WRITE" if kind == "w" else "MIRSAL_RATE_READ", RATE_DEFAULTS[kind]))
            except ValueError:
                limit = RATE_DEFAULTS[kind]
            if limit <= 0:
                return 0
            from ..runtime import cache as cachemod
            now = time.time()
            cc = cachemod.default()
            n = cc.window_count(cc.key("rate", cachemod.digest(str(c.out)), user["id"], kind, int(now // 60)), 65)
            return (int(60 - now % 60) + 1) if n > limit else 0

        def _guard(self, fn):
            self._started = False                        # has this request's answer begun? (a 500 can only be sent while it has not)
            self._t0 = time.perf_counter()
            rid = self.headers.get("X-Request-Id") or ""
            self._rid = rid if _RID.match(rid) else uuid.uuid4().hex[:16]
            if self.path.startswith("/api/v1/"):         # the same API under a versioned prefix: an integrator can pin /api/v1 before anything changes
                self.path = "/api/" + self.path[len("/api/v1/"):]
            why = self._foreign()
            if why:
                return self._json(403, {"error": why})
            path = unquote(urlparse(self.path).path)
            user = self._who(path)
            if user is None:
                return self._json(401, {"error": "an API token is required (Authorization: Bearer <token>)"})
            deny = self._authorize(user, path)
            if deny:
                return self._json(*deny)
            wait = self._wait(user, path)
            if wait:
                b = json.dumps({"error": f"too many requests: wait {wait} s"}).encode()
                self.send_response(429)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(b)))
                self.send_header("Retry-After", str(wait))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(b)
                return
            self.user = user
            tok = pl.OWNER.set(user["id"])           # batches this request creates are stamped with this user
            try:
                fn()
            except (pl.PipelineError, LibraryError, watch.WatchError, telegram.TelegramError, UserError, fx_flow.EffectError) as e:
                if isinstance(e, telegram.TelegramError) and self.command == "POST":
                    try:                                 # a refused Telegram send is a ticket (flow/tickets.py)
                        from ..flow import tickets
                        tickets.open_auto(c.out, source="telegram", issue="other", what=f"Telegram refused: {e}", where=urlparse(self.path).path,
                                          context={"request_id": self._rid}, user=user.get("id"))
                    except Exception:
                        pass
                self._json(e.code, {"error": str(e)})
            except (ValueError, KeyError, TypeError) as e:
                self._json(400, {"error": f"bad request: {e}"})
            except vision_consent.ConsentRequired as e:
                self._json(409, {"error": str(e), "consent_required": True})
            except (BrokenPipeError, ConnectionError):
                pass                                     # the client went away; nothing to answer
            except Exception as e:                       # anything else is OUR fault: a JSON 500, the detail stays on this console (never in the answer)
                self._internal(e)
            finally:
                pl.OWNER.reset(tok)

        def _internal(self, e: Exception):
            from ..obs.scrub import scrub_paths
            print(f"[mirsal] 500 {self.command} {urlparse(self.path).path} [{self._rid}]: {type(e).__name__}: {scrub_paths(str(e))[:300]}", file=sys.stderr, flush=True)
            try:                                         # every 500 is a ticket (flow/tickets.py), folded with the same failure seen before
                from ..flow import tickets
                tickets.open_auto(c.out, source="crash", issue="crash", what=f"{type(e).__name__}: {e}", where=f"{self.command} {urlparse(self.path).path}",
                                  context={"request_id": self._rid}, user=(getattr(self, "user", None) or {}).get("id"))
            except Exception:
                pass
            if not getattr(self, "_started", False):
                self._json(500, {"error": "internal error", "request_id": self._rid})

        def send_response(self, code, message=None):
            self._started = True
            super().send_response(code, message)

        def send_error(self, code, message=None, explain=None):
            """The base class answers with an HTML page; every answer of this server is JSON (docs/api.md)."""
            msg = message or (self.responses.get(code) or ("error",))[0]
            b = json.dumps({"error": msg}).encode()
            self.send_response(code, message)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Connection", "close")
            self.end_headers()
            if self.command != "HEAD" and code >= 200 and code not in (204, 304):
                self.wfile.write(b)

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
                    f = store.path(store.verify(gp[2]))             # signed by someone who could see the file; the signature is the credential
                except AssetError as e:
                    return self._json(e.code, {"error": str(e)})
                if not f.is_file():
                    return self._json(404, {"error": "no such asset"})
                return self._file(f)
            if path == "/api/effects" or path.startswith("/api/effects/"):
                return self._effects("GET", path, {})
            gp = path.strip("/").split("/")
            if gp[:2] == ["api", "generations"] and len(gp) == 4 and gp[3] == "particles":
                return self._json(200, fx_sets.for_generation(c.out, c.lib, gp[2]))
            if path == "/api/particles" or path.startswith("/api/particles/"):
                return self._particles("GET", path, {})
            if path == "/api/me":            # who the server thinks you are (and what you may do): for clients that hold a token
                u = self.user
                return self._json(200, {"id": u["id"], "name": u.get("name"), "role": u["role"], "can_spend": bool(u.get("can_spend")), "via": u.get("via")})
            if path == "/api/users":
                return self._json(200, {"users": c.users.list()})
            if path == "/api/telegram":      # connected or not and which bot: never the token
                return self._json(200, telegram.status(c.out))
            pp = path.strip("/").split("/")
            if len(pp) == 6 and pp[:2] == ["api", "packs"] and pp[3] == "stickers" and pp[5] == "particle-preview":
                if self.user.get("role") != "owner":
                    return self._json(200, {"set": None, "url": None})
                try:
                    return self._json(200, fx_sets.preview_for_sticker(c.out, c.lib, pp[2], pp[4]))
                except fx_sets.SetError as e:
                    raise pl.PipelineError(str(e), e.code)
            if pp[:2] == ["api", "packs"] and pp[-1] == "particles" and len(pp) in (4, 6) and (len(pp) == 4 or pp[3] == "stickers"):
                # the particles made for a sticker (GET /api/packs/{id}/stickers/{sid}/particles) or the counts for a whole pack (GET /api/packs/{id}/particles): a pure read; effects are owner only,
                # a member's answer is simply empty (docs/effects.md)
                if self.user.get("role") != "owner":
                    return self._json(200, {"sticker": pp[4], "created": [], "saved": [], "effects": [], "can_make": False} if len(pp) == 6 else {})
                if len(pp) == 6:
                    return self._json(200, fx_sets.for_sticker(c.out, c.lib, pp[2], pp[4]))
                # the pack's particle studio (docs/particles.md 5): its sets and its bursts, plus the per-sticker counts the old answer carried
                try:
                    return self._json(200, {**fx_sets.for_pack(c.out, c.lib, pp[2]), "counts": fx_sets.counts_for_pack(c.out, c.lib, pp[2])})
                except fx_sets.SetError as e:
                    raise pl.PipelineError(str(e), e.code)
            if path.startswith("/api/packs/") and path.endswith("/telegram"):          # dry run: what would be created, every problem
                st = telegram.status(c.out)
                name = parse_qs(urlparse(self.path).query).get("name", [None])[0]
                return self._json(200, dict(telegram.plan(c.lib, path.split("/")[3], st["bot"], name, c.cfg), status=st))
            if path.startswith("/api/packs/") and path.endswith("/export.zip"):        # the pack's files as a plain download (no Telegram wording)
                try:
                    data, stem = c.lib.export_zip(path.split("/")[3])
                except LibraryError as e:
                    raise pl.PipelineError(str(e), e.code)
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Content-Disposition", f'attachment; filename="{stem}.zip"')
                self.end_headers()
                self.wfile.write(data)
                return
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
                return self._json(200, {"agent": _brain.target(), "agent_status": _brain.status(), "vision": __import__("mirsal.vision.judge", fromlist=["status"]).status(),
                                        "live": higgsfield.available(), "preference": llm.preference(), "availability": llm.availability(),
                                        "styles": styles.PRESETS, "default_style": styles.DEFAULT})
            if path == "/api/llm/models":     # the local server's chat models, the one in use, and whether it can answer (the engine row's dropdown); members read it, only an owner picks (POST /api/ai/backend)
                return self._json(200, llm.models_report())
            if path == "/api/chat/sessions":
                rows, meta = self._page(c.chat_parts(self.user)[0].list())
                return self._json(200, {"sessions": rows, **meta})
            if path.startswith("/api/chat/sessions/") and len(path.strip("/").split("/")) == 4:
                from ..agent.memory import SessionError as _SE
                store, tools, _agent, ag = c.chat_parts(self.user)
                try:
                    sess = store.load(path.rsplit("/", 1)[1])
                    store.refresh(sess)
                    if (sess.get("creator_run") or {}).get("status") == "running":
                        c.drive_creator(self.user, sess["id"])           # resumes a run after a restart; a no-op while a driver is alive
                    c.kick_naming(self.user, sess)                     # AI vision allowed + finished stickers + never looked at: the assistant looks (its own message, its own thread)
                    return self._json(200, ag.hydrate(store, tools, sess))
                except _SE as e:
                    raise pl.PipelineError(str(e), e.code)
            if path == "/api/openapi.json":      # the HTTP contract (console/openapi.py; tests/test_openapi.py guards it against drift)
                from . import openapi as _oa
                return self._json(200, _oa.build(f"http://{self.headers.get('Host') or '127.0.0.1'}"))
            if path in ("/api/health", "/api/health/models", "/api/health/storage"):     # what is this app connected to, and is it healthy
                from ..runtime import health as _h
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
                see = (lambda g: c.visible(self.user, int(str(g).lstrip("G")))) if self.user.get("role") != "owner" else (lambda g: True)
                try:  # Phase 3A: Postgres search when serving the real out/ with the database up, else files
                    from ..store import db as _db, repo as _repo, sync as _sync
                    import os as _os
                    if _sync.is_default_out(c.out) and _os.environ.get("MIRSAL_DB_WRITE", "") not in ("0", "no", "off", "false") and _db.available():
                        with _db.connect() as _c:
                            rows = [r for r in _repo.search(_c, q) if see(r["generation_id"])]
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
                return self._json(200, {"results": [r for r in gates.search(c.out, q) if see(r["generation"])], "via": "files"})
            if path == "/api/inputs":
                return self._json(200, {"inputs": pl.list_inputs(c.inp)})
            if path.startswith("/api/generations/") and path.endswith("/files"):         # where this batch's files are
                gid = int(path.split("/")[3])
                return self._json(200, {"stickers": str(pl.gen_dir(c.out, gid) / "slices"), "batch": str(pl.gen_dir(c.out, gid))})
            if path.startswith("/api/generations/") and path.endswith("/edge_preview"):         # ONE sticker with a stroke/trim, rendered on the fly (a preview, never stored)
                q = parse_qs(urlparse(self.path).query)
                png = pl.edge_preview(c.out, int(path.split("/")[3]), int(q.get("index", ["1"])[0]), int(q.get("outline", ["0"])[0]), int(q.get("erode", ["0"])[0]), int(q.get("px", ["420"])[0]))
                return self._send(200, png, "image/png")
            if path.startswith("/api/generations/") and path.endswith("/sheet_preview"):      # the video sheet at a given fill, small and not stored
                q = parse_qs(urlparse(self.path).query)
                fill = min(0.92, max(0.5, float(q.get("fill", [c.cfg.slot_fill])[0])))
                png = gates.preview_sheet(c.out, int(path.split("/")[3]), c.cfg, fill, int(q.get("px", ["420"])[0]))
                return self._send(200, png, "image/png")
            if path.startswith("/api/generations/") and path.endswith("/history"):            # every sticker's decisions of one batch, grouped by stage (the Studio's folded history)
                gid = int(path.split("/")[3])
                idx = parse_qs(urlparse(self.path).query).get("index")
                return self._json(200, sticker_history.batch_history(pl.read_result(c.out, gid), f"G{gid:03d}", int(idx[0]) if idx else None))
            if path.startswith("/api/generations/") and path.endswith("/captions"):          # the stored AI caption of every cell of the sheet: read-only, no model, no consent
                return self._json(200, transcribe.sheet_with_captions(c.out, int(path.split("/")[3])))
            if path == "/api/metrics":              # quality and timing numbers over every batch (owner only: not in MEMBER_GET)
                return self._json(200, metrics.collect(c.out))
            if path == "/api/history":              # the Studio's persistent history of batches, a page at a time
                q = parse_qs(urlparse(self.path).query)
                return self._json(200, pl.history(c.out, int(q.get("offset", ["0"])[0]), int(q.get("limit", ["5"])[0])))
            if path == "/api/higgsfield":          # is the CLI there, the balance, today's spend (never a credential)
                return self._json(200, c.hf_account())
            if path == "/api/models":              # the selector: curated models + every other Higgsfield model, and the style presets
                return self._json(200, dict(model_catalog.catalog(), styles=styles.PRESETS, default_style=styles.DEFAULT, slot_fill=c.cfg.slot_fill))
            if path == "/api/usage":
                return self._json(200, usage.summary(c.out, int(parse_qs(urlparse(self.path).query).get("limit", ["100"])[0])))
            if path.startswith("/assets/welcome/"):            # the welcome modal's own video and slides: real files, with Range (a browser seeks and loops a video through it)
                name = path.rsplit("/", 1)[-1]
                f = placeholders.ASSETS / "welcome" / name
                if not placeholders.WELCOME.match(name) or not f.is_file():
                    raise pl.PipelineError("not found", 404)
                return self._file(f)
            if path.startswith("/assets/"):
                parts = path.strip("/").split("/")
                a = placeholders.find(parts[1], parts[2]) if len(parts) == 3 else None
                if not a:
                    raise pl.PipelineError("not found", 404)
                return self._send(200, a[0], a[1])
            if path == "/api/jobs":      # S2: jobs for the operator (Generate page polls while waiting)
                st = parse_qs(urlparse(self.path).query).get("status", [None])[0]
                rows = jobs.list(c.out, st)
                if self.user.get("role") != "owner":
                    page, meta = self._page([j for j in rows if (j.get("request") or {}).get("user") == self.user["id"]])
                    return self._json(200, {"jobs": page, **meta})
                page, meta = self._page(rows)
                return self._json(200, {"jobs": page, "typical": usage.typical(c.out), **meta})
            if path.startswith("/api/jobs/") and len(path.strip("/").split("/")) == 3:
                try:
                    return self._json(200, jobs.read(c.out, path.strip("/").split("/")[2]))
                except jobs.JobError as e:
                    raise pl.PipelineError(str(e), e.code)
            if path == "/api/generations":
                if self.user.get("role") != "owner":
                    page, meta = self._page([g for g in pl.summary(c.out) if g.get("owner") == self.user["id"]])
                    return self._json(200, {"busy": c.lock.locked(), "generations": page, **meta})
                page, meta = self._page(pl.summary(c.out))
                return self._json(200, {"busy": c.lock.locked(), "health": c.health(), "paths": {"input": str(c.inp), "out": str(c.out)}, "stale": c.stale(), "generations": page, **meta})
            if path == "/api/generations/removed":      # the trash of batches (owner only like the rest): Restore is reachable long after the remove
                return self._json(200, {"batches": batches.list_removed(c.out)})
            if path == "/api/trash":                    # the whole trash (removed batches + deleted packs) with exactly what a purge would remove (owner only; flow/purge.py)
                return self._json(200, purge.listing(c.out, c.lib))
            if path.startswith("/api/trash/purges/"):   # the progress of a purge that did not finish within the request (a long purge runs in its own thread)
                return self._json(200, purge.status(c.out, path.rsplit("/", 1)[1]))
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
                f = pl.out_path(root, path[5:]).resolve()                # /out/G111/... reaches the labelled folder G111-dog_as_banana-.../
                if root not in f.parents:
                    raise pl.PipelineError("forbidden path", 400)
                if not f.is_file():
                    raise pl.PipelineError("not found", 404)
                ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
                return self._send(200, f.read_bytes(), ctype)
            raise pl.PipelineError(NO_ROUTE, 404)

        def _particles(self, method: str, path: str, body: dict):
            """Particle sets `P###` (docs/particles.md section 6): the durable sticker-owned particle asset with derived pack views. The working
            session stays `/api/effects`; `POST /api/particles {from_effect}` is the bridge that saves one. Free: nothing here spends. A delete moves the
            folder to the trash and a set in use says which packs before it goes (rule 9's spirit: nothing is destroyed on a click)."""
            ps = fx_sets
            parts = path.strip("/").split("/")                     # api, particles[, id[, action]]
            try:
                if len(parts) == 2:
                    if method == "GET":
                        ps.settle_open(c.out)                      # the cells of a sheet that was cut since the last read join their set first
                        return self._json(200, {"sets": ps.list_sets(c.out, c.lib)})
                    if body.get("from_stickers"):
                        return self._json(201, ps.set_from_stickers(c.out, c.lib, body["from_stickers"], body.get("parent_pack_id"), owners=body.get("owners"), name=body.get("name"), target=body.get("target"), user=self.user["id"]))
                    if body.get("from_generation"):                # a sheet of particles that is already a batch: its cells as tight sprites, no effect behind it
                        return self._json(201, ps.set_from_generation(c.out, c.lib, str(body["from_generation"]), name=body.get("name"), owners=body.get("owners"), packs=body.get("packs"),
                                                                         picked=body.get("picked"), user=self.user["id"]))
                    if body.get("from_video"):
                        return self._json(201, ps.set_from_effect(c.out, c.lib, str(body["from_video"]), mode="video", target=body.get("target"), owners=body.get("owners"), name=body.get("name"), picked=body.get("picked"), user=self.user["id"]))
                    if body.get("from_slices"):
                        return self._json(201, ps.set_from_slices(c.out, c.lib, body["from_slices"], owners=body.get("owners"), name=body.get("name"), target=body.get("target"), user=self.user["id"]))
                    if body.get("from_effect"):
                        return self._json(201, ps.set_from_effect(c.out, c.lib, str(body["from_effect"]), target=body.get("target"), name=body.get("name"), owners=body.get("owners"), packs=body.get("packs"),
                                                                       picked=body.get("picked"), user=self.user["id"]))
                    return self._json(201, ps.create(c.out, c.lib, name=body.get("name"), elements=body.get("elements"), owners=body.get("owners"), packs=body.get("packs"),
                                                      kind=str(body.get("kind") or "drawn"), user=self.user["id"]))
                pid = parts[2]
                if len(parts) == 3:
                    if method == "GET" and pid == "deleted":       # the trash (owner only like the rest): Restore is reachable long after the delete
                        return self._json(200, {"sets": ps.list_deleted(c.out, c.lib)})
                    if method == "GET":
                        ps.settle(c.out, pid)                      # (a 404 for a missing set comes from here)
                        return self._json(200, ps.view(c.out, c.lib, pid))
                    return self._json(200, ps.update(c.out, c.lib, pid, name=body.get("name"), elements=body.get("elements"), packs=body.get("packs"),
                                                     picked=body.get("picked"), motion=body.get("motion"), save=body.get("save") is True, user=self.user["id"]))
                act = parts[3]
                if method != "POST":
                    raise pl.PipelineError(NO_ROUTE, 404)
                if act in ("link", "unlink"):
                    return self._json(200, ps.link(c.out, c.lib, pid, body.get("sticker_ids"), self.user["id"], unlink=act == "unlink"))
                if act == "assign":
                    return self._json(200, ps.assign(c.out, c.lib, pid, body.get("packs"), self.user["id"]))
                if act == "unassign":
                    return self._json(200, ps.unassign(c.out, c.lib, pid, body.get("packs"), self.user["id"]))
                if act == "duplicate":
                    return self._json(201, ps.duplicate(c.out, c.lib, pid, name=body.get("name"), user=self.user["id"]))
                if act == "save-as-new":                           # the same sprites with the new motion as a new saved row under the same stickers
                    return self._json(201, ps.save_as_new(c.out, c.lib, pid, motion=body.get("motion"), name=body.get("name"), user=self.user["id"]))
                if act == "delete":
                    return self._json(200, ps.delete(c.out, c.lib, pid, confirm_packs=body.get("confirm") is True, user=self.user["id"]))
                if act == "restore":
                    return self._json(200, ps.restore(c.out, c.lib, pid, self.user["id"]))
                if act == "preview":                               # the burst of the set's picked cells for a pack, as a small looping WebP (free)
                    return self._json(200, ps.preview(c.out, c.lib, pid, pack_id=body.get("pack_id"), preset=body.get("preset"), params=body.get("params") or {}, size=body.get("size", 256)))
                if act == "render":                                # the final 512 px WebM for a pack, judged and stored under renders/ (only Telegram's own limits make it FAILED)
                    return self._json(200, ps.render(c.out, c.lib, pid, c.cfg, pack_id=body.get("pack_id"), preset=body.get("preset"), params=body.get("params") or {}, user=self.user["id"]))
                if act == "add":                                   # rendered bursts into the pack as animated stickers tagged with the pack's emoji
                    return self._json(200, ps.add(c.out, c.lib, pid, body.get("renders"), body.get("pack_id"), body.get("sticker_id"), self.user["id"]))
                if act == "more":                                  # Generate more: the price first (409 until go), then an ordinary sheet job whose cut cells are APPENDED to the set
                    saved = ps.migrate(c.out, c.lib, pid)
                    mode = body.get("mode") or saved.get("source", {}).get("kind") or "drawn"
                    if mode not in ("video", "drawn", "image", "stickers"):
                        raise ps.SetError("mode must be video, drawn, image or stickers")
                    if mode == "video":
                        eid = body.get("effect") or saved.get("source", {}).get("effect")
                        if eid and fx_flow.read(c.out, eid).get("mode") != "video":
                            eid = None
                        if not eid:
                            owners = saved.get("owner") or []
                            if not owners:
                                raise ps.SetError("Attach this set to a sticker before generating video", 409)
                            pack_id = owners[0]["pack_id"]
                            e = fx_flow.create(c.out, c.lib, pack_id=pack_id,
                                               sticker_ids=[o["sticker_id"] for o in owners if o["pack_id"] == pack_id],
                                               mode="video", grid=body.get("grid") or "2x2", user=self.user["id"], note=str(body.get("prompt") or ""))
                            eid = e["id"]
                            fx_flow.analyse(c.out, eid, allowed=False)
                        e = fx_flow.read(c.out, eid)
                        group = str(body.get("group") or (e.get("groups") or [{}])[0].get("id") or "")
                        return self._effects("POST", f"/api/effects/{eid}/" + ("estimate" if body.get("estimate") else "video"), {**body, "group": group, "particle_target": pid})

                    plan = ps.more_plan(c.out, c.lib, pid, body.get("grid"), body.get("elements"))
                    if self._price_sheet(plan, body, False):
                        return
                    base = ps.more_base_plan(c.out, c.lib, plan["id"], plan["grid"], plan["picks"])
                    j = c.live("sheet", {"prompt": base["task"], "grid": f"{plan['grid'][0]}x{plan['grid'][1]}", "outline": 0, "model": body.get("model"), "options": body.get("options")},
                               base_plan=base, particles={"set": plan["id"], "elements": plan["picks"]})
                    return self._json(202, {"job": j["job"], "task": j["task"], "estimate": j["estimate"], "id": plan["id"], "grid": plan["grid"]})
                raise pl.PipelineError(NO_ROUTE, 404)
            except (ps.SetError, fx_flow.EffectError) as e:
                raise pl.PipelineError(str(e), e.code)

        def _price_sheet(self, plan: dict, body: dict, quote_only: bool) -> bool:
            """The price of a sheet of particles comes before anything is spent (rule 13), for an effect's sheet and for *Generate more* of a set alike: it adds `credits`, `model` and `params` to
            the plan. True when the answer has been sent (a quote, or the 409 that shows the price and waits for `go: true`); False when the caller may start the job."""
            if not higgsfield.available():
                raise pl.PipelineError("The Higgsfield CLI is not installed (npm i -g @higgsfield/cli, then higgsfield auth login).", 503)
            model, params = model_catalog.resolve("image", body.get("model"), body.get("options"))
            try:
                credits = higgsfield.cost(model, params, plan["prompt"])
            except higgsfield.HiggsError as ex:
                credits = None
                plan["cost_error"] = str(ex)
            plan.update(credits=credits, model=model, params=params)
            if quote_only or body.get("estimate") is True:
                self._json(200, plan)
                return True
            who = c.actor()
            if not who.get("can_spend") or who.get("disabled"):
                raise pl.PipelineError("This account cannot start paid generation (it spends the owner's credits). Ask the owner to allow it.", 403)
            if body.get("go") is not True:
                self._json(409, {"error": f"This costs {credits} credits. Send go: true to start it.", "estimate": plan})
                return True
            if credits is None:
                self._json(409, {"error": "The price is unavailable. Retry the price before starting.", "estimate": plan})
                return True
            return False

        def _effects(self, method: str, path: str, body: dict):
            """Particle effects (docs/effects.md section 7): a pack's stickers get a Telegram-style burst. Owner only for now (members are denied by the route gate). Paid work needs the price
            shown (`estimate`) and `go: true` (`video`); everything else is free."""
            parts = path.strip("/").split("/")                     # api, effects[, id[, action]]
            if len(parts) == 2:
                if method == "GET":
                    return self._json(200, {"effects": fx_flow.list_effects(c.out)})
                grid = body.get("grid") or "2x2"
                e = fx_flow.create(c.out, c.lib, pack_id=str(body.get("pack_id") or ""), sticker_ids=body.get("sticker_ids", "all"), mode=str(body.get("mode") or "video"),
                                   grid=grid, user=self.user["id"], note=str(body.get("note") or ""))
                allowed = body.get("allow_vlm") is True
                eid, who = e["id"], self.user["id"]

                def run():
                    tok = pl.OWNER.set(who)
                    try:
                        fx_flow.analyse(c.out, eid, allowed=allowed)
                    except Exception as ex:                          # the page reads the status; a failed analysis is a visible state, never a silent one
                        try:
                            rec = fx_flow.read(c.out, eid)
                            rec.update(status="ERROR", error=str(ex)[:300])
                            fx_flow._write(c.out, rec)
                        except Exception:
                            pass
                    finally:
                        pl.OWNER.reset(tok)
                threading.Thread(target=run, daemon=True).start()
                return self._json(202, {"id": eid, "status": "NEW"})
            eid = parts[2]
            if len(parts) == 3:
                if method != "GET":
                    raise pl.PipelineError(NO_ROUTE, 404)
                return self._json(200, fx_flow.view(c.out, eid))
            act = parts[3]
            if method != "POST":
                raise pl.PipelineError(NO_ROUTE, 404)
            if act == "analyse":
                allowed = body.get("allow_vlm") is True
                threading.Thread(target=lambda: fx_flow.analyse(c.out, eid, allowed=allowed), daemon=True).start()
                return self._json(202, {"id": eid})
            if act == "plan":
                gid = str(body.get("group") or "")
                if "sprites" in body:
                    fx_flow.set_sprites(c.out, eid, gid, body["sprites"])
                if any(k in body for k in ("elements", "subject", "style")):
                    fx_flow.set_pieces(c.out, eid, gid, elements=body.get("elements"), subject=body.get("subject"), style=body.get("style"), by=self.user["id"])
                return self._json(200, fx_flow.view(c.out, eid))
            if act in ("estimate", "video"):
                gid = str(body.get("group") or "")
                if any(k in body for k in ("elements", "subject")):
                    fx_flow.set_pieces(c.out, eid, gid, elements=body.get("elements"), subject=body.get("subject"), by=self.user["id"])
                grid = body.get("grid")
                plan = fx_flow.video_plan(c.out, eid, gid, tuple(int(x) for x in str(grid).lower().split("x")) if grid else None)
                if not higgsfield.available():
                    raise pl.PipelineError("The Higgsfield CLI is not installed (npm i -g @higgsfield/cli, then higgsfield auth login).", 503)
                model, params = model_catalog.resolve("video", body.get("model"), body.get("options"))
                try:
                    credits = higgsfield.cost(model, params, plan["prompt"])
                except higgsfield.HiggsError as ex:
                    credits = None
                    plan["cost_error"] = str(ex)
                plan.update(credits=credits, model=model, params=params, effect=eid)
                if act == "estimate":
                    return self._json(200, plan)
                who = c.actor()
                if not who.get("can_spend") or who.get("disabled"):
                    raise pl.PipelineError("This account cannot start paid generation (it spends the owner's credits). Ask the owner to allow it.", 403)
                if body.get("go") is not True:
                    return self._json(409, {"error": f"This costs {credits} credits. Send go: true to start it.", "estimate": plan})
                if credits is None:
                    return self._json(409, {"error": "The price is unavailable. Retry the price before starting.", "estimate": plan})
                job = fx_flow.new_video_job(c.out, eid, gid, grid=tuple(plan["grid"]), user=who["id"], model=body.get("model"), options=body.get("options"), particle_target=body.get("particle_target"))
                def finish_video(j):
                    fx_flow.on_video_done(c.out, eid, gid, j, c.cfg)
                    if body.get("particle_target"):
                        fx_sets.set_from_effect(c.out, c.lib, eid, mode="video", target=body["particle_target"], user=who["id"])
                c.fulfil_async(job["id"], after=finish_video)
                return self._json(202, {"job": job["id"], "estimate": credits, "id": eid, "group": gid})
            if act == "suggest":                                   # candidate particles for the ONE set of the whole effect: the model looks at one picture (with consent), else the table answers
                return self._json(200, fx_flow.suggest(c.out, c.lib, eid, body.get("grid"), allowed=body.get("allow_vlm") is True))
            if act in ("particles_estimate", "particles", "pieces_estimate", "pieces"):    # the ONE sheet of particles for the whole effect: an ordinary sheet job (Nano Banana 2), outline 0, a particle batch linked by start_from_job
                elements = body.get("elements")
                if elements is None and body.get("group"):          # the old routes (`pieces`) named a group: its pieces are the picks (the first ones when it has more than the sheet has cells)
                    elements = fx_flow.group_elements(c.out, eid, str(body["group"]))
                plan = fx_flow.particles_plan(c.out, eid, body.get("grid"), elements, truncate=body.get("elements") is None)
                if self._price_sheet(plan, body, act.endswith("_estimate")):
                    return
                picks = plan["picks"]
                base = fx_flow.particles_base_plan(c.out, eid, plan["grid"], picks)
                j = c.live("sheet", {"prompt": base["task"], "grid": f"{plan['grid'][0]}x{plan['grid'][1]}", "outline": 0, "model": body.get("model"), "options": body.get("options")},
                           base_plan=base, particles={"effect": eid, "elements": picks})
                return self._json(202, {"job": j["job"], "task": j["task"], "estimate": j["estimate"], "id": eid, "grid": plan["grid"]})
            if act == "particles_recut":                           # a sheet drawn before batches knew they were particles (G100) is cut again as one: exact equal cells, warnings only, free
                gn = fx_flow.recut_check(c.out, eid)
                c.submit(lambda: pl.recut_as_particles(c.out, gn, c.cfg, c.pace, by=self.user.get("id") or "human"))
                return self._json(202, {"id": eid, "generation": f"G{gn:03d}"})
            if act == "particles_pick":                            # which cells of the drawn sheet are the particles (the person's decision; a cell with only warnings can be picked)
                return self._json(200, fx_flow.pick_particles(c.out, eid, body.get("indexes"), "you"))
            if act == "preview":
                return self._json(200, fx_flow.sim_preview(c.out, c.lib, eid, str(body.get("sticker_id") or ""), body.get("params") or {}, int(body.get("size") or 256)))
            if act == "render":
                return self._json(200, fx_flow.sim_render(c.out, c.lib, eid, str(body.get("sticker_id") or ""), c.cfg, body.get("params") or {}))
            if act == "add":
                return self._json(200, fx_flow.add_to_pack(c.out, c.lib, eid, body.get("results"), body.get("pack_id"), self.user["id"], body.get("sticker_ids")))
            raise pl.PipelineError(NO_ROUTE, 404)

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
            raise pl.PipelineError(NO_ROUTE, 404)

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
            elif len(parts) == 4 and parts[3] == "delete":      # SOFT: to the trash, restorable (GET /api/trash lists it; POST /api/trash/purge deletes for good)
                self._json(200, lib.delete_pack(parts[2], by=self.user.get("id") or "human"))
            elif len(parts) == 4 and parts[3] == "restore":     # back from the trash under the same id
                self._json(200, lib.restore_pack(parts[2]))
            elif len(parts) == 4 and parts[3] == "telegram":     # create the pack on Telegram (or add what is new to it)
                body = self._body()
                self._json(200, telegram.send(c.out, lib, parts[2], (body.get("name") or None), c.cfg, str(body.get("mode") or "once")))
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
            if path == "/api/effects" or path.startswith("/api/effects/"):
                return self._effects("POST", path, self._body())
            if path == "/api/particles" or path.startswith("/api/particles/"):
                return self._particles("POST", path, self._body())
            if path.startswith("/api/cutout") or path.startswith("/api/packs"):
                if self._post_library(path, parse_qs(u.query)):
                    return
                raise pl.PipelineError(NO_ROUTE, 404)
            if path == "/api/live/ref":          # a reference image for the next sheet (raw body, ?name=file.png)
                return self._json(200, c.save_ref(self._raw(15 * 1024 * 1024), parse_qs(u.query).get("name", ["ref.png"])[0]))
            parts = path.strip("/").split("/")
            if len(parts) == 6 and parts[:2] == ["api", "generations"] and parts[3:4] == ["video_sheet"] and parts[5] == "video":
                return self._post_video(int(parts[2]), parts[4], parse_qs(u.query))
            body = self._body()
            if path == "/api/users":                  # owner: a new account; its token is shown once and never stored
                pub, token = c.users.create(str(body.get("name", "")), str(body.get("role", "member")), bool(body.get("can_spend", False)))
                from ..store import sync as _sync
                _sync.sync_users(c.out)
                return self._json(200, {"user": pub, "token": token})
            up = path.strip("/").split("/")
            if len(up) == 4 and up[:2] == ["api", "users"]:
                act = up[3]
                if act in ("disable", "enable"):
                    r = {"user": c.users.set_disabled(up[2], act == "disable")}
                elif act == "rotate":
                    pub, token = c.users.rotate(up[2])
                    r = {"user": pub, "token": token}
                elif act == "update":
                    r = {"user": c.users.update(up[2], body.get("can_spend"), body.get("role"), body.get("name"))}
                else:
                    raise pl.PipelineError(NO_ROUTE, 404)
                from ..store import sync as _sync
                _sync.sync_users(c.out)
                return self._json(200, r)
            if path == "/api/ai/backend":        # the AI selector (owner only): {backend: auto | local | cloud} and/or {model: <an id the local server lists>}; nothing is restarted, the next call uses it
                if "model" in body:
                    try:
                        llm.set_local_model(str(body.get("model") or ""))
                    except llm.LLMError as e:
                        return self._json(400, {"error": str(e), "models": llm.list_local_models()})       # a model the server does not list: the answer carries the list
                if "backend" in body or "model" not in body:
                    try:
                        llm.set_preference(str(body.get("backend", "")))
                    except llm.LLMError as e:
                        raise pl.PipelineError(str(e), 400)
                return self._json(200, llm.status())
            if path == "/api/telegram/config":
                return self._json(200, telegram.save_config(c.out, str(body.get("token", "")), str(body.get("user_id", ""))))
            if path == "/api/telegram/disconnect":
                return self._json(200, telegram.disconnect(c.out))
            if path == "/api/stickers/move":        # bulk move into one pack, all or nothing: {to, items: [{pack_id, id}, ...]}
                return self._json(200, c.lib.move_stickers([x for x in body.get("items", []) if isinstance(x, dict)], str(body.get("to", ""))))
            if path == "/api/stickers/delete":      # bulk delete from the library: [{pack_id, id}, ...]
                return self._json(200, {"deleted": c.lib.delete_stickers([x for x in body.get("items", []) if isinstance(x, dict)])})
            if path == "/api/watch/remove":      # to the trash, never straight to nothing
                return self._json(200, watch.remove(c.inp, c.out, str(body.get("number", "")), str(body.get("subject", ""))))
            if path == "/api/watch/restore":
                return self._json(200, watch.restore(c.inp, c.out, str(body.get("id", ""))))
            if path == "/api/watch/purge":
                return self._json(200, watch.purge(c.out, str(body.get("id", ""))))
            if path in ("/api/trash/purge", "/api/trash/purge_all"):      # the one real delete (owner only): 200 when it finished within the request, 202 + a task to poll when it is still running
                who = self.user.get("id") or "human"
                if path == "/api/trash/purge":
                    t = purge.purge_one(c.out, c.lib, str(body.get("type") or body.get("kind") or ""), str(body.get("id", "")), by=who, confirm_shared=body.get("confirm_shared") is True, busy=c.lock.locked())
                else:
                    t = purge.purge_all(c.out, c.lib, str(body.get("confirm", "")), by=who, busy=c.lock.locked(), kind=body.get("kind") or None)
                return self._json(200 if t["status"] != "running" else 202, t)
            if path == "/api/plan":      # preview only: nothing is reserved
                return self._json(200, tasks.preview(body.get("prompt", ""), body.get("grid", "3x3"), body.get("style_id", "flat_vector"), bool(body.get("ai")), bool(body.get("loop"))))
            if path == "/api/tasks":     # reserve: the next folder names + out/tasks/<NNN>.json (this is the G1 approval)
                return self._json(200, tasks.reserve(c.out, c.inp, body.get("prompt", ""), body.get("grid", "3x3"), body.get("style_id", "flat_vector"), bool(body.get("ai")), bool(body.get("loop"))))
            if path.startswith("/api/chat/sessions"):
                from ..agent.memory import SessionError as _SE
                cp = path.strip("/").split("/")
                store = c.chat_parts(self.user)[0]
                try:
                    if cp == ["api", "chat", "sessions"]:
                        return self._json(200, store.create(body.get("title"), body.get("settings") if isinstance(body.get("settings"), dict) else None))
                    if len(cp) == 5 and cp[4] == "messages":
                        store.load(cp[3])                                    # a stranger's chat is a 404 before anything is cached or started
                        return self._json(202, c.idem("chat:" + cp[3], self.headers.get("Idempotency-Key"), lambda: c.chat_send(cp[3], body, self.user)))
                    if len(cp) == 5 and cp[4] == "settings":
                        sess = store.load(cp[3])
                        allowed = {"grid": ("2x2", "3x3"), "ask_before_spending": (True, False), "ai": (True, False), "allow_vlm": (True, False)}
                        for k, v in body.items():
                            if k == "creator" and isinstance(v, dict):               # the agentic creator: on / scope (images | video) / bypass
                                cur = dict(sess["settings"].get("creator") or {"on": False, "scope": "images", "bypass": False})
                                for ck, cv in v.items():
                                    if ck in ("on", "bypass") and isinstance(cv, bool):
                                        cur[ck] = cv
                                    elif ck == "scope" and cv in ("images", "video"):
                                        cur[ck] = cv
                                sess["settings"]["creator"] = cur
                            elif k == "allow_vlm" and v in (True, False):
                                store.set_vision(sess, v)                            # state only: no chat turn; the next turn says it once
                            elif k in allowed and v in allowed[k]:
                                sess["settings"][k] = v
                            elif k == "style_id":
                                if v not in {p["id"] for p in styles.PRESETS}:        # an unknown style is refused out loud, never stored to fail later as "unknown style"
                                    raise pl.PipelineError(f"unknown style {v!r}: the styles are " + ", ".join(p["id"] for p in styles.PRESETS), 400)
                                sess["settings"][k] = v
                        store.save(sess)
                        return self._json(200, {"settings": sess["settings"]})
                    if len(cp) == 5 and cp[4] == "delete":
                        store.delete(cp[3])
                        return self._json(200, {"deleted": cp[3]})
                except _SE as e:
                    raise pl.PipelineError(str(e), e.code)
                raise pl.PipelineError(NO_ROUTE, 404)
            if path.startswith("/api/live/"):
                what = path.rsplit("/", 1)[1]
                if what in ("sheet", "video"):          # these spend credits: the same Idempotency-Key answers with the first job instead of starting (and paying for) another
                    return self._json(200, c.idem(f"live:{what}:{self.user['id']}", self.headers.get("Idempotency-Key"), lambda: self._live(what, body)))
                return self._json(200, self._live(what, body))
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
                    if act in ("check", "continue", "retry_estimate", "retry"):
                        from ..generation import recovery
                        job = jobs.read(c.out, jp[2])
                        if act == "check":
                            return self._json(200, recovery.check(c.out, jp[2], on_done=c.job_followup(job), by=self.user["id"]))
                        if act == "retry_estimate":
                            return self._json(200, recovery.quote(c.out, jp[2]))
                        if act == "continue":
                            job = recovery.continue_job(c.out, jp[2], by=self.user["id"])
                        else:
                            if not self.user.get("can_spend"):
                                raise pl.PipelineError("This account cannot start a paid Retry.", 403)
                            job = recovery.retry(c.out, jp[2], body.get("go"), body.get("estimate"), by=self.user["id"])
                        c.fulfil_async(job["id"], after=c.job_followup(job))
                        return self._json(200, job)
                except (jobs.JobError, higgsfield.HiggsError, model_catalog.CatalogError) as e:
                    raise pl.PipelineError(str(e), e.code)
                raise pl.PipelineError(NO_ROUTE, 404)
            if path == "/api/generations" and body.get("task"):      # Run: a generation linked to its reserved task
                if self.user.get("role") != "owner":
                    raise pl.PipelineError("this account cannot do that (owner only)", 403)

                def run_task():
                    if c.lock.locked():
                        raise pl.PipelineError("busy", 409)
                    t = tasks.read_task(c.out, body["task"])
                    gid = pl.start(t["prompt"], c.out, c.inp, pick=tasks.pick_for_task(c.inp, t, int(body.get("take", 0))), task=t,
                                   outline=int(body["outline"]) if body.get("outline") is not None else None,
                                   erode=int(body["erode"]) if body.get("erode") is not None else None)
                    tasks.link_generation(c.out, t["id"], gid)
                    c.submit(lambda: pl.run_stills(c.out, gid, c.cfg, c.pace))
                    return {"id": gid}
                return self._json(202, c.idem("generation-task:" + self.user["id"], self.headers.get("Idempotency-Key"), run_task))
            if path == "/api/assets/sign":      # {key, ttl?}: a signed, expiring link to one file under out/ (never a path the page invents)
                from ..store.assets import AssetError, LocalAssetStore
                store = LocalAssetStore(c.out)
                try:
                    key = str(body.get("key") or "")
                    if not store.exists(key):
                        raise AssetError("no such asset", 404)
                    if self.user.get("role") != "owner":
                        m = _KEY_PATH.match(key)
                        if not m or not c.visible(self.user, int(m.group(1))):
                            raise AssetError("no such asset", 404)
                    ttl = max(5, min(int(body.get("ttl", 300)), 3600))
                    return self._json(200, {"url": store.url(key, ttl, self.user["id"]), "expires_in": ttl})
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
                return self._json(202, c.idem("generation:" + self.user["id"], self.headers.get("Idempotency-Key"), create))
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[:2] == ["api", "generations"]:
                gid = int(parts[2])
                if parts[3] == "remove":         # to the trash, never straight to nothing (flow/batches.py); stickers already in packs stay in their packs
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    return self._json(200, batches.remove(c.out, gid, by=self.user.get("id") or "human"))
                if parts[3] == "restore":
                    return self._json(200, batches.restore(c.out, gid))
                if parts[3] == "join":           # Add to group / drag onto a batch: this batch's family goes under the family of `to` (the target is the parent; flow/groups.py)
                    return self._json(200, groups.join(c.out, gid, int(str(body.get("to") or "0").upper().lstrip("G") or 0), by=self.user.get("id") or "human"))
                if parts[3] == "leave":          # out of its family again: its own root
                    return self._json(200, groups.leave(c.out, gid, by=self.user.get("id") or "human"))
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
                    if body.get("reslice") and any(v["status"] == "SLICED" and v.get("video") for v in pl.read_result(c.out, gid)["video_sheets"]):
                        c.submit(lambda: gates.reslice(c.out, gid, pl.cfg_for(pl.read_result(c.out, gid), c.cfg), c.pace))
                        res_["resliced"] = True
                    return self._json(200, res_)
                if parts[3] == "recut":          # "Cut it anyway": cut a batch whose sheet was stopped, from the stored sheet, free (pipeline.recut)
                    pl.recut_check(c.out, gid)
                    c.submit(lambda: pl.recut(c.out, gid, c.cfg, c.pace, by=self.user.get("id") or "human"))
                    return self._json(202, {"id": gid})
                if parts[3] == "recut_particles":   # a sheet of particles that was cut as stickers: cut again as particles (exact equal cells, no sticker rule), from the stored sheet, free
                    pl.recut_check(c.out, gid)
                    if pl.read_result(c.out, gid).get("kind") == "particles":
                        raise pl.PipelineError("This batch was already cut as particles.", 409)
                    c.submit(lambda: pl.recut_as_particles(c.out, gid, c.cfg, c.pace, by=self.user.get("id") or "human"))
                    return self._json(202, {"id": gid})
                if parts[3] == "reveal":         # open the batch's folder in the file manager (a path the server computed, never one sent by the page)
                    import os as _os, subprocess as _sp, sys as _sys
                    target = pl.gen_dir(c.out, gid) / "slices"
                    if _sys.platform == "win32":
                        _os.startfile(str(target))
                    else:
                        _sp.Popen(["open" if _sys.platform == "darwin" else "xdg-open", str(target)])
                    return self._json(200, {"opened": str(target)})
                if parts[3] == "allow":          # "Use it anyway": a human allows (or takes back) a sticker or an animation that Python blocked as a judgement call (flow/gates.py)
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    allow = bool(body.get("allow", True))
                    kind = str(body.get("kind") or "animation")           # no `kind` = what this route always did: animations
                    if kind == "video_sheet":
                        res = pl.read_result(c.out, gid)
                        idx = gates.allowable(res, allow, kind) if body.get("all") else (body.get("indexes") or [body.get("sheet") or body.get("index")])
                        if not isinstance(idx, list) or not idx or any(not isinstance(a, str) for a in idx):
                            raise pl.PipelineError("sheet (A#), indexes (a list of A#) or all is required")
                        for aid in idx:
                            why = gates.sheet_problem(res, gates.sheet_of(res, aid), allow)
                            if why:
                                raise pl.PipelineError(why, 409)
                        c.submit(lambda: gates.allow_sheet(c.out, gid, idx, allow, c.cfg, c.pace))
                        return self._json(202, {"id": gid, "kind": kind, "indexes": idx, "index": idx[0], "allow": allow})
                    if kind not in gates.KINDS:
                        raise pl.PipelineError("kind must be 'still' or 'animation'")
                    if body.get("all"):
                        idx = gates.allowable(pl.read_result(c.out, gid), allow, kind)
                    else:
                        try:
                            idx = [int(i) for i in (body["indexes"] if isinstance(body.get("indexes"), list) else [body["index"]])]
                        except (KeyError, TypeError, ValueError):
                            raise pl.PipelineError("index (a sticker number), indexes (a list) or all is required")
                    if not idx:
                        raise pl.PipelineError("There is nothing to allow." if allow else "Nothing was allowed in this batch.", 409)
                    for i in idx:
                        gates.check_allow(c.out, gid, i, allow, kind)
                    c.submit(lambda: gates.allow_cells(c.out, gid, kind, idx, allow, pl.cfg_for(pl.read_result(c.out, gid), c.cfg), c.pace))
                    return self._json(202, {"id": gid, "kind": kind, "indexes": idx, "index": idx[0], "allow": allow})
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
                    pl.read_result(c.out, gid)                    # a batch that does not exist is a 404 now, not a 202 and a dead thread
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
                if parts[3] == "captions":       # write the AI caption of every cell (a model call per cell): the person must have allowed AI vision, in this very request
                    vision_consent.require(body.get("allow_vlm"))
                    pl.read_result(c.out, gid)
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    force = bool(body.get("force"))
                    c.submit(lambda: transcribe.captions_for(c.out, gid, force=force, allowed=True))
                    return self._json(202, {"id": gid, "force": force})
                if parts[3] == "judge":          # the vision model pre-reviews the stickers (S6): history lines only, a human still decides
                    vision_consent.require(body.get("allow_vlm"))                  # AI vision is the person's call, asked once and sent with the request
                    if c.lock.locked():
                        raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
                    from ..vision import judge as _vj
                    if _vj.status()["provider"] == "none":
                        raise pl.PipelineError("No vision backend: start LM Studio (MIRSAL_LOCAL_URL) or set OPENAI_API_KEY.", 409)
                    scope = "anim" if body.get("scope") == "anim" else "still"
                    pl.read_result(c.out, gid)                    # same: unknown batch = 404
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
            raise pl.PipelineError(NO_ROUTE, 404)
    return H


def serve(out: Path, inp: Path, port: int = 8770, pace: float = 0.0, cfg=None, block: bool = True, stdlib: bool | None = None, lan: bool = False,
          tls: dict | None = None):
    """FastAPI on uvicorn (console/app.py) by default; `stdlib=True` or MIRSAL_SERVER=stdlib runs the old ThreadingHTTPServer (kept for one release).
    Both serve the same handler, so every answer is the same. `lan`: office colleagues reach it on the local network (0.0.0.0; they sign in; docs/api.md, Office accounts on the LAN),
    `tls`: {cert, key} for HTTPS."""
    if lan:
        os.environ["MIRSAL_LAN"] = "1"
    c = Console(out, inp, pace, cfg)
    if stdlib is None:
        stdlib = os.environ.get("MIRSAL_SERVER", "").strip().lower() == "stdlib"
    if stdlib:
        srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(c))
    else:
        from .app import Server
        srv = Server(c, "0.0.0.0" if lan else "127.0.0.1", port, tls=tls)
    if lan:
        from ..services import admin_bot
        admin_bot.start(c)                             # Haitham's approvals in the Telegram bot (when the bot is configured in Settings)
    if not block:
        return srv, c
    scheme = "https" if tls else "http"
    print(f"Mirsal console on {scheme}://127.0.0.1:{srv.server_address[1]}  ({'stdlib' if stdlib else 'FastAPI on uvicorn'}; input: {inp}  out: {out})")
    if lan:
        names = sorted(n for n in c.lan_names if n[:1].isdigit())
        print("Office network: " + ", ".join(f"{scheme}://{n}:{srv.server_address[1]}" for n in names) + "  (colleagues sign in with an @nadi.ae account; this PC must stay on)")
        if not tls:
            print("WARNING: no TLS: passwords and sign-in cookies cross the office network unencrypted (serve --lan uses HTTPS unless --no-tls)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
