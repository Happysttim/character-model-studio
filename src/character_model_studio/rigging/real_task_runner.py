"""Background orchestration for the isolated real UniRig provider."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Slot

from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.rigging.providers.unirig import UniRigProvider
from character_model_studio.rigging.models import RigStatus
from character_model_studio.storage.repositories import LocalRepository
from character_model_studio.validation.rigged_model import RiggedModelValidator


class _Worker(QObject):
    progress = Signal(object)
    completed = Signal(str)
    failed = Signal(str)

    def __init__(
        self, repository: LocalRepository, attempt_id: str, token: CancellationToken
    ) -> None:
        super().__init__()
        self._repository = repository
        self._attempt_id = attempt_id
        self._token = token

    @Slot()
    def run(self) -> None:
        rig_id: str | None = None
        try:
            attempt = self._repository.get_attempt(self._attempt_id)
            if attempt.model_relative_path is None:
                raise RuntimeError("Accepted model has no GLB artifact")
            provider = UniRigProvider()
            rig = self._repository.create_rig_attempt(attempt.id, provider.name, "upstream-local")
            rig_id = rig.id
            self._repository.set_rig_attempt_status(rig_id, RigStatus.RIGGING)
            output = self._repository.attempt_artifact_path(attempt.id, f"rigs/{rig.id}/rigged.glb")
            work = self._repository.attempt_artifact_path(
                attempt.id, f"rigs/{rig.id}/provider-work"
            )
            result = provider.rig_glb(
                self._repository.projects_root / attempt.model_relative_path,
                work,
                output,
                self._token,
                self.progress.emit,
            )
            self._repository.set_rig_attempt_status(rig_id, RigStatus.VALIDATING)
            report = RiggedModelValidator().validate(result)
            if not report.acceptable:
                raise RuntimeError(f"Rig validation failed: {report.failures}")
            self._repository.complete_rig_attempt(rig.id, result, dict(report.metrics))
            self._repository.persist_rig_validation_report(rig.id, report)
            self.completed.emit(rig.id)
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            if rig_id is not None:
                self._repository.fail_rig_attempt(rig_id, str(error))
            self.failed.emit(str(error))


class RealRiggingTaskRunner(QObject):
    """Own the Qt thread while UniRig itself stays in its isolated child runtime."""

    progress = Signal(object)
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: _Worker | None = None

    def start(self, repository: LocalRepository, attempt_id: str) -> CancellationToken:
        if self._thread is not None:
            raise RuntimeError("A rigging task is already running")
        token = CancellationToken()
        thread = QThread(self)
        worker = _Worker(repository, attempt_id, token)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress)
        worker.completed.connect(self.completed)
        worker.failed.connect(self.failed)
        worker.completed.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._finish)
        self._thread, self._worker = thread, worker
        thread.start()
        return token

    @Slot()
    def _finish(self) -> None:
        thread = self._thread
        self._thread = None
        self._worker = None
        if thread is not None:
            thread.deleteLater()
