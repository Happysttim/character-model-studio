"""Measure the local capture-to-segmentation input that SF3D receives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image

from character_model_studio.app.bootstrap import create_application_context
from character_model_studio.reconstruction.preprocessing import select_representative_frame
from character_model_studio.reconstruction.providers.rembg_segmentation import (
    RembgAnimeSegmentationProvider,
)
from character_model_studio.tools.real_workflow_smoke import _write_fixture_capture


def main() -> int:
    """Print non-sensitive alpha statistics for the local workflow fixture."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture")
    arguments = parser.parse_args()
    create_application_context()
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        capture = Path(arguments.capture) if arguments.capture else root / "capture.mp4"
        selected = root / "selected.png"
        foreground = root / "foreground.png"
        mask = root / "mask.png"
        if not arguments.capture:
            _write_fixture_capture(capture)
        select_representative_frame(capture, selected)
        provider = RembgAnimeSegmentationProvider()
        provider.load()
        try:
            provider.isolate(selected, foreground, mask)
        finally:
            provider.unload()
        with Image.open(mask) as image:
            alpha = np.asarray(image, dtype=np.uint8)
        nonzero = np.argwhere(alpha > 0)
        opaque = np.argwhere(alpha > 127)
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "alpha_range": [int(alpha.min()), int(alpha.max())],
                    "nonzero_pixels": int(nonzero.shape[0]),
                    "opaque_pixels": int(opaque.shape[0]),
                    "nonzero_bounds": _bounds(nonzero),
                    "opaque_bounds": _bounds(opaque),
                }
            )
        )
    return 0


def _bounds(points: np.ndarray) -> list[int] | None:
    if points.size == 0:
        return None
    minimum = points.min(axis=0)
    maximum = points.max(axis=0)
    return [int(minimum[1]), int(minimum[0]), int(maximum[1]), int(maximum[0])]


if __name__ == "__main__":
    raise SystemExit(main())
