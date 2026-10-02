"""Generation lifecycle: 7 stages, each a real step with an event line in out/G00N/events.jsonl.

requested -> sheet_picked -> keyed -> sliced -> video_requested -> video_picked -> video_sliced
Used by the CLI and by the console. Picking steps are lookups over prepared files; the rest is real processing."""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import threading
import time
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np

from . import prompter, sources, tasks
from .engine import chroma, verify
from .engine.config import EngineConfig
from .engine.grid import detect_grid, split_grid
from .engine.render import apply_edge
from .engine.sheet import encode_static, key_sheet, slice_cells, stitch_keyed
from .engine.video import AnimationResult, AnimCache, pick_clip, process_clips, process_video

STAGES = ["requested", "sheet_picked", "keyed", "sliced", "video_requested", "video_picked", "video_sliced",
          "plan_reviewed", "stills_reviewed", "video_sheet_built", "video_sheet_reviewed", "video_returned", "anim_reviewed", "pack_final"]
SLICED = STAGES.index("sliced")     # every stage from here on has the stills on disk


class PipelineError(Exception):
    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code


# ---------- storage ----------
def gen_dir(out: Path, gid: int) -> Path:
    return out / f"G{gid:03d}"


def list_ids(out: Path) -> list[int]:
    if not out.is_dir():
        return []
    return sorted(int(m[1]) for d in out.iterdir() if (m := re.fullmatch(r"G(\d{3,})", d.name)))


import contextvars

OWNER = contextvars.ContextVar("mirsal_owner", default="local")     # who is acting: the request's user, copied into the threads it starts


def current_owner() -> str:
    return OWNER.get()


_IO_LOCK = threading.RLock()     # one reader or writer of result.json at a time inside this process


def _atomic_write(path: Path, data: bytes) -> None:
    """tmp file + os.replace. On Windows the replace fails with WinError 5 while anything (a polling request, an
    antivirus scan) has the target open, so in-process readers take the same lock and a foreign holder is retried."""
    tmp = path.with_name(path.name + ".tmp")
    with _IO_LOCK:
        tmp.write_bytes(data)
        for attempt in range(40):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if attempt == 39:
                    raise
                time.sleep(0.05)


def normalise(res: dict) -> dict:
    """Results written before 1F lack the review fields: give them empty ones so every reader can rely on the shape."""
    res.setdefault("reviews", {"plan": None, "video_sheet": {}, "pack": None})
    res.setdefault("video_sheets", [])
    res.setdefault("verify", {})
    res.setdefault("erode_px", EngineConfig().erode_px)   # generations written before the erosion setting
    for st in res["stickers"]:
        st.setdefault("tags", [st["key"]])
        st.setdefault("review", {"still": "BLOCKED" if st["status"] == "FAILED" else "PENDING", "anim": "NONE"})
        st.setdefault("history", [])
    return res


def read_result(out: Path, gid: int) -> dict:
    p = gen_dir(out, gid) / "result.json"
    if not p.exists():
        raise PipelineError(f"No generation G{gid:03d}", 404)
    with _IO_LOCK:
        return normalise(json.loads(p.read_text(encoding="utf-8")))


def write_result(out: Path, gid: int, res: dict) -> None:
    _atomic_write(gen_dir(out, gid) / "result.json", json.dumps(res, indent=2, ensure_ascii=False).encode())
    try:  # Phase 3A write-through: Postgres mirrors the file store when it is up; never raises
        from .store import sync
        sync.sync_result(out, gid, res)
    except Exception:
        pass


def read_events(out: Path, gid: int) -> list[dict]:
    p = gen_dir(out, gid) / "events.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def emit(out: Path, gid: int, stage: str, status: str, ms: int = 0, detail=None, actor: str | None = None, decision: str | None = None) -> None:
    ev = {"ts": round(time.time(), 3), "stage": stage, "status": status, "ms": ms, "detail": detail}
    if actor:                                  # gate decisions: who decided (python | human | vlm) and what
        ev["actor"], ev["decision"] = actor, decision
    try:                                       # tracing (backend none: returns None at once): the run id rides on the event
        from .obs import trace
        rid = trace.emit_event(out, gid, ev)
        if rid:
            ev["trace_run_id"] = rid
    except Exception:
        pass
    line = json.dumps(ev, ensure_ascii=False)
    with open(gen_dir(out, gid) / "events.jsonl", "a", encoding="utf-8") as f:
        f.write(line + "\n")
    try:                                       # the same event on the Redis stream (Phase 5 names); events.jsonl stays the record
        from . import events as _events
        _events.publish(out, gid, ev)
    except Exception:
        pass


def latest_id(out: Path) -> int:
    ids = list_ids(out)
    if not ids:
        raise PipelineError("No generations yet. Run: create \"<prompt>\"", 404)
    return ids[-1]


def media_name(kind: str, gid: int, task_slug: str, key: str) -> str:
    return f"{kind}-{gid:03d}-{task_slug}-{key}"      # e.g. img-001-teddy_bear_school-teddy_bear_with_a_book


def load_rgb(path: Path) -> np.ndarray:
    img = cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise PipelineError(f"Cannot decode {path.name}", 422)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


class Stage:
    """Context manager: emits start / done|error with timing, plus optional pacing for live demos."""
    def __init__(self, out, gid, stage, pace=0.0, detail=None):
        self.out, self.gid, self.stage, self.pace, self.detail = out, gid, stage, pace, detail

    def __enter__(self):
        self.t0 = time.perf_counter()
        emit(self.out, self.gid, self.stage, "start", 0, self.detail)
        return self

    def __exit__(self, et, ev, tb):
        ms = int((time.perf_counter() - self.t0) * 1000)
        if ev:
            emit(self.out, self.gid, self.stage, "error", ms, str(ev)[:300])
            return False
        if self.pace:
            time.sleep(self.pace)
        emit(self.out, self.gid, self.stage, "done", ms, getattr(self, "result", None))


