"""Trending (flow/trending.py, docs/api.md, Office accounts on the LAN): the owner or an admin shares a pack; everyone signed in likes, comments and uses it; the three
orders; an unshared pack's files stay private; Use in my workflow copies the pack for the owner and gives a member a prompt and a reference. No provider."""
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

from mirsal.flow import trending as tr
from mirsal.media.library import Library
from mirsal.runtime import users as um
from tests.test_effects_flow import sticker_png


class TrendingEngineTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.lib = Library(self.out)
        self.a = self.lib.create_pack("Cats")
        self.b = self.lib.create_pack("Dogs")
        for p in (self.a, self.b):
            self.lib.add_bytes(p["id"], sticker_png(), "png", "one", "static", "🙂")

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def test_orders_likes_comments_and_privacy(self):
        with self.assertRaises(tr.TrendingError):
            tr.like(self.out, self.a["id"], "U1")
        tr.share(self.out, self.lib, self.a["id"], "local")
        time.sleep(0.01)
        tr.share(self.out, self.lib, self.b["id"], "local")
        self.assertEqual([r["pack_id"] for r in tr.listing(self.out, self.lib, "U1", "new")], [self.b["id"], self.a["id"]])
        tr.like(self.out, self.a["id"], "U1")
        tr.like(self.out, self.a["id"], "U2")
        tr.comment(self.out, self.a["id"], "U2", "Rana", "  lovely   cats ")
        top = tr.listing(self.out, self.lib, "U1", "trending")
        self.assertEqual((top[0]["pack_id"], top[0]["likes"], top[0]["liked"], top[0]["comments"]), (self.a["id"], 2, True, 1))
        self.assertEqual(tr.listing(self.out, self.lib, "U1", "liked")[0]["pack_id"], self.a["id"])
        self.assertEqual(tr.like(self.out, self.a["id"], "U1", on=False), 1, "unlike")
        self.assertEqual(tr.detail(self.out, self.lib, self.a["id"], "U9")["comments"][0]["text"], "lovely cats")
        tr.unshare(self.out, self.b["id"])
        with self.assertRaises(tr.TrendingError):
            tr.file_of(self.out, self.lib, self.b["id"], self.b["cover"] or "x")
        self.assertEqual(tr.score({"shared": {"p": {"at": 0}}, "likes": {}, "comments": {}}, "p", now=5 * 86400), 2.0, "half its weight after five days")

    def test_use_copies_for_the_owner_and_gives_a_member_a_prompt_and_a_reference(self):
        tr.share(self.out, self.lib, self.a["id"], "local")
        cp = tr.copy_pack(self.out, self.lib, self.a["id"], "local")
        self.assertEqual(cp["name"], "Cats (from Trending)")
        copy = next(p for p in self.lib.snapshot()["packs"] if p["id"] == cp["pack_id"])
        self.assertEqual(copy["stickers"][0]["source"]["shared_from"], self.a["id"])
        prompt, data, name = tr.as_request(self.out, self.lib, self.a["id"])
        self.assertEqual((prompt, data[:4]), ("Cats", b"\x89PNG"))


class TrendingRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from mirsal.console.server import serve
        cls.tmp = Path(tempfile.mkdtemp())
        cls.env = mock.patch.dict(os.environ, {"MIRSAL_API_TOKEN": "owner-token-for-the-test"})
        cls.loop = mock.patch.object(um, "LOOPBACK", ())
        cls.env.start(); cls.loop.start()
        cls.srv, cls.c = serve(cls.tmp / "out", cls.tmp / "in", 0, block=False, stdlib=False)
        cls.c.lan = True
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        p = cls.c.lib.create_pack("Falcons")
        cls.pid = p["id"]
        cls.sid = cls.c.lib.add_bytes(cls.pid, sticker_png(), "png", "chick", "static", "🦅")["id"]
        a = cls.c.users.signup("m@nadi.ae", "Mona", "password1")
        cls.c.users.decide(a["id"], "approve")

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.c.release_writer()
        cls.loop.stop(); cls.env.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def req(self, method, path, body=None, cookie=None, owner=False):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        hd = {"Content-Type": "application/json"}
        if cookie:
            hd["Cookie"] = f"mirsal_session={cookie}"
        if owner:
            hd["Authorization"] = "Bearer owner-token-for-the-test"
        h.request(method, path, json.dumps(body) if body is not None else None, hd)
        r = h.getresponse()
        raw = r.read()
        h.close()
        try:
            return r.status, json.loads(raw)
        except ValueError:
            return r.status, raw

    def test_the_owner_shares_a_member_likes_comments_sees_files_and_uses_it(self):
        _, tok = self.c.users.login("m@nadi.ae", "password1")
        self.assertEqual(self.req("POST", f"/api/trending/{self.pid}/share", cookie=tok)[0], 403, "a member does not share")
        self.assertEqual(self.req("GET", f"/api/trending/{self.pid}/file/{self.sid}", cookie=tok)[0], 404, "not shared: private")
        self.assertEqual(self.req("POST", f"/api/trending/{self.pid}/share", owner=True)[0], 200)
        code, j = self.req("GET", "/api/trending", cookie=tok)
        self.assertEqual((code, [p["pack_id"] for p in j["packs"]], j["can_share"]), (200, [self.pid], False))
        self.assertEqual(self.req("POST", f"/api/trending/{self.pid}/like", cookie=tok)[1], {"likes": 1})
        code, cm = self.req("POST", f"/api/trending/{self.pid}/comments", {"text": "beautiful"}, cookie=tok)
        self.assertEqual((code, cm["name"]), (201, "Mona"))
        code, data = self.req("GET", f"/api/trending/{self.pid}/file/{self.sid}", cookie=tok)
        self.assertEqual((code, bytes(data[:4])), (200, b"\x89PNG"))
        code, use = self.req("POST", f"/api/trending/{self.pid}/use", cookie=tok)
        self.assertEqual((code, use["prompt"], len(use["refs"])), (200, "Falcons", 1), "a member: a prompt and the cover as a reference")
        code, use = self.req("POST", f"/api/trending/{self.pid}/use", owner=True)
        self.assertEqual((code, use["copied"]["name"]), (201, "Falcons (from Trending)"), "the owner: a copy in the library")
        self.assertEqual(self.req("POST", f"/api/trending/{self.pid}/comments", {"text": ""}, cookie=tok)[0], 400)
        self.assertEqual(self.req("GET", "/api/trending")[0], 401, "signed out: nothing")
