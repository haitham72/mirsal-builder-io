"""The Inbox backend (checkpoint 1G): Haitham's manual loop until Phase 3 automates generation.

  Prepare -> the plan (template + slot JSON) and its final prompt, copyable for Higgsfield
  Reserve -> the next folder names (img-NNN-<subject>, vid-NNN-<subject>) and out/tasks/<NNN>.json (this is the Phase 2 `tasks` row, as JSON)
  Watch   -> every watch folder with its state; misnamed folders are flagged with the nearest valid name
  Run     -> a generation linked to its task, so the prompt that was used is stored with the result

The app NEVER writes inside the watch folders (Phase_01/Images_gen, videos_gen): Haitham creates the folder with the shown name."""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from . import prompter, sources

PROVIDER = "higgsfield-manual"
GRID_NAMES = {"3x3": (3, 3), "2x2": (2, 2), "1x1": (1, 1)}
LOOSE = re.compile(r"^(img|vid)[-_ ]*(\d+)[-_ ]*(.*)$", re.I)


def tasks_dir(out: Path) -> Path:
    return Path(out) / "tasks"


def _write(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


def read_task(out: Path, number: str) -> dict:
    f = tasks_dir(out) / f"{int(number):03d}.json"
    if not f.is_file():
        raise sources_error(f"No task {number}", 404)
    return json.loads(f.read_text(encoding="utf-8"))


def sources_error(msg: str, code: int = 400):
    from .pipeline import PipelineError
    return PipelineError(msg, code)


def list_tasks(out: Path) -> list[dict]:
    d = tasks_dir(out)
    rows = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(d.glob("*.json"))] if d.is_dir() else []
    return list(reversed(rows))


def watch_dirs(inp: Path) -> list[tuple[str, Path]]:
    """Every sub-folder of the two watch folders, as (kind dir, path). Names only; nothing is opened."""
    out = []
    for kind, sub in (("img", "Images_gen"), ("vid", "videos_gen")):
        base = Path(inp) / sub
        if base.is_dir():
            out += [(kind, d) for d in sorted(base.iterdir()) if d.is_dir()]
    return out


def next_number(out: Path, inp: Path) -> int:
    """One number for the whole project: the highest NNN used by any watch folder or task, plus one."""
    nums = [int(m[2]) for _, d in watch_dirs(inp) if (m := sources.DIR_RE.match(d.name))]
    nums += [t["number"] for t in list_tasks(out)]
    return max(nums, default=0) + 1


def nearest_valid(name: str, kind: str, number: int) -> str:
    """img-5-Teddy Bear -> img-005-teddy_bear ; 'Teddy Bear' -> img-<next>-teddy_bear (kind = the folder it sits in)."""
    m = LOOSE.match(name.strip())
    if m:
        kind, num, rest = m[1].lower(), int(m[2]), m[3]
    else:
        num, rest = number, name
    return f"{kind}-{num:03d}-{prompter.slug(rest) or 'subject'}"


def preview(prompt: str, grid: str | list | tuple = "3x3", style_id: str = "flat_vector") -> dict:
    """The plan for a typed task, for the Inbox to show before anything is reserved: template, slot JSON, final prompts."""
    g = GRID_NAMES.get(grid) if isinstance(grid, str) else tuple(grid)
    if g not in prompter.GRIDS:
        raise sources_error("grid must be 3x3, 2x2 or 1x1")
    if not str(prompt).strip():
        raise sources_error("describe the subject first")
    if style_id not in prompter.STYLES:
        raise sources_error(f"unknown style '{style_id}'")
    plan = prompter.expand(str(prompt).strip(), g)
    plan["slots"]["style_id"] = style_id
    built = prompter.render_plan(plan["slots"], plan["template_id"], plan["template_version"])
    plan["sheet_prompt"], plan["video_prompt"] = built["sheet_prompt"], built["video_prompt"]
    for s in plan["stickers"]:
        s["prompt"] = built["prompts"][s["index"]]
    return plan


def subject_of(plan: dict) -> str:
    """The folder subject: the plan's subject words as snake_case (teddy yellow bear for school -> teddy_bear)."""
    return prompter.slug(" ".join(w for w in plan["subject"].split() if w not in prompter.COLORS | prompter.STOP)) or "sticker"


def reserve(out: Path, inp: Path, prompt: str, grid="3x3", style_id: str = "flat_vector") -> dict:
    """Save the task: this IS the G1 approval of the plan (recorded on the task and copied onto every generation run from it)."""
    plan = preview(prompt, grid, style_id)
    n = next_number(out, inp)
    subj = subject_of(plan)
    img, vid = f"img-{n:03d}-{subj}", f"vid-{n:03d}-{subj}"
    now = round(time.time(), 3)
    task = {"id": f"{n:03d}", "number": n, "provider": PROVIDER, "external_task_id": img, "name_key": plan["task_slug"], "status": "reserved",
            "created": now, "prompt": str(prompt).strip(), "grid": plan["grid"], "style_id": style_id,
            "folders": {"img": img, "vid": vid},
            "paths": {"img": str(Path(inp) / "Images_gen" / img), "vid": str(Path(inp) / "videos_gen" / vid)},
            "request": {"template_id": plan["template_id"], "template_version": plan["template_version"], "slots": plan["slots"], "grid": plan["grid"]},
            "plan": plan, "plan_review": {"decision": "APPROVE", "by": "human", "ts": now, "note": "approved when the task was reserved"}, "generations": []}
    _write(tasks_dir(out) / f"{n:03d}.json", task)
    return task


