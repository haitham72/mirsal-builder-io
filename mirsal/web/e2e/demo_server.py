"""E2E harness: the real Mirsal console on synthetic inputs, plus a tiny helper server that plays Haitham's hands.

    python e2e/demo_server.py            (run from mirsal/web; uses the project venv: mirsal/.venv)

  :8772  the console (serves mirsal/mirsal/console/dist)
  :8773  GET /drop?folder=img-001-teddy_bear&grid=3x3   puts a synthetic sheet into that watch folder
         GET /video?gen=1&sheet=A1&drift=1,2             makes a 'returned video' from a video sheet, returns its path
"""
import json
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROJECT = Path(__file__).resolve().parents[2]            # .../mirsal
sys.path.insert(0, str(PROJECT))

import cv2                                                 # noqa: E402
import numpy as np                                         # noqa: E402
from PIL import Image                                      # noqa: E402

from mirsal.console.server import serve                   # noqa: E402
from mirsal.engine.config import EngineConfig             # noqa: E402
from tests import synth                                    # noqa: E402
from tests.test_golden import shape_sheet                  # noqa: E402

ROOT = Path(tempfile.mkdtemp(prefix="mirsal-e2e-"))
INP, OUT = ROOT / "in", ROOT / "out"
(INP / "Images_gen").mkdir(parents=True)
(INP / "videos_gen").mkdir(parents=True)


def drop(folder: str, grid: str) -> str:
    n = int(grid[0])
    d = INP / "Images_gen" / folder
    d.mkdir(parents=True, exist_ok=True)
    cs = [(int((2 * c + 1) * 600 / n), int((2 * r + 1) * 600 / n)) for r in range(n) for c in range(n)]
    cv2.imwrite(str(d / "higgsfield_sheet.png"), cv2.cvtColor(shape_sheet(1200, cs, r=int(300 / n) if n > 1 else 140), cv2.COLOR_RGB2BGR))
    return str(d)


def video(gen: int, sheet: str, drift: str) -> str:
    g = OUT / f"G{gen:03d}" / "video_sheet" / sheet
    lay = json.loads((g / "layout.json").read_text())
    img = np.array(Image.open(g / "sheet.png").convert("RGB"))
    ds = [int(x) for x in drift.split(",") if x]
    d = {}
    if ds:
        d[ds[0]] = (-70, 0)
    if len(ds) > 1:
        d[ds[1]] = (0, -70)
    path = ROOT / f"returned-{gen}-{sheet}.mp4"
    synth.make_layout_video(path, img, lay, size=600, frames=45, drift=d)
    return str(path)


class Helper(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/drop":
                body = drop(q["folder"], q.get("grid", "3x3"))
            elif u.path == "/video":
                body = video(int(q["gen"]), q["sheet"], q.get("drift", ""))
            else:
                self.send_response(404); self.end_headers(); return
            code = 200
        except Exception as e:                      # surfaced to the spec
            body, code = f"error: {e}", 500
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())


if __name__ == "__main__":
    srv, _ = serve(OUT, INP, 8772, cfg=EngineConfig(), block=False)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"demo console on http://127.0.0.1:8772  (inputs {INP})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8773), Helper).serve_forever()
