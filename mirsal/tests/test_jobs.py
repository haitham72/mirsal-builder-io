"""Phase 2 S2: jobs as files (create/claim/done/fail/requeue), the ticket-first rule, the ledger,
the prompt lab (offline) and the slot reviewer. A fake file stands in for the operator's download."""
import http.client
import json
import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from mirsal.generation import jobs
from mirsal.console.server import serve
from mirsal.engine.config import EngineConfig


class JobsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "in" / "Images_gen").mkdir(parents=True)
        (self.tmp / "in" / "videos_gen").mkdir(parents=True)
        self.out = self.tmp / "out"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fake_operator_flow(self):
        j = jobs.create(self.out, "sheet", task="011", request={"prompt": "falcon"})
        self.assertEqual((j["id"], j["status"], j["provider"]), ("J001", "REQUESTED", "higgsfield-cli"))
        with self.assertRaises(jobs.JobError):  # done before claim
            jobs.done(self.out, "J001", __file__, "m")
        j = jobs.claim(self.out, "J001", "higgs-123")
        self.assertEqual((j["status"], j["external_task_id"]), ("CLAIMED", "higgs-123"))
        with self.assertRaises(jobs.JobError):  # claim twice
            jobs.claim(self.out, "J001", "higgs-123")
        fake = self.tmp / "sheet.png"
        fake.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 100)
        j = jobs.done(self.out, "J001", str(fake), "higgs-img-v1", cost=2.5)
        self.assertEqual(j["status"], "DONE")
        self.assertTrue((self.out / "jobs" / "J001" / "result.png").is_file())
        self.assertEqual(j["result"]["sha256"], jobs.read(self.out, "J001")["result"]["sha256"])
        self.assertEqual([x["status"] for x in jobs.list(self.out)], ["DONE"])
        self.assertEqual(jobs.list(self.out, "REQUESTED"), [])

    def test_claim_stores_the_ticket_first(self):
        """A crashed operator re-run resumes by ticket instead of paying twice (rule 10)."""
        from mirsal.generation import tasks as _t
        t = _t.reserve(self.out, self.tmp / "in", "falcon dancing")
        j = jobs.create(self.out, "sheet", task=t["id"], request={"prompt": "falcon"})
        jobs.claim(self.out, j["id"], "higgs-999")
        back = _t.read_task(self.out, t["id"])
        self.assertEqual(back["external_task_id"], "higgs-999")

    def test_fail_and_requeue(self):
        j = jobs.create(self.out, "video", request={})
        jobs.fail(self.out, j["id"], "provider 500")
        self.assertEqual(jobs.read(self.out, j["id"])["status"], "FAILED")
        jobs.requeue(self.out, j["id"])
        self.assertEqual(jobs.read(self.out, j["id"])["status"], "REQUESTED")
        with self.assertRaises(jobs.JobError):  # nothing to re-queue
            jobs.requeue(self.out, j["id"])

    def test_stale_jobs_show_timeout(self):
        j = jobs.create(self.out, "sheet", request={})
        p = self.out / "jobs" / f"{j['id']}.json"
        old = dict(json.loads(p.read_text(encoding="utf-8")))
        old["created_at"] -= jobs.timeout_s() + 10
        p.write_text(json.dumps(old), encoding="utf-8")
        self.assertEqual(jobs.read(self.out, j["id"])["status"], "TIMEOUT")
        jobs.requeue(self.out, j["id"])
        self.assertEqual(jobs.read(self.out, j["id"])["status"], "REQUESTED")

    def test_every_call_is_a_ledger_line(self):
        j = jobs.create(self.out, "sheet", request={})
        jobs.claim(self.out, j["id"], "t")
        fake = self.tmp / "s.png"
        fake.write_bytes(b"data")
        jobs.done(self.out, j["id"], str(fake), "m")
        j2 = jobs.create(self.out, "video", request={})
        jobs.fail(self.out, j2["id"], "boom")
        lines = (self.out / "model_calls.jsonl").read_text(encoding="utf-8").splitlines()
        kinds = [json.loads(l)["kind"] for l in lines]
        self.assertEqual(kinds, ["IMAGE_SHEET", "VIDEO"])
        self.assertTrue(all("bytes" not in l for l in lines))

    def test_api_round_trip(self):
        srv, _ = serve(self.out, self.tmp / "in", 0, cfg=EngineConfig(), block=False)
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            def req(method, path, body=None):
                h = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
                h.request(method, path, json.dumps(body) if body is not None else None,
                          {"Content-Type": "application/json"})
                r = h.getresponse()
                raw = r.read()
                h.close()
                try:
                    return r.status, json.loads(raw)
                except ValueError:
                    return r.status, raw
            s, j = req("POST", "/api/jobs", {"kind": "sheet", "request": {"prompt": "x"}})
            self.assertEqual((s, j["status"]), (200, "REQUESTED"))
            jid = j["id"]
            self.assertEqual(req("GET", "/api/jobs")[0], 200)
            s, _ = req("POST", f"/api/jobs/{jid}/claim", {"ticket": "t1"})
            self.assertEqual(s, 200)
            s, _ = req("POST", f"/api/jobs/{jid}/claim", {"ticket": "t1"})
            self.assertEqual(s, 409)  # claim twice is refused
            fake = self.tmp / "r.png"
            fake.write_bytes(b"png")
            s, done = req("POST", f"/api/jobs/{jid}/done", {"file": str(fake), "model": "m"})
            self.assertEqual((s, done["status"]), (200, "DONE"))
            self.assertEqual(req("GET", f"/api/jobs/{jid}")[1]["status"], "DONE")
            s, _ = req("POST", "/api/jobs", {"kind": "poster"})
            self.assertEqual(s, 400)
        finally:
            srv.shutdown()

    def test_prompt_lab_offline(self):
        from mirsal.cli import main
        self.assertEqual(main(["prompt", "lab"]), 0)
        self.assertEqual(main(["prompt", "green frog with big eyes", "--grid", "2x2"]), 0)
        self.assertEqual(main(["prompt", ""]), 1)

    def test_slot_reviewer(self):
        from mirsal.generation import expander
        from mirsal.services import llm
        key, loaded = os.environ.pop("OPENAI_API_KEY", None), llm._ENV_LOADED
        prov = os.environ.get("MIRSAL_LLM_PROVIDER")
        os.environ["MIRSAL_LLM_PROVIDER"] = "openai"   # no key + openai = no backend, even when LM Studio runs here
        llm._ENV_LOADED = True  # never read the real key here: no live calls in tests
        try:
            good_slots = {"subject_description": "a falcon", "cells": [
                {"label": f"pose {i}", "tags": [f"falcon_pose_{i}"], "emoji": "\U0001F600"} for i in range(1, 10)]}
            self.assertTrue(expander.review(good_slots, 9, "falcon", "falcon")["ok"])  # lint passes, no call
            bad = dict(good_slots)
            bad["cells"] = [dict(c, label="same") for c in good_slots["cells"]]
            self.assertFalse(expander.review(bad, 9, "falcon", "falcon")["ok"])  # duplicates fail the lint
            fake_yes = lambda s, u, **k: (json.dumps({"ok": True, "problems": []}), {"model": "fake"})
            fake_no = lambda s, u, **k: (json.dumps({"ok": False, "problems": ["boring"]}), {"model": "fake"})
            self.assertTrue(expander.review(good_slots, 9, "falcon", "falcon", complete=fake_yes)["ok"])
            rv = expander.review(good_slots, 9, "falcon", "falcon", complete=fake_no)
            self.assertEqual((rv["ok"], rv["problems"]), (False, ["boring"]))
        finally:
            if key is not None:
                os.environ["OPENAI_API_KEY"] = key
            os.environ.pop("MIRSAL_LLM_PROVIDER", None) if prov is None else os.environ.__setitem__("MIRSAL_LLM_PROVIDER", prov)
            llm._ENV_LOADED = loaded


if __name__ == "__main__":
    unittest.main()
