"""Tracing (Phase 3A, second half): every stage, model call and gate decision as a LangSmith run, never the media.

Two backends, `MIRSAL_TRACE=none|langsmith`. `none` (default) records nothing and makes zero network calls. `langsmith`
queues JSON on a background thread and posts it in LangSmith's documented REST shape (`POST /runs`, `PATCH /runs/{id}`,
`POST /feedback`); a failed post is dropped and counted, tracing never blocks or fails the pipeline.

Mapping: one root run per generation (`out/G###/trace.json` keeps its id so later requests parent under it); one child run
per pipeline event (`pipeline.emit` is the single event sink, so every stage and every gate shows up) and per model call
(`model_calls.append`); each gate decision (an event with actor + decision) is feedback on the run it judges, keys
`gate_<plan|still|video_sheet|anim|pack>` for humans and Python, `vlm_<gate>` for the judge, score 1 for APPROVE/PASS and
0 for REJECT/BLOCK, comment = the reason.

What leaves the machine: ids, slot JSON, prompts, metrics, decisions. Never image or video bytes (bytes values are replaced by
their length) and never a file path outside the generation (`safe()` replaces an absolute path in any text with `<path>/name`). The project is `MIRSAL_LANGSMITH_PROJECT` (default `mirsal`);
LANGSMITH_PROJECT is deliberately ignored, because mirsal/.env may hold another project's settings.
Not yet run against a live LangSmith project: the shapes follow its REST documentation and are tested against a fake server."""
from __future__ import annotations

import json
import os
import queue
import re
import threading
import time
import urllib.request
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
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


def project_name() -> str:
    return os.environ.get("MIRSAL_LANGSMITH_PROJECT", "mirsal")


def status() -> dict:
    b = backend()
    return {"backend": b, "project": project_name() if b == "langsmith" else None,
            "reachable": _reachable() if b == "langsmith" else None}


def _endpoint() -> str:
    return os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com").rstrip("/")


def _tls():
    """The tolerant TLS context (a malformed Windows certificate-store entry must not silently drop every trace)."""
    from ..services.telegram import _ssl_context
    return _ssl_context()


def _reachable() -> bool:
    try:
        urllib.request.urlopen(urllib.request.Request(_endpoint() + "/info", method="GET"), timeout=3, context=_tls())
        return True
    except Exception:
        return False


def _iso(t: float) -> str:
    return datetime.fromtimestamp(t, tz=timezone.utc).isoformat(timespec="microseconds")


def _dotted(t: float, run_id: str) -> str:
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + run_id


_WIN_PATH = re.compile(r"(?<!\w)[A-Za-z]:[\\/](?:[^\\/\s'\"<>|:*?]+[\\/])*([^\\/\s'\"<>|:*?]*)")
_POSIX_PATH = re.compile(r"(?<![\w.:/])/(?:Users|home|tmp|var|private|mnt|opt|root|Volumes|srv)/(?:[^/\s'\"<>|]+/)*([^/\s'\"<>|]*)")


def scrub_paths(text: str) -> str:
    """An absolute file path in free text (an exception message, a log line) becomes `<path>/name`: where a machine keeps its files never leaves it,
    the file name stays so the message is still readable. Relative paths and URL paths are left alone."""
    return _POSIX_PATH.sub(r"<path>/\1", _WIN_PATH.sub(r"<path>/\1", text))


def safe(v, depth: int = 0):
    """JSON-safe copy for a payload: bytes become their length, absolute paths their file name, long strings are cut, depth is bounded."""
    if isinstance(v, (bytes, bytearray)):
        return f"<{len(v)} bytes>"
    if depth > 4:
        return "..."
    if isinstance(v, dict):
        return {str(k): safe(x, depth + 1) for k, x in list(v.items())[:60]}
    if isinstance(v, (list, tuple)):
        return [safe(x, depth + 1) for x in list(v)[:60]]
    if isinstance(v, str):
        v = scrub_paths(v)
        return v if len(v) <= 4000 else v[:4000] + "..."
    if isinstance(v, (int, float, bool)) or v is None:
        return v
    return scrub_paths(str(v))[:500]


