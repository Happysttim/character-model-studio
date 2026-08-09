"""Background static-model validation task for Qt workflows."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from character_model_studio.storage.repositories import LocalRepository
from character_model_studio.validation.model import ModelValidator


class _ValidationWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        path: Path,
        repository: LocalRepository | None = None,
        attempt_id: str | None = None,
    ) -> None:
        super().__init__()
        self._path = path
        self._repository = repository
        self._attempt_id = attempt_id

    @Slot()
    def run(self) -> None:
        try:
            report = ModelValidator().validate(self._path)
            if self._repository is not None and self._attempt_id is not None:
                self._repository.persist_validation_report(self._attempt_id, report)
            self.completed.emit(report)
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
        self._start_worker(path)

    def start_attempt(self, repository: LocalRepository, attempt_id: str) -> None:
        """Validate and persist an existing attempt's GLB outside the UI thread."""
        attempt = repository.get_attempt(attempt_id)
        if attempt.model_relative_path is None:
            raise ValueError("The attempt has no generated model artifact")
        self._start_worker(
            repository.projects_root / attempt.model_relative_path, repository, attempt_id
        )

    def _start_worker(
        self,
        path: Path,
        repository: LocalRepository | None = None,
        attempt_id: str | None = None,
    ) -> None:
        if self._thread is not None:
            raise RuntimeError("A model validation task is already running")
        thread = QThread(self)
        worker = _ValidationWorker(path, repository, attempt_id)
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