# ---------- create ----------
def next_variant(out: Path, subject: str, n: int) -> int:
    """Each new generation of a subject takes the next prepared variant (001 -> 002 -> ... -> wrap), like a fresh generation."""
    for gid in reversed(list_ids(out)):
        try:
            r = read_result(out, gid)
        except Exception:
            continue
        if r["source"]["subject"] == subject:
            return r["source"]["variant"] % n + 1
    return 1


def generations_by_folder(out: Path) -> dict:
    """{(subject, folder number): ['G028', ...]} - which generations were made from which watch folder (oldest first)."""
    found: dict = {}
    for gid in list_ids(out):
        try:
            s = read_result(out, gid)["source"]
        except Exception:
            continue
        found.setdefault((s["subject"], s.get("subject_id")), []).append(f"G{gid:03d}")
    return found


def list_inputs(inp: Path) -> list[dict]:
    return [{"subject": subj, "variants": [
        {"variant": p.variant, "folder": p.subject_id, "sheet": p.sheet.name, "video": p.video.name if p.video else None,
         "clips": len(p.clips), "clips_dup_of": p.clips_dup_of, "pairing": p.pairing, "plan": p.plan.name if p.plan else None} for p in picks]}
        for subj, picks in sources.scan(inp).items()]


def start(prompt: str, out: Path, inp: Path, variant: int | None = None, pick: sources.Pick | None = None, parent: int | None = None,
          grid: tuple | None = None, task: dict | None = None, regen_of: str | None = None, regen_plan: dict | None = None,
          outline: int | None = None, erode: int | None = None) -> int:
    """Synchronous part: match source, run the prompter, allocate G00N. Returns the id fast.
    grid: the user's choice (3x3 / 2x2). A prepared sheet's own layout wins: it is measured from its gutters."""
    if outline is not None and not 0 <= int(outline) <= 40:
        raise PipelineError("outline must be 0 (none) to 40 px")
    if erode is not None and not 0 <= int(erode) <= 8:
        raise PipelineError("erode must be 0 (none) to 8 px")
    if pick is None:
        base = sources.find(inp, prompt, 1)
        if base:
            picks = sources.scan(inp)[base.subject]
            pick = picks[min(max(variant or 1, 1), len(picks)) - 1]      # explicit folder, else the first: it never advances by itself
    if not pick:
        raise PipelineError(f"No prepared set for that. Try: {', '.join(sources.known_subjects(inp)) or '(none found)'}", 404)
    if regen_plan:  # 1x1 regeneration of one sticker: the plan is that sticker's own (key, tags, emoji) in a single-cell template
        plan = regen_plan
    elif task and task.get("plan"):   # a task reserved in the Inbox: its saved plan (template + slots) is the plan
        plan = prompter.validate_plan(json.loads(json.dumps(task["plan"])))
    elif pick.plan:   # hand-written prompts that match the sheet Haitham actually generated
        try:
            plan = prompter.validate_plan(json.loads(pick.plan.read_text(encoding="utf-8")))
        except (ValueError, OSError) as e:
            raise PipelineError(f"Bad prompts file {pick.plan.name}: {e}", 422)
    else:
        measured = detect_grid(load_rgb(pick.sheet))
        plan = prompter.expand(prompt, measured if measured in prompter.GRIDS else tuple(grid or (3, 3)))
    out.mkdir(parents=True, exist_ok=True)
    gid = (list_ids(out) or [0])[-1] + 1
    d = gen_dir(out, gid)
    (d / "source").mkdir(parents=True)
    (d / "slices").mkdir()
    (d / "prompts.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    res = {
        "generation_id": f"G{gid:03d}", "number": gid, "owner": current_owner(), "created": round(time.time(), 3), "parent": parent, "prompt": prompt, "task": plan["task"], "task_slug": plan["task_slug"],
        "source": {"subject": pick.subject, "subject_id": pick.subject_id, "variant": pick.variant,
                   "n_variants": pick.n_variants, "sheet": pick.sheet.name, "video": pick.video.name if pick.video else None,
                   "has_video": pick.has_video, "pairing": pick.pairing, "clips_dup_of": pick.clips_dup_of,
                   "clips": {str(n): {f: str(p) for f, p in d.items()} for n, d in pick.clips.items()}, "sheet_path": str(pick.sheet),
                   "video_path": str(pick.video) if pick.video else None},
        "grid": plan["grid"], "stage": "requested", "error": None, "plan_source": "task " + task["id"] if task else pick.plan.name if pick.plan else "stub (prompter.py)",
        "sheet_prompt": plan.get("sheet_prompt", ""), "video_prompt": plan.get("video_prompt", ""),
        "template_id": plan.get("template_id"), "template_version": plan.get("template_version"), "slots": plan.get("slots"),
        "task_id": task["id"] if task else None, "name_key": plan["task_slug"], "regen_of": regen_of,
        "verify_version": verify.VERIFY_VERSION,
        "outline_px": int(outline) if outline is not None else EngineConfig().outline_px,    # the white die-cut stroke is a choice, kept with the generation
        "erode_px": int(erode) if erode is not None else EngineConfig().erode_px,          # fringe trim, kept with the generation; 0 = none
        "reviews": {"plan": (task or {}).get("plan_review"), "video_sheet": {}, "pack": None}, "video_sheets": [], "verify": {},
        "stickers": [new_sticker(gid, plan["task_slug"], s) for s in plan["stickers"]],
    }
    write_result(out, gid, res)
    emit(out, gid, "requested", "done", 0, {"prompt": prompt, "task_slug": plan["task_slug"]})
    return gid


def approve_plan(out: Path, gid: int, note: str) -> None:
    """Pressing Generate on a prepared folder is the human's G1 decision (the same as saving a task in the Inbox)."""
    res = read_result(out, gid)
    if not res["reviews"].get("plan"):
        res["reviews"]["plan"] = {"decision": "APPROVE", "by": "human", "ts": round(time.time(), 3), "note": note}
        write_result(out, gid, res)


