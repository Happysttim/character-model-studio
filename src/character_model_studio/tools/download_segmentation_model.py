"""Explicit user-invoked download command for local rembg segmentation models."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from character_model_studio.platform.windows.paths import resolve_application_paths
from character_model_studio.reconstruction.providers.rembg_segmentation import DEFAULT_MODEL_NAME


def main() -> int:
    """Download one selected rembg model into the configured local app cache."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default=os.environ.get("CHARACTER_MODEL_STUDIO_SEGMENTATION_MODEL", DEFAULT_MODEL_NAME),
    )
    arguments = parser.parse_args()
    paths = resolve_application_paths()
    paths.ensure_exists()
    cache_directory = Path(
        os.environ.setdefault("U2NET_HOME", str(paths.cache_directory / "segmentation" / "rembg"))
    )
    cache_directory.mkdir(parents=True, exist_ok=True)
    model_path = cache_directory / f"{arguments.model}.onnx"
    if not model_path.is_file():
        import onnxruntime as ort
        import torch
        from rembg import new_session

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is required to download and validate the segmentation model.")
        ort.preload_dlls()
        session_options = ort.SessionOptions()
        session_options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        new_session(
            arguments.model,
            sess_opts=session_options,
            providers=["CUDAExecutionProvider"],
        )
    if not model_path.is_file():
        raise RuntimeError("The requested segmentation model was not written to the local cache")
    print({"status": "PASS", "model": arguments.model, "bytes": model_path.stat().st_size})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
