"""In-process reconstruction MVP orchestration for mock or future real providers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.reconstruction.mock import MockReconstructionProvider
from character_model_studio.storage.repositories import LocalRepository
from character_model_studio.validation.model import (
    ModelValidationReport,
    ModelValidator,
    ValidationStatus,
)
from character_model_studio.viewer.scene import load_glb_model


@dataclass(frozen=True, slots=True)
class MvpWorkflowResult:
    """Review-ready result from the local reconstruction MVP pathway."""

    attempt_id: str
    report: ModelValidationReport
    model_path: Path


class MvpWorkflow:
    """Coordinates local attempts without a server or UI-owned provider calls."""

    def __init__(self, repository: LocalRepository) -> None:
        self._repository = repository

    def reconstruct_fixture(
        self, capture_id: str, quality_mode: str = "standard"
    ) -> MvpWorkflowResult:
        """Execute the fully local mock path used while the real provider remains gated."""
        attempt = self._repository.create_attempt(capture_id, quality_mode)
        MockReconstructionProvider().run(
            self._repository, attempt.id, CancellationToken(), lambda _progress: None
        )
        ready = self._repository.get_attempt(attempt.id)
        if ready.model_relative_path is None:
            raise RuntimeError("Reconstruction produced no model artifact")
        model_path = self._repository.projects_root / ready.model_relative_path
        report = ModelValidator().validate(model_path)
        self._repository.persist_validation_report(ready.id, report)
        if report.overall_status is ValidationStatus.FAIL:
            raise RuntimeError("Generated model failed technical validation")
        load_glb_model(model_path)
        return MvpWorkflowResult(ready.id, report, model_path)
