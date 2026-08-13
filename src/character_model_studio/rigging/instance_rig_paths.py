"""Project-local discovery for the optional isolated Instance-Rig provider."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from character_model_studio.platform.windows.paths import resolve_application_paths


@dataclass(frozen=True, slots=True)
class InstanceRigPaths:
    """Configurable source, isolated runtime, and model cache paths."""

    source_directory: Path
    runtime_python: Path
    model_cache: Path


def resolve_instance_rig_paths() -> InstanceRigPaths:
    """Resolve only portable defaults and explicit user settings."""
    root = Path(__file__).resolve().parents[3]
    source = Path(
        os.environ.get(
            "CHARACTER_MODEL_STUDIO_INSTANCE_RIG_SOURCE_DIR", root / "external" / "instance-rig"
        )
    )
    runtime = Path(
        os.environ.get(
            "CHARACTER_MODEL_STUDIO_INSTANCE_RIG_PYTHON",
            source / ".venv" / "Scripts" / "python.exe",
        )
    )
    cache = Path(
        os.environ.get(
            "CHARACTER_MODEL_STUDIO_INSTANCE_RIG_MODEL_CACHE",
            resolve_application_paths().cache_directory / "instance-rig",
        )
    )
    return InstanceRigPaths(source, runtime, cache)
