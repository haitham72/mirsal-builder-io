"""Office accounts on the LAN (docs/api.md, Office accounts on the LAN): @nadi.ae sign-up waits for approval, sign-in with a session cookie, the same words for a wrong email
and a wrong password, Haitham's decisions in Users > People and in the Telegram bot (only his user id is obeyed). The server runs as if on the LAN with
127.0.0.1 treated as another machine; Telegram is a fake."""
import http.client
import json
import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from mirsal.flow import people as pp
from mirsal.runtime import users as um
from mirsal.runtime.users import UserError, UserStore


class AccountStoreTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.u = UserStore(self.out)

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def test_sign_up_waits_approval_gives_ten_credits_and_passwords_are_hashed(self):
        with self.assertRaises(UserError):
            self.u.signup("someone@gmail.com", "X", "longenough")
        a = self.u.signup("Amira.K@nadi.ae", "Amira", "longenough")
        self.assertEqual((a["email"], a["status"], a["credits_left"]), ("amira.k@nadi.ae", "pending", 0))
        self.assertNotIn("longenough", (self.out / "users.json").read_text())
        u, _ = self.u.decide(a["id"], "approve")
        self.assertEqual((u["status"], u["credits_left"]), ("active", 10))
        u, _ = self.u.decide(a["id"], "approve")
        self.assertEqual(u["credits_left"], 10, "approving twice never refills")

    def test_the_allowed_domains_are_a_list_set_by_mirsal_email_domain(self):
        with mock.patch.dict(os.environ, {"MIRSAL_EMAIL_DOMAIN": "nadi.ae, @CPD.gov.ae"}):
            self.assertEqual(um.email_domains(), ["nadi.ae", "cpd.gov.ae"])
            self.assertEqual(self.u.signup("Sara@cpd.gov.ae", "Sara", "longenough")["email"], "sara@cpd.gov.ae")
            for bad in ("x@gmail.com", "x@evil-cpd.gov.ae", "x@cpd.gov.ae.evil.com"):
                with self.assertRaises(UserError, msg=bad):
                    self.u.signup(bad, "X", "longenough")
        with mock.patch.dict(os.environ, {"MIRSAL_EMAIL_DOMAIN": "example.org"}):
            with self.assertRaises(UserError):
                self.u.signup("y@nadi.ae", "Y", "longenough")
        with mock.patch.dict(os.environ, {"MIRSAL_EMAIL_DOMAIN": ""}):
            self.assertEqual(self.u.signup("z@gmail.com", "Z", "longenough")["email"], "z@gmail.com", "empty: any domain")

    def test_login_sessions_and_the_same_words_for_a_wrong_email_or_password(self):
        a = self.u.signup("b@nadi.ae", "B", "password1")
        self.u.decide(a["id"], "approve")
        for email, pw in (("nobody@nadi.ae", "password1"), ("b@nadi.ae", "wrong-one")):
            with self.assertRaises(UserError) as cm:
                self.u.login(email, pw)
            self.assertEqual((cm.exception.code, str(cm.exception)), (401, "email or password is wrong"))
        user, tok = self.u.login("B@nadi.ae", "password1")
        self.assertEqual(self.u.by_session(tok)["id"], a["id"])
        self.u.logout(tok)
        self.assertIsNone(self.u.by_session(tok))

    def test_added_people_get_a_password_once_and_must_change_it(self):
        made = self.u.add_people(["c@nadi.ae"])
        pw = made[0]["password"]
        self.assertTrue(made[0]["must_change_password"])
        u, _ = self.u.login("c@nadi.ae", pw)
        u = self.u.change_password(u["id"], "", "mine-now-1")
        self.assertFalse(u["must_change_password"], "the given password is not asked again")
        with self.assertRaises(UserError):
            self.u.change_password(u["id"], "", "mine-now-2")      # once it is their own, the current one is needed
        self.assertFalse(self.u.change_password(u["id"], "mine-now-1", "mine-now-2")["must_change_password"])

    def test_on_the_lan_another_machine_is_never_the_owner_by_loading_the_page(self):
        self.u.signup("d@nadi.ae", "D", "password1")
        self.assertEqual(self.u.authenticate(None, True, client_ip="127.0.0.1", lan=True)["id"], "local", "this PC is still the owner")
        self.assertIsNone(self.u.authenticate(None, True, client_ip="192.168.1.20", lan=True), "another machine signs in")
        self.assertEqual(self.u.authenticate(None, True, client_ip="192.168.1.20", lan=False)["id"], "local", "without --lan nothing changes")


