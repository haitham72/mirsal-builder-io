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

    @staticmethod
    def block(src: str, marker: str) -> str:
        """The whole of a top-level statement: from `marker` to the next line that starts in column 0 (the Studio's scripts are one statement per line, minified)."""
        rest = src[src.index(marker):]
        lines, out = rest.split("\n"), [rest.split("\n")[0]]
        for ln in lines[1:]:
            if ln and not ln[0].isspace():
                break
            out.append(ln)
        return "\n".join(out)

    def test_the_earlier_batches_title_is_plain_text_not_a_fold(self):
        """Haitham asked for a plain title (2026-10-02): the header is not a button, so nothing folds the list away and nothing remembers that in localStorage."""
        ui, _ = self.scripts()
        src = (ui / "live.js").read_text(encoding="utf-8")
        head = self.block(src, "function drawHist()")
        self.assertNotIn("htoggle", src, "the collapsible Earlier-batches header is gone")
        self.assertNotIn("mirsal.hopen", src, "the fold-away choice (localStorage mirsal.hopen) is gone")
        self.assertNotIn("let HO=", src, "the fold state is gone")
        self.assertNotIn("data-act=", head.split("<div class=lv-hhead>")[0], "nothing in the title folds the list")
        self.assertIn('<span class=lv-ht>Earlier batches</span>', head, "the title is plain text above the cards")
        self.assertIn("HB.items.map(histItem)", head, "the cards are always there")
        css = (ui / "studio.css").read_text(encoding="utf-8")
        import re
        self.assertIsNone(re.search(r"\.lv-hh(?!ead)", css), "the styles of the old header button are gone")
        self.assertNotIn("#ghist.open", css)

    def test_a_history_card_expands_in_place_and_nothing_else_does(self):
        """A click on the card expands it where it stands: the fold lives inside the card, it does not scroll and it does not load the batch into the main area. Every click
        expands its own card, so any number of them can be open at once (they stack). The button that opens a batch in the Studio belongs to the credits pill's recent batches."""
        import re
        ui, order = self.scripts()
        src = (ui / "live.js").read_text(encoding="utf-8")
        card = self.block(src, "const histItem=it=>{")
        hbx = self.block(src, "ACT.hbx=el=>{")
        self.assertIn("hxBatch(it)", card, "the expanded card hosts what already exists (stickers, per-sticker history, AI captions)")
        self.assertNotIn("scrollIntoView", card)
        self.assertIn("data-act=hbx", card, "the card itself is the fold")
        self.assertNotIn("data-act=hopen", card, "no 'Open in Studio' on the card: every click only expands it in place")
        opens = [n for n in order if "data-act=hopen" in (ui / n).read_text(encoding="utf-8")]
        self.assertEqual(opens, ["composer.js"], "only the credits pill's recent batches opens a batch in the Studio, never a history card")
        for gone in ("scrollIntoView", "location.hash", "tick(", "SES=", "HX.open.clear"):
            self.assertNotIn(gone, hbx, "expanding in place must not touch the Studio or close the other cards: " + gone)
        self.assertIn("HX.open.add(id)", hbx)
        css = (ui / "studio.css").read_text(encoding="utf-8")
        self.assertNotIn(".lv-hrow", css, "the row of the old list is gone")
        self.assertNotIn(".lv-huse", css, "the Open in Studio button's style is gone")
        self.assertIn(".lv-hcard", css)
        self.assertIn(".lv-hcard.open", css, "an open card is marked, so a stack of them reads at a glance")
        self.assertNotIn(".lv-hx", css, "the little fold button of the old row is gone: the whole card header is the fold")

    def test_the_credits_pill_reads_the_history_grid(self):
        """The drop-down under the credits pill lists the same batches as the history cards: it draws its one thumbnail from `cells`, not from the four-thumbnail shortcut."""
        ui, _ = self.scripts()
        src = (ui / "composer.js").read_text(encoding="utf-8")
        self.assertNotIn("it.thumbs", src, "`thumbs` is gone from GET /api/history: the pill would throw on every open")
        self.assertIn("it.cells", src)

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
