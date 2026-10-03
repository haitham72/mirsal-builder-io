"""Particle burst: a few sprite images -> a 3 s Telegram video-sticker frame sequence. Pure, deterministic, no network.

The clip starts from nothing, bursts out of an origin (the centre by default), falls, and ends with nothing:
  * the first frames are fully transparent (no particle spawns before frame 3, and a particle is born at scale 0);
  * the last frames are fully transparent (every particle is dead and faded to alpha 0 before `duration - 0.2 s`).

Layout of the module
  ParticleParams   every knob, validated and clamped by `.clamped()`; PRESETS / preset() name the common looks.
  trajectories()   the physics only (positions, scale, angle, opacity per particle per frame): inspectable, no pixels.
  simulate()       trajectories + drawing -> frames `(N, size, size, 4) uint8`, STRAIGHT alpha.
  to_webm()        the engine's own VP9+alpha encoder path under `cfg.video_max_bytes`.
  preview_webp()   an animated WebP loop for the browser.

Units: positions are fractions of the canvas (0..1, y grows downward like an image); speeds are canvas/s; times are seconds.
Same seed + same params + same sprites -> the same bytes (one local `numpy.random.default_rng(seed)`, no global state).
Pure numpy / OpenCV / Pillow; ffmpeg is only reached through `to_webm` (lazy import of the engine's encoder).
"""
from __future__ import annotations

import io
import math
from dataclasses import dataclass, fields, replace
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# ---- physics constants (canvas units) -------------------------------------------------------------------------------
G_CANVAS = 1.6          # gravity=1 pulls down at this many canvas/s^2
SPEED = 1.5             # magnitude=1 launches at SPEED * U(0.5, 1.1) canvas/s
VORTEX_K = 3.0          # vortex=1: tangential acceleration = VORTEX_K * |position - origin| canvas/s^2
DRAG = 0.9              # velocity decays by exp(-DRAG * dt): the burst slows down a little, never stops
GROWTH = 0.12           # a particle grows by this share over its life while flying
FADE_SHARE = 0.25       # the alpha fades to 0 over the last quarter of a particle's life
SPAWN_WINDOW = 0.35     # particles are born staggered over a 0.35 s window (shorter clips scale it down) ...
LEAD_FRAMES = 3         # ... that opens after this many empty frames: the first 3 frames are empty BY CONSTRUCTION (frame 0 certainly)
QUIET_TAIL = 0.2        # every particle is dead this long before the clip ends (last frames empty BY CONSTRUCTION)
MIN_LIFE = 0.3
ALPHA_TRIM = 4          # a sprite's alpha at or below this is haze, not subject: ignored when trimming
_POS_LIMIT = 50.0       # canvas units: positions are clipped here so nothing can overflow


