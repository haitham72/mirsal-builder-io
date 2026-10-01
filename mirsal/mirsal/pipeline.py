"""Generation lifecycle: 7 stages, each a real step with an event line in out/G00N/events.jsonl.

requested -> sheet_picked -> keyed -> sliced -> video_requested -> video_picked -> video_sliced
Used by the CLI and by the console. Picking steps are lookups over prepared files; the rest is real processing."""
from __future__ import annotations

import json
import os
import re
import shutil
import time
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np

from . import prompter, sources
from .engine.config import EngineConfig
from .engine.grid import detect_grid, split_grid
from .engine.sheet import key_sheet, slice_cells, stitch_keyed
from .engine.video import AnimationResult, pick_clip, process_clips, process_video

STAGES = ["requested", "sheet_picked", "keyed", "sliced", "video_requested", "video_picked", "video_sliced"]


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


def _atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def read_result(out: Path, gid: int) -> dict:
    p = gen_dir(out, gid) / "result.json"
    if not p.exists():
        raise PipelineError(f"No generation G{gid:03d}", 404)
    return json.loads(p.read_text(encoding="utf-8"))


def write_result(out: Path, gid: int, res: dict) -> None:
    _atomic_write(gen_dir(out, gid) / "result.json", json.dumps(res, indent=2, ensure_ascii=False).encode())


def read_events(out: Path, gid: int) -> list[dict]:
    p = gen_dir(out, gid) / "events.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def emit(out: Path, gid: int, stage: str, status: str, ms: int = 0, detail=None) -> None:
    line = json.dumps({"ts": round(time.time(), 3), "stage": stage, "status": status, "ms": ms, "detail": detail},
                      ensure_ascii=False)
    with open(gen_dir(out, gid) / "events.jsonl", "a", encoding="utf-8") as f:
        f.write(line + "\n")


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


def list_inputs(inp: Path) -> list[dict]:
    return [{"subject": subj, "variants": [
        {"variant": p.variant, "folder": p.subject_id, "sheet": p.sheet.name, "video": p.video.name if p.video else None,
         "clips": len(p.clips), "clips_dup_of": p.clips_dup_of, "pairing": p.pairing, "plan": p.plan.name if p.plan else None} for p in picks]}
        for subj, picks in sources.scan(inp).items()]


def start(prompt: str, out: Path, inp: Path, variant: int | None = None, pick: sources.Pick | None = None, parent: int | None = None,
          grid: tuple | None = None) -> int:
    """Synchronous part: match source, run the prompter, allocate G00N. Returns the id fast.
    grid: the user's choice (3x3 / 2x2). A prepared sheet's own layout wins: it is measured from its gutters."""
    if pick is None:
        base = sources.find(inp, prompt, 1)
        if base:
            picks = sources.scan(inp)[base.subject]
            pick = picks[(variant or next_variant(out, base.subject, len(picks))) - 1] if (variant or len(picks) > 1) else base
    if not pick:
        raise PipelineError(f"No prepared set for that. Try: {', '.join(sources.known_subjects(inp)) or '(none found)'}", 404)
    if pick.plan:   # hand-written prompts that match the sheet Haitham actually generated
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
        "generation_id": f"G{gid:03d}", "number": gid, "parent": parent, "prompt": prompt, "task": plan["task"], "task_slug": plan["task_slug"],
        "source": {"subject": pick.subject, "subject_id": pick.subject_id, "variant": pick.variant,
                   "n_variants": pick.n_variants, "sheet": pick.sheet.name, "video": pick.video.name if pick.video else None,
                   "has_video": pick.has_video, "pairing": pick.pairing, "clips_dup_of": pick.clips_dup_of,
                   "clips": {str(n): {f: str(p) for f, p in d.items()} for n, d in pick.clips.items()}, "sheet_path": str(pick.sheet),
                   "video_path": str(pick.video) if pick.video else None},
        "grid": plan["grid"], "stage": "requested", "error": None, "plan_source": pick.plan.name if pick.plan else "stub (prompter.py)",
        "sheet_prompt": plan.get("sheet_prompt", ""), "video_prompt": plan.get("video_prompt", ""),
        "stickers": [{"index": s["index"], "key": s["key"], "emoji": s["emoji"], "prompt": s["prompt"],
                      "name": media_name("img", gid, plan["task_slug"], s["key"]),
                      "status": "PENDING", "reason": None, "report": [], "metrics": {}, "png": None,
                      "anim_status": "NOT_REQUESTED", "anim_reason": None, "anim_metrics": {}, "webm": None}
                     for s in plan["stickers"]],
    }
    write_result(out, gid, res)
    emit(out, gid, "requested", "done", 0, {"prompt": prompt, "task_slug": plan["task_slug"]})
    return gid