class AdminBotTests(unittest.TestCase):
    """Taps in Haitham's bot change the account; anyone else is ignored."""

    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        (self.out / "telegram.json").write_text(json.dumps({"token": "123:abc", "user_id": "777", "bot": "mirsal_bot"}))
        self.c = SimpleNamespace(out=self.out, users=UserStore(self.out), lan=True)
        self.calls = []
        self.p = mock.patch("mirsal.services.telegram._call", lambda token, method, fields, files=None, timeout=60: self.calls.append((method, fields)) or {"message_id": 5})
        self.e = mock.patch.dict(os.environ, {"MIRSAL_ADMIN_BOT": "1"})
        self.p.start(); self.e.start()

    def tearDown(self):
        self.p.stop(); self.e.stop()
        shutil.rmtree(self.out, ignore_errors=True)

    def test_a_sign_up_card_is_sent_and_only_haithams_tap_approves_it(self):
        from mirsal.services import admin_bot
        a = self.c.users.signup("e@nadi.ae", "Eman", "password1")
        r = pp.add(self.out, "signup", a)
        card = [f for m, f in self.calls if m == "sendMessage"][-1]
        self.assertIn("New sign-up: Eman <e@nadi.ae>", card["text"])
        self.assertEqual([b["text"] for b in card["reply_markup"]["inline_keyboard"][0]], ["Approve", "Reject", "Admin role"])
        tap = lambda who, act: {"update_id": 1, "callback_query": {"id": "q", "from": {"id": who}, "data": f"a:{r['id']}:{act}",
                                                                    "message": {"message_id": 5, "chat": {"id": 777}, "text": card["text"]}}}
        admin_bot.handle_update(self.c, tap(999, "approve"))
        self.assertEqual(self.c.users.get(a["id"])["status"], "pending", "a stranger's tap does nothing")
        admin_bot.handle_update(self.c, tap(777, "admin"))
        u = self.c.users.get(a["id"])
        self.assertEqual((u["status"], u["role"], u["credits_left"]), ("active", "admin", 10))
        self.assertEqual(pp.get(self.out, r["id"])["status"], "approved")
        edited = [f for m, f in self.calls if m == "editMessageText"][-1]
        self.assertIn("approved as admin", edited["text"])
        admin_bot.handle_update(self.c, tap(777, "reject"))
        self.assertEqual(self.c.users.get(a["id"])["status"], "active", "a decided card does nothing the second time")

    def test_credits_are_never_refilled_without_the_tap_and_a_password_goes_to_haitham_only(self):
        from mirsal.services import admin_bot
        a = self.c.users.signup("f@nadi.ae", "Faris", "password1")
        self.c.users.decide(a["id"], "approve")
        self.c.users.charge(a["id"], 10)
        r = pp.add(self.out, "credits", self.c.users.get(a["id"]), "a client pack")
        self.assertEqual(self.c.users.get(a["id"])["credits_left"], 0)
        admin_bot.handle_update(self.c, {"update_id": 2, "callback_query": {"id": "q", "from": {"id": 777}, "data": f"a:{r['id']}:credits", "message": {}}})
        self.assertEqual(self.c.users.get(a["id"])["credits_left"], 10)
        r2 = pp.add(self.out, "password", self.c.users.get(a["id"]))
        admin_bot.handle_update(self.c, {"update_id": 3, "callback_query": {"id": "q", "from": {"id": 777}, "data": f"a:{r2['id']}:password", "message": {}}})
        sent = [f for m, f in self.calls if m == "sendMessage" and "New password for f@nadi.ae" in f["text"]]
        self.assertEqual([s["chat_id"] for s in sent], ["777"], "the new password goes to Haitham's chat only")
        self.assertTrue(self.c.users.get(a["id"])["must_change_password"])

    def test_a_credit_request_offers_the_amount_asked_and_the_tap_gives_exactly_it(self):
        from mirsal.services import admin_bot
        a = self.c.users.signup("g@nadi.ae", "Ghada", "password1")
        self.c.users.decide(a["id"], "approve")
        self.c.users.charge(a["id"], 10)
        r = pp.add(self.out, "credits", self.c.users.get(a["id"]), "25 for the Eid pack")
        self.assertEqual(r["wanted"], 25)
        card = [f for m, f in self.calls if m == "sendMessage"][-1]
        self.assertIn("asks for 25", card["text"])
        self.assertEqual([(b["text"], b["callback_data"]) for b in card["reply_markup"]["inline_keyboard"][0]][:2],
                         [("Approve +25", f"a:{r['id']}:credits:25"), ("Give 10", f"a:{r['id']}:credits")])
        admin_bot.handle_update(self.c, {"update_id": 4, "callback_query": {"id": "q", "from": {"id": 777}, "data": f"a:{r['id']}:credits:25", "message": {}}})
        self.assertEqual(self.c.users.get(a["id"])["credits_left"], 25, "the 25 asked for, not the default 10")
        self.assertEqual(pp.get(self.out, r["id"])["status"], "approved")
        self.assertEqual([x["id"] for x in pp.recent(self.out)], [r["id"]])
        self.assertIsNone(pp.add(self.out, "credits", self.c.users.get(a["id"]), "for a client")["wanted"], "a purpose in words asks for no number")
        r3 = pp.waiting(self.out, a["id"])[0]
        admin_bot.handle_update(self.c, {"update_id": 5, "callback_query": {"id": "q", "from": {"id": 777}, "data": f"a:{r3['id']}:credits:99999", "message": {}}})
        self.assertEqual((self.c.users.get(a["id"])["credits_left"], pp.get(self.out, r3["id"])["status"]), (25, "waiting"), "an amount out of range gives nothing")


