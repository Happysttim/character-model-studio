"""Application-facing rigging provider contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from character_model_studio.app.capabilities import ProviderReadiness
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.rigging.models import RiggingProgress


class RiggingProvider(ABC):
    """A lazily loaded CUDA rigging provider; UI never imports model dependencies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable provider name."""

    @abstractmethod
    def probe(self) -> ProviderReadiness:
        """Report compatibility without loading heavyweight weights."""

    @abstractmethod
    def load(self) -> None:
        """Load provider resources on the serialized heavyweight lane."""

    @abstractmethod
    def unload(self) -> None:
        """Release provider resources before another heavyweight operation begins."""

    @abstractmethod
    def rig(
        self,
        model_relative_path: str,
        cancellation: CancellationToken,
        progress: Callable[[RiggingProgress], None] | None = None,
    ) -> str:
        """Create and return a project-relative rigged artifact path."""
