"""The 30 s reel's sound: a 128 BPM track synthesised here, and the sound effects from audio/sfx/, both on the
same 64-beat grid the picture is cut to (app/src/scenes/reel.ts, B(n) = n * 60/128). Writes out/reel_mix.wav.

    uv run --no-project --with numpy --with scipy python analysis/reel_mix.py
    ffmpeg -i out/mirsal-reel-30s.mp4 -i out/reel_mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -af loudnorm=I=-14:TP=-1 -shortest out/mirsal-reel-30s_sound.mp4

A track from elsewhere (Suno) replaces the music: set MUSIC to its path (first downbeat at 0, 128 BPM).
"""
import subprocess
from pathlib import Path
import numpy as np
from scipy.signal import butter, lfilter

ROOT = Path(__file__).resolve().parent.parent
SR, BPM, OFFSET = 48000, 129.75, 0.22  # the Suno track's tempo and first beat (measured)
BEAT = 60 / BPM
DUR = 48.125  # the Suno track
N = int(DUR * SR) + SR  # a second of tail
MUSIC = ROOT / "audio" / "suno-48.mp3"  # None: the synthesised placeholder below
rng = np.random.default_rng(7)


def B(n):
    return OFFSET + n * BEAT


def S(t):
    return int(round(t * SR))


def lp(x, f, order=2):
    b, a = butter(order, min(0.99, f / (SR / 2)), "low")
    return lfilter(b, a, x)


def hp(x, f, order=2):
    b, a = butter(order, min(0.99, f / (SR / 2)), "high")
    return lfilter(b, a, x)


def add(buf, t, x, gain=1.0):
    i = S(t)
    if i >= len(buf) or i + len(x) <= 0:
        return
    j0 = max(0, -i)
    x = x[j0:]
    i = max(0, i)
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n] * gain


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ------------------------------------------------------------------ instruments
def kick():
    n = S(0.42); t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.28)
    click = rng.standard_normal(n) * np.exp(-t / 0.004) * 0.35
    return np.tanh(1.6 * (body + hp(click, 2000)))


def clap():
    n = S(0.3); t = np.arange(n) / SR
    env = np.zeros(n)
    for k, d in enumerate([0, 0.011, 0.022]):
        env += (t >= d) * np.exp(-np.maximum(0, t - d) / (0.006 if k < 2 else 0.11))
    x = hp(lp(rng.standard_normal(n), 6500), 900) * env
    return x / np.abs(x).max()


def hat(open_=False):
    n = S(0.3 if open_ else 0.06); t = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 7500, 4) * np.exp(-t / (0.09 if open_ else 0.018))
    return x / np.abs(x).max()


def saw(f, n, detune=(0.0,)):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in detune:
        ff = f * 2 ** (d / 1200)
        out += 2 * ((t * ff + rng.random()) % 1) - 1
    return out / len(detune)


def pluck(f, dur=0.22):
    n = S(dur + 0.25); t = np.arange(n) / SR
    x = saw(f, n, (-9, 0, 9)) * np.exp(-t / dur)
    cut = 600 + 5000 * np.exp(-t / 0.08)
    # a decaying low-pass, applied in a few blocks
    out = np.zeros(n); blk = S(0.02)
    for i in range(0, n, blk):
        out[i:i + blk] = lp(x[i:i + blk + 200], cut[i])[:len(out[i:i + blk])]
    return out


def bass(f, dur):
    n = S(dur); t = np.arange(n) / SR
    x = lp(saw(f, n, (-4, 4)) + 0.5 * np.sin(2 * np.pi * f * t), 380, 2)
    return x * np.minimum(1, t / 0.005) * np.exp(-t / (dur * 0.9))


def pad(fs, dur):
    n = S(dur); t = np.arange(n) / SR
    x = sum(saw(f, n, (-12, -4, 4, 12)) for f in fs) / len(fs)
    return lp(x, 1800, 2) * np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.6)


