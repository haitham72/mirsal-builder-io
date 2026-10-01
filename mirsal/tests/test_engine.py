import hashlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from mirsal.engine.config import EngineConfig
from mirsal.engine.sheet import encode_static, process_sheet
from mirsal.engine.video import close_loop, loop_seam, process_video
from mirsal.engine.grid import detect_grid, scale_rects, split_grid
from mirsal import prompter
from tests import synth

CFG = EngineConfig()


def alpha_bbox(data):
    a = np.array(Image.open(io.BytesIO(data)).convert("RGBA"))[..., 3] > 127
    ys, xs = np.where(a)
    return xs.min(), ys.min(), xs.max(), ys.max()


class SheetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = process_sheet(synth.make_sheet(), CFG)

    def test_statuses(self):
        by = {r.index: r for r in self.res}
        self.assertEqual(by[5].reason, "empty_subject")
        self.assertEqual(by[6].reason, "inside_cell")
        for i in (1, 2, 3, 4, 7, 8, 9):
            self.assertEqual(by[i].status, "READY", (i, by[i].reason, by[i].report.checks))
            self.assertEqual(Image.open(io.BytesIO(by[i].data)).size, (512, 512))

    def test_failed_cells_are_dissected_and_ruled_out(self):
        by = {r.index: r for r in self.res}
        m = by[6].metrics   # subject touches the border: keying can't fix it -> dissect, then ruled out
        self.assertTrue(m["ruled_out"])
        self.assertEqual([a["name"] for a in m["attempts"]], ["default", "dissect"])
        self.assertIn("verdict", m["attempts"][1]["note"])
        m = by[5].metrics   # blank: re-keyed with the sheet-wide background and a lower threshold, then ruled out
        self.assertTrue(m["ruled_out"])
        self.assertEqual(len(m["attempts"]), 4)
        self.assertNotIn("attempts", by[1].metrics)   # healthy cells are not retried

    def test_detached_detail_survives(self):
        # cell 4: circle + sweat drop near the bottom; bbox must reach the drop
        self.assertGreaterEqual(self.res[3].metrics["bbox"][3], 178)

    def test_pack_consistent_scale(self):
        a, b = alpha_bbox(self.res[6].data), alpha_bbox(self.res[7].data)   # tall vs wide, same dimensions
        tall, wide = a[3] - a[1], b[2] - b[0]
        self.assertLess(abs(tall - wide) / tall, 0.02)

    def test_golden_determinism(self):
        h = lambda rs: hashlib.sha256(b"".join(r.data or b"" for r in rs)).hexdigest()
        self.assertEqual(h(self.res), h(process_sheet(synth.make_sheet(), CFG)))

    def test_blue_chroma_keeps_green_subject(self):
        cfg = EngineConfig(chroma="blue")
        r = process_sheet(synth.make_sheet(chroma="blue", subj=(30, 200, 40)), cfg)[0]
        self.assertEqual(r.status, "READY", r.report.checks)
        px = np.array(Image.open(io.BytesIO(r.data)).convert("RGBA"))[256, 256]
        self.assertGreater(px[1], px[0] + 50)   # still green, not keyed away

    def test_webp_fallback(self):
        rng = np.random.default_rng(1)
        img = np.dstack([rng.integers(0, 8, (512, 512, 3)).astype(np.uint8) * 30, np.full((512, 512), 255, np.uint8)])
        png, fmt = encode_static(img, EngineConfig(static_max_bytes=10 ** 9))
        self.assertEqual(fmt, "png")
        data, fmt = encode_static(img, EngineConfig(static_max_bytes=int(len(png) * 0.97)))
        self.assertEqual(fmt, "webp")
        self.assertTrue((np.array(Image.open(io.BytesIO(data)).convert("RGBA")) == img).all())   # lossless
        self.assertLess(len(data), len(png))

    def test_engine_boundary(self):
        code = ("import sys, mirsal.engine.sheet, mirsal.engine.video;"
                "bad=[m for m in ('fastapi','psycopg','langgraph','anthropic','pydantic') if m in sys.modules];"
                "sys.exit(1 if bad else 0)")
        self.assertEqual(subprocess.run([sys.executable, "-c", code]).returncode, 0)


class VideoTests(unittest.TestCase):
    def test_process_video_and_loop_close(self):
        with tempfile.TemporaryDirectory() as td:
            mp4 = Path(td) / "v.mp4"
            synth.make_video(mp4)
            res = process_video(mp4, CFG, cells=[1, 9])
            for r in res:
                self.assertEqual(r.status, "READY", (r.reason, r.report.checks, r.metrics))
                m = r.metrics
                self.assertGreater(m["loop_seam_before"], m["loop_limit"])   # the clip really did not loop
                self.assertLessEqual(m["loop_seam"], m["loop_limit"])        # ...and was closed
                self.assertLess(m["frames_out"], m["frames"])
                self.assertLessEqual(len(r.data), CFG.video_max_bytes)

    def test_presliced_clip_path(self):
        import cv2
        from mirsal.engine import ffmpeg as ff
        from mirsal.engine.video import process_clips
        frames = np.zeros((72, 320, 320, 4), np.uint8)
        for i in range(72):                       # opaque circle drifting right on a transparent background
            cv2.circle(frames[i], (60 + i, 160), 50, (250, 220, 20, 255), -1, cv2.LINE_AA)
            frames[i][..., 3][:40] = np.where(np.random.default_rng(i).random((40, 320)) < 0.3, 2, 0)   # VP9-style alpha haze
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "teddy_01_ (1).webm"
            ff.encode_webm(frames, 24, 30, path)
            (res,) = process_clips({1: {"webm": str(path)}}, CFG)
            self.assertEqual(res.status, "READY", (res.reason, res.report.checks, res.metrics))
            self.assertEqual(res.metrics["source"], "clip:webm")
            self.assertLessEqual(res.metrics["loop_seam"], res.metrics["loop_limit"])

    def test_close_loop_math(self):
        f = np.zeros((40, 8, 8, 4), np.uint8)
        f[..., 3] = 255
        f[..., 0] = np.arange(40)[:, None, None] * 6
        before = loop_seam(f[-1], f[0])
        after = loop_seam(*[close_loop(f, 6)[i] for i in (-1, 0)])
        self.assertLess(after, before / 4)


