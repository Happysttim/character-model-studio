"""Phase 03 static-model review surface."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
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
    AspectRatioPixmapLabel,
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

    regenerate_requested = Signal()
    accepted = Signal(str)

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
        self._review_attempt_id: str | None = None

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

    def load_attempt(self, attempt_id: str) -> None:
        """Open a real reviewable attempt supplied by the local reconstruction workflow."""
        repository = self._context.repository
        if repository is None:
            raise RuntimeError("Local repository is unavailable")
        attempt = repository.get_attempt(attempt_id)
        if attempt.model_relative_path is None:
            raise ValueError("The selected attempt has no model artifact")
        if not self._initialized:
            self._initialized = True
            self._viewport = ModelViewport(self._viewer_host, off_screen=self._off_screen)
            self._viewer_layout.addWidget(self._viewport)
            self._viewer_placeholder.hide()
            self._control_panel.setEnabled(True)
        if self._viewport is None:
            raise RuntimeError("The embedded model viewport did not initialize")
        model_path = repository.projects_root / attempt.model_relative_path
        metadata = self._viewport.load_glb(model_path)
        self._review_attempt_id = attempt_id
        appearance = (
            "vertex colors"
            if metadata.vertex_colors is not None
            else "base-color texture"
            if metadata.base_color_texture is not None
            else "untextured Shape"
        )
        self._model_summary.setText(
            f"Standard Shape GLB · {metadata.vertex_count} vertices · "
            f"{metadata.face_count} faces · {appearance}"
        )
        self._validation_status.label.setText("Validation report persisted for this attempt")
        source_path = repository.attempt_artifact_path(attempt_id, "inputs/selected-frame.png")
        if source_path.is_file():
            self._source_preview.set_source_pixmap(QPixmap(str(source_path)))
        self._validation_runner.start_attempt(repository, attempt_id)

    def import_glb(self) -> None:
        """Copy a local GLB into project storage and validate it for review."""
        source, _ = QFileDialog.getOpenFileName(
            self, "Import GLB for review", "", "GLB files (*.glb)"
        )
        if not source:
            return
        repository = self._context.repository
        if repository is None:
            self._show_validation_failure("Local repository is unavailable")
            return
        try:
            attempt = repository.import_glb_for_review(Path(source))
            self.load_attempt(attempt.id)
        except (OSError, RuntimeError, ValueError) as error:
            self._show_validation_failure(
                f"GLB import failed; the selected source was preserved: {error}"
            )

    def _build_source_panel(self) -> QFrame:
        panel = GlassPanel("secondary", self)
        panel.setObjectName("sourceComparisonPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        label = QLabel("Source reference", panel)
        label.setProperty("sectionTitle", True)
        self._source_preview = AspectRatioPixmapLabel(panel)
        self._source_preview.setObjectName("sourceFixturePreview")
        self._source_preview.set_source_pixmap(source_reference_pixmap())
        self._source_preview.setMinimumHeight(180)
        import_button = SecondaryButton("Import existing GLB", panel)
        import_button.clicked.connect(self.import_glb)
        caption = QLabel("Fixture reference only — no user capture loaded.", panel)
        caption.setWordWrap(True)
        caption.setObjectName("pageSubtitle")
        layout.addWidget(label)
        layout.addWidget(self._source_preview)
        layout.addWidget(caption)
        layout.addWidget(import_button, alignment=Qt.AlignmentFlag.AlignLeft)
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
        for text, button_type in (("Accept", PrimaryButton), ("Reject", SecondaryButton)):
            button = button_type(text, panel)
            button.setEnabled(False)
            button.setToolTip(
                "Available when a reconstruction workflow supplies a reviewable result."
            )
            layout.addWidget(button)
            if text == "Accept":
                self._accept = button
                button.clicked.connect(lambda: self._decide(True))
            else:
                self._reject = button
                button.clicked.connect(lambda: self._decide(False))
        regenerate = SecondaryButton("Regenerate", panel)
        regenerate.setEnabled(True)
        regenerate.setToolTip("Return to Capture and run a new Standard Shape attempt.")
        regenerate.clicked.connect(self.regenerate_requested)
        layout.addWidget(regenerate)
        return panel

    def _decide(self, accepted: bool) -> None:
        repository = self._context.repository
        if repository is None or self._review_attempt_id is None:
            return
        repository.decide(self._review_attempt_id, accepted=accepted)
        decision = "accepted" if accepted else "rejected"
        self._validation_status.label.setText(f"Model {decision}; the project history was updated")
        self._accept.setEnabled(False)
        self._reject.setEnabled(False)
        if accepted:
            self.accepted.emit(self._review_attempt_id)

    def _viewport_apply_camera(self, preset: CameraPreset) -> None:
        self._with_viewport(lambda viewport: viewport.apply_camera(preset))

    def _with_viewport(self, callback: Callable[[ModelViewport], None]) -> None:
        if self._viewport is not None:
            callback(self._viewport)

    def _show_validation_report(self, report: ModelValidationReport) -> None:
        self._validation_status.label.setText(f"{report.overall_status} · technical checks")
        details = [f"{check.name}: {check.detail}" for check in report.checks]
        self._validation_text.setText("\n".join(details))
        if self._review_attempt_id is not None and report.overall_status.value != "FAIL":
            self._accept.setEnabled(True)
            self._reject.setEnabled(True)

    def _show_validation_failure(self, message: str) -> None:
        self._validation_status.label.setText("Validation failed")
        self._validation_text.setText(f"Validation did not complete: {message}")
