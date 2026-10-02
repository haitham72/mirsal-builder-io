"""Live generation through the Higgsfield CLI, with a FAKE CLI (no credits are spent): the ticket-first rule, resume, the daily cap, the Kling 4k ban,
the model catalog, the credit roll-up, v2 prompts, and one full run through the console: sheet job -> stills -> approved video sheet -> Kling job -> sliced."""
import http.client
import json
import os
import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np
from PIL import Image

from mirsal import expander, higgsfield, jobs, llm, model_catalog, prompter, styles, usage
from mirsal import tasks as _tasks
from mirsal.console.server import serve
from mirsal.engine.config import EngineConfig
from tests import synth
from tests.test_golden import shape_sheet


class FakeCLI:
    """Stands in for `higgsfield ... --json`: records every call and answers like the real CLI did on 2026-10-01."""

    def __init__(self, cost=2.0):
        self.calls, self.cost, self.n, self.kind_of, self.wait_hook = [], cost, 0, {}, None

    def __call__(self, args, timeout):
        self.calls.append(list(args))
        if args[:2] == ["account", "status"]:
            return 0, json.dumps({"credits": 100.5, "email": "x@y", "subscription_plan_type": "creator"}), ""
        if args[:2] == ["generate", "cost"]:
            return 0, json.dumps({"credits": self.cost}), ""
        if args[:2] == ["generate", "create"]:
            self.n += 1
            jid = f"fake-job-{self.n}"
            self.kind_of[jid] = "mp4" if args[2] in ("kling3_0", "grok_video_v15") else "png"
            return 0, json.dumps([jid]), ""
        if args[:2] == ["generate", "wait"]:
            if self.wait_hook:
                self.wait_hook(args[2])
            return 0, json.dumps({"id": args[2], "status": "completed", "result_url": f"http://fake/{args[2]}.{self.kind_of[args[2]]}"}), ""
        if args[:2] == ["model", "list"]:
            return 0, "[]", ""
        return 1, "", "unknown command"


