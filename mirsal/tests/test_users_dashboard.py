"""The Users dashboard routes (docs/api.md "Users", flow/user_report.py): the owner sees everyone, a member sees only themselves, a stranger nothing; and a member's answer
carries no other person's email, prompt, batch or media link. Fixture batches, jobs and ledger lines are written to a scratch out/; no provider is reached."""
import json
import time
import unittest
from pathlib import Path

from tests.test_accounts import AccountRouteTests


def batch(out: Path, n: int, owner: str, prompt: str) -> None:
    d = out / f"G{n:03d}"
    (d / "slices").mkdir(parents=True)
    (d / "slices" / "a.png").write_bytes(b"png" * 100)
    (d / "result.json").write_text(json.dumps({"generation_id": f"G{n:03d}", "number": n, "owner": owner, "created": time.time() - 3600, "prompt": prompt,
                                               "sheet_prompt": f"sheet of {prompt}", "video_prompt": "", "stage": "sliced", "grid": [2, 2], "stickers": [
                                                   {"index": 1, "key": "k", "status": "READY", "png": "slices/a.png", "webm": None, "anim_status": "NOT_REQUESTED"}]}), encoding="utf-8")


def job(out: Path, jid: str, user: str, status: str, cost, gen: str) -> None:
    (out / "jobs").mkdir(exist_ok=True)
    (out / "jobs" / f"{jid}.json").write_text(json.dumps({"id": jid, "kind": "sheet", "status": status, "cost": cost, "cost_estimate": 2.0, "generation": gen,
                                                          "request": {"user": user, "label": f"label of {gen}"}, "created_at": time.time() - 3000,
                                                          "completed_at": time.time() - 2900, "error": None if status == "DONE" else "provider said no"}), encoding="utf-8")
    with open(out / "model_calls.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time() - 2900, "kind": "IMAGE_SHEET", "model": "nano_banana_flash", "status": "OK" if status == "DONE" else "ERROR", "cost": cost, "job": jid}) + "\n")


class UsersDashboard(AccountRouteTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ids, cls.cookies = {}, {}
        for email, name in (("amira@nadi.ae", "Amira"), ("bilal@nadi.ae", "Bilal")):
            code, j, r = cls.req(cls, "POST", "/api/auth/signup", {"email": email, "name": name, "password": "password1"})
            cls.cookies[name] = r.getheader("Set-Cookie").split(";")[0].split("=", 1)[1]
            cls.ids[name] = j["user"]["id"]
            cls.req(cls, "POST", f"/api/people/{cls.ids[name]}", {"action": "approve"}, owner=True)
        out = cls.c.out
        batch(out, 1, cls.ids["Amira"], "amira falcon secret")
        batch(out, 2, cls.ids["Bilal"], "bilal camel secret")
        job(out, "J001", cls.ids["Amira"], "DONE", 2.0, "G001")
        job(out, "J002", cls.ids["Bilal"], "FAILED", None, "G002")

    def test_the_owner_sees_everyone(self):
        code, j, _ = self.req("GET", "/api/users/overview", owner=True)
        self.assertEqual(code, 200, j)
        rows = {r["name"]: r for r in j["users"]}
        self.assertEqual((rows["Amira"]["batches"], rows["Amira"]["jobs_ok"], rows["Amira"]["spent"]), (1, 1, 2.0))
        self.assertEqual((rows["Bilal"]["jobs_failed"], rows["Bilal"]["spent"]), (1, 0))
        self.assertEqual(len(rows["Amira"]["series"]["spend"]), 30)
        self.assertGreater(rows["Amira"]["bytes"], 0)
        code, d, _ = self.req("GET", f"/api/users/{self.ids['Bilal']}", owner=True)
        self.assertEqual(code, 200)
        self.assertEqual(d["families"][0]["batches"][0]["prompt"], "bilal camel secret")
        self.assertEqual(d["jobs"][0]["status"], "FAILED")

    def test_a_member_sees_only_themselves(self):
        ck = self.cookies["Amira"]
        self.assertEqual(self.req("GET", "/api/users/overview", cookie=ck)[0], 403)
        code, d, r = self.req("GET", "/api/users/me", cookie=ck)
        self.assertEqual(code, 200, d)
        self.assertEqual((d["user"]["name"], d["summary"]["batches"], d["summary"]["spent"]), ("Amira", 1, 2.0))
        self.assertEqual([j["id"] for j in d["jobs"]], ["J001"])
        self.assertEqual([l["job"] for l in d["ledger"]], ["J001"])
        self.assertEqual(d["families"][0]["batches"][0]["stickers"][0]["png"], "/out/G001/slices/a.png")
        raw = json.dumps(d)
        for foreign in ("bilal", "Bilal", "camel", "G002", "J002"):
            self.assertNotIn(foreign, raw, f"a member's answer carries {foreign}")
        self.assertEqual(self.req("GET", f"/api/users/{self.ids['Amira']}", cookie=ck)[0], 200, "their own id works too")
        self.assertEqual(self.req("GET", f"/api/users/{self.ids['Bilal']}", cookie=ck)[:2], (404, {"error": "not found"}), "someone else is a 404, not a disclosure")
        self.assertEqual(self.req("GET", "/api/users/local", cookie=ck)[0], 404)
        self.assertEqual(self.req("GET", "/out/G002/slices/a.png", cookie=ck)[0], 404, "nor the other person's media")

    def test_a_stranger_sees_nothing(self):
        self.assertEqual(self.req("GET", "/api/users/overview")[0], 401)
        self.assertEqual(self.req("GET", "/api/users/me")[0], 401)


for _n in [n for n in dir(AccountRouteTests) if n.startswith("test_")]:
    setattr(UsersDashboard, _n, None)          # the account tests run in tests/test_accounts.py; this class only borrows their server and helpers

if __name__ == "__main__":
    unittest.main()
