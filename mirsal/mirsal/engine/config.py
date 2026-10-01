from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class EngineConfig:
    size: int = 512
    fit: float = 0.775            # target: longest side / size
    max_fit: float = 0.85         # never exceed this
    outline_px: int = 12          # 0 disables the white die-cut outline
    chroma: str = "green"         # "green" | "blue"
    threshold: int | None = None  # None = auto-calibrate from the border ring
    border_px: int = 4
    min_component_px: int = 64
    min_foreground_px: int = 400
    edge_touch_px: int = 8
    despill_band_px: int = 3
    static_max_bytes: int = 512 * 1024
    video_max_fps: float = 30.0
    video_max_seconds: float = 3.0
    video_max_bytes: int = 256 * 1024
    crf_ladder: tuple = (30, 38, 46, 54, 60)
    loop_seam_max: float = 12.0     # absolute floor
    loop_seam_ratio: float = 1.5    # seam may be up to this x the clip's own frame-to-frame motion
    loop_fade_frames: int = 6
    clip_prefer: tuple = ("mov", "webm")   # pre-sliced clip formats, best first (ProRes 4444 has the cleanest alpha)
    clip_alpha_floor: int = 12               # alpha below this is haze (VP9 alpha leaves values 1-3) -> 0

    def to_dict(self) -> dict:
        return asdict(self)