# ---- parameters ----------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ParticleParams:
    gravity: float = 1.0            # -2..3: positive pulls down, negative floats up
    magnitude: float = 1.0          # 0..3: explosion speed
    vortex: float = 0.0             # -2..2: swirl around the origin; positive = clockwise as seen on screen, negative = counter-clockwise
    count: int = 28                 # 4..80 particles
    size_min: float = 0.10          # sprite's longest side, fraction of the canvas (0.02..0.8)
    size_max: float = 0.22
    spin: float = 1.0               # 0..3: rotation speed (0 = never rotates)
    lifetime: float = 2.2           # seconds a particle lives (<= duration - 0.4)
    spread: float = 360.0           # degrees of emission arc, centred upward when < 360
    pop: float = 0.25               # seconds of scale pop-in
    seed: int = 1
    fps: float = 30.0               # 20..60
    duration: float = 3.0           # seconds (1.0..3.0: Telegram's cap)
    size: int = 512                 # canvas side in px
    origin: tuple = (0.5, 0.5)      # fractions of the canvas
    show_source: bool = False       # reserved: the source sticker is not drawn yet

    @classmethod
    def from_dict(cls, d: dict) -> "ParticleParams":
        """Strict: an unknown key is a ValueError (the JSON contract has no silent extras)."""
        names = {f.name for f in fields(cls)}
        bad = sorted(set(d) - names)
        if bad:
            raise ValueError(f"unknown particle parameter(s): {', '.join(bad)}")
        return cls(**d)

    def to_dict(self) -> dict:
        return {f.name: (list(getattr(self, f.name)) if f.name == "origin" else getattr(self, f.name)) for f in fields(self)}

    def clamped(self) -> "ParticleParams":
        """The same params with every field inside its range. Nonsense raises ValueError: a non-number, count < 1, size <= 0,
        fps <= 0, duration <= 0, an origin that is not two numbers. Out-of-range but meaningful values are clamped, not rejected."""
        def num(name, v):
            try:
                x = float(v)
            except (TypeError, ValueError):
                raise ValueError(f"{name} must be a number, got {v!r}") from None
            if not math.isfinite(x):
                raise ValueError(f"{name} must be finite, got {v!r}")
            return x

        def lim(x, lo, hi):
            return min(max(x, lo), hi)

        count = num("count", self.count)
        if count < 1:
            raise ValueError(f"count must be at least 1, got {self.count!r}")
        size = num("size", self.size)
        if size <= 0:
            raise ValueError(f"size must be positive, got {self.size!r}")
        fps = num("fps", self.fps)
        if fps <= 0:
            raise ValueError(f"fps must be positive, got {self.fps!r}")
        duration = num("duration", self.duration)
        if duration <= 0:
            raise ValueError(f"duration must be positive, got {self.duration!r}")
        try:
            ox, oy = (num("origin", v) for v in self.origin)
        except TypeError:
            raise ValueError(f"origin must be two numbers, got {self.origin!r}") from None
        fps = lim(fps, 20.0, 60.0)
        duration = lim(duration, 1.0, 3.0)
        size_min = lim(num("size_min", self.size_min), 0.02, 0.8)
        size_max = lim(num("size_max", self.size_max), size_min, 0.8)      # size_max below size_min is raised to it
        lifetime = lim(num("lifetime", self.lifetime), MIN_LIFE, max(MIN_LIFE, duration - 0.4))
        return replace(
            self,
            gravity=lim(num("gravity", self.gravity), -2.0, 3.0),
            magnitude=lim(num("magnitude", self.magnitude), 0.0, 3.0),
            vortex=lim(num("vortex", self.vortex), -2.0, 2.0),
            count=int(lim(round(count), 4, 80)),
            size_min=size_min, size_max=size_max,
            spin=lim(num("spin", self.spin), 0.0, 3.0),
            lifetime=lifetime,
            spread=lim(num("spread", self.spread), 10.0, 360.0),
            pop=lim(num("pop", self.pop), 1.0 / fps, max(1.0 / fps, lifetime / 2)),
            seed=int(num("seed", self.seed)) % (2 ** 32),
            fps=fps, duration=duration,
            size=int(lim(round(size), 16, 1024)),
            origin=(lim(ox, 0.0, 1.0), lim(oy, 0.0, 1.0)),
            show_source=bool(self.show_source),
        )


PRESETS: dict = {
    "burst": {},                                                                                   # the defaults: a 360 degree pop from the centre
    "fountain": {"spread": 70.0, "magnitude": 1.9, "gravity": 1.3, "count": 36, "origin": (0.5, 0.8), "spin": 1.5},
    "vortex": {"vortex": 1.1, "gravity": 0.35, "magnitude": 0.8, "spin": 2.0, "count": 40},
    "rain": {"gravity": 0.9, "magnitude": 0.45, "count": 50, "size_min": 0.07, "size_max": 0.15, "origin": (0.5, 0.1), "spin": 0.6},
    "confetti": {"count": 64, "size_min": 0.06, "size_max": 0.12, "spin": 3.0, "gravity": 0.7, "magnitude": 1.5, "spread": 140.0, "lifetime": 2.4},
}


def preset(name: str, **override) -> ParticleParams:
    """A named look (see PRESETS) with keyword overrides, already clamped. Unknown name or parameter -> ValueError."""
    if name not in PRESETS:
        raise ValueError(f"unknown preset {name!r}; choose one of {', '.join(PRESETS)}")
    return ParticleParams.from_dict({**PRESETS[name], **override}).clamped()