def run_stills(out: Path, gid: int, cfg: EngineConfig, pace: float = 0.0) -> None:
    res = read_result(out, gid)
    d = gen_dir(out, gid)
    try:
        with Stage(out, gid, "sheet_picked", pace) as s:
            src = Path(res["source"]["sheet_path"])
            dest = d / "source" / f"sheet{src.suffix.lower()}"
            shutil.copyfile(src, dest)
            res["source"]["sheet_copy"] = f"source/{dest.name}"
            sheet = load_rgb(dest)
            res["source"]["sheet_size"] = [int(sheet.shape[1]), int(sheet.shape[0])]
            s.result = {"subject": res["source"]["subject"], "variant": res["source"]["variant"],
                        "of": res["source"]["n_variants"], "file": src.name}
            res["stage"] = "sheet_picked"; write_result(out, gid, res)
        with Stage(out, gid, "keyed", pace) as s:
            rows, cols = res.get("grid") or (3, 3)
            rects, ginfo = split_grid(sheet, rows, cols, cfg.chroma, cfg.border_px)
            res["source"]["grid"] = {"rows": rows, "cols": cols, "rects": [list(r) for r in rects], **ginfo}
            cells = key_sheet(sheet, cfg, rects)
            ok, buf = cv2.imencode(".png", cv2.cvtColor(stitch_keyed(cells, sheet.shape), cv2.COLOR_RGBA2BGRA))
            (d / "source" / "keyed.png").write_bytes(buf.tobytes())
            res["source"]["keyed"] = "source/keyed.png"
            s.result = {"bg": cells[0].keyed.bg, "threshold": [round(c.keyed.t, 1) for c in cells],
                        "grid": f"{rows}x{cols}", "cut": ginfo["method"], "xs": ginfo["xs"], "ys": ginfo["ys"]}
            res["stage"] = "keyed"; write_result(out, gid, res)
        with Stage(out, gid, "sliced", pace) as s:
            for st, r in zip(res["stickers"], slice_cells(cells, cfg)):
                st.update(status=r.status, reason=r.reason, report=r.report.checks, metrics=r.metrics)
                if r.data:
                    st["png"] = f"slices/{st['name']}.{r.fmt}"
                    (d / st["png"]).write_bytes(r.data)
            ready = sum(1 for st in res["stickers"] if st["status"] == "READY")
            s.result = {"ready": ready, "failed": len(res["stickers"]) - ready}
            res["stage"] = "sliced"; write_result(out, gid, res)
    except Exception as e:
        res["error"] = str(e)[:300]; write_result(out, gid, res)


# ---------- more ----------
def more(out: Path, inp: Path, from_id: int | None = None) -> int:
    from_id = from_id or latest_id(out)
    res = read_result(out, from_id)
    s = res["source"]
    nxt = sources.variant_of(inp, s["subject"], s["variant"] + 1)
    if not nxt:
        raise PipelineError(f"That's all {s['n_variants']} prepared variations of {s['subject']}.", 409)
    return start(res["prompt"], out, inp, pick=nxt, parent=from_id)


# ---------- animate ----------
def check_animate(out: Path, gid: int, scope: str, index: int | None) -> dict:
    res = read_result(out, gid)
    if not res["source"]["has_video"]:
        raise PipelineError("No animation prepared for this variation.", 409)
    if res["stage"] not in ("sliced", "video_picked", "video_sliced"):
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


def run_animate(out: Path, gid: int, cfg: EngineConfig, scope: str, index: int | None = None, pace: float = 0.0) -> dict:
    res = check_animate(out, gid, scope, index)
    d = gen_dir(out, gid)
    wanted = [index] if scope == "slice" else [s["index"] for s in res["stickers"] if s["status"] == "READY"]
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
                st.update(anim_status=r.status, anim_reason=r.reason, anim_metrics=r.metrics)
                if r.data:
                    st["webm"] = f"slices/{st['name'].replace('img-', 'vid-', 1)}.webm"
                    (d / st["webm"]).write_bytes(r.data)
                write_result(out, gid, res)
                emit(out, gid, "video_cell", "done", 0, {"index": r.index, "status": r.status, "reason": r.reason})
            for i in todo:
                res["stickers"][i - 1]["anim_status"] = "PROCESSING"
            write_result(out, gid, res)
            results = []
            for i in missing:
                results.append(AnimationResult(i, "FAILED", "no_video_source")); on_cell(results[-1])
            if use_clips:
                results += process_clips({i: clips[i] for i in use_clips}, cfg, on_cell=on_cell)
            if use_mp4:
                g = res["source"].get("grid")
                results += process_video(mp4, cfg, use_mp4, on_cell=on_cell, rects=g["rects"] if g else None,
                                         sheet_wh=tuple(res["source"]["sheet_size"]) if g else None)
            s.result = {"ready": sum(r.status == "READY" for r in results), "failed": sum(r.status != "READY" for r in results)}
            res["stage"] = "video_sliced"; write_result(out, gid, res)
    except Exception as e:
        res["error"] = str(e)[:300]; write_result(out, gid, res)
    return {"noop": False}


def state(out: Path, gid: int) -> dict:
    res = read_result(out, gid)
    res["events"] = read_events(out, gid)
    res["stages"] = STAGES
    return res


def summary(out: Path) -> list[dict]:
    rows = []
    for gid in reversed(list_ids(out)):
        try:
            r = read_result(out, gid)
        except Exception:
            continue
        rows.append({"id": gid, "generation_id": r["generation_id"], "prompt": r["prompt"], "stage": r["stage"],
                     "subject": r["source"]["subject"], "variant": r["source"]["variant"], "error": r["error"]})
    return rows
