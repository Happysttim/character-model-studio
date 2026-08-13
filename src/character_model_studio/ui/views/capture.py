"""Windows capture workspace, region selector, and out-of-region recording indicator."""

from __future__ import annotations

import uuid
from pathlib import Path
from shutil import rmtree

from PySide6.QtCore import QObject, QPoint, QRect, Qt, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen, QPixmap, QScreen
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QFileDialog, QLabel, QRadioButton, QVBoxLayout, QWidget

from character_model_studio.app.bootstrap import ApplicationContext
from character_model_studio.capture.importer import import_video
from character_model_studio.capture.models import CaptureResult, PhysicalRegion
from character_model_studio.capture.region import LogicalRect, MonitorGeometry, to_physical_region
from character_model_studio.capture.session import CaptureSession
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.domain.models import ProgressUpdate
from character_model_studio.reconstruction.task_runner import RealStandardWorkflowTaskRunner
from character_model_studio.ui.widgets.controls import (
    AspectRatioPixmapLabel,
    PrimaryButton,
    SecondaryButton,
    StatusIndicator,
)
from character_model_studio.ui.widgets.glass import GlassPanel


class RegionSelectionOverlay(QWidget):
    """Transparent one-monitor selector that produces physical DXcam coordinates."""

    selected = Signal(object)
    cancelled = Signal()

    def __init__(self, screen: QScreen) -> None:
        super().__init__(None)
        self._screen = screen
        self._origin: QPoint | None = None
        self._selection = QRect()
        self._confirmed = False
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setGeometry(screen.geometry())

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._confirmed:
            return
        self._origin = event.position().toPoint()
        self._selection = QRect(self._origin, self._origin)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._origin is not None:
            self._selection = QRect(self._origin, event.position().toPoint()).normalized()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self.mouseMoveEvent(event)
        self._confirm()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.close()
        elif event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
            self._confirm()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(35, 22, 17, 150))
        if not self._selection.isNull():
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self._selection, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor("#F3A34D"), 3))
            painter.drawRect(self._selection)
            painter.setPen(QColor("#FFF2D5"))
            painter.drawText(
                self._selection.adjusted(8, 22, 0, 0),
                f"{self._selection.width()} × {self._selection.height()}",
            )

    def _confirm(self) -> None:
        if self._confirmed or self._selection.isNull():
            return
        geometry = self._screen.geometry()
        selection = LogicalRect(
            geometry.x() + self._selection.x(),
            geometry.y() + self._selection.y(),
            self._selection.width(),
            self._selection.height(),
        )
        monitor = MonitorGeometry(
            self._screen.name(),
            geometry.x(),
            geometry.y(),
            geometry.width(),
            geometry.height(),
            self._screen.devicePixelRatio(),
        )
        try:
            self._confirmed = True
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.selected.emit(to_physical_region(selection, monitor))
            self.close()
        except ValueError:
            self._confirmed = False
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.update()


class RecordingIndicator(QWidget):
    """Small visual indicator positioned outside the DXcam source region."""

    def __init__(self) -> None:
        super().__init__(None)
        self._seconds = 0
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._label = QLabel("● REC 00:00", self)
        self._label.setStyleSheet("color: #FFF2D5; background: #8F3F2A; padding: 6px 10px;")
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self, region: PhysicalRegion) -> None:
        from PySide6.QtGui import QGuiApplication

        self._seconds = 0
        self._label.setText("● REC 00:00")
        self.adjustSize()
        scale = QGuiApplication.primaryScreen().devicePixelRatio()
        above = round(region.top / scale) - self.sizeHint().height() - 8
        below = round(region.bottom / scale) + 8
        self.move(round(region.left / scale), above if above >= 0 else below)
        self.show()
        self._timer.start(1000)

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        self._seconds += 1
        self._label.setText(f"● REC {self._seconds // 60:02}:{self._seconds % 60:02}")


class _ImportWorker(QObject):
    """Copy and inspect a selected local video outside the UI thread."""

    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, source: Path, destination: Path, thumbnail: Path) -> None:
        super().__init__()
        self._source = source
        self._destination = destination
        self._thumbnail = thumbnail

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(import_video(self._source, self._destination, self._thumbnail))
        except (OSError, ValueError) as error:
            self.failed.emit(str(error))


