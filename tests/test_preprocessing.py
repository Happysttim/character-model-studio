"""Frame-selection tests for full-character capture handling."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from character_model_studio.reconstruction.preprocessing import (
    FrameSelection,
    _normalize_frame,
    select_complete_character_frame,
)


def test_select_complete_character_frame_penalizes_edge_clipped_mask(tmp_path: Path) -> None:
    masks: list[Path] = []
    for name, bounds in (("full", (30, 20, 480, 490)), ("clipped", (0, 40, 511, 470))):
        mask = np.zeros((512, 512), dtype=np.uint8)
        top, left, bottom, right = bounds
        mask[top:bottom, left:right] = 255
        path = tmp_path / f"{name}.png"
        Image.fromarray(mask).save(path)
        masks.append(path)
    candidates = [
        FrameSelection(0, 0, 100.0, tmp_path / "full-input.png"),
        FrameSelection(1, 33, 1_000.0, tmp_path / "clipped-input.png"),
    ]

    selected = select_complete_character_frame(candidates, masks)

    assert selected.source_frame_index == 0


def test_normalize_frame_letterboxes_tall_capture_without_center_cropping() -> None:
    frame = np.full((946, 322, 3), 200, dtype=np.uint8)

    normalized = _normalize_frame(frame)

    assert normalized.shape == (512, 512, 3)
    foreground = cv2.cvtColor(normalized, cv2.COLOR_BGR2GRAY) > 0
    rows, columns = np.where(foreground)
    assert rows.min() == 0 and rows.max() == 511
    assert columns.min() > 0 and columns.max() < 511
