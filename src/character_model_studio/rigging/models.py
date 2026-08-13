"""Stable rigging records shared by providers, persistence, validation, and UI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RigStatus(StrEnum):
    """Lifecycle state of a derivative rig attempt."""

    CREATED = "CREATED"
    RIGGING = "RIGGING"
    VALIDATING = "VALIDATING"
    READY_FOR_RIG_REVIEW = "READY_FOR_RIG_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class RigAttempt:
    """Project-relative metadata for a rigged derivative of an accepted model."""

    id: str
    model_attempt_id: str
    status: RigStatus
    provider: str
    provider_version: str | None
    rigged_relative_path: str | None
    source_relative_path: str
    metrics: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class RiggingProgress:
    """A provider progress event suitable for a Qt signal payload."""

    stage: str
    label: str
    completed: int
    total: int