# ---- physics --------------------------------------------------------------------------------------------------------
@dataclass
class Trajectories:
    """What `simulate` draws, before any pixel exists. Arrays are (frames, particles[, 2]); the particles are in spawn-draw order
    (draw back to front with `draw_order`)."""
    pos: np.ndarray          # (F, N, 2) canvas fractions of the particle centre (the origin until it spawns)
    scale: np.ndarray        # (F, N) pop-in x flight growth, 0 before spawn
    angle: np.ndarray        # (F, N) radians
    opacity: np.ndarray      # (F, N) 0..1: 1 while flying, fades to 0 over the last quarter of the life
    visible: np.ndarray      # (F, N) bool: spawned, not dead, scale and opacity worth drawing
    size_frac: np.ndarray    # (N,) sprite's longest side as a fraction of the canvas at scale 1
    sprite: np.ndarray       # (N,) which sprite each particle shows
    spawn: np.ndarray        # (N,) first frame (>= 3)
    life: np.ndarray         # (N,) seconds
    draw_order: np.ndarray   # (N,) particle indices, smallest first (drawn first = behind)
    p: ParticleParams        # the clamped params the plan was made with

    @property
    def frames(self) -> int:
        return self.pos.shape[0]


def _ease_out_back(t: np.ndarray, c1: float = 1.2) -> np.ndarray:
    u = t - 1.0
    return 1.0 + (c1 + 1.0) * u ** 3 + c1 * u ** 2


def trajectories(p: ParticleParams, n_sprites: int = 1) -> Trajectories:
    """The deterministic physics of one burst: seeded, vectorised, one semi-implicit Euler step per frame."""
    p = p.clamped()
    if n_sprites < 1:
        raise ValueError("n_sprites must be at least 1")
    n, F, dt = p.count, int(round(p.fps * p.duration)), 1.0 / p.fps
    rng = np.random.default_rng(p.seed)

    order = []                                                      # every sprite appears: seeded shuffles back to back
    while len(order) < n:
        order.extend(rng.permutation(n_sprites).tolist())
    sprite = np.array(order[:n], dtype=np.int64)

    slot = (rng.permutation(n) + rng.uniform(0.1, 0.9, n)) / n      # stratified emission: an even fan, not random clumps
    wheel = rng.uniform(0.0, 2 * math.pi)
    if p.spread >= 360.0:
        ang = wheel + slot * 2 * math.pi
    else:
        ang = -math.pi / 2 + math.radians(p.spread) * (slot - 0.5)  # y grows downward: -pi/2 is up
    window = min(SPAWN_WINDOW, 0.15 * p.duration)
    spawn = LEAD_FRAMES + np.rint(rng.uniform(0.0, window, n) * p.fps).astype(np.int64)     # never before frame 3: the start is empty
    speed = p.magnitude * SPEED * rng.uniform(0.5, 1.1, n)
    size_frac = rng.uniform(p.size_min, p.size_max, n)
    omega = p.spin * rng.uniform(-2.0, 2.0, n)
    theta0 = p.spin * rng.uniform(-0.6, 0.6, n)
    jitter = rng.uniform(0.8, 1.0, n)
    life = np.minimum(p.lifetime * jitter, (p.duration - QUIET_TAIL) - spawn * dt)          # dead before duration - 0.2 s
    life = np.maximum(life, 4 * dt)

    origin = np.array(p.origin, dtype=np.float64)
    v0 = np.stack([np.cos(ang), np.sin(ang)], 1) * speed[:, None]
    g_eff = p.gravity * G_CANVAS
    decay = math.exp(-DRAG * dt)
    pos, vel = np.tile(origin, (n, 1)), np.zeros((n, 2))
    P = np.empty((F, n, 2))
    for f in range(F):
        flying = spawn < f
        if flying.any():
            rel = pos - origin
            acc = np.empty_like(pos)
            acc[:, 0] = -p.vortex * VORTEX_K * rel[:, 1]
            acc[:, 1] = g_eff + p.vortex * VORTEX_K * rel[:, 0]
            vel[flying] = (vel[flying] + acc[flying] * dt) * decay
            pos[flying] = np.clip(pos[flying] + vel[flying] * dt, -_POS_LIMIT, _POS_LIMIT)
        born = spawn == f
        if born.any():
            pos[born] = origin
            vel[born] = v0[born]
        P[f] = pos

    frame_idx = np.arange(F)[:, None]
    age = (frame_idx - spawn[None, :]) * dt                         # (F, N), negative before spawn
    alive = (age >= 0) & (age < life[None, :])
    a = np.clip(age, 0.0, None)
    pop_scale = np.maximum(_ease_out_back(np.clip(a / p.pop, 0.0, 1.0)), 0.0)
    scale = np.where(alive, pop_scale * (1.0 + GROWTH * a / life[None, :]), 0.0)
    x = np.clip((life[None, :] - a) / (FADE_SHARE * life[None, :]), 0.0, 1.0)
    opacity = np.where(alive, x * x * (3.0 - 2.0 * x), 0.0)
    angle = theta0[None, :] + omega[None, :] * a
    visible = alive & (scale > 0.02) & (opacity > 0.004)
    return Trajectories(P, scale, angle, opacity, visible, size_frac, sprite, spawn, life,
                        np.argsort(size_frac, kind="stable"), p)


