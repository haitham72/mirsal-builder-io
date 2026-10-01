"""Deterministic synthetic fixtures (noisy gradient green background, never a flat #00FF00)."""
import subprocess
from pathlib import Path

import cv2
import numpy as np

from mirsal.engine import ffmpeg as ff

YELLOW, RED = (250, 220, 20), (220, 40, 40)


def bg(size, seed, chroma="green"):
    rng = np.random.default_rng(seed)
    key = 225 + np.linspace(0, 25, size)[None, :] + rng.normal(0, 3, (size, size))
    other = 20 + rng.normal(0, 3, (size, size))
    img = np.stack([other, key, other] if chroma == "green" else [other, other, key], -1)
    return np.clip(img, 0, 255).astype(np.uint8)


def cell_art(i, size, seed, chroma="green", subj=YELLOW, t=0):
    """Return one cell. i in 1..9 (see make_sheet for what each is)."""
    c = bg(size, seed + i, chroma).copy()
    m, cx, cy = size // 2, size // 2, size // 2 - 10
    if i == 1:
        cv2.circle(c, (cx, cy), 50, subj, -1, cv2.LINE_AA)
    elif i == 2:   # thin 2px outline
        cv2.circle(c, (cx, cy), 55, RED, 2, cv2.LINE_AA)
        cv2.circle(c, (cx, cy), 30, subj, -1, cv2.LINE_AA)
    elif i == 3:   # soft drop shadow
        sh = np.zeros(c.shape[:2], np.float32)
        cv2.circle(sh, (cx + 8, cy + 10), 50, 1.0, -1)
        sh = cv2.GaussianBlur(sh, (0, 0), 6)[..., None] * 0.35
        c = (c * (1 - sh)).astype(np.uint8)
        cv2.circle(c, (cx, cy), 50, subj, -1, cv2.LINE_AA)
    elif i == 4:   # small detached detail (sweat drop) must survive
        cv2.circle(c, (cx, cy - 10), 45, subj, -1, cv2.LINE_AA)
        cv2.circle(c, (cx, size - 22), 7, (60, 120, 250), -1, cv2.LINE_AA)
    elif i == 5:   # blank
        pass
    elif i == 6:   # touches the cell border
        cv2.rectangle(c, (0, 40), (90, 150), subj, -1)
    elif i == 7:   # tall
        cv2.rectangle(c, (cx - 20, cy - 60), (cx + 20, cy + 60), subj, -1)
    elif i == 8:   # wide (same dimensions rotated)
        cv2.rectangle(c, (cx - 60, cy - 20), (cx + 60, cy + 20), subj, -1)
    elif i == 9:
        cv2.circle(c, (cx, cy), 40, subj, -1, cv2.LINE_AA)
    return c


def make_sheet(cell=200, seed=0, chroma="green", subj=YELLOW):
    rows = [np.concatenate([cell_art(r * 3 + c + 1, cell, seed, chroma, subj) for c in range(3)], 1) for r in range(3)]
    return np.concatenate(rows, 0)


def make_video(path: Path, cell=200, frames=90, fps=30, chroma="green"):
    """3x3 clip; every cell has a circle drifting right, so the end differs from the start (needs loop closing)."""
    size = cell * 3
    base = [bg(cell, 100 + i, chroma) for i in range(9)]
    codec = "libx264" if "libx264" in subprocess.run([ff.ffmpeg_exe(), "-hide_banner", "-encoders"], capture_output=True).stdout.decode() else "mpeg4"
    p = subprocess.Popen([ff.ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size}x{size}",
                          "-r", str(fps), "-i", "-", "-c:v", codec, "-pix_fmt", "yuv420p", "-qscale:v" if codec == "mpeg4" else "-crf",
                          "2" if codec == "mpeg4" else "16", str(path)], stdin=subprocess.PIPE)
    for t in range(frames):
        cells = []
        for i in range(9):
            c = base[i].copy()
            cv2.circle(c, (50 + t, 90), 32, YELLOW, -1, cv2.LINE_AA)
            cells.append(c)
        p.stdin.write(np.concatenate([np.concatenate(cells[r * 3:r * 3 + 3], 1) for r in range(3)], 0).tobytes())
    p.stdin.close()
    assert p.wait() == 0
