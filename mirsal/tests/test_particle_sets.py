"""Particle sets `P###` over the real HTTP server (docs/particles_plan.md sections 3, 4 and 6): a set belongs to pack(s) or stands alone,
*Use as particle set* saves what a run drew, unpicking never deletes a file, assign/unassign/duplicate are list edits, and a delete moves the
folder to the trash with Restore (nothing is destroyed on a click). The engine half is `tests/test_particle_set.py`; nothing here reaches a provider."""
import threading
import unittest

from mirsal.engine.config import EngineConfig
from mirsal.flow import particle_sets as ps
from mirsal.generation import tasks
from mirsal.flow import sources
from tests.test_effects_flow import sticker_png
from tests.test_golden import shape_sheet
from tests.test_live import Base, png_bytes
from tests.test_particle_set import SetBase, new_batch, blobs


class SetRoutesTests(SetBase):
    """A real console, a real pack, a real drawn 2x2 sheet linked to an effect (exactly what the wizard does)."""

    def setUp(self):
        super().setUp()
        self.base = self.req("POST", f"/api/effects/{self.eid}/particles", {"grid": "2x2", "elements": ["pink heart", "rose flower"], "go": True})
        self.assertEqual(self.base[0], 202, self.base[1])
        self.job = self.base[1]["job"]
        self.until(lambda: self.req("GET", f"/api/jobs/{self.job}")[1].get("status") in ("DONE", "FAILED"), "the sheet job")
        self.gen = self.req("GET", f"/api/jobs/{self.job}")[1].get("generation")
        self.until(lambda: self.effect().get("set", {}).get("status") == "DRAWN", "the sheet to be cut")

    def effect(self):
        return self.req("GET", f"/api/effects/{self.eid}")[1]

    def set_from_effect(self, **body):
        code, j = self.req("POST", "/api/particles", {"from_effect": self.eid, **body})
        return code, j

    # ---------- Use as particle set ----------
    def test_the_drawn_sheet_becomes_a_durable_set_kept_under_out_particles(self):
        code, j = self.set_from_effect(name="Barbie hearts")
        self.assertEqual(code, 201)
        self.assertEqual(j["name"], "Barbie hearts")
        self.assertEqual(j["packs"], [self.pack["id"]], "it defaults to the effect's own pack")
        self.assertEqual((j["n_cells"], j["n_picked"]), (4, 4))
        self.assertEqual(j["source"]["effect"], self.eid)
        self.assertTrue(all(c["url"] and not c["missing"] for c in j["cells"]))
        f = self.out / "particles" / j["id"] / "cells" / "c01.png"
        self.assertTrue(f.is_file(), "the cells are copied in, so the set outlives the batch")
        self.assertEqual(j["used_in"], [{"id": self.pack["id"], "name": "Fruits"}])
        self.assertFalse(j["trashed"])

    def test_only_the_picked_cells_are_saved(self):
        _, j = self.set_from_effect(picked=[1, 3])
        self.assertEqual([c["cell"] for c in j["cells"]], [1, 3])
        self.assertEqual(j["n_cells"], 2)

    def test_a_set_can_be_made_for_several_packs_or_none(self):
        other = self.c.lib.create_pack("Princess")
        _, one = self.set_from_effect(packs=[self.pack["id"], other["id"]])
        self.assertEqual(one["packs"], [self.pack["id"], other["id"]])
        self.assertEqual([u["name"] for u in one["used_in"]], ["Fruits", "Princess"])
        _, none = self.set_from_effect(packs=[])
        self.assertEqual(none["packs"], [], "stand-alone is allowed")
        self.assertEqual(none["used_in"], [])

    def test_a_pack_that_does_not_exist_is_refused_not_silently_stored(self):
        code, j = self.set_from_effect(packs=["nope"])
        self.assertEqual(code, 404)
        self.assertEqual(self.req("GET", "/api/particles")[1]["sets"], [], "nothing was created")

    # ---------- the library's list and one set ----------
    def test_the_list_is_the_library_cards(self):
        _, a = self.set_from_effect(name="Barbie hearts")
        _, b = self.set_from_effect(name="Bat signals")
        rows = {r["id"]: r for r in self.req("GET", "/api/particles")[1]["sets"]}
        self.assertEqual(set(rows), {a["id"], b["id"]})
        self.assertEqual(rows[a["id"]]["name"], "Barbie hearts")
        self.assertEqual((rows[a["id"]]["n_cells"], rows[a["id"]]["n_picked"]), (4, 4))
        self.assertEqual(rows[a["id"]]["used_in"][0]["name"], "Fruits")
        self.assertEqual(rows[a["id"]]["picked"], [1, 2, 3, 4])

    def test_rename_and_motion_are_stored_and_linted(self):
        _, a = self.set_from_effect()
        code, j = self.req("POST", f"/api/particles/{a['id']}", {"name": "  Hearts  and  flowers ", "motion": {"preset": "confetti", "params": {"count": 40}}})
        self.assertEqual((code, j["name"]), (200, "Hearts and flowers"))
        self.assertEqual(j["motion"], {"preset": "confetti", "params": {"count": 40}})
        code, j = self.req("POST", f"/api/particles/{a['id']}", {"motion": {"preset": "explode"}})
        self.assertEqual(code, 400, "a preset the engine does not have is refused")
        code, j = self.req("POST", f"/api/particles/{a['id']}", {"motion": {"params": {"warp": 1}}})
        self.assertEqual(code, 400, "a parameter the engine does not read is refused")

    # ---------- unpicking never deletes a file (generate more appends) ----------
    def test_unpicking_a_cell_keeps_its_file(self):
        _, a = self.set_from_effect()
        _, j = self.req("POST", f"/api/particles/{a['id']}", {"picked": [1, 2]})
        self.assertEqual(j["n_picked"], 2)
        self.assertEqual(len(j["cells"]), 4, "the cells stay listed")
        self.assertEqual([c["picked"] for c in j["cells"]], [True, True, False, False])
        self.assertTrue((self.out / "particles" / a["id"] / "cells" / "c04.png").is_file(), "the unpicked cell's file is kept")
        for c in j["cells"]:
            self.assertFalse(c["missing"])
        code, _ = self.req("POST", f"/api/particles/{a['id']}", {"picked": []})
        self.assertEqual(code, 400, "a set with nothing picked cannot be saved")
        code, _ = self.req("POST", f"/api/particles/{a['id']}", {"picked": [9]})
        self.assertEqual(code, 400)

    # ---------- assign / unassign / duplicate ----------
    def test_assigning_is_a_list_edit_and_unassigning_keeps_the_set(self):
        other = self.c.lib.create_pack("Princess")
        _, a = self.set_from_effect(packs=[])
        _, j = self.req("POST", f"/api/particles/{a['id']}/assign", {"packs": [self.pack["id"], other["id"]]})
        self.assertEqual(j["packs"], [self.pack["id"], other["id"]])
        self.assertEqual(j["id"], a["id"], "assigning never copies the set")
        _, j = self.req("POST", f"/api/particles/{a['id']}/unassign", {"packs": [other["id"]]})
        self.assertEqual(j["packs"], [self.pack["id"]])
        self.assertEqual(j["n_cells"], 4, "the cells are still there")

    def test_duplicate_makes_an_independent_copy(self):
        _, a = self.set_from_effect(name="Hearts")
        code, b = self.req("POST", f"/api/particles/{a['id']}/duplicate")
        self.assertEqual(code, 201)
        self.assertNotEqual(b["id"], a["id"])
        self.assertEqual(b["packs"], a["packs"])
        self.assertEqual(b["n_cells"], a["n_cells"])
        self.assertEqual(b["source"]["duplicated_from"], a["id"])
        self.assertTrue((self.out / "particles" / b["id"] / "cells" / "c01.png").is_file())
        self.req("POST", f"/api/particles/{b['id']}", {"picked": [1]})
        self.assertEqual(self.req("GET", f"/api/particles/{a['id']}")[1]["n_picked"], 4, "the copy is independent")

    # ---------- delete / restore: nothing is destroyed on a click ----------
    def test_a_set_in_use_says_which_packs_and_is_refused_until_confirmed(self):
        _, a = self.set_from_effect()
        code, j = self.req("POST", f"/api/particles/{a['id']}/delete", {})
        self.assertEqual(code, 409)
        self.assertIn("Fruits", j["error"])
        self.assertTrue((self.out / "particles" / a["id"] / "set.json").is_file(), "nothing moved")
        code, j = self.req("POST", f"/api/particles/{a['id']}/delete", {"confirm": True})
        self.assertEqual((code, j["trashed"]), (200, True))
        self.assertEqual(j["was_in"], [self.pack["id"]])
        self.assertFalse((self.out / "particles" / a["id"]).exists())
        self.assertTrue((self.out / "trash" / "particles" / a["id"] / "set.json").is_file())
        self.assertEqual([r["id"] for r in self.req("GET", "/api/particles")[1]["sets"]], [])

    def test_restore_puts_it_back_under_the_same_id_and_packs(self):
        _, a = self.set_from_effect()
        self.req("POST", f"/api/particles/{a['id']}/delete", {"confirm": True})
        self.assertEqual(self.req("GET", f"/api/particles/{a['id']}")[0], 404, "a deleted set is not served")
        code, j = self.req("POST", f"/api/particles/{a['id']}/restore")
        self.assertEqual(code, 200)
        self.assertEqual((j["id"], j["packs"], j["n_cells"]), (a["id"], [self.pack["id"]], 4))
        self.assertEqual([r["id"] for r in self.req("GET", "/api/particles")[1]["sets"]], [a["id"]])

    def test_restore_refuses_when_the_id_is_taken_again(self):
        """A live set must never be overwritten by a restore (the ids never collide by construction, so this guards a hand-edited folder)."""
        import shutil
        _, a = self.set_from_effect()
        self.req("POST", f"/api/particles/{a['id']}/delete", {"confirm": True})
        shutil.copytree(self.out / "trash" / "particles" / a["id"], self.out / "particles" / a["id"])   # a folder put back by hand
        code, j = self.req("POST", f"/api/particles/{a['id']}/restore")
        self.assertEqual(code, 409)
        self.assertIn("duplicate", j["error"].lower())
        self.assertTrue((self.out / "trash" / "particles" / a["id"] / "set.json").is_file(), "the deleted copy is still there to retry")

    def test_a_deleted_id_is_never_handed_out_again(self):
        _, a = self.set_from_effect()
        self.req("POST", f"/api/particles/{a['id']}/delete", {"confirm": True})
        _, b = self.req("POST", "/api/particles", {"name": "new"})
        self.assertNotEqual(b["id"], a["id"], "the number space is shared with the trash so a restore cannot collide")

    # ---------- the pack's studio ----------
    def test_the_pack_route_gives_the_sets_and_the_bursts_in_one_read(self):
        _, a = self.set_from_effect(name="Barbie hearts")
        j = self.req("GET", f"/api/packs/{self.pack['id']}/particles")[1]
        self.assertEqual(j["pack_id"], self.pack["id"])
        self.assertEqual([s["id"] for s in j["sets"]], [a["id"]])
        self.assertEqual(j["bursts"], [], "no burst has been rendered from this set yet")
        self.assertIn("counts", j, "the per-sticker counts the old answer carried are still there")

    def test_the_pack_route_only_lists_the_sets_of_that_pack(self):
        _, a = self.set_from_effect()
        other = self.c.lib.create_pack("Princess")
        j = self.req("GET", f"/api/packs/{other['id']}/particles")[1]
        self.assertEqual(j["sets"], [])

    def test_a_pack_that_does_not_exist_is_a_404(self):
        self.assertEqual(self.req("GET", "/api/packs/nope/particles")[0], 404)

    # ---------- a stand-alone set, made without a run ----------
    def test_an_empty_set_can_be_made_by_hand_for_generate_more(self):
        code, j = self.req("POST", "/api/particles", {"name": "Hearts", "elements": ["pink heart", "red heart"], "kind": "stickers"})
        self.assertEqual(code, 201)
        self.assertEqual((j["n_cells"], j["n_picked"]), (0, 0))
        self.assertEqual(j["elements"], ["pink heart", "red heart"])
        code, _ = self.req("POST", "/api/particles", {"name": "x", "kind": "explode"})
        self.assertEqual(code, 400, "only the three kinds the plan has")


