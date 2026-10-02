"""The chat through the REAL console server on synthetic prepared sheets: sessions, a turn in the background, live cards, memory, settings.
No provider (Higgsfield is reported unavailable), no language model (no key, no local server): everything is rules and the file store."""
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

from mirsal.generation import higgsfield
from mirsal.console.server import serve
from mirsal.engine.config import EngineConfig
from tests.test_console import build_inputs


class ChatServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = {k: os.environ.get(k) for k in ("MIRSAL_AGENT_PROVIDER", "MIRSAL_LLM_PROVIDER", "OPENAI_API_KEY")}
        os.environ["MIRSAL_AGENT_PROVIDER"] = "openai"          # no key + openai = no model: the rules decide everything
        os.environ["MIRSAL_LLM_PROVIDER"] = "openai"
        os.environ.pop("OPENAI_API_KEY", None)
        from mirsal.services import llm
        cls._loaded = llm._ENV_LOADED
        llm._ENV_LOADED = True
        cls.patch = mock.patch.object(higgsfield, "available", lambda: False)
        cls.patch.start()
        cls.tmp = Path(tempfile.mkdtemp())
        build_inputs(cls.tmp / "in")
        cls.srv, cls.c = serve(cls.tmp / "out", cls.tmp / "in", 0, cfg=EngineConfig(min_sheet_px=256), block=False)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.c.release_writer()
        cls.patch.stop()
        from mirsal.services import llm
        llm._ENV_LOADED = cls._loaded
        for k, v in cls.env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def req(self, method, path, body=None):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h.request(method, path, json.dumps(body) if body is not None else None, {"Content-Type": "application/json"})
        r = h.getresponse()
        raw = r.read()
        h.close()
        try:
            return r.status, json.loads(raw)
        except ValueError:
            return r.status, raw

    def wait(self, sid, pred, timeout=60):
        end = time.time() + timeout
        while time.time() < end:
            s, j = self.req("GET", f"/api/chat/sessions/{sid}")
            if s == 200 and pred(j):
                return j
            time.sleep(0.2)
        self.fail("timeout: " + json.dumps(j)[:600])

    def test_a_full_conversation(self):
        s, sess = self.req("POST", "/api/chat/sessions", {"settings": {"ai": False}})
        self.assertEqual(s, 200)
        sid = sess["id"]
        self.assertEqual(sess["settings"]["ai"], False)

        # 1. a request: starts in the background, answers at once
        s, r = self.req("POST", f"/api/chat/sessions/{sid}/messages", {"text": "create a blob for school"})
        self.assertEqual((s, r["id"]), (202, sid))
        j = self.wait(sid, lambda j: not j["working"] and j["messages"][-1]["role"] == "assistant")
        last = j["messages"][-1]
        self.assertEqual(last["status"], "done")
        card = next(c for c in last["cards"] if c["type"] == "generation")
        self.assertEqual(card["generation"], "G001")
        self.assertEqual([s_["kind"] for s_ in last["steps"]][0], "task")
        self.assertEqual(last["steps"][-1]["kind"], "final")

        # 2. the stickers appear on the card as the engine finishes them (live data, with file urls)
        j = self.wait(sid, lambda j: len([x for x in (j["messages"][-1]["cards"][0].get("data") or {}).get("stickers", []) if x["status"] == "READY"]) >= 3)
        st = j["messages"][-1]["cards"][0]["data"]["stickers"]
        png = next(x["png"] for x in st if x["png"])
        self.assertEqual(self.req("GET", png)[0], 200)

        # 3. memory: feedback about stickers of that pass is stored on the subject
        self.c.wait_jobs()
        s, r = self.req("POST", f"/api/chat/sessions/{sid}/messages", {"text": "I like 2 and 3 but not 4"})
        j = self.wait(sid, lambda j: not j["working"])
        pass_ = j["subjects"][0]["passes"][0]
        self.assertEqual((pass_["liked"], pass_["disliked"]), (["G001/S2", "G001/S3"], ["G001/S4"]))
        self.assertIn("liked S2, S3", j["summary_text"])
        self.assertIn("noted", j["messages"][-1]["text"].lower())

        # 4. an answer from metadata only, no generation
        s, r = self.req("POST", f"/api/chat/sessions/{sid}/messages", {"text": "which one is number 2?"})
        j = self.wait(sid, lambda j: not j["working"])
        self.assertIn("G001/S2", j["messages"][-1]["text"])
        self.assertEqual(len(self.req("GET", "/api/generations")[1]["summary"] if "summary" in self.req("GET", "/api/generations")[1] else []) or 1, 1)

        # 5. settings through the minimal settings route and through chat
        s, r = self.req("POST", f"/api/chat/sessions/{sid}/settings", {"grid": "2x2", "ask_before_spending": False, "bogus": 1})
        self.assertEqual((r["settings"]["grid"], r["settings"]["ask_before_spending"], "bogus" in r["settings"]), ("2x2", False, False))

        # 6. the list and the resume
        s, lst = self.req("GET", "/api/chat/sessions")
        self.assertIn(sid, [x["id"] for x in lst["sessions"]])
        s, again = self.req("GET", f"/api/chat/sessions/{sid}")
        self.assertEqual(len(again["interactions"]), 3)

    def test_a_second_message_while_one_runs_gets_409(self):
        s, sess = self.req("POST", "/api/chat/sessions", {"settings": {"ai": False}})
        sid = sess["id"]
        store, tools, agent, _ = self.c.chat_parts()
        turn = agent.prepare(sid, "hello", [], None)                      # the first turn holds the session
        try:
            s, r = self.req("POST", f"/api/chat/sessions/{sid}/messages", {"text": "hello again"})
            self.assertEqual(s, 409)
        finally:
            agent.execute(turn)
        s, r = self.req("POST", f"/api/chat/sessions/{sid}/messages", {"text": "hello again"})
        self.assertEqual(s, 202)
        self.wait(sid, lambda j: not j["working"])

    def test_unknown_session_and_bad_input(self):
        self.assertEqual(self.req("GET", "/api/chat/sessions/S999")[0], 404)
        self.assertEqual(self.req("GET", "/api/chat/sessions/../../etc")[0] in (400, 404), True)
        s, sess = self.req("POST", "/api/chat/sessions", {})
        self.assertEqual(self.req("POST", f"/api/chat/sessions/{sess['id']}/messages", {"text": "   "})[0], 400)

    def test_agent_status_reports_the_models(self):
        s, j = self.req("GET", "/api/chat/agent")
        self.assertEqual(s, 200)
        self.assertIn("agent", j)
        self.assertIn("vision", j)
        s, h = self.req("GET", "/api/health")
        self.assertEqual(s, 200)
        self.assertIn("database", h)


if __name__ == "__main__":
    unittest.main()
