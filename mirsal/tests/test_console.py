import http.client
import json
import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path

import cv2

from mirsal import pipeline as pl
from mirsal.engine.config import EngineConfig
from mirsal.console.server import serve
from tests import synth


def build_inputs(root: Path):
    """blob: variant 1 has a video, variant 2 has none (like a missing video take)."""
    d = root / "Images_gen" / "img-001-blob"; d.mkdir(parents=True)
    v = root / "videos_gen" / "vid-001-blob"; v.mkdir(parents=True)
    for k, seed in ((1, 0), (2, 7)):
        cv2.imwrite(str(d / f"img-001-blob ({k}).png"), cv2.cvtColor(synth.make_sheet(seed=seed), cv2.COLOR_RGB2BGR))
    synth.make_video(v / "vid-001-blob (1).mp4")


class ConsoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        build_inputs(cls.tmp / "in")
        cls.srv, cls.c = serve(cls.tmp / "out", cls.tmp / "in", 0, cfg=EngineConfig(min_sheet_px=256), block=False)   # the synthetic sheets are small
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def req(self, method, path, body=None):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h.request(method, path, json.dumps(body) if body is not None else None, {"Content-Type": "application/json"})
        r = h.getresponse(); raw = r.read(); h.close()
        try:
            return r.status, json.loads(raw)
        except ValueError:
            return r.status, raw

    def wait(self, gid, pred, timeout=90):
        end = time.time() + timeout
        while time.time() < end:
            s, j = self.req("GET", f"/api/generations/{gid}")
            if pred(j) and not j["busy"]:
                return j
            time.sleep(0.2)
        self.fail("timeout")

    def test_live_preview_source_and_ui_names(self):
        s, j = self.req("POST", "/api/generations", {"prompt": "create a blob for school", "variant": 1})
        gid = j["id"]; self.wait(gid, lambda x: x["stage"] == "video_sliced" or x["stickers"])
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h.request("GET", f"/src/{gid}/video", headers={"Range": "bytes=0-99"})
        r = h.getresponse(); body = r.read(); h.close()
        self.assertEqual(r.status, 206); self.assertEqual(len(body), 100)
        self.assertEqual(self.req("GET", f"/src/{gid}/clip/1")[0], 404)
        self.assertIn("health", self.req("GET", "/api/generations")[1])
        # inline onclick handlers resolve names on the element first: `animate` is Element.animate and silently broke the button once
        html = (Path(__file__).parents[1] / "mirsal" / "console" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("onclick=\"animate(", html)

    def test_library_api_and_ui_files(self):
        import io as _io
        from PIL import Image
        for f in ("studio.css", "app.js", "packs.js", "editor.js", "animate.js", "chat.js", "prepare.js"):
            self.assertEqual(self.req("GET", f"/ui/{f}")[0], 200)
        self.assertEqual(self.req("GET", "/ui/server.py")[0], 404)
        s, pk = self.req("POST", "/api/packs", {"name": "API Pack"}); self.assertEqual(s, 200)
        png = _io.BytesIO(); Image.new("RGBA", (512, 512), (0, 0, 0, 0)).save(png, "PNG")
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h.request("POST", f"/api/packs/{pk['id']}/render?name=x&emoji=%F0%9F%99%82", png.getvalue()); r = h.getresponse(); r.read(); h.close()
        self.assertEqual(r.status, 400)                                   # empty sticker refused
        self.assertEqual(self.req("POST", "/api/packs/nope", {"name": "z"})[0], 404)
        s, lib = self.req("GET", "/api/library"); self.assertTrue(any(p["id"] == pk["id"] for p in lib["packs"]))
        self.assertEqual(self.req("GET", f"/api/packs/{pk['id']}/export")[0], 409)   # < 3 stickers
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h.request("GET", "/lib/..%2F..%2Fpipeline.py"); r = h.getresponse(); r.read(); h.close()
        self.assertIn(r.status, (400, 404))

    def test_lifecycle(self):
        s, j = self.req("POST", "/api/generations", {"prompt": "create a blob for school"})
        self.assertEqual(s, 202); gid = j["id"]
        g = self.wait(gid, lambda j: j["stage"] == "sliced")
        self.assertEqual(g["task_slug"], "blob_school")
        ready = [t for t in g["stickers"] if t["status"] == "READY"]
        # cell 5 blank. Cell 6 touches the equal-thirds line but has a background gutter beside it, so the measured
        # gutter cut keeps it whole (inside_cell on a really crossing subject is covered in test_engine).
        self.assertEqual(len(ready), 8)
        self.assertEqual(g["grid"], [3, 3]); self.assertEqual(g["source"]["grid"]["method"], "gutter")
        for t in ready:
            self.assertTrue(t["png"].startswith(f"slices/img-{gid:03d}-blob_school-blob_"), t["png"])
            self.assertTrue((self.c.out / g["generation_id"] / t["png"]).exists())
        stages = [(e["stage"], e["status"]) for e in g["events"]]
        self.assertEqual(stages, [("requested", "done")] + [(x, y) for x in ("sheet_picked", "keyed", "sliced") for y in ("start", "done")])

        # animate one slice -> exactly one webm; repeat is a no-op
        s, j = self.req("POST", f"/api/generations/{gid}/animate", {"scope": "slice", "index": 1})
        self.assertEqual(s, 202)
        g = self.wait(gid, lambda j: j["stickers"][0]["anim_status"] in ("READY", "FAILED"))
        self.assertEqual(g["stickers"][0]["anim_status"], "READY", g["stickers"][0]["anim_metrics"])
        self.assertEqual(g["stickers"][0]["webm"], f"slices/vid-{gid:03d}-blob_school-blob_with_a_book.webm")
        self.assertEqual(len(list((self.c.out / g["generation_id"] / "slices").glob("*.webm"))), 1)
        s, j = self.req("POST", f"/api/generations/{gid}/animate", {"scope": "slice", "index": 1})
        self.assertEqual((s, j["noop"]), (200, True))
        s, j = self.req("POST", f"/api/generations/{gid}/animate", {"scope": "slice", "index": 5})
        self.assertEqual(s, 409)   # blank cell has no READY still

        # more -> variant 2 has no video; a third more says "that's all"
        s, j = self.req("POST", f"/api/generations/{gid}/more"); self.assertEqual(s, 202)
        g2 = self.wait(j["id"], lambda j: j["stage"] == "sliced")
        self.assertEqual(g2["source"]["variant"], 2)
        s, j2 = self.req("POST", f"/api/generations/{g2['number']}/animate", {"scope": "pack"})
        self.assertEqual((s, j2["error"]), (409, "No animation prepared for this variation."))
        s, j2 = self.req("POST", f"/api/generations/{g2['number']}/more")
        self.assertEqual(s, 409); self.assertIn("That's all 2 prepared variations of blob", j2["error"])
        # same input -> same event order (timestamps aside)
        seq = lambda g: [(e["stage"], e["status"]) for e in g["events"]]
        s, j = self.req("POST", "/api/generations", {"prompt": "create a blob for school"})
        g3 = self.wait(j["id"], lambda j: j["stage"] == "sliced")
        self.assertEqual(seq(g3), seq(g2))

    def test_video_project_api(self):
        import base64
        from tests.test_video_project import make_clip, overlay_png
        clip = self.tmp / "clip.mp4"; make_clip(clip)
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        h.request("POST", "/api/projects?name=clip.mp4", clip.read_bytes(), {"Content-Type": "application/octet-stream"})
        r = h.getresponse(); pj = json.loads(r.read()); h.close()
        self.assertEqual(r.status, 200); pid = pj["id"]
        s, fr = self.req("GET", f"/proj/{pid}/f/0"); self.assertEqual((s, fr[:2]), (200, b"\xff\xd8"))   # a JPEG preview frame
        self.assertEqual(self.req("GET", f"/proj/{pid}/f/99999")[0], 404)
        self.assertEqual(self.req("GET", "/proj/../f/0")[0], 404)
        s, j = self.req("POST", f"/api/projects/{pid}", {"layers": [{"id": "t1", "type": "text", "timing": {"startMs": 0, "endMs": 500}, "payload": {"text": "hi"}}],
                                                        "video": {"trimStartMs": 0, "trimEndMs": 800, "fps": 10}})
        self.assertEqual((s, j["layers"][0]["timing"]["endMs"]), (200, 500))
        self.assertEqual(self.req("GET", f"/api/projects/{pid}")[1]["video"]["fps"], 10)
        self.assertEqual([x["id"] for x in self.req("GET", "/api/projects")[1]["projects"]], [pid])
        body = {"format": "gif", "overlays": {"t1": "data:image/png;base64," + base64.b64encode(overlay_png()).decode()}}
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        h.request("POST", f"/api/projects/{pid}/render", json.dumps(body), {"Content-Type": "application/json"})
        r = h.getresponse(); data = r.read(); h.close()
        self.assertEqual((r.status, data[:6]), (200, b"GIF89a")); self.assertEqual(json.loads(r.getheader("X-Render"))["frames"], 8)
        self.assertEqual(self.req("POST", f"/api/projects/{pid}/render", {"format": "webp", "overlays": {}, "save": {"pack_id": "x"}})[0], 400)   # only WebM goes into packs
        self.assertEqual(self.req("POST", "/api/projects?name=x.txt")[0], 400)
        self.assertEqual(self.req("POST", f"/api/projects/{pid}/delete")[0], 200); self.assertEqual(self.req("GET", f"/api/projects/{pid}")[0], 404)

    def test_the_simple_flow_animate_then_add(self):
        """type -> stickers -> drop one -> Animate -> Add: the gates are decided behind those clicks and each decision is on record."""
        s, j = self.req("POST", "/api/generations", {"prompt": "create a blob for school", "variant": 1, "outline": 0})
        gid = j["id"]
        g = self.wait(gid, lambda x: x["stage"] == "sliced")
        self.assertEqual((g["outline_px"], g["reviews"]["plan"]["note"]), (0, "approved by pressing Generate"))
        self.assertEqual(self.req("POST", f"/api/generations/{gid}/drop", {"index": 5})[0], 409)       # a blocked sticker cannot be dropped
        s, j = self.req("POST", f"/api/generations/{gid}/drop", {"index": 3})
        self.assertEqual((s, j.get("gate"), j.get("error")), (200, "still", None))
        s, j = self.req("POST", f"/api/generations/{gid}/animate", {"scope": "slice", "index": 1})
        self.assertEqual(s, 202)
        g = self.wait(gid, lambda x: x["stickers"][0]["anim_status"] == "READY")
        pk = self.req("POST", "/api/packs", {"name": "Flow"})[1]
        s, r = self.req("POST", f"/api/generations/{gid}/add", {"pack_id": pk["id"]})
        self.assertEqual((s, r["kind"], r["added"], r["indices"]), (200, "animated", 1, [1]))          # only what was animated and kept
        s, r = self.req("POST", f"/api/generations/{gid}/add", {"pack_id": pk["id"]})
        self.assertEqual((s, r["added"], r["already"]), (200, 0, 1))                                   # pressing Add twice adds nothing twice
        g = self.req("GET", f"/api/generations/{gid}")[1]
        self.assertEqual(g["final"], [1])
        self.assertEqual([(h["actor"], h["decision"]) for h in g["stickers"][2]["history"] if h["stage"] == "still"], [("human", "REJECT")])   # S3: dropped, on record
        lib = self.req("GET", "/api/library")[1]
        pack = next(x for x in lib["packs"] if x["id"] == pk["id"])
        self.assertEqual([x["type"] for x in pack["stickers"]], ["animated"])
        # a drop after the pack was approved reopens it instead of failing
        self.assertEqual(self.req("POST", f"/api/generations/{gid}/drop", {"index": 1, "dropped": True})[1]["gate"], "anim")
        self.assertEqual(self.req("POST", f"/api/generations/{gid}/add", {"pack_id": pk["id"]})[0], 409)   # nothing left to add

    def test_add_without_a_video_adds_the_stills(self):
        s, j = self.req("POST", "/api/generations", {"prompt": "blob", "variant": 2})
        gid = j["id"]
        self.wait(gid, lambda x: x["stage"] == "sliced")
        s, r = self.req("POST", f"/api/generations/{gid}/add", {"pack_name": "Stills"})
        self.assertEqual((s, r["kind"], r["added"]), (200, "static", 8))
        self.assertEqual(len(next(x for x in self.req("GET", "/api/library")[1]["packs"] if x["id"] == r["pack_id"])["stickers"]), 8)

    def test_errors_and_traversal(self):
        self.assertEqual(self.req("POST", "/api/generations", {"prompt": "spaceship"})[0], 404)
        self.assertEqual(self.req("POST", "/api/generations", {"prompt": ""})[0], 400)
        self.assertEqual(self.req("GET", "/out/%2e%2e/%2e%2e/in/Images_gen")[0], 400)
        self.assertEqual(self.req("GET", "/")[0], 200)


if __name__ == "__main__":
    unittest.main()
