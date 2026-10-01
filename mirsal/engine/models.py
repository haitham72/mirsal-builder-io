"""Engine contracts. Frozen as the Phase-03 superset (see `mvp milestones.md` C2–C5).

Pure data: no I/O, no framework imports.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StickerStatus(str, Enum):
    # Superset of mvp plan §36 and full plan §54. MVP emits PROCESSING / READY / FAILED.
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    VALIDATING = "VALIDATING"
    JUDGING = "JUDGING"
    READY = "READY"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class AnimationStatus(str, Enum):
    # full plan §156
    NOT_REQUESTED = "NOT_REQUESTED"
    QUEUED = "QUEUED"
    GENERATING = "GENERATING"
    PROCESSING = "PROCESSING"
    VALIDATING = "VALIDATING"
    READY = "READY"
    FAILED = "FAILED"


TERMINAL = {StickerStatus.READY, StickerStatus.APPROVED, StickerStatus.REJECTED, StickerStatus.FAILED}


class ChromaColor(str, Enum):
    GREEN = "green"
    BLUE = "blue"


class ChromaSpec(BaseModel):
    color: ChromaColor = ChromaColor.GREEN
    # Colour-difference key: key_channel - max(other channels), on a 0–255 scale.
    # >= threshold → fully transparent; <= threshold * soft_ratio → fully opaque; linear between.
    threshold: int = Field(42, ge=1, le=255)
    soft_ratio: float = Field(0.5, gt=0, lt=1)


class GridSpec(BaseModel):
    rows: int = Field(3, ge=1)
    cols: int = Field(3, ge=1)


class PackInfo(BaseModel):
    name: str
    generation_id: str = "G001"


class StickerSpec(BaseModel):
    index: int = Field(ge=1)  # row-major: 1 2 3 / 4 5 6 / 7 8 9
    name: str  # display label, e.g. "dog barking"
    concept: str
    prompt: str
    emoji: list[str] = Field(min_length=1)  # Telegram: ≥1 emoji per sticker


class PackManifest(BaseModel):
    """The single required input manifest (replaces prompts.json + metadata.json — conflict C5)."""

    pack: PackInfo
    sheet_prompt: str | None = None  # the one prompt given to the image tool for the whole sheet
    video_prompt: str | None = None
    chroma: ChromaSpec = ChromaSpec()
    grid: GridSpec = GridSpec()
    animation_grid: GridSpec | None = None  # defaults to `grid` (decision Q2)
    stickers: list[StickerSpec]

    @model_validator(mode="after")
    def _check(self) -> "PackManifest":
        n = self.grid.rows * self.grid.cols
        idx = sorted(s.index for s in self.stickers)
        if idx != list(range(1, n + 1)):
            raise ValueError(f"stickers must have indices 1..{n} exactly once, got {idx}")
        return self

    @property
    def anim_grid(self) -> GridSpec:
        return self.animation_grid or self.grid

    def spec(self, index: int) -> StickerSpec:
        return next(s for s in self.stickers if s.index == index)

    def sticker_id(self, index: int) -> str:
        return f"{self.pack.generation_id}/S{index}"


class EngineConfig(BaseModel):
    sticker_size: int = 512
    occupancy_min: float = 0.65
    occupancy_target: float = 0.775  # linear: max(bbox_w, bbox_h) / sticker_size (conflict C11)
    occupancy_max: float = 0.85
    min_foreground_px: int = 400
    min_component_px: int = 64  # drop keying specks smaller than this; no erosion (mvp §24)
    edge_touch_px: int = 8  # foreground px on the cell border above this → crossed a gutter
    despill_band_px: int = 3
    heavy_upscale_warn: float = 2.0
    static_max_bytes: int = 512 * 1024
    # Telegram video profile (mvp §54)
    video_max_fps: float = 30.0
    video_max_duration: float = 3.0
    video_max_bytes: int = 256 * 1024
    crf_ladder: list[int] = [30, 38, 46, 54]  # bounded size loop — full plan §39


class Check(BaseModel):
    name: str
    ok: bool
    detail: str = ""


class Report(BaseModel):
    checks: list[Check] = []
    warnings: list[str] = []

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    @property
    def first_failure(self) -> str | None:
        return next((c.name for c in self.checks if not c.ok), None)

    def add(self, name: str, ok: bool, detail: str = "") -> bool:
        self.checks.append(Check(name=name, ok=bool(ok), detail=detail))
        return bool(ok)


class StickerResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    index: int
    sticker_id: str
    status: StickerStatus
    reason: str | None = None
    png: bytes | None = Field(default=None, repr=False)
    report: Report = Report()
    metrics: dict = {}


class AnimationResult(BaseModel):
    index: int
    sticker_id: str
    status: AnimationStatus
    reason: str | None = None
    webm: bytes | None = Field(default=None, repr=False)
    report: Report = Report()
    metrics: dict = {}
