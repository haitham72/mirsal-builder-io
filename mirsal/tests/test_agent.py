"""The agent end to end on a fake provider (docs/agent-and-chat.md 4A-4C exits): no network, no spend, no files but the session."""
import json
import tempfile
import threading
import unittest
from pathlib import Path

from mirsal import cache as cachemod
from mirsal.agent.brain import Brain
from mirsal.agent.graph import Agent
from mirsal.agent.memory import SessionError, SessionStore
from mirsal.agent.tools import FakeTools


def gen(gid, n=9, keys=None):
    keys = keys or [f"s{i}" for i in range(1, n + 1)]
    return {"generation": gid, "stickers": [{"id": f"{gid}/S{i}", "index": i, "key": keys[i - 1], "name": keys[i - 1], "tags": [keys[i - 1]],
                                             "emoji": ["😀"], "status": "READY", "still": "PENDING"} for i in range(1, n + 1)]}


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.out = Path(self.td.name)
        self.cache = cachemod.Cache(force_memory=True)
        self.store = SessionStore(self.out, self.cache)
        self.tools = FakeTools()
        self.said = []
        self.agent = Agent(self.store, self.tools, Brain(complete=self._llm), self.cache)
        self.sid = self.store.create()["id"]

    def tearDown(self):
        self.td.cleanup()

    def _llm(self, system, user):
        self.said.append(user)
        return "{}", {"model": "fake"}

    def say(self, text, **kw):
        return self.agent.run_turn(self.sid, text, **kw)

    def sess(self):
        return self.store.load(self.sid)

    def seed(self, gid="G012", keys=None, subject="banana", job=None):
        """A batch that already exists in this chat (as if the user made it earlier)."""
        self.tools.gens[gid] = gen(gid, keys=keys)
        s = self.sess()
        self.store.add_pass(s, subject, generation=gid, job=job, prompt=f"{subject} stickers", grid="3x3", style_id="flat_vector")
        s["focus"] = {"generation": gid, "stickers": []}
        self.store.save(s)


class NewAndConfirm(Base):
    def test_a_request_becomes_a_plan_with_a_price_and_nothing_is_spent(self):
        m = self.say("make me falcon stickers")
        self.assertEqual(m["cards"][0]["type"], "plan")
        self.assertEqual((m["cards"][0]["estimate"], len(m["cards"][0]["names"])), (2.0, 9))
        self.assertEqual([c.get("action") for c in m["chips"]], ["confirm", "cancel"])
        self.assertFalse([c for c in self.tools.calls if c[0] == "create"])            # no credits until the user says so
        self.assertIsNotNone(self.sess()["pending"])

    def test_confirm_by_button_or_by_word_starts_the_job_and_records_the_pass(self):
        self.say("falcon dancing")
        m = self.say("", action={"type": "confirm"})
        self.assertEqual(m["cards"][0]["job"], "J001")
        s = self.sess()
        self.assertIsNone(s["pending"])
        self.assertEqual(s["subjects"][0]["passes"][0]["job"], "J001")
        self.say("make me teddy stickers")
        m2 = self.say("yes")                                                            # a typed go-ahead works too
        self.assertEqual(m2["cards"][0]["type"], "generation")
        self.assertEqual(len([c for c in self.tools.calls if c[0] == "create"]), 2)

    def test_cancel_spends_nothing(self):
        self.say("make me falcon stickers")
        m = self.say("no")
        self.assertIsNone(self.sess()["pending"])
        self.assertIn("nothing was spent", m["text"])
        self.assertFalse([c for c in self.tools.calls if c[0] == "create"])

    def test_instant_mode_creates_without_asking(self):
        self.say("don't ask me before spending")
        self.assertFalse(self.sess()["settings"]["ask_before_spending"])
        m = self.say("make me falcon stickers")
        self.assertEqual(m["cards"][-1]["type"], "generation")
        self.assertEqual(len([c for c in self.tools.calls if c[0] == "create"]), 1)

    def test_without_a_provider_it_is_free_and_starts_at_once(self):
        self.tools._live = False
        m = self.say("make me falcon stickers")
        self.assertEqual(m["cards"][-1]["generation"], "G001")
        self.assertEqual(self.sess()["focus"]["generation"], "G001")

    def test_the_step_trace_reads_like_the_queue(self):
        m = self.say("make me falcon stickers")
        steps = [(s["kind"], s["label"]) for s in m["steps"]]
        self.assertEqual(steps[0], ("task", "generating falcon"))
        self.assertIn(("step", "expand prompt"), steps)
        self.assertEqual(steps[-1][0], "final")
        self.assertTrue(next(s for s in m["steps"] if s["label"] == "expand prompt")["detail"]["lines"])


