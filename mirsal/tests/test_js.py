"""The JavaScript that has no DOM in it (agent.js helpers: the HTML escaping of the chat) under node's built-in test runner. node is a test dependency: without it this FAILS
(an escaping suite that silently skips is no suite). `MIRSAL_SKIP_JS=1` skips it on purpose."""
import os
import shutil
import subprocess
import unittest
from pathlib import Path


class JavaScriptTests(unittest.TestCase):
    def test_node_suite(self):
        node = shutil.which("node")
        if os.environ.get("MIRSAL_SKIP_JS") == "1":
            self.skipTest("MIRSAL_SKIP_JS=1")
        if not node:
            self.fail("node is not installed: the escaping tests of the chat need it (set MIRSAL_SKIP_JS=1 to skip them on purpose)")
        root = Path(__file__).resolve().parent.parent
        files = sorted(str(f.relative_to(root)) for f in (root / "tests" / "js").glob("*.test.js"))
        r = subprocess.run([node, "--test", *files], cwd=str(root), capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr[-800:])


class StudioActionTests(unittest.TestCase):
    """The Studio's buttons are `data-act=name`, handled by `ACT.name = ...`. The scripts share ONE `ACT` object, so a second `ACT.name =` in a later script silently
    replaces the first: `history.js` (the retired History screen) did that to `hopen`, so every batch in "Earlier batches" opened batch NaN. A name may be defined twice
    only on purpose, and every deliberate replacement is listed here."""

    INTENTIONAL = {"ggo": "composer.js", "gsug": "composer.js"}        # the Generate menu replaces the old input row's Generate and chip handlers (it keeps `_ggo`)

    @staticmethod
    def scripts():
        import re
        ui = Path(__file__).resolve().parent.parent / "mirsal" / "console"
        html = (ui / "index.html").read_text(encoding="utf-8")
        order = re.findall(r"/ui/([A-Za-z0-9_.]+\.js)", html)                          # the order the page loads them in
        return ui, order

    def test_an_action_is_not_silently_replaced_by_a_later_script(self):
        import re
        ui, order = self.scripts()
        self.assertTrue(order)
        defs: dict[str, list[str]] = {}
        for name in order:
            src = (ui / name).read_text(encoding="utf-8")
            for m in re.finditer(r"\bACT\.([A-Za-z0-9_]+)\s*=(?!=)", src):
                defs.setdefault(m.group(1), []).append(name)
        twice = {act: files for act, files in defs.items() if len(files) > 1}
        unexpected = {act: files for act, files in twice.items() if self.INTENTIONAL.get(act) != files[-1] or len(files) != 2}
        self.assertEqual(unexpected, {}, "an action assigned twice: the later script silently replaces the earlier handler (rename one, or list it in INTENTIONAL)")
        self.assertEqual(set(self.INTENTIONAL) - set(twice), set(), "INTENTIONAL lists an action that is no longer replaced: delete the entry")

    def test_every_button_of_the_studio_has_a_handler(self):
        import re
        ui, order = self.scripts()
        defined, used = set(), {}
        for name in order + ["index.html"]:
            src = (ui / name).read_text(encoding="utf-8")
            defined |= set(re.findall(r"\bACT\.([A-Za-z0-9_]+)\s*=(?!=)", src))
            for m in re.finditer(r"data-act=\"?([A-Za-z0-9_]+)", src):
                used.setdefault(m.group(1), name)
        self.assertEqual({k: v for k, v in used.items() if k not in defined}, {}, "a button whose action nothing handles")

    def test_the_green_screen_panel_stays_when_a_batch_is_a_video(self):
        """The Animation tab shows the Video sheet AND the green screen (its cut lines, chips and the animation box): the second one used to be replaced."""
        import re
        ui, _ = self.scripts()
        src = (ui / "generate.js").read_text(encoding="utf-8")
        branch =re.search(r"mode==='anim'\?`<div class=gleft>(.*?)</div>`:sheetPanel\(g\)", src)
        self.assertIsNotNone(branch, "the animation branch of batchHtml no longer wraps both panels in .gleft")
        self.assertIn("videoPanel(g)", branch.group(1))
        self.assertIn("sheetPanel(g)", branch.group(1))
        self.assertIn(".gleft", (ui / "studio.css").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