def png_bytes(arr) -> bytes:
    ok, buf = cv2.imencode(".png", cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
    return buf.tobytes()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "in" / "Images_gen").mkdir(parents=True)
        (self.tmp / "in" / "videos_gen").mkdir(parents=True)
        self.out = self.tmp / "out"
        self.cli = FakeCLI()
        self.files = {}                                          # url suffix -> bytes the fake download writes
        self.patches = [mock.patch.object(higgsfield, "RUN", self.cli),
                        mock.patch.object(higgsfield, "binary", lambda: ("fake-hf", True)),
                        mock.patch.object(higgsfield, "download", self._download)]
        for p in self.patches:
            p.start()
        os.environ.pop("MIRSAL_DAILY_CREDITS", None)

    def tearDown(self):
        for p in self.patches:
            p.stop()
        os.environ.pop("MIRSAL_DAILY_CREDITS", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _download(self, url, dest):
        data = self.files.get(url.rsplit(".", 1)[-1], b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        Path(dest).write_bytes(data)
        import hashlib
        return hashlib.sha256(data).hexdigest(), len(data)


class FulfilTests(Base):
    def sheet_job(self, **req):
        t = _tasks.reserve(self.out, self.tmp / "in", "falcon dancing")
        return jobs.create(self.out, "sheet", task=t["id"], request={"model": "nano_banana_flash", "options": {}, "prompt": "p", **req}), t

    def test_ticket_is_stored_before_waiting_and_the_run_is_priced_and_logged(self):
        j, t = self.sheet_job()
        seen = {}

        def at_wait(ticket):
            cur = jobs.read(self.out, j["id"])
            seen.update(status=cur["status"], ticket=cur["external_task_id"], mirrored=_tasks.read_task(self.out, t["id"])["external_task_id"])
        self.cli.wait_hook = at_wait
        done = jobs.fulfil(self.out, j["id"])
        self.assertEqual(seen, {"status": "CLAIMED", "ticket": "fake-job-1", "mirrored": "fake-job-1"})      # ticket first (rule 10)
        self.assertEqual((done["status"], done["cost"], done["model"], done["provider"]), ("DONE", 2.0, "nano_banana_flash", "higgsfield-cli"))
        self.assertTrue((self.out / done["result"]["file"]).is_file())
        create = next(c for c in self.cli.calls if c[:2] == ["generate", "create"])
        self.assertNotIn("--wait", create)                                                                   # create does not wait: the id would come too late
        self.assertEqual(create[create.index("--resolution") + 1], "2k")                                     # Nano Banana 2 at 2k by default
        row = json.loads((self.out / "model_calls.jsonl").read_text().splitlines()[-1])
        self.assertEqual((row["kind"], row["model"], row["cost"], row["external_task_id"]), ("IMAGE_SHEET", "nano_banana_flash", 2.0, "fake-job-1"))

    def test_a_claimed_job_resumes_by_its_ticket_and_never_creates_a_second_paid_job(self):
        j, _ = self.sheet_job()
        jobs.claim(self.out, j["id"], "fake-job-9")
        jobs.update(self.out, j["id"], cost_estimate=2.0)
        self.cli.kind_of["fake-job-9"] = "png"
        done = jobs.fulfil(self.out, j["id"])
        self.assertEqual(done["status"], "DONE")
        self.assertFalse([c for c in self.cli.calls if c[:2] == ["generate", "create"]])

    def test_a_retry_waits_for_the_same_higgsfield_job_and_never_pays_twice(self):
        j, _ = self.sheet_job()
        boom = {"n": 0}

        def flaky(ticket):
            boom["n"] += 1
            if boom["n"] == 1:
                raise higgsfield.HiggsError("Higgsfield API error (HTTP 503) request failed with status 503 Service Unavailable")
        self.cli.wait_hook = flaky
        failed = jobs.fulfil(self.out, j["id"])
        self.assertEqual((failed["status"], failed["external_task_id"]), ("FAILED", "fake-job-1"))          # the job exists at Higgsfield; only the waiting broke
        again = jobs.resume(self.out, j["id"])
        self.assertEqual((again["status"], again["external_task_id"], again["error"]), ("CLAIMED", "fake-job-1", None))
        done = jobs.fulfil(self.out, j["id"])
        self.assertEqual(done["status"], "DONE")
        self.assertEqual(len([c for c in self.cli.calls if c[:2] == ["generate", "create"]]), 1)               # one paid creation in total
        with self.assertRaises(jobs.JobError):
            jobs.resume(self.out, j["id"])                                                                     # a finished job has nothing to retry
        j2, _ = self.sheet_job()
        jobs.fail(self.out, j2["id"], "nothing was created")
        self.assertEqual(jobs.resume(self.out, j2["id"])["status"], "REQUESTED")                               # no ticket: asked again from scratch

    def test_provider_failure_marks_the_job_failed_with_the_reason(self):
        j, _ = self.sheet_job()
        self.cli.wait_hook = lambda t: (_ for _ in ()).throw(higgsfield.HiggsError("boom"))
        with mock.patch.object(higgsfield, "wait", side_effect=higgsfield.HiggsError("the job ended as 'failed'")):
            done = jobs.fulfil(self.out, j["id"])
        self.assertEqual(done["status"], "FAILED")
        self.assertIn("failed", done["error"])

    def test_the_daily_cap_refuses_before_anything_is_paid(self):
        os.environ["MIRSAL_DAILY_CREDITS"] = "1"
        j, _ = self.sheet_job()
        done = jobs.fulfil(self.out, j["id"])
        self.assertEqual(done["status"], "FAILED")
        self.assertIn("daily credit cap", done["error"])
        self.assertFalse([c for c in self.cli.calls if c[:2] == ["generate", "create"]])

    def test_kling_4k_is_never_possible(self):
        with self.assertRaises(model_catalog.CatalogError):
            model_catalog.resolve("video", "kling3_0", {"mode": "4k"})
        with self.assertRaises(higgsfield.HiggsError):
            higgsfield.cost("kling3_0", {"mode": "4k"}, "x")
        self.assertFalse([c for c in self.cli.calls if c[:2] == ["generate", "cost"]])
        # an unknown option or value is refused, never passed through
        with self.assertRaises(model_catalog.CatalogError):
            model_catalog.resolve("image", "nano_banana_flash", {"resolution": "8k"})
        with self.assertRaises(model_catalog.CatalogError):
            model_catalog.resolve("image", "nano_banana_flash", {"nonsense": "1"})

    def test_catalog_defaults_and_selections(self):
        self.assertEqual(model_catalog.resolve("image", None, {}), ("nano_banana_flash", {"aspect_ratio": "1:1", "resolution": "2k"}))
        self.assertEqual(model_catalog.resolve("video", None, {}), ("kling3_0", {"aspect_ratio": "1:1", "sound": "off", "mode": "pro", "duration": "3"}))
        self.assertEqual(model_catalog.resolve("image", "gpt_image_2_5", {"variant": "sunburst"})[1]["variant"], "sunburst")
        self.assertEqual(model_catalog.resolve("video", "grok_video_v15", {"resolution": "1080p"})[1]["resolution"], "1080p")
        ids = {m["id"] for m in model_catalog.IMAGE}
        self.assertTrue({"nano_banana_flash", "nano_banana_pro", "nano_banana_2_lite", "gpt_image_2", "gpt_image_2_5",
                         "seedream_v5_pro", "seedream_5_0_flash", "seedream_v5_lite"} <= ids)
        # every model of the full Higgsfield dump is selectable too, with options built from its own parameters
        model_catalog.set_dump({"image": [{"job_type": "flux_2", "display_name": "FLUX.2", "params": [{"name": "aspect_ratio", "type": "string", "enum": ["1:1", "16:9"]},
                                {"name": "prompt", "type": "string"}, {"name": "resolution", "type": "string", "default": "2k", "enum": ["1k", "2k"]}]}],
                                "video": [], "counts": {"image": 1}})
        try:
            self.assertEqual(model_catalog.resolve("image", "flux_2", {"resolution": "1k"}), ("flux_2", {"aspect_ratio": "1:1", "resolution": "1k"}))
            self.assertEqual([m["id"] for m in model_catalog.catalog()["more"]["image"]], ["flux_2"])
        finally:
            model_catalog.set_dump(None)

    def test_usage_rolls_up_credits_by_model_and_by_run(self):
        j, t = self.sheet_job()
        jobs.fulfil(self.out, j["id"])
        j2, _ = self.sheet_job()
        self.cli.cost = 4.5
        jobs.fulfil(self.out, j2["id"])
        u = usage.summary(self.out)
        self.assertEqual((u["credits_spent"], u["today"], u["calls"]), (6.5, 6.5, 2))
        self.assertEqual([(m["model"], m["label"], m["calls"], m["credits"]) for m in u["by_model"]], [("nano_banana_flash", "Nano Banana 2", 2, 6.5)])
        self.assertEqual(sorted(r["credits"] for r in u["runs"]), [2.0, 4.5])
        self.assertEqual(u["by_group"]["image"]["credits"], 6.5)


class PromptV2Tests(unittest.TestCase):
    def test_v2_prompts_avoid_the_words_that_caused_the_white_outline_and_the_checkerboard(self):
        p = prompter.expand("teddy bear", (3, 3))
        self.assertEqual(p["template_version"], prompter.TEMPLATE_VERSION)
        sheet = p["sheet_prompt"].lower()
        for bad in ("sticker", "grid", "cell", "gap", "row-major", "panel line"):
            self.assertNotIn(bad, sheet.replace("no tiled panels", ""), bad)
        self.assertIn("character 1:", sheet)
        self.assertIn("no outline", sheet)
        self.assertIn("single, seamless, solid pure green", sheet)

    def test_wide_emotions_one_per_mood_and_a_motion_for_every_character(self):
        p = prompter.expand("teddy bear", (3, 3))
        self.assertEqual(len({c["emoji"] for c in p["slots"]["cells"]}), 9)
        self.assertEqual(len({c["label"] for c in p["slots"]["cells"]}), 9)
        lines = [l for l in p["video_prompt"].splitlines() if l[:2] in {f"{i}." for i in range(1, 10)}]
        self.assertEqual(len(lines), 9)
        self.assertEqual(prompter.expand("teddy bear", (3, 3))["slots"], p["slots"])          # deterministic
        self.assertNotEqual([c["label"] for c in prompter.expand("a fox", (3, 3))["slots"]["cells"]], [c["label"] for c in p["slots"]["cells"]])

    def test_a_saved_v1_plan_rebuilds_to_the_v1_wording(self):
        slots = prompter.expand("teddy bear", (3, 3))["slots"]
        v1 = prompter.render_plan(slots, "sheet_3x3", 1)
        self.assertIn("sticker sheet", v1["sheet_prompt"])
        self.assertIn("1. ", v1["sheet_prompt"])

    def test_style_presets_change_the_style_line_only(self):
        a = prompter.render_plan(dict(prompter.expand("teddy bear", (3, 3))["slots"], style_id="glossy_3d"), "sheet_3x3", 2)["sheet_prompt"]
        b = prompter.render_plan(dict(prompter.expand("teddy bear", (3, 3))["slots"], style_id="toon_shade"), "sheet_3x3", 2)["sheet_prompt"]
        self.assertIn(styles.PHRASE["glossy_3d"], a)
        self.assertIn(styles.PHRASE["toon_shade"], b)
        self.assertEqual(len(styles.PRESETS), 6)


class LiveConsoleTests(Base):
    """The whole chain through the HTTP API with the fake CLI: sheet job -> unchanged stills run -> G2 -> video sheet -> G3 -> Kling job -> sliced."""

    def setUp(self):
        super().setUp()
        self.srv, self.c = serve(self.out, self.tmp / "in", 0, cfg=EngineConfig(), block=False)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.files["png"] = png_bytes(shape_sheet(1200, [(x, y) for y in (200, 600, 1000) for x in (200, 600, 1000)]))

    def tearDown(self):
        self.c.wait_jobs(90)                       # every background provider job ends while the fake CLI is still plugged in
        self.srv.shutdown()
        super().tearDown()

    def req(self, method, path, body=None):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        h.request(method, path, json.dumps(body) if body is not None else None, {"Content-Type": "application/json"})
        r = h.getresponse(); data = r.read(); h.close()
        try:
            return r.status, json.loads(data)
        except ValueError:
            return r.status, data

    def until(self, fn, what, timeout=180):
        end = time.time() + timeout
        while time.time() < end:
            v = fn()
            if v:
                return v
            time.sleep(0.3)
        self.fail("timeout: " + what)

    def test_history_lists_every_batch_five_at_a_time_and_survives_opening_another(self):
        import json as _j
        for n in range(1, 8):                                                                       # seven finished batches on disk
            d = self.out / f"G{n:03d}"
            (d / "slices").mkdir(parents=True)
            (d / "prompts.json").write_text("{}", encoding="utf-8")
            res = {"generation_id": f"G{n:03d}", "number": n, "prompt": f"batch {n}", "stage": "sliced", "error": None, "source": {"subject": "blob"},
                   "stickers": [{"index": i, "key": f"k{i}", "status": "READY", "png": f"slices/S{i}.png", "anim_status": "READY" if n % 2 else "NOT_REQUESTED"} for i in range(1, 10)]}
            (d / "result.json").write_text(_j.dumps(res), encoding="utf-8")
        p1 = self.req("GET", "/api/history?limit=5")[1]
        self.assertEqual(([i["generation_id"] for i in p1["items"]], p1["more"], p1["total"]), (["G007", "G006", "G005", "G004", "G003"], True, 7))
        p2 = self.req("GET", "/api/history?limit=5&offset=5")[1]
        self.assertEqual(([i["generation_id"] for i in p2["items"]], p2["more"]), (["G002", "G001"], False))
        self.assertEqual((p1["items"][0]["ready"], p1["items"][0]["animated"], len(p1["items"][0]["thumbs"]), p1["items"][0]["prompt"]), (9, 9, 4, "batch 7"))

    def test_the_export_folder_is_a_choice_and_every_live_batch_is_mirrored(self):
        from mirsal import export
        elsewhere = self.tmp / "my_stickers"
        os.environ["MIRSAL_EXPORT_DIR"] = str(elsewhere)
        try:
            gid = self._stills_ready("export blob")
            self.assertEqual(export.sync_all(self.out), 1)                                      # the back-fill at server start
            imgs = elsewhere / "images" / "img-001-export_blob"
            self.assertTrue(imgs.is_dir() and any(p.name.startswith("img-001-export_blob-s1-") for p in imgs.iterdir()))
            self.assertFalse((self.out / "export").exists() and any((self.out / "export" / "images").glob("img-001-export_blob")))
            self.assertEqual(self.req("GET", f"/api/generations/{gid}/files")[1]["package"], str(imgs))
        finally:
            os.environ.pop("MIRSAL_EXPORT_DIR", None)

    def test_models_account_usage_and_assets_endpoints(self):
        s, j = self.req("GET", "/api/models")
        self.assertEqual(s, 200)
        self.assertEqual((j["defaults"], j["default_style"]), ({"image": "nano_banana_flash", "video": "kling3_0"}, "flat_vector"))
        self.assertEqual([m["id"] for m in j["video"]], ["kling3_0", "grok_video_v15"])
        self.assertEqual(len(j["styles"]), 6)
        s, j = self.req("GET", "/api/higgsfield")
        self.assertEqual((s, j["available"], j["credits"], j["plan"]), (200, True, 100.5, "creator"))
        for kind, name in (("styles", "glossy_3d"), ("vendors", "openai"), ("vendors", "google")):
            s, raw = self.req("GET", f"/assets/{kind}/{name}")
            self.assertEqual(s, 200)
            self.assertIn(b"<svg", raw)                                                  # real file or generated placeholder, never a broken image
        self.assertEqual(self.req("GET", "/assets/styles/..%2Fserver")[0], 404)         # nothing outside the assets folder
        s, j = self.req("POST", "/api/live/cost", {"kind": "image"})
        self.assertEqual((s, j["credits"], j["model"]), (200, 2.0, "nano_banana_flash"))
        s, j = self.req("POST", "/api/live/cost", {"kind": "video", "model": "kling3_0", "options": {"mode": "4k"}})
        self.assertEqual(s, 400)

    def _ai_answer(self):
        names = ["laughing", "crying", "angry", "shocked", "in_love", "proud", "scared", "sleepy", "scheming"]
        return json.dumps({"subject_description": "a small cartoon owl", "cells": [
            {"label": f"owl {n.replace('_', ' ')} with a huge expression", "motion": f"the owl acts {n} with a big bounce", "key": n, "tags": [], "emoji": ["🦉"]} for n in names]})

    def test_the_ai_enhancer_is_only_used_when_asked_and_never_while_typing(self):
        calls = []

        def fake(system, user, **kw):
            calls.append(user)
            return self._ai_answer(), {"model": "fake-llm"}
        os.environ["MIRSAL_OUT"] = str(self.out)                                   # the expander's ledger line must not land in the real out/
        try:
            with mock.patch.object(llm, "complete", fake), mock.patch.object(llm, "configured", lambda: True):
                s, j = self.req("POST", "/api/plan", {"prompt": "owl", "grid": "3x3", "style_id": "flat_vector"})       # what the page sends while typing
                self.assertEqual((s, j["expanded_by"], calls), (200, "deterministic", []))
                s, j = self.req("POST", "/api/live/sheet", {"prompt": "owl", "ai": False})
                self.assertEqual((s, j["expanded_by"], calls), (200, "deterministic", []))                           # switch off: straight into the template
                s, j = self.req("POST", "/api/live/sheet", {"prompt": "owl", "ai": True})
                self.assertEqual((s, j["expanded_by"], len(calls)), (200, "ai", 1))                                  # switch on: expanded first, then sent
                job = self.until(lambda: (lambda x: x if x["status"] == "DONE" else None)(self.req("GET", "/api/jobs/" + j["job"])[1]), "job")
                sent = next(c for c in self.cli.calls if c[:2] == ["generate", "create"] and "owl laughing" in c[c.index("--prompt") + 1])
                self.assertIn("a small cartoon owl", sent[sent.index("--prompt") + 1])                                # the AI's concepts are in what was sent
                self.assertEqual(job["cost"], 2.0)
            with mock.patch.object(llm, "complete", lambda *a, **k: (_ for _ in ()).throw(llm.LLMError("quota"))), mock.patch.object(llm, "configured", lambda: True):
                s, j = self.req("POST", "/api/live/sheet", {"prompt": "owl", "ai": True})
                self.assertEqual((s, j["expanded_by"]), (200, "deterministic"))                                       # falls back, and says why
                self.assertIn("quota", j["expand_error"])
        finally:
            os.environ.pop("MIRSAL_OUT", None)

    def test_reference_images_are_uploaded_stored_and_sent_with_the_sheet_job(self):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h.request("POST", "/api/live/ref?name=angel.png", png_bytes(shape_sheet(300, [(150, 150)])), {"Content-Type": "application/octet-stream"})
        r = h.getresponse(); ref = json.loads(r.read()); h.close()
        self.assertEqual((r.status, ref["id"], ref["file"]), (200, "R001", "refs/R001.png"))
        self.assertTrue((self.out / ref["file"]).is_file())
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h.request("POST", "/api/live/ref?name=x.png", b"not an image", {}); r = h.getresponse(); r.read(); h.close()
        self.assertEqual(r.status, 400)                                                              # only real images are stored
        s, j = self.req("POST", "/api/live/sheet", {"prompt": "blob", "refs": ["R001"], "model": "nano_banana_pro"})
        self.assertEqual(s, 200, j)
        self.until(lambda: self.req("GET", "/api/jobs/" + j["job"])[1]["status"] == "DONE", "job")
        create = next(c for c in self.cli.calls if c[:3] == ["generate", "create", "nano_banana_pro"])
        self.assertEqual(create[create.index("--image-references") + 1], str(self.out / "refs" / "R001.png"))
        self.assertIn(prompter.REFERENCE_CLAUSE, create[create.index("--prompt") + 1])
        job = self.req("GET", "/api/jobs/" + j["job"])[1]
        self.assertEqual((job["request"]["refs"], job["params"]["references"]), (["refs/R001.png"], 1))   # reproducible from the stored job
        self.assertEqual(self.req("POST", "/api/live/sheet", {"prompt": "blob", "refs": ["R999"]})[0], 400)
        self.assertEqual(self.req("POST", "/api/live/sheet", {"prompt": "blob", "refs": ["R001"] * 5})[0], 400)
        model_catalog.set_dump({"image": [{"job_type": "no_refs", "display_name": "No Refs", "params": [{"name": "prompt", "type": "string"}]}], "video": [], "counts": {}})
        try:
            s, j = self.req("POST", "/api/live/sheet", {"prompt": "blob", "refs": ["R001"], "model": "no_refs"})
            self.assertEqual(s, 400)
            self.assertIn("does not take reference images", j["error"])
        finally:
            model_catalog.set_dump(None)

    def test_one_click_animation_builds_and_approves_the_video_sheet_itself(self):
        s, j = self.req("POST", "/api/live/sheet", {"prompt": "blob"})
        job = self.until(lambda: (lambda x: x if x.get("generation") and x["status"] == "DONE" else None)(self.req("GET", "/api/jobs/" + j["job"])[1]), "sheet job")
        gid = int(job["generation"][1:])
        self.until(lambda: (lambda x: x if x["stage"] == "sliced" and not x["busy"] else None)(self.req("GET", f"/api/generations/{gid}")[1]), "stills")
        s, v = self.req("POST", "/api/live/video", {"generation": gid})                     # no sheet named: the click is the decision
        self.assertEqual(s, 200, v)
        st = self.req("GET", f"/api/generations/{gid}")[1]
        self.assertIn(next(x for x in st["video_sheets"] if x["id"] == "A1")["status"], ("APPROVED", "VIDEO_RETURNED", "SLICED", "VIDEO_BLOCKED"))
        create = self.until(lambda: next((c for c in self.cli.calls if c[:3] == ["generate", "create", "kling3_0"]), None), "the Kling create call")   # sent by the job thread
        self.assertEqual(create[create.index("--mode") + 1], "pro")                          # always pro: 1440 px, never std
        prompt = create[create.index("--prompt") + 1]
        self.assertIn("wide range of emotions", prompt)
        self.assertIn("highly expressive", prompt)
        self.assertEqual(self.req("POST", "/api/live/cost", {"kind": "video", "model": "kling3_0", "options": {"mode": "std"}})[0], 400)   # std is not offered any more

    def _stills_ready(self, prompt="blob"):
        s, j = self.req("POST", "/api/live/sheet", {"prompt": prompt})
        job = self.until(lambda: (lambda x: x if x.get("generation") and x["status"] == "DONE" else None)(self.req("GET", "/api/jobs/" + j["job"])[1]), "sheet job")
        gid = int(job["generation"][1:])
        self.until(lambda: (lambda x: x if x["stage"] == "sliced" and not x["busy"] else None)(self.req("GET", f"/api/generations/{gid}")[1]), "stills")
        return gid

    def _png(self, path):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        h.request("GET", path); r = h.getresponse(); data = r.read(); h.close()
        return r.status, r.getheader("Content-Type"), data

    def _idle(self, gid):
        return self.until(lambda: (lambda x: x if not x["busy"] else None)(self.req("GET", f"/api/generations/{gid}")[1]), "the batch to be idle")

    def test_the_edge_is_a_preview_until_applied_then_one_snapshot_that_undo_restores(self):
        import io
        gid = self._stills_ready()
        slices = self.out / f"G{gid:03d}" / "slices"
        stamp = lambda: sorted((p.name, p.stat().st_mtime_ns) for p in slices.glob("*"))
        before, files = self.req("GET", f"/api/generations/{gid}")[1], stamp()

        def visible(o, e=0):
            s, ct, data = self._png(f"/api/generations/{gid}/edge_preview?index=1&outline={o}&erode={e}&px=200")
            self.assertEqual((s, ct), (200, "image/png"))
            return int((np.asarray(Image.open(io.BytesIO(data)).convert("RGBA"))[..., 3] > 128).sum())
        self.assertGreater(visible(12), visible(0))                                   # a stroke adds area, a trim takes it away
        self.assertLess(visible(0, 3), visible(0, 0))
        for o in range(0, 14, 2):                                                    # dragging a slider: every position is only a render
            visible(o)
        after = self.req("GET", f"/api/generations/{gid}")[1]
        self.assertEqual(stamp(), files)                                              # nothing was written or re-rendered
        self.assertEqual((after["outline_px"], after.get("edge_history")), (before["outline_px"], before.get("edge_history")))
        self.assertEqual(self._png(f"/api/generations/{gid}/edge_preview?index=1&outline=99&erode=0")[0], 400)

        # Apply: ONE snapshot (seeded with how the batch started), the whole batch re-rendered
        was = before["outline_px"]
        self.assertEqual(self.req("POST", f"/api/generations/{gid}/edge", {"outline": 6, "erode": 1, "via": "apply"})[0], 202)
        res = self._idle(gid)
        self.assertEqual((res["outline_px"], res["erode_px"]), (6, 1))
        self.assertEqual([(h["outline"], h["erode"], h["via"]) for h in res["edge_history"]], [(was, 0, "initial"), (6, 1, "apply")])
        self.assertTrue(all((s.get("metrics") or {}).get("outline_px") == 6 for s in res["stickers"] if s["status"] == "READY"))
        # the same edge again changes nothing and adds no snapshot
        self.assertEqual(self.req("POST", f"/api/generations/{gid}/edge", {"outline": 6, "erode": 1})[0], 202)
        self.assertEqual(len(self._idle(gid)["edge_history"]), 2)
        # Undo goes back to the previous snapshot (and is itself recorded, never a deletion)
        prev = res["edge_history"][-2]
        self.assertEqual(self.req("POST", f"/api/generations/{gid}/edge", {"outline": prev["outline"], "erode": prev["erode"], "via": "undo"})[0], 202)
        res = self._idle(gid)
        self.assertEqual((res["outline_px"], res["erode_px"]), (was, 0))
        self.assertEqual([h["via"] for h in res["edge_history"]], ["initial", "apply", "undo"])
        self.assertEqual(self.req("POST", f"/api/generations/{gid}/edge", {})[0], 400)

    def test_a_pending_edge_becomes_real_exactly_at_video_generation_and_at_the_pack(self):
        gid = self._stills_ready()
        was = self.req("GET", f"/api/generations/{gid}")[1]["outline_px"]
        self.assertFalse(self.c.commit_edge(gid, None, None, "video"))                # nothing pending: nothing happens
        s, v = self.req("POST", "/api/live/video", {"generation": gid, "outline": 5, "erode": 1})   # image -> video
        self.assertEqual(s, 200, v)
        res = self.req("GET", f"/api/generations/{gid}")[1]
        self.assertEqual((res["outline_px"], res["erode_px"], res["edge_history"][-1]["via"]), (5, 1, "video"))
        self.c.wait_jobs(90)
        self.assertTrue(self.c.commit_edge(gid, 3, 0, "pack"))                         # video -> pack (the add endpoint calls this)
        res = self.req("GET", f"/api/generations/{gid}")[1]
        self.assertEqual((res["outline_px"], res["edge_history"][-1]["via"], res["edge_history"][0]["outline"]), (3, "pack", was))
        self.assertFalse(self.c.commit_edge(gid, 3, 0, "pack"))                        # already exactly this edge: no second snapshot
        self.assertEqual(len(self.req("GET", f"/api/generations/{gid}")[1]["edge_history"]), 3)

    def test_a_blue_screen_sheet_is_keyed_as_blue_and_marked_only_because_it_is_blue(self):
        from mirsal import export, pipeline as pl
        from mirsal.engine import chroma
        green = shape_sheet(1200, [(x, y) for y in (200, 600, 1000) for x in (200, 600, 1000)])
        blue = np.ascontiguousarray(green[..., [0, 2, 1]])                                  # the same sheet on a blue screen
        self.assertEqual(chroma.detect_key(green)[0], "green")
        self.assertEqual(chroma.detect_key(blue)[0], "blue")
        self.assertEqual(chroma.detect_key(np.full((300, 300, 3), 128, np.uint8), asked="blue")[0], "blue")     # no screen at all: the colour that was asked, and the sheet check blocks it
        self.assertEqual(pl.cfg_for({"key_colour": "blue"}, EngineConfig()).chroma, "blue")
        self.assertEqual(pl.cfg_for({}, EngineConfig()).chroma, "green")
        os.environ["MIRSAL_EXPORT_DIR"] = str(self.tmp / "exp")
        try:
            self.files["png"] = png_bytes(blue)
            gid = self._stills_ready("blue blob")
            res = self.req("GET", f"/api/generations/{gid}")[1]
            self.assertEqual(res["key_colour"], "blue")
            self.assertGreaterEqual(sum(1 for s in res["stickers"] if s["status"] == "READY"), 7)       # keyed, not refused by the green check
            self.assertFalse([c for c in res["verify"]["sheet"] if not c["ok"] and c["name"] == "background_is_key"])
            task = _tasks.read_task(self.out, res["task_id"])
            self.assertEqual((task["key_colour"], task.get("key_detected")), ("blue", True))           # green was asked, the model returned blue
            imgs = export.sync(self.out, gid)
            self.assertIn("KEY: blue (the sheet came back blue although green was asked", (imgs / "prompts.txt").read_text(encoding="utf-8"))
            for i in range(1, 10):                                                                      # the video sheet follows: a blue screen, and the video prompt says nothing else
                self.req("POST", f"/api/generations/{gid}/review", {"gate": "still", "decision": "APPROVE", "index": i})
            self.assertEqual(self.req("POST", f"/api/generations/{gid}/video_sheet")[0], 200)
            vs = np.asarray(Image.open(self.out / f"G{gid:03d}" / "video_sheet" / "A1" / "sheet.png").convert("RGB"))
            self.assertEqual(vs[3, 3].tolist(), [0, 0, 255])
            self.assertNotIn("green", self.c.video_prompt_for(gid, "A1").lower())
            # a green sheet leaves no mark at all
            self.files["png"] = png_bytes(green)
            gid2 = self._stills_ready("green blob")
            res2 = self.req("GET", f"/api/generations/{gid2}")[1]
            self.assertNotIn("key_colour", res2)
            task2 = _tasks.read_task(self.out, res2["task_id"])
            self.assertNotIn("key_colour", task2)
            self.assertNotIn("KEY:", (export.sync(self.out, gid2) / "prompts.txt").read_text(encoding="utf-8"))
        finally:
            os.environ.pop("MIRSAL_EXPORT_DIR", None)

    def test_the_export_root_is_inside_the_repo_for_the_project_data_only(self):
        from mirsal import export
        from mirsal.paths import PROJECT, REPO
        os.environ.pop("MIRSAL_EXPORT_DIR", None)
        self.assertEqual(export.export_root(PROJECT / "out"), REPO / "generated")      # visible in the repo, next to inputs/ and mirsal/
        self.assertEqual(export.export_root(self.out), self.out / "export")            # a copy of the data or a test never writes into the repo
        self.assertIn("generated/", (REPO / ".gitignore").read_text(encoding="utf-8").splitlines())
        os.environ["MIRSAL_EXPORT_DIR"] = str(self.tmp / "mine")
        try:
            self.assertEqual(export.export_root(PROJECT / "out"), self.tmp / "mine")
        finally:
            os.environ.pop("MIRSAL_EXPORT_DIR", None)

    def test_the_gap_is_a_slider_and_loop_is_a_choice(self):
        gid = self._stills_ready()
        # the preview sheet follows the gap: a fuller slot means bigger stickers on the same canvas
        import io
        def ink(fill):
            h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
            h.request("GET", f"/api/generations/{gid}/sheet_preview?fill={fill}&px=300"); r = h.getresponse(); data = r.read(); h.close()
            self.assertEqual((r.status, r.getheader("Content-Type")), (200, "image/png"))
            im = np.asarray(Image.open(io.BytesIO(data)).convert("RGB")).astype(int)
            self.assertEqual(max(im.shape[:2]), 300)
            return float(((np.abs(im - np.array([0, 255, 0])).max(-1)) > 40).mean())
        self.assertGreater(ink(0.9), ink(0.5) * 1.5)
        # an old sheet built at the default gap is rejected (not deleted) and rebuilt when the slider moved; Loop on brings the wording and the end image back
        for i in range(1, 10):
            self.assertEqual(self.req("POST", f"/api/generations/{gid}/review", {"gate": "still", "decision": "APPROVE", "index": i})[0], 200)
        self.assertEqual(self.req("POST", f"/api/generations/{gid}/video_sheet")[0], 200)
        s, v = self.req("POST", "/api/live/video", {"generation": gid, "slot_fill": 0.6, "loop": True})
        self.assertEqual(s, 200, v)
        st = self.req("GET", f"/api/generations/{gid}")[1]
        sheets = {x["id"]: x for x in st["video_sheets"]}
        self.assertEqual((sheets["A1"]["status"], sheets["A2"]["slot_fill"]), ("REJECTED", 0.6))
        self.assertEqual(sheets["A1"]["slot_fill"], self.c.cfg.slot_fill)
        create = self.until(lambda: next((c for c in self.cli.calls if c[:3] == ["generate", "create", "kling3_0"]), None), "the Kling create call")      # the job runs in a thread
        self.assertEqual(create[create.index("--start-image") + 1], create[create.index("--end-image") + 1])
        self.assertIn("seamless loop", create[create.index("--prompt") + 1])
        # the plan keeps the choice too: Loop off is the default in the saved video prompt
        task = self.req("GET", "/api/tasks")[1]["tasks"][0]
        self.assertFalse(task["plan"]["slots"]["loop"])
        self.assertNotIn("loop", task["plan"]["video_prompt"].lower())

    def test_from_a_request_to_a_sliced_kling_animation(self):
        s, j = self.req("POST", "/api/live/sheet", {"prompt": "blob", "grid": "3x3", "style_id": "toon_shade", "outline": 12})
        self.assertEqual(s, 200, j)
        self.assertEqual((j["job"], j["estimate"], j["model"]), ("J001", 2.0, "nano_banana_flash"))
        task_id = j["task"]
        # the job finishes, the unchanged stills run starts by itself and the job points at the generation
        job = self.until(lambda: (lambda x: x if x.get("generation") and x["status"] == "DONE" else None)(self.req("GET", "/api/jobs/J001")[1]), "sheet job done")
        gid = int(job["generation"][1:])
        st = self.until(lambda: (lambda x: x if x["stage"] == "sliced" and not x["busy"] else None)(self.req("GET", f"/api/generations/{gid}")[1]), "stills")
        self.assertEqual(st["template_version"], prompter.TEMPLATE_VERSION)
        self.assertIn(styles.PHRASE["toon_shade"], st["sheet_prompt"])
        self.assertEqual(sum(1 for t in st["stickers"] if t["status"] == "READY"), 9)
        self.assertEqual(self.req("GET", f"/api/tasks/{task_id}")[1]["external_task_id"], "fake-job-1")        # the Higgsfield id, stored before waiting
        # no video sheet yet and no approval: nothing may be sent to Kling
        s, j = self.req("POST", "/api/live/video", {"generation": gid, "sheet": "A1"})
        self.assertEqual(s, 404)
        for i in range(1, 10):
            s, j = self.req("POST", f"/api/generations/{gid}/review", {"gate": "still", "decision": "APPROVE", "index": i})
            self.assertEqual(s, 200, j)
        s, j = self.req("POST", f"/api/generations/{gid}/video_sheet")
        self.assertEqual(s, 200, j)
        s, j = self.req("POST", "/api/live/video", {"generation": gid, "sheet": "A1"})
        self.assertEqual(s, 409, j)                                                                            # G3 not approved: a human decides first
        self.assertIn("G3", j["error"])
        self.assertEqual(self.req("POST", f"/api/generations/{gid}/review", {"gate": "video_sheet", "decision": "APPROVE", "index": "A1"})[0], 200)
        base = self.out / st["generation_id"]
        entry = next(v for v in self.req("GET", f"/api/generations/{gid}")[1]["video_sheets"] if v["id"] == "A1")
        mp4 = self.tmp / "kling.mp4"
        synth.make_layout_video(mp4, np.array(Image.open(base / entry["file"]).convert("RGB")), json.loads((base / entry["layout"]).read_text()), size=600, frames=45)
        self.files["mp4"] = mp4.read_bytes()
        self.cli.cost = 4.5
        s, j = self.req("POST", "/api/live/video", {"generation": gid, "sheet": "A1", "model": "kling3_0", "options": {"mode": "pro"}})
        self.assertEqual((s, j["estimate"]), (200, 4.5), j)
        vjob = self.until(lambda: (lambda x: x if x["status"] in ("DONE", "FAILED") else None)(self.req("GET", f"/api/jobs/{j['job']}")[1]), "video job")
        self.assertEqual(vjob["status"], "DONE", vjob)
        create = [c for c in self.cli.calls if c[:3] == ["generate", "create", "kling3_0"]][0]
        self.assertEqual(create[create.index("--mode") + 1], "pro")
        self.assertNotIn("--end-image", create)                                                                     # Loop is off by default: no forced return to the first pose
        self.assertNotIn("loop", create[create.index("--prompt") + 1].lower())                                      # and no loop wording that makes the stickers bounce
        self.assertIn("1. ", [l for l in create[create.index("--prompt") + 1].splitlines() if l[:3] == "1. "][0])  # per-character motion lines
        final = self.until(lambda: (lambda x: x if next(v for v in x["video_sheets"] if v["id"] == "A1")["status"] in ("SLICED", "VIDEO_BLOCKED") and not x["busy"] else None)(
            self.req("GET", f"/api/generations/{gid}")[1]), "slicing")
        self.assertEqual(next(v for v in final["video_sheets"] if v["id"] == "A1")["status"], "SLICED")
        # a light preview of the returned video exists for the browser, next to the full-size original
        sheet = next(v for v in final["video_sheets"] if v["id"] == "A1")
        self.assertTrue((self.out / st["generation_id"] / sheet["video"]).is_file())
        self.assertTrue(sheet.get("preview") and (self.out / st["generation_id"] / sheet["preview"]).is_file())
        # changing the edge afterwards never loses the video: it is re-applied to the stored video, no new job and no credits
        jobs_before = len(self.req("GET", "/api/jobs")[1]["jobs"])
        s, r = self.req("POST", f"/api/generations/{gid}/appearance", {"outline": 6, "erode": 1, "reslice": True})
        self.assertEqual((s, r["outline_px"], r["erode_px"], r.get("resliced")), (200, 6, 1, True), r)
        again = self.until(lambda: (lambda x: x if not x["busy"] and all(t["anim_status"] in ("READY", "FAILED") for t in x["stickers"]) else None)(
            self.req("GET", f"/api/generations/{gid}")[1]), "re-applied animations")
        self.assertEqual(next(v for v in again["video_sheets"] if v["id"] == "A1")["status"], "SLICED")
        notready = [(t["index"], t["anim_status"], t.get("anim_reason")) for t in again["stickers"] if t["anim_status"] != "READY"]
        self.assertGreaterEqual(9 - len(notready), 7, notready)                       # a stroke can tip a borderline synthetic clip over a Python check; never more than that
        self.assertTrue(all(st_ == "FAILED" and why for _, st_, why in notready), notready)   # and every one that is not ready says which check
        self.assertFalse([t for t in again["stickers"] if t["anim_status"] == "STALE"])
        self.assertEqual(len(self.req("GET", "/api/jobs")[1]["jobs"]), jobs_before)                                  # nothing was sent to Higgsfield again
        s, r2 = self.req("POST", f"/api/generations/{gid}/appearance", {"outline": 6, "erode": 1, "reslice": True})   # the same edge again is a cache hit
        again2 = self.until(lambda: (lambda x: x if not x["busy"] and not any(t["anim_status"] in ("STALE", "PROCESSING") for t in x["stickers"]) else None)(
            self.req("GET", f"/api/generations/{gid}")[1]), "cached re-apply")
        self.assertTrue(all((t.get("anim_metrics") or {}).get("cache") == "hit" for t in again2["stickers"] if t["anim_status"] == "READY"))
        # properly named folders for copy and paste: images/img-NNN-subject and videos/vid-NNN-subject, every stroke/trim setting its own snapshot (nothing is deleted)
        import re
        imgs, vids = self.out / "export" / "images" / "img-001-blob", self.out / "export" / "videos" / "vid-001-blob"
        stick = lambda: [p.name for p in imgs.iterdir() if re.fullmatch(r"img-001-blob-s\d-[a-z_0-9]+-stroke\d+px-trim\d+px-\d{8}\.png", p.name)] if imgs.is_dir() else []
        self.until(lambda: any("stroke6px-trim1px" in n for n in stick()), "the new stroke snapshot is mirrored")
        names = sorted(p.name for p in imgs.iterdir())
        self.assertTrue(any(re.fullmatch(r"img-001-blob-sheet-nano_banana_flash-2k-\d{8}\.png", n) for n in names), names)
        self.assertGreaterEqual(len(stick()), 18)                                                            # the first edge and the second: both kept
        self.assertTrue(any("stroke6px" not in n for n in stick()))
        self.assertTrue((imgs / "prompts.txt").is_file())
        vnames = sorted(p.name for p in vids.iterdir())
        self.assertTrue(any(re.fullmatch(r"vid-001-blob-video-kling3_0-pro-3s-\d{8}\.mp4", n) for n in vnames), vnames)
        self.assertTrue(any(re.fullmatch(r"vid-001-blob-videosheet-gap\d+-\d{8}\.png", n) for n in vnames), vnames)
        self.assertTrue(any(re.fullmatch(r"vid-001-blob-s\d-[a-z_0-9]+-stroke\d+px-trim\d+px-\d{8}\.webm", n) for n in vnames), vnames)
        h = self.req("GET", "/api/history?limit=1")[1]
        self.assertEqual((len(h["items"]), h["items"][0]["generation_id"], h["items"][0]["animated"], h["more"] is False), (1, st["generation_id"], sum(1 for t in again2["stickers"] if t["anim_status"] == "READY"), True))
        u = self.req("GET", "/api/usage")[1]
        self.assertEqual((u["credits_spent"], u["runs"][0]["generation"]), (6.5, st["generation_id"]))
        self.assertEqual(sorted(m["credits"] for m in u["by_model"]), [2.0, 4.5])


if __name__ == "__main__":
    unittest.main()
