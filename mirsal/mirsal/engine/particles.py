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
  png_bytes()      an RGBA array as PNG bytes.
The emoji glyph as a sprite is engine/emoji_glyph.py; the Lottie export of these trajectories is engine/lottie.py.

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
VORTEX_W = 7.5          # vortex=1: the swirl's flow field turns at VORTEX_W rad/s around the origin (vortex=1.8 is about 2.1 turns a second)
VORTEX_RELAX = 2.5      # |vortex|>=1: a particle's velocity relaxes toward that field at this rate per second (weaker swirls relax in proportion)
DRAG = 0.9              # velocity decays by exp(-DRAG * dt): the burst slows down a little, never stops
GROWTH = 0.12           # a particle grows by this share over its life while flying
FADE_SHARE = 0.25       # the alpha fades to 0 over the last quarter of a particle's life
SPAWN_WINDOW = 0.35     # particles are born staggered over a 0.35 s window (shorter clips scale it down) ...
LEAD_FRAMES = 3         # ... that opens after this many empty frames: the first 3 frames are empty BY CONSTRUCTION (frame 0 certainly)
QUIET_TAIL = 0.2        # every particle is dead this long before the clip ends (last frames empty BY CONSTRUCTION)
MIN_LIFE = 0.3
MORPH_XFADE = 0.15      # seconds a particle crossfades at its morph (into its target, or out into its children)
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
    particle_size: float = 1.0      # 0.25..3: how big the particles look, a multiplier on size_min/size_max (the "Size" slider)
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
    size_in_dur: float = 0.0        # 0..1.5 s (<= lifetime/2): each particle zooms from nothing to full size over this long after its birth (0 = born full size)
    size_out_dur: float = 0.0       # 0..1.5 s (<= lifetime/2): ... and back to nothing over this long before its death (0 = no zoom out)
    hue_var: float = 0.0            # 0..180 degrees: each particle's colours turn by a seeded hue in [-hue_var, +hue_var] (0 = the sprite's own colours)
    fade_start: float = 0.0         # Fade out start, s after a particle's birth: its opacity starts dropping from 100% here
    fade_dur: float = 0.0           # Fade out duration, s: 100% -> 0% takes this long, linearly (0 = off: the old fade over the last quarter of its life)
    fade_var: float = 0.0           # Fade out variation, s: each particle's start and duration each move by a seeded +-fade_var (never below 0)
    speed_var: float = 0.0          # 0..1: each particle's launch speed is Speed x (1 +- speed_var), seeded (on top of the old 0.5-1.1 spread)
    speed_pulse: float = 0.0        # 0..1: each particle's speed swells and slows by this share, on its own seeded phase (0 = steady)
    pulse_hz: float = 2.0           # 0.2..6: how many swells a second
    flip: float = 0.0               # 0..4 turns/s: the cheap spin, horizontal scale 100% -> -100% -> 100% (a card flip, no rotation; 0 = off)
    flip_var: float = 0.0           # 0..1: each particle's flip rate +- this share
    morph_at: float = 0.0           # 0..2 s after birth: when a particle turns from its origin into a morph target (0 = no morph; Lottie style)
    morph_var: float = 0.0          # 0..1 s: +- per particle on morph_at
    children: int = 0               # 0..12: Morph auxiliary, each particle bursts this many children (same settings, one level) at its morph (its fade start with no morph)
    child_size: float = 0.5         # 0.1..3: a child's size at birth, x its parent's drawn size at that moment
    child_size_var: float = 0.0     # 0..1: a seeded log spread per child around child_size (most stay near it, a few reach 1x or 3x)
    morph_burst: int = 0            # 0 = at its morph a particle turns into its target (1:1); 1 = it bursts into its children (it fades out, they fly the target)

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
        envelope = min(1.5, lifetime / 2)
        return replace(
            self,
            gravity=lim(num("gravity", self.gravity), -2.0, 3.0),
            magnitude=lim(num("magnitude", self.magnitude), 0.0, 3.0),
            vortex=lim(num("vortex", self.vortex), -2.0, 2.0),
            count=int(lim(round(count), 4, 80)),
            size_min=size_min, size_max=size_max,
            particle_size=lim(num("particle_size", self.particle_size), 0.25, 3.0),
            spin=lim(num("spin", self.spin), 0.0, 3.0),
            lifetime=lifetime,
            spread=lim(num("spread", self.spread), 10.0, 360.0),
            pop=lim(num("pop", self.pop), 1.0 / fps, max(1.0 / fps, lifetime / 2)),
            seed=int(num("seed", self.seed)) % (2 ** 32),
            fps=fps, duration=duration,
            size=int(lim(round(size), 16, 1024)),
            origin=(lim(ox, 0.0, 1.0), lim(oy, 0.0, 1.0)),
            show_source=bool(self.show_source),
            size_in_dur=lim(num("size_in_dur", self.size_in_dur), 0.0, envelope),
            size_out_dur=lim(num("size_out_dur", self.size_out_dur), 0.0, envelope),
            hue_var=lim(num("hue_var", self.hue_var), 0.0, 180.0),
            fade_start=lim(num("fade_start", self.fade_start), 0.0, duration),
            fade_dur=lim(num("fade_dur", self.fade_dur), 0.0, duration),
            fade_var=lim(num("fade_var", self.fade_var), 0.0, 1.0),
            speed_var=lim(num("speed_var", self.speed_var), 0.0, 1.0),
            speed_pulse=lim(num("speed_pulse", self.speed_pulse), 0.0, 1.0),
            pulse_hz=lim(num("pulse_hz", self.pulse_hz), 0.2, 6.0),
            flip=lim(num("flip", self.flip), 0.0, 4.0),
            flip_var=lim(num("flip_var", self.flip_var), 0.0, 1.0),
            morph_at=lim(num("morph_at", self.morph_at), 0.0, duration),
            morph_var=lim(num("morph_var", self.morph_var), 0.0, 1.0),
            children=int(lim(round(num("children", self.children)), 0, 12)),
            child_size=lim(num("child_size", self.child_size), 0.1, 3.0),
            child_size_var=lim(num("child_size_var", self.child_size_var), 0.0, 1.0),
            morph_burst=1 if num("morph_burst", self.morph_burst) >= 0.5 else 0,
        )


