"""The hosted gateway (deploy/gateway, branch `deployment`): the Google sign-in (a Supabase JWT, verified with a key generated here), the rules of a public name, the rate limit and the pass-through to the
REAL engine server. No network: the JWKS is served from memory and the engine runs in-process on a random port. Skipped when fastapi is not installed (it is a dependency of the hosted deploy only)."""
import base64
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

try:
    import fastapi  # noqa: F401
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from fastapi.testclient import TestClient
    HAVE = True
except ImportError:
    HAVE = False

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SECRET = "g" * 48
ISS = "https://abc.supabase.co/auth/v1"


def b64(n: int) -> str:
    return base64.urlsafe_b64encode(n.to_bytes((n.bit_length() + 7) // 8, "big")).rstrip(b"=").decode()


@unittest.skipUnless(HAVE, "fastapi / pyjwt are not installed (pip install -r deploy/gateway/requirements.txt)")
class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from deploy.gateway.app import create_app
        from deploy.gateway.auth import Verifier
        from deploy.gateway.config import Settings
        from deploy.gateway.ratelimit import Limiter
        from mirsal.console.server import serve
        from mirsal.engine.config import EngineConfig
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pub = cls.key.public_key().public_numbers()
        cls.jwks = {"keys": [{"kty": "RSA", "kid": "k1", "alg": "RS256", "use": "sig", "n": b64(pub.n), "e": b64(pub.e)}]}
        cls.keep = os.environ.get("MIRSAL_GATEWAY_SECRET")
        os.environ["MIRSAL_GATEWAY_SECRET"] = SECRET
        cls.tmp = Path(tempfile.mkdtemp())
        (cls.tmp / "in" / "Images_gen").mkdir(parents=True)
        (cls.tmp / "in" / "videos_gen").mkdir(parents=True)
        cls.srv, cls.engine = serve(cls.tmp / "out", cls.tmp / "in", 0, cfg=EngineConfig(), block=False)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.s = Settings(engine_url=f"http://127.0.0.1:{cls.srv.server_address[1]}", gateway_secret=SECRET, supabase_url="https://abc.supabase.co", allowed_hosts=["testserver"],
                         cookie_secure=False, rate_per_minute=1000, paid_rate_per_minute=2)
        cls.ver = Verifier(cls.s, fetch=lambda url: cls.jwks)
        cls.lim = Limiter("")
        cls.app = create_app(cls.s, cls.ver, cls.lim)
        cls.c = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.c.close()
        cls.srv.shutdown()
        cls.engine.release_writer()
        if cls.keep is None:
            os.environ.pop("MIRSAL_GATEWAY_SECRET", None)
        else:
            os.environ["MIRSAL_GATEWAY_SECRET"] = cls.keep
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def token(self, sub="11111111-2222-3333-4444-555555555555", name="Amira Haddad", provider="google", exp=3600, aud="authenticated", iss=ISS, key=None, alg="RS256", kid="k1"):
        claims = {"sub": sub, "aud": aud, "iss": iss, "exp": int(time.time()) + exp, "email": "amira@example.com", "user_metadata": {"full_name": name},
                  "app_metadata": {"provider": provider}}
        return jwt.encode(claims, key or self.key, algorithm=alg, headers={"kid": kid})

    def bearer(self, **kw):
        return {"Authorization": "Bearer " + self.token(**kw)}

    # ---- probes and the public pages
    def test_the_probes(self):
        self.assertEqual(self.c.get("/healthz").json(), {"ok": True})
        r = self.c.get("/readyz")
        self.assertEqual((r.status_code, r.json()["engine"], r.json()["auth"]), (200, True, True), r.text)

    def test_the_studio_page_is_public_but_the_api_is_not(self):
        self.assertEqual(self.c.get("/").status_code, 200)
        r = self.c.get("/api/generations")
        self.assertEqual(r.status_code, 401)
        self.assertIn("sign in", r.json()["error"])

    # ---- the person
    def test_a_google_token_is_a_member_with_the_name_of_the_profile(self):
        r = self.c.get("/api/me", headers=self.bearer())
        self.assertEqual(r.status_code, 200, r.text)
        me = r.json()
        self.assertEqual((me["role"], me["name"], me["via"], me["can_spend"]), ("member", "Amira Haddad", "gateway", True))
        again = self.c.get("/api/me", headers=self.bearer(name="Renamed In Google")).json()
        self.assertEqual(me["id"], again["id"], "the same subject is the same account")

    def test_every_kind_of_bad_token_is_refused(self):
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        bad = {
            "wrong audience": self.bearer(aud="anon"),
            "wrong issuer": self.bearer(iss="https://evil.example/auth/v1"),
            "expired": self.bearer(exp=-3600),
            "signed by someone else": self.bearer(key=other),
            "not google": self.bearer(provider="email"),
            "unknown key id": self.bearer(kid="nope"),
            "garbage": {"Authorization": "Bearer abc.def.ghi"},
            "no dots": {"Authorization": "Bearer abc"},
            "unsigned": {"Authorization": "Bearer " + jwt.encode({"sub": "x" * 8, "aud": "authenticated", "iss": ISS, "exp": int(time.time()) + 99}, None, algorithm="none")},
            "hs256 with no secret configured": {"Authorization": "Bearer " + jwt.encode({"sub": "x" * 8, "aud": "authenticated", "iss": ISS, "exp": int(time.time()) + 99}, "k" * 40, algorithm="HS256")},
        }
        for why, h in bad.items():
            self.assertEqual(self.c.get("/api/me", headers=h).status_code, 401, why)

    def test_a_client_cannot_borrow_an_identity_with_the_gateway_headers(self):
        forged = {"X-Mirsal-Gateway-Secret": SECRET, "X-Mirsal-Subject": "victim-subject-1", "X-Mirsal-Name": "Victim"}
        self.assertEqual(self.c.get("/api/me", headers=forged).status_code, 401, "no token, no entry, whatever headers are sent")
        mine = self.c.get("/api/me", headers={**self.bearer(sub="my-own-subject-0001", name="Me"), **forged}).json()
        self.assertEqual(mine["name"], "Me", "the gateway's own headers replace the client's")
        self.assertNotEqual(mine["name"], "Victim")

    def test_the_cookie_session_signs_in_and_out(self):
        c = TestClient(self.app)
        r = c.post("/auth/session", json={"access_token": self.token()})
        self.assertEqual(r.status_code, 200, r.text)
        sc = r.headers["set-cookie"].lower()
        self.assertIn("httponly", sc)
        self.assertIn("samesite=lax", sc)
        self.assertEqual(c.get("/api/me").status_code, 200, "the cookie alone is enough")
        self.assertEqual(c.get("/auth/me").json()["name"], "Amira Haddad")
        c.post("/auth/logout")
        self.assertEqual(c.get("/api/me").status_code, 401)
        self.assertEqual(c.post("/auth/session", json={"access_token": "garbage"}).status_code, 401)
        c.close()

    # ---- the rules of a public name
    def test_a_member_cannot_reach_the_owners_screens_and_the_engine_is_not_reachable_around_the_gateway(self):
        h = self.bearer()
        self.assertEqual(self.c.get("/api/library", headers=h).status_code, 403)
        self.assertEqual(self.c.get("/api/users", headers=h).status_code, 403)
        self.assertEqual(self.c.post("/api/telegram/config", json={"token": "x", "user_id": "1"}, headers=h).status_code, 403)

    def test_a_cross_origin_post_and_an_unknown_host_are_refused(self):
        h = self.bearer()
        self.assertEqual(self.c.post("/api/chat/sessions", json={}, headers={**h, "Origin": "https://evil.example"}).status_code, 403)
        self.assertEqual(self.c.post("/api/chat/sessions", json={}, headers={**h, "Sec-Fetch-Site": "cross-site"}).status_code, 403)
        self.assertEqual(self.c.post("/api/chat/sessions", json={}, headers={**h, "Origin": "http://testserver"}).status_code, 200)
        self.assertEqual(self.c.get("/api/me", headers={**h, "Host": "evil.example"}).status_code, 400)

    def test_the_rate_limit_answers_429_with_a_wait_and_the_paid_routes_have_a_lower_one(self):
        h = self.bearer(sub="rate-limit-subject-1")
        codes = [self.c.post("/api/live/sheet", json={"prompt": "owl"}, headers=h).status_code for _ in range(4)]
        self.assertEqual(codes[2:], [429, 429], codes)                    # two paid requests a minute in this test's settings
        r = self.c.post("/api/live/sheet", json={"prompt": "owl"}, headers=h)
        self.assertIn("retry-after", r.headers)
        self.assertEqual(self.c.get("/api/me", headers=h).status_code, 200, "the ordinary limit is separate")

    def test_the_chat_goes_through_and_belongs_to_the_person(self):
        a, b = self.bearer(sub="person-a-subject-01", name="A"), self.bearer(sub="person-b-subject-01", name="B")
        sid = self.c.post("/api/chat/sessions", json={}, headers=a).json()["id"]
        self.assertEqual(self.c.get(f"/api/chat/sessions/{sid}", headers=a).status_code, 200)
        self.assertEqual(self.c.get(f"/api/chat/sessions/{sid}", headers=b).status_code, 404, "a stranger's chat is a 404")

    def test_an_engine_that_is_down_is_a_502_not_a_crash(self):
        from deploy.gateway.app import create_app
        from deploy.gateway.config import Settings
        s = Settings(engine_url="http://127.0.0.1:9", gateway_secret=SECRET, supabase_url="https://abc.supabase.co", allowed_hosts=["testserver"], cookie_secure=False)
        c = TestClient(create_app(s, self.ver, self.lim))
        self.assertEqual(c.get("/api/me", headers=self.bearer()).status_code, 502)
        self.assertEqual(c.get("/readyz").status_code, 503)

    def test_the_settings_refuse_to_start_with_an_open_door(self):
        from deploy.gateway.config import Settings
        self.assertEqual(Settings(gateway_secret="short", supabase_url="").problems()[0][:20], "MIRSAL_GATEWAY_SECRE")
        self.assertEqual(Settings(gateway_secret=SECRET, supabase_url="https://abc.supabase.co").problems(), [])
        self.assertTrue(Settings(gateway_secret=SECRET, supabase_url="").problems(), "no issuer, no sign-in: the gateway will not start")


if __name__ == "__main__":
    unittest.main()
