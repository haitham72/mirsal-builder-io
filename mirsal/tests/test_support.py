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

    def test_a_plain_text_answer_with_markers_counts_its_markers_as_cites(self):
        plain = lambda s, u: ("Re-export the pack: files over 256 KB are refused [1].", {})
        a = sp.ask(self.out, ME, "Telegram refuses my sticker pack", complete=plain)["messages"][-1]
        self.assertTrue(a["grounded"])
        self.assertEqual(a["text"], "Re-export the pack: files over 256 KB are refused.")
        self.assertEqual(sp._parse("Which screen were you on?")["need"], "clarify")
        self.assertEqual(sp._parse("Could you send a screenshot of it?")["need"], "screenshot")

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

    def test_a_screenshot_finds_the_entry_by_what_the_problem_looks_like(self):
        f = faq.propose(self.out, title="Blocked sticker", question="Why can I not approve this sticker?", answer="Click Use it anyway on the tile.", by="a1")
        with faq._LOCK:
            e = faq.read(self.out, f["id"])
            e["looks_like"] = "a sticker tile with a red Blocked label and a reason under it, next to a Use it anyway button"
            faq._write(self.out, e)
        faq.publish(self.out, f["id"], "a1")
        vision = lambda s, u, images: ("A grid of stickers; one tile has a red Blocked label with a reason and a Use it anyway button.", {})
        down = lambda s, u: (_ for _ in ()).throw(RuntimeError("no text model"))
        cv = sp.ask(self.out, ME, "what is this", image=png(), complete=down, vision=vision)
        a = cv["messages"][-1]
        self.assertEqual(a["cites"][0]["id"], f["id"], "the vision model's words matched the entry's looks_like")
        self.assertIn("Use it anyway on the tile", a["text"])
        self.assertNotIn("Looks like", a["text"], "only the answer is quoted")

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
        tk.patch(self.out, tid, "python", "TEST", summary="internal: the 8 MB guard in _save_image refuses it")
        done = next(n for n in nt.listing(self.out, "u1")["notifications"] if n["kind"] == "resolved")
        self.assertIn("uploads fail", done["text"], "the notification repeats the person's own words")
        self.assertNotIn("internal", done["text"])
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


def cite_activity(ident, reply, request="none"):
    """A fake model that cites the (activity) source naming `ident`, wherever it was numbered."""
    import re as _re
    def run(s, u):
        n = next(int(m.group(1)) for m in _re.finditer(r"\[(\d+)\] \(activity\) ([^\n]+)", u) if ident in m.group(2))
        return json.dumps({"reply": reply, "cites": [n], "need": "none", "request": request}), {}
    return run


