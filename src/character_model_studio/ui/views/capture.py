"""Windows capture workspace, region selector, and out-of-region recording indicator."""

from __future__ import annotations

import uuid
from shutil import rmtree

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen, QScreen
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QLabel, QRadioButton, QVBoxLayout, QWidget

from character_model_studio.app.bootstrap import ApplicationContext
from character_model_studio.capture.models import CaptureResult, PhysicalRegion
from character_model_studio.capture.region import LogicalRect, MonitorGeometry, to_physical_region
from character_model_studio.capture.session import CaptureSession
from character_model_studio.ui.widgets.controls import (
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
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setGeometry(screen.geometry())

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._origin = event.position().toPoint()
        self._selection = QRect(self._origin, self._origin)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._origin is not None:
            self._selection = QRect(self._origin, event.position().toPoint()).normalized()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self.mouseMoveEvent(event)

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
        if self._selection.isNull():
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
            self.selected.emit(to_physical_region(selection, monitor))
            self.close()
        except ValueError:
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
        guidance = QLabel(
            "Select one monitor region, then record at 30 FPS. Ctrl+Alt+S opens or stops capture."
        )
        guidance.setWordWrap(True)
        panel_layout.addWidget(guidance)
        standard = QRadioButton("Standard — Hunyuan3D 2.0 (Default)", panel)
        standard.setChecked(True)
        high_quality = QRadioButton("High Quality — Hunyuan3D 2.1 (Optional)", panel)
        runtime = context.runtime
        if runtime is not None:
            standard.setToolTip(runtime.standard.reason)
            high_quality.setEnabled(runtime.high_quality.status.value == "READY")
            high_quality.setToolTip(runtime.high_quality.reason)
        panel_layout.addWidget(standard)
        panel_layout.addWidget(high_quality)
        self._action = PrimaryButton("Select & Record", panel)
        self._action.clicked.connect(self.open_selector)
        panel_layout.addWidget(self._action, alignment=Qt.AlignmentFlag.AlignLeft)
        self._status = StatusIndicator("Ready for one-monitor capture", "ready", panel)
        panel_layout.addWidget(self._status, alignment=Qt.AlignmentFlag.AlignLeft)
        self._metadata = QLabel("No capture recorded.", panel)
        panel_layout.addWidget(self._metadata)
        self._preview = QVideoWidget(panel)
        self._preview.setMinimumHeight(180)
        self._preview.hide()
        self._player = QMediaPlayer(self)
        self._player.setVideoOutput(self._preview)
        panel_layout.addWidget(self._preview)
        self._discard = SecondaryButton("Discard capture", panel)
        self._discard.clicked.connect(self.discard_capture)
        self._discard.hide()
        panel_layout.addWidget(self._discard, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(panel)
        layout.addStretch(1)
        self._session.completed.connect(self._capture_completed)
        self._session.failed.connect(self._capture_failed)
        self._last_result: CaptureResult | None = None

    @property
    def is_recording(self) -> bool:
        """Return whether the local capture worker is currently active."""
        return self._session.is_recording

    def open_selector(self) -> None:
        """Open the selector on the current primary display."""
        from PySide6.QtGui import QGuiApplication

        screen = QGuiApplication.primaryScreen()
        self._overlay = RegionSelectionOverlay(screen)
        self._overlay.selected.connect(self.start_recording)
        self._overlay.cancelled.connect(
            lambda: self._status.label.setText("Capture selection cancelled")
        )
        self._overlay.show()
        self._overlay.activateWindow()

    def start_recording(self, region: PhysicalRegion) -> None:
        """Start the DXcam/PyAV worker for a confirmed physical region."""
        capture_id = uuid.uuid4().hex
        capture_root = self._context.paths.projects_directory / "UnassignedCaptures" / capture_id
        self._action.setText("Stop recording")
        self._action.clicked.disconnect()
        self._action.clicked.connect(self.stop_recording)
        self._status.label.setText("Recording locally")
        self._indicator.start(region)
        self._session.start(region, capture_root / "capture.mp4", capture_root / "thumbnail.jpg")

    def stop_recording(self) -> None:
        """Request recording finalization without blocking the UI."""
        self._session.stop()
        self._status.label.setText("Finalizing MP4 and thumbnail")

    def _capture_completed(self, result: CaptureResult) -> None:
        self._indicator.stop()
        self._action.setText("Select & Record")
        self._action.clicked.disconnect()
        self._action.clicked.connect(self.open_selector)
        self._status.label.setText("Capture ready for preview")
        self._metadata.setText(
            f"{result.duration_ms / 1000:.1f}s · "
            f"{result.width} × {result.height} · {result.fps} FPS"
        )
        self._last_result = result
        self._player.setSource(QUrl.fromLocalFile(str(result.video_path)))
        self._preview.show()
        self._discard.show()

    def _capture_failed(self, message: str) -> None:
        self._indicator.stop()
        self._status.label.setText("Capture unavailable")
        self._metadata.setText(f"Capture failed: {message}. Existing project data was preserved.")

    def discard_capture(self) -> None:
        """Remove only the most recent unassigned capture after the user explicitly requests it."""
        if self._last_result is None:
            return
        capture_root = self._last_result.video_path.parent
        staging_root = self._context.paths.projects_directory / "UnassignedCaptures"
        if capture_root.parent != staging_root:
            raise RuntimeError("Capture discard target is outside the managed staging folder")
        rmtree(capture_root)
        self._last_result = None
        self._discard.hide()
        self._player.stop()
        self._player.setSource(QUrl())
        self._preview.hide()
        self._metadata.setText("Capture discarded. Select & Record to capture again.")
