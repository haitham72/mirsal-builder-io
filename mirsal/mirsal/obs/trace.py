"""Tracing seam (Phase 3A, second half). span() + feedback() over two backends:
none (default: records nothing outside Postgres) and langsmith (batched posts on a background
thread; a failed post is logged and dropped). Tracing never blocks or fails the pipeline.
What leaves the machine: ids, slot JSON, prompts, metrics, decisions. Never image/video bytes."""
from __future__ import annotations

import json
import os
import queue
import threading
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path


def _load_dotenv() -> None:
    f = Path(__file__).resolve().parent.parent.parent / ".env"
    try:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


def backend() -> str:
    _load_dotenv()
    return os.environ.get("MIRSAL_TRACE", "none").lower()


def status() -> dict:
    b = backend()
    return {"backend": b, "reachable": _reachable() if b == "langsmith" else None}


def _endpoint() -> str:
    return os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com").rstrip("/")


def _reachable() -> bool:
    try:
        req = urllib.request.Request(_endpoint() + "/health", method="GET")
        urllib.request.urlopen(req, timeout=3)
        return True
    except Exception:
        return False


class Tracer:
    def __init__(self, project: str | None = None):
        _load_dotenv()
        self.project = project or os.environ.get("LANGSMITH_PROJECT", "mirsal")
        self.key = os.environ.get("LANGSMITH_API_KEY", "")
        self._q: queue.Queue = queue.Queue()
        self._t: threading.Thread | None = None
        self.sent = 0
        self.dropped = 0

    def _post(self, kind: str, payload: dict) -> None:
        if backend() != "langsmith" or not self.key:
            self.dropped += 1
            return
        body = json.dumps({"project": self.project, "kind": kind, **payload}).encode()
        req = urllib.request.Request(_endpoint() + "/runs", data=body, method="POST",
                                     headers={"content-type": "application/json",
                                              "x-api-key": self.key})
        try:
            urllib.request.urlopen(req, timeout=10).read()
            self.sent += 1
        except Exception:
            self.dropped += 1

    def _submit(self, kind: str, payload: dict) -> None:
        if self._t is None:
            self._t = threading.Thread(target=self._drain, daemon=True)
            self._t.start()
        self._q.put((kind, payload))

    def _drain(self) -> None:
        while True:
            kind, payload = self._q.get()
            try:
                self._post(kind, payload)
            finally:
                self._q.task_done()

    @contextmanager
    def span(self, name: str, inputs: dict | None = None, parent: str | None = None):
        """A child run per stage/model call. Yields the run id (None on the none backend)."""
        run_id = os.urandom(16).hex() if backend() == "langsmith" else None
        t0 = time.perf_counter()
        try:
            yield run_id
        finally:
            if run_id:
                self._submit("span", {"run_id": run_id, "parent": parent, "name": name,
                                     "inputs": inputs or {}, "ms": int((time.perf_counter() - t0) * 1000)})

    def feedback(self, run_id: str | None, key: str, score: int, comment: str = "") -> None:
        """Each gate decision is feedback on the run it judges (gate_plan/gate_still/…/vlm_still/vlm_anim)."""
        if run_id:
            self._submit("feedback", {"run_id": run_id, "key": key, "score": score, "comment": comment or ""})


def gate_feedback(tracer: Tracer, run_id: str | None, gate: str, decision: str, reason: str = "", vlm: bool = False) -> None:
    key = ("vlm_" if vlm else "gate_") + gate
    tracer.feedback(run_id, key, 1 if decision in ("APPROVE", "PASS") else 0, reason)
