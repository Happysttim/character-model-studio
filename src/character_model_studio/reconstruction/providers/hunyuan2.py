"""Hunyuan3D 2.0 Standard shape adapter for the single-process desktop app."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

from character_model_studio.app.capabilities import (
    ProviderReadiness,
    ReadinessStatus,
    probe_runtime,
)
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.reconstruction.interfaces import ReconstructionProvider
from character_model_studio.reconstruction.model_paths import (
    ShapeModelSnapshot,
    resolve_hunyuan3d_2_shape_snapshot,
)


class Hunyuan3D20Provider(ReconstructionProvider):
    """Lazy Hunyuan3D 2.0 adapter; shape-only unless Standard Texture is separately eligible."""

    name = "Hunyuan3D 2.0"
    version = "2.0.2"

    def __init__(self) -> None:
        self._pipeline: Any | None = None
        self._snapshot: ShapeModelSnapshot | None = None

    def probe(self) -> ProviderReadiness:
        """Report adapter/CUDA readiness without loading model weights."""
        runtime = probe_runtime()
        if runtime.standard.status is not ReadinessStatus.PROVIDER_RUNTIME_INCOMPATIBLE:
            return runtime.standard
        return ProviderReadiness(
            self.name,
            ReadinessStatus.READY,
            "Adapter is importable; model weights will be loaded on demand",
            True,
            True,
        )

    def load(self) -> None:
        """Load Hunyuan shape weights only on CUDA; CPU fallback is prohibited."""
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is unavailable; Hunyuan3D 2.0 will not fall back to CPU")
        snapshot = resolve_hunyuan3d_2_shape_snapshot()
        from hy3dgen.shapegen import (  # type: ignore[import-not-found]
            Hunyuan3DDiTFlowMatchingPipeline,
        )

        self._pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            str(snapshot.snapshot_path), device="cuda:0", dtype=torch.float16
        )
        self._snapshot = snapshot

    def unload(self) -> None:
        """Drop provider references and release cache for the next heavyweight owner."""
        self._pipeline = None
        self._snapshot = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def generate_shape(
        self, inputs: list[Path], output_path: Path, cancellation: CancellationToken
    ) -> Path:
        """Generate and export one canonical GLB using a selected representative frame."""
        if self._pipeline is None:
            raise RuntimeError("Hunyuan3D 2.0 is not loaded")
        if cancellation.is_cancelled:
            raise RuntimeError("Hunyuan3D 2.0 generation was cancelled before inference")
        if not inputs:
            raise ValueError("At least one representative input frame is required")
        from PIL import Image

        image = Image.open(inputs[0]).convert("RGBA")
        mesh = self._pipeline(image=image)[0]
        if cancellation.is_cancelled:
            raise RuntimeError("Hunyuan3D 2.0 generation was cancelled before publishing output")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(output_path)
        return output_path
