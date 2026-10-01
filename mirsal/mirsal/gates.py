"""The golden path's review gates (phase_01.md, checkpoint 1F). The rules live here, in Python, and every phase keeps them:

  G1 plan -> sheet -> Python blocks bad cells -> G2 stills -> video sheet (built from the approved stills only) -> G3 video sheet
  -> returned video attached to A<n> -> Python blocks bad slots -> G4 animations -> G5 pack (stickers approved at G2 AND G4)

Python judges what is *correct* and its BLOCK is final: nobody can approve a FAILED sticker. A human (from Phase 3 the VLM
pre-reviews) judges what is *good*. Rejection never deletes. A sticker keeps its original S# through every stage. Every decision is an
event line and a history entry. The UI only displays what is enforced here (a 409 carries the reason)."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from . import pipeline as pl
from . import prompter
from .engine import verify
from .engine.config import EngineConfig
from .engine.video import check_returned_video, process_video
from .engine.video_sheet import build_video_sheet

GATES = ("plan", "still", "video_sheet", "anim", "pack")
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
VIDEO_BLOCKS = ("video_decodes", "video_specs", "layout_match")      # a returned video that fails these is not the video of this sheet
ACTIVE = ("BUILT", "APPROVED", "VIDEO_RETURNED", "VIDEO_BLOCKED", "SLICED")


def refuse(msg: str):
    return pl.PipelineError(msg, 409)


def _stamp(decision: str, by: str, note=None, **extra) -> dict:
    return {"decision": decision, "by": by, "ts": round(time.time(), 3), "note": note, **extra}


def _stage(res: dict, stage: str) -> None:
    res["stage"] = stage


def active_sheet(res: dict):
    """The video sheet the stills decisions are locked to: the latest one that was not rejected."""
    return next((v for v in reversed(res["video_sheets"]) if v["status"] in ACTIVE), None)


def sheet_of(res: dict, aid: str) -> dict:
    v = next((v for v in res["video_sheets"] if v["id"] == aid), None)
    if not v:
        raise pl.PipelineError(f"No video sheet {aid}", 404)
    return v


def final_indices(res: dict) -> list[int]:
    return [s["index"] for s in res["stickers"] if s["review"]["still"] == "APPROVED" and s["review"]["anim"] == "APPROVED"]


def _plan_ok(res: dict) -> None:
    p = res["reviews"].get("plan")
    if not p:
        raise refuse("Approve the plan first (G1).")
    if p["decision"] != "APPROVE":
        raise refuse("The plan was rejected (G1): nothing can move on from it.")


def gate_info(res: dict) -> dict:
    """What the page should ask for next (computed, never stored): the active gate and a one-line instruction."""
    S = res["stickers"]
    if pl.STAGES.index(res["stage"]) < pl.SLICED:
        return {"active": "wait", "message": "The stills are being made."}
    p = res["reviews"].get("plan")
    if not p:
        return {"active": "plan", "message": "G1: approve or reject the plan."}
    if p["decision"] != "APPROVE":
        return {"active": "rejected", "message": "The plan was rejected."}
    pend = [s["index"] for s in S if s["status"] == "READY" and s["review"]["still"] == "PENDING"]
    sheet = active_sheet(res)
    animated = any(s["anim_status"] in ("READY", "FAILED") for s in S)       # animated from the prepared video: no video sheet involved
    if pend and not sheet and not animated:
        return {"active": "still", "message": f"G2: approve or reject the stills ({len(pend)} pending).", "pending": pend}
    if not sheet and not animated:
        return {"active": "video_sheet_build", "message": "Build the video sheet from the approved stills."}
    st = sheet["status"] if sheet else "SLICED"
    if st == "BUILT":
        return {"active": "video_sheet", "message": f"G3: approve or reject video sheet {sheet['id']}.", "sheet": sheet["id"]}
    if st in ("APPROVED", "VIDEO_BLOCKED"):
        return {"active": "video_upload", "message": f"Make the video from {sheet['id']} in your own tool, then upload it.", "sheet": sheet["id"],
                "blocked": sheet.get("block")}
    if st == "VIDEO_RETURNED":
        return {"active": "wait", "message": "Slicing the returned video."}
    apend = [s["index"] for s in S if s["anim_status"] == "READY" and s["review"]["anim"] == "PENDING"]
    if apend:
        return {"active": "anim", "message": f"G4: approve or reject the animations ({len(apend)} pending).", "pending": apend}
    if not res["reviews"].get("pack"):
        return {"active": "pack", "message": "G5: approve the final pack.", "final": final_indices(res)}
    return {"active": "done", "message": "The pack is final.", "final": final_indices(res)}


# ---------- reviews ----------
def review(out: Path, gid: int, gate: str, decision: str, index=None, note=None, by: str = "human") -> dict:
    decision = str(decision).upper()
    if gate not in GATES:
        raise pl.PipelineError(f"gate must be one of {', '.join(GATES)}")
    if decision not in ("APPROVE", "REJECT"):
        raise pl.PipelineError("decision must be APPROVE or REJECT")
    res = pl.read_result(out, gid)
    fn = {"plan": _g_plan, "still": _g_still, "video_sheet": _g_sheet, "anim": _g_anim, "pack": _g_pack}[gate]
    msg = fn(out, gid, res, decision, index, note, by)
    pl.write_result(out, gid, res)
    return {"ok": True, "gate": gate, "decision": decision, **msg, "gate_info": gate_info(res)}


def _g_plan(out, gid, res, decision, index, note, by):
    if any(s["review"]["still"] in ("APPROVED", "REJECTED") for s in res["stickers"]) or active_sheet(res):
        raise refuse("Locked: stills were already reviewed from this plan.")
    res["reviews"]["plan"] = _stamp(decision, by, note)
    if pl.STAGES.index(res["stage"]) >= pl.SLICED:
        _stage(res, "plan_reviewed")
    pl.emit(out, gid, "plan_reviewed", "done", 0, {"gate": "plan", "note": note}, by, decision)
    return {}


def _targets(res: dict, index, decision: str, which: str, ready_field: str, ready_value: str):
    """The stickers a per-sticker gate acts on: one index, or every still-pending READY sticker for index 'ready'."""
    S = res["stickers"]
    if index in ("ready", "all"):
        return [s for s in S if s[ready_field] == ready_value and s["review"][which] == "PENDING"]
    try:
        i = int(index)
    except (TypeError, ValueError):
        raise pl.PipelineError("index must be a sticker number or 'ready'")
    if not 1 <= i <= len(S):
        raise pl.PipelineError(f"index 1..{len(S)} required")
    s = S[i - 1]
    if s[ready_field] != ready_value or s["review"][which] == "BLOCKED":
        why = s["reason"] if which == "still" else s.get("anim_reason")
        raise refuse(f"S{i} is blocked by Python ({why or s[ready_field].lower()}): nobody can approve or reject it.")
    return [s]


def _g_still(out, gid, res, decision, index, note, by):
    _plan_ok(res)
    if pl.STAGES.index(res["stage"]) < pl.SLICED or res.get("error"):
        raise refuse("The stills are not sliced yet.")
    sh = active_sheet(res)
    if sh:
        raise refuse(f"Locked: video sheet {sh['id']} was built from these decisions. Reject {sh['id']} to change them.")
    done = []
    for s in _targets(res, index, decision, "still", "status", "READY"):
        s["review"]["still"] = "APPROVED" if decision == "APPROVE" else "REJECTED"
        pl.hist(s, "still", by, decision, reason=note)
        pl.emit(out, gid, "review", "done", 0, {"gate": "still", "index": s["index"], "note": note}, by, decision)
        done.append(s["index"])
    if not any(s["status"] == "READY" and s["review"]["still"] == "PENDING" for s in res["stickers"]):
        _stage(res, "stills_reviewed")
        pl.emit(out, gid, "stills_reviewed", "done", 0, {"approved": [s["index"] for s in res["stickers"] if s["review"]["still"] == "APPROVED"]}, by, decision)
    return {"indices": done}


def _g_anim(out, gid, res, decision, index, note, by):
    if not any(s["anim_status"] in ("READY", "FAILED") for s in res["stickers"]):
        raise refuse("The video has not been sliced yet.")
    if res["reviews"].get("pack") and res["reviews"]["pack"]["decision"] == "APPROVE":
        raise refuse("Locked: the pack is already final (G5). Reject the pack to change animation decisions.")
    done = []
    for s in _targets(res, index, decision, "anim", "anim_status", "READY"):
        s["review"]["anim"] = "APPROVED" if decision == "APPROVE" else "REJECTED"
        pl.hist(s, "anim", by, decision, reason=note)
        pl.emit(out, gid, "review", "done", 0, {"gate": "anim", "index": s["index"], "note": note}, by, decision)
        done.append(s["index"])
    if not any(s["anim_status"] == "READY" and s["review"]["anim"] == "PENDING" for s in res["stickers"]):
        _stage(res, "anim_reviewed")
        pl.emit(out, gid, "anim_reviewed", "done", 0, {"approved": [s["index"] for s in res["stickers"] if s["review"]["anim"] == "APPROVED"]}, by, decision)
    return {"indices": done}


def _g_sheet(out, gid, res, decision, index, note, by):
    v = sheet_of(res, str(index or ""))
    if v["status"] not in ("BUILT", "APPROVED", "REJECTED"):
        raise refuse(f"Locked: {v['id']} already has a video attached.")
    if decision == "APPROVE" and v.get("blocked"):
        raise refuse(f"{v['id']} is blocked by Python ({v['blocked']}): it cannot be approved.")
    v["status"] = "APPROVED" if decision == "APPROVE" else "REJECTED"
    res["reviews"]["video_sheet"][v["id"]] = _stamp(decision, by, note)
    for slot in v["slots"]:
        pl.hist(res["stickers"][slot - 1], "video_sheet", by, decision, reason=note, ref=v["id"])
    _stage(res, "video_sheet_reviewed")
    pl.emit(out, gid, "video_sheet_reviewed", "done", 0, {"sheet": v["id"], "note": note}, by, decision)
    return {"sheet": v["id"], "status": v["status"]}


def _g_pack(out, gid, res, decision, index, note, by):
    if not any(s["anim_status"] in ("READY", "FAILED") for s in res["stickers"]):
        raise refuse("The video has not been sliced yet.")
    undecided = [s["index"] for s in res["stickers"] if s["anim_status"] == "READY" and s["review"]["anim"] == "PENDING"]
    if decision == "APPROVE":
        if undecided:
            raise refuse(f"Decide the animations first (G4): S{', S'.join(map(str, undecided))} still pending.")
        final = final_indices(res)
        if not final:
            raise refuse("No sticker is approved at both G2 and G4.")
        d = pl.gen_dir(out, gid)
        items = [{"key": res["stickers"][i - 1]["key"], "emoji": res["stickers"][i - 1]["emoji"], "kind": "animated",
                  "bytes": (d / res["stickers"][i - 1]["webm"]).stat().st_size} for i in final]
        chk = verify.run("pack", {"stickers": items}, EngineConfig())[0]
        if not chk.ok:
            raise refuse(f"pack_limits: {chk.note}")
        res["reviews"]["pack"] = _stamp("APPROVE", by, note, stickers=final)
        for i in final:
            pl.hist(res["stickers"][i - 1], "pack", by, "APPROVE", reason=note)
        _stage(res, "pack_final")
        pl.emit(out, gid, "pack_final", "done", 0, {"stickers": final}, by, "APPROVE")
        return {"final": final}
    res["reviews"]["pack"] = _stamp("REJECT", by, note, stickers=[])
    pl.emit(out, gid, "pack_final", "done", 0, {"note": note}, by, "REJECT")
    return {"final": []}


# ---------- G3: the video sheet ----------
def _read_rgba(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("RGBA"))


def build_sheet(out: Path, gid: int, cfg: EngineConfig) -> dict:
    """Build video sheet A<n> from the stills approved at G2: same slot positions, rejected slots blank, no outline, flat key colour."""
    res = pl.read_result(out, gid)
    _plan_ok(res)
    if pl.STAGES.index(res["stage"]) < pl.SLICED or res.get("error"):
        raise refuse("The stills are not sliced yet.")
    if active_sheet(res):
        raise refuse(f"Video sheet {active_sheet(res)['id']} is already built. Reject it to build another.")
    undecided = [s["index"] for s in res["stickers"] if s["status"] == "READY" and s["review"]["still"] == "PENDING"]
    if undecided:
        raise refuse(f"Decide the stills first (G2): S{', S'.join(map(str, undecided))} still pending.")
    approved = [s["index"] for s in res["stickers"] if s["review"]["still"] == "APPROVED"]
    if not approved:
        raise refuse("No still is approved yet (G2): there is nothing to put on a video sheet.")
    d = pl.gen_dir(out, gid)
    rows, cols = res["grid"]
    plain = {i: _read_rgba(d / "source" / "plain" / f"S{i}.png") for i in approved}
    t0 = time.perf_counter()
    sheet, layout = build_video_sheet(plain, approved, cfg, (rows, cols))
    aid = f"A{len(res['video_sheets']) + 1}"
    folder = d / "video_sheet" / aid
    folder.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".png", cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR))
    (folder / "sheet.png").write_bytes(buf.tobytes())
    (folder / "layout.json").write_text(json.dumps(layout, indent=1), encoding="utf-8")
    checks = verify.run("video_sheet", {"sheet": sheet, "layout": layout, "approved": approved}, cfg)
    blocked = next((c for c in checks if not c.ok and c.severity == verify.BLOCK), None)
    entry = {"id": aid, "slots": approved, "grid": [rows, cols], "file": f"video_sheet/{aid}/sheet.png", "layout": f"video_sheet/{aid}/layout.json",
             "video": None, "status": "BUILT", "ts": round(time.time(), 3), "verify": [c.to_dict() for c in checks],
             "blocked": blocked.id if blocked else None, "canvas": layout["canvas"], "video_prompt": res.get("video_prompt", "")}
    res["video_sheets"].append(entry)
    for i in approved:
        pl.hist(res["stickers"][i - 1], "video_sheet", "python", "BLOCK" if blocked else "PASS", blocked.id if blocked else None, aid)
    _stage(res, "video_sheet_built")
    pl.write_result(out, gid, res)
    pl.emit(out, gid, "video_sheet_built", "error" if blocked else "done", int((time.perf_counter() - t0) * 1000),
            {"sheet": aid, "slots": approved, "blocked": blocked.id if blocked else None}, "python", "BLOCK" if blocked else "PASS")
    if blocked:
        raise refuse(f"{aid} was built but Python blocked it ({blocked.id}: {blocked.note}).")
    return {"sheet": aid, "slots": approved, "gate_info": gate_info(res)}


# ---------- 7-8: the returned video ----------
def attach_video(out: Path, gid: int, aid: str, data: bytes, filename: str = "video.mp4") -> dict:
    """Synchronous part: validate the gate order and store the upload next to the sheet it belongs to. Slicing is slice_video()."""
    res = pl.read_result(out, gid)
    v = sheet_of(res, aid)
    if v["status"] not in ("APPROVED", "VIDEO_BLOCKED"):
        raise refuse(f"{aid} is {v['status']}: approve the video sheet (G3) before attaching its video." if v["status"] in ("BUILT", "REJECTED")
                     else f"{aid} already has its video sliced.")
    if not data:
        raise pl.PipelineError("empty upload")
    ext = Path(filename).suffix.lower()
    ext = ext if ext in VIDEO_EXT else ".mp4"
    d = pl.gen_dir(out, gid)
    for old in (d / "video_sheet" / aid).glob("video.*"):
        old.unlink()
    dest = d / "video_sheet" / aid / f"video{ext}"
    dest.write_bytes(data)
    v.update(video=f"video_sheet/{aid}/{dest.name}", video_name=filename, status="VIDEO_RETURNED", block=None, video_flags=[], video_checks=[])
    _stage(res, "video_returned")
    pl.write_result(out, gid, res)
    return {"sheet": aid, "bytes": len(data)}


def slice_video(out: Path, gid: int, aid: str, cfg: EngineConfig, pace: float = 0.0) -> None:
    """Background job: video-stage checks on the returned video, then each approved slot is decoded from the layout's exact
    rectangles, re-keyed on every frame, boundary-checked and encoded. Python's blocks are recorded on the sticker's history."""
    res = pl.read_result(out, gid)
    cfg = pl.cfg_for(res, cfg)
    v = sheet_of(res, aid)
    d = pl.gen_dir(out, gid)
    try:
        layout = json.loads((d / v["layout"]).read_text(encoding="utf-8"))
        sheet = np.array(Image.open(d / v["file"]).convert("RGB"))
        mp4 = d / v["video"]
        with pl.Stage(out, gid, "video_returned", pace) as s:
            info = {}
            checks = check_returned_video(mp4, layout, sheet, cfg, on_probe=lambda i: info.update(i))
            v["video_checks"] = [c.to_dict() for c in checks]
            v["video_info"] = {k: info.get(k) for k in ("codec", "width", "height", "fps", "duration")}
            block = next((c for c in checks if not c.ok and c.id in VIDEO_BLOCKS), None)
            flag = next((c for c in checks if not c.ok and c.id == "blank_slots_stay_empty"), None)
            v["video_flags"] = [flag.id] if flag else []
            s.result = {"sheet": aid, "blocked": block.id if block else None, "flags": v["video_flags"], **v["video_info"]}
            if block:
                v["status"], v["block"] = "VIDEO_BLOCKED", block.id
                for i in v["slots"]:
                    pl.hist(res["stickers"][i - 1], "video", "python", "BLOCK", block.id, aid, {"check": block.id, "value": block.value, "limit": block.limit, "note": block.note})
                _stage(res, "video_returned"); pl.write_result(out, gid, res)
                return
            if flag:   # blocks the generation's video, not the stickers: the approved slots are still sliced
                pl.emit(out, gid, "video_flag", "done", 0, {"sheet": aid, "check": flag.id, "note": flag.note}, "python", "BLOCK")
            _stage(res, "video_returned"); pl.write_result(out, gid, res)
        with pl.Stage(out, gid, "video_sliced", pace) as s:
            refs = {}
            for i in v["slots"]:
                st = res["stickers"][i - 1]
                if st.get("png"):
                    refs[i] = _read_rgba(d / st["png"])[..., 3]
                st["anim_status"], st["anim_reason"] = "PROCESSING", None

            def on_cell(r):
                st = res["stickers"][r.index - 1]
                pl.record_anim(d, st, r, aid)
                pl.write_result(out, gid, res)
                pl.emit(out, gid, "video_cell", "done", 0, {"index": r.index, "status": r.status, "reason": r.reason}, "python", "PASS" if r.status == "READY" else "BLOCK")
            pl.write_result(out, gid, res)
            results = process_video(mp4, cfg, cells=v["slots"], on_cell=on_cell, layout=layout, refs=refs)
            v["status"] = "SLICED"
            s.result = {"ready": sum(r.status == "READY" for r in results), "failed": sum(r.status != "READY" for r in results)}
            _stage(res, "video_sliced"); pl.write_result(out, gid, res)
    except Exception as e:
        res["error"] = str(e)[:300]
        pl.write_result(out, gid, res)


# ---------- the simple flow: one click per step ----------
def _ensure_plan(out: Path, gid: int, note: str) -> dict:
    res = pl.read_result(out, gid)
    if not res["reviews"].get("plan"):
        pl.approve_plan(out, gid, note)
        res = pl.read_result(out, gid)
    _plan_ok(res)
    return res


def _approve_stills(out: Path, gid: int, res: dict, note: str) -> None:
    """The stickers that were not dropped (x) and passed Python are approved at G2; skipped once a video sheet locks the stills."""
    if active_sheet(res) or not any(s["status"] == "READY" and s["review"]["still"] == "PENDING" for s in res["stickers"]):
        return
    review(out, gid, "still", "APPROVE", "ready", note)


def quick_sheet(out: Path, gid: int, cfg: EngineConfig) -> dict:
    """'Make a video': approve the kept stills, build the video sheet and approve it for sending (the download is the decision)."""
    res = _ensure_plan(out, gid, "approved by pressing Make a video")
    _approve_stills(out, gid, res, "approved by Make a video")
    res = pl.read_result(out, gid)
    sheet = active_sheet(res)
    if not sheet:
        build_sheet(out, gid, cfg)
        res = pl.read_result(out, gid)
        sheet = active_sheet(res)
    if sheet["status"] == "BUILT":
        review(out, gid, "video_sheet", "APPROVE", sheet["id"], "approved by Make a video")
    return {"sheet": sheet["id"]}


def quick_add(out: Path, gid: int, lib, pack_id: str | None = None, pack_name: str | None = None) -> dict:
    """'Add to pack': approve what was kept at G2 / G4, approve the final pack (G5) and add it to a Library pack.
    Animated stickers when the video was made, the stills when it was not. Anything already added to that pack is skipped."""
    res = _ensure_plan(out, gid, "approved by pressing Add")
    _approve_stills(out, gid, res, "approved by Add")
    res = pl.read_result(out, gid)
    animated = any(s["anim_status"] == "READY" for s in res["stickers"])
    if animated:
        pack = res["reviews"].get("pack")
        if pack and pack["decision"] == "APPROVE":
            review(out, gid, "pack", "REJECT", note="reopened to add more")
        if any(s["anim_status"] == "READY" and s["review"]["anim"] == "PENDING" for s in pl.read_result(out, gid)["stickers"]):
            review(out, gid, "anim", "APPROVE", "ready", "approved by Add")
        res = pl.read_result(out, gid)
        keep = final_indices(res)
        kind = "animated"
        if not keep:
            raise refuse("Nothing to add: every sticker was dropped or blocked.")
        review(out, gid, "pack", "APPROVE", note="approved by Add")
    else:
        keep = [s["index"] for s in res["stickers"] if s["status"] == "READY" and s["review"]["still"] == "APPROVED"]
        kind = "static"
        if not keep:
            raise refuse("Nothing to add: every sticker was dropped or blocked.")
    pid = pack_id or (lib.create_pack(pack_name or "My stickers")["id"])
    res = pl.read_result(out, gid)
    done = res.setdefault("added", {}).setdefault(pid, [])
    added = []
    for i in keep:
        key = f"{kind}:{i}"
        if key in done:
            continue
        lib.add_from_generation(out, pid, gid, i, kind)
        done.append(key)
        added.append(i)
    pl.write_result(out, gid, res)
    pl.emit(out, gid, "added_to_pack", "done", 0, {"pack": pid, "kind": kind, "stickers": added}, "human", "APPROVE")
    return {"added": len(added), "already": len(keep) - len(added), "kind": kind, "pack_id": pid, "indices": keep}


def drop(out: Path, gid: int, index: int, dropped: bool) -> dict:
    """The x on a tile: drop a sticker from the set (a human reject at the stage it is in), or bring it back. Never deletes."""
    res = pl.read_result(out, gid)
    _plan_ok(res) if res["reviews"].get("plan") else pl.approve_plan(out, gid, "approved by the first decision")
    res = pl.read_result(out, gid)
    animated = any(s["anim_status"] in ("READY", "FAILED") for s in res["stickers"])
    st = res["stickers"][int(index) - 1]
    gate = "anim" if animated and st["anim_status"] == "READY" else "still"
    if gate == "anim" and res["reviews"].get("pack") and res["reviews"]["pack"]["decision"] == "APPROVE":
        review(out, gid, "pack", "REJECT", note="reopened: a sticker was changed")
    review(out, gid, gate, "REJECT" if dropped else "APPROVE", int(index), "dropped from the set" if dropped else "brought back")
    return {"index": int(index), "dropped": dropped, "gate": gate}


# ---------- 1x1 regeneration ----------
def regen_plan(res: dict, index: int) -> dict:
    """The plan of ONE sticker, regenerated as a 1x1 sheet through the same engine."""
    st = res["stickers"][index - 1]
    slots = res.get("slots") or {}
    cell = next((c for c in slots.get("cells", []) if c["pos"] == index), None)
    desc = slots.get("subject_description") or res["task"]
    label = cell["label"] if cell else st["prompt"]
    new = {"subject_description": desc, "style_id": slots.get("style_id", "flat_vector"), "mode": "single_1x1",
           "cells": [{"pos": 1, "label": label, "tags": st["tags"], "emoji": st["emoji"]}], "action_guidance": slots.get("action_guidance", "default"),
           "key_colour": slots.get("key_colour", "green")}
    built = prompter.render_plan(new, "single_1x1", 1)
    return prompter.validate_plan({"task": res["task"], "task_slug": res["task_slug"], "grid": [1, 1], "template_id": "single_1x1", "template_version": 1,
                                   "slots": new, "sheet_prompt": built["sheet_prompt"], "video_prompt": built["video_prompt"],
                                   "stickers": [{"index": 1, "id": "prompt01", "prompt": built["prompts"][1], "key": st["key"], "tags": st["tags"], "emoji": st["emoji"]}]})


# ---------- search ----------
def search(out: Path, q: str, limit: int = 200) -> list[dict]:
    """File search across every generation's stickers: by key, tag, name, emoji, task or prompt words. Phase 2 swaps in Postgres behind the same route."""
    words = [w for w in re.findall(r"[a-z0-9_]+", q.lower()) if w]
    rows = []
    for gid in reversed(pl.list_ids(out)):
        try:
            res = pl.read_result(out, gid)
        except Exception:
            continue
        for s in res["stickers"]:
            hay = " ".join([s["key"], s["name"], res["task_slug"], res.get("name_key") or "", res["prompt"], s["emoji"], *s["tags"]]).lower()
            if all(w in hay for w in words):
                rows.append({"generation": res["generation_id"], "id": gid, "index": s["index"], "key": s["key"], "tags": s["tags"], "name": s["name"],
                             "task_slug": res["task_slug"], "status": s["status"], "reason": s["reason"], "review": s["review"], "anim_status": s["anim_status"],
                             "png": s["png"], "webm": s["webm"], "emoji": s["emoji"], "final": s["index"] in final_indices(res)})
                if len(rows) >= limit:
                    return rows
    return rows
