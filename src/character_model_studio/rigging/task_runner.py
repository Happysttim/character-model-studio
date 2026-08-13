"""Qt-owned background lane for rigging work and explicit fixture demonstrations."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.rigging.models import RiggingProgress
from character_model_studio.rigging.providers.mock import MockRiggingProvider
from character_model_studio.storage.repositories import LocalRepository


class FixtureRiggingTaskRunner(QThread):
    """Run the non-production fixture path outside the Qt UI thread.

    It exists solely to exercise the UI and downstream validation when no real
    compatible CUDA rigging provider is configured.  The emitted status makes that
    distinction explicit to callers.
    """

    progress = Signal(object)
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)
        self._repository: LocalRepository | None = None
        self._attempt_id: str | None = None
        self._token = CancellationToken()

    def start_for_attempt(self, repository: LocalRepository, attempt_id: str) -> None:
        """Configure exactly one fixture run before starting its worker thread."""
        if self.isRunning():
            raise RuntimeError("A rigging task is already running")
        self._repository = repository
        self._attempt_id = attempt_id
        self._token = CancellationToken()
        self.start()

    def cancel(self) -> None:
        """Request cancellation before the fixture is published."""
        self._token.cancel()

    def run(self) -> None:
        """Publish a valid fixture rig without impersonating CUDA inference."""
        try:
            repository = self._repository
            attempt_id = self._attempt_id
            if repository is None or attempt_id is None:
                raise RuntimeError("Rigging task was not configured")
            self.progress.emit(RiggingProgress("fixture_rig", "Preparing fixture rig", 0, 2))
            if self._token.is_cancelled:
                raise RuntimeError("Rigging fixture was cancelled")
            rig_id = MockRiggingProvider().run(repository, attempt_id)
            if self._token.is_cancelled:
                raise RuntimeError("Rigging fixture was cancelled after publication")
            self.progress.emit(RiggingProgress("fixture_rig", "Fixture rig ready", 2, 2))
            self.completed.emit(rig_id)
        except Exception as error:
            self.failed.emit(str(error))
