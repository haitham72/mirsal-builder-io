"""Phase 3B pool, lexical pass: parse, index, search-first, hide, gap math. Own data (G101/G102)
so it is independent of test order; skipped when mirsal-db is not running."""
import json
import os
import tempfile
import unittest
from pathlib import Path

TEST_URL = "postgresql://mirsal:mirsal_local@localhost:5434/mirsal_test"

os.environ["MIRSAL_DATABASE_URL"] = TEST_URL


def _result(gid, keys):
    stickers = [{"index": i + 1, "key": k, "name": f"img-{gid:03d}-poolxyz-{k}",
                 "prompt": f"a poolxyz {k.replace('poolxyz_', '').replace('_', ' ')}",
                 "emoji": "\U0001F600", "status": "READY", "reason": None, "report": [], "metrics": {},
                 "png": None, "webm": None, "anim_status": "NOT_REQUESTED", "anim_reason": None, "anim_metrics": {},
                 "tags": [k], "review": {"still": "APPROVED", "anim": "NONE"},
                 "history": [{"ts": 1700000000.0, "stage": "sliced", "actor": "python",
                              "decision": "PASS", "reason": None, "ref": None, "detail": {}}]}
                for i, k in enumerate(keys)]
    return {"generation_id": f"G{gid:03d}", "number": gid, "parent": None, "prompt": "poolxyz",
            "task": "poolxyz", "task_slug": "poolxyz", "stage": "sliced", "grid": [3, 3],
            "source": {"subject": "poolxyz", "subject_id": "100", "variant": 1},
            "stickers": stickers, "verify_version": "2", "reviews": {}, "video_sheets": []}


class PoolTests(unittest.TestCase):
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
                cur.execute("SELECT 1 FROM pg_database WHERE datname = 'mirsal_test'")
                if not cur.fetchone():
                    cur.execute("CREATE DATABASE mirsal_test")
        from mirsal.store import db, repo
        db.reset_cache()
        db.migrate()
        td = Path(tempfile.mkdtemp())
        for gid, keys in ((101, ["poolxyz_dancing", "poolxyz_waving", "poolxyz_sleeping"]),
                          (102, ["poolxyz_dancing_hard"])):
            gd = td / f"G{gid:03d}"
            gd.mkdir(parents=True)
            (gd / "result.json").write_text(json.dumps(_result(gid, keys)), encoding="utf-8")
            (gd / "prompts.json").write_text("{}", encoding="utf-8")
            (gd / "events.jsonl").write_text("", encoding="utf-8")
        with db.connect() as c:
            repo.save_generation(c, td, 101)
            repo.save_generation(c, td, 102)

    def _conn(self):
        from mirsal.store import db
        return db.connect()

    def test_parse(self):
        from mirsal import pool
        self.assertEqual(pool.parse_query("falcon dancing"), {"subject": "falcon", "action": "dancing", "topics": []})
        self.assertEqual(pool.parse_query("falcon doing a flip")["action"], "a flip")
        self.assertEqual(pool.parse_query("dog as banana")["subject"], "dog as banana")  # 4B refines this
        self.assertEqual(pool.parse_query("sakr yarkos")["action"], "")

    def test_search_first_reuses(self):
        from mirsal import pool
        with self._conn() as c:
            pool.reindex(c)
            c.execute("UPDATE sticker_index SET hidden = false WHERE sticker_id = 'G101/S1'")
            c.commit()
            res = pool.search(c, "poolxyz dancing", count=9)
        self.assertEqual(res["parsed"]["action"], "dancing")
        self.assertTrue(any(h["sticker_id"] == "G101/S1" for h in res["hits"]))
        self.assertEqual((res["found"], res["missing"]), (len(res["hits"]), 9 - len(res["hits"])))

    def test_diversity_and_zero_rule(self):
        from mirsal import pool
        with self._conn() as c:
            pool.reindex(c)
            res = pool.search(c, "poolxyz", count=9)
            per_gen = {}
            for h in res["hits"]:
                if "poolxyz" in h["key"]:
                    per_gen[h["generation_id"]] = per_gen.get(h["generation_id"], 0) + 1
            self.assertTrue(all(v <= 2 for v in per_gen.values()))
            self.assertEqual(pool.search(c, "penguin skiing")["hits"], [])

    def test_hide_removes_without_deleting(self):
        from mirsal import pool
        from mirsal.store import repo
        with self._conn() as c:
            pool.reindex(c)
            self.assertTrue(pool.hide(c, "G101/S1"))
            res = pool.search(c, "poolxyz dancing", count=9)
            self.assertFalse(any(h["sticker_id"] == "G101/S1" for h in res["hits"]))
            self.assertIsNotNone(repo.get_generation(c, "G101"))  # the sticker still exists


if __name__ == "__main__":
    unittest.main()
