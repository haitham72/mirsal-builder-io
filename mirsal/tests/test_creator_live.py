"""The agentic creator through the REAL console server: chat message -> plan -> one click -> fake Higgsfield sheet -> cut and check -> approve -> pack -> fake Telegram.
No provider, no language model, no network: the FakeCLI of tests/test_live.py and the fake Bot API of tests/fake_telegram.py."""
import http.client
import json
import os
import threading
import time
import unittest

from mirsal.console.server import serve
from mirsal.engine.config import EngineConfig
from mirsal.services import telegram as tg
from tests.fake_telegram import TOKEN, USER, FakeServer
from tests.test_live import Base, png_bytes
from tests.test_live import shape_sheet


class CreatorThroughTheServer(Base):
    def setUp(self):
        super().setUp()
        self.fake = FakeServer().__enter__()
        self.env = {k: os.environ.get(k) for k in ("MIRSAL_TELEGRAM_API", "MIRSAL_TELEGRAM_TOKEN", "MIRSAL_TELEGRAM_USER")}
        os.environ["MIRSAL_TELEGRAM_API"] = self.fake.url
        for k in ("MIRSAL_TELEGRAM_TOKEN", "MIRSAL_TELEGRAM_USER"):
            os.environ.pop(k, None)
        self.srv, self.c = serve(self.out, self.tmp / "in", 0, cfg=EngineConfig(), block=False)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.files["png"] = png_bytes(shape_sheet(1200, [(x, y) for y in (200, 600, 1000) for x in (200, 600, 1000)]))

    def tearDown(self):
        self.c.wait_jobs(90)
        self.c.wait_chat(30)
        self.srv.shutdown()
        self.fake.__exit__()
        for k, v in self.env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        super().tearDown()

    def req(self, method, path, body=None):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        h.request(method, path, json.dumps(body) if body is not None else None, {"Content-Type": "application/json"})
        r = h.getresponse()
        data = r.read()
        h.close()
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

    def say(self, sid, text="", action=None):
        s, r = self.req("POST", f"/api/chat/sessions/{sid}/messages", {"text": text, "action": action} if action else {"text": text})
        self.assertEqual(s, 202, r)
        return self.until(lambda: (lambda j: j if not j["working"] else None)(self.req("GET", f"/api/chat/sessions/{sid}")[1]), "the turn")

    def test_one_click_from_a_request_to_a_pack_on_telegram(self):
        tg.save_config(self.out, TOKEN, USER)
        s, sess = self.req("POST", "/api/chat/sessions", {"settings": {"ai": False}})
        sid = sess["id"]
        s, r = self.req("POST", f"/api/chat/sessions/{sid}/settings", {"creator": {"on": True, "scope": "images", "bypass": True}, "allow_vlm": False})
        self.assertEqual(r["settings"]["creator"], {"on": True, "scope": "images", "bypass": True})
        j = self.say(sid, "make me owl stickers")
        plan = j["messages"][-1]["cards"][0]
        self.assertEqual((plan["type"], plan["creator"]["scope"]), ("plan", "images"))
        self.assertEqual(len([c for c in self.cli.calls if c[:2] == ["generate", "create"]]), 0, "nothing is spent before the click")
        self.say(sid, action={"type": "confirm"})
        run = self.until(lambda: (lambda j: j["creator_run"] if (j.get("creator_run") or {}).get("status") in ("done", "stopped", "failed") else None)(
            self.req("GET", f"/api/chat/sessions/{sid}")[1]), "the creator run", 240)
        self.assertEqual((run["status"], run["step"]), ("done", "done"), run.get("stop") or run["log"])
        self.assertEqual(len([c for c in self.cli.calls if c[:2] == ["generate", "create"]]), 1, "one paid sheet, nothing else")
        self.assertEqual(len(self.fake.f.sets), 1)
        stickers = next(iter(self.fake.f.sets.values()))["stickers"]
        self.assertEqual(len(stickers), 9)
        lib = self.req("GET", "/api/library")[1]
        self.assertEqual([len(p["stickers"]) for p in lib["packs"]], [9])
        self.assertRegex(lib["packs"][0]["stickers"][0]["file"], r"^G001-[a-z0-9_]+-\d{8}T\d{6}/img-", "library files are grouped per batch (its labelled folder name) and carry the new names")
        last = self.req("GET", f"/api/chat/sessions/{sid}")[1]["messages"][-1]
        self.assertIn("t.me/addstickers", last["text"])


if __name__ == "__main__":
    unittest.main()