class MemoryAndSummary(Base):
    def test_every_subject_keeps_the_metadata_of_its_passes(self):
        self.seed("G012", subject="banana")
        self.say("I like 2 and 7 but not 3 and 4")
        s = self.sess()
        p = s["subjects"][0]["passes"][0]
        self.assertEqual((p["liked"], p["disliked"]), (["G012/S2", "G012/S7"], ["G012/S3", "G012/S4"]))
        text = self.store.summary_text(s)
        self.assertIn("Subject 'banana'", text)
        self.assertIn("G012", text)
        self.assertIn("liked S2, S7", text)
        self.assertIn("disliked S3, S4", text)

    def test_feedback_is_temporary_unless_the_user_says_so(self):
        self.seed()
        self.say("I hate 4")
        self.assertEqual(self.sess()["feedback"][-1]["scope"], "TEMPORARY")
        self.assertEqual(self.sess()["preferences"]["persistent"], [])
        self.say("I never want dark outlines, I hate 4")
        self.assertEqual(self.sess()["feedback"][-1]["scope"], "PERSISTENT")
        self.assertTrue(self.sess()["preferences"]["persistent"])

    def test_a_trait_asked_for_twice_becomes_a_note_and_part_of_the_next_plan(self):
        self.say("make me falcon stickers")
        self.say("no")
        self.say("make me a dog, with a wider range of emotions")
        self.say("no")
        self.say("make me a cat with more different emotions please")
        m = self.say("no")
        self.say("make me a cow stickers")
        last = self.sess()["messages"][-1]
        notes = [s["label"] for s in last["steps"] if s["kind"] == "note"]
        self.assertTrue(any("wider range of emotions" in n for n in notes), notes)
        self.assertIn("wider range of emotions", last["cards"][0]["prompt"])

    def test_temporary_dislikes_shape_only_the_next_pass(self):
        self.seed()
        self.say("I hate 4")
        self.say("make me falcon stickers")
        notes = [s["label"] for s in self.sess()["messages"][-1]["steps"] if s["kind"] == "note"]
        self.assertTrue(any("S4" in n for n in notes), notes)
        self.say("no")
        self.say("make me cow stickers")
        notes2 = [s["label"] for s in self.sess()["messages"][-1]["steps"] if s["kind"] == "note"]
        self.assertFalse(any("S4" in n for n in notes2))                                # used once, never a lasting preference

    def test_the_reducer_keeps_every_id(self):
        self.seed("G012")
        self.say("I like 2 and 7 but not 3 and 4")
        for i in range(20):
            self.say(f"hello {i}")
        s = self.sess()
        self.assertGreater(s["summary"]["upto"], 0)
        text = self.store.summary_text(s)
        for needle in ("G012", "liked S2, S7", "disliked S3, S4"):
            self.assertIn(needle, text)

    def test_the_model_gets_the_summary_not_the_history(self):
        self.seed("G012", subject="banana")
        self.agent.brain = Brain(complete=lambda s, u: (self.said.append(u) or '{"intents":["ASK"],"confidence":0.9}', {"model": "f"}))
        self.say("blorp zzz qqq vvv www xxx yyy zzz aaa bbb ccc")                         # the rules are unsure: the model is asked
        self.assertTrue(self.said)
        self.assertIn("Subject 'banana'", self.said[0])
        self.assertNotIn("blorp blorp", self.said[0])


