"""CUDA-only readiness adapter for an isolated local Instance-Rig runtime."""

from __future__ import annotations

from collections.abc import Callable

from character_model_studio.app.capabilities import (
    ProviderReadiness,
    ReadinessStatus,
    probe_runtime,
)
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.rigging.instance_rig_paths import resolve_instance_rig_paths
from character_model_studio.rigging.interfaces import RiggingProvider
from character_model_studio.rigging.models import RiggingProgress


class InstanceRigProvider(RiggingProvider):
    """Keep TensorFlow CPU execution from being misrepresented as GPU auto-rigging."""

    @property
    def name(self) -> str:
        return "Instance-Rig"

    def probe(self) -> ProviderReadiness:
        paths = resolve_instance_rig_paths()
        if not paths.source_directory.is_dir() or not paths.runtime_python.is_file():
            return ProviderReadiness(
                self.name,
                ReadinessStatus.NOT_INSTALLED,
                "Instance-Rig isolated source or Python runtime is missing.",
                False,
                False,
            )
        model = paths.model_cache / "bodypix-resnet50-s16-480x640" / "saved_model.pb"
        if not model.is_file():
            return ProviderReadiness(
                self.name,
                ReadinessStatus.NOT_INSTALLED,
                "Instance-Rig BodyPix model is missing from the configured local cache.",
                True,
                False,
            )
        runtime = probe_runtime()
        if not runtime.gpu.cuda_available:
            return ProviderReadiness(
                self.name,
                ReadinessStatus.CUDA_UNAVAILABLE,
                "Instance-Rig must detect a CUDA TensorFlow device; CPU rigging is disabled.",
                True,
                False,
            )
        return ProviderReadiness(
            self.name,
            ReadinessStatus.PROVIDER_RUNTIME_INCOMPATIBLE,
            "The isolated Instance-Rig TensorFlow CUDA runtime has not passed a device smoke test.",
            True,
            True,
        )

    def load(self) -> None:
        readiness = self.probe()
        raise RuntimeError(f"{readiness.status}: {readiness.reason}")

    def unload(self) -> None:
        """No process is retained before a real CUDA smoke test passes."""

    def rig(
        self,
        model_relative_path: str,
        cancellation: CancellationToken,
        progress: Callable[[RiggingProgress], None] | None = None,
    ) -> str:
        del model_relative_path, cancellation, progress
        self.load()
        raise AssertionError("Instance-Rig load must raise until CUDA smoke passes")
