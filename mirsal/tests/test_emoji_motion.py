"""Per-emoji reaction motions (reactions branch): every predefined emoji owns one fixed animation."""
import unittest

import numpy as np

from mirsal.engine import emoji_motion as em
from mirsal.engine import particles as p


class EmojiMotionTests(unittest.TestCase):
    def test_core_36_all_pinned(self):
        self.assertEqual(len(em.CORE_MOTIONS), 36)
        for token, row in em.CORE_MOTIONS.items():
            self.assertIn(row["preset"], ("burst", "fountain", "vortex", "rain", "confetti"), token)
            # every pinned preset must exist in the simulator
            p.preset(row["preset"])

    def test_motion_for_token_is_deterministic(self):
        self.assertEqual(em.motion_for_token("laugh"), em.motion_for_token("laugh"))
        self.assertEqual(em.motion_for_token("laugh")["preset"], "fountain")
        # extended bank: hash fallback, still a known preset and stable
        a = em.motion_for_token("school")
        b = em.motion_for_token("school")
        self.assertEqual(a, b)
        self.assertIn(a["preset"], ("burst", "fountain", "vortex", "rain", "confetti"))

    def test_export_lottie_maps_trajectories_to_keyframes(self):
        params = p.preset("burst", count=6, seed=7)
        doc = p.export_lottie(params, 2)
        self.assertEqual(doc["v"], "5.7.4")
        self.assertEqual(len(doc["layers"]), 6)
        first = doc["layers"][0]
        self.assertEqual(len(first["ks"]["p"]["k"]), doc["op"])
        self.assertEqual(len(first["ks"]["o"]["k"]), doc["op"])
        # placeholder shape per particle
        self.assertEqual(doc["layers"][0]["shapes"][0]["ty"], "gr")

    def test_default_sprite_is_a_tight_rgba_sparkle(self):
        a = p.default_sprite()
        b = p.default_sprite()
        self.assertEqual(a.shape, (128, 128, 4))
        self.assertEqual(a.dtype, np.uint8)
        np.testing.assert_array_equal(a, b)
        self.assertTrue((a[..., 3] > 200).any(), "a solid core")
        self.assertTrue((a[..., 3] == 0).any(), "transparent corners")
        trimmed = p.trim_sprite(a)
        self.assertIsNotNone(trimmed)
        self.assertTrue(max(trimmed.shape[:2]) < 128, "mostly air around the sparkle")


if __name__ == "__main__":
    unittest.main()
