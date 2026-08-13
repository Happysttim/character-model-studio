"""Optional isolated-runtime adapter for the official UniRig provider."""

from __future__ import annotations

from collections.abc import Callable

from character_model_studio.app.capabilities import (
    ProviderReadiness,
    ReadinessStatus,
    probe_runtime,
)
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.rigging.interfaces import RiggingProvider
from character_model_studio.rigging.models import RiggingProgress
from character_model_studio.rigging.unirig_paths import resolve_unirig_paths


class UniRigProvider(RiggingProvider):
    """Gate UniRig honestly until its isolated CUDA runtime and local checkpoints are ready.

    UniRig's upstream dependencies conflict with the reconstruction environment. The
    application therefore reserves an explicit child-runtime boundary for it instead
    of silently downgrading shared dependencies or using CPU fallback.
    """

    @property
    def name(self) -> str:
        return "UniRig"

    def probe(self) -> ProviderReadiness:
        runtime = probe_runtime()
        if not runtime.gpu.cuda_available:
            return ProviderReadiness(
                self.name, ReadinessStatus.CUDA_UNAVAILABLE, "CUDA is unavailable", False, False
            )
        if (runtime.gpu.total_vram_bytes or 0) < 8 * 1024**3:
            return ProviderReadiness(
                self.name,
                ReadinessStatus.VRAM_INELIGIBLE,
                "UniRig upstream requires at least 8 GiB of VRAM for generation.",
                False,
                False,
            )
        paths = resolve_unirig_paths()
        if not paths.source_directory.is_dir():
            return ProviderReadiness(
                self.name,
                ReadinessStatus.NOT_INSTALLED,
                "UniRig source checkout is missing.",
                False,
                True,
            )
        if not paths.runtime_python.is_file():
            return ProviderReadiness(
                self.name,
                ReadinessStatus.PROVIDER_RUNTIME_INCOMPATIBLE,
                "UniRig requires its configured isolated Python runtime; "
                "no shared-runtime install was attempted.",
                False,
                True,
            )
        if not any(paths.model_cache.rglob("*.ckpt")):
            return ProviderReadiness(
                self.name,
                ReadinessStatus.NOT_INSTALLED,
                "UniRig local checkpoints are missing; "
                "online downloads are disabled during inference.",
                True,
                True,
            )
        return ProviderReadiness(
            self.name,
            ReadinessStatus.PROVIDER_RUNTIME_INCOMPATIBLE,
            "The Windows isolated UniRig command adapter has not passed a CUDA smoke test.",
            True,
            True,
        )

    def load(self) -> None:
        readiness = self.probe()
        raise RuntimeError(f"{readiness.status}: {readiness.reason}")

    def unload(self) -> None:
        """No provider is loaded until the external CUDA adapter is smoke-tested."""

    def rig(
        self,
        model_relative_path: str,
        cancellation: CancellationToken,
        progress: Callable[[RiggingProgress], None] | None = None,
    ) -> str:
        del model_relative_path, cancellation, progress
        self.load()
        raise AssertionError("UniRig load must raise until a real CUDA adapter is available")
