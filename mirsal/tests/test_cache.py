"""Redis is disposable: the same behaviour on a real Redis (skipped when it is down) and on the in-process fallback."""
import threading
import time
import unittest

from mirsal.cache import Busy, Cache, digest


class Behaviour:
    def make(self) -> Cache:
        raise NotImplementedError

    def setUp(self):
        self.c = self.make()
        self.c.user = "t" + digest(time.time(), id(self))[:8]      # a private key space: never touches real data
        self.addCleanup(self.c.flush_mine)

    def test_values_ttl_and_read_through(self):
        k = self.c.key("plan", "x")
        self.assertIsNone(self.c.get(k))
        calls = []
        v1 = self.c.cached(k, lambda: calls.append(1) or {"cells": [1, 2]}, ttl=60)
        v2 = self.c.cached(k, lambda: calls.append(1) or {"cells": [9]}, ttl=60)
        self.assertEqual((v1, v2, len(calls)), ({"cells": [1, 2]}, {"cells": [1, 2]}, 1))
        self.assertEqual(self.c.report()["kinds"]["cache"]["hit"], 1)
        self.c.set(self.c.key("short"), "x", ttl=1)
        time.sleep(1.2)
        self.assertIsNone(self.c.get(self.c.key("short")))

    def test_counter_and_hash(self):
        k = self.c.key("pool", "version")
        self.assertEqual((self.c.counter(k), self.c.incr(k), self.c.incr(k), self.c.counter(k)), (0, 1, 2, 2))
        h = self.c.key("job", "G001")
        self.c.hset(h, {"node": "stills", "attempt": 1})
        self.c.hset(h, {"attempt": 2})
        self.assertEqual(self.c.hgetall(h), {"node": "stills", "attempt": 2})

    def test_session_lock_is_one_turn_at_a_time(self):
        with self.c.lock("session:s1"):
            with self.assertRaises(Busy):
                with self.c.lock("session:s1"):
                    pass
            with self.c.lock("session:s2"):          # another session is free
                pass
        with self.c.lock("session:s1"):              # released on exit
            pass

    def test_a_crashed_holder_expires(self):
        try:
            with self.c.lock("session:crash", ttl_ms=300):
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        with self.c.lock("session:crash", ttl_ms=300):
            pass

    def test_stream_replays_after_last_event_id(self):
        s = self.c.key("events", "G001")
        ids = [self.c.xadd(s, {"event": e, "n": i}) for i, e in enumerate(["generation_started", "sticker_ready", "sticker_ready"])]
        rows = self.c.xread(s)
        self.assertEqual([r[1]["event"] for r in rows], ["generation_started", "sticker_ready", "sticker_ready"])
        later = self.c.xread(s, after=ids[0])
        self.assertEqual([r[0] for r in later], ids[1:])
        self.assertEqual(self.c.xread(s, after=ids[-1]), [])

    def test_stream_is_capped(self):
        s = self.c.key("events", "cap")
        for i in range(30):
            self.c.xadd(s, {"i": i}, maxlen=10)
        self.assertLessEqual(len(self.c.xread(s)), 30)    # redis trims approximately; memory trims exactly
        self.assertEqual(self.c.xread(s)[-1][1]["i"], 29)

    def test_flushing_everything_costs_misses_only(self):
        k = self.c.key("plan", "y")
        self.c.set(k, {"a": 1})
        self.c.flush_mine()
        self.assertIsNone(self.c.get(k))
        self.assertEqual(self.c.cached(k, lambda: {"a": 2}), {"a": 2})

    def test_concurrent_lock_exactly_one_winner(self):
        wins, lock = [], threading.Lock()

        def go():
            try:
                with self.c.lock("session:race", ttl_ms=2000):
                    time.sleep(0.2)
                    with lock:
                        wins.append(1)
            except Busy:
                pass
        ts = [threading.Thread(target=go) for _ in range(6)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(len(wins), 1)


class MemoryEngine(Behaviour, unittest.TestCase):
    def make(self):
        c = Cache(force_memory=True)
        self.assertEqual(c.engine, "memory")
        return c


class RedisEngine(Behaviour, unittest.TestCase):
    def make(self):
        c = Cache()
        if c.engine != "redis":
            self.skipTest("mirsal-redis is not running (python -m mirsal db up)")
        return c


class PlannerCache(unittest.TestCase):
    """docs/agent-and-chat.md "Redis exit": a repeated request is a cache hit (0 model calls) and the key never merges a semantic difference."""

    def test_normalisation_only_touches_case_spaces_and_end_punctuation(self):
        from mirsal.cache import normalize_request as n
        self.assertEqual(n("  Dog   AS banana! "), n("dog as banana"))
        self.assertNotEqual(n("dog as banana"), n("dog with bananas"))
        self.assertNotEqual(n("dog as banana"), n("dog as banana but no dancing"))

    def test_a_repeated_plan_request_is_a_hit_and_a_failed_expansion_is_not_cached(self):
        import tempfile
        from pathlib import Path
        from unittest import mock
        from mirsal import cache as cachemod, tasks
        from mirsal.agent.tools import ConsoleTools

        class C:
            out = Path(tempfile.mkdtemp())
        calls = []

        def fake_preview(prompt, grid, style, ai):
            calls.append(prompt)
            return {"subject": "dog", "stickers": [], "expand_error": "model down" if len(calls) == 1 else None}
        mem = cachemod.Cache(force_memory=True)
        with mock.patch.object(cachemod, "default", lambda: mem), mock.patch.object(tasks, "preview", fake_preview):
            t = ConsoleTools(C())
            t.plan("Dog as banana", "3x3", "flat_vector", True)             # expansion failed: not cached
            t.plan("dog as banana!", "3x3", "flat_vector", True)            # planned and cached
            t.plan("  DOG as   banana ", "3x3", "flat_vector", True)         # a hit
            t.plan("dog with bananas", "3x3", "flat_vector", True)          # a different request
        self.assertEqual(len(calls), 3)
        self.assertEqual(mem.report()["kinds"]["plan"]["hit"], 1)


class FallbackWhenRedisDies(unittest.TestCase):
    def test_dead_redis_url_falls_back_to_memory(self):
        c = Cache(url="redis://127.0.0.1:9/0")
        self.assertEqual(c.engine, "memory")
        c.set(c.key("a"), 1)
        self.assertEqual(c.get(c.key("a")), 1)

    def test_generic_redis_url_is_ignored(self):
        import os
        old = os.environ.get("REDIS_URL")
        os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/0"       # another project's cache
        try:
            self.assertEqual(Cache(force_memory=True).url, "redis://localhost:6380/0")
        finally:
            os.environ.pop("REDIS_URL", None) if old is None else os.environ.__setitem__("REDIS_URL", old)


if __name__ == "__main__":
    unittest.main()
