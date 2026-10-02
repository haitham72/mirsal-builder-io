"""Checks for a particle-effect clip (`engine/particles.py`): is it empty at both ends, does it show a burst, does it stay in its cell, does it move.

The verdict is ONLY "PASS" or "WARN", never "BLOCK". This is the owner's standing rule: Python must not hard-block a result he can look at;
he must always be able to use it anyway. A WARN is a line shown next to the preview, not a gate.

What is NOT here: the technical limits of a Telegram video sticker (WEBM/VP9 + alpha, 512x512, 30 fps, 3 s, 256 KB). The existing verifier
(`engine/verify.py`) enforces them on the encoded file; these checks only judge the pixels of the effect itself.

Pure numpy; deterministic; no I/O. Every threshold is a module constant so the UI and the tests read the same numbers.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

ALPHA_ON = 12            # alpha at or above this counts as "something is drawn" (below it is VP9 haze: the engine's clip_alpha_floor)
EDGE_FRAMES = 3          # the first and the last 3 frames must be empty
EMPTY_MAX = 0.003        # empty = at most 0.3% of the canvas covered
BURST_MIN = 0.015        # the peak covers at least 1.5% of the canvas ...
BURST_FRAMES = 20        # ... and something is visible (coverage above EMPTY_MAX) in at least 20 frames
OUTSIDE_MAX = 0.002      # at most 0.2% of a frame's opaque pixels may lie outside the cell
MOTION_COVERAGE = 0.0005 # motion: the coverage changes by at least 0.05% of the canvas per frame on average (between frames that show something) ...
MOTION_PATH = 0.01       # ... or the alpha centroid travels at least 1% of the canvas side in total
PASS, WARN = "PASS", "WARN"


@dataclass(frozen=True)
class Check:
    id: str                       # effect_empty_start ...
    verdict: str                  # "PASS" or "WARN", never "BLOCK"
    detail: str                   # one human line
    value: object = None          # the measured number
    limit: object = None          # what it was compared with
    data: dict = field(default_factory=dict)     # e.g. {"frame": 41}

    @property
    def ok(self) -> bool:
        return self.verdict == PASS

    def to_dict(self) -> dict:
        return {"id": self.id, "verdict": self.verdict, "detail": self.detail, "value": self.value, "limit": self.limit, "data": dict(self.data)}


def _alpha(frames) -> np.ndarray:
    if not isinstance(frames, np.ndarray) or frames.ndim != 4 or frames.shape[3] != 4 or len(frames) == 0:
        raise ValueError("frames must be a non-empty array of shape (N, H, W, 4)")
    return frames[..., 3]


def coverage_curve(frames: np.ndarray, alpha_min: int = ALPHA_ON) -> list:
    """Per frame, the share of the canvas whose alpha is at least `alpha_min` (0..1)."""
    a = _alpha(frames)
    return [float(x) for x in (a >= alpha_min).mean(axis=(1, 2))]


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def _edge(cov: list, frames_idx: list, check_id: str, where: str) -> Check:
    worst = max(frames_idx, key=lambda i: cov[i])
    v = cov[worst]
    if v <= EMPTY_MAX:
        return Check(check_id, PASS, f"the {where} {EDGE_FRAMES} frames are empty (at most {_pct(v)} covered)", v, EMPTY_MAX)
    return Check(check_id, WARN, f"the {where} {EDGE_FRAMES} frames are not empty: frame {worst} covers {_pct(v)} (limit {_pct(EMPTY_MAX)}); "
                 "the effect should start from nothing and end with nothing", v, EMPTY_MAX, {"frame": worst})


def run(frames: np.ndarray, *, cell_bounds: tuple | None = None) -> list:
    """The effect checks on RGBA frames `(N, H, W, 4)`, as a list of `Check` (verdict PASS or WARN only):
      effect_empty_start   the first 3 frames cover <= 0.3% of the canvas
      effect_empty_end     the last 3 frames cover <= 0.3% of the canvas
      effect_has_burst     the peak covers >= 1.5% of the canvas and something is visible in >= 20 frames ("visible" = above the 0.3% empty line)
      effect_inside_cell   only when `cell_bounds=(x0, y0, x1, y1)` (pixels, x1/y1 exclusive) is given: at most 0.2% of any frame's opaque pixels outside it
      effect_not_a_still   the alpha coverage or the alpha centroid changes from frame to frame (motion is present)
    Malformed frames raise ValueError (a caller bug); everything about the clip itself is a verdict."""
    a = _alpha(frames)
    n, h, w = a.shape
    on = a >= ALPHA_ON
    count = on.sum(axis=(1, 2))
    cov = (count / float(h * w)).tolist()
    edge = min(EDGE_FRAMES, n)
    out = [_edge(cov, list(range(edge)), "effect_empty_start", "first"),
           _edge(cov, list(range(n - edge, n)), "effect_empty_end", "last")]

    peak = max(cov)
    visible = sum(1 for c in cov if c > EMPTY_MAX)
    if peak >= BURST_MIN and visible >= BURST_FRAMES:
        out.append(Check("effect_has_burst", PASS, f"peak {_pct(peak)} of the canvas, visible in {visible} frames", peak, BURST_MIN,
                         {"visible_frames": visible, "peak_frame": int(np.argmax(cov))}))
    else:
        why = f"the peak covers only {_pct(peak)} (needs {_pct(BURST_MIN)})" if peak < BURST_MIN else f"it is visible in only {visible} frames (needs {BURST_FRAMES})"
        out.append(Check("effect_has_burst", WARN, f"no clear burst: {why}", peak, BURST_MIN,
                         {"visible_frames": visible, "peak_frame": int(np.argmax(cov))}))

    if cell_bounds is not None:
        x0, y0, x1, y1 = (int(v) for v in cell_bounds)
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
        if x1 <= x0 or y1 <= y0:
            raise ValueError("cell_bounds must be (x0, y0, x1, y1) with x1 > x0 and y1 > y0, inside the canvas")
        inside = on[:, y0:y1, x0:x1].sum(axis=(1, 2))
        frac = np.where(count > 0, (count - inside) / np.maximum(count, 1), 0.0)
        worst = int(np.argmax(frac))
        v = float(frac[worst])
        if v <= OUTSIDE_MAX:
            out.append(Check("effect_inside_cell", PASS, f"inside the cell in every frame (worst {_pct(v)} outside)", v, OUTSIDE_MAX, {"frame": worst}))
        else:
            out.append(Check("effect_inside_cell", WARN, f"frame {worst} has {_pct(v)} of its opaque pixels outside the cell (limit {_pct(OUTSIDE_MAX)})",
                             v, OUTSIDE_MAX, {"frame": worst, "outside_px": int(count[worst] - inside[worst])}))

    # Motion is judged between neighbouring frames that both show something: an effect appearing from nothing is not motion, a still is.
    held = np.flatnonzero((count[:-1] > 0) & (count[1:] > 0))
    change = float(np.mean([abs(cov[i + 1] - cov[i]) for i in held])) if len(held) else 0.0
    path = 0.0
    if len(held):
        gx, gy = np.arange(w, dtype=np.float64), np.arange(h, dtype=np.float64)

        def centre(i):
            wgt = np.where(on[i], a[i], 0)
            col, row = wgt.sum(axis=0, dtype=np.float64), wgt.sum(axis=1, dtype=np.float64)
            tot = col.sum()
            return (col * gx).sum() / tot / w, (row * gy).sum() / tot / h
        cache = {}
        for i in held:
            for j in (i, i + 1):
                if j not in cache:
                    cache[j] = centre(j)
            path += float(np.hypot(cache[i + 1][0] - cache[i][0], cache[i + 1][1] - cache[i][1]))
    msg = f"coverage changes {_pct(change)} per frame, the centroid travels {path * 100:.1f}% of the canvas"
    data = {"coverage_change": change, "centroid_path": path}
    if change >= MOTION_COVERAGE or path >= MOTION_PATH:
        out.append(Check("effect_not_a_still", PASS, "it moves: " + msg, change, MOTION_COVERAGE, data))
    else:
        out.append(Check("effect_not_a_still", WARN, "it looks like a still: " + msg, change, MOTION_COVERAGE, data))
    return out