class AccountRouteTests(unittest.TestCase):
    """The routes on the FastAPI server, as on the LAN: this test's own client counts as another machine."""

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

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.c.release_writer()
        cls.loop.stop(); cls.env.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def req(self, method, path, body=None, cookie=None, owner=False):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        hd = {"Content-Type": "application/json", "Sec-Fetch-Site": "same-origin"}
        if cookie:
            hd["Cookie"] = f"mirsal_session={cookie}"
        if owner:
            hd["Authorization"] = "Bearer owner-token-for-the-test"
        h.request(method, path, json.dumps(body) if body is not None else None, hd)
        r = h.getresponse()
        raw = r.read()
        h.close()
        return r.status, json.loads(raw), r

    def cookie(self, r):
        sc = r.getheader("Set-Cookie") or ""
        self.assertIn("HttpOnly", sc)
        self.assertIn("SameSite=strict", sc)
        return sc.split(";")[0].split("=", 1)[1]

    def test_sign_up_waits_then_the_owner_approves_and_the_person_works(self):
        code, j, _ = self.req("GET", "/api/auth/me")
        self.assertEqual((code, j["signed_out"]), (401, True))
        self.assertEqual(self.req("GET", "/api/generations")[0], 401, "another machine is not the owner by opening the page")
        code, j, r = self.req("POST", "/api/auth/signup", {"email": "g@nadi.ae", "name": "Ghada", "password": "password1"})
        self.assertEqual(code, 201, j)
        ck = self.cookie(r)
        self.assertEqual(self.req("GET", "/api/auth/me", cookie=ck)[1]["user"]["status"], "pending")
        self.assertEqual(self.req("GET", "/api/generations", cookie=ck)[:2], (403, {"error": "waiting for approval"}))
        self.assertEqual(self.req("GET", "/api/people", cookie=ck)[0], 403)
        code, people, _ = self.req("GET", "/api/people", owner=True)
        self.assertEqual(code, 200)
        uid = next(p["id"] for p in people["people"] if p.get("email") == "g@nadi.ae")
        self.assertEqual([r["kind"] for r in people["requests"]], ["signup"])
        code, j, _ = self.req("POST", f"/api/people/{uid}", {"action": "approve"}, owner=True)
        self.assertEqual((code, j["user"]["status"], j["user"]["credits_left"]), (200, "active", 10))
        self.assertEqual(self.req("GET", "/api/generations", cookie=ck)[0], 200, "approved: the member works")
        self.assertEqual(self.req("GET", "/api/people", owner=True)[1]["requests"], [], "the sign-up request is closed")
        code, j, _ = self.req("POST", "/api/auth/forgot", {"email": "nobody@nadi.ae"})
        code2, j2, _ = self.req("POST", "/api/auth/forgot", {"email": "g@nadi.ae"})
        self.assertEqual((code, j["message"]), (code2, j2["message"]), "the same answer whether or not the email exists")
        code, j, _ = self.req("POST", f"/api/people/{uid}", {"action": "password"}, owner=True)
        self.assertEqual(len(j["password"]), 16)
        self.assertEqual(self.req("POST", "/api/auth/login", {"email": "g@nadi.ae", "password": "password1"})[0], 401, "the old password is gone")
        code, j, r = self.req("POST", "/api/auth/login", {"email": "g@nadi.ae", "password": j["password"]})
        self.assertEqual((code, j["user"]["must_change_password"]), (200, True))
        self.assertEqual(self.req("POST", "/api/auth/signup", {"email": "x@gmail.com", "name": "X", "password": "password1"})[0], 400)
