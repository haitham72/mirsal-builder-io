"""Help & Support's records (flow/faq.py, flow/support_kb.py, flow/notifications.py, obs/scrub.py): the FAQ's draft / published / revision rules, what the
index reads and never reads, who may search code, notifications once per event, and scrubbing. Isolated out/ and repo, no Postgres, no model."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from mirsal.flow import faq, notifications as nt, support_kb as kb, tickets as tk
from mirsal.obs.scrub import scrub_personal, scrub_secrets


def make_repo(root: Path) -> Path:
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "inputs").mkdir()
    (root / "docs" / "particles.md").write_text("# Particles\n\nIntro.\n\n## Echo burst\n\nThe Echo chat plays the burst out of the heart badge when a sticker is liked.\n\n"
                                                "## Saving\n\nSave turns a draft into the next row.\n", encoding="utf-8")
    (root / "docs" / "inputs" / "private.md").write_text("# Private\n\nnever read this\n", encoding="utf-8")
    code = root / "mirsal" / "mirsal" / "flow"
    code.mkdir(parents=True)
    (root / "mirsal" / "mirsal" / "__init__.py").write_text("", encoding="utf-8")
    (code / "uploader.py").write_text('TOKEN = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789ab"\n\n'
                                      "def resize_upload(img):\n    # uploads above the zebra limit are shrunk to 1600 px before saving\n    return img\n", encoding="utf-8")
    (root / "mirsal" / ".env").write_text("OPENAI_API_KEY=sk-secretsecretsecretsecret\n", encoding="utf-8")
    (root / "mirsal" / "mirsal" / ".env").write_text("SECRET=1\n", encoding="utf-8")
    return root


class ScrubTests(unittest.TestCase):
    def test_personal_details_secrets_and_ids_never_reach_a_shared_entry(self):
        s = scrub_personal("Haitham (h@nadi.ae) saw G104 and T012 fail; token 123456789:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789ab at C:\\Users\\me\\out\\x.json",
                           names=["Haitham"])
        for gone in ("h@nadi.ae", "G104", "T012", "ABCdefGHI", "Users\\me", "Haitham"):
            self.assertNotIn(gone, s)
        self.assertIn("<email>", s)
        self.assertIn("password=<secret>", scrub_secrets("password=hunter22hunter"))


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def test_one_notification_per_event_and_reading_is_per_person(self):
        a = nt.add(self.out, "u1", "reply:T001:1", "reply", "Support answered", ticket="T001", conversation="C001")
        b = nt.add(self.out, "u1", "reply:T001:1", "reply", "Support answered again", ticket="T001", conversation="C001")
        self.assertEqual(a["id"], b["id"], "a retried event never notifies twice")
        nt.add(self.out, "u1", "resolved:T001:0", "resolved", "Resolved", ticket="T001", conversation="C001")
        nt.add(self.out, "u2", "reply:T009:1", "reply", "Someone else's", ticket="T009", conversation="C009")
        self.assertEqual(nt.listing(self.out, "u1")["unread"], 2)
        self.assertEqual(nt.listing(self.out, "u2")["unread"], 1, "another person's notifications are their own")
        self.assertEqual(nt.mark_read(self.out, "u1", conversation="C001")["unread"], 0)
        self.assertEqual(nt.listing(self.out, "u2")["unread"], 1)
        with self.assertRaises(ValueError):
            nt.add(self.out, "u1", "", "reply", "x")


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.repo = make_repo(Path(tempfile.mkdtemp()))

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)
        shutil.rmtree(self.repo, ignore_errors=True)

    def test_the_index_reads_docs_and_code_never_env_files_or_inputs_and_scrubs_secrets(self):
        r = kb.reindex(self.out, self.repo, embedder=None)
        files = kb.read_index(self.out)["files"]
        self.assertEqual(sorted(files), ["docs/particles.md", "mirsal/mirsal/__init__.py", "mirsal/mirsal/flow/uploader.py"])
        text = json.dumps(files)
        self.assertNotIn("ABCdefGHI", text, "a token in the code is scrubbed before it is kept")
        self.assertNotIn("never read this", text)
        self.assertGreaterEqual(r["chunks"]["doc"], 2)
        self.assertFalse(r["vectors"], "no Postgres in a test: lexical only")
        again = kb.reindex(self.out, self.repo, embedder=None)
        self.assertEqual(again["changed"], 0, "an unchanged file is never cut again")

    def test_members_never_get_code_and_staff_get_it_only_when_faq_and_docs_fall_short(self):
        kb.reindex(self.out, self.repo, embedder=None)
        member = kb.search(self.out, "zebra limit upload shrunk", "member")
        self.assertFalse(any(h["kind"] == "code" for h in member["hits"]))
        staff = kb.search(self.out, "zebra limit upload shrunk", "staff")
        self.assertTrue(staff["code_used"])
        self.assertTrue(any(h["kind"] == "code" and h["path"] == "mirsal/mirsal/flow/uploader.py" for h in staff["hits"]))
        doc = kb.search(self.out, "echo burst heart badge liked", "staff")
        self.assertTrue(doc["enough"])
        self.assertFalse(doc["code_used"], "the docs answered: the code is not read")
        self.assertEqual(doc["hits"][0]["path"], "docs/particles.md")


class FaqTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def hits(self, q):
        return [h["id"] for h in kb.search(self.out, q)["hits"] if h["kind"] == "faq"]

    def test_a_draft_never_answers_a_publish_does_and_a_revision_keeps_the_old_text(self):
        f = faq.propose(self.out, title="Burst too slow", question="Why is the particle burst slow in the chat?", answer="Shorten its duration in the editor.", by="admin")
        self.assertEqual(f["status"], "draft")
        self.assertEqual(self.hits("particle burst slow chat"), [], "a draft is never an answer")
        with self.assertRaises(KeyError):
            faq.public(f)
        p = faq.publish(self.out, f["id"], "admin")
        self.assertEqual((p["status"], p["revision"]), ("published", 1))
        self.assertEqual(self.hits("particle burst slow chat"), [f["id"]])
        self.assertEqual(faq.publish(self.out, f["id"], "admin")["revision"], 1, "publishing twice changes nothing")
        r = faq.propose(self.out, title="Burst too slow", question="Why is the particle burst slow?", answer="Set the duration to 1.2 s in the particle editor.",
                        by="admin", target=f["id"])
        self.assertTrue(r["pending"])
        self.assertIn("Shorten", kb.search(self.out, "particle burst slow")["hits"][0]["text"], "the pending text is not served before it is published")
        p2 = faq.publish(self.out, f["id"], "admin")
        self.assertEqual(p2["revision"], 2)
        self.assertIn("1.2 s", p2["answer"])
        self.assertEqual(p2["revisions"][0]["answer"], "Shorten its duration in the editor.")
        faq.archive(self.out, f["id"], "admin")
        self.assertEqual(self.hits("particle burst slow chat"), [])

    def test_a_resolved_ticket_proposes_once_scrubbed_and_a_known_question_becomes_a_revision(self):
        t = tk.open_support(self.out, user="u7", text="Telegram send fails for my pack", context={"conversation": None}, draft=False)
        tk.add_message(self.out, t["id"], "admin", "local", "Re-export the pack: the webm was over 256 KB.")
        fake = lambda s, u: (json.dumps({"title": "Telegram send fails", "question": "Why does sending my pack to Telegram fail?",
                                         "answer": "Write to ops@nadi.ae about T001. A file over 256 KB is refused: re-export the pack."}), {})
        f = faq.propose_from_ticket(self.out, t["id"], "local", complete=fake)
        self.assertEqual(f["status"], "draft")
        self.assertNotIn("ops@nadi.ae", f["answer"])
        self.assertNotIn("T001", f["answer"])
        self.assertEqual(f["provenance"][0]["ticket"], t["id"])
        self.assertEqual(faq.propose_from_ticket(self.out, t["id"], "local", complete=fake)["id"], f["id"], "one proposal per ticket")
        faq.publish(self.out, f["id"], "local")
        t2 = tk.open_support(self.out, user="u8", text="Telegram send fails", context={"conversation": None}, draft=False)
        tk.add_message(self.out, t2["id"], "admin", "local", "Re-export it smaller.")
        g = faq.propose_from_ticket(self.out, t2["id"], "local", complete=fake)
        self.assertEqual(g["id"], f["id"], "the same question is a revision of the published entry, not a twin")
        self.assertTrue(g["pending"])

    def test_with_no_model_the_admins_own_words_are_the_answer_and_nothing_to_say_is_no_proposal(self):
        t = tk.open_support(self.out, user="u7", text="The library is empty", context={"conversation": None}, draft=False)
        self.assertIsNone(faq.propose_from_ticket(self.out, t["id"], "local", complete=lambda s, u: (_ for _ in ()).throw(RuntimeError("down"))))
        tk.add_message(self.out, t["id"], "admin", "local", "Your packs are per person now: sign in with your own account.")
        f = faq.propose_from_ticket(self.out, t["id"], "local", complete=lambda s, u: (_ for _ in ()).throw(RuntimeError("down")))
        self.assertIn("per person", f["answer"])


if __name__ == "__main__":
    unittest.main()
