"""Provisional word timings for a script that has no voiceover yet: the plates can be built and
previewed before the read exists.

Reads SCRIPT from align_vo.py (one source for the script) and times every word at a launch pace:
a word lasts by its letters, a comma or a dash is a short pause, the end of a sentence a longer one, and
a new plate (a `# comment` in SCRIPT) a longer one still. Writes data/lyrics.json and data/audio.json in
the same shapes align_vo.py and audio_vo.py write, with flat loudness envelopes.

When the real voiceover arrives, run align_vo.py and audio_vo.py: they overwrite both files and every
plate re-times itself (plates find their words by content, never by seconds).

    uv run --no-project python analysis/approx_vo.py
"""
import ast, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FPS = 100
src = (ROOT / "analysis" / "align_vo.py").read_text(encoding="utf-8")

# SCRIPT's lines, and which of them open a new plate (a comment right before them)
start = src.index("SCRIPT = [")
body = src[start: src.index("\n]", start) + 2]
script = ast.literal_eval(body.split("=", 1)[1].strip())
plate_breaks, seen_comment, k = set(), False, 0
for raw in body.splitlines()[1:]:
    s = raw.strip()
    if s.startswith("#"):
        seen_comment = True
    elif s.startswith('"'):
        if seen_comment and k:
            plate_breaks.add(k)
        seen_comment, k = False, k + 1

t, lines = 0.35, []
for i, text in enumerate(script):
    if i:
        t += 0.75 if i in plate_breaks else 0.38
    words = []
    for tok in text.split():
        if tok == "—":  # a pause, shown as its own token
            words.append({"w": tok, "start": round(t, 3), "end": round(t + 0.12, 3)})
            t += 0.16
            continue
        letters = len(re.sub(r"[^A-Za-z0-9]", "", tok))
        d = 0.11 + 0.052 * letters
        words.append({"w": tok, "start": round(t, 3), "end": round(t + d, 3)})
        t += d + 0.035
        if re.search(r"[.?!…]”?$", tok):
            t += 0.3
        elif re.search(r"[,:;]”?$", tok):
            t += 0.14
    lines.append({"text": text, "start": words[0]["start"], "end": words[-1]["end"], "words": words})

dur = round(lines[-1]["end"] + 1.2, 3)
(ROOT / "data" / "lyrics.json").write_text(json.dumps({"source": "approx_vo.py (provisional, no voiceover)", "lines": lines}, indent=1, ensure_ascii=False), encoding="utf-8")

n = int(dur * FPS) + 1
env = [0.0] * n
for l in lines:
    for w in l["words"]:
        for f in range(int(w["start"] * FPS), min(n, int(w["end"] * FPS))):
            env[f] = 0.7
period = 0.5
beats = [round(i * period, 3) for i in range(int(dur / period) + 1)]
out = {
    "duration": dur, "bpm": 120.0, "beat_period": period, "time_signature": 4,
    "beats": beats, "downbeats": beats[::4],
    "sections": [{"name": f"l{i}", "start": l["start"], "end": l["end"]} for i, l in enumerate(lines)],
    "fps": FPS,
    "rms": env, "vocal": env, "low": env, "mid": env, "high": env,
    "drums": [0.0] * n, "bass": [0.0] * n, "other": [0.0] * n,
    "onsets": {"vocal": [[w["start"], 0.7] for l in lines for w in l["words"]], "kick": [[l["start"], 1.0] for l in lines], "snare": [], "hat": []},
    "notes": "PROVISIONAL (approx_vo.py): no voiceover yet; replace with align_vo.py + audio_vo.py.",
}
(ROOT / "data" / "audio.json").write_text(json.dumps(out), encoding="utf-8")
print(f"provisional: {len(lines)} lines, {sum(len(l['words']) for l in lines)} words, {dur:.2f} s, plate breaks before lines {sorted(plate_breaks)}")
