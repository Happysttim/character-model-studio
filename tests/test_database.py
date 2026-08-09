"""SQLite bootstrap tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from character_model_studio.storage.database import INITIAL_SCHEMA_VERSION, initialize_database


def test_initialize_database_creates_schema_metadata(tmp_path: Path) -> None:
    database_path = tmp_path / "metadata.sqlite3"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        version = connection.execute("SELECT schema_version FROM schema_metadata").fetchone()

    assert version == (INITIAL_SCHEMA_VERSION,)