class SetUnitTests(unittest.TestCase):
    """The storage rules on their own, without a server."""

    def setUp(self):
        import shutil
        import tempfile
        from pathlib import Path
        self.tmp = Path(tempfile.mkdtemp())
        self.out = self.tmp / "out"
        self.out.mkdir()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_the_id_is_a_P_and_the_folder_is_out_particles(self):
        s = ps.create(self.out, None, name="Hearts")
        self.assertRegex(s["id"], r"^P\d{3}$")
        self.assertTrue((self.out / "particles" / s["id"] / "set.json").is_file())
        self.assertEqual(ps.read(self.out, s["id"])["name"], "Hearts")

    def test_a_set_with_no_name_gets_a_default_and_a_long_one_is_cut(self):
        self.assertEqual(ps.create(self.out, None, name="   ")["name"], "particles")
        self.assertLessEqual(len(ps.create(self.out, None, name="x" * 200)["name"]), ps.MAX_NAME)

    def test_duplicate_element_names_are_folded(self):
        self.assertEqual(ps.create(self.out, None, elements=["heart", "Heart", " HEART ", "rose"])["elements"], ["heart", "rose"])

    def test_reading_a_set_that_does_not_exist_is_a_404_not_a_crash(self):
        with self.assertRaises(ps.SetError) as e:
            ps.read(self.out, "P999")
        self.assertEqual(e.exception.code, 404)
        for bad in ("nope", "", "X001", "P1x"):
            with self.assertRaises(ps.SetError):
                ps.read(self.out, bad)

    def test_a_path_that_looks_like_an_id_cannot_escape_the_folder(self):
        with self.assertRaises(ps.SetError):
            ps.read(self.out, "P001/../../etc")

