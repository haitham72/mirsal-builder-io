"""python -m mirsal create "<prompt>" | more [G001] | animate [G001] [--slice N] | serve [--port N] [--pace S] [--workers N] | profile [G001] [--sweep 1,4,9] | recheck [G001|all]
   | db (up|migrate|reset --yes|import) | list | show G002 | history G002/S5 | search "<text>" [--approved --animated] | task <external-id> [--key <prefix>]"""
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


def _dbc():
    """Connect or explain. Returns None (after printing) when Postgres is unreachable."""
    from .store import db as _db
    if not _db.available():
        print(f"Postgres is not reachable at {_db.url()} (start it: python -m mirsal db up)")
        return None
    return _db.connect()


def db_cmd(out, action: str, yes: bool) -> int:
    from .store import db as _db
    from .store import repo
    if action == "up":
        import subprocess
        yml = out_root_compose()
        r = subprocess.run(["docker", "compose", "-f", str(yml), "up", "-d"], capture_output=True, text=True)
        print((r.stdout or "") + (r.stderr or ""))
        if r.returncode:
            return 1
        for _ in range(30):
            _db.reset_cache()
            if _db.available():
                break
            time.sleep(1)
        if not _db.available():
            print("mirsal-db started but is not answering yet; retry migrate in a few seconds")
            return 1
        action = "migrate"
    if action == "migrate":
        try:
            files = _db.migrate()
        except Exception as e:
            print(f"migrate failed: {e}")
            return 1
        print("migrated: " + (", ".join(files) or "nothing new"))
        return 0
    if action == "reset":
        if not yes:
            print("refusing: `db reset` destroys the local Mirsal database; pass --yes (dev only)")
            return 1
        try:
            _db.reset("yes")
            _db.migrate()
        except Exception as e:
            print(f"reset failed: {e}")
            return 1
        print("reset: local Mirsal database dropped and migrated fresh")
        return 0
    if action == "import":
        c = _dbc()
        if c is None:
            return 1
        with c:
            try:
                _db.migrate()
            except Exception as e:
                print(f"migrate failed: {e}")
                return 1
            nt = repo.import_tasks(c, out)
            ok, bad = 0, []
            for gid in pl.list_ids(out):
                try:
                    repo.save_generation(c, out, gid)
                    ok += 1
                except Exception as e:
                    c.rollback()  # one bad generation must not poison the rest of the import
                    bad.append(f"G{gid:03d}: {e}")
        print(f"imported {ok} generation(s), {nt} task file(s)")
        for b in bad:
            print("FAILED " + b)
        return 1 if bad else 0
    return 1


def out_root_compose():
    from pathlib import Path as _P
    return _P(__file__).resolve().parent.parent / "docker-compose.yml"


def store_cmd(args) -> int:
    import json as _json
    from .store import repo
    c = _dbc()
    if c is None:
        return 1
    with c:
        if args.cmd == "list":
            for g in repo.list_generations(c, args.limit):
                print(f"{g['id']}  {g['task_slug'] or g['prompt'][:40]:<42} {g['ready'] or 0}/{g['n'] or 0} {g['status']}"
                      + (f"  parent={g['parent_id']}" if g["parent_id"] else ""))
            return 0
        if args.cmd == "show":
            gid = f"G{_gid(args.gid):03d}"
            g = repo.get_generation(c, gid)
            if not g:
                print(f"no {gid} in Postgres (import: python -m mirsal db import)")
                return 1
            print(f"{g['id']}  {g['prompt']}\n  task={g['task_slug']} status={g['status']} parent={g['parent_id'] or '-'} "
                  f"template={g['template_id']} v{g['template_version']} assets={len(g['assets'])}")
            for s in g["stickers"]:
                print(f"  S{s['idx']} {''.join(s['emoji'])} {s['key']:<48} {s['status']}"
                      + (f" {s['reason']}" if s["reason"] else "")
                      + f"  still={s['still_review']} anim={s['anim_review']} {s['animation_status']}")
            return 0
        if args.cmd == "history":
            rows = repo.history(c, args.sid.upper())
            if not rows:
                print(f"no decisions for {args.sid} (import first: python -m mirsal db import)")
                return 1
            for r in rows:
                print(f"{r['ts']}  {r['gate']:<11} {r['decision']:<8} {r['actor']:<6} {r['reason'] or ''}")
            return 0
        if args.cmd == "search":
            rows = repo.search(c, args.query, approved=args.approved, animated=args.animated,
                               generation=args.generation, since=args.since)
            if args.as_json:
                print(_json.dumps(rows, ensure_ascii=False, default=str))
                return 0
            for r in rows:
                print(f"{r['generation_id']}/S{r['idx']} {''.join(r['emoji'])} {r['key']:<48} "
                      f"still={r['still_review']} anim={r['anim_review']}  {r['png'] or r['webm'] or ''}")
            if not rows:
                print("no matches")
            return 0
        if args.cmd == "task":
            rows = repo.find_task(c, external_id=args.ext, key_prefix=args.key)
            if not rows:
                print("no such task (import first: python -m mirsal db import)")
                return 1
            for t in rows:
                print(f"{t['provider']}:{t['external_task_id']}  kind={t['kind']} name_key={t['name_key']} "
                      f"status={t['status']} generation={t['generation_id'] or '-'}")
            return 0
    return 1


