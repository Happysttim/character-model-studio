"""Qt orchestration for a single local capture session."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from character_model_studio.capture.models import CaptureSettings, PhysicalRegion
from character_model_studio.capture.recorder import (
    CaptureWorker,
    DxcamFrameSource,
    FrameSource,
    PyAvH264Encoder,
    VideoEncoder,
)


class CaptureSession(QObject):
    """Starts and stops one capture without blocking the Qt UI event loop."""

    elapsed_changed = Signal(int)
    completed = Signal(object)
    failed = Signal(str)
    state_changed = Signal(str)

    def __init__(
        self,
        frame_source_factory: Callable[[], FrameSource] = DxcamFrameSource,
        encoder_factory: Callable[[Path, int, int, int], VideoEncoder] = PyAvH264Encoder,
    ) -> None:
        super().__init__()
        self._frame_source_factory = frame_source_factory
        self._encoder_factory = encoder_factory
        self._thread: QThread | None = None
        self._worker: CaptureWorker | None = None
        self._outcome: tuple[str, object] | None = None

    @property
    def is_recording(self) -> bool:
        """Return whether a capture worker is active."""
        return self._thread is not None

    def start(
        self,
        region: PhysicalRegion,
        video_path: Path,
        thumbnail_path: Path,
        settings: CaptureSettings | None = None,
    ) -> None:
        """Begin local recording of the selected region."""
        if self._thread is not None:
            raise RuntimeError("Capture is already recording")
        worker = CaptureWorker(
            region,
            video_path,
            thumbnail_path,
            settings or CaptureSettings(),
            self._frame_source_factory,
            self._encoder_factory,
        )
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.elapsed_changed)
        worker.completed.connect(lambda result: self._record_outcome("completed", result))
        worker.failed.connect(lambda message: self._record_outcome("failed", message))
        worker.completed.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._finish)
        self._worker = worker
        self._thread = thread
        self.state_changed.emit("recording")
        thread.start()

    def stop(self) -> None:
        """Request an idempotent capture stop; finalization remains in the worker."""
        if self._worker is not None:
            self._worker.request_stop()

    def _finish(self) -> None:
        thread = self._thread
        if thread is not None and thread.isRunning():
            thread.wait(1000)
        self._worker = None
        self._thread = None
        if self._outcome is not None:
            outcome, payload = self._outcome
            self._outcome = None
            if outcome == "completed":
                self.completed.emit(payload)
            else:
                self.failed.emit(str(payload))
        self.state_changed.emit("idle")

    def _record_outcome(self, outcome: str, payload: object) -> None:
        self._outcome = (outcome, payload)
