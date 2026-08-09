"""Camera preset actions for the embedded model viewer."""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class CameraPreset(StrEnum):
    """Named review camera positions."""

    FIT = "fit"
    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    THREE_QUARTER = "three_quarter"


def apply_camera_preset(plotter: Any, preset: CameraPreset) -> None:
    """Apply a named camera orientation through PyVista's camera helpers."""
    if preset is CameraPreset.FIT:
        plotter.reset_camera()
    elif preset is CameraPreset.FRONT:
        plotter.view_xz()
    elif preset is CameraPreset.BACK:
        plotter.view_xz(negative=True)
    elif preset is CameraPreset.LEFT:
        plotter.view_yz()
    elif preset is CameraPreset.RIGHT:
        plotter.view_yz(negative=True)
    elif preset is CameraPreset.TOP:
        plotter.view_xy()
    elif preset is CameraPreset.THREE_QUARTER:
        plotter.view_isometric()
    plotter.reset_camera_clipping_range()
    plotter.render()
