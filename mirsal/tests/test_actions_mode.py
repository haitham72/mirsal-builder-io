"""Predefined or creative stickers (Haitham, 2026-10-11): a plan's nine actions come from the 36 bank actions, or from the AI / the mood bank as before."""
import unittest

from mirsal.generation import actions, tasks


class ActionsModeTests(unittest.TestCase):
    def test_predefined_draws_the_first_nine_bank_actions_as_whole_characters(self):
        p = tasks.preview("kid superman", "3x3", actions_mode="predefined")
        self.assertEqual(p["actions_mode"], "predefined")
        self.assertEqual([s["key"].rsplit("_", 1)[-1] for s in p["stickers"]][:3], ["happy", "laugh", "cry"])
        self.assertFalse(p["slots"]["face"], "a character is drawn whole, not as a face")
        self.assertEqual(len(p["stickers"]), 9)
        self.assertGreater(p["batches_max"], 1, "the rest of the 36 follow as the next batches")

    def test_creative_is_todays_plan_and_an_emoji_pack_is_the_36_either_way(self):
        self.assertNotEqual(tasks.preview("kid superman", "3x3").get("actions_mode"), "predefined")
        a, b = tasks.preview("cat emojis", "3x3"), tasks.preview("cat emojis", "3x3", actions_mode="predefined")
        self.assertEqual([s["key"] for s in a["stickers"]], [s["key"] for s in b["stickers"]])
        self.assertEqual(a["slots"]["preset"], "core-v1")

    def test_an_unknown_mode_is_refused(self):
        with self.assertRaises(Exception):
            tasks.preview("kid superman", "3x3", actions_mode="random")

    def test_the_bank_is_the_four_grids(self):
        self.assertEqual(set(actions.ACTION_BANK), {t for g in actions.PRESETS.values() for t in g})


if __name__ == "__main__":
    unittest.main()