# Each preset has a measurable signature (tests/test_emoji_motion.py checks it on trajectories(), numbers only):
#   burst     radial outward, a 360 degree fan from the centre
#   fountain  from the bottom (0.5, 0.8), a cone of at most 90 degrees, launched upward, then falls back
#   vortex    tangential speed well above radial (vortex >= 1.5, magnitude <= 0.6), two or more turns around the origin, stays on the canvas
#   rain      from the top (0.5, 0.1), magnitude <= 0.5, gravity down, a spread of at most 120 degrees: it falls
#   confetti  48 or more particles, low gravity, fast spin, a wide fan
PRESETS: dict = {
    "burst": {},                                                                                   # the defaults: a 360 degree pop from the centre
    "fountain": {"spread": 70.0, "magnitude": 1.9, "gravity": 1.3, "count": 36, "origin": (0.5, 0.8), "spin": 1.5},
    "vortex": {"vortex": 1.8, "gravity": 0.1, "magnitude": 0.5, "spin": 2.0, "count": 36, "lifetime": 2.6, "size_min": 0.07, "size_max": 0.14},
    "rain": {"gravity": 0.9, "magnitude": 0.35, "count": 50, "size_min": 0.07, "size_max": 0.15, "origin": (0.5, 0.1), "spin": 0.6, "spread": 100.0},
    "confetti": {"count": 64, "size_min": 0.06, "size_max": 0.12, "spin": 3.0, "gravity": 0.4, "magnitude": 1.5, "spread": 160.0, "lifetime": 2.4},
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
    opacity: np.ndarray      # (F, N) 0..1: 1 while flying, with fade_dur: 1 until fade_start (+-fade_var) after birth, then linearly to 0 over fade_dur (+-fade_var), done by its death at the latest; else fades over the last quarter of the life
    visible: np.ndarray      # (F, N) bool: spawned, not dead, scale and opacity worth drawing
    size_frac: np.ndarray    # (N,) sprite's longest side as a fraction of the canvas at scale 1
    sprite: np.ndarray       # (N,) which sprite each particle shows
    hue: np.ndarray          # (N,) degrees each particle's colours are turned by (0 everywhere when hue_var is 0)
    spawn: np.ndarray        # (N,) first frame (>= 3)
    life: np.ndarray         # (N,) seconds
    draw_order: np.ndarray   # (N,) particle indices, smallest first (drawn first = behind)
    p: ParticleParams        # the clamped params the plan was made with
    flipx: np.ndarray = None     # (F, N) the card flip's horizontal scale, 1 -> -1 -> 1 (all 1 with flip 0)
    morph: np.ndarray = None     # (N,) seconds after birth each particle morphs (inf = never)
    pick: np.ndarray = None      # (N,) 0..1 which morph target
    parent: np.ndarray = None    # (N,) the root a child burst from (-1 = a root)

    @property
    def frames(self) -> int:
        return self.pos.shape[0]


def _ease_out_back(t: np.ndarray, c1: float = 1.2) -> np.ndarray:
    u = t - 1.0
    return 1.0 + (c1 + 1.0) * u ** 3 + c1 * u ** 2


def trajectories(p: ParticleParams, n_sprites: int = 1) -> Trajectories:
    """The deterministic physics of one burst: seeded, vectorised, one semi-implicit Euler step per frame. With `children` > 0 every root
    particle bursts that many children (same settings, one level) from where it is at its morph (its fade start without one); they follow the roots in every array."""
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
    ang = _fan(p, wheel, slot)
    window = min(SPAWN_WINDOW, 0.15 * p.duration)
    spawn = LEAD_FRAMES + np.rint(rng.uniform(0.0, window, n) * p.fps).astype(np.int64)     # never before frame 3: the start is empty
    speed = p.magnitude * SPEED * rng.uniform(0.5, 1.1, n)
    size_frac = np.minimum(rng.uniform(p.size_min, p.size_max, n) * p.particle_size, 0.9)
    omega = p.spin * rng.uniform(-2.0, 2.0, n)
    theta0 = p.spin * rng.uniform(-0.6, 0.6, n)
    jitter = rng.uniform(0.8, 1.0, n)
    hue = rng.uniform(-1.0, 1.0, n) * p.hue_var                     # drawn after every older draw: an older burst is unchanged
    fade_k = rng.uniform(-1.0, 1.0, (2, n)) * p.fade_var             # +- seconds on (start, duration)
    extra = _Extra.draw(rng, p, n)                                   # drawn LAST, for the same reason: speed spread, pulse, flip, morph
    speed = speed * extra.speed_k
    life = np.minimum(p.lifetime * jitter, (p.duration - QUIET_TAIL) - spawn * dt)          # dead before duration - 0.2 s
    life = np.maximum(life, 4 * dt)

    origin = np.tile(np.array(p.origin, dtype=np.float64), (n, 1))
    v0 = np.stack([np.cos(ang), np.sin(ang)], 1) * speed[:, None]
    P = _fly(p, F, dt, spawn, origin, v0, extra)
    scale, opacity, a, alive = _look(p, F, dt, spawn, life, fade_k)
    morphs = p.morph_at > 0
    m_at = np.maximum(p.morph_at + extra.morph_k, dt)                # seconds after birth each root morphs (when morphs)
    if morphs and p.morph_burst and p.children > 0:                  # Bursts into: the root fades out over MORPH_XFADE at its morph, its children take over
        cut = m_at[None, :] + MORPH_XFADE
        alive = alive & (a < cut)
        opacity = np.where(alive, opacity * np.clip((cut - a) / MORPH_XFADE, 0.0, 1.0), 0.0)
        scale = np.where(alive, scale, 0.0)
        life = np.minimum(life, m_at + MORPH_XFADE)

    parent = np.full(n, -1, dtype=np.int64)
    if p.children > 0:                                               # Morph auxiliary: one level of child bursts, every child drawn after the roots
        when = m_at if morphs else _fade_start_s(p, life, fade_k)    # the morph starts the children (Haitham 2026-10-14); no morph = the fade start
        f_start = spawn + np.rint(when * p.fps).astype(np.int64)
        f_last = int(round((p.duration - QUIET_TAIL) * p.fps)) - 4
        k = p.children
        par = np.repeat(np.arange(n), k)
        c_spawn = np.repeat(f_start, k)
        m = len(par)
        c_slot = (np.tile(np.arange(k), n) + rng.uniform(0.1, 0.9, m)) / k
        c_wheel = np.repeat(rng.uniform(0.0, 2 * math.pi, n), k)
        c_ang = _fan(p, c_wheel, c_slot)
        c_speed = p.magnitude * SPEED * rng.uniform(0.5, 1.1, m)
        c_rel = np.clip(p.child_size * np.exp(p.child_size_var * rng.standard_normal(m)), 0.1, 3.0)
        c_omega = p.spin * rng.uniform(-2.0, 2.0, m)
        c_theta0 = p.spin * rng.uniform(-0.6, 0.6, m)
        c_jitter = rng.uniform(0.8, 1.0, m)
        c_fade_k = rng.uniform(-1.0, 1.0, (2, m)) * p.fade_var
        c_extra = _Extra.draw(rng, p, m)
        sel = np.flatnonzero((c_spawn > spawn[par]) & (c_spawn < f_last))
        if len(sel):
            par, c_spawn = par[sel], c_spawn[sel]
            c_origin = P[c_spawn, par]                                # where the parent is when its fade starts
            c_size = np.minimum(size_frac[par] * np.maximum(scale[c_spawn, par], 0.05) * c_rel[sel], 0.9)
            c_extra = c_extra.take(sel)
            c_v0 = np.stack([np.cos(c_ang[sel]), np.sin(c_ang[sel])], 1) * (c_speed[sel] * c_extra.speed_k)[:, None]
            c_life = np.maximum(np.minimum(p.lifetime * c_jitter[sel], (p.duration - QUIET_TAIL) - c_spawn * dt), 4 * dt)
            c_fk = c_fade_k[:, sel]
            CP = _fly(p, F, dt, c_spawn, c_origin, c_v0, c_extra)
            CP = np.where((np.arange(F)[:, None] < c_spawn[None, :])[..., None], c_origin[None, :, :], CP)
            c_scale, c_opacity, c_a, c_alive = _look(p, F, dt, c_spawn, c_life, c_fk)
            P = np.concatenate([P, CP], 1)
            scale, opacity, a, alive = (np.concatenate(x, 1) for x in ((scale, c_scale), (opacity, c_opacity), (a, c_a), (alive, c_alive)))
            spawn, life, size_frac = np.concatenate([spawn, c_spawn]), np.concatenate([life, c_life]), np.concatenate([size_frac, c_size])
            omega, theta0 = np.concatenate([omega, c_omega[sel]]), np.concatenate([theta0, c_theta0[sel]])
            sprite, hue = np.concatenate([sprite, sprite[par]]), np.concatenate([hue, hue[par]])
            parent = np.concatenate([parent, par])
            extra = extra.join(c_extra)

    angle = theta0[None, :] + omega[None, :] * a
    flipx = np.where(alive, np.cos(2 * math.pi * extra.flip_rate[None, :] * a), 1.0) if p.flip > 0 else np.ones_like(a)
    visible = alive & (scale > 0.02) & (opacity > 0.004)
    morph = np.maximum(p.morph_at + extra.morph_k, dt) if morphs else np.full(len(spawn), np.inf)
    morph[parent >= 0] = np.inf                                      # a child is born as the target: it never morphs again
    return Trajectories(P, scale, angle, opacity, visible, size_frac, sprite, hue, spawn, life,
                        np.argsort(size_frac, kind="stable"), p, flipx, morph, extra.pick, parent)


def _fan(p: ParticleParams, wheel, slot):
    if p.spread >= 360.0:
        return wheel + slot * 2 * math.pi
    return -math.pi / 2 + math.radians(p.spread) * (slot - 0.5)      # y grows downward: -pi/2 is up


@dataclass
class _Extra:
    """The per-particle draws added for Lottie style (2026-10-14), always drawn after the older ones so an older burst keeps its bytes."""
    speed_k: np.ndarray      # launch speed multiplier, 1 +- speed_var
    phase: np.ndarray        # the speed pulse's phase
    flip_rate: np.ndarray    # card flips per second, flip +- flip_var share
    morph_k: np.ndarray      # +- seconds on morph_at
    pick: np.ndarray         # 0..1: which morph target (the exporter maps it onto its list)

    @classmethod
    def draw(cls, rng, p: ParticleParams, n: int) -> "_Extra":
        u = rng.uniform(-1.0, 1.0, (4, n))
        return cls(1.0 + p.speed_var * u[0], math.pi * (u[1] + 1.0), p.flip * (1.0 + p.flip_var * u[2]), p.morph_var * u[3], rng.uniform(0.0, 1.0, n))

    def take(self, idx) -> "_Extra":
        return _Extra(*(getattr(self, f.name)[idx] for f in fields(self)))

    def join(self, other: "_Extra") -> "_Extra":
        return _Extra(*(np.concatenate([getattr(self, f.name), getattr(other, f.name)]) for f in fields(self)))


def _fly(p: ParticleParams, F: int, dt: float, spawn, origin, v0, extra: _Extra) -> np.ndarray:
    """(F, n, 2) positions: gravity, drag, the swirl about each particle's own origin, the speed pulse on the displacement."""
    n = len(spawn)
    g_eff = p.gravity * G_CANVAS
    decay = math.exp(-DRAG * dt)
    swirl = min(1.0, abs(p.vortex))                                  # the swirl is a flow field: velocity relaxes toward a rotation about the origin,
    turn = p.vortex * VORTEX_W                                       # and the centripetal term keeps the orbit (no centrifugal fling off the canvas)
    pos, vel = origin.copy(), np.zeros((n, 2))
    P = np.empty((F, n, 2))
    for f in range(F):
        flying = spawn < f
        if flying.any():
            acc = np.zeros_like(pos)
            acc[:, 1] = g_eff
            if swirl:
                rel = pos - origin
                r = np.hypot(rel[:, 0], rel[:, 1])[:, None] + 1e-6
                field = np.stack([-rel[:, 1], rel[:, 0]], 1) * turn
                tang = (rel[:, 0] * vel[:, 1] - rel[:, 1] * vel[:, 0])[:, None] / r
                acc += VORTEX_RELAX * swirl * (field - vel) - swirl * (tang * tang / r) * (rel / r)
            vel[flying] = (vel[flying] + acc[flying] * dt) * decay
            step = vel[flying] * dt
            if p.speed_pulse > 0:                                    # Speed pulse: each particle swells and slows on its own phase
                age = (f - spawn[flying]) * dt
                step = step * (1.0 + p.speed_pulse * np.sin(2 * math.pi * p.pulse_hz * age + extra.phase[flying]))[:, None]
            pos[flying] = np.clip(pos[flying] + step, -_POS_LIMIT, _POS_LIMIT)
        born = spawn == f
        if born.any():
            pos[born] = origin[born]
            vel[born] = v0[born]
        P[f] = pos
    return P


def _fade_start_s(p: ParticleParams, life, fade_k):
    """Seconds after birth each particle's fade starts (what `_look` uses): the Fade out start, else the last quarter of its life."""
    if p.fade_dur > 0:
        dt = 1.0 / p.fps
        f_end = np.minimum(np.maximum(p.fade_start + fade_k[0], 0.0) + np.maximum(p.fade_dur + fade_k[1], dt), life)
        return np.minimum(np.maximum(p.fade_start + fade_k[0], 0.0), f_end - dt)
    return life * (1.0 - FADE_SHARE)


def _look(p: ParticleParams, F: int, dt: float, spawn, life, fade_k):
    """(scale, opacity, age, alive), each (F, n): pop-in, growth, Size in / out, and the fade."""
    frame_idx = np.arange(F)[:, None]
    age = (frame_idx - spawn[None, :]) * dt                         # (F, N), negative before spawn
    alive = (age >= 0) & (age < life[None, :])
    a = np.clip(age, 0.0, None)
    pop_scale = np.maximum(_ease_out_back(np.clip(a / p.pop, 0.0, 1.0)), 0.0)
    envelope = np.ones_like(a)                                       # Size in / Size out: multiplies the pop-in and the growth, never replaces them
    if p.size_in_dur > 0:
        envelope *= np.clip(a / p.size_in_dur, 0.0, 1.0)
    if p.size_out_dur > 0:
        envelope *= np.clip((life[None, :] - a) / p.size_out_dur, 0.0, 1.0)
    scale = np.where(alive, pop_scale * (1.0 + GROWTH * a / life[None, :]) * envelope, 0.0)
    if p.fade_dur > 0:                                               # Fade out: start and duration in seconds, per particle, linear 100% -> 0%
        f_end = np.minimum(np.maximum(p.fade_start + fade_k[0], 0.0) + np.maximum(p.fade_dur + fade_k[1], dt), life)     # 0% by its death at the latest
        f_start = np.minimum(np.maximum(p.fade_start + fade_k[0], 0.0), f_end - dt)
        x = np.clip((f_end[None, :] - a) / (f_end - f_start)[None, :], 0.0, 1.0)
        opacity = np.where(alive, x, 0.0)
    else:
        x = np.clip((life[None, :] - a) / (FADE_SHARE * life[None, :]), 0.0, 1.0)
        opacity = np.where(alive, x * x * (3.0 - 2.0 * x), 0.0)
    return scale, opacity, a, alive


# ---- sprites --------------------------------------------------------------------------------------------------------
@dataclass
class AnimatedSprite:
    """One sprite's RGBA timeline. Every frame shares a canvas; playback begins at particle birth."""
    frames: np.ndarray
    fps: float = 30.0

    def __post_init__(self):
        if (not isinstance(self.frames, np.ndarray) or self.frames.dtype != np.uint8
                or self.frames.ndim != 4 or self.frames.shape[-1] != 4 or not len(self.frames)
                or not self.frames.shape[1] or not self.frames.shape[2]):
            raise ValueError("animated sprite frames must be non-empty RGBA uint8 (F, H, W, 4)")
        if not math.isfinite(float(self.fps)) or self.fps <= 0:
            raise ValueError("animated sprite fps must be positive and finite")


def trim_animation(sprite: AnimatedSprite, pad: int = 2) -> AnimatedSprite | None:
    """Crop once around the whole timeline, preserving internal movement and empty frames."""
    ys, xs = np.where((sprite.frames[..., 3] > ALPHA_TRIM).any(axis=0))
    if not len(ys):
        return None
    y0, y1 = max(0, int(ys.min()) - pad), min(sprite.frames.shape[1], int(ys.max()) + 1 + pad)
    x0, x1 = max(0, int(xs.min()) - pad), min(sprite.frames.shape[2], int(xs.max()) + 1 + pad)
    return AnimatedSprite(sprite.frames[:, y0:y1, x0:x1].copy(), sprite.fps)


@dataclass
class _Sprite:
    levels: list             # premultiplied float32 RGBA, a 1 px transparent border, each level half the one before
    content: list            # longest side of the drawn content at each level (the border excluded)


@dataclass
class _Animated:
    frames: list[_Sprite]
    fps: float

    def at(self, age: float) -> _Sprite:
        return self.frames[int(math.floor(max(0.0, age) * self.fps + 1e-9)) % len(self.frames)]


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


def _prepare(img, max_long: int, keep_canvas: bool = False) -> _Sprite | None:
    """Trim to the alpha bbox (+1 px transparent padding), premultiply, shrink to the largest size it will ever be drawn at, and
    build a half-size pyramid so a small particle is never sampled from a big image (no aliasing). None when fully transparent."""
    if not isinstance(img, np.ndarray) or img.dtype != np.uint8 or img.ndim != 3 or img.shape[2] != 4:
        raise ValueError("a sprite must be an RGBA uint8 array of shape (H, W, 4)")
    ys, xs = np.where(img[..., 3] > ALPHA_TRIM)
    if len(ys) == 0 and not keep_canvas:
        return None
    crop = (img if keep_canvas else img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]).astype(np.float32) * (1.0 / 255.0)
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
    max_long = max(8, math.ceil(min(p.size_max * p.particle_size, 0.9) * p.size * 1.5))      # the biggest a particle gets: size_max x Size x pop overshoot x growth
    ready = []
    for img in sprites:
        if isinstance(img, AnimatedSprite):
            trimmed = trim_animation(img, pad=0)
            if trimmed is not None:
                ready.append(_Animated([_prepare(fr, max_long, keep_canvas=True) for fr in trimmed.frames], trimmed.fps))
        else:
            spr = _prepare(img, max_long)
            if spr is not None:
                ready.append(spr)
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
        if isinstance(img, AnimatedSprite):
            trimmed = trim_animation(img, pad=0)
            if trimmed is None:
                out.append(img)
                continue
            h, w = trimmed.frames.shape[1:3]
            if max(h, w) > px:
                ratio = px / max(h, w)
                wh = (max(1, round(w * ratio)), max(1, round(h * ratio)))
                fitted = [np.asarray(Image.fromarray(np.ascontiguousarray(fr), "RGBA").resize(wh, Image.LANCZOS), np.uint8) for fr in trimmed.frames]
                trimmed = AnimatedSprite(np.stack(fitted), img.fps)
            out.append(trimmed)
            continue
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


