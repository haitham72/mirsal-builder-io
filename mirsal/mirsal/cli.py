"""python -m mirsal create "<prompt>" | more [G001] | animate [G001] [--slice N] | serve [--port N] [--pace S]"""
from __future__ import annotations

import argparse
import time

from . import pipeline as pl
from .engine.config import EngineConfig
from .paths import input_root, out_root


def _gid(s):
    return int(s.lstrip("Gg")) if s else None


def _show(out, gid, t0):
    r = pl.read_result(out, gid)
    print(f"{r['generation_id']}  {r['task_slug']}  ({r['source']['subject']} variant {r['source']['variant']}/{r['source']['n_variants']})  {time.perf_counter() - t0:.1f}s")
    for s in r["stickers"]:
        v = f"  video:{s['anim_status']}" if s["anim_status"] != "NOT_REQUESTED" else ""
        print(f"  {s['index']} {s['emoji']} {s['name']:<60} {s['status']}{' ' + s['reason'] if s['reason'] else ''}{v}")
    if r["error"]:
        print("ERROR:", r["error"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="mirsal")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create"); c.add_argument("prompt")
    for n in ("more", "another"):
        m = sub.add_parser(n); m.add_argument("gid", nargs="?")
    a = sub.add_parser("animate"); a.add_argument("gid", nargs="?"); a.add_argument("--slice", type=int)
    sub.add_parser("doctor")
    s = sub.add_parser("serve"); s.add_argument("--port", type=int, default=8770); s.add_argument("--pace", type=float, default=0.0)
    args = ap.parse_args(argv)
    out, inp, cfg, t0 = out_root(), input_root(), EngineConfig(), time.perf_counter()
    if args.cmd == "doctor":
        return doctor()
    try:
        if args.cmd == "serve":
            from .console.server import serve
            serve(out, inp, args.port, args.pace, cfg)
            return 0
        if args.cmd == "create":
            gid = pl.start(args.prompt, out, inp); pl.run_stills(out, gid, cfg)
        elif args.cmd in ("more", "another"):
            gid = pl.more(out, inp, _gid(args.gid)); pl.run_stills(out, gid, cfg)
        else:
            gid = _gid(args.gid) or pl.latest_id(out)
            pl.run_animate(out, gid, cfg, "slice" if args.slice else "pack", args.slice)
        _show(out, gid, t0)
        return 0
    except pl.PipelineError as e:
        print(e)
        return 1


def doctor() -> int:
    """Offline-friendly self check: what is installed, what is missing, and how to fix it without internet."""
    import importlib, subprocess
    bad = 0
    for mod, pkg in (("numpy", "numpy"), ("cv2", "opencv-python-headless"), ("PIL", "pillow")):
        try:
            m = importlib.import_module(mod); print(f"OK      {pkg} {getattr(m, '__version__', '')}")
        except ImportError:
            bad += 1; print(f"MISSING {pkg}   (offline: pip install --no-index --find-links wheels {pkg})")
    try:
        from .engine import ffmpeg as ff
        exe = ff.ffmpeg_exe()
        enc = subprocess.run([exe, "-hide_banner", "-encoders"], capture_output=True).stdout.decode()
        print(f"OK      ffmpeg {exe}")
        if "libvpx-vp9" not in enc:
            bad += 1; print("MISSING libvpx-vp9 in any ffmpeg found (needed for WEBM alpha). Fix, easiest first: `pip install imageio-ffmpeg` (its bundled build has it; offline: pip download it on a connected PC), or a full build from gyan.dev and set MIRSAL_FFMPEG=<path to ffmpeg.exe>")
    except Exception as e:
        bad += 1; print("MISSING ffmpeg:", e, "\n        put ffmpeg.exe on PATH, or set MIRSAL_FFMPEG=<path>")
    from . import prompter
    from .engine import verify
    tpl = sorted(f.stem for f in prompter.TEMPLATES.glob("*.txt"))
    print(f"OK      verifier v{verify.VERIFY_VERSION}: {sum(len(v) for v in verify.CATALOGUE.values())} checks over {len(verify.CATALOGUE)} stages; prompt templates: {', '.join(tpl)}")
    from datetime import datetime
    from .console.server import DIST
    page = DIST / "index.html"
    print(f"OK      frontend: dist built {datetime.fromtimestamp(page.stat().st_mtime):%Y-%m-%d %H:%M}" if page.is_file()
          else "NOTE    frontend: legacy console (React app not built: cd web && npm ci && npm run build)")
    from . import sources
    subs = sources.known_subjects(input_root())
    from . import matte
    ms, mf = matte.status(), matte.status(True)
    print(f"OK      AI matte {ms['model']} (photos), {mf['model']} (video)" if ms["ok"] else f"NOTE    AI matte off, photos use GrabCut (optional): {ms['reason']}")
    print(("OK      " if subs else "MISSING ") + f"input {input_root()}  subjects: {', '.join(subs) or 'none'}")
    bad += 0 if subs else 1
    for subject, picks in sources.scan(input_root()).items():
        clips = sum(1 for p in picks if p.clips)
        print(f"        {subject}: {len(picks)} variant(s), {sum(1 for p in picks if p.video)} with a 3x3 video, {clips} with pre-sliced clips")
        for p in picks:
            if p.clips_dup_of:
                print(f"WARN    {subject} {p.subject_id}: pre-sliced clips are copies of {p.clips_dup_of}'s; ignored, its own 3x3 video is used"
                      + ("" if p.video else " (none: no animation)"))
        if any(p.pairing == "order" for p in picks):
            print(f"WARN    {subject}: image/video pairing is GUESSED by order (folder numbers or take numbers don't match).")
    print("ready" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0