LAB_INPUTS = [  # S1 prompt lab: English, Arabic, Arabizi, occasion, green subject, constraint, blends
    "yellow teddy bear in Pixar 3D iOS style",
    "yellow teddy bear in toon cel shade with ios 3d genmoji style",
    "a cute yellow emoji face, 16 reactions",
    "falcon dancing",
    "banana shocked",
    "camel as cupcake",
    "dog as banana",
    "dog with bananas",
    "teddy bear playing football",
    "teddy bear with no dancing",
    "green frog with big eyes",
    "watermelon sticker pack",
    "dubai skyline at night",
    "arabic coffee celebration",
    "eid mubarak stickers",
    "\u062f\u0628 \u064a\u0631\u0642\u0635",
    "\u0635\u0642\u0631 \u0633\u0639\u064a\u062f",
    "\u062a\u062f\u064a \u0628\u064a\u0631 \u0645\u0628\u0633\u0648\u0637",
    "sakr yarkos",
    "teddy bear mabsout",
]


def prompt_cmd(out, args) -> int:
    from . import tasks as _t
    if (args.request or "") == "lab":
        ok = 0
        for req in LAB_INPUTS:
            try:
                plan = _t.preview(req, "3x3", args.style, ai=False)
                from . import prompter as _pr
                _pr.validate_plan(dict(plan))
                n, key = len(plan["stickers"]), plan["slots"]["key_colour"]
                uniq = len({s["key"] for s in plan["stickers"]})
                good = n == 9 and uniq == 9 and all(s["emoji"] for s in plan["stickers"])
                ok += good
                print(f"{'ok  ' if good else 'FAIL'}  {req[:52]:<54} {n} cells, {uniq} unique keys, key={key}")
            except Exception as e:
                print(f"FAIL  {req[:52]:<54} {e}")
        print(f"{ok}/{len(LAB_INPUTS)} lab inputs pass lint")
        return 0 if ok == len(LAB_INPUTS) else 1
    if not (args.request or "").strip():
        print('usage: mirsal prompt "<request>" [--grid 3x3|2x2|1x1] [--style ID] [--ai] | mirsal prompt lab')
        return 1
    try:
        plan = _t.preview(args.request, args.grid, args.style, ai=args.ai)
        if args.review_ai and args.ai:
            from . import expander as _ex
            plan = _ex.expand(args.request, tuple(plan["grid"]), use_ai=True, review_ai=True)
    except Exception as e:
        print(f"plan failed: {e}")
        return 1
    from . import prompter as _pr
    try:
        _pr.validate_plan(dict(plan))
        lint = "lint: PASS"
    except ValueError as e:
        lint = f"lint: FAIL {e}"
    sl = plan["slots"]
    print(f"task: {plan['task_slug']}  grid: {plan['grid']}  template: {plan['template_id']} v{plan['template_version']}  "
          f"expanded_by: {plan.get('expanded_by', 'deterministic')}  {lint}")
    print(f"subject: {sl.get('subject_description')}  style: {sl.get('style_id')}  key: {sl.get('key_colour')}")
    for s in plan["stickers"]:
        print(f"  {s['index']} {s['emoji']} {s['key']:<48} {' | '.join(s['tags'][1:])}")
    if args.mode == "single":
        for s in plan["stickers"]:
            print(f"--- single S{s['index']} ---\n{s['prompt']}")
    else:
        print(f"--- sheet prompt ---\n{plan['sheet_prompt']}\n--- video prompt ---\n{plan['video_prompt']}")
    return 0


