"""Part A: rows x cols sheet (3x3, 2x2, 1x1) -> keyed cells -> 512x512 stickers. Pure: arrays in, results out, never raises per cell."""
from __future__ import annotations

import io
from dataclasses import dataclass, field, replace

import cv2
import numpy as np
from PIL import Image

from . import verify
from .chroma import Keyed, border_mask, key_diff, key_image
from .render import bbox_of, fit_scale, render_sticker
from .verify import Report


@dataclass
class CellKey:
    index: int
    rect: tuple            # x, y, w, h in the sheet
    keyed: Keyed
    bbox: tuple | None
    fg_px: int
    edge_px: int
    raw: np.ndarray | None = None   # the untouched RGB cell (a view), kept so a failed cell can be keyed again


@dataclass
class StickerResult:
    index: int
    status: str            # READY | FAILED
    reason: str | None = None
    report: Report = field(default_factory=Report)
    metrics: dict = field(default_factory=dict)
    data: bytes | None = None
    fmt: str = "png"
    img: np.ndarray | None = None   # the rendered 512x512 RGBA (not serialised; the video sheet builder reuses the pipeline's keyed cells)


def _cellkey(index: int, rect: tuple, raw: np.ndarray, k: Keyed) -> CellKey:
    alpha = k.rgba[..., 3]
    ring = np.zeros(alpha.shape, bool)
    ring[:2] = True; ring[-2:] = True; ring[:, :2] = True; ring[:, -2:] = True
    return CellKey(index, rect, k, bbox_of(alpha), int((alpha > 127).sum()), int((alpha[ring] > 127).sum()), raw)


def key_sheet(sheet_rgb: np.ndarray, cfg, rects: list | None = None) -> list[CellKey]:
    """rects = row-major (x, y, w, h) from grid.split_grid(); None = equal thirds (old behaviour)."""
    if rects is None:
        h, w = sheet_rgb.shape[:2]
        rects = [(c * (w // 3), r * (h // 3), w // 3, h // 3) for r in range(3) for c in range(3)]
    out = []
    for i, (x, y, cw, ch) in enumerate(rects):
        raw = sheet_rgb[y:y + ch, x:x + cw]
        out.append(_cellkey(i + 1, (int(x), int(y), int(cw), int(ch)), raw, key_image(raw, cfg)))
    return out


def stitch_keyed(cells: list[CellKey], shape) -> np.ndarray:
    """Whole-sheet RGBA of the keyed cells (for the UI's 'keyed' stage)."""
    canvas = np.zeros((shape[0], shape[1], 4), np.uint8)
    for c in cells:
        x, y, w, h = c.rect
        canvas[y:y + h, x:x + w] = c.keyed.rgba
    return canvas


def encode_static(rgba: np.ndarray, cfg):
    ok, buf = cv2.imencode(".png", cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    data = buf.tobytes()
    if len(data) <= cfg.static_max_bytes:
        return data, "png"
    bio = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(bio, "WEBP", lossless=True, quality=100, method=6)
    return bio.getvalue(), "webp"


def _make(c: CellKey, cfg, pack: float) -> StickerResult:
    S = cfg.size
    m = {"cell": list(c.rect), "bg": c.keyed.bg, "threshold": round(c.keyed.t, 1), "fg_px": c.fg_px, "bbox": list(c.bbox) if c.bbox else None}

    def render():
        bw, bh = c.bbox[2] - c.bbox[0], c.bbox[3] - c.bbox[1]
        s = min(pack, cfg.max_fit * S / max(bw, bh))
        m["scale"], m["scale_mode"] = round(s, 4), ("pack" if s >= pack - 1e-9 else "clamped")
        return render_sticker(c.keyed.rgba, c.bbox, s, cfg)

    inp = {"cell": c, "metrics": m, "render": render, "encode": encode_static}
    rep = Report(verify.run("still", inp, cfg))
    if rep.ok:
        return StickerResult(c.index, "READY", None, rep, m, inp["data"], inp["fmt"], inp.get("img"))
    return StickerResult(c.index, "FAILED", rep.first_failure, rep, m)


def _diagnose(c: CellKey, cfg) -> dict:
    """Step 1 of the recovery branch: find out WHY it failed before touching any parameter."""
    d = key_diff(c.raw, cfg.chroma)
    ring = border_mask(c.raw.shape[0], c.raw.shape[1], cfg.border_px)
    return {"ring_polluted": round(float((d[ring] < c.keyed.t / 2).mean()), 3), "bg": c.keyed.bg,
            "threshold": round(c.keyed.t, 1), "fg_px": c.fg_px, "edge_px": c.edge_px}


def _ladder(reason: str, c: CellKey, gbg, gt) -> list:
    """Re-key steps per failure reason: (name, background, threshold, despill band). inside_cell cannot be fixed by keying."""
    t = c.keyed.t
    if reason == "inside_cell":
        return []
    if reason == "empty_subject":
        return [("sheet-wide background", gbg, gt, None), ("sheet-wide background, threshold x0.6", gbg, gt * 0.6, None)]
    if reason == "no_spill":
        return [("threshold x0.75, despill 6px", c.keyed.bg, t * 0.75, 6), ("threshold x0.6, despill 10px", c.keyed.bg, t * 0.6, 10)]
    return [("sheet-wide background", gbg, gt, None)]


def _recover(c: CellKey, first: StickerResult, cfg, pack: float, gbg, gt) -> StickerResult:
    """Failed cell -> dissect -> key again (bounded ladder) -> finally rule it out. Every step is logged in metrics.attempts."""
    attempts = [{"name": "default", "ok": False, "reason": first.reason}]
    attempts.append({"name": "dissect", "ok": None, "note": _diagnose(c, cfg)})
    best = first
    steps = _ladder(first.reason, c, gbg, gt)
    if not steps:
        attempts[-1]["note"]["verdict"] = "the subject crosses the cell border; keying cannot fix that (regenerate the sheet or adjust the grid)"
    for name, bg, t, band in steps:
        cfg2 = replace(cfg, despill_band_px=band or cfg.despill_band_px)
        c2 = _cellkey(c.index, c.rect, c.raw, key_image(c.raw, cfg2, (bg, float(t))))
        r = _make(c2, cfg2, pack)
        attempts.append({"name": name, "ok": r.status == "READY", "reason": r.reason})
        if r.status == "READY":
            r.metrics["recovered_by"] = name
            best = r
            break
    if best.status != "READY":
        best.metrics["ruled_out"] = True
    best.metrics["attempts"] = attempts
    return best


def slice_cells(cells: list[CellKey], cfg) -> list[StickerResult]:
    valid = [c for c in cells if c.bbox and c.fg_px >= cfg.min_foreground_px]
    fits = [fit_scale(c.bbox, cfg) for c in valid]
    pack = float(np.median(fits)) if fits else 1.0     # ONE pack-wide scale: no size jumping between poses
    gbg = [int(v) for v in np.median([c.keyed.bg for c in cells], axis=0)]
    gt = float(np.median([c.keyed.t for c in cells]))
    results = []
    for c in cells:
        r = _make(c, cfg, pack)
        if r.status != "READY" and c.raw is not None:
            r = _recover(c, r, cfg, pack, gbg, gt)
        results.append(r)
    return results


def process_sheet(sheet_rgb: np.ndarray, cfg, rects: list | None = None) -> list[StickerResult]:
    return slice_cells(key_sheet(sheet_rgb, cfg, rects), cfg)
