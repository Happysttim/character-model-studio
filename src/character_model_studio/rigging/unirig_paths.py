"""Local-only discovery for an optional UniRig checkout and its isolated runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from character_model_studio.platform.windows.paths import resolve_application_paths


@dataclass(frozen=True, slots=True)
class UniRigPaths:
    """User-configurable paths; no machine-specific path is persisted in code."""

    source_directory: Path
    runtime_python: Path
    model_cache: Path


def resolve_unirig_paths() -> UniRigPaths:
    """Resolve the optional provider checkout, isolated Python, and local checkpoint cache."""
    root = Path(__file__).resolve().parents[3]
    source = Path(
        os.environ.get("CHARACTER_MODEL_STUDIO_UNIRIG_SOURCE_DIR", root / "external" / "UniRig")
    )
    runtime = Path(
        os.environ.get(
            "CHARACTER_MODEL_STUDIO_UNIRIG_PYTHON",
            source / ".venv" / "Scripts" / "python.exe",
        )
    )
    cache = Path(
        os.environ.get(
            "CHARACTER_MODEL_STUDIO_UNIRIG_MODEL_CACHE",
            resolve_application_paths().cache_directory / "unirig",
        )
    )
    return UniRigPaths(source, runtime, cache)
