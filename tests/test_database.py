"""SQLite bootstrap tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from character_model_studio.domain.states import AttemptStatus
from character_model_studio.rigging.fixture_glb import write_fixture_rigged_glb
from character_model_studio.rigging.models import RigStatus
from character_model_studio.storage.database import INITIAL_SCHEMA_VERSION, initialize_database
from character_model_studio.storage.repositories import LocalRepository
from character_model_studio.validation.rigged_model import RiggedModelValidator


def test_initialize_database_creates_schema_metadata(tmp_path: Path) -> None:
    database_path = tmp_path / "metadata.sqlite3"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        version = connection.execute("SELECT schema_version FROM schema_metadata").fetchone()

    assert version == (INITIAL_SCHEMA_VERSION,)


def test_import_glb_for_review_copies_source_and_creates_reviewable_attempt(tmp_path: Path) -> None:
    database_path = tmp_path / "metadata.sqlite3"
    initialize_database(database_path)
    source = tmp_path / "source.glb"
    write_fixture_rigged_glb(source)
    repository = LocalRepository(database_path, tmp_path / "Projects")

    attempt = repository.import_glb_for_review(source)

    assert attempt.status is AttemptStatus.READY_FOR_REVIEW
    assert attempt.provider == "local-glb-import"
    assert attempt.model_relative_path is not None
    copied = repository.projects_root / attempt.model_relative_path
    assert copied.is_file()
    assert copied.read_bytes() == source.read_bytes()


def test_failed_rig_attempt_keeps_the_accepted_source(tmp_path: Path) -> None:
    database_path = tmp_path / "metadata.sqlite3"
    initialize_database(database_path)
    source = tmp_path / "source.glb"
    write_fixture_rigged_glb(source)
    repository = LocalRepository(database_path, tmp_path / "Projects")
    attempt = repository.import_glb_for_review(source)
    repository.decide(attempt.id, accepted=True)

    rig = repository.create_rig_attempt(attempt.id, "UniRig", "upstream-local")
    repository.set_rig_attempt_status(rig.id, RigStatus.RIGGING)
    failed = repository.fail_rig_attempt(rig.id, "provider smoke failure")

    assert failed.status is RigStatus.FAILED
    assert repository.get_attempt(attempt.id).model_relative_path == attempt.model_relative_path
    assert (repository.projects_root / str(attempt.model_relative_path)).is_file()


def test_pose_and_animation_payloads_reopen_for_a_validated_rig(tmp_path: Path) -> None:
    database_path = tmp_path / "metadata.sqlite3"
    initialize_database(database_path)
    source = tmp_path / "source.glb"
    write_fixture_rigged_glb(source)
    repository = LocalRepository(database_path, tmp_path / "Projects")
    attempt = repository.import_glb_for_review(source)
    repository.decide(attempt.id, accepted=True)
    rig = repository.create_rig_attempt(attempt.id, "fixture", "test")
    rigged_path = repository.attempt_artifact_path(attempt.id, f"rigs/{rig.id}/rigged.glb")
    rigged_path.parent.mkdir(parents=True, exist_ok=True)
    write_fixture_rigged_glb(rigged_path)
    repository.complete_rig_attempt(rig.id, rigged_path, {})
    repository.persist_rig_validation_report(rig.id, RiggedModelValidator().validate(rigged_path))

    repository.save_pose_document(
        rig.id,
        "From",
        {"schemaVersion": 1, "rigRevision": rig.id, "bones": {"root": [0, 0, 0, 1]}},
    )
    repository.save_animation_clip(rig.id, "From-To", {"durationMs": 1200, "loopPreview": False})

    assert repository.load_pose_documents(rig.id)["From"]["rigRevision"] == rig.id
    assert repository.load_animation_clip(rig.id) == {"durationMs": 1200, "loopPreview": False}