class Ref(dict):
    """A run's identity: {id, trace_id, dotted_order}. Children are parented with it."""

    @property
    def id(self) -> str:
        return self["id"]


class Tracer:
    def __init__(self, project: str | None = None):
        _load_dotenv()
        self.project = project or project_name()
        self.key = os.environ.get("LANGSMITH_API_KEY", "")
        self._q: queue.Queue = queue.Queue()
        self._t: threading.Thread | None = None
        self.sent = 0
        self.dropped = 0
        self.last_error = ""           # why the last post was dropped (never contains the key)

    # ---- transport ------------------------------------------------------------------------------
    def _post(self, method: str, path: str, payload: dict) -> None:
        if backend() != "langsmith" or not self.key:
            self.dropped += 1
            return
        req = urllib.request.Request(_endpoint() + path, data=json.dumps(payload).encode(), method=method,
                                     headers={"content-type": "application/json", "x-api-key": self.key})
        try:
            urllib.request.urlopen(req, timeout=10, context=_tls()).read()
            self.sent += 1
        except Exception as e:
            self.dropped += 1
            body = ""
            try:
                body = e.read()[:300].decode("utf-8", "replace")      # an HTTPError carries the service's reason
            except Exception:
                pass
            self.last_error = f"{method} {path}: {type(e).__name__} {getattr(e, 'code', '')} {body}".strip()

    def _submit(self, method: str, path: str, payload: dict) -> None:
        if self._t is None:
            self._t = threading.Thread(target=self._drain, daemon=True)
            self._t.start()
        self._q.put((method, path, payload))

    def _drain(self) -> None:
        while True:
            method, path, payload = self._q.get()
            try:
                before = self.sent
                self._post(method, path, payload)
                # LangSmith accepts a POST /runs asynchronously: a PATCH or a feedback that arrives before the run is
                # ingested is refused once. Retry those in this background thread (never in the pipeline), twice.
                for _ in range(2):
                    if self.sent > before or not (method == "PATCH" or path == "/feedback") or backend() != "langsmith":
                        break
                    time.sleep(1.0)
                    self.dropped -= 1
                    self._post(method, path, payload)
            finally:
                self._q.task_done()

    def flush(self, timeout: float = 5.0) -> None:
        end = time.time() + timeout
        while self._q.unfinished_tasks and time.time() < end:
            time.sleep(0.02)

    # ---- runs -----------------------------------------------------------------------------------
    def run(self, name: str, inputs: dict | None = None, parent: dict | None = None, run_type: str = "chain",
            start: float | None = None, end: float | None = None, outputs: dict | None = None,
            error: str | None = None, metadata: dict | None = None, open_run: bool = False) -> Ref | None:
        """Create one run (finished when `end` is given or `open_run` is False). Returns its Ref, or None on the `none` backend."""
        if backend() != "langsmith":
            return None
        t0 = start if start is not None else time.time()
        rid = str(uuid.uuid4())
        own = _dotted(t0, rid)
        ref = Ref(id=rid, trace_id=(parent or {}).get("trace_id") or rid,
                  dotted_order=((parent["dotted_order"] + ".") if parent else "") + own)
        body = {"id": rid, "trace_id": ref["trace_id"], "dotted_order": ref["dotted_order"],
                "parent_run_id": parent["id"] if parent else None, "name": name, "run_type": run_type,
                "start_time": _iso(t0), "inputs": safe(inputs or {}), "session_name": self.project,
                "extra": {"metadata": safe(metadata or {})}}
        if not open_run:
            body.update(end_time=_iso(end if end is not None else time.time()), outputs=safe(outputs or {}), error=error)
        self._submit("POST", "/runs", body)
        return ref

    def end(self, ref: dict | None, outputs: dict | None = None, error: str | None = None) -> None:
        if ref:
            self._submit("PATCH", f"/runs/{ref['id']}", {"end_time": _iso(time.time()), "outputs": safe(outputs or {}),
                                                         "error": error})

    @contextmanager
    def span(self, name: str, inputs: dict | None = None, parent: dict | None = None, run_type: str = "chain"):
        """A child run around a block. Yields its Ref (None on the none backend)."""
        ref = self.run(name, inputs, parent, run_type, open_run=True)
        err = None
        try:
            yield ref
        except Exception as e:
            err = f"{type(e).__name__}: {e}"[:500]
            raise
        finally:
            self.end(ref, error=err)

    def feedback(self, ref, key: str, score: int, comment: str = "") -> None:
        """Each gate decision is feedback on the run it judges."""
        rid = ref["id"] if isinstance(ref, dict) else ref
        if rid:
            self._submit("POST", "/feedback", {"id": str(uuid.uuid4()), "run_id": rid, "key": key,
                                               "score": score, "comment": comment or ""})


