"""The video side of the particle effects on a SYNTHETIC clip (a 2x2 grid of bursts on a green screen made here), never a real video."""
import shutil
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from mirsal.engine import effect_checks, effect_video as ev, ffmpeg as ff
from mirsal.engine.config import EngineConfig

CFG = EngineConfig()
SIDE, FPS, N = 480, 24, 73


def make_clip(path, key=(0, 255, 0), empty_tail=(True, True, True, True)):
    """2x2 cells, a small burst of coloured discs per cell: empty at the start, bursts at 0.4 s, falls, empty again at the end unless `empty_tail[i]` is False."""
    w = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (SIDE, SIDE))
    rng = np.random.default_rng(3)
    ang = rng.uniform(0, 6.28, (4, 7)); spd = rng.uniform(40, 90, (4, 7))
    for f in range(N):
        t = f / FPS
        img = np.zeros((SIDE, SIDE, 3), np.uint8); img[:] = key[::-1]           # BGR
        for ci in range(4):
            cx0, cy0 = (ci % 2) * 240 + 120, (ci // 2) * 240 + 120
            live = 0.4 <= t <= (2.6 if empty_tail[ci] else 3.1)
            if not live:
                continue
            for k in range(7):
                tt = t - 0.4
                x = cx0 + np.cos(ang[ci, k]) * spd[ci, k] * tt * 0.5
                y = cy0 + np.sin(ang[ci, k]) * spd[ci, k] * tt * 0.5 + 25 * tt * tt
                cv2.circle(img, (int(x), int(y)), 14, (60 + 25 * k, 90, 220 - 20 * k), -1)
        w.write(img)
    w.release()


@unittest.skipUnless(shutil.which("ffmpeg") or ff.ffmpeg_exe(), "ffmpeg is needed")
class EffectVideoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.mp4 = cls.tmp / "fx.mp4"
        make_clip(cls.mp4, empty_tail=(True, False, True, True))
        cls.cells = ev.cut_cells(cls.mp4, 2, 2, CFG, "green")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_cell_rects_and_resample_and_square(self):
        self.assertEqual(ev.cell_rects(480, 480, 2, 2), [(0, 0, 240, 240), (240, 0, 240, 240), (0, 240, 240, 240), (240, 240, 240, 240)])
        fr = np.zeros((73, 8, 8, 4), np.uint8)
        self.assertEqual(ev.resample(fr, 24.0).shape[0], 90, "Telegram's clock: 3 s at 30 fps")
        self.assertEqual(ev.square(np.zeros((2, 20, 20, 4), np.uint8), 512).shape, (2, 512, 512, 4))

    def test_every_cell_is_cut_and_keyed(self):
        self.assertEqual([c["index"] for c in self.cells], [1, 2, 3, 4])
        for c in self.cells:
            self.assertEqual(c["key"], "green")
            self.assertIsNone(c.get("error"))
            cov = effect_checks.coverage_curve(c["frames"])
            self.assertLess(max(cov[:3]), 0.003, "the clip starts on an empty screen")
            self.assertGreater(max(cov), 0.01, "something bursts")

    def test_the_screen_that_is_there_wins_over_the_one_asked_for(self):
        blue = self.tmp / "blue.mp4"
        make_clip(blue, key=(0, 0, 255))
        cells = ev.cut_cells(blue, 2, 2, CFG, "green")
        self.assertEqual({c["key"] for c in cells}, {"blue"})

    def test_a_good_cell_becomes_a_sticker_a_late_one_is_faded_and_says_so(self):
        good, late = ev.finish_cell(self.cells[0], CFG), ev.finish_cell(self.cells[1], CFG)
        for r in (good, late):
            self.assertEqual(r["status"], "READY", r["checks"])
            self.assertEqual(r["blocks"], [])
            self.assertLessEqual(len(r["data"]), CFG.video_max_bytes)
            self.assertEqual(r["metrics"]["frames"], 90)
        self.assertNotIn("effect_tail_faded", good["warnings"])
        self.assertIn("effect_tail_faded", late["warnings"], "it still had pieces on screen at the end: faded, and said")
        self.assertTrue(late["metrics"]["tail_faded"])
        self.assertGreater(late["metrics"]["raw_end_coverage"], 0.003)

    def test_settle_makes_both_ends_empty_by_construction(self):
        fr = np.zeros((90, 64, 64, 4), np.uint8)
        fr[:, 20:40, 20:40] = (255, 0, 0, 255)                       # on screen all the time: no empty start, no empty end
        out, info = ev.settle(fr)
        self.assertEqual(info, {"tail_faded": True, "head_faded": True})
        cov = effect_checks.coverage_curve(out)
        self.assertEqual((max(cov[:3]), max(cov[-3:])), (0.0, 0.0))
        self.assertGreater(max(cov), 0.05, "the middle is untouched")

    def test_an_effect_check_never_blocks_only_a_telegram_limit_does(self):
        r = ev.encode_and_check(np.zeros((90, 512, 512, 4), np.uint8), CFG)           # nothing on screen at all
        self.assertTrue(set(r["blocks"]) <= ev.TECHNICAL, "only Telegram's own limits may be a block")
        self.assertIn("effect_has_burst", r["warnings"], "an empty clip is a warning a person can read")

    def test_an_unreadable_cell_is_reported_not_raised(self):
        r = ev.finish_cell({"index": 7, "frames": None, "src_fps": 24.0, "error": "no key"}, CFG)
        self.assertEqual((r["status"], r["blocks"]), ("FAILED", ["cell_unreadable"]))


if __name__ == "__main__":
    unittest.main()
