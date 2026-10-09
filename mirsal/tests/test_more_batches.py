"""One Generate, several batches (generation/tasks.more_batches, batches_max): the next preset grids of an emoji pack, else the next bank actions. Pure: no provider."""
import unittest

from mirsal.generation import actions, tasks


class MoreBatchesTests(unittest.TestCase):
    def test_an_emoji_pack_goes_through_its_four_grids_once(self):
        p = tasks.preview("generic emojis")
        self.assertEqual((p["slots"]["preset"], p["batches_max"]), ("core-v1", 4))
        more = tasks.more_batches("generic emojis", p, 3)
        self.assertEqual([m["slots"]["preset"] for m in more], ["social-v1", "reactions-v1", "daily-v1"])
        keys = [s["key"] for x in [p, *more] for s in x["stickers"]]
        self.assertEqual(len(keys), 36)
        self.assertEqual(len(set(keys)), 36, "36 different actions, none twice")
        self.assertEqual(len(tasks.more_batches("generic emojis", p, 9)), 3, "never more than the grids left")

    def test_a_named_grid_is_skipped_not_repeated(self):
        p = tasks.preview("generic emojis social-v1")
        self.assertEqual([m["prompt"] for m in tasks.more_batches("generic emojis social-v1", p, 3)],
                         ["generic emojis core-v1", "generic emojis reactions-v1", "generic emojis daily-v1"])

    def test_any_other_request_takes_the_next_unused_bank_actions(self):
        p = tasks.preview("a teddy bear")
        more = tasks.more_batches("a teddy bear", p, 2)
        self.assertEqual(len(more), 2)
        used = [actions.canonical_for(s["key"], s["tags"]) for x in [p, *more] for s in x["stickers"]]
        names = [u[0] for u in used if u]
        self.assertEqual(len(names), len(set(names)), "no action twice across the batches")

    def test_one_character_changed_is_one_batch(self):
        self.assertEqual(tasks.preview("turn the banana into a pirate")["batches_max"], 1)
        self.assertEqual(tasks.more_batches("turn the banana into a pirate", tasks.preview("turn the banana into a pirate"), 3), [])


if __name__ == "__main__":
    unittest.main()
