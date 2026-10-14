"""Reaction effects (Create > New): one bank emoji -> its fixed motion flying as the literal glyph -> a playable Lottie file.
Over the real HTTP server, a temporary out/, no provider. Numbers and JSON only: no media file is judged by eye (rule 9)."""
import http.client
import json
import threading
import unittest
from unittest import mock

import numpy as np

from mirsal.console.server import serve
from mirsal.engine import emoji_glyph, lottie, particles
from mirsal.engine.config import EngineConfig
from mirsal.flow import emoji_reactions as er, particle_sets as ps
from tests.test_live import Base


class EmojiLottieTests(Base):
    def setUp(self):
        super().setUp()
        if not emoji_glyph.emoji_font():                          # no colour emoji font here: the contract is still tested, with a stand-in glyph
            patch = mock.patch.object(emoji_glyph, "render_emoji", lambda glyph, px=160, font_path=None: particles.default_sprite(px))
            patch.start()
            self.addCleanup(patch.stop)
        self.srv, self.c = serve(self.out, self.tmp / "in", 0, cfg=EngineConfig(), block=False)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        super().tearDown()

    def req(self, method, path, body=None):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        h.request(method, path, json.dumps(body) if body is not None else None, {"Content-Type": "application/json"})
        r = h.getresponse()
        data = r.read()
        h.close()
        try:
            return r.status, json.loads(data)
        except ValueError:
            return r.status, data

    def test_kiss_exports_a_playable_lottie_of_its_own_glyph_and_stores_it(self):
        code, j = self.req("POST", "/api/particles/emoji-lottie", {"token": "kiss"})
        self.assertEqual(code, 200, j)
        self.assertEqual((j["id"], j["token"], j["emoji"], j["preset"]), ("L001", "kiss", "\U0001F618", "burst"))
        self.assertEqual((j["params"]["size_in_dur"], j["params"]["size_out_dur"], j["params"]["hue_var"]), (0.4, 0.4, 25.0), "the screen's defaults")
        d = er.emoji_dir(self.out, "kiss")
        doc = json.loads((d / "renders" / "L001.lottie.json").read_text(encoding="utf-8"))
        self.assertTrue((d / "renders" / "L001.png").is_file(), "the glyph asset is kept for inspection")
        self.assertEqual(j["url"], "/out/particles/emoji/kiss/renders/L001.lottie.json")
        self.assertEqual(j["layers"], len(doc["layers"]))
        self.assertTrue(doc["layers"] and all(x["ty"] == 2 for x in doc["layers"]), "image layers of the glyph, no placeholder")
        self.assertTrue(all(a["p"].startswith("data:image/png;base64,") for a in doc["assets"]))
        rec = json.loads((d / "emoji.json").read_text(encoding="utf-8"))
        self.assertEqual([h["decision"] for h in rec["history"]], ["LOTTIE"])
        self.assertEqual([x["id"] for x in rec["lottie"]], ["L001"])
        self.assertEqual(self.req("GET", j["url"])[0], 200, "the browser downloads the stored file")
        self.assertEqual((d / "renders" / "L001.webp").read_bytes()[8:12], b"WEBP", "its card's loop is kept beside it")
        code, made = self.req("GET", "/api/particles/emoji-lottie")
        self.assertEqual(code, 200, made)
        self.assertEqual([(r["id"], r["token"], r["url"], r["preview"]) for r in made["reactions"]],
                         [("L001", "kiss", j["url"], "/out/particles/emoji/kiss/renders/L001.webp")])
        self.req("POST", "/api/particles/emoji-lottie", {"token": "cry"})
        self.assertEqual([r["token"] for r in self.req("GET", "/api/particles/emoji-lottie")[1]["reactions"]], ["cry", "kiss"], "newest first")
        self.assertEqual(self.req("GET", "/api/particles")[1]["sets"], [], "no set is made: this flow has no pack, no sticker, no set")

    def test_same_emoji_options_and_seed_are_the_same_bytes_and_each_export_is_numbered(self):
        body = {"token": "\U0001F618", "preset": "vortex", "size_in_dur": 0.2, "size_out_dur": 0.6, "hue_var": 50, "seed": 4}
        a = self.req("POST", "/api/particles/emoji-lottie", body)[1]
        b = self.req("POST", "/api/particles/emoji-lottie", body)[1]
        self.assertEqual((a["id"], b["id"], a["token"], a["preset"]), ("L001", "L002", "kiss", "vortex"), "a glyph resolves to its token")
        d = er.emoji_dir(self.out, "kiss") / "renders"
        self.assertEqual((d / "L001.lottie.json").read_bytes(), (d / "L002.lottie.json").read_bytes())
        self.assertEqual(a["params"]["vortex"], particles.PRESETS["vortex"]["vortex"], "an override takes the preset's own look")
        other = self.req("POST", "/api/particles/emoji-lottie", {**body, "seed": 5})[1]
        self.assertNotEqual((d / "L001.lottie.json").read_bytes(), (d / f"{other['id']}.lottie.json").read_bytes())

    def test_zero_options_are_the_plain_motion(self):
        code, j = self.req("POST", "/api/particles/emoji-lottie", {"token": "laugh", "size_in_dur": 0, "size_out_dur": 0, "hue_var": 0})
        self.assertEqual(code, 200, j)
        plain = particles.preset("fountain", magnitude=1.9, gravity=1.3, spin=1.5).to_dict()
        self.assertEqual(j["params"], plain, "laugh's pinned fountain, nothing else")
        self.assertEqual(j["assets"], 1, "no hue variation: the glyph is embedded once")

    def test_size_and_size_variation(self):
        own = self.req("POST", "/api/particles/emoji-lottie", {"token": "kiss"})[1]["params"]
        self.assertEqual((own["size_min"], own["size_max"], own["particle_size"]), (0.1, 0.22, 1.0), "untouched: the motion's own sizes")
        same = self.req("POST", "/api/particles/emoji-lottie", {"token": "kiss", "size_var": 0, "particle_size": 2})[1]["params"]
        self.assertAlmostEqual(same["size_min"], 0.16)
        self.assertAlmostEqual(same["size_max"], 0.16, msg="variation 0: every emoji the same size, the motion's average")
        self.assertEqual(same["particle_size"], 2.0, "Size scales them all")
        wide = self.req("POST", "/api/particles/emoji-lottie", {"token": "kiss", "size_var": 1})[1]["params"]
        self.assertEqual((round(wide["size_min"], 3), round(wide["size_max"], 3)), (0.02, 0.32), "variation 1: from (almost) nothing to twice the average")
        mid = self.req("POST", "/api/particles/emoji-lottie", {"token": "kiss", "size_var": 0.375})[1]["params"]
        self.assertEqual((round(mid["size_min"], 6), round(mid["size_max"], 6)), (0.1, 0.22), "its own variation reproduces its own range")
        tr = particles.trajectories(particles.ParticleParams.from_dict({**same, "origin": tuple(same["origin"])}))
        self.assertAlmostEqual(float(tr.size_frac.min()), float(tr.size_frac.max()), msg="the simulator draws them all one size")
        for bad in ({"size_var": "big"}, {"particle_size": True}):
            self.assertEqual(self.req("POST", "/api/particles/emoji-preview", {"token": "kiss", **bad})[0], 400, bad)

    def test_simulation_overrides_only_what_is_sent(self):
        own = self.req("POST", "/api/particles/emoji-lottie", {"token": "kiss"})[1]["params"]
        j = self.req("POST", "/api/particles/emoji-lottie", {"token": "kiss", "magnitude": 2, "spin": 0, "count": 12, "spread": 90, "gravity": -0.5, "vortex": 1})[1]["params"]
        self.assertEqual((j["magnitude"], j["spin"], j["count"], j["spread"], j["gravity"], j["vortex"]), (2.0, 0.0, 12, 90.0, -0.5, 1.0))
        part = self.req("POST", "/api/particles/emoji-lottie", {"token": "kiss", "count": 12})[1]["params"]
        self.assertEqual({k: part[k] for k in ("magnitude", "gravity", "spin")}, {k: own[k] for k in ("magnitude", "gravity", "spin")}, "a setting left out keeps the motion's value")
        self.assertEqual(self.req("POST", "/api/particles/emoji-lottie", {"token": "kiss", "count": 999})[1]["params"]["count"], 80, "the engine clamps")
        self.assertEqual(self.req("POST", "/api/particles/emoji-preview", {"token": "kiss", "spin": "fast"})[0], 400)

    def test_save_preset_then_apply_it_to_many_emojis(self):
        code, p1 = self.req("POST", "/api/particles/emoji-presets", {"settings": {"preset": "vortex", "magnitude": 0.4, "particle_size": 1.5, "hue_var": 0}})
        self.assertEqual(code, 201, p1)
        self.assertEqual((p1["id"], p1["name"]), ("preset01", "Preset 01"))
        p2 = self.req("POST", "/api/particles/emoji-presets", {"settings": {"count": 12}})[1]
        self.assertEqual((p2["id"], p2["name"]), ("preset02", "Preset 02"))
        self.assertEqual([p["id"] for p in self.req("GET", "/api/particles/emoji-presets")[1]["presets"]], ["preset01", "preset02"])
        code, j = self.req("POST", "/api/particles/emoji-lottie/batch", {"tokens": ["kiss", "cry", "kiss", "nope"], "preset_id": "preset01"})
        self.assertEqual(code, 200, j)
        self.assertEqual([r["token"] for r in j["reactions"]], ["kiss", "cry"], "repeats dropped, order kept")
        self.assertEqual([e["token"] for e in j["errors"]], ["nope"], "one bad emoji does not stop the others")
        for r in j["reactions"]:
            self.assertEqual((r["preset"], r["params"]["magnitude"], r["params"]["particle_size"], r["params"]["hue_var"]), ("vortex", 0.4, 1.5, 0.0))
        own = self.req("POST", "/api/particles/emoji-lottie/batch", {"tokens": ["cry"]})[1]["reactions"][0]
        self.assertEqual((own["preset"], own["params"]["hue_var"]), ("rain", 25.0), "no preset: each emoji's own motion with the screen's defaults")
        counted = self.req("POST", "/api/particles/emoji-lottie/batch", {"tokens": ["cry"], "preset_id": "preset02"})[1]["reactions"][0]
        self.assertEqual((counted["preset"], counted["params"]["count"]), ("rain", 12), "a preset without a motion keeps each emoji's own motion")
        self.assertEqual(self.req("POST", "/api/particles/emoji-presets/preset01/delete", {})[1]["deleted"], "preset01")
        self.assertEqual(self.req("POST", "/api/particles/emoji-lottie/batch", {"tokens": ["cry"], "preset_id": "preset01"})[0], 404)
        p3 = self.req("POST", "/api/particles/emoji-presets", {"settings": {}})[1]
        self.assertEqual(p3["id"], "preset03", "ids are never reused")
        for bad in ({"settings": {"wind": 1}}, {"settings": {"preset": "spiral"}}, {"settings": {"spin": "fast"}}, {"settings": "x"}):
            self.assertEqual(self.req("POST", "/api/particles/emoji-presets", bad)[0], 400, bad)
        self.assertEqual(self.req("POST", "/api/particles/emoji-lottie/batch", {"tokens": []})[0], 400)
        self.assertEqual(self.req("POST", "/api/particles/emoji-lottie/batch", {"tokens": ["cry"] * 25})[0], 400)
        self.assertEqual(self.req("POST", "/api/particles/emoji-presets/preset99/delete", {})[0], 404)

    def test_unknown_emoji_is_409_and_bad_options_are_400(self):
        for token in ("not-a-token", "", None, "abc"):
            code, j = self.req("POST", "/api/particles/emoji-lottie", {"token": token})
            self.assertEqual(code, 409, (token, j))
        self.assertEqual(self.req("POST", "/api/particles/emoji-preview", {"token": "nope"})[0], 409)
        for bad in ({"preset": "spiral"}, {"hue_var": "lots"}, {"size_in_dur": True}, {"size": 20}):
            code, j = self.req("POST", "/api/particles/emoji-lottie", {"token": "kiss", **bad})
            self.assertEqual(code, 400, (bad, j))
        self.assertFalse(er.emoji_dir(self.out, "kiss").exists(), "a refused export writes nothing")

    def test_the_preview_is_a_cached_webp_of_the_same_burst(self):
        code, j = self.req("POST", "/api/particles/emoji-preview", {"token": "cry", "size": 128})
        self.assertEqual(code, 200, j)
        self.assertEqual((j["token"], j["preset"]), ("cry", "rain"))
        f = er.emoji_dir(self.out, "cry") / "previews" / j["url"].rsplit("/", 1)[1]
        self.assertTrue(f.is_file())
        self.assertEqual(f.read_bytes()[8:12], b"WEBP")
        again = self.req("POST", "/api/particles/emoji-preview", {"token": "cry", "size": 128})[1]
        self.assertEqual(again["url"], j["url"], "same options, same file")
        lottie = self.req("POST", "/api/particles/emoji-lottie", {"token": "cry"})[1]
        self.assertEqual({**lottie["params"], "size": 128}, j["params"], "the preview and the Lottie are the same burst")

    def test_the_hover_preview_is_the_whole_burst_scaled_never_cut(self):
        code, j = self.req("POST", "/api/particles/emoji-preview", {"token": "laugh", "size": 128, "fit": True})
        self.assertEqual(code, 200, j)
        self.assertTrue(j["url"].endswith("-fit.webp"), j["url"])
        t, g, name, p = er.emoji_burst("laugh", size=128)
        img = er._glyph(g)
        cut = lambda a: sum(1 for f in a if f[0].max() > 127 or f[-1].max() > 127 or f[:, 0].max() > 127 or f[:, -1].max() > 127)
        self.assertGreater(cut(particles.simulate([img], p)[..., 3]), 0, "the plain burst runs past its square")
        self.assertEqual(cut(particles.simulate([img], p, fit=True)[..., 3]), 0, "fit: nothing reaches the edge")


class SetLottieTests(unittest.TestCase):
    def test_sprite_pngs_embed_a_still_and_an_animated_sprites_fullest_frame(self):
        still = particles.default_sprite(32)
        frames = np.zeros((3, 10, 10, 4), np.uint8)
        frames[1, 2:8, 2:8] = 255
        pngs = ps._sprite_pngs([still, particles.AnimatedSprite(frames, 30.0)])
        self.assertEqual(len(pngs), 2)
        doc = lottie.export_lottie(particles.preset("burst", count=6), pngs)
        self.assertEqual(len(doc["assets"]), 2)


if __name__ == "__main__":
    unittest.main()
