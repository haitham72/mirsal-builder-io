"""The prompts of the particle effects: template-locked (a plan in, text out), linted, with the screen colour chosen by the pieces."""
import unittest

from mirsal.generation import effect_prompts as ep


class EffectPromptTests(unittest.TestCase):
    PLAN = {"subject": "strawberry", "elements": ["ripe red strawberries", "tiny seeds", "small gold sparkles"]}

    def test_a_burst_starts_and_ends_empty_and_has_no_start_image(self):
        t = ep.video_prompt(self.PLAN, 2, 2)
        self.assertIn("#00FF00 green screen", t)
        self.assertIn("empty green screen again until the end", t)
        for must in ("0.0 to 0.4 seconds the cell is completely empty", "gravity takes over", "By 2.6 seconds every piece has left", "until the end at 3.0 seconds", "2 by 2", "cell 4"):
            self.assertIn(must, t)
        self.assertNotIn("start image", t.lower())

    def test_the_screen_is_blue_when_a_piece_is_green(self):
        self.assertEqual(ep.key_colour_for(["ripe red strawberries"]), "green")
        self.assertEqual(ep.key_colour_for(["strawberries", "green leaves"]), "blue")
        self.assertIn("#0000FF blue", ep.video_prompt({"subject": "strawberry", "elements": ["red strawberries", "green leaves"]}, 2, 2))

    def test_three_by_three_has_nine_different_takes(self):
        t = ep.video_prompt(self.PLAN, 3, 3)
        self.assertIn("3 by 3", t)
        self.assertEqual(sum(f"cell {i}" in t for i in range(1, 10)), 9)
        self.assertEqual(len({v for v in ep.VARIATIONS if v in t}), 9)

    def test_the_plan_is_linted_with_a_reason_a_person_can_act_on(self):
        for bad, why in (({"subject": "", "elements": ["x"]}, "subject"), ({"subject": "cat", "elements": []}, "at least one piece"),
                         ({"subject": "cat", "elements": ["a sticker of a cat"]}, "sticker"), ({"subject": "cat", "elements": ["one two three four five six"]}, "too long"),
                         ({"subject": "cat", "elements": [f"p{i}" for i in range(10)]}, "at most 9"), ({"subject": "cat", "elements": ["paws"], "style": "with text"}, "style")):
            with self.assertRaises(ValueError) as cm:
                ep.lint_plan(bad)
            self.assertIn(why, str(cm.exception))
        self.assertEqual(ep.lint_plan({"subject": " Cat ", "elements": ["paws", "PAWS", " ears. "]})["elements"], ["paws", "ears"])
        with self.assertRaises(ValueError):
            ep.video_prompt(self.PLAN, 4, 4)

    def test_describe_is_what_the_page_shows(self):
        d = ep.describe(self.PLAN, 2, 2)
        self.assertEqual((d["template"], d["version"], d["key"], d["grid"]), ("effect_video", 1, "green", [2, 2]))
        self.assertEqual(d["prompt"], ep.video_prompt(self.PLAN, 2, 2))


if __name__ == "__main__":
    unittest.main()