# ---- hue ------------------------------------------------------------------------------------------------------------
def hue_matrix(deg: float) -> np.ndarray:
    """The 3x3 hue rotation of CSS `filter: hue-rotate(deg)` (a turn about the grey axis, luminance weights 0.213/0.715/0.072).
    Linear in RGB, so it applies to premultiplied colour as it is. 0 degrees is the identity."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[0.213 + c * 0.787 - s * 0.213, 0.715 - c * 0.715 - s * 0.715, 0.072 - c * 0.072 + s * 0.928],
                     [0.213 - c * 0.213 + s * 0.143, 0.715 + c * 0.285 + s * 0.140, 0.072 - c * 0.072 - s * 0.283],
                     [0.213 - c * 0.213 - s * 0.787, 0.715 - c * 0.715 + s * 0.715, 0.072 + c * 0.928 + s * 0.072]], np.float32)


def hue_rotate(img: np.ndarray, deg: float) -> np.ndarray:
    """A straight-alpha RGBA uint8 picture with its colours turned by `deg` degrees (hue_matrix); alpha untouched. Pure."""
    if abs(deg) <= 1e-9:
        return img.copy()
    rgb = img[..., :3].astype(np.float32) @ hue_matrix(deg).T
    return np.dstack([np.clip(rgb + 0.5, 0, 255).astype(np.uint8), img[..., 3]])


# ---- drawing --------------------------------------------------------------------------------------------------------
def fit_zoom(tr: "Trajectories", origin: tuple) -> float:
    """The zoom (<= 1) about `origin` that keeps every visible particle, its whole sprite, inside the canvas: the burst SCALED to fit
    instead of cut at the edges (the hover preview; Haitham, 2026-10-14). 1.0 when it already fits."""
    vis = tr.visible
    if not vis.any():
        return 1.0
    h = 0.5 * (tr.size_frac[None, :] * tr.scale)[vis] * 1.42          # a rotated sprite's half-diagonal, as a share of the canvas
    dx, dy = tr.pos[..., 0][vis] - origin[0], tr.pos[..., 1][vis] - origin[1]
    z = 1.0
    for room, need in ((origin[0], np.max(h - dx)), (1 - origin[0], np.max(h + dx)), (origin[1], np.max(h - dy)), (1 - origin[1], np.max(h + dy))):
        if need > 1e-6:
            z = min(z, max(room, 0.0) / need)
    return float(max(0.05, z))


def simulate(sprites: list, p: ParticleParams, on_frame=None, fit: bool = False) -> np.ndarray:
    """Draw one burst. `sprites` are static RGBA uint8 arrays or AnimatedSprite timelines (trimmed to their union alpha bbox; fully transparent ones are ignored;
    ValueError when none is usable). Returns `(N, size, size, 4) uint8` with N = round(fps * duration) (90 at the defaults) and STRAIGHT
    alpha (composited premultiplied, then un-premultiplied). Frame 0 and the last frames are empty by construction. Pieces may leave the
    canvas. With more particles than sprites every sprite appears; with fewer particles than sprites only `count` of them can.
    `on_frame(i, n)` is called after each frame is drawn (progress). `fit`: the whole burst is zoomed about its origin until nothing leaves
    the canvas (`fit_zoom`), the same motion smaller, never cut."""
    p = p.clamped()
    ready = _prepare_all(sprites, p)
    tr = trajectories(p, len(ready))
    S, F = p.size, tr.frames
    z = fit_zoom(tr, p.origin) if fit else 1.0
    frames = np.zeros((F, S, S, 4), np.uint8)
    canvas = np.zeros((S, S, 4), np.float32)                      # premultiplied, 0..1
    ox = (p.origin[0] + (tr.pos[..., 0] - p.origin[0]) * z) * S - 0.5        # pixel-centre convention: the canvas centre is (S - 1) / 2
    oy = (p.origin[1] + (tr.pos[..., 1] - p.origin[1]) * z) * S - 0.5
    cos, sin = np.cos(tr.angle), np.sin(tr.angle)
    length = tr.size_frac[None, :] * S * tr.scale * z             # the sprite's longest side in px, per frame
    sprite_of = tr.sprite.tolist()
    turn = {i: hue_matrix(h) for i, h in enumerate(tr.hue.tolist()) if abs(h) > 1e-9}
    for f in range(F):
        idx = tr.draw_order[tr.visible[f, tr.draw_order]].tolist()
        dirty = None
        for i in idx:
            spr = ready[sprite_of[i]]
            if isinstance(spr, _Animated):
                spr = spr.at((f - int(tr.spawn[i])) / p.fps)
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
            fx = float(tr.flipx[f, i])                              # the card flip: x scaled before the rotation
            M = np.array([[sc * c * fx, -sc * s, (cx - x0) - (sc * c * fx * scx - sc * s * scy)],
                          [sc * s * fx, sc * c, (cy - y0) - (sc * s * fx * scx + sc * c * scy)]])
            buf = cv2.warpAffine(lvl, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            if i in turn:                                          # linear, so it is exact on premultiplied colour; alpha untouched
                buf[..., :3] = np.clip(buf[..., :3] @ turn[i].T, 0.0, buf[..., 3:4])
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
def to_webm(frames: np.ndarray, cfg, path, fps: float | None = None, budget: int | None = None) -> dict:
    """Encode with the engine's own Telegram path (VP9 + alpha, `engine.video._encode_fit` walks the crf ladder to the best quality that fits
    `budget`, default `cfg.video_max_bytes`) and write the file to `path`. `fps` defaults to `cfg.video_max_fps`; pass the clip's own fps when it differs.
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
    crf, data, encodes = _encode_fit(frames, fps, cfg, path, budget=budget)
    path.write_bytes(data)                                         # _encode_fit leaves the LAST attempt on disk, not necessarily the chosen one
    limit = budget if budget is not None else cfg.video_max_bytes
    return {"bytes": data, "crf": crf, "size_bytes": len(data), "frames": len(frames), "fps": fps,
            "seconds": round(len(frames) / fps, 3), "fits": len(data) <= limit, "encodes": encodes}


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


