"""Credits per person (docs/office_lan_plan.md 2.5): a paid job reserves its price from the person's balance before it starts, the real cost replaces the
reservation when it ends, a failed job gives everything back, a job that could not be created never keeps the credits, and a price above the balance is
refused in words before anything starts. The owner and token accounts without a balance spend as before. No provider is called."""
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from mirsal.console.server import Console
from mirsal.flow import pipeline as pl
from mirsal.generation import jobs
from mirsal.runtime.users import UserStore


class CreditTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.users = UserStore(self.out)
        a = self.users.signup("h@nadi.ae", "Huda", "password1")
        self.uid = self.users.decide(a["id"], "approve")[0]["id"]
        self.c = SimpleNamespace(users=self.users)

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def left(self):
        return self.users.get(self.uid)["credits_left"]

    def test_reserve_then_settle_on_the_real_cost(self):
        r = Console.reserve(self.c, {"id": self.uid}, 4.5)
        self.assertEqual((r, self.left()), (4.5, 5.5))
        j = jobs.create(self.out, "video", request={"model": "kling", "prompt": "p", "user": self.uid, "reserved": r})
        jobs.claim(self.out, j["id"], "provider-ticket-1")
        f = self.out / "clip.mp4"
        f.write_bytes(b"x")
        jobs.done(self.out, j["id"], str(f), "kling", cost=3.0)
        self.assertEqual((self.left(), self.users.get(self.uid)["credits_spent"]), (7.0, 3.0), "the real cost replaced the reservation")

    def test_a_failed_job_gives_everything_back_and_only_once(self):
        r = Console.reserve(self.c, {"id": self.uid}, 2)
        j = jobs.create(self.out, "sheet", request={"model": "nano", "prompt": "p", "user": self.uid, "reserved": r})
        jobs.fail(self.out, j["id"], "provider said no")
        self.assertEqual(self.left(), 10.0)
        jobs.requeue(self.out, j["id"])
        jobs.fail(self.out, j["id"], "again")
        self.assertEqual(self.left(), 10.0, "settled once: a retried failure gives nothing twice")

    def test_a_price_above_the_balance_is_refused_before_anything_starts(self):
        self.users.charge(self.uid, 9)
        with self.assertRaises(pl.PipelineError) as cm:
            Console.reserve(self.c, {"id": self.uid}, 2)
        self.assertEqual(cm.exception.code, 402)
        self.assertIn("Request credits", str(cm.exception))
        self.assertEqual(self.left(), 1.0, "nothing was taken")

    def test_the_owner_and_accounts_without_a_balance_are_not_charged(self):
        self.assertIsNone(Console.reserve(self.c, {"id": "local"}, 99))
        tok, _ = self.users.create("Script", "member", can_spend=True)
        self.assertIsNone(Console.reserve(self.c, {"id": tok["id"]}, 99))

    def test_a_reservation_whose_job_was_never_created_goes_back(self):
        r = Console.reserve(self.c, {"id": self.uid}, 4)
        Console._unreserve(self.c, {"id": self.uid}, r, None)
        self.assertEqual(self.left(), 10.0)
