"""CUDA-only local character-background isolation through rembg isnet-anime."""

from __future__ import annotations

import os
from gc import collect
from pathlib import Path
from typing import Any

from PIL import Image

from character_model_studio.app.capabilities import (
    ProviderReadiness,
    ReadinessStatus,
    probe_runtime,
)
from character_model_studio.reconstruction.interfaces import SegmentationProvider

DEFAULT_MODEL_NAME = "isnet-anime"
MODEL_NAME_ENV = "CHARACTER_MODEL_STUDIO_SEGMENTATION_MODEL"


class RembgAnimeSegmentationProvider(SegmentationProvider):
    """Use a locally cached isnet-anime ONNX model without CPU fallback."""

    name = "rembg isnet-anime"

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or os.environ.get(MODEL_NAME_ENV, DEFAULT_MODEL_NAME)
        self._session: Any | None = None

    @property
    def model_name(self) -> str:
        """Return the configured model identifier without exposing a machine path."""
        return self._model_name

    def probe(self) -> ProviderReadiness:
        """Expose the inexpensive startup readiness result for this provider."""
        return probe_runtime().segmentation

    def load(self) -> None:
        """Create a CUDAExecutionProvider session only from an existing local model."""
        readiness = self.probe()
        if readiness.status is not ReadinessStatus.READY:
            raise RuntimeError(readiness.reason)
        model_path = self._model_path()
        if not model_path.is_file():
            raise RuntimeError("The selected local segmentation model has not been downloaded")

        # Importing PyTorch first exposes its CUDA/cuDNN DLLs to ONNX Runtime.
        import onnxruntime as ort
        import torch
        from rembg import new_session

        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is unavailable; background isolation will not fall back to CPU"
            )
        ort.preload_dlls()
        session_options = ort.SessionOptions()
        session_options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        session = new_session(
            self._model_name,
            sess_opts=session_options,
            providers=["CUDAExecutionProvider"],
        )
        providers = session.inner_session.get_providers()
        if not providers or providers[0] != "CUDAExecutionProvider":
            raise RuntimeError("ONNX Runtime did not initialize CUDAExecutionProvider")
        self._session = session

    def isolate(self, input_path: Path, output_path: Path, mask_path: Path) -> Path:
        """Save an RGBA foreground image and alpha mask as project-local artifacts."""
        if self._session is None:
            raise RuntimeError("The segmentation provider is not loaded")
        if not input_path.is_file():
            raise FileNotFoundError(f"Segmentation input does not exist: {input_path}")
        from rembg import remove

        with Image.open(input_path) as input_image:
            foreground = remove(input_image.convert("RGBA"), session=self._session)
        if foreground.mode != "RGBA":
            foreground = foreground.convert("RGBA")
        alpha = foreground.getchannel("A")
        extrema = alpha.getextrema()
        if extrema is None or extrema[1] == 0:
            raise RuntimeError("Background isolation produced an empty character mask")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mask_path.parent.mkdir(parents=True, exist_ok=True)
        foreground.save(output_path)
        alpha.save(mask_path)
        return output_path

    def unload(self) -> None:
        """Release the ONNX session before Hunyuan acquires the GPU."""
        self._session = None
        collect()
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def _model_path(self) -> Path:
        cache_directory = os.environ.get("U2NET_HOME")
        if not cache_directory:
            raise RuntimeError("The local segmentation cache directory is not configured")
        return Path(cache_directory) / f"{self._model_name}.onnx"
