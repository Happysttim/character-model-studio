"""Qt-threaded execution lane for local reconstruction providers."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Slot

from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.domain.states import AttemptStatus
from character_model_studio.reconstruction.mock import MockReconstructionProvider
from character_model_studio.reconstruction.standard_workflow import StandardShapeWorkflow
from character_model_studio.storage.repositories import LocalRepository


class _ReconstructionWorker(QObject):
    progress = Signal(object)
    completed = Signal(str)
    cancelled = Signal(str)
    failed = Signal(str, str)

    def __init__(
        self,
        repository: LocalRepository,
        attempt_id: str,
        token: CancellationToken,
    ) -> None:
        super().__init__()
        self._repository = repository
        self._attempt_id = attempt_id
        self._token = token

    @Slot()
    def run(self) -> None:
        try:
            MockReconstructionProvider().run(
                self._repository, self._attempt_id, self._token, self.progress.emit
            )
            status = self._repository.get_attempt(self._attempt_id).status
            if status is AttemptStatus.CANCELLED:
                self.cancelled.emit(self._attempt_id)
            elif status is AttemptStatus.READY_FOR_REVIEW:
                self.completed.emit(self._attempt_id)
            else:
                self.failed.emit(self._attempt_id, f"Unexpected terminal state: {status}")
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            self.failed.emit(self._attempt_id, str(error))


class MockWorkflowTaskRunner(QObject):
    """Runs one mock reconstruction attempt outside the Qt UI thread."""

    progress = Signal(object)
    completed = Signal(str)
    cancelled = Signal(str)
    failed = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: _ReconstructionWorker | None = None
        self._outcome: tuple[str, tuple[str, ...]] | None = None

    def start(self, repository: LocalRepository, attempt_id: str) -> CancellationToken:
        """Start an attempt and return the token used to request cancellation."""
        if self._thread is not None:
            raise RuntimeError("A reconstruction task is already running")
        token = CancellationToken()
        thread = QThread(self)
        worker = _ReconstructionWorker(repository, attempt_id, token)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress)
        worker.completed.connect(
            lambda completed_id: self._record_outcome("completed", completed_id)
        )
        worker.cancelled.connect(
            lambda cancelled_id: self._record_outcome("cancelled", cancelled_id)
        )
        worker.failed.connect(
            lambda failed_id, detail: self._record_outcome("failed", failed_id, detail)
        )
        worker.completed.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._finish_task)
        self._thread = thread
        self._worker = worker
        thread.start()
        return token

    @Slot()
    def _finish_task(self) -> None:
        self._worker = None
        self._thread = None
        if self._outcome is not None:
            outcome, arguments = self._outcome
            self._outcome = None
            if outcome == "completed":
                self.completed.emit(arguments[0])
            elif outcome == "cancelled":
                self.cancelled.emit(arguments[0])
            else:
                self.failed.emit(arguments[0], arguments[1])

    def _record_outcome(self, outcome: str, *arguments: str) -> None:
        self._outcome = (outcome, arguments)


class _RealReconstructionWorker(QObject):
    """Qt worker that keeps all real CUDA work off the GUI thread."""

    progress = Signal(object)
    completed = Signal(str)
    cancelled = Signal(str)
    failed = Signal(str, str)

    def __init__(
        self, repository: LocalRepository, attempt_id: str, token: CancellationToken
    ) -> None:
        super().__init__()
        self._repository = repository
        self._attempt_id = attempt_id
        self._token = token

    @Slot()
    def run(self) -> None:
        try:
            StandardShapeWorkflow().run(
                self._repository, self._attempt_id, self._token, self.progress.emit
            )
            status = self._repository.get_attempt(self._attempt_id).status
            if status is AttemptStatus.CANCELLED:
                self.cancelled.emit(self._attempt_id)
            elif status is AttemptStatus.READY_FOR_REVIEW:
                self.completed.emit(self._attempt_id)
            else:
                self.failed.emit(self._attempt_id, f"Unexpected terminal state: {status}")
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            self.failed.emit(self._attempt_id, str(error))


class RealStandardWorkflowTaskRunner(QObject):
    """Runs local Hunyuan3D 2.0 Standard Shape work in an application-owned Qt thread."""

    progress = Signal(object)
    completed = Signal(str)
    cancelled = Signal(str)
    failed = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: _RealReconstructionWorker | None = None
        self._outcome: tuple[str, tuple[str, ...]] | None = None

    def start(self, repository: LocalRepository, attempt_id: str) -> CancellationToken:
        """Start one real CUDA attempt and return its cooperative cancellation token."""
        if self._thread is not None:
            raise RuntimeError("A reconstruction task is already running")
        token = CancellationToken()
        thread = QThread(self)
        worker = _RealReconstructionWorker(repository, attempt_id, token)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress)
        worker.completed.connect(lambda item_id: self._record_outcome("completed", item_id))
        worker.cancelled.connect(lambda item_id: self._record_outcome("cancelled", item_id))
        worker.failed.connect(
            lambda item_id, detail: self._record_outcome("failed", item_id, detail)
        )
        worker.completed.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._finish_task)
        self._thread = thread
        self._worker = worker
        thread.start()
        return token

    @Slot()
    def _finish_task(self) -> None:
        thread = self._thread
        self._worker = None
        self._thread = None
        if self._outcome is not None:
            outcome, arguments = self._outcome
            self._outcome = None
            if outcome == "completed":
                self.completed.emit(arguments[0])
            elif outcome == "cancelled":
                self.cancelled.emit(arguments[0])
            else:
                self.failed.emit(arguments[0], arguments[1])
        if thread is not None:
            thread.deleteLater()

    def _record_outcome(self, outcome: str, *arguments: str) -> None:
        self._outcome = (outcome, arguments)