class ChatAllowPayloadTests(unittest.TestCase):
    """Rule 10 on the chat surface needs the SERVER to say what may be allowed: a tile that cannot know cannot offer the override (no stubs, rule 6).
    No server and no provider: `ConsoleTools.generation` reads one result.json, so this is the payload contract alone."""

    def setUp(self):
        import shutil
        import tempfile
        from pathlib import Path
        from mirsal.engine.config import EngineConfig
        from mirsal.flow import pipeline as pl
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.out = self.tmp / "out"
        pl.gen_dir(self.out, 1).mkdir(parents=True)
        res = {"generation_id": "G001", "prompt": "p", "grid": [2, 2], "stage": "sliced", "owner": "local", "source": {}, "reviews": {},
               "stickers": [{"index": i, "key": f"k{i}", "name": f"S{i}", "emoji": "X", "tags": [], "status": "READY", "review": {"still": "PENDING", "anim": "NONE"},
                             "report": [], "metrics": {"bbox": [0, 0, 40, 40], "fg_px": 900}, "anim_status": "NOT_REQUESTED", "anim_report": [], "history": [], "png": None, "webm": None} for i in (1, 2)]}
        res["stickers"][0].update(status="FAILED", reason="holes", review={"still": "BLOCKED", "anim": "NONE"},
                                  report=[{"name": "holes", "ok": False, "severity": "BLOCK", "value": 1, "limit": 0}])
        # a cell with nothing cut may never be allowed, and a cell with one may: the metrics say so (gates.still_problem)
        res["stickers"][1].update(still_override=["inside_cell"])          # a person already allowed this one
        pl.write_result(self.out, 1, res)

    def tools(self):
        from mirsal.agent.tools import ConsoleTools
        return ConsoleTools(type("C", (), {"out": self.out, "lib": None})(), {"id": "local", "role": "owner", "can_spend": True})

    def test_every_sticker_carries_what_a_person_may_do_with_it(self):
        cells = self.tools().generation("G001")["stickers"]
        self.assertEqual([c["index"] for c in cells], [1, 2])
        for c in cells:
            self.assertEqual(sorted(c["allow"]), ["animation", "still"])
            for kind in ("still", "animation"):
                self.assertEqual(sorted(c["allow"][kind]), ["allowed", "can", "final", "undo", "why"], "the tile needs all five to draw the override")

    def test_a_judgement_call_is_allowable_and_an_allowed_one_can_be_taken_back(self):
        cells = {c["index"]: c for c in self.tools().generation("G001")["stickers"]}
        self.assertTrue(cells[1]["allow"]["still"]["can"], "holes is a judgement call: the chat tile may offer 'use it anyway'")
        self.assertIn("holes", (cells[1]["allow"]["still"]["why"] or "") + (cells[1]["reason"] or ""))
        self.assertEqual(cells[2]["allow"]["still"]["allowed"], True, "the permission is visible, so the tile can say 'allowed by you'")
        self.assertEqual(cells[2]["waived"], ["inside_cell"])
        self.assertFalse(cells[2]["allow"]["still"]["can"], "what was allowed is not offered twice")

    def test_the_fake_says_the_same_shape(self):
        from mirsal.agent.tools import FakeTools
        f = FakeTools({"G001": {"generation": "G001", "stickers": [{"id": "G001/S1", "index": 1, "status": "FAILED", "reason": "holes", "still": "BLOCKED"}]}})
        cell = f.generation("G001")["stickers"][0]
        self.assertTrue(cell["allow"]["still"]["can"])
        self.assertEqual(cell["waived"], [])
        self.assertEqual(f.gens["G001"]["stickers"][0].get("allow"), None, "the fixture is never mutated")
