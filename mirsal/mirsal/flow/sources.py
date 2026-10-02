"""PhaseDirSource: discovers Haitham's prepared inputs by the inputs/ naming convention (read-only, never renames).

  Images_gen/img-NNN-<subject>/<file>.jpg            one folder per variant; NNN is the variant's folder number
  videos_gen/vid-NNN-<subject>/<file>.mp4            the 3x3 video of the SAME NNN
  videos_gen/vid-NNN-<subject>/slices/{quicktime,webm}/<anything> (n).<ext>    pre-sliced clips, n = grid cell 1..9
Optional hand-written prompts: "<sheet file name>.json" beside the sheet, or "<folder>/prompts.json".
All variants of one subject are ordered by folder number (then by take number inside a folder)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VID_EXT = {".mp4", ".mov", ".webm", ".mkv"}
CLIP_EXT = {".mov": "mov", ".webm": "webm", ".mp4": "mp4"}
DIR_RE = re.compile(r"^(img|vid)-(\d{3})-(.+)$")
TAKE_RE = re.compile(r"\((\d+)\)")
CLIP_RE = re.compile(r"\((\d+)\)$")


@dataclass
class Pick:
    subject: str            # teddy_bear
    subject_id: str         # folder number of this variant, e.g. 002
    variant: int            # 1-based over ALL folders of the subject
    n_variants: int
    sheet: Path
    video: Path | None      # the 3x3 mp4, if any
    plan: Path | None = None
    pairing: str = "folder"  # folder = same NNN folder number | number = same (K) | order = GUESSED by position | none
    clips: dict = field(default_factory=dict)   # {cell: {"mov": Path, "webm": Path}} pre-sliced clips
    clips_dup_of: str | None = None              # folder number whose clips these are copies of (then ignored)

    @property
    def has_video(self) -> bool:
        return bool(self.video or self.clips)


def take_of(f: Path) -> int | None:
    m = TAKE_RE.search(f.stem)
    return int(m[1]) if m else None


def _files(folder: Path | None, exts) -> list[Path]:
    if not folder:
        return []
    fs = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in exts]
    return sorted(fs, key=lambda f: (take_of(f) or 0, f.name))


def _plan_for(sheet: Path) -> Path | None:
    for c in (sheet.with_suffix(".json"), sheet.parent / "prompts.json"):
        if c.is_file():
            return c
    return None


def _clips_for(vdir: Path | None) -> dict:
    out: dict = {}
    root = vdir / "slices" if vdir else None
    if not root or not root.is_dir():
        return out
    for f in sorted(root.rglob("*")):
        m = CLIP_RE.search(f.stem)
        if f.is_file() and f.suffix.lower() in CLIP_EXT and m and 1 <= int(m[1]) <= 9:
            out.setdefault(int(m[1]), {}).setdefault(CLIP_EXT[f.suffix.lower()], f)
    return out


def _clip_fingerprint(clips: dict) -> tuple:
    """File sizes per cell/format (stat only). A clip set copied from another variant has the same fingerprint."""
    return tuple(sorted((n, f, p.stat().st_size) for n, d in clips.items() for f, p in d.items()))


def scan(root: Path) -> dict[str, list[Pick]]:
    """{subject: [Pick per variant]} - filenames only, never opens media."""
    folders: dict = {}
    for kind, sub in (("img", "Images_gen"), ("vid", "videos_gen")):
        base = root / sub
        if base.is_dir():
            for d in sorted(base.iterdir()):
                m = DIR_RE.match(d.name)
                if d.is_dir() and m and m[1] == kind:
                    folders.setdefault((m[3], m[2]), {})[kind] = d
    out: dict[str, list[Pick]] = {}
    for (subject, sid), v in sorted(folders.items()):
        imgs, vids, clips = _files(v.get("img"), IMG_EXT), _files(v.get("vid"), VID_EXT), _clips_for(v.get("vid"))
        vby = {take_of(x): x for x in vids if take_of(x) is not None}
        for n, img in enumerate(imgs):
            if len(imgs) == 1 and len(vids) <= 1:
                video, pairing = (vids[0] if vids else None), ("folder" if (vids or clips) else "none")
            elif vby and set(vby) <= {take_of(i) for i in imgs}:
                video, pairing = vby.get(take_of(img)), "number"
            else:
                video, pairing = (vids[n] if n < len(vids) else None), ("order" if vids else "none")
            out.setdefault(subject, []).append(Pick(subject, sid, 0, 0, img, video, _plan_for(img), pairing, clips))
    for picks in out.values():
        seen: dict = {}
        for i, p in enumerate(picks):
            p.variant, p.n_variants = i + 1, len(picks)
            if p.clips:
                fp = _clip_fingerprint(p.clips)
                if fp in seen and seen[fp] != p.subject_id:
                    # copies of another variant's clips would animate the wrong stickers: use this variant's own mp4
                    p.clips, p.clips_dup_of = {}, seen[fp]
                else:
                    seen.setdefault(fp, p.subject_id)
    return out


def find(root: Path, prompt: str, variant: int = 1) -> Pick | None:
    words = set(re.findall(r"[a-z0-9]+", prompt.lower()))
    words |= {w.rstrip("s") for w in words}
    best, best_score = None, 0
    for subject, picks in scan(root).items():
        score = len(set(subject.split("_")) & words)
        if picks and score > best_score:
            best, best_score = picks, score
    return best[min(max(variant, 1), len(best)) - 1] if best else None


def variant_of(root: Path, subject: str, variant: int) -> Pick | None:
    picks = scan(root).get(subject, [])
    return picks[variant - 1] if 0 < variant <= len(picks) else None


def known_subjects(root: Path) -> list[str]:
    return sorted(scan(root))
