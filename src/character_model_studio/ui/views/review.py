"""Phase 03 static-model review surface."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from character_model_studio.app.bootstrap import ApplicationContext
from character_model_studio.ui.views.workspace import WorkspaceDefinition
from character_model_studio.ui.widgets.controls import (
    PrimaryButton,
    SecondaryButton,
    StatusIndicator,
)
from character_model_studio.ui.widgets.glass import GlassPanel
from character_model_studio.validation.model import ModelValidationReport
from character_model_studio.validation.task_runner import ModelValidationTaskRunner
from character_model_studio.viewer.cameras import CameraPreset
from character_model_studio.viewer.fixtures import ensure_sample_glb, source_reference_pixmap
from character_model_studio.viewer.widget import ModelViewport


class ReviewWorkspace(QWidget):
    """Source comparison, viewer, validation placeholder, and review actions."""

    def __init__(
        self,
        context: ApplicationContext,
        definition: WorkspaceDefinition,
        parent: QWidget | None = None,
        *,
        off_screen: bool = False,
    ) -> None:
        super().__init__(parent)
        self._context = context
        self.definition = definition
        self._initialized = False
        self._off_screen = off_screen
        self._viewport: ModelViewport | None = None
        self._validation_runner = ModelValidationTaskRunner()
        self._validation_runner.completed.connect(self._show_validation_report)
        self._validation_runner.failed.connect(self._show_validation_failure)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._build_source_panel(), stretch=2)
        layout.addWidget(self._build_viewer_panel(), stretch=6)
        layout.addWidget(self._build_validation_panel(), stretch=2)

    def activate(self) -> None:
        """Lazy-load the small fixture model only when the Review workspace opens."""
        if self._initialized:
            return
        self._initialized = True
        self._viewport = ModelViewport(self._viewer_host, off_screen=self._off_screen)
        self._viewer_layout.addWidget(self._viewport)
        fixture_path = ensure_sample_glb(self._context.paths.cache_directory / "viewer-fixtures")
        metadata = self._viewport.load_glb(fixture_path)
        self._model_summary.setText(
            f"Fixture GLB · {metadata.vertex_count} vertices · {metadata.face_count} faces"
        )
        self._viewer_placeholder.hide()
        self._control_panel.setEnabled(True)
        self._validation_runner.start(fixture_path)

    def _build_source_panel(self) -> QFrame:
        panel = GlassPanel("secondary", self)
        panel.setObjectName("sourceComparisonPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        label = QLabel("Source reference", panel)
        label.setProperty("sectionTitle", True)
        preview = QLabel(panel)
        preview.setObjectName("sourceFixturePreview")
        preview.setPixmap(source_reference_pixmap())
        preview.setScaledContents(True)
        preview.setMinimumHeight(180)
        caption = QLabel("Fixture reference only — no user capture loaded.", panel)
        caption.setWordWrap(True)
        caption.setObjectName("pageSubtitle")
        layout.addWidget(label)
        layout.addWidget(preview)
        layout.addWidget(caption)
        layout.addStretch(1)
        return panel

    def _build_viewer_panel(self) -> QFrame:
        panel = GlassPanel("secondary", self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        self._viewer_host = QFrame(panel)
        self._viewer_host.setObjectName("embeddedModelViewport")
        self._viewer_layout = QVBoxLayout(self._viewer_host)
        self._viewer_layout.setContentsMargins(0, 0, 0, 0)
        self._viewer_placeholder = QLabel(
            "Open Review to prepare the embedded model viewport.", self._viewer_host
        )
        self._viewer_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._viewer_layout.addWidget(self._viewer_placeholder)
        layout.addWidget(self._viewer_host, stretch=1)

        self._model_summary = QLabel("Fixture model not loaded", panel)
        self._model_summary.setObjectName("pageSubtitle")
        layout.addWidget(self._model_summary)
        self._control_panel = self._create_control_panel(panel)
        self._control_panel.setEnabled(False)
        layout.addWidget(self._control_panel)
        return panel

    def _create_control_panel(self, parent: QWidget) -> QWidget:
        controls = QWidget(parent)
        layout = QGridLayout(controls)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)

        camera_buttons = (
            ("Fit", CameraPreset.FIT),
            ("Front", CameraPreset.FRONT),
            ("Back", CameraPreset.BACK),
            ("Left", CameraPreset.LEFT),
            ("Right", CameraPreset.RIGHT),
            ("Top", CameraPreset.TOP),
            ("3/4", CameraPreset.THREE_QUARTER),
        )
        for index, (label, preset) in enumerate(camera_buttons):
            camera_button = SecondaryButton(label, controls)
            camera_button.clicked.connect(
                lambda checked=False, selected=preset: self._viewport_apply_camera(selected)
            )
            layout.addWidget(camera_button, 0, index)

        wireframe = QPushButton("Wireframe", controls)
        wireframe.setCheckable(True)
        wireframe.toggled.connect(
            lambda enabled: self._with_viewport(lambda viewport: viewport.set_wireframe(enabled))
        )
        grid = QPushButton("Grid", controls)
        grid.setCheckable(True)
        grid.toggled.connect(
            lambda enabled: self._with_viewport(lambda viewport: viewport.set_grid_visible(enabled))
        )
        axes = QPushButton("Axes", controls)
        axes.setCheckable(True)
        axes.setChecked(True)
        axes.toggled.connect(
            lambda enabled: self._with_viewport(lambda viewport: viewport.set_axes_visible(enabled))
        )
        bounds = QPushButton("Bounds", controls)
        bounds.setCheckable(True)
        bounds.toggled.connect(
            lambda enabled: self._with_viewport(
                lambda viewport: viewport.set_bounds_visible(enabled)
            )
        )
        turntable = QPushButton("Turntable", controls)
        turntable.setCheckable(True)
        turntable.toggled.connect(
            lambda enabled: self._with_viewport(
                lambda viewport: viewport.set_turntable_enabled(enabled)
            )
        )
        for column, button in enumerate((wireframe, grid, axes, bounds, turntable)):
            layout.addWidget(button, 1, column)
        return controls

    def _build_validation_panel(self) -> QFrame:
        panel = GlassPanel("secondary", self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(QLabel("Technical validation", panel))
        self._validation_status = StatusIndicator("Validating fixture model", "info", panel)
        layout.addWidget(self._validation_status)
        self._validation_text = QLabel(
            "Checks will appear after background validation completes.", panel
        )
        self._validation_text.setWordWrap(True)
        self._validation_text.setObjectName("pageSubtitle")
        layout.addWidget(self._validation_text)
        layout.addStretch(1)
        for text, button_type in (
            ("Accept", PrimaryButton),
            ("Reject", SecondaryButton),
            ("Regenerate", SecondaryButton),
        ):
            button = button_type(text, panel)
            button.setEnabled(False)
            button.setToolTip(
                "Available when a reconstruction workflow supplies a reviewable result."
            )
            layout.addWidget(button)
        return panel

    def _viewport_apply_camera(self, preset: CameraPreset) -> None:
        self._with_viewport(lambda viewport: viewport.apply_camera(preset))

    def _with_viewport(self, callback: Callable[[ModelViewport], None]) -> None:
        if self._viewport is not None:
            callback(self._viewport)

    def _show_validation_report(self, report: ModelValidationReport) -> None:
        self._validation_status.label.setText(f"{report.overall_status} · technical checks")
        details = [f"{check.name}: {check.detail}" for check in report.checks]
        self._validation_text.setText("\n".join(details))

    def _show_validation_failure(self, message: str) -> None:
        self._validation_status.label.setText("Validation failed")
        self._validation_text.setText(f"Validation did not complete: {message}")
