"""The verifier: ONE catalogue of every check on the golden path (phase_01.md, "The verifier").

Python judges what is *correct*; humans (and from Phase 3 the VLM) judge what is *good*. A BLOCK failure is final: the
API refuses an APPROVE on it. A WARN is shown to the human at the gate. The verifier is deterministic (same bytes in,
same verdict out), never raises (a crash is a BLOCK `verifier_error`), never looks at meaning and never repairs pixels.

Every check is one function `fn(inp, cfg) -> Check`. Thresholds live in EngineConfig only. `run(stage, inp, cfg)` runs the
stage's checks in catalogue order. Checks may record metrics in `inp["metrics"]`; `run` adds the id of every failed WARN
to `metrics["warnings"]`. Pure: numpy / OpenCV only (the ffmpeg work stays in video.py and hands its results in).
"""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field

import cv2
import numpy as np

from .chroma import key_diff

VERIFY_VERSION = 1          # stored on every result: Phase 2 can tell which rule set judged an old sticker
BLOCK, WARN = "BLOCK", "WARN"


@dataclass
class Check:
    id: str                      # 'inside_slot'; also the reason string and the reviews.reason value
    stage: str                   # sheet | still | video_sheet | video | anim | pack
    severity: str                # BLOCK (final) | WARN (shown to the human)
    ok: bool
    value: object = None         # the measured metric
    limit: object = None         # the threshold it was compared with (from EngineConfig)
    detail: dict = field(default_factory=dict)   # e.g. {"frame": 41, "over_px": 6}
    note: str = ""               # one human line (what the console prints next to the check)
    reason: str | None = None    # reason string when it BLOCKs and differs from the id (blank_cell -> empty_subject)

    def to_dict(self) -> dict:
        # name/ok/detail keep the shape results have always had; the rest is what the gate UI shows
        return {"name": self.id, "ok": bool(self.ok), "detail": self.note, "severity": self.severity, "stage": self.stage,
                "value": _plain(self.value), "limit": _plain(self.limit), "data": _plain(self.detail)}


def _plain(v):
    """JSON-safe copy (numpy scalars and tuples become plain values)."""
    if isinstance(v, dict):
        return {str(k): _plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if isinstance(v, np.generic):
        return v.item()
    return v


@dataclass
class Report:
    """A view over list[Check]: the first failing BLOCK is the reason; WARN failures never fail a sticker."""
    items: list = field(default_factory=list)

    @property
    def checks(self) -> list:
        return [c.to_dict() for c in self.items]

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.items if c.severity == BLOCK)

    @property
    def first_failure(self):
        c = next((c for c in self.items if not c.ok and c.severity == BLOCK), None)
        return (c.reason or c.id) if c else None

    @property
    def warnings(self) -> list:
        return [c.id for c in self.items if not c.ok and c.severity == WARN]

    def get(self, check_id: str):
        return next((c for c in self.items if c.id == check_id), None)


def _c(stage, cid, severity, ok, value=None, limit=None, note="", reason=None, **detail) -> Check:
    return Check(cid, stage, severity, bool(ok), value, limit, detail, str(note), reason)


# ---------- catalogue plumbing ----------
CATALOGUE: dict[str, list] = {}        # stage -> [(id, severity, fn, gate)] in catalogue order


def check(stage: str, cid: str, severity: str, gate: bool = False):
    """Register a check. gate=True: when it fails (BLOCK) the stage stops there (later checks need what it guards)."""
    def deco(fn):
        CATALOGUE.setdefault(stage, []).append((cid, severity, fn, gate))
        return fn
    return deco


def run(stage: str, inp: dict, cfg) -> list[Check]:
    """Run every check of `stage` in catalogue order. Never raises: a crashing check is a BLOCK `verifier_error`."""
    out: list[Check] = []
    m = inp.setdefault("metrics", {})
    for cid, severity, fn, gate in CATALOGUE.get(stage, []):
        t0 = time.perf_counter()
        try:
            res = fn(inp, cfg)
        except Exception as e:                                     # pragma: no cover - defensive
            res = Check(cid, stage, BLOCK, False, None, None, {"error": str(e)[:200], "trace": traceback.format_exc()[-400:]},
                        f"verifier crashed: {e}", "verifier_error")
        res.detail.setdefault("ms", round((time.perf_counter() - t0) * 1000, 1))
        out.append(res)
        if not res.ok and res.severity == WARN:
            m.setdefault("warnings", []).append(res.id)
        if gate and not res.ok and res.severity == BLOCK:
            break
    inp["_checks"] = out
    return out


def report(stage: str, inp: dict, cfg) -> Report:
    return Report(run(stage, inp, cfg))


# ---------- helpers ----------
def _img(inp: dict) -> np.ndarray:
    """The rendered 512x512 sticker, rendered lazily so a blank cell never pays for it."""
    if "img" not in inp:
        inp["img"] = inp["render"]()
    return inp["img"]


# ================= still (one cell -> one sticker) =================
@check("still", "blank_cell", BLOCK, gate=True)
def blank_cell(inp, cfg):
    c = inp["cell"]
    ok = bool(c.bbox and c.fg_px >= cfg.min_foreground_px)
    return _c("still", "blank_cell", BLOCK, ok, c.fg_px, cfg.min_foreground_px, f"{c.fg_px}px < {cfg.min_foreground_px}", reason="empty_subject")


@check("still", "dimensions", BLOCK)
def dimensions(inp, cfg):
    img = _img(inp)
    return _c("still", "dimensions", BLOCK, img.shape == (cfg.size, cfg.size, 4), list(img.shape), [cfg.size, cfg.size, 4], img.shape)


