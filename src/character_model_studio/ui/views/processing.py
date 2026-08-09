"""Visible local reconstruction progress and concise task-log workspace."""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QProgressBar, QVBoxLayout, QWidget

from character_model_studio.domain.models import ProgressUpdate
from character_model_studio.ui.widgets.glass import GlassPanel


class ProcessingWorkspace(QWidget):
    """Shows the active local task without pretending a server-side job exists."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = GlassPanel("secondary", self)
        panel_layout = QVBoxLayout(panel)
        self._status = QLabel("No active reconstruction task.", panel)
        self._progress = QProgressBar(panel)
        self._log = QPlainTextEdit(panel)
        self._log.setObjectName("processingLog")
        self._log.setReadOnly(True)
        self._log.setMaximumBlockCount(200)
        log_font = QFont()
        log_font.setFamilies(["Noto Sans KR", "Noto Sans", "Segoe UI", "Malgun Gothic"])
        log_font.setPointSize(10)
        self._log.setFont(log_font)
        panel_layout.addWidget(self._status)
        panel_layout.addWidget(self._progress)
        panel_layout.addWidget(self._log, stretch=1)
        layout.addWidget(panel)

    def begin(self, attempt_id: str) -> None:
        self._status.setText("Preparing local Standard Shape reconstruction")
        self._progress.setRange(0, 0)
        self._log.setPlainText(f"Attempt {attempt_id}: queued locally")

    def update_progress(self, update: ProgressUpdate) -> None:
        self._status.setText(update.label)
        if update.percent is None:
            self._progress.setRange(0, 0)
        else:
            self._progress.setRange(0, 100)
            self._progress.setValue(update.percent)
        self._log.appendPlainText(f"[{update.stage}] {update.label}")

    def finish(self, message: str, success: bool) -> None:
        self._progress.setRange(0, 100)
        self._progress.setValue(100 if success else 0)
        self._status.setText(message)
        self._log.appendPlainText(message)