def new_sticker(gid: int, task_slug: str, s: dict) -> dict:
    return {"index": s["index"], "key": s["key"], "tags": s.get("tags") or [s["key"]], "emoji": s["emoji"], "prompt": s["prompt"],
            "name": media_name("img", gid, task_slug, s["key"]),
            "status": "PENDING", "reason": None, "report": [], "metrics": {}, "png": None,
            "anim_status": "NOT_REQUESTED", "anim_reason": None, "anim_metrics": {}, "webm": None,
            "review": {"still": "PENDING", "anim": "NONE"}, "history": []}


def hist(st: dict, stage: str, actor: str, decision: str, reason: str | None = None, ref: str | None = None, detail=None) -> None:
    """One line of a sticker's path through the golden path (Phase 2: one `reviews` row)."""
    st.setdefault("history", []).append({"ts": round(time.time(), 3), "stage": stage, "actor": actor, "decision": decision,
                                         "reason": reason, "ref": ref, "detail": detail})


def block_detail(report: list) -> dict | None:
    """The first failing BLOCK check of a report (dicts as stored in result.json), trimmed for a history line."""
    c = next((c for c in report if not c.get("ok") and c.get("severity", "BLOCK") == "BLOCK"), None)
    if not c:
        return None
    return {"check": c["name"], "value": c.get("value"), "limit": c.get("limit"), "note": c.get("detail"), "data": c.get("data")}


def cfg_for(res: dict, cfg: EngineConfig) -> EngineConfig:
    """The engine config of one generation: the server's, with the edge finish that was chosen for it
    (outline_px 0 = no stroke, erode_px 0 = no trim)."""
    kw = {}
    if res.get("outline_px") is not None:
        kw["outline_px"] = int(res["outline_px"])
    if res.get("erode_px") is not None:
        kw["erode_px"] = int(res["erode_px"])
    if res.get("key_colour") == "blue":       # the sheet came with a blue screen (green is the default and is never written): keyer, despill and video sheet follow it
        kw["chroma"] = "blue"
    return cfg if not kw else replace(cfg, **kw)


def run_stills(out: Path, gid: int, cfg: EngineConfig, pace: float = 0.0) -> None:
    res = read_result(out, gid)
    base = cfg
    cfg = cfg_for(res, cfg)
    d = gen_dir(out, gid)
    try:
        blocked = None
        with Stage(out, gid, "sheet_picked", pace) as s:
            src = Path(res["source"]["sheet_path"])
            dest = d / "source" / f"sheet{src.suffix.lower()}"
            shutil.copyfile(src, dest)
            res["source"]["sheet_copy"] = f"source/{dest.name}"
            rows, cols = res.get("grid") or (3, 3)
            asked = (res.get("slots") or {}).get("key_colour", "green")
            try:
                key, key_score = chroma.detect_key(load_rgb(dest), base.border_px, asked, base.min_key_diff)      # the screen the sheet REALLY has wins over the one that was asked for
            except Exception:
                key, key_score = asked, {}
            if key == "blue":
                res["key_colour"] = "blue"          # written only for blue: green is the default
            else:
                res.pop("key_colour", None)
            cfg = cfg_for(res, replace(base, chroma="green") if key != "blue" else base)
            if res.get("task_id"):
                tasks.annotate_key(out, res["task_id"], key, asked)
            vin = {"data": dest.read_bytes(), "grid": (rows, cols), "chroma": cfg.chroma}
            checks = verify.run("sheet", vin, cfg)                  # the sheet is judged on arrival, before anything is sliced
            res["verify"]["sheet"] = [c.to_dict() for c in checks]
            blocked = next((c for c in checks if not c.ok and c.severity == verify.BLOCK), None)
            sheet = vin.get("rgb")
            if sheet is not None:
                res["source"]["sheet_size"] = [int(sheet.shape[1]), int(sheet.shape[0])]
            s.result = {"subject": res["source"]["subject"], "variant": res["source"]["variant"],
                        "of": res["source"]["n_variants"], "file": src.name,
                        "blocked": blocked.id if blocked else None, "warnings": [c.id for c in checks if not c.ok and c.severity == verify.WARN]}
            res["stage"] = "sheet_picked"; write_result(out, gid, res)
        if blocked:
            with Stage(out, gid, "sliced", pace) as s:
                for st in res["stickers"]:
                    st.update(status="FAILED", reason=blocked.id, report=[blocked.to_dict()], metrics={"sheet_blocked": True})
                    st["review"]["still"] = "BLOCKED"
                    hist(st, "sheet", "python", "BLOCK", blocked.id, detail={"check": blocked.id, "value": _json(blocked.value), "limit": _json(blocked.limit), "note": blocked.note})
                s.result = {"ready": 0, "failed": len(res["stickers"]), "blocked": blocked.id}
                res["stage"] = "sliced"; write_result(out, gid, res)
            return
        with Stage(out, gid, "keyed", pace) as s:
            rects, ginfo = vin["rects"], vin["split_info"]
            res["source"]["grid"] = {"rows": rows, "cols": cols, "rects": [list(r) for r in rects], **ginfo}
            cells = key_sheet(sheet, cfg, rects)
            ok, buf = cv2.imencode(".png", cv2.cvtColor(stitch_keyed(cells, sheet.shape), cv2.COLOR_RGBA2BGRA))
            (d / "source" / "keyed.png").write_bytes(buf.tobytes())
            res["source"]["keyed"] = "source/keyed.png"
            s.result = {"bg": cells[0].keyed.bg, "threshold": [round(c.keyed.t, 1) for c in cells],
                        "grid": f"{rows}x{cols}", "cut": ginfo["method"], "xs": ginfo["xs"], "ys": ginfo["ys"]}
            res["stage"] = "keyed"; write_result(out, gid, res)
        with Stage(out, gid, "sliced", pace) as s:
            (d / "source" / "plain").mkdir(exist_ok=True)
            for st, r in zip(res["stickers"], slice_cells(cells, cfg)):
                st.update(status=r.status, reason=r.reason, report=r.report.checks, metrics=r.metrics)
                if r.data:
                    st["png"] = f"slices/{st['name']}.{r.fmt}"
                    (d / st["png"]).write_bytes(r.data)
                if r.plain is not None:    # the outline-free twin the video sheet is built from
                    ok, buf = cv2.imencode(".png", cv2.cvtColor(r.plain, cv2.COLOR_RGBA2BGRA))
                    (d / "source" / "plain" / f"S{st['index']}.png").write_bytes(buf.tobytes())
                if r.status == "READY":
                    st["review"]["still"] = "PENDING"
                    hist(st, "sliced", "python", "PASS", detail={"warnings": r.metrics.get("warnings", [])})
                else:
                    st["review"]["still"] = "BLOCKED"
                    hist(st, "sliced", "python", "BLOCK", r.reason, detail=block_detail(r.report.checks))
                try:                       # sticker_ready / sticker_failed, one per sticker as it is cut (Redis stream, best effort)
                    from . import events as _events
                    _events.sticker_events(out, gid, [st])
                except Exception:
                    pass
            ready = sum(1 for st in res["stickers"] if st["status"] == "READY")
            s.result = {"ready": ready, "failed": len(res["stickers"]) - ready}
            res["stage"] = "sliced"; write_result(out, gid, res)
    except Exception as e:
        res["error"] = str(e)[:300]; write_result(out, gid, res)