def _job_line(j: dict) -> str:
    el = ""
    if j.get("created_at"):
        import time as _ti
        el = f"  elapsed={int(_ti.time() - j['created_at'])}s"
    return (f"{j['id']}  {j['kind']:<6} {j['status']:<9} task={j.get('task') or '-'} "
            f"ticket={j.get('external_task_id') or '-'}{el}"
            + (f"  error={j['error']}" if j.get("error") else ""))


def jobs_cmd(out, args) -> int:
    import json as _json
    from . import jobs as _j
    try:
        rows = _j.list(out, args.status)
    except Exception as e:
        print(e)
        return 1
    if args.as_json:
        print(_json.dumps(rows, ensure_ascii=False))
        return 0
    for j in rows:
        print(_job_line(j))
    if not rows:
        print("no jobs" + (f" with status {args.status}" if args.status else ""))
    return 0


def job_cmd(out, args) -> int:
    import json as _json
    from . import jobs as _j
    try:
        if args.action == "show":
            j = _j.read(out, args.jid or "")
            print(_json.dumps(j, indent=2, ensure_ascii=False))
        elif args.action == "create":
            j = _j.create(out, args.kind, task=args.task, generation=args.generation,
                          request={"note": "created from the CLI"})
            print(_job_line(j))
        elif args.action == "claim":
            print(_job_line(_j.claim(out, args.jid or "", args.ticket or "")))
        elif args.action == "done":
            j = _j.done(out, args.jid or "", args.file or "", args.model or "", args.cost)
            print(_job_line(j) + f"  file={j['result']['file']} sha={j['result']['sha256'][:12]}")
        elif args.action == "fail":
            print(_job_line(_j.fail(out, args.jid or "", args.reason)))
        elif args.action == "requeue":
            print(_job_line(_j.requeue(out, args.jid or "")))
        return 0
    except _j.JobError as e:
        print(e)
        return 1


def hf_cmd(out, args) -> int:
    from . import higgsfield as _hf, jobs as _j
    try:
        if args.action == "status":
            a = _hf.account()
            print(f"Higgsfield: {a['credits']:g} credits, plan {a['plan'] or '?'}")
        elif args.action == "models":
            d = _hf.load_models(out, refresh=args.refresh)
            if not d:
                print("The Higgsfield CLI is not installed and there is no cached list.")
                return 1
            print("models: " + ", ".join(f"{t} {d['counts'].get(t, 0)}" for t in _hf.TYPES) + f"  ->  {out / _hf.DUMP_NAME}")
            if args.type:
                for m in d.get(args.type, []):
                    ps = ", ".join(p["name"] + ("=" + "/".join(map(str, p["enum"])) if p.get("enum") else "") for p in m["params"] if p["name"] not in ("prompt",))
                    print(f"  {m['job_type']:<34} {m['display_name']:<30} {ps}")
        elif args.action == "run":
            j = _j.fulfil(out, args.jid or "")
            print(_job_line(j) + (f"  cost={j['cost']:g}" if j.get("cost") else "") + (f"  {j['error']}" if j.get("error") else ""))
            return 0 if j["status"] == "DONE" else 1
        return 0
    except (_hf.HiggsError, _j.JobError) as e:
        print(e)
        return 1


def pool_cmd(args) -> int:
    import json as _json
    from . import pool as _pool
    c = _dbc()
    if c is None:
        return 1
    with c:
        if args.action == "reindex":
            print(f"indexed { _pool.reindex(c)} sticker(s)")
            return 0
        if args.action == "hide":
            print("hidden" if _pool.hide(c, (args.query or "").upper()) else "no such indexed sticker")
            return 0
        res = _pool.search(c, args.query or "", count=args.count)
        if args.as_json:
            print(_json.dumps(res, ensure_ascii=False, default=str))
            return 0
        print(f"parsed: subject={res['parsed']['subject']!r} action={res['parsed']['action']!r}")
        for h in res["hits"]:
            print(f"  {h['sticker_id']} {''.join(h['emoji'])} {h['key']:<44} rank={h['rank']}")
        if res["missing"]:
            print(f"Found {res['found']} - generate {res['missing']} more? (confirm first: generation is never automatic)")
        elif not res["hits"]:
            print("no pool matches (zero, never the closest junk)")
        return 0


