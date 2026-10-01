"""Properly named folders per live batch, for copy and paste: out/export/images/img-NNN-<subject>/ and out/export/videos/vid-NNN-<subject>/ (the same pairing the
watch folders use). Files carry everything that makes them what they are, so nothing needs opening to tell two versions apart:

    images/img-004-batman_lego/
        img-004-batman_lego-sheet-nano_banana_flash-2k-20261001.png               the generated sheet (model, size, date)
        img-004-batman_lego-s1-ready_to_fight-stroke12px-trim0px-20261001.png     a finished sticker: sheet position, action, stroke, trim, date
        prompts.txt                                                               prompts, models, credits and Higgsfield ids
    videos/vid-004-batman_lego/
        vid-004-batman_lego-video-kling3_0-pro-3s-20261001.mp4                    the returned video (model, quality, seconds, date)
        vid-004-batman_lego-videosheet-gap26-20261001.png                         the sheet that was sent (the gap in %)
        vid-004-batman_lego-s1-ready_to_fight-stroke12px-trim0px-20261001.webm    an animation, same naming as its sticker

Every stroke/trim setting is its own snapshot: a new setting makes new files, an old one is never deleted or overwritten. `sN` keeps the files in sheet order and ties them to
S1..S9 in the Studio. The engine's own names (out/G00N/slices/<media>-<NNN>-<task_slug>-<key>.<ext>) stay as they are: the database and the pack use them.
The files stay where the engine keeps them; this is a mirror that `sync` brings up to date after every step. Only batches made from a live job are mirrored: prepared sheets
already live in the watch folders, which are never written to (a returned Kling video is laid out for the normalised video sheet, so pairing it with the raw sheet there would be wrong)."""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from . import jobs
from . import pipeline as pl


def folder_name(res: dict) -> str | None:
    s = res.get("source") or {}
    return f"img-{s['subject_id']}-{s['subject']}" if s.get("subject_id") and s.get("subject") else None


def is_live(out: Path, res: dict) -> bool:
    """A live batch's sheet came from out/jobs/J###/result.* (a prepared one from a watch folder). Judged by the path's shape, so a moved or copied out/ still works."""
    sp = (res.get("source") or {}).get("sheet_path")
    return bool(sp) and Path(sp).parent.parent.name == "jobs"


def export_root(out: Path) -> Path:
    """<repo>/generated for the project's own data folder (so the files are visible in the repo, next to Phase_01 and mirsal/), out/export for any other data
    folder (a copy, a test), or the folder named by MIRSAL_EXPORT_DIR. Never a watch folder."""
    env = os.environ.get("MIRSAL_EXPORT_DIR")
    if env:
        return Path(env)
    from .paths import PROJECT, REPO
    return REPO / "generated" if Path(out).resolve() == (PROJECT / "out").resolve() else Path(out) / "export"


def package_dirs(out: Path, res: dict) -> tuple[Path, Path] | None:
    name = folder_name(res)
    if not name or not is_live(out, res):
        return None
    root = export_root(out)
    return root / "images" / name, root / "videos" / ("vid-" + name[4:])


def package_dir(out: Path, res: dict) -> Path | None:
    p = package_dirs(out, res)
    return p[0] if p else None


def _day(f: Path) -> str:
    return time.strftime("%Y%m%d", time.localtime(f.stat().st_mtime))


def _action(key: str, subject: str) -> str:
    return key[len(subject) + 1:] if key.startswith(subject + "_") else key


def _copy(src: Path, dest: Path) -> None:
    if not src.is_file():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size == src.stat().st_size and dest.stat().st_mtime >= src.stat().st_mtime:
        return
    shutil.copy2(src, dest)


