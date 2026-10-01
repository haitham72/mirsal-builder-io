"""Scale + white outline + report, shared by stills and video frames."""
from __future__ import annotations

import cv2
import numpy as np

from .chroma import despill
from .verify import Report  # noqa: F401  (re-exported: Report moved to verify.py)


def bbox_of(alpha_u8: np.ndarray, floor: int = 25):
    ys, xs = np.where(alpha_u8 > floor)
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def fit_scale(bbox, cfg) -> float:
    x0, y0, x1, y1 = bbox
    return cfg.fit * cfg.size / max(x1 - x0, y1 - y0, 1)


def apply_edge(rgb: np.ndarray, alpha: np.ndarray, outline_px: int, erode_px: int) -> np.ndarray:
    """Trim N px of key fringe, then draw the white die-cut ring outside the trimmed edge.

    rgb: float32 HxWx3, straight (un-premultiplied) colour. alpha: float32 HxW, 0..1.
    Returns uint8 HxWx4. The stored RGB is exact for its alpha: a viewer renders
    rgb*out_a + bg*(1-out_a) with no second application (the old code composited the
    subject over white *and* kept alpha, washing the edge out twice)."""
    A = np.clip(alpha, 0, 1)
    if erode_px > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * erode_px + 1, 2 * erode_px + 1))
        A = cv2.erode(A, k)
    if outline_px > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * outline_px + 1, 2 * outline_px + 1))
        ad = cv2.GaussianBlur(cv2.dilate(A, k), (0, 0), 1.0)
        out_a = np.clip(np.maximum(ad, A), 0, 1)
    else:
        out_a = A
    denom = np.maximum(out_a, 1e-4)
    rgb = (rgb * A[..., None] + 255.0 * (out_a - A)[..., None]) / denom[..., None]
    return np.clip(np.dstack([rgb, out_a * 255.0]) + 0.5, 0, 255).astype(np.uint8)


def render_sticker(rgba: np.ndarray, bbox, scale: float, cfg, outline_px: int | None = None, erode_px: int | None = None) -> np.ndarray:
    """Trim to bbox -> premultiply -> resize -> un-premultiply -> centre on SxS -> edge finish. Never stretches."""
    r = cfg.outline_px if outline_px is None else outline_px
    e = cfg.erode_px if erode_px is None else erode_px
    x0, y0, x1, y1 = bbox
    crop = rgba[y0:y1, x0:x1].astype(np.float32)
    a = crop[..., 3:4] / 255.0
    pm = np.concatenate([crop[..., :3] * a, a], axis=-1)
    nw, nh = max(1, int(round((x1 - x0) * scale))), max(1, int(round((y1 - y0) * scale)))
    pm = cv2.resize(pm, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    S = cfg.size
    canvas = np.zeros((S, S, 4), np.float32)
    ox, oy = (S - nw) // 2, (S - nh) // 2
    sx, sy, dx, dy = max(0, -ox), max(0, -oy), max(0, ox), max(0, oy)
    w, h = min(nw - sx, S - dx), min(nh - sy, S - dy)
    canvas[dy:dy + h, dx:dx + w] = pm[sy:sy + h, sx:sx + w]
    A = np.clip(canvas[..., 3], 0, 1)
    rgb = np.where(A[..., None] > 1e-4, canvas[..., :3] / np.maximum(A[..., None], 1e-4), 0)
    rgb = despill(np.clip(rgb + 0.5, 0, 255).astype(np.uint8), A, cfg.chroma, cfg.despill_band_px).astype(np.float32)
    return apply_edge(rgb, A, r, e)
