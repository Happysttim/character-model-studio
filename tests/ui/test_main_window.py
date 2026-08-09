"""Phase 01 Qt shell tests."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import QCheckBox, QPushButton

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
    assert window.current_destination == "projects"
    assert {button.text() for button in window.findChildren(QPushButton)} >= {
        "Projects",
        "Capture",
        "Processing",
        "Review",
        "Rig",
        "Animate",
        "Diagnostics",
    }


def test_navigation_and_reduce_motion_remain_available(qtbot, tmp_path) -> None:
    root = tmp_path / "application-data"
    paths = ApplicationPaths(
        root, root / "logs", root / "Projects", root / "cache", root / "metadata.sqlite3"
    )
    window = MainWindow(ApplicationContext(paths=paths, logger=logging.getLogger(__name__)))
    qtbot.addWidget(window)

    window.navigate("diagnostics")

    assert window.current_destination == "diagnostics"
    reduce_motion = window.findChild(QCheckBox)
    assert reduce_motion is not None
    reduce_motion.setChecked(True)
    assert window._motion_preferences.reduce_motion is True
