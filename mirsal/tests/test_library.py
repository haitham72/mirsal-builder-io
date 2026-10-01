import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from mirsal.engine.config import EngineConfig
from mirsal.library import Library, LibraryError, cutout, decode_image, png_bytes
from tests import synth


def photo(bgcolor=(120, 90, 60), noise=6):
    """Non-green 'photo': brown noisy background, a yellow disc with a red core."""
    rng = np.random.default_rng(3)
    im = np.clip(np.array(bgcolor) + rng.normal(0, noise, (300, 400, 3)), 0, 255).astype(np.uint8)
    cv2.circle(im, (200, 150), 90, (250, 220, 20), -1, cv2.LINE_AA)
    cv2.circle(im, (200, 150), 30, (200, 30, 30), -1, cv2.LINE_AA)
    return im


def encode(rgb, fmt="png"):
    b = io.BytesIO(); Image.fromarray(rgb).save(b, fmt); return b.getvalue()


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.lib = Library(self.tmp); self.cfg = EngineConfig()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sticker_png(self, seed=0):
        rgba = np.zeros((512, 512, 4), np.uint8)
        cv2.circle(rgba, (256, 256), 150 + seed, (250, 200, 20, 255), -1, cv2.LINE_AA)
        return png_bytes(rgba)

    def test_cutout_methods(self):
        rgba, info = cutout(decode_image(encode(photo())), self.cfg, "grabcut")
        self.assertEqual(info["method"], "grabcut")
        a = rgba[..., 3]
        self.assertGreater((a > 127).mean(), 0.3)
        self.assertEqual(a[0, 0], 0)                      # background removed at the corner
        green = synth.make_sheet(seed=1)[:200, :200]
        rgba, info = cutout(decode_image(encode(green)), self.cfg)
        self.assertTrue(info["method"].startswith("chroma"))
        cut = np.zeros((100, 100, 4), np.uint8); cut[30:70, 30:70] = (255, 0, 0, 255)
        self.assertEqual(cutout(decode_image(png_bytes(cut)), self.cfg)[1]["method"], "existing_alpha")
        with self.assertRaises(LibraryError):
            cutout(decode_image(encode(np.full((200, 200, 3), 128, np.uint8))), self.cfg)

    def test_cutout_matte_and_forced_methods(self):
        from mirsal import matte
        img = np.dstack([photo(), np.full(photo().shape[:2], 255, np.uint8)])
        with self.assertRaises(LibraryError):
            cutout(img, self.cfg, "bogus")
        _, info = cutout(img, self.cfg, "grabcut"); self.assertEqual(info["method"], "grabcut")
        if matte.status()["ok"]:
            out, info = cutout(img, self.cfg, "matte")
            self.assertTrue(info["method"].startswith("matte_")); self.assertTrue(0.03 < info["foreground"] < 0.9)
            self.assertLess(float((out[..., 3] > 127).mean()), 0.95)      # not a rectangle: background pixels are transparent
        else:
            with self.assertRaises(LibraryError):
                cutout(img, self.cfg, "matte")

    def test_packs_stickers_and_export(self):
        p = self.lib.create_pack("UAE Moments")
        for i in range(4):
            s = self.lib.add_render(p["id"], self.sticker_png(i), f"Sticker {i}", "🇦🇪", self.cfg)
        self.assertTrue(s["file"].startswith("img-004-uae_moments-sticker_3"))
        snap = self.lib.snapshot()
        self.assertEqual(len(snap["packs"][0]["stickers"]), 4); self.assertEqual(snap["packs"][0]["cover"], snap["packs"][0]["stickers"][0]["id"])
        ids = [x["id"] for x in snap["packs"][0]["stickers"]]
        self.lib.update_pack(p["id"], name="Renamed", order=ids[::-1], cover=ids[2])
        pk = self.lib.snapshot()["packs"][0]
        self.assertEqual([x["id"] for x in pk["stickers"]], ids[::-1]); self.assertEqual(pk["cover"], ids[2]); self.assertEqual(pk["name"], "Renamed")
        with self.assertRaises(LibraryError):
            self.lib.update_pack(p["id"], order=ids[:2])
        data, rep = self.lib.export_wastickers(p["id"])
        z = zipfile.ZipFile(io.BytesIO(data)); names = z.namelist()
        self.assertIn("tray.png", names); self.assertEqual(sum(n.endswith(".webp") for n in names), 4)
        self.assertEqual(Image.open(io.BytesIO(z.read("tray.png"))).size, (96, 96))
        self.assertTrue(all(f["kb"] <= 100 for f in rep["files"]))
        self.lib.delete_sticker(p["id"], ids[2])                       # deleting the cover promotes another sticker
        self.assertNotEqual(self.lib.snapshot()["packs"][0]["cover"], ids[2])
        self.lib.delete_sticker(p["id"], ids[0])
        with self.assertRaises(LibraryError):                          # 2 stickers left: below the pack minimum
            self.lib.export_wastickers(p["id"])
        self.lib.delete_pack(p["id"]); self.assertEqual(self.lib.snapshot()["packs"], []); self.assertEqual(list(self.lib.files.iterdir()), [])

    def test_move_sticker_between_packs(self):
        a = self.lib.create_pack("Old Pack")["id"]; b = self.lib.create_pack("New Pack")["id"]
        s1 = self.lib.add_render(a, self.sticker_png(0), "One", "🙂", self.cfg)
        s2 = self.lib.add_render(a, self.sticker_png(1), "Two", "🙂", self.cfg)
        m = self.lib.move_sticker(a, s1["id"], b)
        self.assertEqual(m["file"], "img-001-new_pack-one.webp".replace("webp", m["file"].rsplit(".", 1)[-1]))
        pk = {p["id"]: p for p in self.lib.snapshot()["packs"]}
        self.assertEqual([x["id"] for x in pk[a]["stickers"]], [s2["id"]]); self.assertEqual(pk[a]["cover"], s2["id"])
        self.assertEqual([x["id"] for x in pk[b]["stickers"]], [s1["id"]]); self.assertEqual(pk[b]["cover"], s1["id"])
        self.assertTrue((self.lib.files / m["file"]).is_file()); self.assertEqual(len(list(self.lib.files.iterdir())), 2)
        with self.assertRaises(LibraryError):
            self.lib.move_sticker(a, s1["id"], b)                     # no longer in pack a
        with self.assertRaises(LibraryError):
            self.lib.move_sticker(b, s1["id"], b)                     # same pack

    def test_bad_render(self):
        p = self.lib.create_pack("x")
        with self.assertRaises(LibraryError):
            self.lib.add_render(p["id"], png_bytes(np.zeros((256, 256, 4), np.uint8)), "a", "🙂", self.cfg)
        with self.assertRaises(LibraryError):
            self.lib.add_render(p["id"], png_bytes(np.zeros((512, 512, 4), np.uint8)), "a", "🙂", self.cfg)