def sync(out: Path, gid: int) -> Path | None:
    """Bring the batch's folders up to date (add and refresh, never delete). Returns the images folder, or None for a batch that is not from a live job."""
    out = Path(out)
    res = pl.read_result(out, gid)
    dirs = package_dirs(out, res)
    if not dirs:
        return None
    imgs, vids = dirs
    d = pl.gen_dir(out, gid)
    src, nnn, subject = res["source"], res["source"]["subject_id"], res["source"]["subject"]
    img, vid = f"img-{nnn}-{subject}", f"vid-{nnn}-{subject}"
    sjob = next((j for j in jobs.list(out) if j["kind"] == "sheet" and j.get("generation") == res["generation_id"] and j["status"] == "DONE"), None)
    own = src.get("sheet_copy")
    sheet = d / own if own and (d / own).is_file() else Path(src["sheet_path"])
    if sheet.is_file():
        p = (sjob or {}).get("params") or {}
        parts = [(sjob or {}).get("model") or "sheet", p.get("resolution") or p.get("quality") or ""]
        _copy(sheet, imgs / ("-".join([img, "sheet"] + [x for x in parts if x] + [_day(sheet)]) + sheet.suffix.lower()))
    o, e = res.get("outline_px") or 0, res.get("erode_px") or 0
    for st in res["stickers"]:
        if st.get("status") != "READY" or (st.get("review") or {}).get("still") == "REJECTED":
            continue
        act = _action(st["key"], subject)
        base = f"-s{st['index']}-{act}-stroke{(st.get('metrics') or {}).get('outline_px', o)}px-trim{(st.get('metrics') or {}).get('erode_px', e)}px"
        if st.get("png") and (d / st["png"]).is_file():
            f = d / st["png"]
            _copy(f, imgs / f"{img}{base}-{_day(f)}.png")
        if st.get("webm") and st.get("anim_status") == "READY" and (d / st["webm"]).is_file():
            f = d / st["webm"]
            _copy(f, vids / f"{vid}-s{st['index']}-{act}-stroke{o}px-trim{e}px-{_day(f)}.webm")
    vjobs = [j for j in jobs.list(out) if j["kind"] == "video" and j.get("generation") == res["generation_id"] and j["status"] == "DONE"]
    for v in res.get("video_sheets", []):
        if v.get("status") == "REJECTED":
            continue
        sf = d / v["file"]
        if sf.is_file():
            _copy(sf, vids / f"{vid}-videosheet-gap{round((1 - float(v.get('slot_fill') or 0.74)) * 100)}-{_day(sf)}.png")
        if v.get("video") and (d / v["video"]).is_file():
            mf = d / v["video"]
            vj = next((j for j in vjobs if (j.get("request") or {}).get("sheet") == v["id"]), None) or (vjobs[-1] if vjobs else None)
            p = (vj or {}).get("params") or {}
            parts = [(vj or {}).get("model") or "video", p.get("mode") or p.get("resolution") or "", f"{p['duration']}s" if p.get("duration") else ""]
            _copy(mf, vids / ("-".join([vid, "video"] + [x for x in parts if x] + [_day(mf)]) + mf.suffix.lower()))
    lines = [f"{res['generation_id']}  {res.get('prompt', '')}", ""]
    if res.get("key_colour") == "blue":          # noted only when it is blue (green is the default)
        asked = (res.get("slots") or {}).get("key_colour", "green")
        lines += ["KEY: blue" + ("" if asked == "blue" else f" (the sheet came back blue although {asked} was asked; keyed as blue)"), ""]
    try:
        plan = json.loads((d / "prompts.json").read_text(encoding="utf-8"))
        lines += ["SHEET PROMPT", plan.get("sheet_prompt", ""), ""]
    except (OSError, ValueError):
        pass
    if sjob:
        lines += [f"SHEET: {sjob.get('model')}  {json.dumps(sjob.get('params') or {})}  credits {sjob.get('cost')}  Higgsfield {sjob.get('external_task_id')}", ""]
    for j in vjobs:
        lines += [f"VIDEO ({j['id']}): {j.get('model')}  {json.dumps(j.get('params') or {})}  credits {j.get('cost')}  Higgsfield {j.get('external_task_id')}",
                  "VIDEO PROMPT", (j.get("request") or {}).get("prompt", ""), ""]
    imgs.mkdir(parents=True, exist_ok=True)
    (imgs / "prompts.txt").write_text("\n".join(lines), encoding="utf-8")
    return imgs


def sync_all(out: Path) -> int:
    """Mirror every live batch (at server start, so batches made before the mirror existed get their folders too). Never raises."""
    n = 0
    try:
        for gid in pl.list_ids(out):
            try:
                n += 1 if sync(out, gid) else 0
            except Exception:
                continue
    except Exception:
        pass
    return n


def sync_recent(out: Path, limit: int = 4) -> None:
    """After a step: refresh the folders of the newest batches. Never raises (a mirror must not break a generation)."""
    try:
        for gid in reversed(pl.list_ids(out)[-limit:]):
            try:
                sync(out, gid)
            except Exception:
                continue
    except Exception:
        pass
