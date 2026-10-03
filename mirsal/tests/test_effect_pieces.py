"""The AI-drawn pieces sheet of a particle effect (docs/effects.md): the template-locked prompt, the base plan the normal sheet path accepts, the price first (409 without go), the sheet job
made through the fake CLI (outline 0, the effect and group on the job), the link made by `Console.start_from_job` (thread mode and queue mode both run it), and the simulated burst made of
the cut cells (a cell with only warnings is still used). Nothing here reaches a provider."""
import http.client
import json
import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image

from mirsal.console.server import serve
from mirsal.engine.config import EngineConfig
from mirsal.flow import effects as fx
from mirsal.generation import effect_prompts as ep, jobs, tasks
from tests.test_effects_flow import sticker_png
from tests.test_golden import shape_sheet
from tests.test_live import Base, png_bytes

GOLD = {"subject": "jewelry", "elements": ["gold bar", "diamond", "ring", "coin"]}


class PiecesPromptTests(unittest.TestCase):
    def test_the_prompt_is_a_sheet_of_different_isolated_pieces_on_the_key_colour_without_an_outline(self):
        t = ep.pieces_prompt(GOLD, 2, 2)
        for must in ("4 separate small objects", "2 rows of 2", "Outline: none", "#00FF00 green", "isolated and centred", "nothing touches the edge of its cell",
                     "Piece 1 (top row, left): gold bar", "Piece 2 (top row, right): diamond", "Piece 4 (bottom row, right): coin", "never a character, a person"):
            self.assertIn(must, t)
        self.assertNotIn("sticker", t.lower(), "the word sticker makes image models draw a die-cut border")
        self.assertEqual((ep.PIECES_TEMPLATE_ID, ep.PIECES_VERSION), ("effect_pieces", 1))

    def test_fewer_pieces_than_cells_are_cycled_in_other_sizes_so_no_two_cells_match(self):
        cells = ep.pieces_cells({"subject": "jewelry", "elements": ["gold bar", "diamond"]}, 3, 3)
        labels = [c["label"] for c in cells]
        self.assertEqual(len(labels), 9)
        self.assertEqual(len(set(labels)), 9)
        self.assertEqual(labels[0], "gold bar")
        self.assertEqual(labels[1], "diamond")
        self.assertTrue(labels[2].startswith("gold bar, "), labels[2])
        one = ep.pieces_cells({"subject": "heart", "elements": ["red heart"]}, 2, 2)
        self.assertEqual(len({c["label"] for c in one}), 4)
        self.assertEqual([c["pos"] for c in one], [1, 2, 3, 4])

    def test_more_pieces_than_cells_use_the_first_ones(self):
        cells = ep.pieces_cells({"subject": "x", "elements": [f"piece{i}" for i in range(6)]}, 2, 2)
        self.assertEqual([c["label"] for c in cells], ["piece0", "piece1", "piece2", "piece3"])

    def test_three_by_three_and_the_screen_colour(self):
        t = ep.pieces_prompt({"subject": "strawberry", "elements": ["red strawberry", "green leaf"]}, 3, 3)
        self.assertIn("9 separate small objects", t)
        self.assertIn("#0000FF blue", t, "a green piece makes the screen blue")
        self.assertEqual(sum(f"Piece {i} (" in t for i in range(1, 10)), 9)
        self.assertEqual(ep.describe_pieces({"subject": "strawberry", "elements": ["green leaf"]}, 2, 2)["key"], "blue")

    def test_the_plan_is_linted_and_the_subject_never_says_sticker(self):
        with self.assertRaises(ValueError):
            ep.pieces_prompt({"subject": "cat", "elements": ["a sticker of a cat"]}, 2, 2)
        with self.assertRaises(ValueError):
            ep.pieces_prompt({"subject": "cat", "elements": ["a logo"]}, 2, 2)
        with self.assertRaises(ValueError):
            ep.pieces_prompt(GOLD, 4, 4)
        t = ep.pieces_prompt({"subject": "Batman sticker", "elements": ["bat signal"]}, 2, 2)
        self.assertNotIn("sticker", t.lower())
        self.assertIn("Batman", t)


