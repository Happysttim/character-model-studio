"""Capture domain objects independent of Qt and capture backends."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PhysicalRegion:
    """A rectangular capture area in physical desktop pixels."""

    left: int
    top: int
    width: int
    height: int
    monitor_id: str

    @property
    def right(self) -> int:
        """Return the exclusive right boundary."""
        return self.left + self.width

    @property
    def bottom(self) -> int:
        """Return the exclusive bottom boundary."""
        return self.top + self.height


@dataclass(frozen=True, slots=True)
class CaptureSettings:
    """User-visible recording settings for the MVP."""

    fps: int = 30
    codec: str = "h264"


@dataclass(frozen=True, slots=True)
class CaptureResult:
    """Finalized local capture artifacts and measured metadata."""

    video_path: Path
    thumbnail_path: Path
    duration_ms: int
    width: int
    height: int
    fps: int
    frame_count: int
