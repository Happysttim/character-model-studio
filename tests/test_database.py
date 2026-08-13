"""SQLite bootstrap tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from character_model_studio.domain.states import AttemptStatus
from character_model_studio.rigging.fixture_glb import write_fixture_rigged_glb
from character_model_studio.storage.database import INITIAL_SCHEMA_VERSION, initialize_database
from character_model_studio.storage.repositories import LocalRepository


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