if __name__ == "__main__":
    unittest.main()


def _grid_sheet(size, centres, r=40, seed=7):
    """Green sheet with one yellow disc per (cx, cy) centre; gutters fall wherever the discs leave room."""
    import cv2
    s = synth.bg(size, seed).copy()
    for cx, cy in centres:
        cv2.circle(s, (cx, cy), r, synth.YELLOW, -1, cv2.LINE_AA)
    return s


class GridTests(unittest.TestCase):
    def test_off_third_gutters_are_cut_in_the_gutter(self):
        # columns centred at 70 / 220 / 470 on a 600 sheet: disc 2 spans 180..260, crossing the thirds line at 200
        cols, rows = (70, 220, 470), (100, 300, 500)
        s = _grid_sheet(600, [(x, y) for y in rows for x in cols])
        self.assertEqual(detect_grid(s), (3, 3))
        rects, info = split_grid(s, 3, 3)
        self.assertEqual(info["method"], "gutter")
        self.assertTrue(110 < info["xs"][1] < 180 and 260 < info["xs"][2] < 430, info["xs"])
        self.assertEqual([r.status for r in process_sheet(s, CFG, rects)], ["READY"] * 9)
        thirds = process_sheet(s, CFG)                      # the old equal split cuts disc 2 / 5 / 8
        self.assertIn("inside_cell", {r.reason for r in thirds})

    def test_two_by_two_and_single(self):
        s = _grid_sheet(400, [(100, 100), (300, 100), (100, 300), (300, 300)], r=50)
        self.assertEqual(detect_grid(s), (2, 2))
        rects, _ = split_grid(s, 2, 2)
        self.assertEqual([r.status for r in process_sheet(s, CFG, rects)], ["READY"] * 4)
        one = _grid_sheet(300, [(150, 150)], r=60)
        self.assertEqual(detect_grid(one), (1, 1))
        rects, info = split_grid(one, 1, 1)
        self.assertEqual((rects, info["method"]), ([(0, 0, 300, 300)], "single"))
        self.assertEqual([r.status for r in process_sheet(one, CFG, rects)], ["READY"])

    def test_video_uses_the_measured_rects(self):
        with tempfile.TemporaryDirectory() as td:
            mp4 = Path(td) / "v.mp4"
            synth.make_video(mp4)                          # 600x600 video made from a 1200x1200 "sheet"
            sheet_rects = [(c * 400, r * 400, 400, 400) for r in range(3) for c in range(3)]
            self.assertEqual(scale_rects(sheet_rects, (1200, 1200), (600, 600))[4], (200, 200, 200, 200))
            res = process_video(mp4, CFG, cells=[5], rects=sheet_rects, sheet_wh=(1200, 1200))
            self.assertEqual(res[0].status, "READY", (res[0].reason, res[0].metrics))


class PrompterGridTests(unittest.TestCase):
    def test_expand_follows_the_grid(self):
        self.assertEqual(len(prompter.expand("teddy bear")["stickers"]), 9)
        p = prompter.expand("teddy bear", (2, 2))
        self.assertEqual((p["grid"], len(p["stickers"])), ([2, 2], 4))
        self.assertIn("2x2", p["sheet_prompt"])

    def test_validate_infers_grid_and_rejects_odd_counts(self):
        st = lambda n: [{"index": i, "prompt": "p", "key": f"k{i}", "emoji": "x"} for i in range(1, n + 1)]
        self.assertEqual(prompter.validate_plan({"stickers": st(4)})["grid"], [2, 2])
        self.assertEqual(prompter.validate_plan({"stickers": st(1)})["grid"], [1, 1])
        with self.assertRaises(ValueError):
            prompter.validate_plan({"stickers": st(5)})


class SpillTests(unittest.TestCase):
    def test_green_inside_the_subject_is_a_warning_not_spill(self):
        import cv2
        s = _grid_sheet(300, [(150, 150)], r=80)
        cv2.circle(s, (150, 150), 35, (120, 170, 110), -1)        # a muted green patch deep inside the subject (stays opaque)
        rects, _ = split_grid(s, 1, 1)
        r = process_sheet(s, CFG, rects)[0]
        self.assertEqual(r.status, "READY", r.report.checks)
        self.assertLessEqual(r.metrics["spill_px"], 20)
        self.assertGreater(r.metrics["chroma_risk"], CFG.chroma_risk_warn)
        self.assertEqual(r.metrics["warnings"], ["chroma_risk"])
