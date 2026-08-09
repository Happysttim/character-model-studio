"""Local path resolution tests."""

from __future__ import annotations

from pathlib import Path

from character_model_studio.platform.windows.paths import ApplicationPaths


def test_application_paths_create_expected_directories(tmp_path: Path) -> None:
    root = tmp_path / "application-data"
    paths = ApplicationPaths(
        root_directory=root,
        logs_directory=root / "logs",
        projects_directory=root / "Projects",
        cache_directory=root / "cache",
        database_path=root / "metadata.sqlite3",
    )

    paths.ensure_exists()

    assert paths.logs_directory.is_dir()
    assert paths.projects_directory.is_dir()
    assert paths.cache_directory.is_dir()