class SupportCaseTests(unittest.TestCase):
    """The real cases (Haitham, 2026-10-05): where is my video (the person's own jobs, a watch that says when it finished), why only 2 of 9
    (the batch's blocked stickers, a button to open it), a feature request, and a token sent as a private message."""

    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        (self.out / "jobs").mkdir()
        now = __import__("time").time()
        for i, (st, made, took) in enumerate([("DONE", 9000, 300), ("DONE", 8000, 420), ("DONE", 7000, 360)], 1):
            (self.out / "jobs" / f"J00{i}.json").write_text(json.dumps({"id": f"J00{i}", "kind": "video", "model": "kling3_0", "status": st, "created_at": now - made,
                                                                          "claimed_at": now - made, "completed_at": now - made + took, "request": {"user": "u1"}}), encoding="utf-8")
        (self.out / "jobs" / "J004.json").write_text(json.dumps({"id": "J004", "kind": "video", "model": "kling3_0", "status": "CLAIMED", "created_at": now - 240,
                                                                   "claimed_at": now - 240, "external_task_id": "0f3c6a2e-1111-2222-3333-444455556666",
                                                                   "generation": "G007", "request": {"user": "u1"}}), encoding="utf-8")
        (self.out / "jobs" / "J005.json").write_text(json.dumps({"id": "J005", "kind": "video", "status": "CLAIMED", "created_at": now, "request": {"user": "u2"}}), encoding="utf-8")
        d = self.out / "G007"
        (d / "slices").mkdir(parents=True)
        sts = [{"index": i, "key": f"k{i}", "status": "READY" if i <= 2 else "BLOCKED", "reason": None if i <= 2 else "inside_cell", "review": {}} for i in range(1, 10)]
        (d / "result.json").write_text(json.dumps({"generation_id": "G007", "number": 7, "prompt": "teddy bear", "stage": "sliced", "owner": "u1", "grid": [3, 3],
                                                   "stickers": sts, "history": []}), encoding="utf-8")
        self.pings = []
        self.p1 = mock.patch.object(sp, "_ping_later", lambda out, tid, reason: sp.ping(out, tid, reason))
        self.p2 = mock.patch("mirsal.services.admin_bot.notify_support", lambda out, text: self.pings.append(text) or True)
        self.p1.start(); self.p2.start()

    def tearDown(self):
        self.p1.stop(); self.p2.stop()
        shutil.rmtree(self.out, ignore_errors=True)

    def test_where_is_my_video_names_the_job_and_says_when_it_finishes(self):
        acts = sp.activity(self.out, ME, "my video J004")
        j = next(h for h in acts if h["id"] == "J004")
        self.assertIn("still being made at Higgsfield", j["text"])
        self.assertIn("0f3c6a2e-1111-2222-3333-444455556666", j["text"])
        self.assertIn("usually takes about 6.0 minutes", j["text"], "the median of the person's finished video jobs")
        self.assertFalse(any(h["id"] == "J005" for h in acts), "another person's job is never a source")
        cv = sp.ask(self.out, ME, "I keep asking for a video and it never arrives", complete=cite_activity("J004", "Your video J004 is still rendering at Higgsfield."))
        a = cv["messages"][-1]
        self.assertEqual(a["actions"][0], {"kind": "open_batch", "id": "G007", "label": "Open G007 in the Studio"})
        self.assertEqual(sp.read(self.out, cv["id"])["watch"], ["J004"])
        self.assertEqual(sp.check_watches(self.out, ME), 0, "still running: nothing to say")
        p = self.out / "jobs" / "J004.json"
        jj = json.loads(p.read_text(encoding="utf-8")); jj["status"] = "DONE"; p.write_text(json.dumps(jj), encoding="utf-8")
        self.assertEqual(sp.check_watches(self.out, ME), 1)
        self.assertEqual(sp.check_watches(self.out, ME), 0, "said once")
        after = sp.read(self.out, cv["id"])
        self.assertIn("has finished: it is in batch G007", after["messages"][-1]["text"])
        self.assertEqual(after["status"], "resolved")
        self.assertEqual([n["kind"] for n in nt.listing(self.out, "u1")["notifications"]], ["update"])

    def test_only_two_of_nine_explains_the_blocked_stickers_and_offers_the_batch(self):
        b = next(h for h in sp.activity(self.out, ME, "G007") if h["id"] == "G007")
        self.assertIn("2 of 9 stickers accepted", b["text"])
        self.assertIn("S3: inside cell", b["text"])
        self.assertIn("Use it anyway", b["text"])
        self.assertEqual(sp.activity(self.out, OTHER, "G007"), [h for h in sp.activity(self.out, OTHER, "G007") if h["id"] != "G007"], "never another person's batch")

    def test_a_feature_request_is_its_own_kind_of_ticket(self):
        cv = sp.ask(self.out, ME, "Can I import my Photoshop edit back into the same pack?",
                    complete=lambda s, u: (json.dumps({"reply": "That is not possible yet.", "cites": [], "need": "none", "request": "feature"}), {}))
        self.assertEqual(cv["messages"][-1]["request"], "feature")
        e = sp.escalate(self.out, ME, cv["id"], "feature")
        t = tk.read(self.out, e["ticket"])
        self.assertEqual((t["issue"], t["context"]["kind"]), ("feature", "feature"))
        self.assertIn("feature request", e["messages"][-1]["text"])
        self.assertIn("asks for a feature", self.pings[0])
        self.assertEqual(sp.queue(self.out)[0]["kind"], "feature")
        with self.assertRaises(sp.SupportError):
            sp.escalate(self.out, ME, cv["id"], "gossip")

    def test_a_token_is_a_private_message_only_its_person_sees(self):
        cv = sp.escalate(self.out, ME, sp.ask(self.out, ME, "the Telegram tester needs a token", complete=answer("Ask the admin.", need="clarify"))["id"], "access")
        tid = cv["ticket"]
        sp.admin_reply(self.out, ADMIN, tid, "123456789:AAEFsecretsecretsecretsecretsecret", private=True)
        t = tk.read(self.out, tid)
        self.assertNotIn("AAEF", json.dumps(t), "the ticket never holds the secret")
        self.assertNotIn("AAEF", json.dumps(nt.listing(self.out, "u1")), "nor the notification")
        self.assertNotIn("AAEF", json.dumps(sp._redacted(sp.read(self.out, cv["id"]))), "nor the Postgres copy")
        mine = sp.view(sp.read(self.out, cv["id"]), ME)["messages"][-1]
        self.assertEqual((mine["private"], mine["text"][:13]), (True, "123456789:AAE"))
        self.assertNotIn("AAEF", json.dumps(sp.view(sp.read(self.out, cv["id"]), ADMIN)), "staff see that it was sent, not what")
        seen = {}
        sp.ask(self.out, ME, "thanks, and one more thing", cid=None, complete=lambda s, u: seen.setdefault("u", u) and (json.dumps({"reply": "Which?", "need": "clarify"}), {}))
        self.assertNotIn("AAEF", seen["u"], "no model ever reads it")
        sp.forget(self.out, ME, cv["id"], mine["id"])
        self.assertNotIn("AAEF", (self.out / "support" / f"{cv['id']}.json").read_text(encoding="utf-8"), "forgotten means erased from the record")
        with self.assertRaises(sp.SupportError):
            sp.forget(self.out, ADMIN, cv["id"], mine["id"])          # only its person can forget it


