"""Background static-model validation task for Qt workflows."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from character_model_studio.validation.model import ModelValidator


class _ValidationWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = path

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(ModelValidator().validate(self._path))
        except (OSError, RuntimeError, ValueError) as error:
            self.failed.emit(str(error))


class ModelValidationTaskRunner(QObject):
    """Run one static validation task off the UI thread."""

    completed = Signal(object)
    failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: _ValidationWorker | None = None
        self._outcome: tuple[str, object] | None = None

    def start(self, path: Path) -> None:
        """Start validation; a second concurrent request is rejected explicitly."""
        if self._thread is not None:
            raise RuntimeError("A model validation task is already running")
        thread = QThread(self)
        worker = _ValidationWorker(path)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.completed.connect(lambda report: self._record_outcome("completed", report))
        worker.failed.connect(lambda message: self._record_outcome("failed", message))
        worker.completed.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._finish)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _record_outcome(self, outcome: str, payload: object) -> None:
        self._outcome = (outcome, payload)

    def _finish(self) -> None:
        thread = self._thread
        if thread is not None and thread.isRunning():
            thread.wait(1000)
        self._thread = None
        self._worker = None
        if self._outcome is not None:
            outcome, payload = self._outcome
            self._outcome = None
            if outcome == "completed":
                self.completed.emit(payload)
            else:
                self.failed.emit(str(payload))
        if thread is not None:
            thread.deleteLater()
