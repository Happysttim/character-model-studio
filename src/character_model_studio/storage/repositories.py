"""SQLite repositories for the in-process local mock workflow."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING

from character_model_studio.domain.models import Capture, ModelAttempt, Project
from character_model_studio.domain.states import AttemptStatus, can_transition
from character_model_studio.rigging.fixture_glb import write_fixture_rigged_glb
from character_model_studio.rigging.models import RigAttempt, RigStatus

if TYPE_CHECKING:
    from character_model_studio.validation.model import ModelValidationReport
    from character_model_studio.validation.rigged_model import RiggedModelValidationReport


def _now() -> str:
    return datetime.now(UTC).isoformat()


class LocalRepository:
    """Metadata repository; binary artifacts remain in project-relative folders."""

    def __init__(self, database_path: Path, projects_root: Path) -> None:
        self._database_path = database_path
        self._projects_root = projects_root

    @property
    def projects_root(self) -> Path:
        """Return the managed root used to resolve project-relative artifacts."""
        return self._projects_root

    def create_project(self, name: str) -> Project:
        project_id = uuid.uuid4().hex
        created_at = _now()
        (self._projects_root / project_id / "captures").mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO projects VALUES (?, ?, ?)", (project_id, name, created_at)
            )
        return Project(project_id, name, datetime.fromisoformat(created_at))

    def list_projects(self) -> list[Project]:
        """Return local project history in stable newest-first order for reopening."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, name, created_at FROM projects ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [Project(row[0], row[1], datetime.fromisoformat(row[2])) for row in rows]

    def get_project(self, project_id: str) -> Project:
        """Reopen one persisted project record by its stable local identifier."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, name, created_at FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown local project: {project_id}")
        return Project(row[0], row[1], datetime.fromisoformat(row[2]))

    def recover_interrupted_attempts(self) -> int:
        """Mark transient attempts failed after an abnormal application exit."""
        transient = tuple(
            status.value
            for status in (
                AttemptStatus.PREPROCESSING,
                AttemptStatus.RECONSTRUCTING,
                AttemptStatus.TEXTURING,
                AttemptStatus.VALIDATING_MODEL,
            )
        )
        placeholders = ", ".join("?" for _ in transient)
        with self._connect() as connection:
            cursor = connection.execute(
                f"UPDATE model_attempts SET status = ?, finished_at = ? "
                f"WHERE status IN ({placeholders})",
                (AttemptStatus.FAILED.value, _now(), *transient),
            )
        return cursor.rowcount

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

    def register_capture_file(self, project_id: str, source_path: Path) -> Capture:
        """Copy a user-approved local capture into its managed project-relative location."""
        if not source_path.is_file():
            raise FileNotFoundError(f"Capture file does not exist: {source_path}")
        capture_id = uuid.uuid4().hex
        suffix = source_path.suffix.lower() or ".mp4"
        relative_path = f"{project_id}/captures/{capture_id}/capture{suffix}"
        destination = self._projects_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy2(source_path, destination)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO captures VALUES (?, ?, ?)", (capture_id, project_id, relative_path)
            )
        return Capture(capture_id, project_id, relative_path)

    def import_glb_for_review(self, source_path: Path) -> ModelAttempt:
        """Copy a selected GLB into a new local project and make it reviewable."""
        if source_path.suffix.lower() != ".glb":
            raise ValueError("Only GLB assets can be imported into Review")
        if not source_path.is_file():
            raise FileNotFoundError(f"GLB asset does not exist: {source_path}")
        project = self.create_project("Imported GLB")
        capture_id = uuid.uuid4().hex
        source_relative = f"{project.id}/imports/{capture_id}/source.glb"
        destination = self._projects_root / source_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy2(source_path, destination)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO captures VALUES (?, ?, ?)", (capture_id, project.id, source_relative)
            )
        attempt = self.create_attempt(
            capture_id,
            "imported",
            provider="local-glb-import",
            parameters={"source": "user-selected-local-glb"},
        )
        self.transition_attempt(attempt.id, AttemptStatus.PREPROCESSING)
        self.transition_attempt(attempt.id, AttemptStatus.RECONSTRUCTING)
        self.transition_attempt(
            attempt.id,
            AttemptStatus.VALIDATING_MODEL,
            model_path=source_relative,
            texture_path=source_relative,
        )
        return self.transition_attempt(attempt.id, AttemptStatus.READY_FOR_REVIEW)

    def create_attempt(
        self,
        capture_id: str,
        quality_mode: str,
        *,
        provider: str | None = None,
        provider_version: str | None = None,
        parameters: dict[str, object] | None = None,
    ) -> ModelAttempt:
        if quality_mode not in {"standard", "high_quality", "experimental_textured", "imported"}:
            raise ValueError(f"Unsupported mock quality mode: {quality_mode}")
        provider = provider or (
            "mock-hunyuan3d-2" if quality_mode == "standard" else "mock-hunyuan3d-2.1"
        )
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
                "(id, capture_id, sequence_number, status, quality_mode, provider, "
                "provider_version, "
                "parameters_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    attempt_id,
                    capture_id,
                    sequence,
                    AttemptStatus.CREATED.value,
                    quality_mode,
                    provider,
                    provider_version,
                    json.dumps(parameters or {}),
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
            provider_version,
            parameters or {},
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
                "provider, model_relative_path, texture_relative_path, provider_version, "
                "parameters_json, metrics_json "
                "FROM model_attempts WHERE capture_id = ? ORDER BY sequence_number",
                (capture_id,),
            ).fetchall()
        return [
            ModelAttempt(
                row[0],
                row[1],
                row[2],
                AttemptStatus(row[3]),
                row[4],
                row[5],
                row[6],
                row[7],
                row[8],
                json.loads(row[9] or "{}"),
                json.loads(row[10]) if row[10] else None,
            )
            for row in rows
        ]

    def latest_accepted_attempt(self) -> ModelAttempt | None:
        """Return the most recently accepted source model for the Rig handoff."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id FROM model_attempts WHERE status = ? "
                "ORDER BY finished_at DESC, id DESC LIMIT 1",
                (AttemptStatus.ACCEPTED.value,),
            ).fetchone()
        return None if row is None else self.get_attempt(str(row[0]))

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
                "provider, model_relative_path, texture_relative_path, provider_version, "
                "parameters_json, metrics_json "
                "FROM model_attempts WHERE id = ?",
                (attempt_id,),
            ).fetchone()
        if row is None:
            raise KeyError(attempt_id)
        return ModelAttempt(
            row[0],
            row[1],
            row[2],
            AttemptStatus(row[3]),
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
            json.loads(row[9] or "{}"),
            json.loads(row[10]) if row[10] else None,
        )

    def get_capture(self, capture_id: str) -> Capture:
        """Return capture metadata needed by a local preprocessing worker."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, project_id, relative_path FROM captures WHERE id = ?", (capture_id,)
            ).fetchone()
        if row is None:
            raise KeyError(capture_id)
        return Capture(row[0], row[1], row[2])

    def persist_attempt_metrics(self, attempt_id: str, metrics: dict[str, object]) -> None:
        """Store non-sensitive, reproducible runtime metrics for a local AI attempt."""
        with self._connect() as connection:
            connection.execute(
                "UPDATE model_attempts SET metrics_json = ? WHERE id = ?",
                (json.dumps(metrics), attempt_id),
            )

    def write_attempt_metadata(self, attempt_id: str, metadata: dict[str, object]) -> Path:
        """Persist project-relative provenance without retaining raw input bytes in SQLite."""
        output = self.attempt_artifact_path(attempt_id, "attempt.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return output

    def decide(self, attempt_id: str, accepted: bool, reason: str | None = None) -> ModelAttempt:
        target = AttemptStatus.ACCEPTED if accepted else AttemptStatus.REJECTED
        attempt = self.transition_attempt(attempt_id, target)
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO model_reviews VALUES (?, ?, ?, ?)",
                (attempt_id, target.value, reason, _now()),
            )
        return attempt

    def persist_validation_report(self, attempt_id: str, report: ModelValidationReport) -> None:
        """Persist the technical static-model report independently of viewer rendering."""
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO validation_reports VALUES (?, ?, ?, ?)",
                (attempt_id, report.overall_status.value, json.dumps(report.as_dict()), _now()),
            )

    def validation_status(self, attempt_id: str) -> str | None:
        """Return the persisted static validation outcome for an attempt, when available."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT overall_status FROM validation_reports WHERE attempt_id = ?", (attempt_id,)
            ).fetchone()
        return None if row is None else str(row[0])

    def create_mock_rig(self, attempt_id: str) -> str:
        """Create an explicitly marked fixture rig for non-provider UI and validation tests."""
        attempt = self.get_attempt(attempt_id)
        if attempt.status is not AttemptStatus.ACCEPTED:
            raise ValueError("Mock rigging requires an accepted model attempt")
        rig_id = uuid.uuid4().hex
        output = self.attempt_artifact_path(attempt_id, f"rigs/{rig_id}/rigged.glb")
        output.parent.mkdir(parents=True, exist_ok=True)
        write_fixture_rigged_glb(output)
        rig_path = self.as_project_relative_path(output)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO rig_attempts
                (id, model_attempt_id, status, rigged_relative_path, provider, provider_version,
                 source_relative_path, metrics_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rig_id,
                    attempt_id,
                    RigStatus.READY_FOR_RIG_REVIEW.value,
                    rig_path,
                    "fixture-rigging",
                    "1",
                    attempt.model_relative_path or "",
                    json.dumps({"mock": True, "joint_count": 2, "skinned_vertex_count": 4}),
                ),
            )
        return rig_id

    def create_rig_attempt(
        self, attempt_id: str, provider: str, provider_version: str | None
    ) -> RigAttempt:
        """Create a derivative rig attempt without modifying the accepted source asset."""
        attempt = self.get_attempt(attempt_id)
        if attempt.status is not AttemptStatus.ACCEPTED or attempt.model_relative_path is None:
            raise ValueError("Rigging requires an accepted model artifact")
        rig_id = uuid.uuid4().hex
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO rig_attempts
                (id, model_attempt_id, status, rigged_relative_path, provider, provider_version,
                 source_relative_path, metrics_json)
                VALUES (?, ?, ?, NULL, ?, ?, ?, NULL)
                """,
                (
                    rig_id,
                    attempt_id,
                    RigStatus.CREATED.value,
                    provider,
                    provider_version,
                    attempt.model_relative_path,
                ),
            )
        return self.get_rig_attempt(rig_id)

    def get_rig_attempt(self, rig_id: str) -> RigAttempt:
        """Return one persisted rig attempt."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, model_attempt_id, status, provider, provider_version,
                       rigged_relative_path, source_relative_path, metrics_json
                FROM rig_attempts WHERE id = ?
                """,
                (rig_id,),
            ).fetchone()
        if row is None:
            raise KeyError(rig_id)
        return RigAttempt(
            row[0],
            row[1],
            RigStatus(row[2]),
            row[3],
            row[4],
            row[5],
            row[6],
            None if row[7] is None else json.loads(row[7]),
        )

    def list_rig_attempts(self, model_attempt_id: str | None = None) -> list[RigAttempt]:
        """List rig derivatives without exposing absolute file paths to application layers."""
        query = """
            SELECT id, model_attempt_id, status, provider, provider_version,
                   rigged_relative_path, source_relative_path, metrics_json
            FROM rig_attempts
        """
        parameters: tuple[str, ...] = ()
        if model_attempt_id is not None:
            query += " WHERE model_attempt_id = ?"
            parameters = (model_attempt_id,)
        query += " ORDER BY rowid DESC"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [
            RigAttempt(
                row[0],
                row[1],
                RigStatus(row[2]),
                row[3],
                row[4],
                row[5],
                row[6],
                None if row[7] is None else json.loads(row[7]),
            )
            for row in rows
        ]

    def complete_rig_attempt(
        self, rig_id: str, rigged_path: Path, metrics: dict[str, object]
    ) -> RigAttempt:
        """Publish only a completed rig artifact and preserve the static source asset."""
        relative_path = self.as_project_relative_path(rigged_path)
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE rig_attempts
                SET status = ?, rigged_relative_path = ?, metrics_json = ?
                WHERE id = ?
                """,
                (RigStatus.READY_FOR_RIG_REVIEW.value, relative_path, json.dumps(metrics), rig_id),
            )
        return self.get_rig_attempt(rig_id)

    def set_rig_attempt_status(self, rig_id: str, status: RigStatus) -> RigAttempt:
        """Advance a rig derivative without changing its accepted source artifact."""
        with self._connect() as connection:
            connection.execute(
                "UPDATE rig_attempts SET status = ? WHERE id = ?",
                (status.value, rig_id),
            )
        return self.get_rig_attempt(rig_id)

    def fail_rig_attempt(self, rig_id: str, reason: str) -> RigAttempt:
        """Record a recoverable rigging failure while retaining the static source."""
        with self._connect() as connection:
            connection.execute(
                "UPDATE rig_attempts SET status = ?, metrics_json = ? WHERE id = ?",
                (RigStatus.FAILED.value, json.dumps({"failure_reason": reason}), rig_id),
            )
        return self.get_rig_attempt(rig_id)

    def persist_rig_validation_report(
        self, rig_id: str, report: RiggedModelValidationReport
    ) -> None:
        """Persist the independent rig report for review and animation gating."""
        report_dict = report.as_dict()
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO rig_validation_reports VALUES (?, ?, ?, ?)",
                (rig_id, report.overall_status.value, json.dumps(report_dict), _now()),
            )

    def rig_validation_status(self, rig_id: str) -> str | None:
        """Return the persisted independent rig validation status."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT overall_status FROM rig_validation_reports WHERE rig_attempt_id = ?",
                (rig_id,),
            ).fetchone()
        return None if row is None else str(row[0])

    def save_pose_document(self, rig_id: str, name: str, payload: dict[str, object]) -> str:
        """Persist one named quaternion pose for a validated rig revision."""
        if self.rig_validation_status(rig_id) != "PASS":
            raise ValueError("Pose editing requires a rig that passed validation")
        pose_id = uuid.uuid4().hex
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM pose_documents WHERE rig_attempt_id = ? AND name = ?", (rig_id, name)
            )
            connection.execute(
                "INSERT INTO pose_documents VALUES (?, ?, ?, ?)",
                (pose_id, rig_id, name, json.dumps(payload)),
            )
        return pose_id

    def load_pose_documents(self, rig_id: str) -> dict[str, dict[str, object]]:
        """Return named pose payloads for reopening the local animation editor."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT name, payload_json FROM pose_documents WHERE rig_attempt_id = ?", (rig_id,)
            ).fetchall()
        return {str(name): json.loads(payload) for name, payload in rows}

    def save_animation_clip(self, rig_id: str, name: str, payload: dict[str, object]) -> str:
        """Persist timeline settings without coupling them to a UI widget."""
        if self.rig_validation_status(rig_id) != "PASS":
            raise ValueError("Animation playback requires a rig that passed validation")
        clip_id = uuid.uuid4().hex
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM animation_clips WHERE rig_attempt_id = ? AND name = ?", (rig_id, name)
            )
            connection.execute(
                "INSERT INTO animation_clips VALUES (?, ?, ?, ?)",
                (clip_id, rig_id, name, json.dumps(payload)),
            )
        return clip_id

    def load_animation_clip(self, rig_id: str, name: str = "From-To") -> dict[str, object] | None:
        """Load one saved local timeline configuration for a rig revision."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM animation_clips WHERE rig_attempt_id = ? AND name = ?",
                (rig_id, name),
            ).fetchone()
        return None if row is None else json.loads(row[0])

    def save_pose_and_animation(self, rig_id: str) -> tuple[str, str]:
        """Keep the legacy mock-fixture helper independent from production validation gates."""
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

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Yield one short-lived SQLite connection and always release its Windows file handle."""
        connection = sqlite3.connect(self._database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
