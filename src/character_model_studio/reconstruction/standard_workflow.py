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
from character_model_studio.storage.repositories import LocalRepository
from character_model_studio.viewer.scene import load_glb_model


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
        provider = Hunyuan3D20Provider()
        started = time.perf_counter()
        runtime = probe_runtime()
        try:
            attempt = repository.get_attempt(attempt_id)
            if attempt.quality_mode != "standard":
                raise ValueError("The real Shape workflow supports Standard Hunyuan3D 2.0 only")
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

            device = torch.device("cuda:0")
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats(device)
            before_load = _gpu_memory(device)
            repository.transition_attempt(attempt_id, AttemptStatus.RECONSTRUCTING)
            progress(ProgressUpdate("load", "Loading Hunyuan3D 2.0 Shape on CUDA", None, True))
            load_started = time.perf_counter()
            provider.load()
            after_load = _gpu_memory(device)
            progress(ProgressUpdate("shape", "Generating untextured 3D shape", None, True))
            output_path = repository.attempt_artifact_path(attempt_id, "model.glb")
            provider.generate_shape([input_path], output_path, token)
            torch.cuda.synchronize(device)

            repository.transition_attempt(
                attempt_id,
                AttemptStatus.VALIDATING_MODEL,
                repository.as_project_relative_path(output_path),
            )
            progress(
                ProgressUpdate("viewer", "Checking generated GLB in the embedded viewer", 90, False)
            )
            viewer_model = load_glb_model(output_path)
            metrics: dict[str, object] = {
                "operation": "shape_reconstruction",
                "quality_mode": "standard",
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
                "output_path": repository.as_project_relative_path(output_path),
                "vertex_count": viewer_model.vertex_count,
                "face_count": viewer_model.face_count,
                "texture_stage": "not_requested",
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
            raise RuntimeError(f"Standard Hunyuan3D 2.0 Shape failed: {error}") from error
        finally:
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
