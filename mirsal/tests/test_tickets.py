"""Tickets (flow/tickets.py, docs/tickets_plan.md): automatic tickets fold by fingerprint, a Report gathers what happened around its target, answers and
status, the local model's draft validated strictly (a bad or missing one keeps the preset questions), and the native routes on the FastAPI server: a server
error opens a ticket, the owner sees and closes them. No provider and no real model: a fake answer stands in."""
import http.client
import json
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from mirsal.flow import pipeline as pl
from mirsal.flow import tickets as tk


class TicketEngineTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def test_the_same_failure_folds_into_one_ticket_whatever_its_numbers_and_paths(self):
        a = tk.open_auto(self.out, source="job", issue="stuck_job", what="video job failed: J041 timed out at /Users/me/x/out/G104", where="video/kling", draft=False)
        b = tk.open_auto(self.out, source="job", issue="stuck_job", what="video job failed: J052 timed out at /Users/me/x/out/G105", where="video/kling", draft=False)
        self.assertEqual(a["id"], b["id"])
        self.assertEqual(b["count"], 2)
        self.assertNotIn("/Users/me", b["what_happened"], "a path on this machine never leaves it")
        c = tk.open_auto(self.out, source="crash", issue="crash", what="KeyError: 'x'", where="GET /api/history", draft=False)
        self.assertNotEqual(c["id"], a["id"])
        self.assertEqual([q["text"] for q in a["questions"]], [q for q, _ in tk.PRESET["stuck_job"]], "the preset questions are there before any model")
        tk.set_status(self.out, a["id"], "fixed", "abc123")
        d = tk.open_auto(self.out, source="job", issue="stuck_job", what="video job failed: J060 timed out", where="video/kling", draft=False)
        self.assertNotEqual(d["id"], a["id"], "a fixed ticket is not reopened: the same failure after a fix is a new ticket")

    def test_a_report_keeps_the_persons_words_and_what_happened_around_the_target(self):
        d = self.out / "G007"
        (d / "slices").mkdir(parents=True)
        (d / "result.json").write_text(json.dumps({"generation_id": "G007", "number": 7, "prompt": "cat", "stage": "sliced", "error": None, "grid": [2, 2],
                                                   "source": {"subject": "cat"}, "stickers": [{"index": 3, "key": "nap", "status": "FAILED", "reason": "blank_cell",
                                                                                               "review": {}, "history": []}], "reviews": {}, "video_sheets": []}))
        (d / "events.jsonl").write_text("\n".join(json.dumps({"stage": f"s{i}"}) for i in range(20)))
        t = tk.report(self.out, user="U1", text="S3 is empty", target={"kind": "sticker", "id": "G007", "sticker": "S3"}, draft=False)
        self.assertEqual((t["intent"], t["what_happened"], t["user"]), ("S3 is empty", "G007/S3: FAILED (blank_cell)", "U1"))
        self.assertEqual(len(t["context"]["last_events"]), 12)
        self.assertEqual(t["context"]["sticker"]["reason"], "blank_cell")

    def test_answers_finish_the_questions_and_a_wrong_choice_is_refused(self):
        t = tk.report(self.out, user="U1", text="slow", draft=False)
        with self.assertRaises(ValueError):
            tk.answer(self.out, t["id"], 0, choice="not a choice")
        t = tk.answer(self.out, t["id"], 0, choice=t["questions"][0]["choices"][0])
        self.assertEqual(t["status"], "answered", "every question answered")
        self.assertEqual([r["id"] for r in tk.listing(self.out, user="U1")], [t["id"]])
        self.assertEqual(tk.listing(self.out, user="U2"), [])

    def test_an_answer_to_the_shown_preset_counts_after_the_draft_replaced_the_questions(self):
        """Haitham's live T001 (2026-10-05): the page showed the preset "How bad is it?", the local model's draft replaced the questions a moment later,
        and the click was refused with "that is not one of the choices". The answer now names its question and is kept against it."""
        from mirsal.services import llm
        t = tk.report(self.out, user="local", text="most of them are rejected by python", draft=False)
        shown = t["questions"][0]
        good = json.dumps({"issue": "wrong_result", "summary": "Most stickers rejected", "proposed_fix": "Check the cut",
                           "questions": [{"text": "Which check rejected them?", "choices": ["the cut", "the size"]}]})
        with mock.patch.object(llm, "provider", lambda: "local"), mock.patch.object(llm, "complete", lambda *a, **k: (good, {"model": "fake-local"})):
            tk.draft(self.out, t["id"])
        a = tk.answer(self.out, t["id"], 0, shown["choices"][0], user="local", question_text=shown["text"])
        self.assertEqual(a["answers"][0]["question_text"], shown["text"], "kept against the question that was shown")
        self.assertEqual(a["answers"][0]["choice"], shown["choices"][0])
        self.assertEqual(a["status"], "open", "the model's own question is still unanswered")
        b = tk.answer(self.out, t["id"], 0, "the cut", user="local", question_text="Which check rejected them?")
        self.assertEqual(b["status"], "answered")
        with self.assertRaises(ValueError) as e:
            tk.answer(self.out, t["id"], 0, shown["choices"][0], user="local")      # an old page that does not send the question text
        self.assertIn("changed while you were reading", str(e.exception))

    def test_the_local_models_draft_is_validated_and_a_bad_one_keeps_the_presets(self):
        from mirsal.services import llm
        good = json.dumps({"issue": "slow", "summary": "Animating takes minutes", "proposed_fix": "Cache the keyed frames",
                           "questions": [{"text": "Which step was slow?", "choices": ["the sheet", "the video"]}]})
        t = tk.report(self.out, user="U1", text="it takes forever", draft=False)
        with mock.patch.object(llm, "provider", lambda: "local"), mock.patch.object(llm, "complete", lambda *a, **k: (good, {"model": "fake-local"})):
            t = tk.draft(self.out, t["id"])
        self.assertEqual((t["issue"], t["drafted_by"], t["questions"][0]["text"]), ("slow", "fake-local", "Which step was slow?"))
        u = tk.report(self.out, user="U1", text="odd", draft=False)
        with mock.patch.object(llm, "provider", lambda: "local"), mock.patch.object(llm, "complete", lambda *a, **k: ('{"issue": "made-up"}', {})):
            u = tk.draft(self.out, u["id"])
        self.assertEqual((u["issue"], u["drafted_by"]), ("other", "preset"))
        self.assertTrue(u["draft_error"])
        self.assertEqual(len(u["questions"]), len(tk.PRESET["other"]))


class TicketRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from mirsal.console.server import serve
        cls.tmp = Path(tempfile.mkdtemp())
        cls.srv, cls.c = serve(cls.tmp / "out", cls.tmp / "in", 0, block=False, stdlib=False)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.c.release_writer()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def req(self, method, path, body=None, headers=None):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        h.request(method, path, json.dumps(body) if body is not None else None, {"Content-Type": "application/json", **(headers or {})})
        r = h.getresponse()
        raw = r.read()
        h.close()
        return r.status, json.loads(raw), r

    def test_report_list_answer_close_and_the_servers_own_error_shapes(self):
        code, t, r = self.req("POST", "/api/tickets", {"text": "the button does nothing", "target": {"kind": "other"}})
        self.assertEqual(code, 201, t)
        self.assertTrue(r.getheader("X-API-Version") and r.getheader("X-Request-Id"))
        self.assertIn(t["id"], [x["id"] for x in self.req("GET", "/api/tickets")[1]["tickets"]])
        code, j, _ = self.req("POST", f"/api/tickets/{t['id']}/answer", {"question": 0, "choice": t["questions"][0]["choices"][1]})
        self.assertEqual(code, 200, j)
        code, j, _ = self.req("POST", f"/api/v1/tickets/{t['id']}/status", {"status": "fixed", "fixed_by": "abc123"})
        self.assertEqual((code, j["status"], j["fixed_by"]), (200, "fixed", "abc123"))
        code, j, _ = self.req("POST", "/api/tickets", {"text": ""})
        self.assertEqual(code, 400, "a body that does not match answers 400 in this server's words, never FastAPI's 422")
        self.assertTrue(j["error"].startswith("bad request"))
        self.assertEqual(self.req("GET", "/api/tickets/T999")[0], 404)
        self.assertEqual(self.req("GET", "/api/tickets", headers={"Host": "evil.example"})[:2], (403, {"error": "unexpected Host header"}))

    def test_a_server_error_opens_a_crash_ticket(self):
        with mock.patch.object(pl, "history", side_effect=RuntimeError("boom at /Users/me/secret/out")):
            code, j, _ = self.req("GET", "/api/history")
        self.assertEqual(code, 500)
        crash = [x for x in self.req("GET", "/api/tickets")[1]["tickets"] if x["source"] == "crash"]
        self.assertTrue(crash)
        full = self.req("GET", f"/api/tickets/{crash[0]['id']}")[1]
        self.assertIn("RuntimeError: boom", full["what_happened"])
        self.assertNotIn("/Users/me", full["what_happened"])
        self.assertEqual(full["context"]["where"], "GET /api/history")
        self.assertEqual(full["context"]["request_id"], j["request_id"])
