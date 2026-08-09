"""Real Hunyuan3D 2.0 Standard Shape workflow owned by the desktop application."""

from __future__ import annotations

import gc
import time
from collections.abc import Callable
from pathlib import Path

import torch

from character_model_studio.app.capabilities import probe_runtime
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.domain.models import ProgressUpdate
from character_model_studio.domain.states import AttemptStatus
from character_model_studio.reconstruction.preprocessing import select_representative_frame
from character_model_studio.reconstruction.providers.hunyuan2 import Hunyuan3D20Provider
from character_model_studio.reconstruction.providers.rembg_segmentation import (
    RembgAnimeSegmentationProvider,
)
from character_model_studio.reconstruction.providers.sf3d import StableFast3DProvider
from character_model_studio.storage.repositories import LocalRepository
from character_model_studio.validation.model import ModelValidator, ValidationStatus


class StandardShapeWorkflow:
    """Executes preprocessing, CUDA Shape generation, provenance, and viewer proof locally."""

    def run(
        self,
        repository: LocalRepository,
        attempt_id: str,
        token: CancellationToken,
        progress: Callable[[ProgressUpdate], None],
    ) -> Path:
        """Publish an untextured Standard GLB or leave the attempt in a truthful terminal state."""
        segmentation = RembgAnimeSegmentationProvider()
        started = time.perf_counter()
        runtime = probe_runtime()
        try:
            attempt = repository.get_attempt(attempt_id)
            provider = _provider_for_attempt(attempt.provider)
            repository.transition_attempt(attempt_id, AttemptStatus.PREPROCESSING)
            progress(
                ProgressUpdate("preprocess", "Selecting a representative capture frame", 10, True)
            )
            capture = repository.get_capture(attempt.capture_id)
            input_path = repository.attempt_artifact_path(attempt_id, "inputs/selected-frame.png")
            selection = select_representative_frame(
                repository.projects_root / capture.relative_path, input_path
            )
            if token.is_cancelled:
                repository.transition_attempt(attempt_id, AttemptStatus.CANCELLED)
                return input_path

            progress(
                ProgressUpdate(
                    "segment", "Removing the capture background on local CUDA", None, True
                )
            )
            isolated_input_path = repository.attempt_artifact_path(
                attempt_id, "inputs/isolated-character.png"
            )
            mask_path = repository.attempt_artifact_path(attempt_id, "inputs/character-mask.png")
            segmentation.load()
            segmentation.isolate(input_path, isolated_input_path, mask_path)
            segmentation.unload()

            device = torch.device("cuda:0")
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats(device)
            before_load = _gpu_memory(device)
            repository.transition_attempt(attempt_id, AttemptStatus.RECONSTRUCTING)
            progress(ProgressUpdate("load", f"Loading {provider.name} on CUDA", None, True))
            load_started = time.perf_counter()
            provider.load()
            after_load = _gpu_memory(device)
            progress(
                ProgressUpdate(
                    "shape",
                    "Generating textured 3D asset"
                    if provider.name == StableFast3DProvider.name
                    else "Generating untextured 3D shape",
                    None,
                    True,
                )
            )
            output_path = repository.attempt_artifact_path(attempt_id, "model.glb")
            provider.generate_shape(
                [isolated_input_path], output_path, token, _shape_progress(progress, provider.name)
            )
            torch.cuda.synchronize(device)

            repository.transition_attempt(
                attempt_id,
                AttemptStatus.VALIDATING_MODEL,
                repository.as_project_relative_path(output_path),
            )
            progress(ProgressUpdate("validate", "Validating the generated GLB", 90, False))
            validation = ModelValidator().validate(output_path)
            repository.persist_validation_report(attempt_id, validation)
            if validation.overall_status is ValidationStatus.FAIL:
                detail = "; ".join(validation.failures) or "unknown validation failure"
                raise RuntimeError(f"Generated GLB failed technical validation: {detail}")
            metrics: dict[str, object] = {
                "operation": "shape_reconstruction",
                "quality_mode": attempt.quality_mode,
                "provider": provider.name,
                "provider_version": provider.version,
                "cuda_available": runtime.gpu.cuda_available,
                "device": str(device),
                "total_vram_bytes": runtime.gpu.total_vram_bytes,
                "free_vram_before_bytes": before_load["free_bytes"],
                "provider_load_seconds": time.perf_counter() - load_started,
                "after_load": after_load,
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
                "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
                "duration_seconds": time.perf_counter() - started,
                "selected_frame": {
                    "source_frame_index": selection.source_frame_index,
                    "source_timestamp_ms": selection.source_timestamp_ms,
                    "sharpness": selection.sharpness,
                    "output_path": repository.as_project_relative_path(input_path),
                },
                "segmentation": {
                    "provider": segmentation.name,
                    "model": segmentation.model_name,
                    "input_path": repository.as_project_relative_path(input_path),
                    "isolated_input_path": repository.as_project_relative_path(isolated_input_path),
                    "mask_path": repository.as_project_relative_path(mask_path),
                },
                "output_path": repository.as_project_relative_path(output_path),
                "vertex_count": validation.metrics["vertex_count"],
                "face_count": validation.metrics["face_count"],
                "validation_status": validation.overall_status.value,
                "texture_stage": "generated"
                if provider.name == StableFast3DProvider.name
                else "not_requested",
            }
            repository.persist_attempt_metrics(attempt_id, metrics)
            repository.write_attempt_metadata(attempt_id, metrics)
            repository.transition_attempt(attempt_id, AttemptStatus.READY_FOR_REVIEW)
            progress(
                ProgressUpdate(
                    "review", "Standard Shape is ready for technical validation", 100, False
                )
            )
            return output_path
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            current = repository.get_attempt(attempt_id)
            if current.status not in {AttemptStatus.FAILED, AttemptStatus.CANCELLED}:
                repository.transition_attempt(attempt_id, AttemptStatus.FAILED)
            raise RuntimeError(f"Local reconstruction failed: {error}") from error
        finally:
            segmentation.unload()
            if "provider" in locals():
                provider.unload()
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


def _gpu_memory(device: torch.device) -> dict[str, int]:
    free, total = torch.cuda.mem_get_info(device)
    return {
        "free_bytes": free,
        "total_bytes": total,
        "allocated_bytes": torch.cuda.memory_allocated(device),
        "reserved_bytes": torch.cuda.memory_reserved(device),
    }


def _provider_for_attempt(provider_name: str) -> Hunyuan3D20Provider | StableFast3DProvider:
    if provider_name == StableFast3DProvider.name:
        return StableFast3DProvider()
    if provider_name == Hunyuan3D20Provider.name:
        return Hunyuan3D20Provider()
    raise ValueError(f"Unsupported reconstruction provider: {provider_name}")


def _shape_progress(
    publish: Callable[[ProgressUpdate], None], provider_name: str
) -> Callable[[str, int, int], None]:
    """Translate actual Hunyuan iteration totals into bounded workflow progress."""

    ranges = {
        "diffusion": (15, 65, "Diffusion Sampling"),
        "volume": (65, 88, "Volume Decoding"),
    }

    def report(stage: str, completed: int, total: int) -> None:
        if provider_name == StableFast3DProvider.name:
            label = "SF3D geometry" if stage == "sf3d_geometry" else "SF3D texture baking"
            percent = 45 + round(40 * completed / max(total, 1))
            publish(ProgressUpdate(stage, f"{label} {completed}/{total}", percent, True))
            return
        start, end, label = ranges[stage]
        percent = start + round((end - start) * completed / max(total, 1))
        publish(ProgressUpdate(stage, f"{label} {completed}/{total}", percent, True))

    return report