def link_generation(out: Path, number: str, gid: int) -> None:
    t = read_task(out, number)
    t.setdefault("generations", []).append(f"G{gid:03d}")
    t["status"] = "running"
    _write(tasks_dir(out) / f"{int(number):03d}.json", t)


def _files(folder: Path, exts) -> list[str]:
    return sorted(f.name for f in folder.iterdir() if f.is_file() and f.suffix.lower() in exts) if folder.is_dir() else []


def inbox(out: Path, inp: Path) -> dict:
    """Every watch folder with its state (names and sizes only). Tasks first, then folders made outside the app."""
    inp = Path(inp)
    img_root, vid_root = inp / "Images_gen", inp / "videos_gen"
    picks = sources.scan(inp)
    by_id: dict = {}
    for subject, ps in picks.items():
        for p in ps:
            by_id.setdefault((subject, p.subject_id), []).append(p)
    nxt = next_number(out, inp)
    from .pipeline import generations_by_folder
    made = generations_by_folder(out)
    tasks = {t["id"]: t for t in list_tasks(out)}
    rows, seen = [], set()
    img_names = {d.name for k, d in watch_dirs(inp) if k == "img"}
    for t in sorted(tasks.values(), key=lambda t: -t["number"]):
        img, vid = t["folders"]["img"], t["folders"]["vid"]
        subj = img.split("-", 2)[2]
        seen |= {img, vid}
        ifiles, vfiles = _files(img_root / img, sources.IMG_EXT), _files(vid_root / vid, sources.VID_EXT)
        ps = by_id.get((subj, t["id"]), [])
        states = ["reserved, waiting for file"] if not ifiles else ["sheet arrived"]
        has_video = bool(vfiles) or any(p.has_video for p in ps)
        if ifiles:
            states.append("video arrived" if has_video else "no video yet")
        for p in ps:
            if p.clips_dup_of:
                states.append(f"clips: copies of {p.clips_dup_of} (ignored)")
                break
        rows.append({"kind": "task", "task": t["id"], "name": img, "vid_name": vid, "subject": subj, "prompt": t["prompt"], "grid": t["plan"]["grid"],
                     "states": states, "state": " · ".join(states),
                     "sheets": ifiles, "videos": vfiles, "paths": t["paths"], "generations": sorted(set(t.get("generations", [])) | set(made.get((subj, t["id"]), []))), "has_video": has_video,
                     "can_run": bool(ifiles), "problems": [], "ts": t["created"]})
    for kind, d in watch_dirs(inp):
        if d.name in seen:
            continue
        m = sources.DIR_RE.match(d.name)
        if m and m[1] == "vid" and kind == "vid" and any(n.startswith(f"img-{m[2]}-") for n in img_names):
            continue          # its video is already shown on the image folder's row
        if m and m[1] == kind:
            files = _files(d, sources.IMG_EXT if kind == "img" else sources.VID_EXT)
            ps = by_id.get((m[3], m[2]), [])
            has_video = any(p.has_video for p in ps) or (kind == "vid" and bool(files))
            states = ["sheet arrived" if kind == "img" and files else "video arrived" if files else "empty folder"]
            if kind == "img" and files:
                states.append("video arrived" if has_video else "no video yet")
                states.append("no matching task (made outside the app; prompts come from the stub or a <sheet>.json)")
            if any(p.clips_dup_of for p in ps):
                states.append(f"clips: copies of {next(p.clips_dup_of for p in ps if p.clips_dup_of)} (ignored)")
            vi = next((i + 1 for i, p in enumerate(picks.get(m[3], [])) if p.subject_id == m[2]), None)
            rows.append({"kind": "folder", "task": None, "name": d.name, "subject": m[3], "variant": vi, "prompt": m[3].replace("_", " "), "states": states, "state": " · ".join(x for x in states if not x.startswith("no matching") and "ignored" not in x), "sheets": files if kind == "img" else [],
                         "videos": files if kind == "vid" else [], "can_run": kind == "img" and bool(files), "problems": [], "paths": {kind: str(d)},
                         "generations": made.get((m[3], m[2]), []) if kind == "img" else [], "has_video": has_video, "ts": d.stat().st_mtime})
        else:
            fix = nearest_valid(d.name, kind, nxt)
            why = (f"is a {m[1]}- folder inside {'Images_gen' if kind == 'img' else 'videos_gen'}" if m else "does not match img-NNN-<subject> / vid-NNN-<subject>")
            rows.append({"kind": "invalid", "task": None, "name": d.name, "subject": None, "states": ["name invalid"], "state": "name invalid",
                         "sheets": [], "videos": [], "can_run": False, "paths": {kind: str(d)}, "generations": [], "ts": d.stat().st_mtime,
                         "problems": [{"what": why, "expected": "img-NNN-<subject> in Images_gen, vid-NNN-<subject> in videos_gen (NNN = 3 digits, subject = lowercase_snake)",
                                       "nearest": fix}]})
    return {"next_number": nxt, "paths": {"images": str(img_root), "videos": str(vid_root)}, "rows": rows,
            "subjects": sorted(picks), "grids": list(GRID_NAMES), "styles": list(prompter.STYLES)}


def pick_for_task(inp: Path, task: dict, take: int = 0):
    """The prepared sheet that belongs to a reserved task: its own folder, by folder number (never by filename guessing)."""
    img = task["folders"]["img"]
    subj, nnn = img.split("-", 2)[2], task["id"]
    ps = [p for p in sources.scan(inp).get(subj, []) if p.subject_id == nnn]
    if not ps:
        raise sources_error(f"The sheet has not arrived yet: put it in {task['paths']['img']}", 409)
    return ps[min(max(take, 0), len(ps) - 1)]
