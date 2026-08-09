"""Local capture-frame extraction and character-completeness selection."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True, slots=True)
class FrameSelection:
    """A normalized representative input and auditable frame-selection metrics."""

    source_frame_index: int
    source_timestamp_ms: int
    sharpness: float
    output_path: Path


def extract_candidate_frames(capture_path: Path, output_directory: Path) -> list[FrameSelection]:
    """Extract evenly spaced, aspect-preserved candidate frames from a local capture."""
    video = cv2.VideoCapture(str(capture_path))
    if not video.isOpened():
        raise ValueError("Capture video cannot be opened for local preprocessing")
    try:
        total_frames = max(int(video.get(cv2.CAP_PROP_FRAME_COUNT)), 1)
        fps = video.get(cv2.CAP_PROP_FPS) or 30.0
        sample_indices = sorted({round(i * (total_frames - 1) / 11) for i in range(12)})
        candidates: list[FrameSelection] = []
        output_directory.mkdir(parents=True, exist_ok=True)
        for sequence, index in enumerate(sample_indices):
            video.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = video.read()
            if not ok or frame is None:
                continue
            output_path = output_directory / f"candidate-{sequence:02d}.png"
            if not cv2.imwrite(str(output_path), _normalize_frame(frame)):
                raise OSError("Unable to write normalized reconstruction input")
            sharpness = float(
                cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
            )
            candidates.append(
                FrameSelection(index, round(index * 1000 / fps), sharpness, output_path)
            )
        if not candidates:
            raise ValueError("Capture video contained no decodable frame candidates")
        return candidates
    finally:
        video.release()


def select_complete_character_frame(
    candidates: list[FrameSelection], mask_paths: list[Path]
) -> FrameSelection:
    """Prefer a sharp subject mask that is not clipped by a capture edge."""
    if len(candidates) != len(mask_paths) or not candidates:
        raise ValueError("Frame candidates and segmentation masks must be non-empty and aligned")
    sharpness_scale = max(candidate.sharpness for candidate in candidates) or 1.0
    ranked: list[tuple[float, FrameSelection]] = []
    for candidate, mask_path in zip(candidates, mask_paths, strict=True):
        mask = np.asarray(Image.open(mask_path).convert("L"), dtype=np.uint8)
        completeness = _mask_completeness(mask)
        sharpness = candidate.sharpness / sharpness_scale
        ranked.append((completeness * 100.0 + sharpness, candidate))
    return max(ranked, key=lambda item: item[0])[1]


def with_output_path(selection: FrameSelection, output_path: Path) -> FrameSelection:
    """Return selected provenance with its stable attempt-artifact path."""
    return replace(selection, output_path=output_path)


def select_representative_frame(capture_path: Path, output_path: Path) -> FrameSelection:
    """Compatibility helper that selects the sharpest aspect-preserved candidate."""
    candidates = extract_candidate_frames(capture_path, output_path.parent / "candidates")
    selected = max(candidates, key=lambda candidate: candidate.sharpness)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(selected.output_path.read_bytes())
    return with_output_path(selected, output_path)


def _mask_completeness(mask: np.ndarray) -> float:
    """Score subject coverage while heavily penalizing masks touching capture edges."""
    foreground = mask >= 32
    rows, columns = np.where(foreground)
    if len(rows) == 0:
        return -10.0
    height, width = mask.shape[:2]
    top, bottom = int(rows.min()), int(rows.max())
    left, right = int(columns.min()), int(columns.max())
    border = max(3, round(min(height, width) * 0.02))
    edge_contacts = sum(
        (
            top <= border,
            bottom >= height - border - 1,
            left <= border,
            right >= width - border - 1,
        )
    )
    vertical_coverage = (bottom - top + 1) / height
    area_coverage = float(foreground.mean())
    return float(vertical_coverage + area_coverage - edge_contacts * 0.75)


def _normalize_frame(frame: np.ndarray) -> np.ndarray:
    """Letterbox to the provider input size without discarding a tall character."""
    height, width = frame.shape[:2]
    scale = min(512 / width, 512 / height)
    resized = cv2.resize(
        frame,
        (max(1, round(width * scale)), max(1, round(height * scale))),
        interpolation=cv2.INTER_AREA,
    )
    canvas = np.zeros((512, 512, 3), dtype=np.uint8)
    top = (512 - resized.shape[0]) // 2
    left = (512 - resized.shape[1]) // 2
    canvas[top : top + resized.shape[0], left : left + resized.shape[1]] = resized
    return canvas