class SupportRouteTests(unittest.TestCase):
    """The native routes: privacy (a stranger's conversation is a 404), staff-only actions, members never see internal ticket fields, notifications read on open."""

    @classmethod
    def setUpClass(cls):
        import os
        import threading
        from mirsal.runtime import users as um
        from mirsal.console.server import serve
        cls.tmp = Path(tempfile.mkdtemp())
        cls.env = mock.patch.dict(os.environ, {"MIRSAL_API_TOKEN": "owner-token-for-the-test"})
        cls.loop = mock.patch.object(um, "LOOPBACK", ())
        cls.ping = mock.patch.object(sp, "_ping_later", lambda *a: None)
        cls.env.start(); cls.loop.start(); cls.ping.start()
        cls.srv, cls.c = serve(cls.tmp / "out", cls.tmp / "in", 0, block=False, stdlib=False)
        cls.c.lan = True
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        for email, name in (("m@nadi.ae", "Mona"), ("s@nadi.ae", "Sam")):
            a = cls.c.users.signup(email, name, "password1")
            cls.c.users.decide(a["id"], "approve")
        cls.mona = cls.c.users.login("m@nadi.ae", "password1")[1]
        cls.sam = cls.c.users.login("s@nadi.ae", "password1")[1]

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.c.release_writer()
        cls.ping.stop(); cls.loop.stop(); cls.env.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def req(self, method, path, body=None, cookie=None, owner=False):
        import http.client
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
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

    def test_a_member_asks_escalates_and_hears_back_and_nobody_else_sees_it(self):
        code, cv = self.req("POST", "/api/support/ask", {"text": "my uploads vanish"}, cookie=self.mona)
        self.assertEqual(code, 200, cv)
        self.assertEqual(cv["messages"][-1]["role"], "agent")
        self.assertNotIn("mode", cv["messages"][-1], "internal fields stay with staff")
        cid = cv["id"]
        self.assertEqual(self.req("GET", f"/api/support/conversations/{cid}", cookie=self.sam)[0], 404)
        self.assertEqual(self.req("GET", f"/api/support/conversations/{cid}", owner=True)[0], 404, "staff see a conversation once it reached a ticket")
        self.assertEqual(self.req("GET", "/api/support/queue", cookie=self.sam)[0], 403)
        code, cv = self.req("POST", f"/api/support/conversations/{cid}/escalate", {}, cookie=self.mona)
        self.assertEqual((code, cv["status"]), (200, "awaiting_admin"))
        tid = cv["ticket"]
        self.assertEqual(self.req("POST", f"/api/support/conversations/{cid}/escalate", {}, cookie=self.mona)[1]["ticket"], tid)
        self.assertEqual([t["id"] for t in self.req("GET", "/api/support/queue", owner=True)[1]["tickets"]], [tid])
        code, both = self.req("GET", f"/api/support/tickets/{tid}", owner=True)
        self.assertEqual((code, both["conversation"]["id"]), (200, cid))
        self.assertEqual(self.req("POST", f"/api/tickets/{tid}/reply", {"text": "Which browser?"}, cookie=self.sam)[0], 403)
        code, t = self.req("POST", f"/api/tickets/{tid}/reply", {"text": "Which browser?"}, owner=True)
        self.assertEqual((code, t["status"]), (200, "replied"))
        self.assertEqual(self.req("GET", "/api/notifications", cookie=self.mona)[1]["unread"], 1)
        self.assertEqual(self.req("GET", "/api/notifications", cookie=self.sam)[1]["unread"], 0)
        self.assertEqual(self.req("GET", f"/api/support/conversations/{cid}", cookie=self.mona)[1]["status"], "admin_replied")
        self.assertEqual(self.req("GET", "/api/notifications", cookie=self.mona)[1]["unread"], 0, "opening the conversation reads its notifications")
        self.assertEqual(self.req("POST", f"/api/support/conversations/{cid}/reply", {"text": "Firefox"}, cookie=self.mona)[1]["status"], "awaiting_admin")
        with mock.patch.object(sp, "_propose", lambda *a: None):
            code, t = self.req("POST", f"/api/tickets/{tid}/resolve", {"text": "Fixed: uploads over 8 MB were refused."}, owner=True)
        self.assertEqual((code, t["status"]), (200, "fixed"))
        code, mine = self.req("GET", f"/api/tickets/{tid}", cookie=self.mona)
        self.assertEqual(code, 200)
        self.assertNotIn("context", mine, "a member never sees the ticket's internal fields")
        self.assertNotIn("fingerprint", mine)
        self.assertEqual(self.req("GET", f"/api/tickets/{tid}", cookie=self.sam)[0], 404)

    def test_the_faq_a_member_reads_is_only_ever_published_text(self):
        f = faq.propose(self.c.out, title="Empty library", question="Why is my library empty?", answer="Packs are per person: sign in with your account.", by="local")
        self.assertEqual(self.req("GET", f"/api/faq/{f['id']}", cookie=self.mona)[0], 404, "a draft is not readable")
        self.assertEqual(self.req("POST", f"/api/faq/{f['id']}/publish", {}, cookie=self.mona)[0], 403)
        self.assertEqual(self.req("GET", "/api/faq?status=pending", owner=True)[1]["faq"][0]["id"], f["id"])
        code, p = self.req("POST", f"/api/faq/{f['id']}/publish", {}, owner=True)
        self.assertEqual((code, p["status"]), (200, "published"))
        code, pub = self.req("GET", f"/api/faq/{f['id']}", cookie=self.mona)
        self.assertEqual((code, sorted(pub)), (200, ["answer", "id", "looks_like", "question", "revision", "screen", "title", "updated"]))
        self.assertEqual([x["id"] for x in self.req("GET", "/api/faq?status=all", cookie=self.mona)[1]["faq"]], [f["id"]], "a member's list is the published one")


if __name__ == "__main__":
    unittest.main()