_tracer: Tracer | None = None
_lock = threading.Lock()


def tracer() -> Tracer:
    global _tracer
    with _lock:
        if _tracer is None:
            _tracer = Tracer()
        return _tracer


def reset() -> None:
    """Forget the process tracer and the cached roots (tests change the environment between cases)."""
    global _tracer
    with _lock:
        _tracer = None
        _roots.clear()


def gate_feedback(tracer: Tracer, run_id, gate: str, decision: str, reason: str = "", vlm: bool = False) -> None:
    key = ("vlm_" if vlm else "gate_") + gate
    tracer.feedback(run_id, key, 1 if decision in ("APPROVE", "PASS") else 0, reason)


# ---- the pipeline hooks (called from pipeline.emit and model_calls.append; never raise) ---------------------------

_roots: dict = {}
STAGE_GATE = {"sheet": "still", "sliced": "still", "still": "still", "stills_reviewed": "still", "plan_reviewed": "plan",
              "video_sheet": "video_sheet", "video_sheet_built": "video_sheet", "video_sheet_reviewed": "video_sheet",
              "video_returned": "video_sheet", "video_flag": "video_sheet", "video": "anim", "anim": "anim",
              "anim_reviewed": "anim", "pack": "pack", "pack_final": "pack"}


def generation_run(out, gid: int, name: str | None = None) -> Ref | None:
    """The root run of one generation, created on first use and remembered in out/G###/trace.json."""
    if backend() != "langsmith":
        return None
    f = Path(out) / f"G{gid:03d}" / "trace.json"
    key = (str(Path(out).resolve()), gid, project_name())
    with _lock:
        if key in _roots:
            return _roots[key]
    ref = None
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("project") == project_name() and d.get("run"):
            ref = Ref(d["run"])
    except (OSError, ValueError):
        ref = None
    if ref is None:
        ref = tracer().run(name or f"generation G{gid:03d}", {"generation": f"G{gid:03d}"}, open_run=True)
        if ref is not None:
            try:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(json.dumps({"project": project_name(), "run": dict(ref)}), encoding="utf-8")
            except OSError:
                pass
    with _lock:
        _roots[key] = ref
    return ref


def emit_event(out, gid: int, ev: dict) -> str | None:
    """One pipeline event -> one finished child run of its generation; a decision also becomes gate feedback. Returns the run id."""
    try:
        if backend() != "langsmith":
            return None
        root = generation_run(out, gid)
        now = ev.get("ts") or time.time()
        ms = int(ev.get("ms") or 0)
        t = tracer()
        ref = t.run(str(ev.get("stage") or "event"), {"status": ev.get("status"), "detail": ev.get("detail")}, root,
                    start=now - ms / 1000.0, end=now, outputs={"status": ev.get("status"), "ms": ms},
                    error=str(ev.get("detail"))[:500] if ev.get("status") == "error" else None,
                    metadata={"actor": ev.get("actor"), "decision": ev.get("decision")})
        if ref and ev.get("actor") and ev.get("decision"):
            d = ev.get("detail") if isinstance(ev.get("detail"), dict) else {}
            gate = d.get("gate") or STAGE_GATE.get(str(ev.get("stage")))
            if gate:
                gate_feedback(t, ref, gate, str(ev["decision"]), str(d.get("note") or d.get("reason") or ""),
                              vlm=ev.get("actor") == "vlm")
        return ref.id if ref else None
    except Exception:
        return None


