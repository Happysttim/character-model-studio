"""Rig review surface with truthful provider readiness and skeleton overlay."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from character_model_studio.app.bootstrap import ApplicationContext
from character_model_studio.rigging.providers.unirig import UniRigProvider
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
        self._viewport: ModelViewport | None = None
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
        self.refresh()

    def refresh(self) -> None:
        """Refresh the optional provider status and reopen the newest completed rig."""
        readiness = UniRigProvider().probe()
        self._provider_status.label.setText(f"UniRig — {readiness.status}")
        self._provider_detail.setText(readiness.reason)
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
