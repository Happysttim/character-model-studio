"""Stable local-workflow domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from character_model_studio.domain.states import AttemptStatus


@dataclass(frozen=True, slots=True)
class Project:
    id: str
    name: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Capture:
    id: str
    project_id: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class ModelAttempt:
    id: str
    capture_id: str
    sequence_number: int
    status: AttemptStatus
    quality_mode: str
    provider: str
    model_relative_path: str | None
    texture_relative_path: str | None
    provider_version: str | None = None
    parameters: dict[str, object] | None = None
    metrics: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ProgressUpdate:
    stage: str
    label: str
    percent: int | None
    cancellable: bool