class CaptureWorkspace(QWidget):
    """Capture-ready surface that keeps selection/recording outside the main UI."""

    def __init__(self, context: ApplicationContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._session = CaptureSession()
        self._indicator = RecordingIndicator()
        self._overlay: RegionSelectionOverlay | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = GlassPanel("secondary", self)
        panel_layout = QVBoxLayout(panel)
        guidance = QLabel("Drag once to lock a region. Alt + / starts and stops recording.")
        guidance.setWordWrap(True)
        panel_layout.addWidget(guidance)
        self._standard = QRadioButton("Standard — Hunyuan3D 2.0 (Default)", panel)
        self._standard.setChecked(True)
        self._sf3d = QRadioButton("Textured Experimental — Stable Fast 3D", panel)
        high_quality = QRadioButton("High Quality — Hunyuan3D 2.1 (Optional)", panel)
        self._hunyuan2gp = QRadioButton("Textured Experimental - Hunyuan3D-2GP (Multi-view)", panel)
        runtime = context.runtime
        if runtime is not None:
            self._standard.setToolTip(
                f"Shape: {runtime.standard.reason}\n"
                f"Background isolation: {runtime.segmentation.reason}"
            )
            high_quality.setEnabled(runtime.high_quality.status.value == "READY")
            high_quality.setToolTip(runtime.high_quality.reason)
            self._sf3d.setEnabled(runtime.sf3d.status.value == "READY")
            self._sf3d.setToolTip(runtime.sf3d.reason)
        self._standard.toggled.connect(self._select_standard_provider)
        self._hunyuan2gp.setEnabled(
            runtime is not None and runtime.hunyuan2gp.status.value == "READY"
        )
        if runtime is not None:
            self._hunyuan2gp.setToolTip(runtime.hunyuan2gp.reason)
        self._hunyuan2gp.toggled.connect(self._select_hunyuan2gp_provider)
        self._sf3d.toggled.connect(self._select_sf3d_provider)
        panel_layout.addWidget(self._standard)
        panel_layout.addWidget(self._sf3d)
        panel_layout.addWidget(self._hunyuan2gp)
        panel_layout.addWidget(high_quality)
        self._action = PrimaryButton("Select capture region", panel)
        self._action.clicked.connect(self._handle_capture_action)
        panel_layout.addWidget(self._action, alignment=Qt.AlignmentFlag.AlignLeft)
        self._import_video = SecondaryButton("Import existing video", panel)
        self._import_video.clicked.connect(self._import_existing_video)
        panel_layout.addWidget(self._import_video, alignment=Qt.AlignmentFlag.AlignLeft)
        self._status = StatusIndicator("Ready for one-monitor capture", "ready", panel)
        panel_layout.addWidget(self._status, alignment=Qt.AlignmentFlag.AlignLeft)
        self._metadata = QLabel("No capture recorded.", panel)
        panel_layout.addWidget(self._metadata)
        self._poster = AspectRatioPixmapLabel(panel)
        self._poster.setObjectName("capturePoster")
        self._poster.setMinimumHeight(180)
        self._poster.hide()
        self._preview = QVideoWidget(panel)
        self._preview.setMinimumHeight(180)
        self._preview.hide()
        self._player = QMediaPlayer(self)
        self._player.setVideoOutput(self._preview)
        self._play_preview = SecondaryButton("Play capture preview", panel)
        self._play_preview.clicked.connect(self._show_video_preview)
        self._play_preview.hide()
        panel_layout.addWidget(self._poster)
        panel_layout.addWidget(self._preview)
        panel_layout.addWidget(self._play_preview, alignment=Qt.AlignmentFlag.AlignLeft)
        self._discard = SecondaryButton("Discard capture", panel)
        self._discard.clicked.connect(self.discard_capture)
        self._discard.hide()
        panel_layout.addWidget(self._discard, alignment=Qt.AlignmentFlag.AlignLeft)
        self._generate = PrimaryButton("Generate Standard Shape", panel)
        self._generate.clicked.connect(self._start_reconstruction)
        self._generate.hide()
        panel_layout.addWidget(self._generate, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(panel)
        layout.addStretch(1)
        self._session.completed.connect(self._capture_completed)
        self._session.failed.connect(self._capture_failed)
        self._session.elapsed_changed.connect(self._show_capture_elapsed)
        self._last_result: CaptureResult | None = None
        self._capture_id: str | None = None
        self._selected_region: PhysicalRegion | None = None
        self._reconstruction_runner = RealStandardWorkflowTaskRunner()
        self._reconstruction_runner.progress.connect(self._show_reconstruction_progress)
        self._reconstruction_runner.completed.connect(self._reconstruction_completed)
        self._reconstruction_runner.cancelled.connect(self._reconstruction_cancelled)
        self._reconstruction_runner.failed.connect(self._reconstruction_failed)
        self._reconstruction_token: CancellationToken | None = None
        self._selected_provider = "Hunyuan3D 2.0"
        self._import_thread: QThread | None = None
        self._import_worker: _ImportWorker | None = None

    @property
    def is_recording(self) -> bool:
        """Return whether the local capture worker is currently active."""
        return self._session.is_recording

    def open_selector(self) -> None:
        """Open the selector on the current primary display."""
        from PySide6.QtGui import QGuiApplication

        screen = QGuiApplication.primaryScreen()
        self._overlay = RegionSelectionOverlay(screen)
        self._overlay.selected.connect(self._set_capture_region)
        self._overlay.cancelled.connect(
            lambda: self._status.label.setText("Capture selection cancelled")
        )
        self._overlay.show()
        self._overlay.activateWindow()

    def handle_hotkey(self) -> None:
        """Start/stop only after a region is locked; otherwise open region selection."""
        if self.is_recording:
            self.stop_recording()
        elif self._selected_region is not None:
            self.start_recording(self._selected_region)
        else:
            self.open_selector()

    def _handle_capture_action(self) -> None:
        if self.is_recording:
            self.stop_recording()
        elif self._selected_region is None:
            self.open_selector()
        else:
            self.start_recording(self._selected_region)

    def _import_existing_video(self) -> None:
        """Bring a user-selected local video into the same capture/reconstruction workflow."""
        source, _ = QFileDialog.getOpenFileName(
            self, "Import character video", "", "Video files (*.mp4 *.mov *.mkv *.avi)"
        )
        if not source:
            return
        video_path = Path(source)
        root = self._context.paths.projects_directory / "UnassignedCaptures" / uuid.uuid4().hex
        destination = root / f"imported{video_path.suffix.lower() or '.mp4'}"
        thumbnail = root / "thumbnail.jpg"
        if self._import_thread is not None:
            self._status.label.setText("A video import is already running")
            return
        thread = QThread(self)
        worker = _ImportWorker(video_path, destination, thumbnail)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.completed.connect(self._capture_completed)
        worker.failed.connect(self._capture_failed)
        worker.completed.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._finish_import)
        self._import_thread = thread
        self._import_worker = worker
        self._status.label.setText("Importing local video")
        thread.start()

    def _finish_import(self) -> None:
        """Release the retained import task only after its queued Qt signals are delivered."""
        self._import_worker = None
        self._import_thread = None

    def _set_capture_region(self, region: PhysicalRegion) -> None:
        """Lock the selected bounds until the user explicitly starts capture."""
        self._selected_region = region
        self._status.label.setText("Capture region locked — press Alt + / to start")
        self._metadata.setText(f"Locked region: {region.width} × {region.height} pixels")
        self._action.setText("Start recording")

    def start_recording(self, region: PhysicalRegion) -> None:
        """Start the DXcam/PyAV worker for a confirmed physical region."""
        capture_id = uuid.uuid4().hex
        capture_root = self._context.paths.projects_directory / "UnassignedCaptures" / capture_id
        self._action.setText("Stop recording")
        self._status.label.setText("Recording locally")
        self._metadata.setText("● RECORDING — waiting for the first captured frame…")
        self._indicator.start(region)
        self._session.start(region, capture_root / "capture.mp4", capture_root / "thumbnail.jpg")

    def stop_recording(self) -> None:
        """Request recording finalization without blocking the UI."""
        self._session.stop()
        self._status.label.setText("Finalizing MP4 and thumbnail")
        self._metadata.setText("Stopping recording and writing the local MP4…")

    def _show_capture_elapsed(self, elapsed_ms: int) -> None:
        """Show proof that the capture worker is receiving frames and encoding locally."""
        seconds = max(0, elapsed_ms // 1000)
        self._status.label.setText("● Recording locally")
        self._metadata.setText(
            f"● RECORDING {seconds // 60:02}:{seconds % 60:02} — "
            "Alt + / or Stop recording ends capture"
        )

    def _capture_completed(self, result: CaptureResult) -> None:
        self._indicator.stop()
        self._action.setText("Start recording")
        self._status.label.setText("Capture ready for preview")
        self._metadata.setText(
            f"{result.duration_ms / 1000:.1f}s · "
            f"{result.width} × {result.height} · {result.fps} FPS"
        )
        self._last_result = result
        repository = self._context.repository
        if repository is None:
            self._capture_failed("Local repository is unavailable")
            return
        project = repository.create_project("Captured character project")
        self._capture_id = repository.register_capture_file(project.id, result.video_path).id
        self._player.setSource(QUrl.fromLocalFile(str(result.video_path)))
        poster = QPixmap(str(result.thumbnail_path))
        if poster.isNull():
            self._capture_failed("The saved capture thumbnail could not be opened")
            return
        self._poster.set_source_pixmap(poster)
        self._poster.show()
        self._preview.hide()
        self._play_preview.show()
        self._discard.show()
        workflow_ready = self._workflow_is_ready()
        self._generate.setEnabled(workflow_ready)
        self._generate.setToolTip(
            self._workflow_description() if workflow_ready else self._workflow_unavailable_reason()
        )
        self._generate.show()

    def _capture_failed(self, message: str) -> None:
        self._indicator.stop()
        self._status.label.setText("Capture unavailable")
        self._metadata.setText(f"Capture failed: {message}. Existing project data was preserved.")

    def _show_video_preview(self) -> None:
        """Start actual playback only after the visible thumbnail has been shown."""
        self._poster.hide()
        self._preview.show()
        self._player.play()

    def _start_reconstruction(self) -> None:
        if self._reconstruction_token is not None:
            self._reconstruction_token.cancel()
            self._status.label.setText("Cancellation requested; releasing the local CUDA provider")
            return
        if not self._workflow_is_ready():
            self._status.label.setText(self._workflow_unavailable_reason())
            return
        repository = self._context.repository
        if repository is None or self._capture_id is None:
            self._status.label.setText("Record a capture before reconstruction")
            return
        attempt = repository.create_attempt(
            self._capture_id,
            "experimental_textured"
            if self._selected_provider in {"Stable Fast 3D", "Hunyuan3D-2GP"}
            else "standard",
            provider=self._selected_provider,
            provider_version=(
                "upstream-local-experimental"
                if self._selected_provider in {"Stable Fast 3D", "Hunyuan3D-2GP"}
                else "2.0.2"
            ),
            parameters={
                "texture_stage": "generated"
                if self._selected_provider in {"Stable Fast 3D", "Hunyuan3D-2GP"}
                else "disabled",
                "source": "windows_capture",
            },
        )
        self._generate.setText("Cancel reconstruction")
        self._generate.setEnabled(True)
        self._reconstruction_token = self._reconstruction_runner.start(repository, attempt.id)
        self.reconstruction_started.emit(attempt.id)

    def _show_reconstruction_progress(self, update: ProgressUpdate) -> None:
        self._status.label.setText(update.label)
        self.reconstruction_progress.emit(update)

    def _reconstruction_completed(self, attempt_id: str) -> None:
        self._reconstruction_token = None
        self._restore_generate_label()
        self._status.label.setText("Model validated and ready for review")
        self.reconstruction_finished.emit("Model validated and ready for review", True)
        self.reconstruction_ready.emit(attempt_id)

    def _reconstruction_cancelled(self, _attempt_id: str) -> None:
        self._reconstruction_token = None
        self._restore_generate_label()
        self._status.label.setText("Reconstruction cancelled; project remains usable")
        self.reconstruction_finished.emit("Reconstruction cancelled; project remains usable", False)

    def _reconstruction_failed(self, _attempt_id: str, detail: str) -> None:
        self._reconstruction_token = None
        self._restore_generate_label()
        self._status.label.setText(f"Reconstruction failed: {detail}")
        self.reconstruction_finished.emit(f"Reconstruction failed: {detail}", False)

    def _standard_workflow_is_ready(self) -> bool:
        runtime = self._context.runtime
        return (
            runtime is not None
            and runtime.standard.status.value == "READY"
            and runtime.segmentation.status.value == "READY"
        )

    def _standard_workflow_unavailable_reason(self) -> str:
        runtime = self._context.runtime
        if runtime is None:
            return "Runtime readiness is unavailable"
        if runtime.standard.status.value != "READY":
            return f"Standard Shape is unavailable: {runtime.standard.reason}"
        return f"Background isolation is unavailable: {runtime.segmentation.reason}"

    def _workflow_is_ready(self) -> bool:
        runtime = self._context.runtime
        if runtime is None or runtime.segmentation.status.value != "READY":
            return False
        if self._selected_provider == "Stable Fast 3D":
            return runtime.sf3d.status.value == "READY"
        if self._selected_provider == "Hunyuan3D-2GP":
            return runtime.hunyuan2gp.status.value == "READY"
        return runtime.standard.status.value == "READY"

    def _workflow_unavailable_reason(self) -> str:
        runtime = self._context.runtime
        if runtime is None:
            return "Runtime readiness is unavailable"
        provider = (
            runtime.sf3d
            if self._selected_provider == "Stable Fast 3D"
            else runtime.hunyuan2gp
            if self._selected_provider == "Hunyuan3D-2GP"
            else runtime.standard
        )
        if provider.status.value != "READY":
            return f"{provider.provider} is unavailable: {provider.reason}"
        return f"Background isolation is unavailable: {runtime.segmentation.reason}"

    def _workflow_description(self) -> str:
        return (
            "Remove the background on CUDA, then generate a textured SF3D GLB locally"
            if self._selected_provider == "Stable Fast 3D"
            else "Remove the background locally on CUDA, then run Hunyuan3D 2.0 Shape"
        )

    def _select_standard_provider(self, checked: bool) -> None:
        if checked:
            self._selected_provider = "Hunyuan3D 2.0"
            self._restore_generate_label()

    def _select_sf3d_provider(self, checked: bool) -> None:
        if checked:
            self._selected_provider = "Stable Fast 3D"
            self._restore_generate_label()

    def _select_hunyuan2gp_provider(self, checked: bool) -> None:
        if checked:
            self._selected_provider = "Hunyuan3D-2GP"
            self._restore_generate_label()

    def _restore_generate_label(self) -> None:
        self._generate.setText(
            "Generate Textured Model"
            if self._selected_provider in {"Stable Fast 3D", "Hunyuan3D-2GP"}
            else "Generate Standard Shape"
        )
        if self._last_result is not None:
            self._generate.setEnabled(self._workflow_is_ready())
            self._generate.setToolTip(
                self._workflow_description()
                if self._workflow_is_ready()
                else self._workflow_unavailable_reason()
            )

    def discard_capture(self) -> None:
        """Remove only the most recent unassigned capture after the user explicitly requests it."""
        if self._last_result is None:
            return
        capture_root = self._last_result.video_path.parent
        staging_root = self._context.paths.projects_directory / "UnassignedCaptures"
        if capture_root.parent != staging_root:
            raise RuntimeError("Capture discard target is outside the managed staging folder")
        self._player.stop()
        self._player.setSource(QUrl())
        try:
            rmtree(capture_root)
        except PermissionError:
            self._status.label.setText("Capture file is still in use; it was kept safely")
            self._metadata.setText(
                "Discard skipped because Windows has not released the preview file yet."
            )
            return
        self._last_result = None
        self._discard.hide()
        self._play_preview.hide()
        self._poster.hide()
        self._preview.hide()
        self._metadata.setText("Capture discarded. Select & Record to capture again.")

    reconstruction_ready = Signal(str)
    reconstruction_started = Signal(str)
    reconstruction_progress = Signal(object)
    reconstruction_finished = Signal(str, bool)