def riser(dur):
    n = S(dur); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n); blk = S(0.05)
    for i in range(0, n, blk):
        f = 300 + 9000 * (i / n) ** 2
        out[i:i + blk] = hp(noise[i:i + blk + 400], f)[:len(out[i:i + blk])]
    sweep = np.sin(2 * np.pi * np.cumsum(200 + 1400 * (t / dur) ** 2) / SR) * 0.25
    return (out + sweep) * (t / dur) ** 2


def impact():
    n = S(1.6); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 90 * np.exp(-t / 0.06)) / SR) * np.exp(-t / 0.5)
    crash = hp(rng.standard_normal(n), 3000) * np.exp(-t / 0.45) * 0.4
    return np.tanh(1.4 * (boom + crash))


# ------------------------------------------------------------------ the arrangement (beats)
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
drums = np.zeros(N); synth = np.zeros(N); bassb = np.zeros(N); fx = np.zeros(N)
K, C, HC, HO = kick(), clap(), hat(), hat(True)
full = lambda b: (8 <= b < 44) or (46 <= b < 56)  # the drops
for b16 in range(64 * 4):
    b = b16 / 4
    bar = int(b // 4); ch = CHORDS[bar % 4]
    if full(b):
        if b16 % 4 == 0: add(drums, B(b), K, 1.0)
        if b16 % 8 == 4: add(drums, B(b), C, 0.55)
        if b16 % 4 == 2: add(drums, B(b), HO, 0.16)
        add(drums, B(b), HC, 0.09 if b16 % 2 else 0.05)
        if b16 % 2 == 1: add(bassb, B(b), bass(midi(ch[0] - 24), BEAT / 2 * 0.95), 0.55)
    elif b < 8 or 56 <= b < 60:
        add(drums, B(b), HC, 0.05 if b16 % 2 else 0.03)
    # arpeggiated plucks everywhere except the build's last beat
    if not (59 <= b < 60):
        note = ch[[0, 1, 2, 1][b16 % 4]] + (12 if (b16 // 4) % 2 else 0)
        g = 0.13 if full(b) else 0.09
        add(synth, B(b), pluck(midi(note + 12)), g)
# snare rolls into the drops
for b0, b1 in [(6, 8), (57.5, 59.5)]:
    k = 0
    while B(b0) + k * BEAT / 4 < B(b1) - 1e-6:
        tb = B(b0) + k * BEAT / 4
        add(drums, tb, C, 0.2 + 0.4 * (tb - B(b0)) / (B(b1) - B(b0)))
        k += 1
# risers and impacts
add(fx, B(8) - B(4), riser(B(4)), 0.35)
add(fx, B(59.5) - B(3.5), riser(B(3.5)), 0.4)
add(fx, B(46) - B(2), riser(B(2)), 0.25)
for b in (8, 46, 59.5):
    add(fx, B(b), impact(), 0.5)
# the outro: a held chord, one last kick
add(synth, B(60), pad([midi(m + 12) for m in CHORDS[0]], B(4) + 0.6), 0.22)
add(drums, B(60), K, 1.0)
# the break before the second drop: pads instead of drums
add(synth, B(44), pad([midi(m + 12) for m in CHORDS[2]], B(2)), 0.18)

# sidechain: the synths duck under every kick of the drops
duck = np.ones(N)
for b in range(64):
    if full(b) or b == 60:
        i = S(B(b)); n = S(0.22)
        duck[i:i + n] = np.minimum(duck[i:i + n], 0.35 + 0.65 * (np.arange(min(n, N - i)) / n) ** 0.7)
music = drums * 0.9 + (synth + bassb) * duck + fx
music = hp(music, 28)

if MUSIC:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(MUSIC), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    m = np.frombuffer(raw, dtype=np.float32)[:N]
    music = np.zeros(N); music[:len(m)] = m

# ------------------------------------------------------------------ the sound effects, on the picture's beats
SFX = ROOT / "audio" / "sfx"
_cache = {}


def take(name, k=0):
    fs = sorted(SFX.glob(f"{name}_*.mp3"))
    f = fs[k % len(fs)]
    if f not in _cache:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype=np.float32).copy()
        _cache[f] = x / (np.abs(x).max() + 1e-9)
    return _cache[f]


PEAK = {"whoosh2", "whoosh_soft", "whoosh2"}
END = {"reverse_suck", "riser", "riser2"}
counter = {}


def cue(t, name, db, rate=1.0):
    k = counter.get(name, 0); counter[name] = k + 1
    x = take(name, k)
    if rate != 1.0:
        x = np.interp(np.arange(int(len(x) / rate)) * rate, np.arange(len(x)), x)
    if name in PEAK:
        env = np.convolve(np.abs(x), np.ones(960) / 960, mode="same"); off = int(np.argmax(env))
    elif name in END:
        off = len(x)
    else:
        idx = np.where(np.abs(x) > 0.5)[0]; off = max(0, int(idx[0]) - S(0.008)) if len(idx) else 0
    add(fx_sfx, t - off / SR, x, 10 ** (db / 20))


fx_sfx = np.zeros(N)
W = lambda b, db=-12: (cue(B(b) - 0.004, "slam", db), cue(B(b), "whoosh2", db - 5))  # a word card
# A. the chat box: typing, the send, the bubble (beats 0-8)
for i in range(32):
    cue(B(1) + (B(6.4) - B(1)) * i / 32, "key_click", -20 + (i % 3), rate=1 + 0.04 * ((i * 7) % 5 - 2))
for b in (2, 3, 5):
    cue(B(b), "whoosh_soft", -19)
W(4)
cue(B(6) + 0.18, "mouse_click", -10); cue(B(6) + 0.22, "sent", -10)
cue(B(7) + 0.12, "whoosh2", -12); cue(B(8), "riser2", -14)
# B. Mirsal AI at work, the sheet (beats 8-16)
cue(B(8), "impact2", -11); cue(B(8.5), "scan_sweep", -22)
cue(B(10), "whoosh_soft", -17); cue(B(10) + 0.05, "spark_zip", -21)
W(11)
cue(B(12), "impact2", -12); cue(B(12) + 0.02, "paper_slide", -15)
cue(B(13), "scan_sweep", -14)
# C. cut, cleaned, checked (beats 16-28)
cue(B(16), "falling_pieces", -16); cue(B(16), "snip", -12)
W(17)
for i in range(9):
    cue(B(18) + i * B(0.3), "pop2", -14, rate=1 + 0.05 * i)
    cue(B(18) + i * B(0.3) + 0.14, "pen_tick", -20)
W(21); cue(B(21) + 0.05, "chime2", -12)
cue(B(22), "stamp", -13)
cue(B(24), "scan_sweep", -18); cue(B(25.2), "chime2", -16)
cue(B(26), "whoosh_soft", -18)
# D. alive (beats 28-40)
for i in range(8):
    cue(B(28 + i * 0.5), "whoosh2", -16 - (i % 2) * 3)
    cue(B(28 + i * 0.5), "pop2", -22, rate=1 + 0.06 * (i % 4))
W(32); cue(B(34), "whoosh_soft", -16)
for i in range(4):
    cue(B(36 + i), "whoosh2", -17)
# E. particles (beats 40-52)
cue(B(41), "riser2", -15)
for b, db in [(41, -10), (42, -12), (43, -12), (44, -12), (45, -12), (46, -12), (47, -13), (47.25, -15), (47.5, -15), (48, -12), (49, -12), (50, -12), (51, -12)]:
    cue(B(b), "sparkle", db); cue(B(b) + 0.03, "falling_pieces", db - 7)
W(42)
# F. export to Mirsal, live (beats 52-60)
cue(B(53), "mouse_click", -9); cue(B(53) + 0.12, "whoosh2", -12); cue(B(53) + 0.75, "pop2", -10, rate=0.8)
cue(B(54), "whoosh_soft", -15); cue(B(54.4), "chime2", -10)
for i in range(9):
    cue(B(54.6) + i * B(0.125), "pop2", -17, rate=1 + 0.05 * i)
cue(B(56), "sent", -11)
for b in (56.6, 57, 57.4):
    cue(B(b), "pop2", -13, rate=1.2)
W(58)
# G. three at once, no dead ends (beats 60-72)
for j in range(3):
    cue(B(60 + j * 0.5), "whoosh2", -15)
    for i in range(9):
        cue(B(60 + j * 0.5) + 0.15 + i * 0.08, "pop2", -25, rate=1.1 + 0.03 * i)
cue(B(62.4), "chime2", -15)
W(63)
cue(B(64), "marker_strike", -15); cue(B(65.6), "mouse_click", -9); cue(B(65.6) + 0.08, "chime2", -10)
W(67)
for i in range(8):
    cue(B(68 + i * 0.25), "snip" if i % 2 else "pop2", -15)
for i in range(4):
    cue(B(70 + i * 0.5), "sparkle", -12); cue(B(70 + i * 0.5), "whoosh2", -18)
# H. taste, team, Trending, the words (beats 72-92)
cue(B(72), "whoosh_soft", -14)
for b in (72.4, 72.9, 73.4):
    for i in range(5):
        cue(B(b) + i * 0.05, "key_click", -23)
cue(B(74), "pop2", -12, rate=0.9)
cue(B(75), "whoosh2", -14)
for j in range(5):
    cue(B(75) + j * B(0.25), "pop2", -20, rate=1 + 0.04 * j)
cue(B(76.8), "mouse_click", -10); cue(B(76.8) + 0.08, "chime2", -11)
cue(B(78), "whoosh_soft", -14); cue(B(80.5), "pop2", -11, rate=1.25)
W(84); W(85); W(86); cue(B(86.2), "falling_pieces", -17)
for i in range(21):
    cue(B(88) + B(1.2) * i / 21, "key_click", -21)
cue(B(89.5), "sent", -12)
for i in range(9):
    cue(B(90) + i * B(0.125), "pop2", -18, rate=1 + 0.05 * i)
# I. the logo
cue(B(92), "whoosh_soft", -15)
cue(B(95.5), "riser2", -12); cue(B(95.5), "impact2", -9); cue(B(95.5), "sparkle", -13)
cue(B(96.5), "whoosh_soft", -17)
cue(B(100), "mouse_click", -9); cue(B(100) + 0.06, "chime2", -10)

# ------------------------------------------------------------------ the voice (Liam, ElevenLabs): one line per section
VO = [(None, 1), (8, 2), (16, 3), (28, 4), (40, 5), (52, 6), (60, 7), (72, 8), (96.6, 9)]  # (beat, audio/reel48-vo/lNN.mp3)
vo = np.zeros(N)
for b, k in VO:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ROOT / "audio" / "reel48-vo" / f"l{k:02d}.mp3"), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy(); x /= np.abs(x).max() + 1e-9
    env = np.convolve(np.abs(x), np.ones(480) / 480, mode="same")
    on = int(np.argmax(env > 0.08 * env.max()))
    t0 = 0.35 if b is None else B(b) + 0.1
    add(vo, t0 - on / SR, x, 1.0)
venv = np.convolve(np.abs(vo), np.ones(S(0.12)) / S(0.12), mode="same")
duckv = 1 - 0.45 * np.clip(venv / (venv.max() + 1e-9) * 4, 0, 1)

# ------------------------------------------------------------------ mix
mix = music * 0.55 * duckv + fx_sfx * 0.85 * (1 - 0.3 * (1 - duckv)) + vo * 0.95
mix = mix[: S(DUR + 0.4)]
fade = S(0.4); mix[-fade:] *= np.linspace(1, 0, fade)
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix /= np.abs(mix).max() / 0.89
stereo = np.stack([mix, mix], 1).astype(np.float32)
out = ROOT / "out" / "reel_mix.wav"
out.parent.mkdir(exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", str(out)], input=stereo.tobytes(), check=True)
print(f"wrote {out} ({len(mix) / SR:.2f} s, {sum(counter.values())} effect cues)")
