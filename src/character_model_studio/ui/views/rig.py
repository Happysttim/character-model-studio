"""Rig review surface with truthful provider readiness and skeleton overlay."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from character_model_studio.app.bootstrap import ApplicationContext
from character_model_studio.rigging.providers.unirig import UniRigProvider
from character_model_studio.rigging.real_task_runner import RealRiggingTaskRunner
from character_model_studio.ui.views.workspace import WorkspaceDefinition
from character_model_studio.ui.widgets.controls import SecondaryButton, StatusIndicator
from character_model_studio.ui.widgets.glass import GlassPanel
from character_model_studio.viewer.widget import ModelViewport


class RigWorkspace(QWidget):
    """Review completed rig derivatives without claiming fixture output is AI generated."""

    def __init__(
        self,
        context: ApplicationContext,
        definition: WorkspaceDefinition,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._context = context
        self.definition = definition
        self._active = False
        self._viewport: ModelViewport | None = None
        self._runner = RealRiggingTaskRunner()
        self._runner.progress.connect(self._show_progress)
        self._runner.completed.connect(self._show_completed)
        self._runner.failed.connect(self._show_failed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        provider_panel = GlassPanel("secondary", self)
        provider_layout = QVBoxLayout(provider_panel)
        self._provider_status = StatusIndicator(
            "Checking local rigging readiness", "info", provider_panel
        )
        self._provider_detail = QLabel(provider_panel)
        self._provider_detail.setWordWrap(True)
        provider_layout.addWidget(self._provider_status)
        provider_layout.addWidget(self._provider_detail)
        refresh = SecondaryButton("Refresh readiness", provider_panel)
        refresh.clicked.connect(self.refresh)
        provider_layout.addWidget(refresh, alignment=Qt.AlignmentFlag.AlignLeft)
        self._create_rig = SecondaryButton("Create Rig", provider_panel)
        self._create_rig.clicked.connect(self._start_rigging)
        provider_layout.addWidget(self._create_rig, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(provider_panel)

        viewer_panel = GlassPanel("secondary", self)
        viewer_layout = QVBoxLayout(viewer_panel)
        self._summary = QLabel(
            "No completed rig is available in the local project history.", viewer_panel
        )
        self._summary.setWordWrap(True)
        self._viewer_host = QWidget(viewer_panel)
        self._viewer_layout = QVBoxLayout(self._viewer_host)
        self._viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.addWidget(self._summary)
        viewer_layout.addWidget(self._viewer_host, stretch=1)
        layout.addWidget(viewer_panel, stretch=1)
        self._refresh_readiness()

    def activate(self) -> None:
        """Create the native VTK surface only after the visible Rig tab is entered."""
        self._active = True
        self.refresh()

    def reset_loaded_rig(self) -> None:
        """Clear stale viewer data after a different GLB enters review."""
        if self._viewport is not None:
            self._viewport.close()
            self._viewport.deleteLater()
            self._viewport = None
        self._summary.setText("A new model was loaded. Create or reopen its rig.")

    def refresh(self) -> None:
        """Refresh the optional provider status and reopen the newest completed rig."""
        self._refresh_readiness()
        if not self._active:
            return
        repository = self._context.repository
        if repository is None:
            return
        rigs = [rig for rig in repository.list_rig_attempts() if rig.rigged_relative_path]
        if not rigs:
            return
        rig = rigs[0]
        if self._viewport is None:
            self._viewport = ModelViewport(self._viewer_host)
            self._viewer_layout.addWidget(self._viewport)
        path = repository.projects_root / str(rig.rigged_relative_path)
        metadata = self._viewport.load_glb(path)
        overlay = self._viewport.set_skeleton_overlay(path, True)
        fixture_note = (
            " Fixture output; not CUDA inference." if rig.provider == "fixture-rigging" else ""
        )
        self._summary.setText(
            f"{rig.provider}: {metadata.vertex_count} vertices, {metadata.face_count} faces. "
            f"Skeleton overlay: {'available' if overlay else 'unavailable'}.{fixture_note}"
        )

    def _refresh_readiness(self) -> None:
        """Update readiness controls without initializing the OpenGL-backed viewer."""
        readiness = UniRigProvider().probe()
        self._provider_status.label.setText(f"UniRig — {readiness.status}")
        self._provider_detail.setText(readiness.reason)
        repository = self._context.repository
        accepted = repository.latest_accepted_attempt() if repository is not None else None
        self._create_rig.setEnabled(
            not self._runner.is_running
            and readiness.status.value == "READY"
            and accepted is not None
        )
        self._create_rig.setToolTip(
            "Create a CUDA rig from the newest accepted GLB"
            if self._create_rig.isEnabled()
            else "Accept a GLB in Review and configure the local UniRig runtime first."
        )

    def _start_rigging(self) -> None:
        repository = self._context.repository
        accepted = None if repository is None else repository.latest_accepted_attempt()
        if repository is None or accepted is None:
            self._provider_detail.setText("Accept a GLB in Review before creating a rig.")
            return
        try:
            self._runner.start(repository, accepted.id)
            self._create_rig.setEnabled(False)
            self._provider_detail.setText("UniRig is running in its isolated local CUDA runtime.")
        except RuntimeError as error:
            self._show_failed(str(error))

    def _show_progress(self, update: object) -> None:
        label = getattr(update, "label", "Rigging in progress")
        self._create_rig.setEnabled(False)
        self._provider_detail.setText(str(label))

    def _show_completed(self, _rig_id: str) -> None:
        self._provider_detail.setText("Rig validated; texture-preserved GLB is ready for review.")
        self.refresh()

    def _show_failed(self, message: str) -> None:
        self._provider_detail.setText(f"Rigging failed; accepted model was preserved: {message}")
        self.refresh()
