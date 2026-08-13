"""Project creation and reopen controls for the local desktop workspace."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QInputDialog, QLabel, QListWidget, QVBoxLayout, QWidget

from character_model_studio.app.bootstrap import ApplicationContext
from character_model_studio.domain.models import Project
from character_model_studio.ui.widgets.controls import PrimaryButton, SecondaryButton
from character_model_studio.ui.widgets.glass import GlassPanel


class ProjectsWorkspace(QWidget):
    """Create, browse, and reopen local SQLite-backed project records."""

    project_opened = Signal(str)

    def __init__(self, context: ApplicationContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._projects: list[Project] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = GlassPanel("secondary", self)
        panel_layout = QVBoxLayout(panel)
        self._summary = QLabel("Create a local project or reopen one from this device.", panel)
        self._list = QListWidget(panel)
        self._list.setObjectName("projectList")
        controls = QHBoxLayout()
        create = PrimaryButton("Create project", panel)
        create.setObjectName("createProjectButton")
        create.clicked.connect(self.create_project)
        reopen = SecondaryButton("Open selected project", panel)
        reopen.setObjectName("openProjectButton")
        reopen.clicked.connect(self.open_selected_project)
        refresh = SecondaryButton("Refresh projects", panel)
        refresh.clicked.connect(self.refresh)
        controls.addWidget(create)
        controls.addWidget(reopen)
        controls.addWidget(refresh)
        controls.addStretch(1)
        panel_layout.addWidget(self._summary)
        panel_layout.addWidget(self._list, stretch=1)
        panel_layout.addLayout(controls)
        layout.addWidget(panel, stretch=1)
        self.refresh()

    def refresh(self) -> None:
        """Reload persisted project records without touching project artifacts."""
        repository = self._context.repository
        self._projects = [] if repository is None else repository.list_projects()
        self._list.clear()
        for project in self._projects:
            self._list.addItem(f"{project.name} — {project.created_at.date().isoformat()}")
        self._summary.setText(
            "No local projects yet."
            if not self._projects
            else f"{len(self._projects)} local project(s)."
        )

    def create_project(self) -> None:
        """Ask for a non-empty local project name and open the newly created record."""
        name, accepted = QInputDialog.getText(self, "Create project", "Project name:")
        if not accepted or not name.strip() or self._context.repository is None:
            return
        project = self._context.repository.create_project(name.strip())
        self.refresh()
        self.project_opened.emit(project.id)

    def open_selected_project(self) -> None:
        """Emit the selected stable ID; project data remains on the local filesystem."""
        index = self._list.currentRow()
        if index < 0 or index >= len(self._projects):
            self._summary.setText("Select a project to reopen.")
            return
        self.project_opened.emit(self._projects[index].id)
