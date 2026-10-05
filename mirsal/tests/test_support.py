"""The support agent (flow/support.py): answers only with a valid cite, the fallback without a model, memory per person, the screenshot read by the
vision model, privacy, one ticket and one ping per escalation (a failed ping kept for the retry), reply versus resolve, notifications once, reopen.
Fake model, fake vision, fake Telegram; isolated out/."""
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mirsal.flow import faq, notifications as nt, support as sp, tickets as tk

ME = {"id": "u1", "role": "member", "name": "Sara"}
OTHER = {"id": "u2", "role": "member", "name": "Omar"}
ADMIN = {"id": "a1", "role": "admin", "name": "Admin"}


def answer(reply, cites=(), need="none"):
    return lambda s, u: (json.dumps({"reply": reply, "cites": list(cites), "need": need}), {})


def png() -> bytes:
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (40, 30), (200, 10, 10)).save(b, "PNG")
    return b.getvalue()


class SupportTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        f = faq.propose(self.out, title="Telegram refuses a pack", question="Why does Telegram refuse my sticker pack?",
                        answer="A video sticker over 256 KB is refused: re-export the pack.", by="a1")
        self.fid = faq.publish(self.out, f["id"], "a1")["id"]
        self.pings = []
        self.p1 = mock.patch.object(sp, "_ping_later", lambda out, tid, reason: sp.ping(out, tid, reason))
        self.p2 = mock.patch("mirsal.services.admin_bot.notify_support", lambda out, text: self.pings.append(text) or True)
        self.p1.start()
        self.p2.start()

    def tearDown(self):
        self.p1.stop()
        self.p2.stop()
        shutil.rmtree(self.out, ignore_errors=True)

    def test_an_answer_is_shown_only_with_a_cite_to_what_was_retrieved(self):
        cv = sp.ask(self.out, ME, "Telegram refuses my sticker pack", complete=answer("Re-export it: files over 256 KB are refused.", [1]))
        a = cv["messages"][-1]
        self.assertTrue(a["grounded"])
        self.assertEqual(a["cites"][0]["id"], self.fid)
        bad = sp.ask(self.out, ME, "Telegram refuses my sticker pack", complete=answer("Turn on turbo mode in Settings.", [7]))
        self.assertEqual(bad["messages"][-1]["text"], sp.NO_ANSWER, "a cite to nothing retrieved is an invented fix: not shown")
        none = sp.ask(self.out, ME, "Telegram refuses my sticker pack", complete=answer("Restart your computer."))
        self.assertEqual(none["messages"][-1]["text"], sp.NO_ANSWER)
        ask = sp.ask(self.out, ME, "it is broken", complete=answer("Which screen are you on?", need="clarify"))
        self.assertEqual(ask["messages"][-1]["need"], "clarify", "a short question needs no cite")

    def test_without_a_model_the_matching_faq_is_quoted_word_for_word_and_nothing_else_is_guessed(self):
        down = lambda s, u: (_ for _ in ()).throw(RuntimeError("LM Studio is down"))
        cv = sp.ask(self.out, ME, "Why does Telegram refuse my sticker pack", complete=down)
        self.assertIn("re-export the pack", cv["messages"][-1]["text"])
        self.assertEqual(cv["messages"][-1]["cites"][0]["id"], self.fid)
        cv2 = sp.ask(self.out, ME, "the zebra crossing flickers purple", complete=down)
        self.assertEqual(cv2["messages"][-1]["text"], sp.NO_ANSWER)

    def test_memory_is_this_persons_earlier_problems_only(self):
        sp.ask(self.out, ME, "Telegram refuses my sticker pack", complete=answer("Re-export.", [1]))
        sp.ask(self.out, OTHER, "Omar's secret problem with batches", complete=answer("x", need="clarify"))
        seen = {}
        sp.ask(self.out, ME, "and now the library is empty", complete=lambda s, u: seen.setdefault("u", u) and (json.dumps({"reply": "Which pack?", "need": "clarify"}), {}))
        self.assertIn("Telegram refuses", seen["u"])
        self.assertNotIn("Omar", seen["u"], "never another person's history")

    def test_a_screenshot_is_read_by_the_vision_model_and_only_staff_see_its_description(self):
        vision = lambda s, u, images: ("The Library screen shows the error 'pack is empty'.", {"model": "fake-vlm"})
        cv = sp.ask(self.out, ME, "this happens", image=png(), complete=answer("Which pack?", need="clarify"), vision=vision)
        um = next(m for m in cv["messages"] if m["role"] == "user")
        self.assertTrue(um["image"].startswith("img-"))
        self.assertIn("pack is empty", um["seen"])
        self.assertNotIn("seen", sp.view(cv, ME)["messages"][0], "the person never sees internal fields")
        self.assertIn("seen", sp.view(sp.escalate(self.out, ME, cv["id"]), ADMIN)["messages"][0])
        with self.assertRaises(sp.SupportError):
            sp.ask(self.out, ME, "x", image=b"not a picture")

    def test_a_strangers_conversation_does_not_exist_and_staff_see_only_escalated_ones(self):
        cv = sp.ask(self.out, ME, "help", complete=answer("Which screen?", need="clarify"))
        with self.assertRaises(KeyError):
            sp.mine(self.out, OTHER, cv["id"])
        with self.assertRaises(KeyError):
            sp.mine(self.out, ADMIN, cv["id"])
        sp.escalate(self.out, ME, cv["id"])
        self.assertEqual(sp.mine(self.out, ADMIN, cv["id"])["id"], cv["id"])
        with self.assertRaises(sp.SupportError):
            sp.ask(self.out, ADMIN, "I am staff, close it", cid=cv["id"])

    def test_escalation_is_one_ticket_and_one_ping_however_often_it_is_asked(self):
        cv = sp.ask(self.out, ME, "my animation never finishes", complete=answer("Which batch?", need="clarify"))
        a = sp.feedback(self.out, ME, cv["id"], False)
        b = sp.escalate(self.out, ME, cv["id"])
        self.assertEqual(a["ticket"], b["ticket"])
        self.assertEqual(len([t for t in tk.listing(self.out) if t["source"] == "support"]), 1)
        self.assertEqual(len(self.pings), 1)
        self.assertIn("/#/help/" + cv["id"], self.pings[0])
        t = tk.read(self.out, a["ticket"])
        self.assertEqual((t["conversation"], t["questions"]), (cv["id"], []))
        self.assertEqual(b["status"], "awaiting_admin")

    def test_a_failed_ping_keeps_the_ticket_and_is_sent_by_the_retry(self):
        self.p2.stop()
        with mock.patch("mirsal.services.admin_bot.notify_support", side_effect=OSError("telegram down")):
            cv = sp.escalate(self.out, ME, sp.ask(self.out, ME, "x happens", complete=answer("Which?", need="clarify"))["id"])
        t = tk.read(self.out, cv["ticket"])
        self.assertFalse(t["pinged"][f"escalate:{t['id']}"]["ok"])
        self.p2.start()
        self.assertEqual(sp.retry_pings(self.out), 1)
        self.assertEqual(sp.retry_pings(self.out), 0, "a sent ping is never sent again")
        self.assertEqual(len(self.pings), 1)

    def test_reply_keeps_it_open_resolve_closes_and_each_notifies_once(self):
        cv = sp.escalate(self.out, ME, sp.ask(self.out, ME, "uploads fail", complete=answer("Which file?", need="clarify"))["id"])
        tid = cv["ticket"]
        sp.admin_reply(self.out, ADMIN, tid, "Is the file over 8 MB?", client_id="k1")
        sp.admin_reply(self.out, ADMIN, tid, "Is the file over 8 MB?", client_id="k1")
        t = tk.read(self.out, tid)
        self.assertEqual((t["status"], len(t["thread"])), ("replied", 1), "a reply does not close, and a retried reply is one line")
        self.assertEqual(sp.read(self.out, cv["id"])["status"], "admin_replied")
        self.assertEqual(nt.listing(self.out, "u1")["unread"], 1)
        sp.reply_user(self.out, ME, cv["id"], "Yes, 12 MB")
        self.assertEqual(tk.read(self.out, tid)["status"], "open")
        self.assertEqual(sp.read(self.out, cv["id"])["status"], "awaiting_admin")
        sp.resolve(self.out, ADMIN, tid, "Uploads above 8 MB are refused: shrink it first.", propose=False)
        sp.resolve(self.out, ADMIN, tid, propose=False)
        self.assertEqual(tk.read(self.out, tid)["status"], "fixed")
        self.assertEqual(sp.read(self.out, cv["id"])["status"], "resolved")
        kinds = [n["kind"] for n in nt.listing(self.out, "u1")["notifications"]]
        self.assertEqual(kinds.count("resolved"), 1, "resolving twice notifies once")
        with self.assertRaises(sp.SupportError):
            sp.admin_reply(self.out, ME, tid, "I resolve my own ticket")

    def test_reopening_a_resolved_issue_opens_its_ticket_and_pings_once_more(self):
        cv = sp.escalate(self.out, ME, sp.ask(self.out, ME, "sound is gone", complete=answer("Which?", need="clarify"))["id"])
        sp.resolve(self.out, ADMIN, cv["ticket"], "Fixed in the last update.", propose=False)
        r = sp.reopen(self.out, ME, cv["id"], "Still no sound")
        self.assertEqual(r["status"], "awaiting_admin")
        self.assertEqual(tk.read(self.out, cv["ticket"])["status"], "open")
        self.assertEqual(len(self.pings), 2)
        self.assertIn("reopened", self.pings[1])
        sp.resolve(self.out, ADMIN, cv["ticket"], propose=False)
        self.assertEqual([n["kind"] for n in nt.listing(self.out, "u1")["notifications"]].count("resolved"), 2, "a new resolution after a reopen notifies again")

    def test_the_queue_lists_support_tickets_waiting_for_a_person(self):
        cv = sp.escalate(self.out, ME, sp.ask(self.out, ME, "help me", complete=answer("Which?", need="clarify"))["id"])
        q = sp.queue(self.out)
        self.assertEqual([r["id"] for r in q], [cv["ticket"]])
        self.assertEqual(q[0]["name"], "Sara")
        sp.resolve(self.out, ADMIN, cv["ticket"], "done", propose=False)
        self.assertEqual(sp.queue(self.out), [])
        self.assertEqual(len(sp.queue(self.out, "all")), 1)


if __name__ == "__main__":
    unittest.main()
