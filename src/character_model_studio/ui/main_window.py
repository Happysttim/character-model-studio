"""Phase 02 native desktop shell with visible-label navigation."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from character_model_studio.app.bootstrap import ApplicationContext
from character_model_studio.platform.windows.dwm import enable_system_backdrop
from character_model_studio.ui.motion import MotionPreferences, fade_in
from character_model_studio.ui.theme import application_stylesheet
from character_model_studio.ui.views.capture import CaptureWorkspace
from character_model_studio.ui.views.diagnostics import DiagnosticsWorkspace
from character_model_studio.ui.views.review import ReviewWorkspace
from character_model_studio.ui.views.workspace import WORKSPACES, WorkspaceView
from character_model_studio.ui.widgets.controls import StatusIndicator, Toast


class MainWindow(QMainWindow):
    """Warm, content-first shell whose workspaces are implemented in later phases."""

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self._context = context
        self._motion_preferences = MotionPreferences()
        self._navigation_buttons: dict[str, QPushButton] = {}
        self._workspace_indexes: dict[str, int] = {}
        self._backdrop_requested = False

        self.setObjectName("mainWindow")
        self.setWindowTitle("Character Model Studio")
        self.setMinimumSize(QSize(1180, 760))
        self.setStyleSheet(application_stylesheet())
        self._build_shell()
        self.navigate("projects")

    @property
    def current_destination(self) -> str:
        """Return the stable key of the current workspace."""
        return self._current_destination

    def navigate(self, destination: str) -> None:
        """Switch the active workspace and animate the context heading."""
        if destination not in self._workspace_indexes:
            raise KeyError(f"Unknown workspace destination: {destination}")

        self._current_destination = destination
        self._workspace_stack.setCurrentIndex(self._workspace_indexes[destination])
        current_workspace = self._workspace_stack.currentWidget()
        if isinstance(current_workspace, ReviewWorkspace):
            current_workspace.activate()
        definition = next(item for item in WORKSPACES if item.key == destination)
        self._page_title.setText(definition.title)
        self._page_subtitle.setText(definition.subtitle)
        for key, button in self._navigation_buttons.items():
            button.setChecked(key == destination)
        fade_in(self._page_header, self._motion_preferences)

    def handle_capture_hotkey(self) -> None:
        """Toggle the capture flow when Windows delivers Ctrl+Alt+S."""
        self.navigate("capture")
        if self._capture_workspace.is_recording:
            self._capture_workspace.stop_recording()
        else:
            self._capture_workspace.open_selector()

    def _build_shell(self) -> None:
        root = QWidget(self)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_navigation())
        root_layout.addWidget(self._build_workspace(), stretch=1)
        self.setCentralWidget(root)

    def _build_navigation(self) -> QFrame:
        navigation = QFrame(self)
        navigation.setObjectName("navigationPane")
        navigation.setFixedWidth(238)
        layout = QVBoxLayout(navigation)
        layout.setContentsMargins(18, 24, 18, 18)
        layout.setSpacing(8)

        brand = QLabel("Character Model Studio", navigation)
        brand.setObjectName("brandName")
        caption = QLabel("Local character craft", navigation)
        caption.setObjectName("brandCaption")
        layout.addWidget(brand)
        layout.addWidget(caption)
        layout.addSpacing(24)

        for definition in WORKSPACES:
            button = QPushButton(definition.title, navigation)
            button.setObjectName("navigationButton")
            button.setProperty("navRole", "item")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, key=definition.key: self.navigate(key))
            self._navigation_buttons[definition.key] = button
            layout.addWidget(button)

        layout.addStretch(1)
        layout.addWidget(
            StatusIndicator("Desktop shell", "ready", navigation),
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        return navigation

    def _build_workspace(self) -> QFrame:
        workspace = QFrame(self)
        workspace.setObjectName("workspaceSurface")
        outer_layout = QVBoxLayout(workspace)
        outer_layout.setContentsMargins(32, 28, 32, 26)
        outer_layout.setSpacing(24)

        self._page_header = QWidget(workspace)
        header_layout = QVBoxLayout(self._page_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        self._page_title = QLabel(self._page_header)
        self._page_title.setObjectName("pageTitle")
        self._page_subtitle = QLabel(self._page_header)
        self._page_subtitle.setObjectName("pageSubtitle")
        self._page_subtitle.setWordWrap(True)
        header_layout.addWidget(self._page_title)
        header_layout.addWidget(self._page_subtitle)
        outer_layout.addWidget(self._page_header)

        self._workspace_stack = QStackedWidget(workspace)
        for definition in WORKSPACES:
            view: QWidget
            if definition.key == "review":
                view = ReviewWorkspace(self._context, definition, self._workspace_stack)
            elif definition.key == "capture":
                view = CaptureWorkspace(self._context, self._workspace_stack)
                self._capture_workspace = view
            elif definition.key == "diagnostics":
                view = DiagnosticsWorkspace(self._context, self._workspace_stack)
                view.reduce_motion.toggled.connect(self._set_reduce_motion)
            else:
                view = WorkspaceView(definition, self._workspace_stack)
            index = self._workspace_stack.addWidget(view)
            self._workspace_indexes[definition.key] = index
            if isinstance(view, WorkspaceView) and view.reduce_motion is not None:
                view.reduce_motion.toggled.connect(self._set_reduce_motion)
        outer_layout.addWidget(self._workspace_stack, stretch=1)

        self._toast = Toast(self._motion_preferences, workspace)
        outer_layout.addWidget(self._toast, alignment=Qt.AlignmentFlag.AlignRight)
        return workspace

    def _set_reduce_motion(self, enabled: bool) -> None:
        self._motion_preferences.reduce_motion = enabled
        self._toast.show_message("Reduced motion enabled" if enabled else "Motion restored")

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        if not self._backdrop_requested:
            self._backdrop_requested = True
            enable_system_backdrop(int(self.winId()))
