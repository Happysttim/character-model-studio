"""Minimal Phase 01 Qt main window."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QMainWindow, QWidget

from character_model_studio.app.bootstrap import ApplicationContext


class MainWindow(QMainWindow):
    """The empty native desktop shell that later phases populate."""

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self._context = context
        self.setObjectName("mainWindow")
        self.setWindowTitle("Character Model Studio")
        self.setMinimumSize(QSize(1180, 760))
        self.setCentralWidget(QWidget(self))
