"""Empty Phase 02 workspaces with purposeful future-facing guidance."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from character_model_studio.ui.widgets.controls import PrimaryButton, StatusIndicator
from character_model_studio.ui.widgets.glass import GlassPanel


@dataclass(frozen=True, slots=True)
class WorkspaceDefinition:
    """Text-only description of a desktop workspace destination."""

    key: str
    title: str
    subtitle: str
    empty_state: str


WORKSPACES = (
    WorkspaceDefinition(
        "projects",
        "Projects",
        "Local creative work, kept on this device.",
        "No project is open yet.",
    ),
    WorkspaceDefinition(
        "capture",
        "Capture",
        "Record a clear character view when capture is configured.",
        "Capture tools are prepared for a later phase.",
    ),
    WorkspaceDefinition(
        "processing",
        "Processing",
        "Follow real processing stages when a job is running.",
        "There are no active attempts.",
    ),
    WorkspaceDefinition(
        "review",
        "Review",
        "Inspect a generated asset before accepting it.",
        "No reconstruction is ready for review.",
    ),
    WorkspaceDefinition(
        "rig",
        "Rig",
        "Review skeleton and skinning results when a rig is available.",
        "No rig is ready for review.",
    ),
    WorkspaceDefinition(
        "animate",
        "Animate",
        "Edit and preview a validated rig in a later phase.",
        "No animation document is open.",
    ),
    WorkspaceDefinition(
        "settings",
        "Settings",
        "Choose the application language and local preferences.",
        "Language preferences are stored locally.",
    ),
    WorkspaceDefinition(
        "diagnostics",
        "Diagnostics",
        "Local readiness and accessibility preferences.",
        "Runtime diagnostics will appear as features are enabled.",
    ),
)


class WorkspaceView(QWidget):
    """A content-first empty workspace that avoids decorative dashboard cards."""

    def __init__(self, definition: WorkspaceDefinition, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.definition = definition
        self.reduce_motion: QCheckBox | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        guidance = GlassPanel("secondary", self)
        guidance_layout = QVBoxLayout(guidance)
        guidance_layout.setContentsMargins(20, 18, 20, 18)
        message = QLabel(definition.empty_state, guidance)
        message.setWordWrap(True)
        guidance_layout.addWidget(message)

        if definition.key == "projects":
            create_project = PrimaryButton("Create project", guidance)
            create_project.setEnabled(False)
            create_project.setToolTip("Available when the local workflow is implemented.")
            guidance_layout.addWidget(create_project, alignment=Qt.AlignmentFlag.AlignLeft)
        elif definition.key == "diagnostics":
            self.reduce_motion = QCheckBox("Reduce motion", guidance)
            guidance_layout.addWidget(self.reduce_motion)
        else:
            readiness = StatusIndicator("Workspace shell ready", "info", guidance)
            guidance_layout.addWidget(readiness, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(guidance)
        layout.addStretch(1)


def definitions_by_key() -> dict[str, WorkspaceDefinition]:
    """Return navigation definitions by their stable destination keys."""
    return {definition.key: definition for definition in WORKSPACES}
