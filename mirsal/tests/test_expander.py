"""Subject -> the full named set (AI), with lint, one repair round and the built-in sets as the fallback. The model is replaced by a fake: no network, no key."""
import json
import os
import unittest

from mirsal import expander, llm, prompter, tasks

ACTIONS = ["waving hello", "laughing out loud", "sleeping on a cloud", "flying fast", "holding a gift", "thinking hard", "dancing", "surprised", "giving a thumbs up"]


def cells(labels=ACTIONS):
    return [{"label": a, "key": a.replace(" ", "_"), "tags": ["fun"], "emoji": ["\U0001F600"]} for a in labels]


def good(desc="a young brown saker falcon chick with big eyes"):
    return json.dumps({"subject_description": desc, "cells": cells()})


class Fake:
    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def __call__(self, system, user):
        self.calls.append(user)
        a = self.answers.pop(0)
        if isinstance(a, Exception):
            raise a
        return a, {"model": "fake-model"}


class ExpanderTests(unittest.TestCase):
    def setUp(self):
        self.key = os.environ.pop(llm.KEY_VAR, None)
        llm._ENV_LOADED = True                       # do not read a real mirsal/.env during the tests

    def tearDown(self):
        if self.key is not None:
            os.environ[llm.KEY_VAR] = self.key

    def test_ai_names_every_sticker_and_the_template_builds_the_prompts(self):
        f = Fake(good())
        plan = expander.expand("falcon", (3, 3), use_ai=True, complete=f)
        self.assertEqual((plan["expanded_by"], plan["expand_model"], len(plan["stickers"])), ("ai", "fake-model", 9))
        keys = [s["key"] for s in plan["stickers"]]
        self.assertEqual(len(set(keys)), 9)
        self.assertTrue(all(k.startswith("falcon_") for k in keys), keys)
        self.assertEqual(plan["stickers"][0]["key"], "falcon_waving_hello")
        self.assertTrue(all(s["tags"][0] == s["key"] and 1 <= len(s["tags"]) <= 5 and s["emoji"] for s in plan["stickers"]))
        self.assertIn("a young brown saker falcon chick", plan["sheet_prompt"])                 # the saved template, filled: not free text
        self.assertTrue(all(prompter.MARGIN.split(",")[0] in s["prompt"] for s in plan["stickers"]))
        prompter.validate_plan(json.loads(json.dumps(plan)))                                      # same contract as every other plan

    def test_one_repair_round_then_the_built_in_sets(self):
        f = Fake(json.dumps({"subject_description": "x", "cells": cells(ACTIONS[:8])}), good())
        plan = expander.expand("falcon", (3, 3), use_ai=True, complete=f)
        self.assertEqual(plan["expanded_by"], "ai")
        self.assertIn("exactly 9", f.calls[1])                                                     # the repair prompt names the problem
        bad = json.dumps({"subject_description": "x", "cells": cells(ACTIONS[:8])})
        plan = expander.expand("falcon", (3, 3), use_ai=True, complete=Fake(bad, bad))
        self.assertEqual(plan["expanded_by"], "deterministic")
        self.assertIn("did not pass", plan["expand_error"])
        self.assertEqual(len(plan["stickers"]), 9)                                                 # a usable plan either way

    def test_lint_catches_duplicates_banned_words_and_missing_emoji(self):
        c = cells(); c[1]["label"] = c[0]["label"]; c[2]["label"] = "holding a flag"; c[3]["emoji"] = []
        p = expander._lint(c, 9, "falcon", "falcon")
        self.assertTrue(any("repeats the label" in x for x in p) and any("banned" in x for x in p) and any("emoji" in x for x in p), p)

    def test_failures_fall_back_without_raising(self):
        for ans in (llm.LLMError("Cannot reach the AI service: timed out"), "not json at all"):
            plan = expander.expand("falcon", (3, 3), use_ai=True, complete=Fake(ans, ans))
            self.assertEqual((plan["expanded_by"], len(plan["stickers"])), ("deterministic", 9))
            self.assertTrue(plan["expand_error"])

    def test_no_key_means_the_built_in_sets_and_says_so(self):
        plan = expander.expand("falcon", (3, 3), use_ai=True)
        self.assertEqual(plan["expanded_by"], "deterministic")
        self.assertIn(llm.KEY_VAR, plan["expand_error"])
        self.assertEqual(expander.expand("falcon", (3, 3))["expanded_by"], "deterministic")      # AI off: untouched behaviour
        with self.assertRaises(llm.LLMError):
            llm.complete("s", "u")

    def test_a_green_subject_gets_the_blue_key(self):
        plan = expander.expand("frog", (3, 3), use_ai=True, complete=Fake(good("a green frog with big eyes")))
        self.assertEqual(plan["slots"]["key_colour"], "blue")
        self.assertEqual(expander.expand("falcon", (3, 3), use_ai=True, complete=Fake(good()))["slots"]["key_colour"], "green")

    def test_the_inbox_preview_can_use_it(self):
        p = tasks.preview("falcon", "3x3", "flat_vector", ai=True)           # no key here -> built-in sets, and it says so
        self.assertEqual((p["expanded_by"], len(p["stickers"])), ("deterministic", 9))

class MotionTests(unittest.TestCase):
    def test_motion_lines_from_the_model_reach_the_video_prompt(self):
        answer = json.dumps({"subject_description": "a small cartoon owl", "cells": [
            {"label": f"owl pose number {i} with a huge expression", "motion": f"the owl does move number {i} with a bounce", "key": f"pose_{i}", "tags": [], "emoji": ["🦉"]}
            for i in range(1, 10)]})
        plan = expander.expand("owl", (3, 3), use_ai=True, complete=Fake(answer))
        self.assertEqual(plan["expanded_by"], "ai")
        self.assertEqual(plan["slots"]["cells"][3]["motion"], "the owl does move number 4 with a bounce")
        self.assertIn("4. the owl does move number 4 with a bounce", plan["video_prompt"])
        bad = json.loads(answer)
        bad["cells"][0]["motion"] = "adds a caption and a logo"
        self.assertTrue(expander._lint(bad["cells"], 9, "owl", "owl"))                         # banned words are caught in motions too



if __name__ == "__main__":
    unittest.main()