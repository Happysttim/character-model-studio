"""Reconstruction MVP integration with the local Mock provider contract."""

from __future__ import annotations

from character_model_studio.app.mvp_workflow import MvpWorkflow
from character_model_studio.domain.states import AttemptStatus
from character_model_studio.storage.database import initialize_database
from character_model_studio.storage.repositories import LocalRepository
from character_model_studio.validation.model import ValidationStatus


def test_mock_mvp_workflow_validates_accepts_and_restores_after_restart(tmp_path) -> None:
    database = tmp_path / "app.sqlite3"
    projects_root = tmp_path / "Projects"
    initialize_database(database)
    repository = LocalRepository(database, projects_root)
    capture = repository.create_fixture_capture(repository.create_project("MVP fixture").id)

    result = MvpWorkflow(repository).reconstruct_fixture(capture.id)
    accepted = repository.decide(result.attempt_id, accepted=True)
    restarted = LocalRepository(database, projects_root)

    assert result.report.overall_status is ValidationStatus.PASS
    assert result.model_path.is_file()
    assert accepted.status is AttemptStatus.ACCEPTED
    assert restarted.get_attempt(result.attempt_id).status is AttemptStatus.ACCEPTED


def test_startup_recovery_preserves_artifacts_and_marks_transient_attempt_failed(tmp_path) -> None:
    database = tmp_path / "app.sqlite3"
    initialize_database(database)
    repository = LocalRepository(database, tmp_path / "Projects")
    capture = repository.create_fixture_capture(repository.create_project("Recovery fixture").id)
    attempt = repository.create_attempt(capture.id, "standard")
    repository.transition_attempt(attempt.id, AttemptStatus.PREPROCESSING)

    recovered = repository.recover_interrupted_attempts()

    assert recovered == 1
    assert repository.get_attempt(attempt.id).status is AttemptStatus.FAILED


def test_project_history_can_reopen_local_project_metadata(tmp_path) -> None:
    database = tmp_path / "app.sqlite3"
    initialize_database(database)
    repository = LocalRepository(database, tmp_path / "Projects")
    created = repository.create_project("Reopen fixture")

    history = LocalRepository(database, tmp_path / "Projects").list_projects()

    assert history[0].id == created.id
    assert history[0].name == "Reopen fixture"
