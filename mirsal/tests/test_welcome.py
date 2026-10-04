"""The welcome modal: the files it shows are served with Range (a browser seeks and loops a video through it), nothing outside its folder is, the page loads its script, and the
Mirsal logo is the home button. The modal's own markup is tested in tests/js/welcome.test.js."""
import http.client
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from mirsal.console.server import serve
from mirsal.engine.config import EngineConfig

UI = Path(__file__).resolve().parents[1] / "mirsal" / "console"


class WelcomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        (cls.tmp / "in" / "Images_gen").mkdir(parents=True)
        (cls.tmp / "in" / "videos_gen").mkdir(parents=True)
        cls.srv, cls.c = serve(cls.tmp / "out", cls.tmp / "in", 0, cfg=EngineConfig(), block=False)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def get(self, path, headers=None):
        h = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h.request("GET", path, headers=headers or {})
        r = h.getresponse()
        body = r.read()
        h.close()
        return r.status, dict(r.getheaders()), body

    def test_a_slide_is_served_whole_and_in_ranges(self):
        code, hdr, body = self.get("/assets/welcome/s1.webp")
        self.assertEqual((code, hdr["Content-Type"]), (200, "image/webp"))
        self.assertEqual(hdr["Accept-Ranges"], "bytes")
        self.assertEqual(body[:4], b"RIFF")
        code, hdr, part = self.get("/assets/welcome/s1.webp", {"Range": "bytes=0-99"})
        self.assertEqual((code, len(part)), (206, 100))
        self.assertTrue(hdr["Content-Range"].startswith("bytes 0-99/"))

    def test_only_its_own_files_are_served(self):
        for p in ("/assets/welcome/nope.webp", "/assets/welcome/..%2f..%2fserver.py", "/assets/welcome/s1.exe", "/assets/welcome/"):
            self.assertEqual(self.get(p)[0], 404, p)

    def test_the_page_loads_the_script_and_the_logo_is_home(self):
        code, _, html = self.get("/")
        self.assertEqual(code, 200)
        self.assertIn(b"/ui/welcome.js", html)
        self.assertIn(b"<div id=welcome>", html)
        self.assertEqual(self.get("/ui/welcome.js")[0], 200)
        self.assertIn("data-act=home", (UI / "app.js").read_text(encoding="utf-8"))

    def test_the_session_and_home_rules(self):
        js = (UI / "welcome.js").read_text(encoding="utf-8")
        self.assertIn("sessionStorage,WL_SEEN", js, "the first open of a browser session")
        self.assertIn("ACT.home=", js)
        self.assertIn("ACT.wlclose", js)
        self.assertIn("Escape", js)


if __name__ == "__main__":
    unittest.main()
