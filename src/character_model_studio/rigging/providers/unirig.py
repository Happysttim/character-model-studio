"""Optional isolated-runtime adapter for the official UniRig provider."""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from shutil import copy2

from character_model_studio.app.capabilities import (
    ProviderReadiness,
    ReadinessStatus,
    probe_runtime,
)
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.rigging.interfaces import RiggingProvider
from character_model_studio.rigging.models import RiggingProgress
from character_model_studio.rigging.unirig_paths import UniRigPaths, resolve_unirig_paths
from character_model_studio.validation.rigged_model import RiggedModelValidator


class UniRigProvider(RiggingProvider):
    """Gate UniRig honestly until its isolated CUDA runtime and local checkpoints are ready.

    UniRig's upstream dependencies conflict with the reconstruction environment. The
    application therefore reserves an explicit child-runtime boundary for it instead
    of silently downgrading shared dependencies or using CPU fallback.
    """

    _TEXTURED_MERGE_TIMEOUT_SECONDS = 300
    _STAGE_TIMEOUT_SECONDS = 300

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
        required = (
            paths.model_cache / "skeleton" / "articulation-xl_quantization_256" / "model.ckpt",
            paths.model_cache / "skin" / "articulation-xl" / "model.ckpt",
        )
        if not all(path.is_file() for path in required):
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
            ReadinessStatus.READY,
            "Isolated UniRig CUDA runtime and local skeleton/skinning checkpoints are ready.",
            True,
            True,
        )

    def load(self) -> None:
        readiness = self.probe()
        if readiness.status is not ReadinessStatus.READY:
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
        log_path = output_glb.parent / "unirig-texture-merge.log"
        log_file = log_path.open("w", encoding="utf-8", errors="replace")
        process = subprocess.Popen(
            command,
            cwd=paths.source_directory,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        deadline = time.monotonic() + self._TEXTURED_MERGE_TIMEOUT_SECONDS
        artifact_ready_at: float | None = None
        while True:
            if output_glb.is_file() and output_glb.stat().st_size > 0:
                artifact_ready_at = artifact_ready_at or time.monotonic()
                if time.monotonic() - artifact_ready_at >= 2:
                    if process.poll() is None:
                        self._terminate_process_tree(process)
                    break
            elif process.poll() is not None and process.returncode != 0:
                log_file.flush()
                raise RuntimeError(f"UniRig textured rig merge failed; see {log_path.name}")
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
        log_file.close()
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
        raise RuntimeError("UniRig requires an application-owned project artifact path")

    def rig_glb(
        self,
        source_glb: Path,
        work_directory: Path,
        output_glb: Path,
        cancellation: CancellationToken,
        progress: Callable[[RiggingProgress], None] | None = None,
    ) -> Path:
        """Run the official local UniRig stages then preserve source GLB textures."""
        self.load()
        if not source_glb.is_file():
            raise FileNotFoundError(f"Accepted source GLB was not found: {source_glb}")
        paths = resolve_unirig_paths()
        input_directory = work_directory / "input"
        intermediate = work_directory / "intermediate"
        skeleton_output = work_directory / "skeleton-output"
        skin_output = work_directory / "skin-output"
        input_directory.mkdir(parents=True, exist_ok=True)
        copied_source = input_directory / "source.glb"
        copy2(source_glb, copied_source)
        environment = {
            "PYTHONPATH": "",
            "UNIRIG_MODEL_CACHE": str(paths.model_cache),
            "UNIRIG_TRANSFORMERS_MODEL_DIR": str(
                paths.model_cache / "transformers" / "facebook-opt-350m"
            ),
            "HF_HUB_OFFLINE": "1",
        }
        self._run_stage(
            [
                "-m",
                "src.data.extract",
                "--config",
                "configs/data/quick_inference.yaml",
                "--require_suffix",
                "obj,fbx,FBX,dae,glb,gltf,vrm",
                "--force_override",
                "true",
                "--num_runs",
                "1",
                "--id",
                "0",
                "--time",
                "app",
                "--faces_target_count",
                "50000",
                "--input_dir",
                str(input_directory),
                "--output_dir",
                str(intermediate),
            ],
            paths,
            environment,
            cancellation,
            progress,
            "prepare",
            "Preparing UniRig mesh input",
            1,
            4,
            intermediate / "source" / "raw_data.npz",
        )
        self._set_flash_attention(paths, enabled=False)
        environment["UNIRIG_PRESERVE_INTERMEDIATE"] = "1"
        self._run_stage(
            [
                "run.py",
                "--task",
                "configs/task/quick_inference_skeleton_articulationxl_ar_256.yaml",
                "--input_dir",
                str(input_directory),
                "--output_dir",
                str(skeleton_output),
                "--npz_dir",
                str(intermediate),
            ],
            paths,
            environment,
            cancellation,
            progress,
            "skeleton",
            "Generating skeleton on CUDA",
            2,
            4,
            skeleton_output / "source" / "skeleton.fbx",
        )
        self._set_flash_attention(paths, enabled=True)
        environment.pop("UNIRIG_PRESERVE_INTERMEDIATE", None)
        self._run_stage(
            [
                "run.py",
                "--task",
                "configs/task/quick_inference_unirig_skin.yaml",
                "--input_dir",
                str(input_directory),
                "--output_dir",
                str(skin_output),
                "--npz_dir",
                str(intermediate),
            ],
            paths,
            environment,
            cancellation,
            progress,
            "skinning",
            "Generating skinning weights on CUDA",
            3,
            4,
            skin_output / "source" / "predict.fbx",
        )
        result = self.merge_textured_rig(
            skin_output / "source" / "predict.fbx",
            copied_source,
            output_glb,
            cancellation,
            progress,
        )
        return result

    def _run_stage(
        self,
        arguments: list[str],
        paths: UniRigPaths,
        environment: dict[str, str],
        cancellation: CancellationToken,
        progress: Callable[[RiggingProgress], None] | None,
        stage: str,
        label: str,
        completed: int,
        total: int,
        completion_artifact: Path | None = None,
    ) -> None:
        if progress is not None:
            progress(RiggingProgress(stage, label, completed - 1, total))
        log_directory = (
            paths.model_cache / "logs"
            if completion_artifact is None
            else completion_artifact.parent
        )
        log_directory.mkdir(parents=True, exist_ok=True)
        log_path = log_directory / f"unirig-{stage}.log"
        log_file = log_path.open("w", encoding="utf-8", errors="replace")
        process = subprocess.Popen(
            [str(paths.runtime_python), "-E", *arguments],
            cwd=paths.source_directory,
            env={**os.environ, **environment},
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        deadline = time.monotonic() + self._STAGE_TIMEOUT_SECONDS
        artifact_ready_at: float | None = None
        while True:
            if completion_artifact is not None and completion_artifact.is_file():
                artifact_ready_at = artifact_ready_at or time.monotonic()
                if time.monotonic() - artifact_ready_at >= 2:
                    if process.poll() is None:
                        self._terminate_process_tree(process)
                    break
            elif completion_artifact is None and process.poll() is not None:
                if process.returncode != 0:
                    log_file.flush()
                    raise RuntimeError(f"UniRig {stage} failed; see {log_path.name}")
                break
            elif (
                completion_artifact is not None
                and process.poll() is not None
                and process.returncode != 0
            ):
                log_file.flush()
                raise RuntimeError(f"UniRig {stage} failed; see {log_path.name}")
            if cancellation.is_cancelled:
                self._terminate_process_tree(process)
                raise RuntimeError(f"UniRig {stage} was cancelled")
            if time.monotonic() >= deadline:
                self._terminate_process_tree(process)
                raise RuntimeError(
                    f"UniRig {stage} exceeded its five-minute time limit; "
                    "the isolated provider process was stopped."
                )
            time.sleep(0.1)
        log_file.close()
        if progress is not None:
            progress(RiggingProgress(stage, label, completed, total))

    @staticmethod
    def _set_flash_attention(paths: UniRigPaths, *, enabled: bool) -> None:
        """Switch the isolated runtime backend between Skeleton and Skinning.

        The upstream Skeleton dependency imports a Windows-incompatible Triton path
        when FlashAttention is installed.  Skinning needs the compiled extension.
        The wheel is a locally cached provider runtime artifact; no download occurs.
        """
        command = [str(paths.runtime_python), "-E", "-m", "pip"]
        if not enabled:
            result = subprocess.run(
                [*command, "uninstall", "-y", "flash-attn"],
                cwd=paths.source_directory,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.returncode not in {0, 1}:
                raise RuntimeError(f"Unable to prepare UniRig Skeleton backend: {result.stderr}")
            return
        wheels = sorted((paths.model_cache / "runtime-wheels").glob("flash_attn-*.whl"))
        if not wheels:
            raise RuntimeError(
                "UniRig Skinning requires a locally cached Windows FlashAttention wheel; "
                "no online download was attempted."
            )
        result = subprocess.run(
            [*command, "install", "--force-reinstall", "--no-deps", str(wheels[-1])],
            cwd=paths.source_directory,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Unable to prepare UniRig Skinning backend: {result.stderr}")
