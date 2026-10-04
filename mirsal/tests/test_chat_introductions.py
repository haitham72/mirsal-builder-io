"""Haitham's transcript (2026-10-04): "hello from haitham" became a 9-sticker plan, "it is 'haitham'" replaced the held plan with the subject "it is haitham", "what is my name?" had no
answer, and the AI-vision question came with a hello. A greeting, a name or a question is answered or remembered, never planned; only a request to make something is a plan."""
import unittest

from mirsal.agent.resolver import classify, introduced_name
from tests.test_agent import Base


class TheTranscript(Base):
    def plans(self, m):
        return [c for c in m["cards"] if c.get("type") == "plan"]

    def test_hello_from_a_name_is_remembered_and_never_a_plan(self):
        m = self.say("hello from haitham")
        self.assertEqual(self.plans(m), [])
        self.assertIsNone(self.sess().get("pending"))
        self.assertIn("Nice to meet you, Haitham", m["text"])
        self.assertNotIn("vision", m["text"].lower(), "a hello has nothing to look at: no AI-vision question")
        self.assertEqual(self.say("what is my name?")["text"], "You're Haitham.")
        self.assertIn("Hi Haitham!", self.say("hi")["text"])

    def test_a_name_said_while_a_plan_is_held_keeps_the_plan(self):
        self.say("make me falcon stickers")
        held = self.sess()["pending"]
        m = self.say("it is 'haitham'")
        self.assertEqual(self.plans(m), [])
        self.assertEqual(self.sess()["pending"]["subject"], held["subject"], "the falcon plan is still the one held")
        self.assertNotIn("replaces the plan", m["text"])
        self.assertIn("still waiting", m["text"])

    def test_no_name_yet_is_said_plainly(self):
        self.assertIn("haven't told me your name", self.say("what is my name?")["text"])

    def test_a_statement_is_not_a_subject(self):
        for text in ("I am tired", "it is cute", "that's it"):
            with self.subTest(text=text):
                self.assertEqual(self.plans(self.say(text)), [])
                self.assertIsNone(self.sess().get("pending"))


class TheRules(unittest.TestCase):
    def test_who_introduces_themselves(self):
        cases = {"hello from haitham": "Haitham", "it is 'haitham'": "Haitham", "It is Haitham": "Haitham", "my name is Haitham": "Haitham", "call me sam": "Sam",
                 "I'm Haitham": "Haitham", "hi, it's Amira": "Amira", "hey Sam here": "Sam",
                 "hi falcon": None, "I am tired": None, "it is cute": None, "hello kitty": None, "I'm Batman stickers": None, "make me a falcon": None}
        for text, name in cases.items():
            with self.subTest(text=text):
                self.assertEqual(introduced_name(text), name)

    def test_only_a_request_is_new(self):
        for text in ("hello from haitham", "it is 'haitham'", "what is my name?", "I am tired", "that's it"):
            with self.subTest(text=text):
                self.assertNotIn(classify(text, True, False)[0][0], ("NEW", "NEW_MULTI"))
        for text in ("make me a falcon", "falcon dancing", "a cat in a hat", "i want a teddy bear"):
            with self.subTest(text=text):
                self.assertEqual(classify(text, False, False)[0], ["NEW"])


if __name__ == "__main__":
    unittest.main()
