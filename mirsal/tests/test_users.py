"""Accounts, ownership and rate limits (users.py + console/server.py): who may call, what a member can reach, and that a stranger's batch,
chat, job or file is a 404 (never a 403 that says it exists). Real server on synthetic prepared sheets; Redis replaced by a private in-memory cache;
Higgsfield and the language model are never reached."""
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

from mirsal import cache as cachemod, higgsfield, jobs
from mirsal.console.server import serve
from mirsal.engine.config import EngineConfig
from mirsal.users import LOCAL, UserError, UserStore
from tests.test_console import build_inputs

PAGE = {"Sec-Fetch-Site": "same-origin"}            # what a browser sends for the Studio's own fetches: the owner


class UserStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s = UserStore(self.tmp)
        self.env = os.environ.pop("MIRSAL_API_TOKEN", None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self.env is not None:
            os.environ["MIRSAL_API_TOKEN"] = self.env

    def test_a_token_is_shown_once_and_only_its_digest_is_stored(self):
        u, tok = self.s.create("Amira", "member", True)
        self.assertTrue(tok.startswith("mk_") and len(tok) > 40)
        raw = (self.tmp / "users.json").read_text(encoding="utf-8")
        self.assertNotIn(tok, raw)
        self.assertNotIn("token_sha256", json.dumps(self.s.list()))
        self.assertEqual(self.s.find_by_token(tok)["id"], u["id"])
        self.assertIsNone(self.s.find_by_token(tok + "x"))
        self.assertIsNone(self.s.find_by_token(""))

    def test_rotate_disable_update(self):
        u, tok = self.s.create("Amira")
        u2, tok2 = self.s.rotate(u["id"])
        self.assertIsNone(self.s.find_by_token(tok))
        self.assertEqual(self.s.find_by_token(tok2)["id"], u["id"])
        self.s.set_disabled(u["id"], True)
        self.assertIsNone(self.s.find_by_token(tok2))
        self.s.set_disabled(u["id"], False)
        self.assertEqual(self.s.update(u["id"], can_spend=True, role="owner", name="Amira K")["role"], "owner")
        for bad in (lambda: self.s.update("U999"), lambda: self.s.update(u["id"], role="root"), lambda: self.s.create(""), lambda: self.s.create("x", "root")):
            with self.assertRaises(UserError):
                bad()

    def test_authenticate_matrix(self):
        a = self.s.authenticate
        self.assertEqual((a(None, False)["id"], a(None, False)["via"]), ("local", "open"))         # nobody configured: the open sandbox as before
        u, tok = self.s.create("Amira")
        self.assertIsNone(a(None, False))                                                            # one user exists: authentication is on
        self.assertIsNone(a("Bearer nope", False))
        self.assertEqual((a(None, True)["id"], a(None, True)["via"]), ("local", "page"))             # the Studio's own page
        self.assertEqual(a(f"Bearer {tok}", False)["id"], u["id"])
        self.assertEqual(a(f"Bearer {tok}", True)["id"], u["id"])                                    # a token beats the page header: a member cannot widen themselves
        self.s.set_disabled(u["id"])
        self.assertIsNone(a(f"Bearer {tok}", False))
        self.assertEqual(self.s.get("local")["role"], LOCAL["role"])

    def test_the_env_token_is_the_owner(self):
        os.environ["MIRSAL_API_TOKEN"] = "env-secret"
        try:
            got = self.s.authenticate("Bearer env-secret", False)
            self.assertEqual((got["id"], got["role"], got["via"]), ("local", "owner", "token"))
            self.assertIsNone(self.s.authenticate("Bearer other", False))
        finally:
            os.environ.pop("MIRSAL_API_TOKEN", None)


class UsersServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = {k: os.environ.get(k) for k in ("MIRSAL_AGENT_PROVIDER", "MIRSAL_LLM_PROVIDER", "OPENAI_API_KEY", "MIRSAL_API_TOKEN", "MIRSAL_RATE_WRITE", "MIRSAL_RATE_READ")}
        os.environ["MIRSAL_AGENT_PROVIDER"] = "openai"
        os.environ["MIRSAL_LLM_PROVIDER"] = "openai"
        for k in ("OPENAI_API_KEY", "MIRSAL_API_TOKEN", "MIRSAL_RATE_WRITE", "MIRSAL_RATE_READ"):
            os.environ.pop(k, None)
        from mirsal import llm
        cls._loaded = llm._ENV_LOADED
        llm._ENV_LOADED = True
        cls.mem = cachemod.Cache(force_memory=True)
        cls.patches = [mock.patch.object(cachemod, "default", lambda: cls.mem), mock.patch.object(higgsfield, "available", lambda: False)]
        for p in cls.patches:
            p.start()
        cls.tmp = Path(tempfile.mkdtemp())
        build_inputs(cls.tmp / "in")
        cls.srv, cls.c = serve(cls.tmp / "out", cls.tmp / "in", 0, cfg=EngineConfig(min_sheet_px=256), block=False)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.alice, cls.t_alice = cls.c.users.create("Alice")
        cls.bob, cls.t_bob = cls.c.users.create("Bob")
        cls.boss, cls.t_boss = cls.c.users.create("Boss", "owner", True)
        cls.A, cls.B, cls.O = ({"Authorization": f"Bearer {t}"} for t in (cls.t_alice, cls.t_bob, cls.t_boss))

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.c.release_writer()
        for p in cls.patches:
            p.stop()
        from mirsal import llm
        llm._ENV_LOADED = cls._loaded
        for k, v in cls.env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def raw(self, method, path, body=None, headers=None):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h.request(method, path, json.dumps(body) if body is not None else None, {"Content-Type": "application/json", **(headers or {})})
        r = h.getresponse()
        data = r.read()
        h.close()
        try:
            data = json.loads(data)
        except ValueError:
            pass
        return r.status, data, dict(r.getheaders())

    def req(self, method, path, body=None, headers=None):
        s, d, _ = self.raw(method, path, body, headers)
        return s, d

    def make_batch(self, who):
        s, r = self.req("POST", "/api/generations", {"prompt": "create a blob for school", "variant": 1}, who)
        self.assertEqual(s, 202, r)
        self.c.wait_jobs()
        return r["id"]

    # ---- who may call ----------------------------------------------------------------------------------------------------
    def test_authentication_is_on_once_a_user_exists(self):
        self.assertEqual(self.req("GET", "/api/generations")[0], 401)
        self.assertEqual(self.req("GET", "/api/generations", headers={"Authorization": "Bearer nope"})[0], 401)
        self.assertEqual(self.req("GET", "/api/generations", headers=PAGE)[0], 200)                  # the Studio's own page is the owner
        self.assertEqual(self.req("GET", "/api/generations", headers=self.A)[0], 200)
        self.assertEqual(self.req("GET", "/")[0], 200)                                               # the page itself carries no data: a browser can always open it
        self.assertEqual(self.req("GET", "/api/health")[0], 401)
        s, me = self.req("GET", "/api/me", headers=self.A)
        self.assertEqual((s, me["id"], me["role"], me["can_spend"], me["via"]), (200, self.alice["id"], "member", False, "token"))
        self.assertEqual(self.req("GET", "/api/me", headers={**self.A, **PAGE})[1]["id"], self.alice["id"])      # a token beats the page header

    def test_disabling_a_user_stops_the_token_at_once(self):
        u, tok = self.c.users.create("Temp")
        h = {"Authorization": f"Bearer {tok}"}
        self.assertEqual(self.req("GET", "/api/me", headers=h)[0], 200)
        self.assertEqual(self.req("POST", f"/api/users/{u['id']}/disable", {}, PAGE)[0], 200)
        self.assertEqual(self.req("GET", "/api/me", headers=h)[0], 401)
        self.assertEqual(self.req("POST", f"/api/users/{u['id']}/enable", {}, PAGE)[0], 200)
        self.assertEqual(self.req("GET", "/api/me", headers=h)[0], 200)
        s, r = self.req("POST", f"/api/users/{u['id']}/rotate", {}, PAGE)
        self.assertEqual(self.req("GET", "/api/me", headers=h)[0], 401)                              # the old token is dead
        self.assertEqual(self.req("GET", "/api/me", headers={"Authorization": f"Bearer {r['token']}"})[0], 200)

    def test_only_an_owner_manages_users_and_the_list_never_holds_a_token(self):
        for who in (self.A, self.B):
            self.assertEqual(self.req("GET", "/api/users", headers=who)[0], 403)
            self.assertEqual(self.req("POST", "/api/users", {"name": "x"}, who)[0], 403)
            self.assertEqual(self.req("POST", f"/api/users/{self.alice['id']}/update", {"role": "owner"}, who)[0], 403)
        s, r = self.req("GET", "/api/users", headers=self.O)                                          # an owner-role token works like the page
        self.assertEqual(s, 200)
        self.assertNotIn("token", json.dumps(r))
        s, made = self.req("POST", "/api/users", {"name": "Dana", "can_spend": True}, self.O)
        self.assertEqual((s, made["user"]["role"], made["user"]["can_spend"]), (200, "member", True))
        self.assertEqual(self.req("GET", "/api/me", headers={"Authorization": f"Bearer {made['token']}"})[1]["name"], "Dana")
        self.assertEqual(self.req("POST", "/api/users", {"name": ""}, PAGE)[0], 400)
        self.assertEqual(self.req("POST", f"/api/users/{made['user']['id']}/update", {"can_spend": False}, PAGE)[1]["user"]["can_spend"], False)
        self.assertEqual(self.req("POST", "/api/users/U999/disable", {}, PAGE)[0], 404)

    def test_a_member_cannot_reach_the_owners_surface(self):
        for path in ("/api/users", "/api/library", "/api/telegram", "/api/usage", "/api/higgsfield", "/api/watch", "/api/tasks", "/api/inbox", "/api/projects",
                     "/api/models", "/api/inputs", "/api/history", "/api/jobs/J999/x"):
            self.assertIn(self.req("GET", path, headers=self.A)[0], (403, 404), path)
        for path, body in (("/api/telegram/config", {"token": "x"}), ("/api/watch/remove", {"number": "1"}), ("/api/tasks", {"prompt": "x"}),
                           ("/api/jobs", {"kind": "sheet"}), ("/api/packs", {"name": "p"}), ("/api/stickers/delete", {"items": []}),
                           ("/api/projects", {}), ("/api/cutout", {})):
            self.assertEqual(self.req("POST", path, body, self.A)[0], 403, path)
        self.assertEqual(self.req("POST", "/api/generations", {"task": "T001", "prompt": "x"}, self.A)[0], 403)       # runs a reserved task: owner only

    # ---- what a member owns ----------------------------------------------------------------------------------------------
    def test_batches_are_stamped_with_their_owner_and_hidden_from_strangers(self):
        gid = self.make_batch(self.A)
        res = json.loads((self.tmp / "out" / f"G{gid:03d}" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(res["owner"], self.alice["id"])
        g = f"/api/generations/{gid}"
        self.assertEqual(self.req("GET", g, headers=self.A)[0], 200)
        self.assertEqual(self.req("GET", g, headers=self.B)[0], 404)                                  # not 403: it is not revealed to exist
        self.assertEqual(self.req("GET", g + "/events", headers=self.B)[0], 404)
        self.assertEqual(self.req("POST", g + "/more", {}, self.B)[0], 404)
        self.assertEqual(self.req("POST", g + "/review", {"gate": "plan", "decision": "APPROVE"}, self.B)[0], 404)
        self.assertEqual(self.req("GET", g + "/files", headers=self.A)[0], 403)                       # server paths: owner only
        self.assertEqual(self.req("POST", g + "/reveal", {}, self.A)[0], 403)                         # opens a window on the owner's machine
        self.assertEqual(self.req("POST", g + "/add", {"pack_id": "x"}, self.A)[0], 403)              # into the owner's library
        self.assertEqual(self.req("GET", g + "/edge_preview?index=1", headers=self.A)[0], 200)
        png = next(f for f in (self.tmp / "out" / f"G{gid:03d}" / "slices").glob("*.png"))
        url = f"/out/G{gid:03d}/slices/{png.name}"
        self.assertEqual(self.req("GET", url, headers=self.A)[0], 200)
        self.assertEqual(self.req("GET", url, headers=self.B)[0], 404)
        self.assertEqual(self.req("GET", url, headers=self.O)[0], 200)                                # an owner sees everything
        self.assertEqual(self.req("GET", "/out/users.json", headers=self.A)[0], 403)                  # nothing outside a batch of their own
        self.assertEqual(self.req("GET", "/out/refs/R001.png", headers=self.A)[0], 403)

        def ids(h):
            return [x["id"] for x in self.req("GET", "/api/generations", headers=h)[1]["generations"]]
        self.assertIn(gid, ids(self.A))
        self.assertNotIn(gid, ids(self.B))
        self.assertIn(gid, ids(PAGE))
        owned = self.req("GET", "/api/generations", headers=self.A)[1]
        self.assertNotIn("paths", owned)
        self.assertNotIn("health", owned)
        self.assertEqual({x["owner"] for x in self.req("GET", "/api/generations", headers=PAGE)[1]["generations"] if x["id"] == gid}, {self.alice["id"]})

    def test_search_is_scoped_to_what_the_caller_owns(self):
        gid = self.make_batch(self.A)
        mine = self.req("GET", "/api/search?q=blob", headers=self.A)[1]["results"]
        self.assertTrue(any(r["id"] == gid for r in mine))
        self.assertEqual([r for r in self.req("GET", "/api/search?q=blob", headers=self.B)[1]["results"] if r["id"] == gid], [])
        self.assertTrue(any(r["id"] == gid for r in self.req("GET", "/api/search?q=blob", headers=PAGE)[1]["results"]))

    def test_signed_links_are_for_files_the_signer_may_see_and_work_without_a_header(self):
        gid = self.make_batch(self.A)
        png = next(f for f in (self.tmp / "out" / f"G{gid:03d}" / "slices").glob("*.png"))
        key = f"G{gid:03d}/slices/{png.name}"
        s, link = self.req("POST", "/api/assets/sign", {"key": key, "ttl": 30}, self.A)
        self.assertEqual(s, 200)
        got, body = self.req("GET", link["url"])                                                      # an <img> cannot send a header: the signature is the credential
        self.assertEqual((got, body[:4]), (200, b"\x89PNG"))
        self.assertEqual(self.req("POST", "/api/assets/sign", {"key": key}, self.B)[0], 404)          # Bob cannot mint a link to Alice's file
        self.assertEqual(self.req("POST", "/api/assets/sign", {"key": "users.json"}, self.A)[0], 404)
        self.assertEqual(self.req("POST", "/api/assets/sign", {"key": key}, self.O)[0], 200)

    def test_jobs_belong_to_whoever_asked(self):
        mine = jobs.create(self.c.out, "sheet", request={"user": self.alice["id"]})
        other = jobs.create(self.c.out, "sheet", request={"user": self.bob["id"]})
        s, r = self.req("GET", "/api/jobs", headers=self.A)
        self.assertEqual({j["id"] for j in r["jobs"]} & {mine["id"], other["id"]}, {mine["id"]})
        self.assertNotIn("typical", r)
        self.assertEqual(self.req("GET", f"/api/jobs/{mine['id']}", headers=self.A)[0], 200)
        self.assertEqual(self.req("GET", f"/api/jobs/{other['id']}", headers=self.A)[0], 404)
        for act in ("claim", "done", "fail", "requeue", "retry"):
            self.assertEqual(self.req("POST", f"/api/jobs/{mine['id']}/{act}", {}, self.A)[0], 403, act)      # the operator's actions: owner only
        self.assertTrue({mine["id"], other["id"]} <= {j["id"] for j in self.req("GET", "/api/jobs", headers=PAGE)[1]["jobs"]})

    def test_paid_generation_needs_the_right_to_spend(self):
        with mock.patch.object(higgsfield, "available", lambda: True):
            for what, body in (("sheet", {"prompt": "a blob"}), ("video", {"generation": 1})):
                s, r = self.req("POST", f"/api/live/{what}", body, self.A)
                self.assertEqual(s, 403, r)
                self.assertIn("cannot start paid generation", r["error"])
            gid = self.make_batch(self.A)
            self.assertEqual(self.req("POST", "/api/live/video", {"generation": gid}, self.B)[0], 403)          # Bob cannot spend either
            s, _ = self.req("POST", "/api/live/video", {"generation": 999}, self.O)                              # an owner may (this one fails later, not at the gate)
            self.assertNotEqual(s, 403)
        s, r = self.req("POST", "/api/live/sheet", {"prompt": "a blob"}, self.A)                                   # authorisation comes before the provider is mentioned
        self.assertEqual(s, 403)

    # ---- chat ------------------------------------------------------------------------------------------------------------
    def test_chats_are_private_and_the_turn_acts_as_its_user(self):
        s, sess = self.req("POST", "/api/chat/sessions", {"settings": {"ai": False}}, self.A)
        self.assertEqual(s, 200)
        sid = sess["id"]
        self.assertEqual(sess["user"], self.alice["id"])
        self.assertEqual(self.req("GET", f"/api/chat/sessions/{sid}", headers=self.B)[0], 404)
        self.assertEqual(self.req("POST", f"/api/chat/sessions/{sid}/messages", {"text": "hi"}, self.B)[0], 404)
        self.assertEqual(self.req("POST", f"/api/chat/sessions/{sid}/delete", {}, self.B)[0], 404)
        self.assertEqual(self.req("POST", f"/api/chat/sessions/{sid}/settings", {"grid": "2x2"}, self.B)[0], 404)
        self.assertNotIn(sid, [x["id"] for x in self.req("GET", "/api/chat/sessions", headers=self.B)[1]["sessions"]])
        self.assertIn(sid, [x["id"] for x in self.req("GET", "/api/chat/sessions", headers=self.A)[1]["sessions"]])
        self.assertIn(sid, [x["id"] for x in self.req("GET", "/api/chat/sessions", headers=PAGE)[1]["sessions"]])      # an owner sees every chat
        s, r = self.req("POST", f"/api/chat/sessions/{sid}/messages", {"text": "create a blob for school"}, self.A)
        self.assertEqual(s, 202, r)
        self.c.wait_chat()
        self.c.wait_jobs()
        j = self.req("GET", f"/api/chat/sessions/{sid}", headers=self.A)[1]
        card = next(c for m in j["messages"] for c in (m.get("cards") or []) if c["type"] == "generation")
        res = json.loads((self.tmp / "out" / card["generation"] / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(res["owner"], self.alice["id"])                  # the batch the chat started is Alice's, though it ran in another thread
        self.assertEqual(self.req("GET", f"/api/generations/{res['number']}", headers=self.B)[0], 404)
        self.assertEqual(self.req("POST", f"/api/chat/sessions/{sid}/delete", {}, self.A)[0], 200)

    def test_the_tools_refuse_a_strangers_batch(self):
        from mirsal.agent.tools import ConsoleTools, ToolError
        gid = self.make_batch(self.A)
        tb = ConsoleTools(self.c, dict(self.bob, via="token"))
        for call in (lambda: tb.more(f"G{gid:03d}"), lambda: tb.ready_indexes(f"G{gid:03d}")):
            with self.assertRaises(ToolError) as cm:
                call()
            self.assertEqual(cm.exception.code, 404)
        self.assertIsNone(ConsoleTools(self.c, dict(self.bob)).credits())                                 # the owner's balance is not a member's business

    # ---- rate limits -----------------------------------------------------------------------------------------------------
    def test_a_token_holder_is_limited_per_minute_and_each_user_has_their_own_allowance(self):
        os.environ["MIRSAL_RATE_WRITE"] = "3"
        try:
            codes = [self.req("POST", "/api/chat/sessions", {"title": "x"}, self.B)[0] for _ in range(3)]
            self.assertEqual(codes, [200, 200, 200])
            s, body, hdr = self.raw("POST", "/api/chat/sessions", {"title": "x"}, self.B)
            self.assertEqual(s, 429, body)
            self.assertTrue(1 <= int(hdr["Retry-After"]) <= 61)
            self.assertIn("too many requests", body["error"])
            self.assertEqual(self.req("GET", "/api/me", headers=self.B)[0], 200)                         # reads have their own (larger) allowance
            self.assertEqual(self.req("POST", "/api/chat/sessions", {"title": "x"}, self.A)[0], 200)      # Alice's allowance is separate from Bob's
            for _ in range(6):
                self.assertEqual(self.req("POST", "/api/chat/sessions", {"title": "x"}, PAGE)[0], 200)   # the owner's own page is never limited
            self.assertEqual(self.req("GET", "/api/health", headers=self.B)[0], 200)                      # health checks are exempt
        finally:
            os.environ.pop("MIRSAL_RATE_WRITE", None)

    def test_a_limit_of_zero_switches_it_off(self):
        os.environ["MIRSAL_RATE_WRITE"] = "0"
        try:
            self.assertEqual([self.req("POST", "/api/chat/sessions", {}, self.O)[0] for _ in range(5)], [200] * 5)
        finally:
            os.environ.pop("MIRSAL_RATE_WRITE", None)


if __name__ == "__main__":
    unittest.main()
