"""SQLite repositories for the in-process local mock workflow."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

import trimesh

from character_model_studio.domain.models import Capture, ModelAttempt, Project
from character_model_studio.domain.states import AttemptStatus, can_transition


def _now() -> str:
    return datetime.now(UTC).isoformat()


class LocalRepository:
    """Metadata repository; binary artifacts remain in project-relative folders."""

    def __init__(self, database_path: Path, projects_root: Path) -> None:
        self._database_path = database_path
        self._projects_root = projects_root

    def create_project(self, name: str) -> Project:
        project_id = uuid.uuid4().hex
        created_at = _now()
        (self._projects_root / project_id / "captures").mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO projects VALUES (?, ?, ?)", (project_id, name, created_at)
            )
        return Project(project_id, name, datetime.fromisoformat(created_at))

    def create_fixture_capture(self, project_id: str) -> Capture:
        capture_id = uuid.uuid4().hex
        relative_path = f"{project_id}/captures/{capture_id}/fixture.mp4"
        artifact = self._projects_root / relative_path
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"mock-capture-fixture")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO captures VALUES (?, ?, ?)", (capture_id, project_id, relative_path)
            )
        return Capture(capture_id, project_id, relative_path)

    def create_attempt(self, capture_id: str, quality_mode: str) -> ModelAttempt:
        if quality_mode not in {"standard", "high_quality"}:
            raise ValueError(f"Unsupported mock quality mode: {quality_mode}")
        provider = "mock-hunyuan3d-2" if quality_mode == "standard" else "mock-hunyuan3d-2.1"
        attempt_id = uuid.uuid4().hex
        with self._connect() as connection:
            sequence = (
                connection.execute(
                    "SELECT COUNT(*) FROM model_attempts WHERE capture_id = ?", (capture_id,)
                ).fetchone()[0]
                + 1
            )
            connection.execute(
                "INSERT INTO model_attempts "
                "(id, capture_id, sequence_number, status, quality_mode, provider, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    attempt_id,
                    capture_id,
                    sequence,
                    AttemptStatus.CREATED.value,
                    quality_mode,
                    provider,
                    _now(),
                ),
            )
        return ModelAttempt(
            attempt_id,
            capture_id,
            sequence,
            AttemptStatus.CREATED,
            quality_mode,
            provider,
            None,
            None,
        )

    def regenerate(self, attempt_id: str) -> ModelAttempt:
        """Create the next attempt for the same capture and persisted quality mode."""
        attempt = self.get_attempt(attempt_id)
        return self.create_attempt(attempt.capture_id, attempt.quality_mode)

    def list_attempts(self, capture_id: str) -> list[ModelAttempt]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, capture_id, sequence_number, status, quality_mode, "
                "provider, model_relative_path, texture_relative_path "
                "FROM model_attempts WHERE capture_id = ? ORDER BY sequence_number",
                (capture_id,),
            ).fetchall()
        return [
            ModelAttempt(
                row[0], row[1], row[2], AttemptStatus(row[3]), row[4], row[5], row[6], row[7]
            )
            for row in rows
        ]

    def attempt_artifact_path(self, attempt_id: str, filename: str) -> Path:
        """Return the project-local output location for an attempt artifact."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT captures.project_id FROM model_attempts "
                "JOIN captures ON captures.id = model_attempts.capture_id "
                "WHERE model_attempts.id = ?",
                (attempt_id,),
            ).fetchone()
        if row is None:
            raise KeyError(attempt_id)
        project_id: str = row[0]
        return self._projects_root / project_id / "attempts" / attempt_id / filename

    def as_project_relative_path(self, path: Path) -> str:
        """Serialize an artifact path without exposing an installation-specific root."""
        return str(path.relative_to(self._projects_root))

    def transition_attempt(
        self,
        attempt_id: str,
        target: AttemptStatus,
        model_path: str | None = None,
        texture_path: str | None = None,
    ) -> ModelAttempt:
        attempt = self.get_attempt(attempt_id)
        if not can_transition(attempt.status, target):
            raise ValueError(f"Invalid transition: {attempt.status} -> {target}")
        finished_at = (
            _now()
            if target
            in {AttemptStatus.READY_FOR_REVIEW, AttemptStatus.CANCELLED, AttemptStatus.FAILED}
            else None
        )
        with self._connect() as connection:
            connection.execute(
                "UPDATE model_attempts SET status = ?, "
                "model_relative_path = COALESCE(?, model_relative_path), "
                "texture_relative_path = COALESCE(?, texture_relative_path), "
                "finished_at = COALESCE(?, finished_at) WHERE id = ?",
                (target.value, model_path, texture_path, finished_at, attempt_id),
            )
        return self.get_attempt(attempt_id)

    def get_attempt(self, attempt_id: str) -> ModelAttempt:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, capture_id, sequence_number, status, quality_mode, "
                "provider, model_relative_path, texture_relative_path "
                "FROM model_attempts WHERE id = ?",
                (attempt_id,),
            ).fetchone()
        if row is None:
            raise KeyError(attempt_id)
        return ModelAttempt(
            row[0], row[1], row[2], AttemptStatus(row[3]), row[4], row[5], row[6], row[7]
        )

    def decide(self, attempt_id: str, accepted: bool, reason: str | None = None) -> ModelAttempt:
        target = AttemptStatus.ACCEPTED if accepted else AttemptStatus.REJECTED
        attempt = self.transition_attempt(attempt_id, target)
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO model_reviews VALUES (?, ?, ?, ?)",
                (attempt_id, target.value, reason, _now()),
            )
        return attempt

    def create_mock_rig(self, attempt_id: str) -> str:
        attempt = self.get_attempt(attempt_id)
        if attempt.status is not AttemptStatus.ACCEPTED:
            raise ValueError("Mock rigging requires an accepted model attempt")
        rig_id = uuid.uuid4().hex
        output = self.attempt_artifact_path(attempt_id, f"rigs/{rig_id}/rigged.glb")
        output.parent.mkdir(parents=True, exist_ok=True)
        trimesh.creation.icosphere(subdivisions=1).export(output)
        rig_path = self.as_project_relative_path(output)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO rig_attempts VALUES (?, ?, ?, ?)",
                (rig_id, attempt_id, "READY_FOR_RIG_REVIEW", rig_path),
            )
        return rig_id

    def save_pose_and_animation(self, rig_id: str) -> tuple[str, str]:
        pose_id, clip_id = uuid.uuid4().hex, uuid.uuid4().hex
        pose = json.dumps({"schemaVersion": 1, "bones": {}})
        clip = json.dumps({"schemaVersion": 1, "durationMs": 1000, "loopPreview": True})
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO pose_documents VALUES (?, ?, ?, ?)", (pose_id, rig_id, "From", pose)
            )
            connection.execute(
                "INSERT INTO animation_clips VALUES (?, ?, ?, ?)",
                (clip_id, rig_id, "Fixture", clip),
            )
        return pose_id, clip_id

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
