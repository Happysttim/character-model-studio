"""Local-only path resolution for the experimental Hunyuan3D-2GP lane."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from character_model_studio.platform.windows.paths import resolve_application_paths


@dataclass(frozen=True, slots=True)
class Hunyuan2GPPaths:
    """The source checkout and explicit local checkpoints required by Hunyuan3D-2GP."""

    source_directory: Path
    model_cache: Path

    @property
    def shape_directory(self) -> Path:
        return self.model_cache / "tencent" / "Hunyuan3D-2mv" / "hunyuan3d-dit-v2-mv"

    @property
    def delight_directory(self) -> Path:
        return self.model_cache / "tencent" / "Hunyuan3D-2" / "hunyuan3d-delight-v2-0"

    @property
    def paint_directory(self) -> Path:
        return self.model_cache / "tencent" / "Hunyuan3D-2" / "hunyuan3d-paint-v2-0"


def resolve_hunyuan2gp_paths() -> Hunyuan2GPPaths:
    """Resolve project-local defaults, allowing explicit user configuration overrides."""
    root = Path(__file__).resolve().parents[3]
    cache = resolve_application_paths().cache_directory / "hunyuan3d-2gp"
    # Development and portable launches may opt into a project-local data root.
    # Keep this as a path-resolution fallback, never a machine-specific path.
    project_cache = root / ".local" / "cache" / "hunyuan3d-2gp"
    if not (cache / "tencent" / "Hunyuan3D-2mv").exists() and project_cache.exists():
        cache = project_cache
    return Hunyuan2GPPaths(
        Path(
            os.environ.get(
                "CHARACTER_MODEL_STUDIO_HUNYUAN2GP_SOURCE_DIR", root / "external" / "Hunyuan3D-2GP"
            )
        ),
        Path(os.environ.get("CHARACTER_MODEL_STUDIO_HUNYUAN2GP_MODEL_CACHE", cache)),
    )
