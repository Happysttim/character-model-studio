"""End-to-end in-process mock workflow and restart-persistence tests."""

from __future__ import annotations

from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.domain.states import AttemptStatus
from character_model_studio.reconstruction.mock import MockReconstructionProvider
from character_model_studio.reconstruction.task_runner import MockWorkflowTaskRunner
from character_model_studio.rigging.providers.mock import MockRiggingProvider
from character_model_studio.storage.database import initialize_database
from character_model_studio.storage.repositories import LocalRepository


def test_mock_workflow_persists_review_rig_and_animation(tmp_path) -> None:
    database = tmp_path / "app.sqlite3"
    initialize_database(database)
    repository = LocalRepository(database, tmp_path / "Projects")
    project = repository.create_project("Fixture project")
    capture = repository.create_fixture_capture(project.id)
    attempt = repository.create_attempt(capture.id, "standard")
    updates = []

    MockReconstructionProvider().run(repository, attempt.id, CancellationToken(), updates.append)
    ready = repository.get_attempt(attempt.id)
    accepted = repository.decide(ready.id, accepted=True)
    restarted = LocalRepository(database, tmp_path / "Projects")
    rig_id = MockRiggingProvider().run(restarted, accepted.id)
    pose_id, clip_id = restarted.save_pose_and_animation(rig_id)

    assert ready.status is AttemptStatus.READY_FOR_REVIEW
    assert accepted.status is AttemptStatus.ACCEPTED
    assert restarted.get_attempt(attempt.id).status is AttemptStatus.ACCEPTED
    assert ready.model_relative_path is not None
    assert (tmp_path / "Projects" / ready.model_relative_path).is_file()
    assert ready.texture_relative_path is not None
    assert (tmp_path / "Projects" / ready.texture_relative_path).is_file()
    assert any((tmp_path / "Projects").rglob("rigged.glb"))
    rig = restarted.get_rig_attempt(rig_id)
    assert rig.provider == "fixture-rigging"
    assert rig.rigged_relative_path is not None
    rigged_path = tmp_path / "Projects" / rig.rigged_relative_path
    assert rigged_path.is_file()
    assert updates[-1].percent == 100
    assert pose_id and clip_id


def test_mock_workflow_can_regenerate_and_cancel(tmp_path) -> None:
    database = tmp_path / "app.sqlite3"
    initialize_database(database)
    repository = LocalRepository(database, tmp_path / "Projects")
    capture = repository.create_fixture_capture(repository.create_project("Fixture").id)
    first = repository.create_attempt(capture.id, "high_quality")
    MockReconstructionProvider().run(
        repository, first.id, CancellationToken(), lambda _update: None
    )
    rejected = repository.decide(first.id, accepted=False, reason="Fixture rejection")
    regenerated = repository.regenerate(first.id)
    token = CancellationToken()
    token.cancel()

    MockReconstructionProvider().run(repository, regenerated.id, token, lambda _update: None)

    history = repository.list_attempts(capture.id)
    assert [attempt.sequence_number for attempt in history] == [1, 2]
    assert rejected.status is AttemptStatus.REJECTED
    assert regenerated.provider == "mock-hunyuan3d-2.1"
    assert repository.get_attempt(regenerated.id).status is AttemptStatus.CANCELLED


def test_mock_workflow_runner_emits_progress_off_the_calling_thread(tmp_path, qtbot) -> None:
    database = tmp_path / "app.sqlite3"
    initialize_database(database)
    repository = LocalRepository(database, tmp_path / "Projects")
    capture = repository.create_fixture_capture(repository.create_project("Fixture").id)
    attempt = repository.create_attempt(capture.id, "standard")
    runner = MockWorkflowTaskRunner()
    progress = []
    runner.progress.connect(progress.append)

    with qtbot.waitSignal(runner.completed, timeout=3000) as completed:
        runner.start(repository, attempt.id)

    assert completed.args == [attempt.id]
    assert progress[-1].stage == "review"
