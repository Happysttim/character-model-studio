"""Local capture-frame selection for the Standard reconstruction provider."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True, slots=True)
class FrameSelection:
    """A normalized representative input and auditable frame-selection metrics."""

    source_frame_index: int
    source_timestamp_ms: int
    sharpness: float
    output_path: Path


def select_representative_frame(capture_path: Path, output_path: Path) -> FrameSelection:
    """Sample a local video, select its sharpest candidate, and save a normalized PNG."""
    video = cv2.VideoCapture(str(capture_path))
    if not video.isOpened():
        raise ValueError("Capture video cannot be opened for local preprocessing")
    try:
        total_frames = max(int(video.get(cv2.CAP_PROP_FRAME_COUNT)), 1)
        fps = video.get(cv2.CAP_PROP_FPS) or 30.0
        sample_indices = sorted({round(i * (total_frames - 1) / 11) for i in range(12)})
        best: tuple[float, int, np.ndarray] | None = None
        for index in sample_indices:
            video.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = video.read()
            if not ok or frame is None:
                continue
            sharpness = float(
                cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
            )
            if best is None or sharpness > best[0]:
                best = (sharpness, index, frame)
        if best is None:
            raise ValueError("Capture video contained no decodable frame candidates")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        normalized = _normalize_frame(best[2])
        if not cv2.imwrite(str(output_path), normalized):
            raise OSError("Unable to write normalized reconstruction input")
        return FrameSelection(
            source_frame_index=best[1],
            source_timestamp_ms=round(best[1] * 1000 / fps),
            sharpness=best[0],
            output_path=output_path,
        )
    finally:
        video.release()


def _normalize_frame(frame: np.ndarray) -> np.ndarray:
    """Center-crop to a square then resize to the provider's configured RGB input size."""
    height, width = frame.shape[:2]
    edge = min(height, width)
    top, left = (height - edge) // 2, (width - edge) // 2
    cropped = frame[top : top + edge, left : left + edge]
    return cv2.resize(cropped, (512, 512), interpolation=cv2.INTER_AREA)
