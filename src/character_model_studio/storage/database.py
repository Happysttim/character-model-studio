"""SQLite schema bootstrap for the greenfield application."""

from __future__ import annotations

import sqlite3
from pathlib import Path

INITIAL_SCHEMA_VERSION = 1


def initialize_database(database_path: Path) -> None:
    """Create the versioned SQLite metadata store if it does not yet exist."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_metadata (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                schema_version INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO schema_metadata (singleton, schema_version) VALUES (1, ?)",
            (INITIAL_SCHEMA_VERSION,),
        )
