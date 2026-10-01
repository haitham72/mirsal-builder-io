"""result.json is rewritten after every animated cell while the UI polls it: a write must survive a reader holding the file (WinError 5)."""
import json
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mirsal import pipeline as pl


class AtomicWrite(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.p = self.tmp / "result.json"
        self.p.write_text("{}", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_write_waits_for_a_foreign_reader(self):
        f = open(self.p, "rb")                      # an antivirus scan or another process: outside our lock
        threading.Timer(0.3, f.close).start()
        t0 = time.time()
        pl._atomic_write(self.p, b'{"a": 1}')
        self.assertEqual(json.loads(self.p.read_text()), {"a": 1})
        self.assertFalse(self.p.with_name("result.json.tmp").exists())
        self.assertLess(time.time() - t0, 5)

    def test_concurrent_readers_and_writer(self):
        stop, errs = threading.Event(), []

        def reader():
            while not stop.is_set():
                try:
                    with pl._IO_LOCK:
                        json.loads(self.p.read_text(encoding="utf-8"))
                except Exception as e:
                    errs.append(e)
                time.sleep(0.001)
        ts = [threading.Thread(target=reader) for _ in range(4)]
        [t.start() for t in ts]
        try:
            for i in range(100):
                pl._atomic_write(self.p, json.dumps({"i": i}).encode())
        finally:
            stop.set()
            [t.join() for t in ts]
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
