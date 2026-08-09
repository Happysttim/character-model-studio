"""Phase 01 Qt shell tests."""

from __future__ import annotations

import logging

from character_model_studio.app.bootstrap import ApplicationContext
from character_model_studio.platform.windows.paths import ApplicationPaths
from character_model_studio.ui.main_window import MainWindow


def test_main_window_instantiates(qtbot, tmp_path) -> None:
    root = tmp_path / "application-data"
    paths = ApplicationPaths(
        root_directory=root,
        logs_directory=root / "logs",
        projects_directory=root / "Projects",
        cache_directory=root / "cache",
        database_path=root / "metadata.sqlite3",
    )
    window = MainWindow(ApplicationContext(paths=paths, logger=logging.getLogger(__name__)))

    qtbot.addWidget(window)
    window.show()

    assert window.minimumSize().width() == 1180
    assert window.windowTitle() == "Character Model Studio"
