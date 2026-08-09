"""Local mock reconstruction provider used before real AI providers exist."""

from __future__ import annotations

from base64 import b64decode
from collections.abc import Callable
from time import sleep

import trimesh

from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.domain.models import ProgressUpdate
from character_model_studio.domain.states import AttemptStatus
from character_model_studio.storage.repositories import LocalRepository


class MockReconstructionProvider:
    """Publishes a fixture GLB through the same lifecycle shape as a future provider."""

    def run(
        self,
        repository: LocalRepository,
        attempt_id: str,
        token: CancellationToken,
        progress: Callable[[ProgressUpdate], None],
    ) -> None:
        for status, update in (
            (
                AttemptStatus.PREPROCESSING,
                ProgressUpdate("preprocess", "Selecting fixture views", 20, True),
            ),
            (
                AttemptStatus.RECONSTRUCTING,
                ProgressUpdate("shape", "Generating fixture geometry", None, True),
            ),
            (
                AttemptStatus.TEXTURING,
                ProgressUpdate("texture", "Publishing fixture texture", 70, True),
            ),
            (
                AttemptStatus.VALIDATING_MODEL,
                ProgressUpdate("validate", "Preparing fixture GLB", 85, True),
            ),
        ):
            if token.is_cancelled:
                repository.transition_attempt(attempt_id, AttemptStatus.CANCELLED)
                return
            repository.transition_attempt(attempt_id, status)
            progress(update)
            sleep(0.01)
        model_output = repository.attempt_artifact_path(attempt_id, "model.glb")
        texture_output = repository.attempt_artifact_path(attempt_id, "albedo.png")
        model_output.parent.mkdir(parents=True, exist_ok=True)
        trimesh.creation.icosphere(subdivisions=1).export(model_output)
        texture_output.write_bytes(
            b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL6KwAAAABJRU5ErkJggg=="
            )
        )
        repository.transition_attempt(
            attempt_id,
            AttemptStatus.READY_FOR_REVIEW,
            repository.as_project_relative_path(model_output),
            repository.as_project_relative_path(texture_output),
        )
        progress(ProgressUpdate("review", "Ready for review", 100, False))
