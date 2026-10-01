"""Phase 3A: Postgres round trip, idempotent import, history, search, engine boundary, trace seam.
Uses a throwaway database (mirsal_test) on the same container; skipped when it is not running."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

TEST_URL = "postgresql://mirsal:mirsal_local@localhost:5434/mirsal_test"

os.environ["MIRSAL_DATABASE_URL"] = TEST_URL


def _result(gid, parent=None, full=True):
    stickers = []
    for i in range(1, 10):
        s = {"index": i, "key": f"tedy_book_{i}" if i == 1 else f"sticker_{i}",
             "name": f"img-{gid:03d}-tedy-tedy_book_{i}" if i == 1 else f"img-{gid:03d}-tedy-sticker_{i}",
             "prompt": "a teddy bear holding a book" if i == 1 else f"a teddy bear pose {i}",
             "emoji": "\U0001F4DA" if i == 1 else "\U0001F600",
             "status": "READY" if i != 4 else "FAILED", "reason": None if i != 4 else "empty_subject",
             "report": [], "metrics": {}, "png": None, "webm": None,
             "anim_status": "NOT_REQUESTED", "anim_reason": None, "anim_metrics": {}}
        if full:
            s["tags"] = [s["key"], "book"] if i == 1 else [s["key"]]
            s["review"] = {"still": "APPROVED", "anim": "NONE"}
            s["history"] = [
                {"ts": 1700000000.0 + i, "stage": "sliced", "actor": "python",
                 "decision": "PASS", "reason": None, "ref": None, "detail": {}},
                {"ts": 1700000100.0 + i, "stage": "still", "actor": "human",
                 "decision": "APPROVE", "reason": "good", "ref": None, "detail": None}]
        stickers.append(s)
    res = {"generation_id": f"G{gid:03d}", "number": gid, "parent": parent, "prompt": "tedy with a book",
           "task": "tedy with a book", "task_slug": "tedy", "stage": "sliced",
           "source": {"subject": "tedy", "subject_id": "099", "variant": 1},
           "stickers": stickers}
    if full:
        res.update({"grid": [3, 3], "verify_version": "2", "template_id": "sheet_3x3", "template_version": 1,
                    "slots": {"cells": []}, "outline_px": 12, "erode_px": 0, "name_key": "tedy",
                    "reviews": {"plan": {"decision": "APPROVE", "by": "human", "ts": 1700000000.0, "note": "go"}},
                    "video_sheets": [], "verify": {}})
    return res


def _write_gen(td, gid, res):
    gd = Path(td) / f"G{gid:03d}"
    gd.mkdir(parents=True, exist_ok=True)
    (gd / "result.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    (gd / "prompts.json").write_text(json.dumps({"task_slug": res["task_slug"]}), encoding="utf-8")
    (gd / "events.jsonl").write_text(
        json.dumps({"ts": 1700000000.0, "stage": "requested", "status": "done", "ms": 1, "detail": {}}) + "\n",
        encoding="utf-8")


class StoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        base = TEST_URL.rsplit("/", 1)[0] + "/mirsal"
        try:
            boot = psycopg.connect(base, connect_timeout=5, autocommit=True)
        except Exception:
            raise unittest.SkipTest("mirsal-db is not running (python -m mirsal db up)")
        with boot:
            with boot.cursor() as cur:
                cur.execute("DROP DATABASE IF EXISTS mirsal_test")
                cur.execute("CREATE DATABASE mirsal_test")
        from mirsal.store import db
        db.reset_cache()
        db.migrate()
        cls.tmp = Path(tempfile.mkdtemp())
        _write_gen(cls.tmp, 1, _result(1, full=False))   # pre-1F shape: no tags/history
        _write_gen(cls.tmp, 2, _result(2, parent=1))     # int parent -> G001
        with db.connect() as c:
            from mirsal.store import repo
            repo.save_generation(c, cls.tmp, 1)
            repo.save_generation(c, cls.tmp, 2)

    def _conn(self):
        from mirsal.store import db
        return db.connect()

    def test_round_trip(self):
        from mirsal.store import repo
        with self._conn() as c:
            g = repo.get_generation(c, "G002")
        self.assertEqual((g["task_slug"], len(g["stickers"]), g["parent_id"]), ("tedy", 9, "G001"))
        s1 = next(s for s in g["stickers"] if s["idx"] == 1)
        self.assertEqual((s1["key"], s1["tags"][0], s1["emoji"]), ("tedy_book_1", "tedy_book_1", ["\U0001F4DA"]))
        self.assertEqual(s1["still_review"], "APPROVED")

    def test_pre_1f_import(self):
        """Results written before 1F have no tags/history: tags = [key], python verdicts from status, gates PENDING."""
        from mirsal.store import repo
        with self._conn() as c:
            g = repo.get_generation(c, "G001")
            h = repo.history(c, "G001/S1")
        s1 = next(s for s in g["stickers"] if s["idx"] == 1)
        self.assertEqual(s1["tags"], ["tedy_book_1"])
        self.assertEqual(s1["still_review"], "PENDING")
        self.assertEqual(h, [])

    def test_import_is_idempotent(self):
        from mirsal.store import repo
        from mirsal.store import db
        with db.connect() as c:
            before = {t: c.execute(f"select count(*) from {t}").fetchone()[0]
                      for t in ("generations", "stickers", "reviews", "generation_events", "assets", "tasks")}
            repo.save_generation(c, self.tmp, 2)
            repo.save_generation(c, self.tmp, 2)
            after = {t: c.execute(f"select count(*) from {t}").fetchone()[0]
                     for t in ("generations", "stickers", "reviews", "generation_events", "assets", "tasks")}
        self.assertEqual(before, after)

    def test_history_order(self):
        from mirsal.store import repo
        with self._conn() as c:
            h = repo.history(c, "G002/S1")
        self.assertEqual([(r["gate"], r["decision"], r["actor"]) for r in h],
                         [("still", "PASS", "python"), ("still", "APPROVE", "human")])

    def test_search_and_trigram(self):
        from mirsal.store import repo
        with self._conn() as c:
            self.assertTrue(any(r["id"] == "G002/S1" for r in repo.search(c, "tedy book")))
            self.assertTrue(any(r["id"] == "G002/S1" for r in repo.search(c, "tedy bok")))  # typo fallback
            self.assertEqual(repo.search(c, "penguin skiing"), [])                          # nothing -> nothing
            self.assertEqual(repo.search(c, "tedy", approved=True)[0]["id"], "G002/S1")

    def test_task_prefix(self):
        from mirsal.store import repo
        with self._conn() as c:
            rows = repo.find_task(c, key_prefix="ted")
        self.assertTrue(rows and all(r["provider"] == "prepared" for r in rows))

    def test_tmp_out_never_touches_the_shared_db(self):
        """The golden-path suite serves temp dirs with the DB up: search and write-through must stay on files."""
        from mirsal.store import sync
        self.assertFalse(sync.is_default_out(self.tmp))
        self.assertFalse(sync.enabled(self.tmp))

    def test_engine_boundary(self):
        code = ("import sys, mirsal.engine.sheet, mirsal.engine.video;"
                "bad=[m for m in ('fastapi','psycopg','langgraph','anthropic','pydantic','redis') if m in sys.modules];"
                "sys.exit(1 if bad else 0)")
        self.assertEqual(subprocess.run([sys.executable, "-c", code]).returncode, 0)

    def test_trace_none_makes_no_network_calls(self):
        from mirsal.obs import trace as tr
        real = socket.socket
        socket.socket = lambda *a, **k: (_ for _ in ()).throw(OSError("blocked"))
        try:
            os.environ["MIRSAL_TRACE"] = "none"
            t = tr.Tracer()
            with t.span("stage", {"a": 1}) as rid:
                self.assertIsNone(rid)
            t.feedback(None, "gate_still", 1, "ok")
        finally:
            socket.socket = real
            os.environ.pop("MIRSAL_TRACE", None)

    def test_trace_langsmith_shape_and_failure(self):
        from mirsal.obs import trace as tr
        seen, calls = [], {"n": 0}

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0))
                seen.append(json.loads(self.rfile.read(n).decode()))
                calls["n"] += 1
                self.send_response(500 if calls["n"] == 1 else 200)  # first post fails
                self.end_headers()

            def log_message(self, *a):
                pass

        srv = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        os.environ.update(MIRSAL_TRACE="langsmith",
                          LANGSMITH_ENDPOINT=f"http://127.0.0.1:{srv.server_port}",
                          LANGSMITH_API_KEY="test-key")
        try:
            t = tr.Tracer(project="p")
            with t.span("sliced", {"prompt": "x"}) as rid:
                pass
            t.feedback(rid, "gate_still", 1, "good")
            t._q.join()
        finally:
            os.environ.pop("MIRSAL_TRACE", None)
            os.environ.pop("LANGSMITH_ENDPOINT", None)
            os.environ.pop("LANGSMITH_API_KEY", None)
            srv.shutdown()
        self.assertTrue(seen)
        blob = json.dumps(seen)
        self.assertNotIn("bytes", blob.replace("latency_ms", ""))
        self.assertEqual(t.dropped, 1)  # the 500 was dropped, the pipeline never noticed


if __name__ == "__main__":
    unittest.main()