# ---- sprites --------------------------------------------------------------------------------------------------------
@dataclass
class _Sprite:
    levels: list             # premultiplied float32 RGBA, a 1 px transparent border, each level half the one before
    content: list            # longest side of the drawn content at each level (the border excluded)


def trim_sprite(img, pad: int = 2):
    """A particle is a TIGHT sprite (the UI/UX spec P6): the RGBA picture cropped to its alpha bounding box (alpha at or below ALPHA_TRIM is haze, not subject) plus `pad` px of air that never runs
    off the picture. Never a 512 px sticker canvas. None when nothing is drawn. Pure."""
    if not isinstance(img, np.ndarray) or img.dtype != np.uint8 or img.ndim != 3 or img.shape[2] != 4:
        raise ValueError("a sprite must be an RGBA uint8 array of shape (H, W, 4)")
    ys, xs = np.where(img[..., 3] > ALPHA_TRIM)
    if len(ys) == 0:
        return None
    y0, y1 = max(0, int(ys.min()) - pad), min(img.shape[0], int(ys.max()) + 1 + pad)
    x0, x1 = max(0, int(xs.min()) - pad), min(img.shape[1], int(xs.max()) + 1 + pad)
    return img[y0:y1, x0:x1].copy()


def _prepare(img, max_long: int) -> _Sprite | None:
    """Trim to the alpha bbox (+1 px transparent padding), premultiply, shrink to the largest size it will ever be drawn at, and
    build a half-size pyramid so a small particle is never sampled from a big image (no aliasing). None when fully transparent."""
    if not isinstance(img, np.ndarray) or img.dtype != np.uint8 or img.ndim != 3 or img.shape[2] != 4:
        raise ValueError("a sprite must be an RGBA uint8 array of shape (H, W, 4)")
    ys, xs = np.where(img[..., 3] > ALPHA_TRIM)
    if len(ys) == 0:
        return None
    crop = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32) * (1.0 / 255.0)
    crop[..., :3] *= crop[..., 3:4]
    h, w = crop.shape[:2]
    r = min(1.0, max_long / max(h, w))
    cur = cv2.resize(crop, (max(1, round(w * r)), max(1, round(h * r))), interpolation=cv2.INTER_AREA) if r < 1.0 else crop
    levels, content = [], []
    while True:
        h, w = cur.shape[:2]
        levels.append(cv2.copyMakeBorder(cur, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0)))
        content.append(float(max(h, w)))
        if max(h, w) <= 8 or len(levels) >= 6:
            break
        cur = cv2.resize(cur, (max(1, round(w / 2)), max(1, round(h / 2))), interpolation=cv2.INTER_AREA)
    return _Sprite(levels, content)


def _prepare_all(sprites, p: ParticleParams) -> list:
    if sprites is None or len(sprites) == 0:
        raise ValueError("no sprites given")
    max_long = max(8, math.ceil(p.size_max * p.size * 1.5))      # the biggest a particle gets: size_max x pop overshoot x growth
    ready = [s for s in (_prepare(img, max_long) for img in sprites) if s is not None]
    if not ready:
        raise ValueError("no usable sprite: every sprite is fully transparent")
    return ready