@check("still", "transparent_corners", BLOCK)
def transparent_corners(inp, cfg):
    a, S = _img(inp)[..., 3], cfg.size
    return _c("still", "transparent_corners", BLOCK, all(a[y, x] == 0 for y in (0, S - 1) for x in (0, S - 1)))


@check("still", "foreground", BLOCK)
def foreground(inp, cfg):
    n = int((_img(inp)[..., 3] > 127).sum())
    return _c("still", "foreground", BLOCK, n >= cfg.min_foreground_px, n, cfg.min_foreground_px)


@check("still", "inside_cell", BLOCK)
def inside_cell(inp, cfg):
    c = inp["cell"]
    return _c("still", "inside_cell", BLOCK, c.edge_px <= cfg.edge_touch_px, c.edge_px, cfg.edge_touch_px, f"{c.edge_px}px on cell border")


def _edge_analysis(inp, cfg) -> dict:
    """Key colour left ON THE EDGE (between subject and outline) versus deep inside the subject (the subject's own colours).
    Measured on the real sheets: every pixel the old whole-subject rule failed on was interior, with 0 on the edge."""
    if "_spill" not in inp:
        c, img = inp["cell"], _img(inp)
        opaque = img[..., 3] > 127
        keyish = opaque & (key_diff(img[..., :3], cfg.chroma) > c.keyed.t / 4)
        dist = cv2.distanceTransform(opaque.astype(np.uint8), cv2.DIST_L2, 3)
        edge = keyish & (dist <= cfg.outline_px + cfg.despill_band_px + 3)
        spill, inner = int(edge.sum()), int((keyish & ~edge).sum())
        n = int(opaque.sum())
        inp["_spill"] = {"spill": spill, "n": n, "risk": round(inner / max(n, 1), 4)}
        inp["metrics"]["spill_px"], inp["metrics"]["chroma_risk"] = spill, inp["_spill"]["risk"]
    return inp["_spill"]


@check("still", "no_spill", BLOCK)
def no_spill(inp, cfg):
    e = _edge_analysis(inp, cfg)
    limit = max(20, 0.001 * e["n"])
    return _c("still", "no_spill", BLOCK, e["spill"] <= limit, e["spill"], limit, f"{e['spill']}px on the edge band")


@check("still", "chroma_risk", WARN)
def chroma_risk(inp, cfg):
    e = _edge_analysis(inp, cfg)     # a warning, not a block: the human judges it at G2; Phase 3 re-keys on blue
    return _c("still", "chroma_risk", WARN, e["risk"] <= cfg.chroma_risk_warn, e["risk"], cfg.chroma_risk_warn,
              f"{e['risk'] * 100:.1f}% of the subject is key-coloured")


@check("still", "static_file", BLOCK)
def static_file(inp, cfg):
    data, fmt = inp["encode"](_img(inp), cfg)
    inp["data"], inp["fmt"] = data, fmt
    m = inp["metrics"]
    m["kb"], m["format"] = round(len(data) / 1024, 1), fmt
    return _c("still", "static_file", BLOCK, len(data) <= cfg.static_max_bytes, m["kb"], cfg.static_max_bytes // 1024, f"{m['kb']}KB {fmt}")


# ================= anim (one encoded WEBM) =================
@check("anim", "size_budget", BLOCK)
def size_budget(inp, cfg):
    n = len(inp["data"])
    return _c("anim", "size_budget", BLOCK, n <= cfg.video_max_bytes, n // 1024, cfg.video_max_bytes // 1024, f"{n // 1024}KB @crf{inp['metrics']['crf']}")


@check("anim", "codec_vp9", BLOCK)
def codec_vp9(inp, cfg):
    return _c("anim", "codec_vp9", BLOCK, inp["info"]["codec"] == "vp9", inp["info"]["codec"], "vp9", inp["info"]["codec"])


@check("anim", "dimensions", BLOCK)
def anim_dimensions(inp, cfg):
    i = inp["info"]
    return _c("anim", "dimensions", BLOCK, (i["width"], i["height"]) == (cfg.size, cfg.size), f"{i['width']}x{i['height']}", f"{cfg.size}x{cfg.size}",
              f"{i['width']}x{i['height']}")


@check("anim", "fps", BLOCK)
def anim_fps(inp, cfg):
    f = inp["info"]["fps"]
    return _c("anim", "fps", BLOCK, 0 < f <= cfg.video_max_fps + 0.01, f, cfg.video_max_fps, f)


@check("anim", "duration", BLOCK)
def anim_duration(inp, cfg):
    d = round(inp["info"]["duration"], 3)
    return _c("anim", "duration", BLOCK, inp["info"]["duration"] <= cfg.video_max_seconds + 0.02, d, cfg.video_max_seconds, d)


@check("anim", "no_audio", BLOCK)
def no_audio(inp, cfg):
    return _c("anim", "no_audio", BLOCK, not inp["info"]["audio"])


@check("anim", "alpha_mode_tag", BLOCK)
def alpha_mode_tag(inp, cfg):
    return _c("anim", "alpha_mode_tag", BLOCK, inp["info_native"]["alpha_mode"] or inp["info"]["alpha_mode"])


@check("anim", "alpha_decoded", BLOCK)
def alpha_decoded(inp, cfg):
    al = inp["alpha"]
    ok = len(al) > 0 and al[..., 3].min() < 8 and al[..., 3].max() > 247
    return _c("anim", "alpha_decoded", BLOCK, ok)


@check("anim", "loop_seam", BLOCK)
def loop_seam_check(inp, cfg):
    m = inp["metrics"]
    return _c("anim", "loop_seam", BLOCK, m["loop_seam"] <= m["loop_limit"], m["loop_seam"], m["loop_limit"], f"{m['loop_seam']} <= {m['loop_limit']}")
