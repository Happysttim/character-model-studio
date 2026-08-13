"""Optional isolated-runtime adapter for the official UniRig provider."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from character_model_studio.app.capabilities import (
    ProviderReadiness,
    ReadinessStatus,
    probe_runtime,
)
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.rigging.interfaces import RiggingProvider
from character_model_studio.rigging.models import RiggingProgress
from character_model_studio.rigging.unirig_paths import resolve_unirig_paths
from character_model_studio.validation.rigged_model import RiggedModelValidator


class UniRigProvider(RiggingProvider):
    """Gate UniRig honestly until its isolated CUDA runtime and local checkpoints are ready.

    UniRig's upstream dependencies conflict with the reconstruction environment. The
    application therefore reserves an explicit child-runtime boundary for it instead
    of silently downgrading shared dependencies or using CPU fallback.
    """

    _TEXTURED_MERGE_TIMEOUT_SECONDS = 300

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

    def merge_textured_rig(
        self,
        skinning_fbx: Path,
        textured_source_glb: Path,
        output_glb: Path,
        cancellation: CancellationToken,
        progress: Callable[[RiggingProgress], None] | None = None,
    ) -> Path:
        """Transfer UniRig bones/weights onto the original textured GLB.

        UniRig's direct skinning export is FBX and can omit source materials.  Its
        upstream transfer utility instead imports the original GLB and applies the
        generated armature and weights, preserving the original material/image
        references.  This method intentionally runs in UniRig's isolated runtime.
        """
        readiness = self.probe()
        if not readiness.adapter_installed or not readiness.vram_eligible:
            raise RuntimeError(f"{readiness.status}: {readiness.reason}")
        if not skinning_fbx.is_file():
            raise FileNotFoundError(f"UniRig skinning output was not found: {skinning_fbx}")
        if not textured_source_glb.is_file():
            raise FileNotFoundError(f"Textured source GLB was not found: {textured_source_glb}")
        if textured_source_glb.suffix.lower() != ".glb":
            raise ValueError("Textured source asset must be a GLB file")
        if cancellation.is_cancelled:
            raise RuntimeError("UniRig textured rig merge was cancelled before start")

        output_glb.parent.mkdir(parents=True, exist_ok=True)
        paths = resolve_unirig_paths()
        command = self._merge_command(
            paths.runtime_python, skinning_fbx, textured_source_glb, output_glb
        )
        if progress is not None:
            progress(RiggingProgress("texture_merge", "Preserving textured source GLB", 0, 2))
        process = subprocess.Popen(
            command,
            cwd=paths.source_directory,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        deadline = time.monotonic() + self._TEXTURED_MERGE_TIMEOUT_SECONDS
        while process.poll() is None:
            if bool(cancellation.is_cancelled):
                self._terminate_process_tree(process)
                raise RuntimeError("UniRig textured rig merge was cancelled")
            if time.monotonic() >= deadline:
                self._terminate_process_tree(process)
                raise RuntimeError(
                    "UniRig textured rig merge exceeded its five-minute time limit; "
                    "the isolated provider process was stopped."
                )
            time.sleep(0.1)
        if process.returncode != 0:
            detail = "" if process.stderr is None else process.stderr.read().strip()[-2000:]
            raise RuntimeError(f"UniRig textured rig merge failed: {detail}")
        report = RiggedModelValidator().validate(output_glb)
        if not report.acceptable:
            raise RuntimeError(f"Merged rigged GLB failed validation: {report.failures}")
        if progress is not None:
            progress(RiggingProgress("texture_merge", "Textured rigged GLB validated", 2, 2))
        return output_glb

    @staticmethod
    def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
        """Stop a Windows provider launcher and any Blender/Python descendants."""
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    @staticmethod
    def _merge_command(
        runtime_python: Path, skinning_fbx: Path, textured_source_glb: Path, output_glb: Path
    ) -> list[str]:
        """Build the upstream transfer command without embedding local paths."""
        return [
            str(runtime_python),
            "-E",
            "-m",
            "src.inference.merge",
            "--require_suffix",
            "glb",
            "--num_runs",
            "1",
            "--id",
            "0",
            "--source",
            str(skinning_fbx),
            "--target",
            str(textured_source_glb),
            "--output",
            str(output_glb),
        ]

    def rig(
        self,
        model_relative_path: str,
        cancellation: CancellationToken,
        progress: Callable[[RiggingProgress], None] | None = None,
    ) -> str:
        del model_relative_path, cancellation, progress
        self.load()
        raise AssertionError("UniRig load must raise until a real CUDA adapter is available")
