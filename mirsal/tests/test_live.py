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
        self.assertEqual(p["template_version"], 2)
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
        create = next(c for c in self.cli.calls if c[:3] == ["generate", "create", "kling3_0"])
        self.assertEqual(create[create.index("--mode") + 1], "pro")                          # always pro: 1440 px, never std
        prompt = create[create.index("--prompt") + 1]
        self.assertIn("wide range of emotions", prompt)
        self.assertIn("highly expressive", prompt)
        self.assertEqual(self.req("POST", "/api/live/cost", {"kind": "video", "model": "kling3_0", "options": {"mode": "std"}})[0], 400)   # std is not offered any more

    def test_from_a_request_to_a_sliced_kling_animation(self):
        s, j = self.req("POST", "/api/live/sheet", {"prompt": "blob", "grid": "3x3", "style_id": "toon_shade", "outline": 12})
        self.assertEqual(s, 200, j)
        self.assertEqual((j["job"], j["estimate"], j["model"]), ("J001", 2.0, "nano_banana_flash"))
        task_id = j["task"]
        # the job finishes, the unchanged stills run starts by itself and the job points at the generation
        job = self.until(lambda: (lambda x: x if x.get("generation") and x["status"] == "DONE" else None)(self.req("GET", "/api/jobs/J001")[1]), "sheet job done")
        gid = int(job["generation"][1:])
        st = self.until(lambda: (lambda x: x if x["stage"] == "sliced" and not x["busy"] else None)(self.req("GET", f"/api/generations/{gid}")[1]), "stills")
        self.assertEqual(st["template_version"], 2)
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
        self.assertEqual(create[create.index("--start-image") + 1], create[create.index("--end-image") + 1])       # start = end image: a loop
        self.assertIn("1. ", [l for l in create[create.index("--prompt") + 1].splitlines() if l[:3] == "1. "][0])  # per-character motion lines
        final = self.until(lambda: (lambda x: x if next(v for v in x["video_sheets"] if v["id"] == "A1")["status"] in ("SLICED", "VIDEO_BLOCKED") and not x["busy"] else None)(
            self.req("GET", f"/api/generations/{gid}")[1]), "slicing")
        self.assertEqual(next(v for v in final["video_sheets"] if v["id"] == "A1")["status"], "SLICED")
        u = self.req("GET", "/api/usage")[1]
        self.assertEqual((u["credits_spent"], u["runs"][0]["generation"]), (6.5, st["generation_id"]))
        self.assertEqual(sorted(m["credits"] for m in u["by_model"]), [2.0, 4.5])


if __name__ == "__main__":
    unittest.main()
