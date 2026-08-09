"""DPI-aware region geometry for the one-monitor reconstruction MVP."""

from __future__ import annotations

from dataclasses import dataclass

from character_model_studio.capture.models import PhysicalRegion

MIN_CAPTURE_DIMENSION = 160


@dataclass(frozen=True, slots=True)
class LogicalRect:
    """Qt logical-pixel rectangle."""

    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class MonitorGeometry:
    """Logical monitor bounds and its Windows scale factor."""

    monitor_id: str
    x: float
    y: float
    width: float
    height: float
    device_pixel_ratio: float


def to_physical_region(selection: LogicalRect, monitor: MonitorGeometry) -> PhysicalRegion:
    """Convert an in-monitor logical selection to physical capture coordinates."""
    if not _contained(selection, monitor):
        raise ValueError("Capture selection must remain on one monitor")
    scale = monitor.device_pixel_ratio
    width = round(selection.width * scale)
    height = round(selection.height * scale)
    if width < MIN_CAPTURE_DIMENSION or height < MIN_CAPTURE_DIMENSION:
        raise ValueError(f"Capture region must be at least {MIN_CAPTURE_DIMENSION} physical pixels")
    return PhysicalRegion(
        left=round((selection.x - monitor.x) * scale),
        top=round((selection.y - monitor.y) * scale),
        width=width,
        height=height,
        monitor_id=monitor.monitor_id,
    )


def _contained(selection: LogicalRect, monitor: MonitorGeometry) -> bool:
    return (
        selection.x >= monitor.x
        and selection.y >= monitor.y
        and selection.x + selection.width <= monitor.x + monitor.width
        and selection.y + selection.height <= monitor.y + monitor.height
    )