class AnimateTests(unittest.TestCase):
    def setUp(self):
        from mirsal.engine import ffmpeg as ff
        self.tmp = Path(tempfile.mkdtemp()); self.lib = Library(self.tmp); self.cfg = EngineConfig()
        frs = np.zeros((30, 512, 512, 4), np.uint8)
        for i in range(30):
            cv2.circle(frs[i], (100 + i * 8, 256), 60, (250, 120, 20, 255), -1, cv2.LINE_AA)
        p = self.tmp / "a.webm"; ff.encode_webm(frs, 30, 38, p)
        self.pack = self.lib.create_pack("Anim")["id"]
        self.sid = self.lib.add_bytes(self.pack, p.read_bytes(), "webm", "Bounce", "animated")["id"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_formats_trim_and_save(self):
        data, mime, ext, info = self.lib.animate(self.pack, self.sid, 0.0, 0.5, 15, "webp", True, self.cfg)
        self.assertEqual((data[:4], data[8:12], mime), (b"RIFF", b"WEBP", "image/webp")); self.assertEqual(info["frames"], 8)   # 0.5 s at 15 fps
        self.assertLessEqual(len(data), 500 * 1024)
        self.assertEqual(self.lib.animate(self.pack, self.sid, 0.2, 0.8, 10, "gif", True, self.cfg)[0][:6], b"GIF89a")
        new = self.lib.animate(self.pack, self.sid, 0.0, 0.6, 12, "webm", True, self.cfg, save=True, name="Short")
        self.assertEqual((new["type"], new["name"]), ("animated", "Short")); self.assertEqual(new["info"]["frames"], 7)
        self.assertEqual(len(self.lib.snapshot()["packs"][0]["stickers"]), 2)
        with self.assertRaises(LibraryError):
            self.lib.animate(self.pack, self.sid, 0.5, 0.52, 12, "webm", True, self.cfg)          # too short
        with self.assertRaises(LibraryError):
            self.lib.animate(self.pack, self.sid, 0, 1, 12, "webp", True, self.cfg, save=True)    # only webm can be saved

    def test_wastickers_includes_animated(self):
        for i in range(2):
            self.lib.add_bytes(self.pack, png_bytes(np.dstack([np.full((512, 512, 3), 200, np.uint8), np.full((512, 512), 255, np.uint8)])), "png", f"s{i}")
        data, rep = self.lib.export_wastickers(self.pack, cfg=self.cfg)
        z = zipfile.ZipFile(io.BytesIO(data))
        self.assertEqual(sum(n.endswith(".webp") for n in z.namelist()), 3); self.assertTrue(any(f.get("animated") for f in rep["files"]))