class EditsAskAndReview(Base):
    def test_edit_one_sticker_is_a_child_generation_and_the_rest_stays(self):
        self.seed("G012", keys=["banana_dancing", "banana_shocked", "banana_squashed", "dog_banana", "x5", "x6", "x7", "x8", "x9"])
        m = self.say("make number 3 less flattened")
        self.assertIn("pending", self.sess() and self.sess())
        p = self.sess()["pending"]
        self.assertEqual((p["type"], len(p["items"]), p["items"][0]["regen_of"], p["items"][0]["parent"]), ("batch", 1, "G012/S3", "G012"))
        self.assertIn("flattened", p["items"][0]["prompt"])
        self.say("yes")
        c = [x for x in self.tools.calls if x[0] == "create"][0]
        self.assertEqual((c[2], c[3], c[4]), ("1x1", "G012", "G012/S3"))
        pa = self.sess()["subjects"][0]["passes"][-1]
        self.assertEqual(pa["parent"], "G012")

    def test_select_two_and_make_these_more_energetic(self):
        self.seed("G012")
        self.say("make these more energetic", selected=["G012/S2", "G012/S7"])
        p = self.sess()["pending"]
        self.assertEqual([i["regen_of"] for i in p["items"]], ["G012/S2", "G012/S7"])

    def test_which_one_is_the_shocked_banana_is_answered_from_metadata_with_no_generation(self):
        self.seed("G013", keys=["banana_dancing", "banana_shocked", "banana_squashed", "a", "b", "c", "d", "e", "f"])
        before = list(self.tools.calls)
        m = self.say("which one is the shocked banana?")
        self.assertIn("G013/S2", m["text"])
        self.assertEqual(self.tools.calls, before)                                       # no generation, no image analysis, no model needed
        self.assertEqual(self.sess()["focus"]["stickers"], ["G013/S2"])

    def test_two_plausible_stickers_ask_one_short_question_with_chips(self):
        self.seed("G012", keys=["dog_banana", "dog_banana_waving", "c", "d", "e", "f", "g", "h", "i"])
        m = self.say("make the dog banana happier")
        self.assertTrue(m["chips"])
        self.assertLess(len(m["text"]), 60)

    def test_approve_all_but_5_and_6_records_a_human_decision_for_the_rest(self):
        self.seed("G012")
        m = self.say("approve all but 5 and 6")
        call = [c for c in self.tools.calls if c[0] == "review"][0]
        self.assertEqual((call[2], call[3]), ("APPROVE", [1, 2, 3, 4, 7, 8, 9]))
        self.assertIn("Approved S1", m["text"])

    def test_animate_asks_first_then_starts_the_job(self):
        self.seed("G012")
        self.say("animate")
        self.assertEqual(self.sess()["pending"]["type"], "animate")
        self.assertFalse([c for c in self.tools.calls if c[0] == "animate"])
        m = self.say("yes")
        self.assertEqual([c[0] for c in self.tools.calls if c[0] == "animate"], ["animate"])
        self.assertTrue(m["cards"][0]["animating"])

    def test_another_is_a_child_pass_of_the_focus(self):
        self.seed("G012", subject="banana")
        self.say("another one")
        self.assertEqual(self.sess()["pending"]["parent"], "G012")
        self.say("yes")
        self.assertEqual(self.sess()["subjects"][0]["passes"][-1]["parent"], "G012")

    def test_the_previous_one_means_the_parent_in_this_branch(self):
        self.seed("G011")
        self.seed("G012")
        self.tools.gens["G012"]["parent"] = "G011"
        self.tools.gens["G012"]["generation"] = "G012"
        self.seed("G013")
        s = self.sess()
        s["focus"] = {"generation": "G012", "stickers": []}
        self.store.save(s)
        self.say("what happened to the previous one")
        self.assertEqual(self.sess()["interactions"][-1]["resolved"]["generation"], "G011")


class SettingsSearchAndSafety(Base):
    def test_settings_change_and_persist(self):
        self.say("use 2x2 please")
        st = self.sess()["settings"]
        self.assertEqual(st["grid"], "2x2")
        self.assertNotIn("animate", st)
        m = self.say("make me falcon stickers")
        self.assertEqual(m["cards"][0]["grid"], "2x2")

    def test_search_returns_a_carousel_card(self):
        self.seed("G012", keys=["banana_dancing"] + ["x"] * 8)
        m = self.say("find my banana stickers")
        self.assertEqual(m["cards"][0]["type"], "stickers")

    def test_a_second_message_while_one_is_running_is_refused_not_queued_blindly(self):
        started, release = threading.Event(), threading.Event()

        def slow(prompt, grid, style_id, ai):
            started.set()
            release.wait(5)
            return FakeTools.plan(self.tools, prompt, grid, style_id, ai)
        self.tools.plan = slow
        t = threading.Thread(target=lambda: self.say("make me falcon stickers"))
        t.start()
        started.wait(5)
        with self.assertRaises(SessionError) as cm:
            self.say("hello")
        self.assertEqual(cm.exception.code, 409)
        release.set()
        t.join(10)

    def test_a_failure_inside_a_node_is_a_calm_sentence_and_spends_nothing(self):
        self.tools.plan = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        m = self.say("make me falcon stickers")
        self.assertEqual(m["status"], "error")
        self.assertIn("nothing was spent", m["text"])
        self.assertNotIn("boom", m["text"])
        self.assertFalse([c for c in self.tools.calls if c[0] == "create"])

    def test_hello_gets_suggestions_not_a_generation(self):
        m = self.say("hello")
        self.assertTrue(m["chips"])
        self.assertEqual(m["cards"], [])

    def test_sessions_persist_and_resume(self):
        self.seed("G012")
        self.say("I like 2")
        again = SessionStore(self.out, self.cache).load(self.sid)
        self.assertEqual(again["focus"]["generation"], "G012")
        self.assertEqual(len(again["interactions"]), 1)
        self.assertEqual([x["id"] for x in SessionStore(self.out, self.cache).list()], [self.sid])

    def test_session_ids_cannot_escape_the_folder(self):
        for bad in ("../x", "S1/../../y", "x"):
            with self.assertRaises(SessionError):
                self.store.load(bad)


if __name__ == "__main__":
    unittest.main()
