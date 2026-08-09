"""Desktop application entry point."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from character_model_studio.app.bootstrap import create_application_context
from character_model_studio.ui.main_window import MainWindow
from character_model_studio.ui.theme import application_stylesheet


def run(argv: Sequence[str] | None = None) -> int:
    """Start the native Qt desktop application."""
    application = QApplication(list(argv) if argv is not None else sys.argv)
    application.setStyle("Fusion")
    application.setStyleSheet(application_stylesheet())
    context = create_application_context()
    window = MainWindow(context)
    window.show()
    return application.exec()
