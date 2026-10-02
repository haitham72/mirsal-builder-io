"""Tracing wired into the pipeline (Phase 3A, A2): events, gate feedback, model calls, no media, no network when off."""
import json
import os
import socket
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from mirsal import model_calls, pipeline as pl
from mirsal.obs import trace


class FakeLangSmith:
    def __init__(self):
        self.seen = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def _do(self):
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n).decode() or "{}")
                outer.seen.append((self.command, self.path, body, self.headers.get("x-api-key")))
                self.send_response(200)
                self.end_headers()

            do_POST = do_PATCH = do_GET = _do

            def log_message(self, *a):
                pass

        self.srv = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def runs(self):
        return [b for m, p, b, _ in self.seen if m == "POST" and p == "/runs"]

    def feedback(self):
        return [b for m, p, b, _ in self.seen if m == "POST" and p == "/feedback"]


class TraceWiringTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.out = Path(self.td.name)
        (self.out / "G007").mkdir()
        self.env = {k: os.environ.get(k) for k in ("MIRSAL_TRACE", "LANGSMITH_ENDPOINT", "LANGSMITH_API_KEY",
                                                   "LANGSMITH_PROJECT", "MIRSAL_LANGSMITH_PROJECT")}
        trace.reset()

    def tearDown(self):
        for k, v in self.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        trace.reset()
        self.td.cleanup()

    def _on(self):
        fake = FakeLangSmith()
        os.environ.update(MIRSAL_TRACE="langsmith", LANGSMITH_ENDPOINT=f"http://127.0.0.1:{fake.srv.server_port}",
                          LANGSMITH_API_KEY="k", LANGSMITH_PROJECT="NeoHealth")   # another project's setting must be ignored
        trace.reset()
        return fake

    def test_one_root_per_generation_and_a_child_per_event(self):
        fake = self._on()
        pl.emit(self.out, 7, "requested", "done", 5, {"prompt": "teddy"})
        pl.emit(self.out, 7, "sliced", "done", 40, {"ready": 9})
        trace.tracer().flush()
        runs = fake.runs()
        roots = [r for r in runs if r["parent_run_id"] is None]
        kids = [r for r in runs if r["parent_run_id"]]
        self.assertEqual(len(roots), 1)
        self.assertEqual([k["name"] for k in kids], ["requested", "sliced"])
        self.assertTrue(all(k["parent_run_id"] == roots[0]["id"] and k["trace_id"] == roots[0]["id"] for k in kids))
        self.assertTrue(all(k["dotted_order"].startswith(roots[0]["dotted_order"] + ".") for k in kids))
        self.assertTrue(all(r["session_name"] == "mirsal" for r in runs))       # never LANGSMITH_PROJECT
        # the run id rides on the event line, and a second request parents under the same root (trace.json)
        ev = pl.read_events(self.out, 7)
        self.assertEqual([e["trace_run_id"] for e in ev], [k["id"] for k in kids])
        trace.reset()
        pl.emit(self.out, 7, "anim_reviewed", "done", 1, {})
        trace.tracer().flush()
        self.assertEqual(len([r for r in fake.runs() if r["parent_run_id"] is None]), 1)
        self.assertEqual(fake.runs()[-1]["parent_run_id"], roots[0]["id"])

    def test_a_decision_is_feedback_on_the_run_it_judges(self):
        fake = self._on()
        pl.emit(self.out, 7, "stills_reviewed", "done", 0, {"index": 5, "note": "too dark"}, "human", "REJECT")
        pl.emit(self.out, 7, "video_sheet_built", "done", 3, {}, "python", "PASS")
        pl.emit(self.out, 7, "anim_reviewed", "done", 0, {}, "vlm", "APPROVE")
        trace.tracer().flush()
        fb = fake.feedback()
        self.assertEqual([(f["key"], f["score"]) for f in fb],
                         [("gate_still", 0), ("gate_video_sheet", 1), ("vlm_anim", 1)])
        self.assertEqual(fb[0]["comment"], "too dark")
        ids = {r["id"] for r in fake.runs()}
        self.assertTrue(all(f["run_id"] in ids for f in fb))

    def test_model_call_is_a_run_and_carries_no_bytes(self):
        fake = self._on()
        model_calls.append(self.out, "IMAGE_SHEET", "higgsfield-cli", "nano_banana_2", latency_ms=1200, cost=12.5,
                           generation_id="G007", extra={"blob": b"\x89PNG" * 10, "output": "jobs/J001/result.png"})
        trace.tracer().flush()
        run = next(r for r in fake.runs() if r["name"] == "IMAGE_SHEET")
        self.assertEqual(run["run_type"], "tool")
        self.assertEqual(run["outputs"]["cost"], 12.5)
        self.assertIsNotNone(run["parent_run_id"])
        self.assertNotIn("PNG", json.dumps(fake.seen))
        line = json.loads((self.out / "model_calls.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(line["trace_run_id"], run["id"])

    def test_off_means_no_network_and_no_ids(self):
        os.environ["MIRSAL_TRACE"] = "none"
        trace.reset()
        real = socket.socket
        socket.socket = lambda *a, **k: (_ for _ in ()).throw(OSError("blocked"))
        try:
            pl.emit(self.out, 7, "requested", "done", 1, {})
            model_calls.append(self.out, "LLM_PLAN", "openai", "m")
        finally:
            socket.socket = real
        self.assertNotIn("trace_run_id", pl.read_events(self.out, 7)[0])
        self.assertFalse((self.out / "G007" / "trace.json").exists())

    def test_a_dead_server_never_slows_or_fails_the_pipeline(self):
        os.environ.update(MIRSAL_TRACE="langsmith", LANGSMITH_ENDPOINT="http://127.0.0.1:9", LANGSMITH_API_KEY="k")
        trace.reset()
        pl.emit(self.out, 7, "requested", "done", 1, {})
        self.assertEqual(len(pl.read_events(self.out, 7)), 1)

    def test_safe_replaces_bytes_and_cuts_long_text(self):
        s = trace.safe({"a": b"12345", "b": "x" * 9000, "c": [b"zz"]})
        self.assertEqual(s["a"], "<5 bytes>")
        self.assertLess(len(s["b"]), 4100)
        self.assertEqual(s["c"], ["<2 bytes>"])


if __name__ == "__main__":
    unittest.main()