def fit_sprites(sprites: list, px: int) -> list:
    """Resize the sprites BEFORE simulating, for latency (a sticker is 512 px, a burst never draws a piece bigger than ~170 px): each sprite is trimmed to its alpha bbox and fitted into
    `px` x `px` (aspect kept, LANCZOS on premultiplied colour, never enlarged). A fully transparent sprite is returned as it is (`simulate` ignores it). Same order, same count."""
    px = int(px)
    if px < 1:
        raise ValueError("px must be positive")
    out = []
    for img in sprites:
        if not isinstance(img, np.ndarray) or img.dtype != np.uint8 or img.ndim != 3 or img.shape[2] != 4:
            raise ValueError("a sprite must be an RGBA uint8 array of shape (H, W, 4)")
        ys, xs = np.where(img[..., 3] > ALPHA_TRIM)
        if len(ys) == 0:
            out.append(img)
            continue
        crop = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        h, w = crop.shape[:2]
        if max(h, w) > px:
            k = px / max(h, w)
            crop = np.asarray(Image.fromarray(np.ascontiguousarray(crop), "RGBA").resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS), np.uint8)
        out.append(np.ascontiguousarray(crop))
    return out


# ---- drawing --------------------------------------------------------------------------------------------------------
def simulate(sprites: list, p: ParticleParams, on_frame=None) -> np.ndarray:
    """Draw one burst. `sprites` are RGBA uint8 arrays of any size (trimmed to their alpha bbox; fully transparent ones are ignored;
    ValueError when none is usable). Returns `(N, size, size, 4) uint8` with N = round(fps * duration) (90 at the defaults) and STRAIGHT
    alpha (composited premultiplied, then un-premultiplied). Frame 0 and the last frames are empty by construction. Pieces may leave the
    canvas. With more particles than sprites every sprite appears; with fewer particles than sprites only `count` of them can.
    `on_frame(i, n)` is called after each frame is drawn (progress)."""
    p = p.clamped()
    ready = _prepare_all(sprites, p)
    tr = trajectories(p, len(ready))
    S, F = p.size, tr.frames
    frames = np.zeros((F, S, S, 4), np.uint8)
    canvas = np.zeros((S, S, 4), np.float32)                      # premultiplied, 0..1
    ox = tr.pos[..., 0] * S - 0.5                                 # pixel-centre convention: the canvas centre is (S - 1) / 2
    oy = tr.pos[..., 1] * S - 0.5
    cos, sin = np.cos(tr.angle), np.sin(tr.angle)
    length = tr.size_frac[None, :] * S * tr.scale                 # the sprite's longest side in px, per frame
    sprite_of = tr.sprite.tolist()
    for f in range(F):
        idx = tr.draw_order[tr.visible[f, tr.draw_order]].tolist()
        dirty = None
        for i in idx:
            spr = ready[sprite_of[i]]
            L = float(length[f, i])
            if L < 0.5:
                continue
            k = min(len(spr.levels) - 1, max(0, int(math.floor(math.log2(spr.content[0] / L)))))
            lvl, k_len = spr.levels[k], spr.content[k]
            sc = L / k_len
            c, s = float(cos[f, i]), float(sin[f, i])
            ph, pw = lvl.shape[:2]
            hx = 0.5 * sc * (abs(c) * pw + abs(s) * ph) + 1.5
            hy = 0.5 * sc * (abs(s) * pw + abs(c) * ph) + 1.5
            cx, cy = float(ox[f, i]), float(oy[f, i])
            x0, x1 = max(0, math.floor(cx - hx)), min(S, math.ceil(cx + hx) + 1)
            y0, y1 = max(0, math.floor(cy - hy)), min(S, math.ceil(cy + hy) + 1)
            if x1 <= x0 or y1 <= y0:
                continue
            scx, scy = (pw - 1) / 2.0, (ph - 1) / 2.0
            M = np.array([[sc * c, -sc * s, (cx - x0) - (sc * c * scx - sc * s * scy)],
                          [sc * s, sc * c, (cy - y0) - (sc * s * scx + sc * c * scy)]])
            buf = cv2.warpAffine(lvl, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            op = float(tr.opacity[f, i])
            if op < 0.999:
                buf *= op
            roi = canvas[y0:y1, x0:x1]
            roi *= 1.0 - buf[..., 3:4]
            roi += buf
            dirty = (x0, y0, x1, y1) if dirty is None else (min(dirty[0], x0), min(dirty[1], y0), max(dirty[2], x1), max(dirty[3], y1))
        if dirty is not None:
            x0, y0, x1, y1 = dirty
            reg = canvas[y0:y1, x0:x1]
            a = reg[..., 3]
            a8 = np.clip(a * 255.0 + 0.5, 0, 255).astype(np.uint8)
            rgb = np.clip(reg[..., :3] * (255.0 / np.maximum(a, 1e-6))[..., None] + 0.5, 0, 255).astype(np.uint8)
            rgb[a8 == 0] = 0
            frames[f, y0:y1, x0:x1, :3] = rgb
            frames[f, y0:y1, x0:x1, 3] = a8
            reg[...] = 0.0
        if on_frame is not None:
            on_frame(f, F)
    return frames


# ---- output ---------------------------------------------------------------------------------------------------------
def to_webm(frames: np.ndarray, cfg, path, fps: float | None = None) -> dict:
    """Encode with the engine's own Telegram path (VP9 + alpha, `engine.video._encode_fit` walks the crf ladder to the best quality that fits
    `cfg.video_max_bytes`) and write the file to `path`. `fps` defaults to `cfg.video_max_fps`; pass the clip's own fps when it differs.
    Returns {bytes, crf, size_bytes, frames, fps, seconds, fits, encodes}. `bytes` is the file's content. If even the last rung is over the
    budget the file is still written and `fits` is False: format/size/codec limits are judged by the existing verifier, not here."""
    from . import ffmpeg as ff
    from .video import _encode_fit
    frames = np.ascontiguousarray(frames)
    if frames.ndim != 4 or frames.shape[3] != 4 or frames.dtype != np.uint8 or len(frames) == 0:
        raise ValueError("frames must be a non-empty uint8 array of shape (N, H, W, 4)")
    if not ff.has_vp9():
        raise RuntimeError("ffmpeg with libvpx-vp9 is not available")
    fps = float(fps if fps else cfg.video_max_fps)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    crf, data, encodes = _encode_fit(frames, fps, cfg, path)
    path.write_bytes(data)                                         # _encode_fit leaves the LAST attempt on disk, not necessarily the chosen one
    return {"bytes": data, "crf": crf, "size_bytes": len(data), "frames": len(frames), "fps": fps,
            "seconds": round(len(frames) / fps, 3), "fits": len(data) <= cfg.video_max_bytes, "encodes": encodes}


def preview_webp(frames: np.ndarray, size: int = 256, fps: float = 30.0) -> bytes:
    """An animated, looping, alpha-keeping WebP of the clip at `size` x `size` for the browser preview (Pillow only). The frame durations
    are spread so the loop is exactly `len(frames) / fps` long (33/34 ms alternating at 30 fps). The encoder may merge identical
    neighbouring frames (the empty end), so count the duration, not the frames, when judging it."""
    if frames.ndim != 4 or frames.shape[3] != 4 or len(frames) == 0:
        raise ValueError("frames must be a non-empty array of shape (N, H, W, 4)")
    size = int(size)
    if size < 1:
        raise ValueError("size must be positive")
    src = frames if frames.shape[1] == size and frames.shape[2] == size else None
    ims = []
    for fr in frames:
        if src is None:
            a = fr[..., 3:4].astype(np.float32)                    # shrink premultiplied: straight-alpha resizing would bleed the colour of invisible pixels
            pm = cv2.resize(np.concatenate([fr[..., :3].astype(np.float32) * a / 255.0, a], -1), (size, size), interpolation=cv2.INTER_AREA)
            al = pm[..., 3:4]
            rgb = np.where(al > 0.5, pm[..., :3] * 255.0 / np.maximum(al, 1e-3), 0.0)
            fr = np.clip(np.concatenate([rgb, al], -1) + 0.5, 0, 255).astype(np.uint8)
        ims.append(Image.fromarray(np.ascontiguousarray(fr), "RGBA"))
    n = len(ims)
    durations = [max(1, round((i + 1) * 1000.0 / fps) - round(i * 1000.0 / fps)) for i in range(n)]
    buf = io.BytesIO()
    ims[0].save(buf, "WEBP", save_all=True, append_images=ims[1:], duration=durations, loop=0, quality=80, method=2, exact=True)
    return buf.getvalue()