def backfill(conn, out, since: str | None = None) -> dict:
    """Replay what Postgres holds without a trace_run_id: every event becomes a child run of its generation's root and
    every review becomes gate feedback on that root. Idempotent: a row is only replayed while its trace_run_id is NULL.
    Needs MIRSAL_TRACE=langsmith (otherwise nothing is sent and nothing is marked)."""
    if backend() != "langsmith":
        return {"events": 0, "reviews": 0, "note": "MIRSAL_TRACE is not langsmith: nothing sent"}
    t = tracer()
    n_ev = n_rv = 0
    flt, args = ("AND ts >= %s::timestamptz", [since]) if since else ("", [])

    def gnum(g: str) -> int | None:
        g = str(g or "")
        return int(g[1:]) if g[:1].upper() == "G" and g[1:].isdigit() else None

    with conn.cursor() as cur:
        cur.execute(f"SELECT id, generation_id, ts, stage, status, ms, detail FROM generation_events "
                    f"WHERE trace_run_id IS NULL {flt} ORDER BY generation_id, ts", args)
        events = cur.fetchall()
        cur.execute(f"SELECT id, generation_id, gate, actor, decision, reason FROM reviews "
                    f"WHERE trace_run_id IS NULL {flt} ORDER BY generation_id, ts", args)
        reviews = cur.fetchall()
        for eid, gen, ts, stage, status_, ms, detail in events:
            n = gnum(gen)
            if n is None:
                continue
            root = generation_run(out, n)
            end = ts.timestamp()
            ref = t.run(stage, {"status": status_, "detail": detail}, root, start=end - (ms or 0) / 1000.0, end=end,
                        outputs={"status": status_, "ms": ms or 0})
            if ref:
                cur.execute("UPDATE generation_events SET trace_run_id = %s WHERE id = %s", (ref.id, eid))
                n_ev += 1
        for rid, gen, gate, actor, decision, reason in reviews:
            n = gnum(gen)
            root = generation_run(out, n) if n is not None else None
            if root:
                gate_feedback(t, root, gate, decision, reason or "", vlm=actor == "vlm")
                cur.execute("UPDATE reviews SET trace_run_id = %s WHERE id = %s", (root.id, rid))
                n_rv += 1
    conn.commit()
    t.flush(30)
    return {"events": n_ev, "reviews": n_rv}


def model_call(out, row: dict) -> str | None:
    """One ledger line -> one run, under its generation's root when it names one. Returns the run id."""
    try:
        if backend() != "langsmith":
            return None
        parent = None
        g = str(row.get("generation_id") or "")
        if g[:1].upper() == "G" and g[1:].isdigit() and out is not None:
            parent = generation_run(out, int(g[1:]))
        now = row.get("ts") or time.time()
        ms = int(row.get("latency_ms") or 0)
        kind = str(row.get("kind") or "call")
        ref = tracer().run(kind, {"model": row.get("model"), "provider": row.get("provider"),
                                  "prompt_version": row.get("prompt_version"), "seed": row.get("seed")}, parent,
                           "llm" if kind.startswith(("LLM", "VLM")) else "tool", start=now - ms / 1000.0, end=now,
                           outputs={"status": row.get("status"), "cost": row.get("cost"), "latency_ms": ms,
                                    "tokens_in": row.get("tokens_in"), "tokens_out": row.get("tokens_out")},
                           error=row.get("error"))
        return ref.id if ref else None
    except Exception:
        return None
