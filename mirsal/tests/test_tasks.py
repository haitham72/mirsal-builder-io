"""1G backend: the Inbox. Reserve a task, watch its folder flip state, flag a misnamed folder, run a generation linked to its task."""
import shutil
import tempfile
import unittest
from pathlib import Path

import cv2

from tests.test_golden import Api, shape_sheet


def tree(root: Path):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")) if root.exists() else []


class InboxTests(Api):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.tmp / "in2").mkdir()

    def test_reserve_watch_run(self):
        watch = self.tmp / "in"
        before = tree(watch)
        s, plan = self.req("POST", "/api/plan", {"prompt": "teddy bear for school", "grid": "2x2"})
        self.assertEqual((s, plan["template_id"], len(plan["stickers"])), (200, "sheet_2x2", 4))
        self.assertIn("2x2 sticker sheet", plan["sheet_prompt"])
        self.assertEqual(self.req("POST", "/api/plan", {"prompt": "x", "grid": "5x5"})[0], 400)
        self.assertEqual(self.req("POST", "/api/plan", {"prompt": "  "})[0], 400)
        s, t = self.req("POST", "/api/tasks", {"prompt": "teddy bear for school", "grid": "3x3"})
        self.assertEqual(s, 200)
        n = t["number"]
        self.assertEqual((t["folders"]["img"], t["folders"]["vid"]), (f"img-{n:03d}-teddy_bear", f"vid-{n:03d}-teddy_bear"))
        self.assertEqual((t["provider"], t["external_task_id"], t["name_key"], t["plan_review"]["decision"]), ("higgsfield-manual", t["folders"]["img"], "teddy_bear_school", "APPROVE"))
        self.assertEqual(t["request"]["template_id"], "sheet_3x3")
        self.assertTrue((self.tmp / "out" / "tasks" / f"{n:03d}.json").is_file())
        self.assertEqual(tree(watch), before)                                    # the app never writes inside the watch folders
        n2 = self.req("POST", "/api/tasks", {"prompt": "puppy"})[1]["number"]
        self.assertEqual(n2, n + 1)                                              # next number, never reused

        row = lambda: next(r for r in self.req("GET", "/api/inbox")[1]["rows"] if r["task"] == f"{n:03d}")
        self.assertEqual((row()["state"], row()["can_run"]), ("reserved, waiting for file", False))
        s, j = self.req("POST", "/api/generations", {"task": f"{n:03d}"})
        self.assertEqual(s, 409, j)                                              # the sheet has not arrived
        d = watch / "Images_gen" / t["folders"]["img"]
        d.mkdir(parents=True)
        self.assertEqual(row()["state"], "reserved, waiting for file")
        cv2.imwrite(str(d / "sheet.png"), cv2.cvtColor(shape_sheet(1200, [(x, y) for y in (200, 600, 1000) for x in (200, 600, 1000)]), cv2.COLOR_RGB2BGR))
        self.assertEqual((row()["state"], row()["can_run"]), ("sheet arrived", True))   # flips within one poll
        (watch / "videos_gen" / t["folders"]["vid"]).mkdir(parents=True)
        (watch / "videos_gen" / t["folders"]["vid"] / "x.mp4").write_bytes(b"0")
        self.assertIn("video arrived", row()["states"])

        s, j = self.req("POST", "/api/generations", {"task": f"{n:03d}"})
        self.assertEqual(s, 202, j)
        g = self.wait(j["id"], lambda x: x["stage"] == "sliced")
        self.assertEqual((g["task_id"], g["name_key"], g["plan_source"], g["reviews"]["plan"]["decision"]), (f"{n:03d}", "teddy_bear_school", f"task {n:03d}", "APPROVE"))
        self.assertEqual(g["sheet_prompt"], t["plan"]["sheet_prompt"])           # the prompt used is stored with the result
        self.assertEqual(self.req("GET", f"/api/tasks/{n:03d}")[1]["generations"], [g["generation_id"]])

    def test_misnamed_and_orphan_folders(self):
        watch = self.tmp / "in"
        (watch / "Images_gen" / "Teddy Bear").mkdir(parents=True, exist_ok=True)
        (watch / "Images_gen" / "img-7-puppy dog").mkdir(exist_ok=True)
        (watch / "Images_gen" / "vid-009-wrongplace").mkdir(exist_ok=True)
        rows = {r["name"]: r for r in self.req("GET", "/api/inbox")[1]["rows"]}
        nxt = self.req("GET", "/api/inbox")[1]["next_number"]
        self.assertEqual(rows["Teddy Bear"]["state"], "name invalid")
        self.assertEqual(rows["Teddy Bear"]["problems"][0]["nearest"], f"img-{nxt:03d}-teddy_bear")
        self.assertEqual(rows["img-7-puppy dog"]["problems"][0]["nearest"], "img-007-puppy_dog")
        self.assertIn("vid- folder", rows["vid-009-wrongplace"]["problems"][0]["what"])
        self.assertIn("img-NNN-<subject>", rows["Teddy Bear"]["problems"][0]["expected"])
        cv2.imwrite(str(watch / "Images_gen" / "img-001-blob" / "extra.png"), cv2.cvtColor(shape_sheet(300, [(150, 150)]), cv2.COLOR_RGB2BGR))
        rows = {r["name"]: r for r in self.req("GET", "/api/inbox")[1]["rows"]}
        self.assertTrue(any("no matching task" in x for x in rows["img-001-blob"]["states"]))   # a sheet made outside the app is flagged

    def test_legacy_console_and_missing_dist(self):
        s, body = self.req("GET", "/legacy")
        self.assertEqual(s, 200)
        self.assertIn(b"Mirsal", body)
        self.assertEqual(self.req("GET", "/")[0], 200)
        self.assertEqual(self.req("GET", "/assets/..%2F..%2Fserver.py")[0], 404)   # an escape from dist/ is refused


if __name__ == "__main__":
    unittest.main()