class PiecesFlowTests(Base):
    """One effect on a real console with the fake CLI."""

    def setUp(self):
        super().setUp()
        self.srv, self.c = serve(self.out, self.tmp / "in", 0, cfg=EngineConfig(), block=False)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.sheet = shape_sheet(1200, [(x, y) for y in (300, 900) for x in (300, 900)], r=110)
        self.files["png"] = png_bytes(self.sheet)
        self.pack = self.c.lib.create_pack("Jewelry")
        self.sid = self.c.lib.add_bytes(self.pack["id"], sticker_png(), "png", "Gold ring", "static", "💍")["id"]
        s, j = self.req("POST", "/api/effects", {"pack_id": self.pack["id"], "sticker_ids": [self.sid], "mode": "sim"})
        self.eid = j["id"]
        self.until(lambda: self.req("GET", f"/api/effects/{self.eid}")[1].get("status") == "READY", "the analysis")
        self.gid = self.req("GET", f"/api/effects/{self.eid}")[1]["groups"][0]["id"]
        self.req("POST", f"/api/effects/{self.eid}/plan", {"group": self.gid, "subject": "jewelry", "elements": GOLD["elements"]})

    def tearDown(self):
        self.c.wait_jobs(90)
        self.srv.shutdown()
        super().tearDown()

    def req(self, method, path, body=None):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        h.request(method, path, json.dumps(body) if body is not None else None, {"Content-Type": "application/json"})
        r = h.getresponse(); data = r.read(); h.close()
        try:
            return r.status, json.loads(data)
        except ValueError:
            return r.status, data

    def until(self, fn, what, timeout=180):
        end = time.time() + timeout
        while time.time() < end:
            v = fn()
            if v:
                return v
            time.sleep(0.3)
        self.fail("timeout: " + what)

    def group(self):
        return next(g for g in self.req("GET", f"/api/effects/{self.eid}")[1]["groups"] if g["id"] == self.gid)

    def creates(self):
        return [c for c in self.cli.calls if c[:2] == ["generate", "create"]]

    # ---------- the plan

    def test_the_base_plan_is_what_the_normal_reserve_path_accepts_and_keeps_the_pieces_prompt(self):
        base = fx.pieces_base_plan(self.out, self.eid, self.gid, "2x2")
        self.assertEqual((base["template_id"], base["template_version"], base["grid"]), ("sheet_2x2", 3, [2, 2]))
        self.assertEqual([s["key"] for s in base["stickers"]], ["gold_bar", "diamond", "ring", "coin"])
        self.assertEqual({s["emoji"] for s in base["stickers"]}, {"💍"}, "the emoji of the source sticker")
        self.assertEqual(base["slots"]["key_colour"], "green")
        self.assertEqual(base["custom"]["sheet_prompt"], ep.pieces_prompt(GOLD, 2, 2))
        t = tasks.reserve(self.out, self.tmp / "in", base["task"], "2x2", "flat_vector", base_plan=base)
        self.assertEqual(t["plan"]["sheet_prompt"], ep.pieces_prompt(GOLD, 2, 2), "the pieces prompt is what is sent, not the template's character text")
        self.assertEqual(t["plan"]["slots"]["cells"][0]["label"], "gold bar")

    def test_pieces_plan_is_what_the_screen_shows_before_spending(self):
        p = fx.pieces_plan(self.out, self.eid, self.gid, "2x2")
        self.assertEqual((p["grid"], p["key"], p["template"], p["outline"]), ([2, 2], "green", "effect_pieces", 0))
        self.assertEqual([c["label"] for c in p["cells"]], ["gold bar", "diamond", "ring", "coin"])
        self.assertEqual(len(fx.pieces_plan(self.out, self.eid, self.gid, "3x3")["cells"]), 9)
        with self.assertRaises(fx.EffectError):
            fx.pieces_plan(self.out, self.eid, self.gid, "4x4")
        with self.assertRaises(fx.EffectError):
            fx.pieces_plan(self.out, self.eid, "G99")

    # ---------- the price first

    def test_the_price_is_shown_and_nothing_is_spent_without_go(self):
        before = len(self.creates())
        s, est = self.req("POST", f"/api/effects/{self.eid}/pieces_estimate", {"group": self.gid})
        self.assertEqual((s, est["credits"], est["grid"], len(est["cells"])), (200, 2.0, [2, 2], 4), est)
        self.assertIn("Piece 1", est["prompt"])
        s, est2 = self.req("POST", f"/api/effects/{self.eid}/pieces", {"group": self.gid, "estimate": True, "grid": "3x3"})
        self.assertEqual((s, len(est2["cells"])), (200, 9))
        s, no = self.req("POST", f"/api/effects/{self.eid}/pieces", {"group": self.gid})
        self.assertEqual(s, 409)
        self.assertEqual(no["estimate"]["credits"], 2.0)
        self.assertEqual(len(self.creates()), before, "no go-ahead, no spending")
        self.assertNotIn("pieces", self.group())
        self.assertEqual(self.req("POST", f"/api/effects/{self.eid}/pieces", {"group": self.gid, "grid": "4x4", "go": True})[0], 400)
        self.assertEqual(self.req("POST", f"/api/effects/{self.eid}/pieces", {"group": "G99", "go": True})[0], 404)

    # ---------- the job, the link, the burst

    def _draw(self, grid="2x2"):
        s, j = self.req("POST", f"/api/effects/{self.eid}/pieces", {"group": self.gid, "grid": grid, "go": True})
        self.assertEqual(s, 202, j)
        return j

    def test_the_job_is_a_normal_sheet_job_and_its_cut_cells_become_the_sprites(self):
        j = self._draw()
        self.assertEqual((j["estimate"], j["grid"], j["id"], j["group"]), (2.0, [2, 2], self.eid, self.gid))
        job = jobs.read(self.out, j["job"])
        self.assertEqual((job["kind"], job["request"]["outline"], job["request"]["pieces"]), ("sheet", 0, {"effect": self.eid, "group": self.gid}))
        self.assertIn("Piece 1 (top row, left): gold bar", job["request"]["prompt"])
        self.assertEqual(jobs.read(self.out, j["job"])["task"], j["task"])
        done = self.until(lambda: (lambda x: x if x.get("generation") and x["status"] == "DONE" else None)(self.req("GET", "/api/jobs/" + j["job"])[1]), "the sheet job")
        gn = int(done["generation"][1:])
        pc = self.group()["pieces"]
        self.assertEqual((pc["status"], pc["generation"], pc["job"], pc["grid"]), ("DRAWN", gn, j["job"], [2, 2]))
        self.assertEqual(self.group()["sprites"], {"generation": gn})
        self.assertTrue(any(h["decision"] == "LINK" for h in self.req("GET", f"/api/effects/{self.eid}")[1]["history"]))
        self.until(lambda: (lambda x: x if x["stage"] == "sliced" and not x["busy"] else None)(self.req("GET", f"/api/generations/{gn}")[1]), "the cells")
        res = self.req("GET", f"/api/generations/{gn}")[1]
        self.assertEqual(res["outline_px"], 0, "the cut pieces carry no baked outline")
        self.assertEqual([s["key"] for s in res["stickers"]], ["gold_bar", "diamond", "ring", "coin"])
        pcs = fx.sprites_of(self.out, self.c.lib, self.eid, self.gid)
        self.assertEqual(len(pcs), sum(1 for s in res["stickers"] if s["status"] == "READY"))
        self.assertGreaterEqual(len(pcs), 1)
        s, pv = self.req("POST", f"/api/effects/{self.eid}/preview", {"sticker_id": self.sid, "params": {}})
        self.assertEqual((s, pv["sprites"]), (200, len(pcs)), pv)

    def test_queue_mode_links_too_because_the_link_lives_in_start_from_job(self):
        with mock.patch.object(type(self.c), "fulfil_async", lambda self_, jid, after=None: None):      # a queue worker fulfils the job elsewhere and calls start_from_job
            j = self._draw()
        self.assertEqual(self.group()["pieces"], {"job": j["job"], "grid": [2, 2], "status": "REQUESTED"})
        self.assertEqual(self.group()["sprites"], "own", "nothing is linked before the sheet exists")
        f = self.tmp / "sheet.png"
        f.write_bytes(png_bytes(self.sheet))
        jobs.claim(self.out, j["job"], "ticket-1")
        jobs.done(self.out, j["job"], str(f), "nano_banana_flash")
        self.c.start_from_job(jobs.read(self.out, j["job"]))
        gn = int(jobs.read(self.out, j["job"])["generation"][1:])
        self.assertEqual((self.group()["pieces"]["status"], self.group()["sprites"]), ("DRAWN", {"generation": gn}))
        self.until(lambda: (lambda x: x if x["stage"] == "sliced" and not x["busy"] else None)(self.req("GET", f"/api/generations/{gn}")[1]), "the cells")
        self.assertGreaterEqual(len(fx.sprites_of(self.out, self.c.lib, self.eid, self.gid)), 1)

    def test_before_the_cells_exist_the_burst_answers_a_clear_409(self):
        with mock.patch.object(type(self.c), "fulfil_async", lambda self_, jid, after=None: None):
            self._draw()
        fx.link_pieces(self.out, self.eid, self.gid, 77)          # a batch that does not exist (yet)
        s, r = self.req("POST", f"/api/effects/{self.eid}/preview", {"sticker_id": self.sid, "params": {}})
        self.assertEqual(s, 409)
        self.assertIn("G077", r["error"])

    def test_a_request_without_a_link_target_is_just_a_batch(self):
        """A job whose effect was removed meanwhile still makes its batch (the link is best effort)."""
        j = self._draw()
        shutil.rmtree(self.out / "effects" / self.eid)
        done = self.until(lambda: (lambda x: x if x.get("generation") and x["status"] == "DONE" else None)(self.req("GET", "/api/jobs/" + j["job"])[1]), "the sheet job")
        self.assertTrue(done["generation"].startswith("G"))

    # ---------- warnings never block; blocks and rejections are not sprites

    def _batch(self, gn, cells):
        d = self.out / f"G{gn:03d}"
        (d / "slices").mkdir(parents=True)
        (d / "prompts.json").write_text("{}", encoding="utf-8")
        sts = []
        for i, (status, review, checks) in enumerate(cells, 1):
            a = np.zeros((64, 64, 4), np.uint8)
            a[16:48, 16:48] = (200, 160, 30, 255)
            Image.fromarray(a, "RGBA").save(d / "slices" / f"S{i}.png")
            sts.append({"index": i, "key": f"k{i}", "status": status, "png": f"slices/S{i}.png", "review": review, "checks": checks, "anim_status": "NOT_REQUESTED"})
        res = {"generation_id": f"G{gn:03d}", "number": gn, "prompt": "pieces", "stage": "sliced", "error": None, "grid": [2, 2], "source": {"subject": "pieces"}, "stickers": sts}
        (d / "result.json").write_text(json.dumps(res), encoding="utf-8")

    def test_a_cell_with_only_warnings_is_used_and_a_blocked_or_rejected_one_is_not(self):
        warn = [{"id": "sharpness", "verdict": "WARN"}]
        self._batch(5, [("READY", {}, warn), ("READY", {"still": "REJECTED"}, []), ("BLOCKED", {}, [{"id": "alpha", "verdict": "BLOCK"}]), ("READY", {}, [])])
        fx.set_sprites(self.out, self.eid, self.gid, {"generation": 5})
        pcs = fx.sprites_of(self.out, self.c.lib, self.eid, self.gid)
        self.assertEqual(len(pcs), 2, "the warned cell and the clean one")
        pv = fx.sim_preview(self.out, self.c.lib, self.eid, self.sid, {})
        self.assertEqual(pv["sprites"], 2)
        self.assertTrue((self.out / "effects" / self.eid / pv["file"]).is_file())

    def test_a_batch_with_no_ready_cell_is_a_409_with_the_reason(self):
        self._batch(6, [("PENDING", {}, []), ("PENDING", {}, [])])
        fx.set_sprites(self.out, self.eid, self.gid, {"generation": 6})
        with self.assertRaises(fx.EffectError) as cm:
            fx.sprites_of(self.out, self.c.lib, self.eid, self.gid)
        self.assertEqual(cm.exception.code, 409)
        self.assertIn("still being cut", str(cm.exception))
        self._batch(7, [("BLOCKED", {}, []), ("READY", {"still": "REJECTED"}, [])])
        fx.set_sprites(self.out, self.eid, self.gid, {"generation": 7})
        with self.assertRaises(fx.EffectError) as cm:
            fx.sprites_of(self.out, self.c.lib, self.eid, self.gid)
        self.assertEqual(cm.exception.code, 409)
        self.assertIn("no ready cell", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
