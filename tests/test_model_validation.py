"""Fixture coverage for the static GLB validation contract."""

from __future__ import annotations

import sqlite3

import numpy as np
import trimesh

from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.reconstruction.mock import MockReconstructionProvider
from character_model_studio.storage.database import initialize_database
from character_model_studio.storage.repositories import LocalRepository
from character_model_studio.validation.model import ModelValidator, ValidationStatus


def test_valid_untextured_glb_passes(tmp_path) -> None:
    path = tmp_path / "valid.glb"
    trimesh.creation.icosphere().export(path)

    report = ModelValidator().validate(path)

    assert report.overall_status is ValidationStatus.PASS
    assert report.metrics["vertex_count"] > 0


def test_malformed_and_empty_models_fail_without_crashing(tmp_path) -> None:
    malformed = tmp_path / "malformed.glb"
    malformed.write_bytes(b"not a glb")
    empty = tmp_path / "empty.glb"
    empty.write_bytes(b"")

    assert ModelValidator().validate(malformed).overall_status is ValidationStatus.FAIL
    assert ModelValidator().validate(empty).overall_status is ValidationStatus.FAIL


def test_fragmented_model_remains_inspectable(tmp_path) -> None:
    vertices = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [10.0, 0.0, 0.0],
            [11.0, 0.0, 0.0],
            [10.0, 1.0, 0.0],
        ]
    )
    mesh = trimesh.Trimesh(vertices=vertices, faces=[[0, 1, 2], [3, 4, 5]], process=False)
    path = tmp_path / "fragmented.glb"
    mesh.export(path)

    report = ModelValidator().validate(path)

    assert report.overall_status is ValidationStatus.PASS
    assert report.metrics["connected_components"] == 2


def test_validation_report_persists_for_a_model_attempt(tmp_path) -> None:
    database = tmp_path / "app.sqlite3"
    initialize_database(database)
    repository = LocalRepository(database, tmp_path / "Projects")
    capture = repository.create_fixture_capture(repository.create_project("Fixture").id)
    attempt = repository.create_attempt(capture.id, "standard")
    MockReconstructionProvider().run(
        repository, attempt.id, CancellationToken(), lambda _update: None
    )
    ready = repository.get_attempt(attempt.id)
    assert ready.model_relative_path is not None
    report = ModelValidator().validate(tmp_path / "Projects" / ready.model_relative_path)

    repository.persist_validation_report(attempt.id, report)

    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT overall_status FROM validation_reports WHERE attempt_id = ?", (attempt.id,)
        ).fetchone()
    assert row == (ValidationStatus.PASS.value,)
