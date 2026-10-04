"""The hosted gateway's login (deployment branch): a request with the right secret from loopback is the person the gateway vouches for, a member created on first sight.
Nothing else gets an identity from these headers."""
import http.client
import json
import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from mirsal.console.server import serve
from mirsal.engine.config import EngineConfig
from mirsal.runtime.users import UserStore

SECRET = "s" * 40


class GatewayUnit(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.us = UserStore(Path(self.td.name))
        self.keep = os.environ.get("MIRSAL_GATEWAY_SECRET")
        os.environ["MIRSAL_GATEWAY_SECRET"] = SECRET

    def tearDown(self):
        if self.keep is None:
            os.environ.pop("MIRSAL_GATEWAY_SECRET", None)
        else:
            os.environ["MIRSAL_GATEWAY_SECRET"] = self.keep
        self.td.cleanup()

    def test_the_right_secret_from_loopback_is_that_person_and_created_once(self):
        a = self.us.authenticate_gateway(SECRET, "google-oauth2|1234567", "Amira Haddad", "127.0.0.1")
        b = self.us.authenticate_gateway(SECRET, "google-oauth2|1234567", "A different name", "127.0.0.1")
        self.assertEqual((a["role"], a["via"], a["can_spend"], a["name"]), ("member", "gateway", True, "Amira Haddad"))
        self.assertEqual(a["id"], b["id"], "the same subject is the same account")
        self.assertEqual(len(self.us.list()), 1)
        c = self.us.authenticate_gateway(SECRET, "google-oauth2|7654321", "Omar", "127.0.0.1")
        self.assertNotEqual(a["id"], c["id"])

    def test_a_wrong_missing_or_short_secret_or_a_foreign_peer_gets_nothing(self):
        for secret, ip in (("x" * 40, "127.0.0.1"), (None, "127.0.0.1"), ("", "127.0.0.1"), (SECRET, "10.1.2.3"), (SECRET, "203.0.113.9")):
            self.assertIsNone(self.us.authenticate_gateway(secret, "google-oauth2|1234567", "X", ip), (secret, ip))
        os.environ["MIRSAL_GATEWAY_SECRET"] = "short"
        self.assertIsNone(self.us.authenticate_gateway("short", "google-oauth2|1234567", "X", "127.0.0.1"), "a secret under 32 characters is not a secret")
        self.assertEqual(self.us.list(), [], "no account was created by any refused request")

    def test_a_bad_subject_is_refused(self):
        for sub in ("", "ab", "x" * 200, "has space here", "semi;colon;1234"):
            self.assertIsNone(self.us.authenticate_gateway(SECRET, sub, "X", "127.0.0.1"), sub)

    def test_a_disabled_account_stays_disabled(self):
        a = self.us.authenticate_gateway(SECRET, "google-oauth2|1234567", "A", "127.0.0.1")
        self.us.set_disabled(a["id"])
        self.assertIsNone(self.us.authenticate_gateway(SECRET, "google-oauth2|1234567", "A", "127.0.0.1"))

    def test_setting_the_secret_turns_authentication_on(self):
        self.assertTrue(self.us.any())
        del os.environ["MIRSAL_GATEWAY_SECRET"]
        os.environ.pop("MIRSAL_API_TOKEN", None)
        self.assertFalse(self.us.any(), "without a secret and without accounts the local sandbox is open as before")


class GatewayThroughTheServer(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "in" / "Images_gen").mkdir(parents=True)
        (self.tmp / "in" / "videos_gen").mkdir(parents=True)
        self.keep = os.environ.get("MIRSAL_GATEWAY_SECRET")
        os.environ["MIRSAL_GATEWAY_SECRET"] = SECRET
        self.srv, self.c = serve(self.tmp / "out", self.tmp / "in", 0, cfg=EngineConfig(), block=False)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.c.release_writer()
        if self.keep is None:
            os.environ.pop("MIRSAL_GATEWAY_SECRET", None)
        else:
            os.environ["MIRSAL_GATEWAY_SECRET"] = self.keep
        shutil.rmtree(self.tmp, ignore_errors=True)

    def req(self, path, headers=None):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h.request("GET", path, headers=headers or {})
        r = h.getresponse()
        data = r.read()
        h.close()
        try:
            return r.status, json.loads(data)
        except ValueError:
            return r.status, data

    def test_the_gateways_person_is_a_member_and_a_stranger_is_refused(self):
        gw = {"X-Mirsal-Gateway-Secret": SECRET, "X-Mirsal-Subject": "google-oauth2|1234567", "X-Mirsal-Name": "Amira"}
        s, me = self.req("/api/me", gw)
        self.assertEqual((s, me["role"], me["name"], me["via"]), (200, "member", "Amira", "gateway"))
        self.assertEqual(self.req("/api/me")[0], 401, "no identity, no entry: the open sandbox is gone as soon as the secret is set")
        self.assertEqual(self.req("/api/me", {**gw, "X-Mirsal-Gateway-Secret": "y" * 40})[0], 401)
        self.assertEqual(self.req("/api/library", gw)[0], 403, "a member cannot reach the owner-only library")


if __name__ == "__main__":
    unittest.main()