def record_anim(d: Path, st: dict, r, ref: str) -> None:
    """Store one animation result on its sticker: status, metrics, file, review state and the verifier's history line."""
    st.update(anim_status=r.status, anim_reason=r.reason, anim_metrics=r.metrics, anim_report=r.report.checks)
    if r.data:
        st["webm"] = f"slices/{st['name'].replace('img-', 'vid-', 1)}.webm"
        (d / st["webm"]).write_bytes(r.data)
    oob = next((c for c in (r.report.checks if r.status == "READY" else []) if c["name"] == "inside_frame" and not c["ok"]), None)
    if oob:       # made, but the character leaves its cell: kept for inspection, blocked for review so it cannot be added
        st["review"]["anim"] = "BLOCKED"
        hist(st, "video", "python", "BLOCK", "inside_frame", ref, {"check": "inside_frame", "value": oob.get("value"), "limit": oob.get("limit"), "note": oob.get("detail"), "data": oob.get("data")})
    elif r.status == "READY":
        st["review"]["anim"] = "PENDING"
        hist(st, "video", "python", "PASS", ref=ref, detail={"warnings": r.metrics.get("warnings", [])})
    else:
        st["review"]["anim"] = "BLOCKED"
        hist(st, "video", "python", "BLOCK", r.reason, ref, block_detail(r.report.checks) or {"check": r.reason, "note": r.metrics.get("error")})


def _json(v):
    return v.item() if hasattr(v, "item") else v


# ---------- Studio edit: layers over a sticker, exported to BOTH its image and its animation ----------
def _original(d: Path, st: dict, kind: str) -> Path:
    """The file as the generator made it, kept once in source/orig/; every Studio edit starts from it, so re-editing never stacks on a previous edit."""
    rel = st["webm"] if kind == "webm" else st["png"]
    orig = d / "source" / "orig" / (Path(rel).name if kind == "webm" else f"S{st['index']}.png")
    if not orig.exists():
        orig.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(d / rel, orig)
    return orig


def studio_edit_open(out: Path, gid: int, index: int, projects, cfg: EngineConfig) -> dict:
    """Open (or reopen) the layered edit of a sticker that has an animation: a video project made from the ORIGINAL animation, whose layers are the
    edit. The project lives in the Studio; nothing is baked into the generator's files until `studio_edit_commit`."""
    res = read_result(out, gid)
    if not 1 <= index <= len(res["stickers"]):
        raise PipelineError(f"index 1..{len(res['stickers'])} required")
    st = res["stickers"][index - 1]
    if st.get("anim_status") != "READY" or not st.get("webm"):
        raise PipelineError("This sticker has no animation yet: edit its image from the Stickers view.", 409)
    pid = (st.get("edit") or {}).get("project")
    if pid:
        try:
            projects.get(pid)
            return {"project": pid, "reused": True}
        except Exception:
            pass
    d = gen_dir(out, gid)
    base = _original(d, st, "webm")
    proj = projects.create(base.read_bytes(), st["name"] + ".webm")
    fps = int(max(6, min(cfg.video_max_fps, round((st.get("anim_metrics") or {}).get("fps") or 24))))
    projects.update(proj["id"], {"video": {"fps": fps}, "name": st["key"].replace("_", " ")[:60]})
    st["edit"] = {"project": proj["id"], "layers": [], "at": None}
    write_result(out, gid, res)
    return {"project": proj["id"], "reused": False}


