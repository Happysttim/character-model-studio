"""SQLite schema bootstrap for the greenfield application."""

from __future__ import annotations

import sqlite3
from pathlib import Path

INITIAL_SCHEMA_VERSION = 6


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
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS captures (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id),
                relative_path TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS model_attempts (
                id TEXT PRIMARY KEY,
                capture_id TEXT NOT NULL REFERENCES captures(id),
                sequence_number INTEGER NOT NULL,
                status TEXT NOT NULL,
                quality_mode TEXT NOT NULL,
                provider TEXT NOT NULL,
                provider_version TEXT,
                parameters_json TEXT,
                metrics_json TEXT,
                model_relative_path TEXT,
                texture_relative_path TEXT,
                created_at TEXT NOT NULL,
                finished_at TEXT
            );
            CREATE TABLE IF NOT EXISTS model_reviews (
                attempt_id TEXT PRIMARY KEY REFERENCES model_attempts(id),
                decision TEXT NOT NULL,
                reason TEXT,
                reviewed_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS validation_reports (
                attempt_id TEXT PRIMARY KEY REFERENCES model_attempts(id),
                overall_status TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rig_attempts (
                id TEXT PRIMARY KEY,
                model_attempt_id TEXT NOT NULL REFERENCES model_attempts(id),
                status TEXT NOT NULL,
                rigged_relative_path TEXT,
                provider TEXT NOT NULL DEFAULT 'unknown',
                provider_version TEXT,
                source_relative_path TEXT NOT NULL DEFAULT '',
                metrics_json TEXT
            );
            CREATE TABLE IF NOT EXISTS pose_documents (
                id TEXT PRIMARY KEY,
                rig_attempt_id TEXT NOT NULL REFERENCES rig_attempts(id),
                name TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS animation_clips (
                id TEXT PRIMARY KEY,
                rig_attempt_id TEXT NOT NULL REFERENCES rig_attempts(id),
                name TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rig_validation_reports (
                rig_attempt_id TEXT PRIMARY KEY REFERENCES rig_attempts(id),
                overall_status TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        attempt_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(model_attempts)").fetchall()
        }
        if "texture_relative_path" not in attempt_columns:
            connection.execute("ALTER TABLE model_attempts ADD COLUMN texture_relative_path TEXT")
        if "provider_version" not in attempt_columns:
            connection.execute("ALTER TABLE model_attempts ADD COLUMN provider_version TEXT")
        if "parameters_json" not in attempt_columns:
            connection.execute("ALTER TABLE model_attempts ADD COLUMN parameters_json TEXT")
        if "metrics_json" not in attempt_columns:
            connection.execute("ALTER TABLE model_attempts ADD COLUMN metrics_json TEXT")
        rig_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(rig_attempts)").fetchall()
        }
        if "provider" not in rig_columns:
            connection.execute(
                "ALTER TABLE rig_attempts ADD COLUMN provider TEXT NOT NULL DEFAULT 'unknown'"
            )
        if "provider_version" not in rig_columns:
            connection.execute("ALTER TABLE rig_attempts ADD COLUMN provider_version TEXT")
        if "source_relative_path" not in rig_columns:
            connection.execute(
                "ALTER TABLE rig_attempts ADD COLUMN source_relative_path TEXT NOT NULL DEFAULT ''"
            )
        if "metrics_json" not in rig_columns:
            connection.execute("ALTER TABLE rig_attempts ADD COLUMN metrics_json TEXT")
        connection.execute(
            "INSERT OR IGNORE INTO schema_metadata (singleton, schema_version) VALUES (1, ?)",
            (INITIAL_SCHEMA_VERSION,),
        )
        connection.execute(
            "UPDATE schema_metadata SET schema_version = ? WHERE singleton = 1",
            (INITIAL_SCHEMA_VERSION,),
        )
