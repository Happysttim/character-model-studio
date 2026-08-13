"""Background-safe import of an existing local capture video."""

from __future__ import annotations

from pathlib import Path
from shutil import copy2

import cv2

from character_model_studio.capture.models import CaptureResult


def import_video(source: Path, destination: Path, thumbnail: Path) -> CaptureResult:
    """Copy a user-selected video and generate a representative thumbnail."""
    video = cv2.VideoCapture(str(source))
    if not video.isOpened():
        raise ValueError("The selected video could not be opened")
    try:
        frames = max(1, int(video.get(cv2.CAP_PROP_FRAME_COUNT)))
        fps = video.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video.set(cv2.CAP_PROP_POS_FRAMES, frames // 2)
        ok, frame = video.read()
    finally:
        video.release()
    if not ok or frame is None:
        raise ValueError("The selected video contains no decodable frame")
    destination.parent.mkdir(parents=True, exist_ok=True)
    copy2(source, destination)
    if not cv2.imwrite(str(thumbnail), frame):
        raise OSError("Could not create an import thumbnail")
    return CaptureResult(
        destination, thumbnail, round(frames * 1000 / fps), width, height, round(fps), frames
    )
