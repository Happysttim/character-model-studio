"""Experimental local Stable Fast 3D textured reconstruction provider."""

from __future__ import annotations

import gc
import os
import sys
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import torch
import yaml  # type: ignore[import-untyped]
from PIL import Image

from character_model_studio.app.capabilities import (
    ProviderReadiness,
    ReadinessStatus,
    probe_runtime,
)
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.platform.windows.paths import resolve_application_paths
from character_model_studio.reconstruction.interfaces import ReconstructionProvider


class StableFast3DProvider(ReconstructionProvider):
    """Local-only SF3D adapter that emits a textured GLB from one isolated image."""

    name = "Stable Fast 3D"
    version = "upstream-local-experimental"

    def __init__(self) -> None:
        self._model: Any | None = None
        self._model_directory, self._dino_directory, self._source_directory = _paths()

    def probe(self) -> ProviderReadiness:
        return probe_runtime().sf3d

    def load(self) -> None:
        readiness = self.probe()
        if readiness.status is not ReadinessStatus.READY:
            raise RuntimeError(f"Stable Fast 3D is unavailable: {readiness.reason}")
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is unavailable; Stable Fast 3D will not fall back to CPU")
        _configure_offline_cache()
        sys.path.insert(0, str(self._source_directory))
        from sf3d.system import SF3D  # type: ignore[import-not-found]

        with TemporaryDirectory(dir=self._model_directory.parent) as temporary:
            runtime_directory = _runtime_model_directory(
                Path(temporary), self._model_directory, self._dino_directory
            )
            self._model = SF3D.from_pretrained(
                str(runtime_directory), config_name="config.yaml", weight_name="model.safetensors"
            )
        self._model.to("cuda:0")
        self._model.eval()
        if str(next(self._model.parameters()).device) != "cuda:0":
            raise RuntimeError("Stable Fast 3D parameters were not loaded on cuda:0")

    def unload(self) -> None:
        self._model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def generate_shape(
        self,
        inputs: list[Path],
        output_path: Path,
        cancellation: CancellationToken,
        progress: Callable[[str, int, int], None] | None = None,
    ) -> Path:
        if self._model is None:
            raise RuntimeError("Stable Fast 3D is not loaded")
        if not inputs:
            raise ValueError("Stable Fast 3D requires one isolated RGBA input")
        if cancellation.is_cancelled:
            raise RuntimeError("Stable Fast 3D generation was cancelled before inference")
        from sf3d.utils import resize_foreground  # type: ignore[import-not-found]

        if progress is not None:
            progress("sf3d_geometry", 0, 2)
        with (
            Image.open(inputs[0]) as image,
            torch.no_grad(),
            torch.autocast(device_type="cuda", dtype=torch.bfloat16),
        ):
            mesh, _ = self._model.run_image(
                resize_foreground(_normalize_alpha(image.convert("RGBA")), 0.85),
                bake_resolution=1024,
                remesh="none",
            )
        if cancellation.is_cancelled:
            raise RuntimeError("Stable Fast 3D generation was cancelled before publishing output")
        if progress is not None:
            progress("sf3d_texture", 1, 2)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(output_path, include_normals=True)
        if progress is not None:
            progress("sf3d_texture", 2, 2)
        return output_path


def _paths() -> tuple[Path, Path, Path]:
    paths = resolve_application_paths()
    cache = paths.cache_directory / "sf3d"
    project_root = Path(__file__).resolve().parents[4]
    return (
        Path(os.environ.get("CHARACTER_MODEL_STUDIO_SF3D_MODEL_DIR", cache / "stable-fast-3d")),
        Path(os.environ.get("CHARACTER_MODEL_STUDIO_SF3D_DINO_DIR", cache / "dinov2-large")),
        Path(
            os.environ.get(
                "CHARACTER_MODEL_STUDIO_SF3D_SOURCE_DIR", project_root / "external" / "StableFast3D"
            )
        ),
    )


def _configure_offline_cache() -> None:
    paths = resolve_application_paths()
    os.environ["HF_HOME"] = str(paths.cache_directory / "huggingface")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"


def _runtime_model_directory(root: Path, model_directory: Path, dino_directory: Path) -> Path:
    config = yaml.safe_load((model_directory / "config.yaml").read_text(encoding="utf-8"))
    config["image_tokenizer"]["pretrained_model_name_or_path"] = str(dino_directory)
    directory = root / "model"
    directory.mkdir()
    (directory / "config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    (directory / "model.safetensors").hardlink_to(model_directory / "model.safetensors")
    return directory


def _normalize_alpha(image: Image.Image) -> Image.Image:
    """Convert soft segmentation confidence into SF3D's explicit foreground mask."""
    alpha = image.getchannel("A")
    extrema = alpha.getextrema()
    maximum = extrema[1] if isinstance(extrema, tuple) else None
    if not isinstance(maximum, (int, float)) or maximum == 0:
        raise RuntimeError("SF3D requires a non-empty isolated character mask")
    maximum = int(maximum)
    threshold = max(16, round(maximum * 0.35))
    mask = alpha.point(lambda value: 255 if value >= threshold else 0)
    if mask.getbbox() is None:
        raise RuntimeError("SF3D character mask is too weak after normalization")
    normalized = image.copy()
    normalized.putalpha(mask)
    return normalized
