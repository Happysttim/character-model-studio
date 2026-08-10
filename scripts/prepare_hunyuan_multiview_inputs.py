"""Create CUDA-segmented, time-diverse multiview inputs from a local capture."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import cv2
import numpy as np

from character_model_studio.reconstruction.preprocessing import _mask_completeness, _normalize_frame
from character_model_studio.reconstruction.providers.rembg_segmentation import (
    RembgAnimeSegmentationProvider,
)

VIEW_NAMES = ("front", "left", "back", "right")


def parse_args() -> argparse.Namespace:
    """Parse local input and output locations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--segmentation-cache", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    """Extract and isolate one representative frame for each expected view sector."""
    args = parse_args()
    if args.samples < len(VIEW_NAMES):
        raise ValueError("At least four samples are required for multiview selection")
    if not args.capture.is_file():
        raise FileNotFoundError(f"Capture does not exist: {args.capture}")

    os.environ["U2NET_HOME"] = str(args.segmentation_cache.resolve())
    candidates_directory = args.output_directory / "candidates"
    isolated_directory = args.output_directory / "isolated"
    args.output_directory.mkdir(parents=True, exist_ok=True)

    candidates = extract_frames(args.capture, candidates_directory, args.samples)
    provider = RembgAnimeSegmentationProvider()
    provider.load()
    try:
        for candidate in candidates:
            candidate_path = Path(candidate["path"])
            isolated_path = isolated_directory / f"{candidate_path.stem}-rgba.png"
            mask_path = isolated_directory / f"{candidate_path.stem}-mask.png"
            provider.isolate(candidate_path, isolated_path, mask_path)
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if mask is None:
                raise RuntimeError(f"Unable to read generated alpha mask: {mask_path}")
            candidate["isolated_path"] = str(isolated_path)
            candidate["mask_path"] = str(mask_path)
            candidate["completeness"] = _mask_completeness(mask)
    finally:
        provider.unload()

    selected = select_views(candidates)
    views: list[dict[str, object]] = []
    for view_name, candidate in zip(VIEW_NAMES, selected, strict=True):
        source = Path(str(candidate["isolated_path"]))
        destination = args.output_directory / f"{view_name}.png"
        destination.write_bytes(source.read_bytes())
        views.append({"view": view_name, **candidate, "path": str(destination)})

    report = {
        "capture": str(args.capture.resolve()),
        "selection_assumption": "capture begins front-ish and rotates consistently leftward",
        "segmentation_provider": provider.name,
        "segmentation_model": provider.model_name,
        "views": views,
    }
    (args.output_directory / "selection.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


def extract_frames(capture: Path, output_directory: Path, samples: int) -> list[dict[str, object]]:
    """Extract aspect-preserved frames and record auditable source timings."""
    video = cv2.VideoCapture(str(capture))
    if not video.isOpened():
        raise ValueError("Capture video cannot be opened")
    try:
        frame_count = max(1, int(video.get(cv2.CAP_PROP_FRAME_COUNT)))
        fps = video.get(cv2.CAP_PROP_FPS) or 30.0
        indices = sorted({round(i * (frame_count - 1) / (samples - 1)) for i in range(samples)})
        output_directory.mkdir(parents=True, exist_ok=True)
        frames: list[dict[str, object]] = []
        for sequence, frame_index in enumerate(indices):
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = video.read()
            if not ok or frame is None:
                continue
            output_path = output_directory / f"candidate-{sequence:02d}.png"
            if not cv2.imwrite(str(output_path), _normalize_frame(frame)):
                raise OSError(f"Unable to write frame: {output_path}")
            grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            sharpness = float(cv2.Laplacian(grayscale, cv2.CV_64F).var())
            frames.append(
                {
                    "path": str(output_path),
                    "frame_index": frame_index,
                    "timestamp_ms": round(frame_index * 1000 / fps),
                    "sharpness": sharpness,
                }
            )
        if len(frames) < len(VIEW_NAMES):
            raise ValueError("Capture did not yield enough decodable frames")
        return frames
    finally:
        video.release()


def select_views(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    """Select the most complete/sharp subject from each temporal view sector."""
    groups = np.array_split(np.arange(len(candidates)), len(VIEW_NAMES))
    selected: list[dict[str, object]] = []
    sharpness_max = max(float(candidate["sharpness"]) for candidate in candidates) or 1.0
    for group in groups:
        sector = [candidates[int(index)] for index in group]
        selected.append(
            max(
                sector,
                key=lambda candidate: (
                    float(candidate["completeness"]) * 100.0
                    + float(candidate["sharpness"]) / sharpness_max
                ),
            )
        )
    return selected


if __name__ == "__main__":
    main()
