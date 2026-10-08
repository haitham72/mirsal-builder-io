"""Export-as-ZIP names (`docs/export to team/mirsal-export-architecture.md`): `{emoji}-{pack_slug}-{multi_action_tag}-{sNN}-{G###}-{date}`,
e.g. `🤣-falcon-laugh_rofl_lmao-s08-G112-20261008.webm`. Pure functions only: no provider, no Postgres, no files."""
import unittest

from mirsal.generation import actions
from mirsal.media import export_names as xn


class BankTests(unittest.TestCase):
    def test_the_bank_has_36_tokens(self):
        self.assertEqual(len(actions.ACTION_BANK), 36)

    def test_alias_lookup_finds_the_canonical_token(self):
        token, aliases = actions.canonical_for("laughing out loud", ["lmao", "rofl"])
        self.assertEqual(token, "laugh")
        self.assertIn("lmao", aliases)
        self.assertEqual(actions.canonical_for("x", ["lmfao"])[0], "laugh")

    def test_underscored_aliases_normalize_to_the_same_token(self):
        self.assertEqual(actions.canonical_for("x", ["thank_you"])[0], "thanks")
        self.assertEqual(actions.canonical_for("x", ["eye_roll"])[0], "eye-roll")
        self.assertEqual(actions.canonical_for("x", ["thumbs_up"])[0], "approve")

    def test_unknown_words_are_unresolved_not_guessed(self):
        self.assertIsNone(actions.canonical_for("batman_lego_gliding", ["gotham"]))
        self.assertEqual(actions.fallback_tag("Laughing Falcon"), "laughing_falcon")
        self.assertEqual(actions.fallback_tag("cat_1", ["cat"]), "cat")
        self.assertEqual(actions.fallback_tag("generic_emojis_grumpy", ["generic_emojis_grumpy", "grumpy", "arms", "crossed"],
                                              exclude=["generic", "emojis"]),
                         "grumpy_arms_crossed")


class NameTests(unittest.TestCase):
    def test_build_matches_the_decided_format(self):
        stem = xn.build(emoji="🤣", slug="falcon", tag="laugh_rofl_lmao", index=8, gid=112, date="20261008")
        self.assertEqual(stem, "🤣-falcon-laugh_rofl_lmao-s08-G112-20261008")

    def test_parse_round_trips_including_hyphenated_slugs(self):
        stem = "👌-royal_falcon-approve_okay_yes_thumbsup-s06-G113-20261009"
        p = xn.parse(stem + ".webm")
        self.assertEqual((p["emoji"], p["slug"], p["tag"], p["index"], p["gid"], p["date"]),
                         ("👌", "royal_falcon", "approve_okay_yes_thumbsup", 6, 113, "20261009"))

    def test_parse_reads_older_hyphenated_slugs_best_effort(self):
        p = xn.parse("👌-royal-falcon-approve_okay-s06-G113-20261009.webm")
        self.assertEqual((p["slug"], p["tag"]), ("royal-falcon", "approve_okay"))

    def test_parse_rejects_garbage(self):
        self.assertIsNone(xn.parse("img-001-cat.png"))
        self.assertIsNone(xn.parse("not-a-name.webm"))

    def test_first_emoji_keeps_modifiers_and_zwj_together(self):
        self.assertEqual(xn.first_emoji("😂🤣"), "😂")
        self.assertEqual(xn.first_emoji("👍🏽ok"), "👍🏽")
        self.assertEqual(xn.first_emoji("❤️‍🔥x"), "❤️‍🔥")
        self.assertEqual(xn.first_emoji(""), "")

    def test_describe_resolves_a_bank_hit_and_flags_a_fallback(self):
        hit = xn.describe(emoji="🤣😂", key="laughing_hard", tags=["lmao"], slug="falcon", index=8, gid=112, date="20261008")
        self.assertEqual((hit["stem"], hit["action"], hit["unresolved"], hit["emojis"]),
                         ("🤣-falcon-laugh_laughing_lol_rofl_lmao_lmfao-s08-G112-20261008", "laugh", False, ["🤣", "😂"]))
        miss = xn.describe(emoji="", key="cat_1", tags=["cat"], slug="cat", index=2, gid=1, date="20261008")
        self.assertEqual((miss["stem"], miss["action"], miss["unresolved"]), ("🙂-cat-cat-s02-G001-20261008", "cat", True))
        hyph = xn.describe(emoji="🙄", key="eye_roll", tags=["eyeroll"], slug="falcon", index=3, gid=112, date="20261008")
        self.assertEqual((hyph["tag"], hyph["action"]), ("eyeroll", "eye-roll"))


if __name__ == "__main__":
    unittest.main()
