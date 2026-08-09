"""User-writable Windows path resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ApplicationPaths:
    """User-local application directories kept outside the installation directory."""

    root_directory: Path
    logs_directory: Path
    projects_directory: Path
    cache_directory: Path
    database_path: Path

    def ensure_exists(self) -> None:
        """Create the local application directories if they are absent."""
        for directory in (
            self.root_directory,
            self.logs_directory,
            self.projects_directory,
            self.cache_directory,
        ):
            directory.mkdir(parents=True, exist_ok=True)


def resolve_application_paths() -> ApplicationPaths:
    """Resolve user-local storage without embedding machine-specific paths."""
    configured_root = os.environ.get("CHARACTER_MODEL_STUDIO_DATA_DIR")
    if configured_root:
        root_directory = Path(configured_root)
    else:
        local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        root_directory = local_app_data / "CharacterModelStudio"
    return ApplicationPaths(
        root_directory=root_directory,
        logs_directory=root_directory / "logs",
        projects_directory=root_directory / "Projects",
        cache_directory=root_directory / "cache",
        database_path=root_directory / "character-model-studio.sqlite3",
    )