def studio_edit_commit(out: Path, gid: int, index: int, projects, overlays: dict, cfg: EngineConfig, lib=None) -> dict:
    """Export the Studio edit: the animation is re-rendered from the original with the layers (with their timing), and the same layers are composited
    onto the original image (all visible layers, timing ignored). Both files are replaced in place (same names, same S#); the originals stay in
    source/orig/; the pack copies of this sticker take the new files."""
    import numpy as np
    from .library import LibraryError, decode_image, png_bytes, validate_render
    from .video_project import _over
    res = read_result(out, gid)
    st = res["stickers"][index - 1]
    pid = (st.get("edit") or {}).get("project")
    if not pid:
        raise PipelineError("Open the edit first.", 409)
    try:
        proj = projects.get(pid)
        data, _mime, ext, info = projects.render(pid, "webm", overlays)
    except LibraryError as e:
        raise PipelineError(str(e), e.code if hasattr(e, "code") else 409)
    if ext != "webm" or len(data) > cfg.video_max_bytes:
        raise PipelineError(f"The edited animation is {len(data) // 1024} KB, over Telegram's {cfg.video_max_bytes // 1024} KB limit. Remove a layer or shorten it.", 409)
    d = gen_dir(out, gid)
    base_png = _original(d, st, "png")
    img = decode_image(base_png.read_bytes())
    drawn = []
    for L in sorted(proj["layers"], key=lambda x: x["zIndex"]):
        if L["visible"] and L["id"] in overlays:
            ov = decode_image(overlays[L["id"]])
            if ov.shape[:2] != img.shape[:2]:
                import cv2
                ov = cv2.resize(ov, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_AREA)
            img = _over(img, ov)
            drawn.append({"type": L["type"], "text": (L.get("payload") or {}).get("text") or (L.get("payload") or {}).get("char"), "timing": L.get("timing")})
    try:
        body, ext2, _ = validate_render(png_bytes(img), cfg)
    except LibraryError as e:
        raise PipelineError(str(e), 409)
    (d / st["webm"]).write_bytes(data)
    cur = Path(st["png"])
    if ext2 != cur.suffix.lstrip("."):
        (d / st["png"]).unlink(missing_ok=True)
        st["png"] = str(cur.with_suffix("." + ext2)).replace("\\", "/")
    (d / st["png"]).write_bytes(body)
    now = round(time.time(), 3)
    st["edited"], st["edited_at"] = True, now
    st["edit"].update(layers=drawn, at=now)
    st["metrics"]["kb"] = max(1, len(body) // 1024)
    st.setdefault("anim_metrics", {})["kb"] = round(len(data) / 1024, 1)
    st["anim_metrics"]["edited"] = True
    hist(st, "video", "human", "EDIT", reason="edited in the Studio: image and animation", detail={"layers": drawn})
    write_result(out, gid, res)
    emit(out, gid, "still_edited", "done", 0, {"index": index, "studio": True, "layers": len(drawn)}, "human", "EDIT")
    refreshed = lib.refresh_from_generation(out, res["generation_id"], index, d / st["png"], d / st["webm"]) if lib else 0
    return {"index": index, "edited_at": now, "layers": len(drawn), "kb_video": round(len(data) / 1024, 1), "kb_image": st["metrics"]["kb"], "pack_copies": refreshed}


# ---------- judge animations that were made before the border check existed ----------
def recheck_bounds(out: Path, gid: int, cfg: EngineConfig) -> dict:
    """Animations made by older code have no `inside_frame` verdict, so a character that leaves its cell was never flagged. This runs that one check on
    the SOURCE cell of every READY animation that lacks a verdict (decode + key only, no render, no encode, ~1 s for 9 cells), records it exactly as a
    new animation would be (the check in `anim_report`, a warning, `review.anim = BLOCKED` on a failure, a history line) and marks the sticker
    `bounds_checked`. A sticker the human already rejected stays rejected. Video-sheet slots have `inside_slot` and are skipped."""
    from concurrent.futures import ThreadPoolExecutor
    from .engine import ffmpeg as ff
    from .engine.grid import scale_rects
    from .engine.video import bounds_check, keyed_cell, keyed_clip
    res = read_result(out, gid)
    cfg = cfg_for(res, cfg)
    src = res["source"]
    clips = {int(k): {f: Path(p) for f, p in v.items()} for k, v in src.get("clips", {}).items()}
    mp4 = Path(src["video_path"]) if src.get("video_path") and Path(src["video_path"]).is_file() else None
    todo = []
    for st in res["stickers"]:
        names = {c["name"] for c in st.get("anim_report") or []}
        how = (st.get("anim_metrics") or {}).get("source") or ""
        if st["anim_status"] == "READY" and not st.get("bounds_checked") and not names & {"inside_frame", "inside_slot"} and (how == "3x3 mp4" or how.startswith("clip:")):
            todo.append((st["index"], how))
    if not todo:
        return {"checked": 0, "flagged": []}
    geo = None
    if mp4 and any(h == "3x3 mp4" for _, h in todo):
        info = ff.probe(mp4)
        g = src.get("grid")
        W, H = info["width"], info["height"]
        vr = scale_rects(g["rects"], tuple(src["sheet_size"]), (W, H)) if g else [(c * (W // 3), r * (H // 3), W // 3, H // 3) for r in range(3) for c in range(3)]
        cap = cfg.video_max_fps if info["fps"] > cfg.video_max_fps else None
        fps = cfg.video_max_fps if cap else info["fps"]
        geo = (vr, cap, int(math.floor(cfg.video_max_seconds * fps)))

    def one(item):
        i, how = item
        try:
            if how == "3x3 mp4":
                if not geo:
                    return i, None
                keyed = keyed_cell(mp4, geo[0][i - 1], geo[1], geo[2], cfg)
            else:
                fmt = how.split(":", 1)[1]
                if i not in clips or fmt not in clips[i]:
                    return i, None
                keyed = keyed_clip(clips[i][fmt], cfg)
            return i, bounds_check(keyed, cfg)
        except Exception:
            return i, None
    with ThreadPoolExecutor(max_workers=max(1, min(cfg.anim_workers, len(todo)))) as ex:
        checks = list(ex.map(one, todo))
    flagged = []
    for i, chk in checks:
        if chk is None:
            continue
        st = res["stickers"][i - 1]
        st["bounds_checked"] = True
        st.setdefault("anim_report", []).append(chk.to_dict())
        if not chk.ok:
            st.setdefault("anim_metrics", {}).setdefault("warnings", []).append("inside_frame")
            if st["review"]["anim"] != "REJECTED":
                st["review"]["anim"] = "BLOCKED"
            hist(st, "video", "python", "BLOCK", "inside_frame", "bounds recheck",
                 {"check": "inside_frame", "value": chk.value, "limit": chk.limit, "note": chk.note, "data": chk.to_dict()["data"]})
            flagged.append(i)
    write_result(out, gid, res)
    emit(out, gid, "bounds_rechecked", "done", 0, {"checked": [i for i, c in checks if c is not None], "flagged": flagged})
    return {"checked": sum(c is not None for _, c in checks), "flagged": flagged}


# ---------- edit a still in place (the sticker editor's Save, opened from Generate) ----------
def edit_still(out: Path, gid: int, index: int, png: bytes, cfg: EngineConfig, lib=None) -> dict:
    """Replace one still with the editor's 512x512 result, in place: same file name, same S#. The original is kept once in source/orig/ so
    nothing is lost; the animation (made from the video, not from the still) is untouched."""
    from .library import LibraryError, validate_render
    res = read_result(out, gid)
    if not 1 <= index <= len(res["stickers"]):
        raise PipelineError(f"index 1..{len(res['stickers'])} required")
    st = res["stickers"][index - 1]
    if st["status"] != "READY" or not st.get("png"):
        raise PipelineError(f"S{index} is not a READY still.", 409)
    try:
        body, ext, _ = validate_render(png, cfg)
    except LibraryError as e:
        raise PipelineError(str(e), 409)
    d = gen_dir(out, gid)
    f, orig = d / st["png"], d / "source" / "orig" / f"S{index}.png"
    if not orig.exists():
        orig.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, orig)
    if ext != f.suffix.lstrip("."):            # over the PNG limit: Telegram takes a lossless WebP just as well; the file keeps its name, the extension follows
        f.unlink(missing_ok=True)
        st["png"] = str(Path(st["png"]).with_suffix("." + ext)).replace("\\", "/")
        f = d / st["png"]
    f.write_bytes(body)
    st["edited"], st["edited_at"] = True, round(time.time(), 3)
    st["metrics"]["kb"] = max(1, len(body) // 1024)
    hist(st, "still", "human", "EDIT", reason="edited in the sticker editor")
    write_result(out, gid, res)
    emit(out, gid, "still_edited", "done", 0, {"index": index}, "human", "EDIT")
    refreshed = lib.refresh_from_generation(out, res["generation_id"], index, d / st["png"], None) if lib else 0
    return {"index": index, "edited_at": st["edited_at"], "kb": st["metrics"]["kb"], "has_animation": st.get("anim_status") == "READY", "pack_copies": refreshed}


# ---------- appearance (re-finish the edge of an existing generation) ----------
# The full "still" stage judges keying (needs the cell); an appearance re-render only re-judges the
# finished image. These checks run on the new file; the keying-stage verdicts (blank_cell, inside_cell,
# no_spill, chroma_risk, single_subject, duplicate_cell) and their metrics stay as Python recorded them.
APPEARANCE_CHECKS = ("dimensions", "transparent_corners", "foreground", "holes", "edge_trimmed", "static_file")


def edge_preview(out: Path, gid: int, index: int, outline: int, erode: int, px: int = 420) -> bytes:
    """One sticker as it would look with this stroke and trim, rendered from its stroke-free twin by the same function the real render uses. Nothing is stored:
    the Studio shows it on ONE thumbnail while a slider moves, and the edge only becomes real on Apply, when the video is generated, or when the stickers go into a pack."""
    if not 0 <= int(outline) <= 40 or not 0 <= int(erode) <= 8:
        raise PipelineError("outline must be 0..40 px and erode 0..8 px")
    plain = gen_dir(out, gid) / "source" / "plain" / f"S{int(index)}.png"
    if not plain.is_file():
        raise PipelineError("This sticker has no stroke-free original to preview.", 404)
    rgba = cv2.cvtColor(cv2.imdecode(np.fromfile(str(plain), np.uint8), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
    fin = apply_edge(rgba[..., :3].astype(np.float32), rgba[..., 3].astype(np.float32) / 255.0, int(outline), int(erode))
    if px and max(fin.shape[:2]) > px:
        k = px / max(fin.shape[:2])
        fin = cv2.resize(fin, (max(1, round(fin.shape[1] * k)), max(1, round(fin.shape[0] * k))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".png", cv2.cvtColor(fin, cv2.COLOR_RGBA2BGRA))
    return buf.tobytes()


def set_appearance(out: Path, gid: int, cfg: EngineConfig, outline: int | None = None, erode: int | None = None) -> dict:
    """Change the edge finish stored with a generation and re-render its stills from the outline-free
    `source/plain/S#.png` (cheap: no re-keying). Animation files keep their old edge, so any sticker with a
    webm is marked STALE: the next Animate re-renders its frames from the source video. Returns the new state."""
    if outline is not None and not 0 <= int(outline) <= 40:
        raise PipelineError("outline must be 0 (none) to 40 px")
    if erode is not None and not 0 <= int(erode) <= 8:
        raise PipelineError("erode must be 0 (none) to 8 px")
    res = read_result(out, gid)
    if outline is not None:
        res["outline_px"] = int(outline)
    if erode is not None:
        res["erode_px"] = int(erode)
    cfg = cfg_for(res, cfg)
    d = gen_dir(out, gid)
    rerendered, stale = 0, []
    for st in res["stickers"]:
        if st["status"] != "READY":
            continue
        plain = d / "source" / "plain" / f"S{st['index']}.png"
        if st.get("edited") or not plain.exists():              # an edited still keeps the user's pixels                            # generations written before the plain twins
            continue
        rgba = cv2.cvtColor(cv2.imdecode(np.fromfile(str(plain), np.uint8), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
        fin = apply_edge(rgba[..., :3].astype(np.float32), rgba[..., 3].astype(np.float32) / 255.0,
                         cfg.outline_px, cfg.erode_px)
        metrics: dict = {}
        img_bgra = cv2.cvtColor(fin, cv2.COLOR_RGBA2BGRA)
        ok, buf = cv2.imencode(".png", img_bgra)
        data = buf.tobytes()
        report = verify.run("still", {"plain": rgba[..., 3], "metrics": metrics, "img": fin,
                                      "render": lambda: fin,
                                      "encode": lambda img, c: (data, "png")}, cfg, only=APPEARANCE_CHECKS)
        fresh = {c.id: c.to_dict() for c in report}
        if any(c["severity"] == "BLOCK" and not c["ok"] for c in fresh.values()):
            continue                                     # never writes a file the verifier BLOCKs; the old still stands
        kept = [c for c in st.get("report", []) if c.get("name") not in fresh]
        order = [c for c, _, _, _ in verify.CATALOGUE.get("still", [])]
        st["report"] = sorted(kept + list(fresh.values()), key=lambda c: order.index(c["name"]) if c["name"] in order else 99)
        st.get("metrics", {}).update({k: v for k, v in metrics.items() if k in ("holes", "kb", "format")})
        st["metrics"]["outline_px"], st["metrics"]["erode_px"] = cfg.outline_px, cfg.erode_px
        ok, buf = cv2.imencode(".png", cv2.cvtColor(fin, cv2.COLOR_RGBA2BGRA))
        (d / st["png"]).write_bytes(buf.tobytes())
        st["rendered_at"] = round(time.time(), 3)                  # the page puts it in the image URL, so the new edge is fetched, not the cached old one
        hist(st, "appearance", "human", "PASS", detail={"outline_px": cfg.outline_px, "erode_px": cfg.erode_px})
        rerendered += 1
        if st.get("webm"):
            st["anim_status"] = "STALE"
            st["anim_reason"] = ("edge changed: applied again from the stored video" if any(v.get("video") for v in res.get("video_sheets", []))
                                 else "edge changed: Animate again to apply it")
            st["review"]["anim"] = "NONE"
            stale.append(st["index"])
    write_result(out, gid, res)
    emit(out, gid, "appearance", "done", 0, {"outline_px": res["outline_px"], "erode_px": res["erode_px"],
                                             "rerendered": rerendered, "stale": stale})
    return {"ok": True, "outline_px": res["outline_px"], "erode_px": res["erode_px"],
            "rerendered": rerendered, "stale": stale}


# ---------- more ----------
def more(out: Path, inp: Path, from_id: int | None = None) -> int:
    from_id = from_id or latest_id(out)
    res = read_result(out, from_id)
    s = res["source"]
    nxt = sources.variant_of(inp, s["subject"], s["variant"] + 1)
    if not nxt:
        raise PipelineError(f"That's all {s['n_variants']} prepared variations of {s['subject']}.", 409)
    return start(res["prompt"], out, inp, pick=nxt, parent=from_id,
                   outline=res.get("outline_px"), erode=res.get("erode_px"))   # a batch keeps the session's edge finish


def regen(out: Path, inp: Path, gid: int, index: int, subject: str | None = None) -> int:
    """Regenerate ONE sticker as a 1x1 run through the same engine. It becomes a new generation (`regen_of: G00N/S#`) whose single
    sticker goes through G2 -> video -> G4 alone; the parent is never modified."""
    from . import gates
    res = read_result(out, gid)
    if not 1 <= index <= len(res["stickers"]):
        raise PipelineError(f"index 1..{len(res['stickers'])} required")
    subj = subject or res["source"]["subject"]
    picks = sources.scan(inp).get(subj)
    if not picks:
        raise PipelineError(f"No prepared sheet for '{subj}'. Put a 1x1 sheet in img-NNN-{subj}/.", 404)
    pick = picks[next_variant(out, subj, len(picks)) - 1]
    if detect_grid(load_rgb(pick.sheet)) != (1, 1):
        raise PipelineError(f"{pick.sheet.name} is not a 1x1 sheet (one character on one canvas).", 409)
    new = start(res["prompt"], out, inp, pick=pick, parent=gid, regen_of=f"{res['generation_id']}/S{index}", regen_plan=gates.regen_plan(res, index),
                outline=res.get("outline_px"), erode=res.get("erode_px"))
    plan = res["reviews"].get("plan")
    if plan and plan["decision"] == "APPROVE":
        r2 = read_result(out, new)
        r2["reviews"]["plan"] = {"decision": "APPROVE", "by": plan["by"], "ts": plan["ts"], "note": f"inherited from {res['generation_id']}"}
        write_result(out, new, r2)
    return new


# ---------- animate ----------
def check_animate(out: Path, gid: int, scope: str, index: int | None) -> dict:
    res = read_result(out, gid)
    if not res["source"]["has_video"]:
        raise PipelineError("No animation prepared for this variation.", 409)
    if STAGES.index(res["stage"]) < SLICED:
        raise PipelineError("Stills are not ready yet.", 409)
    if scope not in ("pack", "slice"):
        raise PipelineError("scope must be 'pack' or 'slice'")
    if scope == "slice":
        n = len(res["stickers"])
        if not index or not 1 <= index <= n:
            raise PipelineError(f"index 1..{n} required for scope 'slice'")
        if res["stickers"][index - 1]["status"] != "READY":
            raise PipelineError(f"Slice {index} is not a READY still.", 409)
    return res


def animate_cells(res: dict, cfg: EngineConfig, cells: list[int], on_cell=None, cache: AnimCache | None = None) -> list[AnimationResult]:
    """Animate these cells of a generation from its prepared sources (pre-sliced clips where there are any, else the 3x3 mp4).
    Nothing is saved here; `cache` (out/cache/anim) lets the same source cell come back without being rendered again."""
    clips = {int(k): {f: Path(p) for f, p in v.items()} for k, v in res["source"].get("clips", {}).items()}
    mp4 = Path(res["source"]["video_path"]) if res["source"].get("video_path") else None
    use_clips = [i for i in cells if i in clips]
    use_mp4 = [i for i in cells if i not in clips and mp4]
    missing = [i for i in cells if i not in use_clips and i not in use_mp4]
    results = []
    for i in missing:
        results.append(AnimationResult(i, "FAILED", "no_video_source"))
        on_cell and on_cell(results[-1])
    if use_clips:
        results += process_clips({i: clips[i] for i in use_clips}, cfg, on_cell=on_cell, cache=cache)
    if use_mp4:
        g = res["source"].get("grid")
        results += process_video(mp4, cfg, use_mp4, on_cell=on_cell, rects=g["rects"] if g else None,
                                 sheet_wh=tuple(res["source"]["sheet_size"]) if g else None, cache=cache)
    return results


def run_animate(out: Path, gid: int, cfg: EngineConfig, scope: str, index: int | None = None, pace: float = 0.0) -> dict:
    res = check_animate(out, gid, scope, index)
    cfg = cfg_for(res, cfg)
    d = gen_dir(out, gid)
    wanted = [index] if scope == "slice" else [s["index"] for s in res["stickers"] if s["status"] == "READY" and s["review"]["still"] != "REJECTED"]
    todo = [i for i in wanted if res["stickers"][i - 1]["anim_status"] != "READY"]
    emit(out, gid, "video_requested", "done", 0, {"scope": scope if scope == "pack" else f"slice S{index}", "cells": todo})
    if not todo:
        return {"noop": True, "message": "Already animated."}
    clips = {int(k): {f: Path(p) for f, p in v.items()} for k, v in res["source"].get("clips", {}).items()}
    mp4 = Path(res["source"]["video_path"]) if res["source"].get("video_path") else None
    use_clips = [i for i in todo if i in clips]
    use_mp4 = [i for i in todo if i not in clips and mp4]
    missing = [i for i in todo if i not in use_clips and i not in use_mp4]
    try:
        with Stage(out, gid, "video_picked", pace) as s:
            info = {"mode": "pre-sliced clips" if use_clips and not use_mp4 else "3x3 mp4" if use_mp4 and not use_clips else "mixed",
                    "clips": len(use_clips), "from_mp4": len(use_mp4), "missing": missing}
            if use_clips:
                info["clip_format"] = next(iter(pick_clip(clips[use_clips[0]], cfg)))
            if use_mp4:
                from .engine import ffmpeg as ff
                pi = ff.probe(mp4)
                info.update(file=mp4.name, size=f"{pi['width']}x{pi['height']}", fps=pi["fps"], duration=round(pi["duration"], 2), codec=pi["codec"])
            s.result = info
            res["source"]["video_info"] = info
            res["stage"] = "video_picked"; write_result(out, gid, res)
        with Stage(out, gid, "video_sliced", pace) as s:
            def on_cell(r):
                st = res["stickers"][r.index - 1]
                record_anim(d, st, r, "prepared video")
                write_result(out, gid, res)
                emit(out, gid, "video_cell", "done", 0, {"index": r.index, "status": r.status, "reason": r.reason})
            for i in todo:
                res["stickers"][i - 1]["anim_status"] = "PROCESSING"
            write_result(out, gid, res)
            results = animate_cells(res, cfg, todo, on_cell, AnimCache(out / "cache" / "anim"))
            s.result = {"ready": sum(r.status == "READY" for r in results), "failed": sum(r.status != "READY" for r in results)}
            res["stage"] = "video_sliced"; write_result(out, gid, res)
    except Exception as e:
        res["error"] = str(e)[:300]
        for i in todo:       # cells the job never reached go back to "not requested", else the UI shows "Animating…" forever
            if res["stickers"][i - 1]["anim_status"] == "PROCESSING":
                res["stickers"][i - 1]["anim_status"] = "NOT_REQUESTED"
        write_result(out, gid, res)
    return {"noop": False}


def state(out: Path, gid: int) -> dict:
    res = read_result(out, gid)
    from . import gates
    res["events"] = read_events(out, gid)
    res["stages"] = STAGES
    res["gate"] = gates.gate_info(res)
    res["final"] = gates.final_indices(res)
    return res


def history(out: Path, offset: int = 0, limit: int = 5) -> dict:
    """Every batch ever made, the most recently EDITED first (any change to a batch counts: a new stroke, an animation, a decision), a page at a time:
    title, times, counts and up to four thumbnails."""
    stamped = []
    for gid in list_ids(out):
        try:
            stamped.append(((gen_dir(out, gid) / "result.json").stat().st_mtime, gid))
        except OSError:
            continue
    stamped.sort(reverse=True)
    ids = [g for _, g in stamped]
    offset, limit = max(0, int(offset)), max(1, min(int(limit), 50))
    edited = dict((g, t) for t, g in stamped)
    items = []
    for gid in ids[offset:offset + limit]:
        try:
            r = read_result(out, gid)
        except Exception:
            continue
        d = gen_dir(out, gid)
        ready = [s for s in r["stickers"] if s.get("status") == "READY" and s.get("png")]
        try:
            created = r.get("created") or round((d / "prompts.json").stat().st_mtime, 3)
        except OSError:
            created = None
        items.append({"id": gid, "generation_id": r["generation_id"], "prompt": r.get("prompt") or r["source"].get("subject", ""), "created": created,
                      "edited": round(edited[gid], 3), "stage": r["stage"], "error": r.get("error"), "ready": len(ready),
                      "animated": sum(1 for s in ready if s.get("anim_status") == "READY"),
                      "thumbs": [f"{s['png']}?e={s.get('rendered_at') or s.get('edited_at') or 0}" for s in ready[:4]],
                      "outline_px": r.get("outline_px")})
    return {"items": items, "more": offset + limit < len(ids), "total": len(ids)}


def summary(out: Path) -> list[dict]:
    rows = []
    for gid in reversed(list_ids(out)):
        try:
            r = read_result(out, gid)
        except Exception:
            continue
        s = r["source"]
        rows.append({"id": gid, "generation_id": r["generation_id"], "owner": r.get("owner", "local"), "prompt": r["prompt"], "stage": r["stage"],
                     "subject": s["subject"], "variant": s["variant"], "error": r["error"],
                     "folder": f"img-{s.get('subject_id')}-{s['subject']}" if s.get("subject_id") else None})
    return rows
