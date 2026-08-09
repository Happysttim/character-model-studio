"""Application-facing reconstruction provider contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from character_model_studio.app.capabilities import ProviderReadiness
from character_model_studio.common.cancellation import CancellationToken


class ReconstructionProvider(ABC):
    """A lazily loaded CUDA reconstruction provider; never called from widgets."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable provider name."""

    @abstractmethod
    def probe(self) -> ProviderReadiness:
        """Return runtime readiness without loading heavyweight weights."""

    @abstractmethod
    def load(self) -> None:
        """Load provider resources on the heavyweight task lane."""

    @abstractmethod
    def unload(self) -> None:
        """Release provider resources and CUDA cache when safe."""

    @abstractmethod
    def generate_shape(
        self, inputs: list[Path], output_path: Path, cancellation: CancellationToken
    ) -> Path:
        """Generate a model artifact and return its project-relative path."""