def photo_cmd(out, args, cfg) -> int:
    """3C, offline core: photo -> cutout (existing alpha | chroma | AI matte | GrabCut) -> the Phase 1
    edge finish -> a validated 512 sticker in out/photo/. Private by default (shared=false, no pool row)."""
    import json as _json
    from pathlib import Path as _P
    import numpy as _np
    from .engine.render import bbox_of, fit_scale, render_sticker
    from .library import LibraryError, cutout, decode_image, png_bytes, validate_render
    src = _P(str(args.file or ""))
    if not src.is_file():
        print(f"no such photo: {args.file}")
        return 1
    if src.stat().st_size > 50 * 1024 * 1024:
        print("photo is over 50 MB")
        return 1
    try:
        rgba = decode_image(src.read_bytes())
    except LibraryError as e:
        print(e)
        return 1
    if args.outline < 0 or args.outline > 40 or args.erode < 0 or args.erode > 8:
        print("outline is 0-40, erode is 0-8")
        return 1
    try:
        cut, info = cutout(rgba, cfg, args.method)
    except LibraryError as e:
        print(e)
        return 1
    bb = bbox_of(_np.ascontiguousarray(cut[..., 3]))
    if not bb:
        print("no subject found")
        return 1
    sticker = render_sticker(cut, bb, fit_scale(bb, cfg), cfg, args.outline, args.erode)
    try:
        body, ext, checks = validate_render(png_bytes(sticker), cfg)
    except LibraryError as e:
        print(e)
        return 1
    d = _P(out) / "photo"
    d.mkdir(parents=True, exist_ok=True)
    stem = f"photo-{src.stem[:40]}"
    (d / f"{stem}.{ext}").write_bytes(body)
    (d / f"{stem}.json").write_text(_json.dumps(
        {"src": str(src), "method": info.get("method"), "foreground": info.get("foreground"),
         "outline_px": args.outline, "erode_px": args.erode, "shared": False,
         "checks": checks, "warning": info.get("warning")}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{stem}.{ext}  method={info.get('method')} foreground={info.get('foreground')} "
          + " ".join(f"{n}={'ok' if ok else 'FAIL'}({d_})" for n, ok, d_ in checks))
    return 0


def main(argv=None) -> int:
    import sys as _sys
    try:  # Windows consoles default to cp1252, which cannot print emoji: replace, never crash
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="mirsal")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create"); c.add_argument("prompt")
    for n in ("more", "another"):
        m = sub.add_parser(n); m.add_argument("gid", nargs="?")
    a = sub.add_parser("animate"); a.add_argument("gid", nargs="?"); a.add_argument("--slice", type=int)
    sub.add_parser("doctor")
    rc = sub.add_parser("recheck", help="run the border check on animations made before it existed"); rc.add_argument("gid", nargs="?", default="all")
    pr = sub.add_parser("profile", help="time the animation of a generation stage by stage (nothing is saved)")
    pr.add_argument("gid", nargs="?"); pr.add_argument("--sweep", default="", help="worker counts to compare, e.g. 1,4,9")
    s = sub.add_parser("serve"); s.add_argument("--port", type=int, default=8770); s.add_argument("--pace", type=float, default=0.0)
    for p_ in (s, a):
        p_.add_argument("--workers", type=int, help="cells animated at the same time (default: CPU count up to 9, or MIRSAL_ANIM_WORKERS)")
    d = sub.add_parser("db", help="Postgres: up (start mirsal-db) | migrate | reset --yes (dev only) | import (backfill out/)")
    d.add_argument("action", choices=["up", "migrate", "reset", "import"]); d.add_argument("--yes", action="store_true")
    li = sub.add_parser("list", help="generations in Postgres, newest first"); li.add_argument("--limit", type=int, default=50)
    sh = sub.add_parser("show", help="one generation: stickers, files, gate decisions"); sh.add_argument("gid")
    hi = sub.add_parser("history", help="every decision for one sticker, in time order"); hi.add_argument("sid")
    se = sub.add_parser("search", help="search stickers in Postgres (full-text, trigram fallback)"); se.add_argument("query")
    se.add_argument("--approved", action="store_true"); se.add_argument("--animated", action="store_true")
    se.add_argument("--generation"); se.add_argument("--since"); se.add_argument("--json", action="store_true", dest="as_json")
    ta = sub.add_parser("task", help="what happened to a provider task id"); ta.add_argument("ext", nargs="?"); ta.add_argument("--key")
    pr = sub.add_parser("prompt", help='print locks, concepts and template-built prompts (S1 lab: "prompt lab")')
    pr.add_argument("request", nargs="?"); pr.add_argument("--grid", default="3x3"); pr.add_argument("--style", default="flat_vector")
    pr.add_argument("--ai", action="store_true"); pr.add_argument("--review-ai", action="store_true")
    pr.add_argument("--mode", default="sheet", choices=["sheet", "single"])
    js = sub.add_parser("jobs", help="pending generation jobs for the operator"); js.add_argument("--status")
    js.add_argument("--json", action="store_true", dest="as_json")
    jo = sub.add_parser("job", help="show|create|claim|done|fail|requeue one job")
    jo.add_argument("action", choices=["show", "create", "claim", "done", "fail", "requeue"]); jo.add_argument("jid", nargs="?")
    jo.add_argument("--kind", default="sheet"); jo.add_argument("--task"); jo.add_argument("--generation")
    jo.add_argument("--ticket"); jo.add_argument("--file"); jo.add_argument("--model"); jo.add_argument("--cost", type=float)
    jo.add_argument("--reason", default="")
    hf = sub.add_parser("hf", help="Higgsfield CLI: status (credits) | models [--type image|video] [--refresh] (full list) | run J### (fulfil a job)")
    hf.add_argument("action", choices=["status", "models", "run"]); hf.add_argument("jid", nargs="?")
    hf.add_argument("--type", choices=["image", "video", "audio", "text"]); hf.add_argument("--refresh", action="store_true")
    po = sub.add_parser("pool", help="search approved stickers first; generate only the gaps")
    po.add_argument("action", choices=["search", "reindex", "hide"]); po.add_argument("query", nargs="?")
    po.add_argument("--count", type=int, default=9); po.add_argument("--json", action="store_true", dest="as_json")
    ph = sub.add_parser("photo", help="a photo -> a cut-out 512 sticker (3C; on-device by default)")
    ph.add_argument("file"); ph.add_argument("--method", default="auto", choices=["auto", "matte", "grabcut"])
    ph.add_argument("--outline", type=int, default=12); ph.add_argument("--erode", type=int, default=0)
    args = ap.parse_args(argv)
    out, inp, cfg, t0 = out_root(), input_root(), EngineConfig(), time.perf_counter()
    if getattr(args, "workers", None):
        from dataclasses import replace
        cfg = replace(cfg, anim_workers=max(1, args.workers))
    if args.cmd == "doctor":
        return doctor()
    if args.cmd == "recheck":
        ids = pl.list_ids(out) if args.gid == "all" else [_gid(args.gid)]
        tot = bad = 0
        for gid in ids:
            r = pl.recheck_bounds(out, gid, cfg)
            tot += r["checked"]; bad += len(r["flagged"])
            if r["checked"]:
                print(f"G{gid:03d}: checked {r['checked']}, out of bounds: {', '.join('S' + str(i) for i in r['flagged']) or 'none'}")
        print(f"{tot} animations checked, {bad} leave their cell and are now blocked for review")
        return 0
    if args.cmd == "profile":
        return profile(out, _gid(args.gid), cfg, args.sweep)
    if args.cmd == "db":
        return db_cmd(out, args.action, args.yes)
    if args.cmd in ("list", "show", "history", "search", "task"):
        return store_cmd(args)
    if args.cmd == "prompt":
        return prompt_cmd(out, args)
    if args.cmd == "jobs":
        return jobs_cmd(out, args)
    if args.cmd == "job":
        return job_cmd(out, args)
    if args.cmd == "hf":
        return hf_cmd(out, args)
    if args.cmd == "pool":
        return pool_cmd(args)
    if args.cmd == "photo":
        return photo_cmd(out, args, cfg)
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


