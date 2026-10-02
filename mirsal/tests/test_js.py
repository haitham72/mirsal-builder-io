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

    def test_an_expanded_history_card_is_that_batch_s_studio_view(self):
        """Haitham, 2026-10-02: one click on an earlier batch expands the card and you see THAT batch's Studio view — the same working Request > Prompt > Stickers >
        Animation > Pack header, repeated for every open card. It reuses the Studio's own markup (no second view written for it), and the history lines and AI captions stay below."""
        ui, _ = self.scripts()
        live = (ui / "live.js").read_text(encoding="utf-8")
        gen = (ui / "generate.js").read_text(encoding="utf-8")
        card = self.block(live, "const histItem=it=>{")
        self.assertIn("studioFor(g)", card, "the expanded card renders that batch's Studio view")
        self.assertIn("hxBatch(it)", card, "the per-sticker history and the AI captions stay, below it")
        view = self.block(gen, "function studioFor(g)")
        for reused in ("stepsHtml(", "gbodyHtml(", "barHtml("):
            self.assertIn(reused, view, "the card's view is the Studio's own header, views and bar: " + reused)
        self.assertNotIn("class=gsteps", view, "no second header written for the card")
        self.assertIn("CT[g.number]", gen, "each card has its own step (CT)")
        self.assertIn(".gcardview", (ui / "studio.css").read_text(encoding="utf-8"))

    def test_the_step_header_and_the_actions_work_per_card(self):
        """Two open cards must not share a tab or an action: the header's tabs carry the batch (data-c -> CT), and Animate / Add to a pack act on the batch the button names."""
        ui, _ = self.scripts()
        gen = (ui / "generate.js").read_text(encoding="utf-8")
        steps = self.block(gen, "function stepsHtml(c")
        self.assertIn("tab===cur", steps, "the current step is the one passed in, not the session's global tab")
        self.assertIn("data-c=${gid}", steps, "every tab button says which card it belongs to")
        self.assertIn("data-g=${gid}", steps, "the Pack step is that card's pack")
        gtab = self.block(gen, "ACT.gtab=el=>{")
        self.assertIn("el.dataset.c", gtab, "a card's tab is remembered in CT and only that card is re-drawn")
        self.assertIn("drawHist()", gtab)
        for act in ("ACT.ganimate=async el=>", "ACT.gadd=async el=>"):
            self.assertIn(act, gen, act + " takes the button it was clicked on")
        self.assertIn("scopeGens(el)", gen, "both actions are scoped to that batch when the button carries data-g")
        scope = self.block(gen, "const scopeGens=el=>")
        self.assertIn("el.dataset.g", scope)
        self.assertIn("included()", scope, "without data-g they still act on the whole session")
        run = self.block(gen, "async function gaddrun(")
        self.assertIn("PW.rows.map(r=>r.g)", run, "the wizard adds exactly the batches it listed (a card's one batch), not the session's")
        self.assertIn("if(!card)", run, "a card never changes the session's pack")

    def test_two_cards_never_share_an_element_id(self):
        """The Prompt and Request views use element ids (copy boxes, the request textarea): inside two open cards they must be suffixed with the batch."""
        ui, _ = self.scripts()
        gen = (ui / "generate.js").read_text(encoding="utf-8")
        self.assertIn("function planView(g,pfx='')", gen)
        self.assertIn("`pp1${pfx}`", gen, "the sheet prompt box id carries the batch")
        self.assertIn("`pp2${pfx}`", gen)
        self.assertIn("function requestView(gs,pfx='')", gen)
        self.assertIn("id=greq${pfx}", gen)
        body = self.block(gen, "function gbodyHtml(gs,c")
        self.assertIn("requestView(gs,gid)", body)
        self.assertIn("planView(gs[0],gid)", body)

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


class ShellTests(unittest.TestCase):
    """docs/design.md 4: ONE shell for every screen. The rail is declared in app.js (six items, AI first), the column widths are tokens, and the narrow-screen layout is the
    shell's, not one screen's: it used to exist only under `body.agent-view` in agent.css, so only AI had a phone layout."""

    @staticmethod
    def ui():
        return Path(__file__).resolve().parent.parent / "mirsal" / "console"

    def test_the_rail_declares_six_items_and_ai_is_first(self):
        import re
        ui = self.ui()
        app = (ui / "app.js").read_text(encoding="utf-8")
        rail = re.search(r"const RAIL=\[(.*?)\],RAILOF", app).group(1)
        items = re.findall(r"\['(\w+)','(\w+)','([^']+)'\]", rail)
        self.assertEqual([i[2] for i in items], ["AI", "Studio", "Library", "Chat", "Create", "Settings"])
        screens = re.search(r"const SCREENS=\[(.*?)\]", app).group(1)
        html = (ui / "index.html").read_text(encoding="utf-8")
        for route, icon, _ in items:
            self.assertIn(f"'{route}'", screens, f"the rail's {route} is a screen")
            self.assertIn(f"id=s-{route}", html, f"the rail's {route} has a section")
            self.assertRegex(app, rf"\b{icon}:'<", f"the rail's icon {icon} exists")
        self.assertNotIn("RAIL.unshift", (ui / "agent.js").read_text(encoding="utf-8"), "a later script must not register itself in the navigation")

    def test_the_narrow_layout_is_the_shells_and_not_one_screens(self):
        import re
        ui = self.ui()
        studio = (ui / "studio.css").read_text(encoding="utf-8")
        agent = (ui / "agent.css").read_text(encoding="utf-8")
        self.assertNotIn("agent-view", agent + studio + (ui / "app.js").read_text(encoding="utf-8"), "no screen has its own shell")
        for token in ("--rail-w:", "--col2-w:"):
            self.assertIn(token, studio)
        self.assertNotRegex(agent, r"grid-template-columns:\s*(96px|var\(--rail-w\))", "agent.css does not size the page grid")
        self.assertNotRegex(agent, r"#rail|#app|#col2\{", "agent.css does not restyle the shell")
        phone = studio[studio.index("@media (max-width:760px){\n body #app"):]
        self.assertIn("#rail{order:2;flex-direction:row", phone, "every screen gets the bottom bar on phones")
        self.assertIn("body.col2 #col2{left:0", phone)
        self.assertIn("#c2tog", studio)
        self.assertIn("id=c2tog", (ui / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
