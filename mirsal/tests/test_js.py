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

    def test_the_earlier_batches_title_is_plain_text_and_the_list_is_not_paged_by_a_button(self):
        """Haitham asked for a plain title (2026-10-02) and, with the move into the shared column, for no "Load more": the list scrolls and asks for its next page by itself.
        Nothing folds the list away, nothing remembers that in localStorage."""
        ui, order = self.scripts()
        src = (ui / "live.js").read_text(encoding="utf-8")
        head = self.block(src, "function histColHTML()")
        self.assertNotIn("htoggle", src, "the collapsible Earlier-batches header is gone")
        self.assertNotIn("mirsal.hopen", src, "the fold-away choice (localStorage mirsal.hopen) is gone")
        self.assertNotIn("let HO=", src, "the fold state is gone")
        self.assertIn("<h1>Earlier batches</h1>", head, "the title is plain text above the rows")
        self.assertIn("HB.items.map(histRow)", head, "every batch is a row")
        for n in order + ["index.html"]:
            self.assertNotIn("hmore", (ui / n).read_text(encoding="utf-8"), f"no 'Load more' button action left in {n}")
        self.assertIn("histLoad(true)", self.block(src, "function histCol()"), "the column asks for its next page when it is scrolled near the end")
        css = (ui / "studio.css").read_text(encoding="utf-8")
        import re
        self.assertIsNone(re.search(r"\.lv-hh(?!ead)", css), "the styles of the old header button are gone")
        self.assertNotIn("#ghist.open", css)
        self.assertNotIn(".lv-hmore", css, "the Load more button's style is gone")

    def test_a_click_on_a_batch_presents_that_batch_and_only_that_batch(self):
        """Haitham, 2026-10-02: showing several batches at once in the Studio is not wanted. A click on a batch in the column makes it THE batch the Studio presents (ACT.hopen, the
        same action as the credits pill's recent batches): one session, one batch, one Studio view. The stacked open cards, their open-set, their localStorage key and the per-card
        copy of the Studio's header, views, bar and element ids are gone."""
        ui, order = self.scripts()
        src = (ui / "live.js").read_text(encoding="utf-8")
        row = self.block(src, "const histRow=it=>{")
        self.assertIn("data-act=hopen", row, "the row presents the batch")
        hopen = self.block(src, "ACT.hopen=el=>{")
        self.assertIn("gens:[it.id]", hopen, "the session becomes exactly this one batch")
        self.assertIn("location.hash='#/studio'", hopen, "from any other screen it goes to the Studio")
        everything = "".join((ui / n).read_text(encoding="utf-8") for n in order + ["studio.css"])
        for gone in ("HX.open", "hxSave", "mirsal.hbopen", "histItem", "studioFor", "cardTab", "ACT.hbx", "data-act=hbx", "gcardview", "lv-hcard", "lv-hitem", "scopeGens", "const CT=", "pfx"):
            self.assertNotIn(gone, everything, "the stacked cards are gone completely: " + gone)
        for needs in (".lv-hrow", ".lv-hrow.on"):
            self.assertIn(needs, (ui / "studio.css").read_text(encoding="utf-8"), "the presented batch is marked in the column")

    def test_under_the_presented_batch_its_own_history_stays(self):
        """The per-sticker history and the AI captions belong to the batch the Studio presents: one block per batch of the session (one unless Create more was used)."""
        ui, _ = self.scripts()
        src = (ui / "live.js").read_text(encoding="utf-8")
        draw = self.block(src, "function drawHist(){")
        self.assertIn("SES.gens.map", draw)
        self.assertIn("hxBatch(it)", draw)
        self.assertIn("HX.det", draw)
        sync = self.block(src, "function hxSync(){")
        self.assertIn("SES.gens", sync, "the presented batch is read again when it was edited or is still working")

    def test_every_list_bearing_screen_has_the_second_column(self):
        """Studio and Create list the earlier batches in the shared column (it used to exist only for Library, Pack, Chat and AI); Settings and the full-screen tools have none."""
        ui, _ = self.scripts()
        app = (ui / "app.js").read_text(encoding="utf-8")
        import re
        col2 = re.search(r"const COL2=\[(.*?)\]", app).group(1)
        for route in ("agent", "generate", "library", "pack", "chat", "create"):
            self.assertIn(f"'{route}'", col2)
        for route in ("settings", "editor", "export", "prepare", "animate"):
            self.assertNotIn(f"'{route}'", col2)
        self.assertIn("histCol()", self.block(app, "function drawCol2()"))

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

    def test_every_screen_shares_the_glow_the_page_width_and_the_row_states_of_ai(self):
        """docs/design.md 5: Library takes AI's glow and AI's hover / selection; the plain screens sit in ONE page width with ONE header; a heading's icon is sized (the Settings
        Telegram icon used to fill the page because nothing sized it)."""
        import re
        ui = self.ui()
        css = (ui / "studio.css").read_text(encoding="utf-8")
        self.assertIn("--glow-bg:", css)
        self.assertRegex(css, r"#app\{[^}]*background:var\(--glow-bg\)", "the glow is behind the whole shell, columns included")
        self.assertRegex(css, r"\.page\{max-width:\d+px;margin:0 auto\}")
        self.assertRegex(css, r"h1 svg,h2 svg\{width:\d+px")
        for name in ("app.js", "editor.js", "packs.js"):
            self.assertNotRegex((ui / name).read_text(encoding="utf-8"), r'<div style="max-width:\d+px;margin:0 auto">', f"{name}: a screen's width is the shared .page, not its own number")
        self.assertIn("class=page", (ui / "app.js").read_text(encoding="utf-8"))
        agent = (ui / "agent.css").read_text(encoding="utf-8")
        for state in ("hover{background:#F0F9FC}", "on{background:#E3F4F9}"):          # AI's chat rows: the pack rows, the chat rows and the batch rows read the same
            self.assertIn(state, agent.replace(" ", ""))
            self.assertIn(state, css.replace(" ", ""))
        self.assertIn("drawCol2()", self.block_of((ui / "packs.js").read_text(encoding="utf-8"), "RENDER.pack="), "a pack opened by its address draws its column after the library is read")

    @staticmethod
    def block_of(src, marker):
        return src[src.index(marker):].split("\n", 1)[0]

    def test_the_composer_has_no_palette_of_its_own_and_the_style_tiles_are_compact(self):
        """docs/design.md 5, Studio: the composer panel was a near-black navy island in a light app. It takes the shared glass surface, and the style tiles are small wrapping
        squares chosen by a ring and a check (they were six huge portrait cards in a horizontal scroller). The tiles are read from the API, never listed in the page."""
        import re
        ui = self.ui()
        css = (ui / "studio.css").read_text(encoding="utf-8")
        for navy in ("#070b1c", "#050816", "#2a52ff", "#0b1124", "#0e1633", "#3466ff", "#eaf0ff"):
            self.assertNotIn(navy, css, "the composer's navy island is gone: " + navy)
        self.assertRegex(css, r"\.cp\{[^}]*background:var\(--glass\)")
        styles = re.search(r"\.cp-styles\{([^}]*)\}", css).group(1)
        self.assertIn("flex-wrap:wrap", styles)
        tile = re.search(r"\.cp-style\{([^}]*)\}", css).group(1)
        self.assertNotIn("aspect-ratio:3/4", tile)
        self.assertRegex(tile, r"width:\d{2,3}px")
        self.assertIn(".cp-style.on", css)
        self.assertIn("LIVE.m.styles.map(", (ui / "composer.js").read_text(encoding="utf-8"), "the tiles come from the API's presets")

    def test_sizes_and_radii_come_from_one_scale_and_everything_answers_focus(self):
        """docs/design.md 3.2: six type steps and one radius scale, so a screen cannot drift; every interactive thing has a keyboard focus ring; motion respects the user's setting."""
        import re
        ui = self.ui()
        css = {n: (ui / n).read_text(encoding="utf-8") for n in ("studio.css", "agent.css")}
        for name, text in css.items():
            bare = [m for m in re.findall(r"font-size:\s*([0-9.]+)px", text)]
            self.assertEqual(bare, [], f"{name}: a font size outside the scale (use var(--fs-xs|s|m|l|xl|2xl)): {bare[:8]}")
            radii = [m for m in re.findall(r"border-radius:\s*([^;}]+)", text) if re.search(r"(?<![\w-])(?:[5-9]|[1-9]\d)px", m)]
            self.assertEqual(radii, [], f"{name}: a radius outside the scale (use var(--r-s|r-m|r|r-l|r-pill)): {radii[:8]}")
        self.assertRegex(css["studio.css"], r"--fs-xs:[\d.]+px;--fs-s:[\d.]+px;--fs-m:[\d.]+px;--fs-l:[\d.]+px;--fs-xl:[\d.]+px;--fs-2xl:[\d.]+px")
        self.assertIn("button:focus-visible", css["studio.css"])
        self.assertIn("prefers-reduced-motion:reduce){*,", css["studio.css"].replace(" ", ""))

    def test_the_ai_screen_shows_the_styles_and_the_settings_under_its_box(self):
        """Haitham, 2026-10-02: the AI screen shows the styles too, smaller. They are the Studio's presets (from GET /api/chat/agent), picked with one click; picking one before the first
        message must not create an empty chat (it waits in A.pre and is applied when the chat starts), and the grid and spending chips are the gear's settings, one click away."""
        import re
        ui = self.ui()
        js = (ui / "agent.js").read_text(encoding="utf-8")
        css = (ui / "agent.css").read_text(encoding="utf-8")
        self.assertIn("id=ag-styles", js)
        self.assertIn("(A.agent&&A.agent.styles)", js, "the tiles come from the API's presets, never a list in the page")
        pick = self.block_of(js, "ACT.agstyle=")
        self.assertIn("saveSet({style_id:A.pre})", pick, "with a chat, the pick is the chat's setting")
        self.assertIn("else drawBar()", pick, "without a chat, nothing is created")
        self.assertIn("applyPre()", self.block_of(js, " A.sid=r.j.id;"), "the pick is applied when the chat is created")
        self.assertIn("data-act=agsetgrid", js)
        self.assertIn("data-act=agsetask", js)
        for sel in (".ag-styles", ".ag-st", ".ag-st.on", ".ag-chip"):
            self.assertIn(sel, css)
        self.assertNotIn("#ai-sheet", js)


if __name__ == "__main__":
    unittest.main()