def profile(out, gid, cfg, sweep: str) -> int:
    """Where the time goes when a generation is animated: every cell, every stage (milliseconds), then the whole batch at each worker count.
    Runs the real engine on the prepared source, without the result cache and without saving anything."""
    import os
    from dataclasses import replace
    gid = gid or pl.latest_id(out)
    res = pl.read_result(out, gid)
    if not res["source"]["has_video"]:
        print(f"G{gid:03d} has no prepared video."); return 1
    cfg = pl.cfg_for(res, cfg)
    cells = [s["index"] for s in res["stickers"] if s["status"] == "READY"]
    src = res["source"]
    print(f"G{gid:03d} {res['task_slug']}: {len(cells)} cells, source {'pre-sliced clips' if src.get('clips') else '3x3 mp4'} ({(src.get('video_info') or {}).get('size', '')}), "
          f"{os.cpu_count()} CPUs, default workers {cfg.anim_workers}\n")
    counts = [int(x) for x in sweep.split(",") if x.strip()] or [1, cfg.anim_workers]
    stages = ["decode", "key", "bounds", "render", "seam", "encode", "probe", "verify"]
    for n, w in enumerate(dict.fromkeys(counts)):
        t0 = time.perf_counter()
        results = sorted(pl.animate_cells(res, replace(cfg, anim_workers=w), cells), key=lambda r: r.index)
        wall = time.perf_counter() - t0
        if n == 0:
            print("cell " + "".join(f"{x:>8}" for x in stages) + "   encodes   total  result")
            tot = dict.fromkeys(stages, 0)
            for r in results:
                ms = r.metrics.get("ms", {})
                for x in stages:
                    tot[x] += ms.get(x, 0)
                print(f"S{r.index:<3} " + "".join(f"{ms.get(x, 0):>8}" for x in stages) + f"   {ms.get('encodes', 0):>7}  {sum(ms.get(x, 0) for x in stages):>6}  {r.status}"
                      + (f" {r.reason}" if r.reason else "") + (" (out of bounds)" if (r.report.get('inside_frame') and not r.report.get('inside_frame').ok) else ""))
            grand = sum(tot.values()) or 1
            print("sum  " + "".join(f"{tot[x]:>8}" for x in stages) + f"   {'':>7}  {grand:>6}   ms of work in total")
            print("share" + "".join(f"{100 * tot[x] / grand:>7.0f}%" for x in stages) + "\n")
            print(f"workers  wall time   (work / wall = how many cores were really busy)")
        print(f"{w:>7}  {wall:>7.1f} s   {sum(sum(r.metrics.get('ms', {}).get(x, 0) for x in stages) for r in results) / 1000 / wall:>5.1f}x")
    return 0


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
    from . import llm
    print("OK      AI expansion: " + (f"on, model {llm.model()}" if llm.configured() else f"off: add {llm.KEY_VAR} to mirsal/.env to let the AI expand a subject and name every sticker (the built-in sets are used meanwhile)"))
    from . import higgsfield as _hf
    if not _hf.available():
        print("NOTE    Higgsfield: CLI not installed (npm i -g @higgsfield/cli, then higgsfield auth login): live generation is off, prepared sheets still work")
    else:
        try:
            _a = _hf.account()
            print(f"OK      Higgsfield: {_a['credits']:g} credits, plan {_a['plan'] or '?'} (live generation on; Nano Banana 2 at 2k and Kling v3.0 by default, Kling 4k is never used)")
        except _hf.HiggsError as e:
            print(f"NOTE    Higgsfield: installed but not usable ({str(e)[:140]}): run higgsfield auth login")
    import os
    print(f"OK      animation workers: {EngineConfig().anim_workers} of {os.cpu_count()} CPUs (MIRSAL_ANIM_WORKERS or serve --workers N changes it)")
    try:
        from .store import db as _db
        if _db.available():
            print(f"OK      Postgres: reachable ({_db.url().split('@')[-1]}); write-through "
                  + ("on" if os.environ.get("MIRSAL_DB_WRITE", "") not in ("0", "no", "off", "false") and not os.environ.get("MIRSAL_OUT") else "off (MIRSAL_OUT copy or MIRSAL_DB_WRITE=0: use `db import`)"))
        else:
            print(f"NOTE    Postgres: not connected ({_db.url().split('@')[-1]}; start it: python -m mirsal db up)")
    except Exception as e:
        print(f"NOTE    Postgres: store unavailable ({e}; pip install -r requirements.txt)")
    try:
        from .obs import trace as _tr
        st = _tr.status()
        print(f"OK      trace backend: {st['backend']}" + (f" (reachable)" if st["reachable"] else " (unreachable)" if st["reachable"] is False else ""))
    except Exception as e:
        print(f"NOTE    trace: {e}")
    from . import telegram
    try:
        import ssl
        ssl.create_default_context(); print("OK      TLS: system certificate store loads")
    except ssl.SSLError as e:
        telegram._ssl_context(); print(f"NOTE    TLS: this PC's certificate store has malformed entries ({e.reason}); Mirsal skips them, Telegram still works")
    t = telegram.status(out_root())
    print(f"OK      Telegram: connected as @{t['bot']} (user {t['user_id']})" if t["configured"] else "NOTE    Telegram: not connected (optional: Settings -> Telegram, or MIRSAL_TELEGRAM_TOKEN and MIRSAL_TELEGRAM_USER)")
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