def png_bytes(img: np.ndarray) -> bytes:
    """An RGBA uint8 array as PNG bytes (Pillow, deterministic for the same pixels)."""
    buf = io.BytesIO()
    Image.fromarray(np.ascontiguousarray(img), "RGBA").save(buf, "PNG")
    return buf.getvalue()


# ---- default sprite -----------------------------------------------------------------------------------------------------
def default_sprite(px: int = 128) -> np.ndarray:
    """A procedural fallback sprite (RGBA uint8): a soft four-point sparkle on transparency. Deterministic, free, no network.

    Bank reactions start life with this while they have no drawn sprites yet (a person replaces it later through Generate more).
    Pure numpy / OpenCV."""
    px = int(px)
    if px < 8:
        raise ValueError("px must be at least 8")
    yy, xx = np.mgrid[0:px, 0:px].astype(np.float64)
    cx = cy = (px - 1) / 2.0
    dx, dy = xx - cx, yy - cy
    r = np.sqrt(dx * dx + dy * dy) / (px / 2.0)
    glow = np.clip(1.0 - r, 0.0, 1.0) ** 2.2
    arm = np.clip(1.0 - np.abs(dx) / (px * 0.045), 0.0, 1.0) * np.clip(1.0 - np.abs(dy) / (px * 0.42), 0.0, 1.0)
    arm = np.maximum(arm, np.clip(1.0 - np.abs(dy) / (px * 0.045), 0.0, 1.0) * np.clip(1.0 - np.abs(dx) / (px * 0.42), 0.0, 1.0))
    core = np.clip(1.0 - r / 0.16, 0.0, 1.0) ** 1.5
    alpha = np.clip(glow * 0.55 + arm * 0.75 + core, 0.0, 1.0)
    rgb = np.full((px, px, 3), 255.0)
    rgba = np.dstack([rgb, alpha * 255.0])
    return np.clip(rgba + 0.5, 0, 255).astype(np.uint8)
