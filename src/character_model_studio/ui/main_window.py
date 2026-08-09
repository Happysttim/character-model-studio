"""Phase 02 native desktop shell with visible-label navigation."""

from __future__ import annotations

import sys
from ctypes import wintypes
from typing import cast

from PySide6.QtCore import QByteArray, QPoint, QSize, Qt
from PySide6.QtGui import QCursor, QMouseEvent, QShowEvent
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
from character_model_studio.ui.views.processing import ProcessingWorkspace
from character_model_studio.ui.views.review import ReviewWorkspace
from character_model_studio.ui.views.workspace import WORKSPACES, WorkspaceView
from character_model_studio.ui.widgets.controls import StatusIndicator, Toast


class WindowTitleBar(QFrame):
    """Small app-owned title bar for the frameless desktop window."""

    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._drag_origin: QPoint | None = None
        self.setObjectName("windowTitleBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.addWidget(QLabel("Character Model Studio", self))
        layout.addStretch(1)
        for text, action, tooltip in (
            ("−", self._minimize_window, "Minimize"),
            ("□", self._toggle_maximize, "Maximize or restore"),
            ("×", window.close, "Close"),
        ):
            button = QPushButton(text, self)
            button.setObjectName("windowControl")
            button.setToolTip(tooltip)
            button.clicked.connect(action)
            layout.addWidget(button)

    def _minimize_window(self) -> None:
        """Minimize explicitly; this remains reliable for a frameless Qt window."""
        self._window.setWindowState(self._window.windowState() | Qt.WindowState.WindowMinimized)

    def _toggle_maximize(self) -> None:
        """Toggle the app-owned maximize control without relying on native chrome."""
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = (
                event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._drag_origin)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_origin = None


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
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
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
        """Toggle the capture flow when Windows delivers Alt + /."""
        self.navigate("capture")
        self._capture_workspace.handle_hotkey()

    def _build_shell(self) -> None:
        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(WindowTitleBar(self))
        content = QWidget(root)
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._build_navigation())
        content_layout.addWidget(self._build_workspace(), stretch=1)
        root_layout.addWidget(content, stretch=1)
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
        self._processing_workspace = ProcessingWorkspace(self._workspace_stack)
        for definition in WORKSPACES:
            view: QWidget
            if definition.key == "review":
                view = ReviewWorkspace(self._context, definition, self._workspace_stack)
                self._review_workspace = view
                view.regenerate_requested.connect(lambda: self.navigate("capture"))
            elif definition.key == "capture":
                view = CaptureWorkspace(self._context, self._workspace_stack)
                self._capture_workspace = view
                view.reconstruction_ready.connect(self._open_review_attempt)
            elif definition.key == "processing":
                view = self._processing_workspace
            elif definition.key == "diagnostics":
                view = DiagnosticsWorkspace(self._context, self._workspace_stack)
                view.reduce_motion.toggled.connect(self._set_reduce_motion)
            else:
                view = WorkspaceView(definition, self._workspace_stack)
            index = self._workspace_stack.addWidget(view)
            self._workspace_indexes[definition.key] = index
            if isinstance(view, WorkspaceView) and view.reduce_motion is not None:
                view.reduce_motion.toggled.connect(self._set_reduce_motion)
        self._capture_workspace.reconstruction_started.connect(self._start_processing)
        self._capture_workspace.reconstruction_progress.connect(
            self._processing_workspace.update_progress
        )
        self._capture_workspace.reconstruction_finished.connect(self._processing_workspace.finish)
        outer_layout.addWidget(self._workspace_stack, stretch=1)

        self._toast = Toast(self._motion_preferences, workspace)
        outer_layout.addWidget(self._toast, alignment=Qt.AlignmentFlag.AlignRight)
        return workspace

    def _open_review_attempt(self, attempt_id: str) -> None:
        self._review_workspace.load_attempt(attempt_id)
        self.navigate("review")

    def _start_processing(self, attempt_id: str) -> None:
        self._processing_workspace.begin(attempt_id)
        self.navigate("processing")

    def _set_reduce_motion(self, enabled: bool) -> None:
        self._motion_preferences.reduce_motion = enabled
        self._toast.show_message("Reduced motion enabled" if enabled else "Motion restored")

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        if not self._backdrop_requested:
            self._backdrop_requested = True
            enable_system_backdrop(int(self.winId()))

    def nativeEvent(  # noqa: N802
        self, event_type: QByteArray | bytes | bytearray | memoryview[int], message: int
    ) -> tuple[bool, int]:
        """Use Windows hit testing so every frameless window edge can resize natively."""
        if (
            sys.platform == "win32"
            and event_type == b"windows_generic_MSG"
            and not self.isMaximized()
        ):
            native_message = wintypes.MSG.from_address(message)
            if native_message.message == 0x0084:  # WM_NCHITTEST
                hit = _window_resize_hit_test(self)
                if hit is not None:
                    return True, hit
        return cast(tuple[bool, int], super().nativeEvent(event_type, message))


def _window_resize_hit_test(window: QMainWindow) -> int | None:
    """Return a Windows sizing hit-test code when the cursor is on a window edge."""
    border = 8
    point = window.mapFromGlobal(QCursor.pos())
    left = point.x() < border
    right = point.x() >= window.width() - border
    top = point.y() < border
    bottom = point.y() >= window.height() - border
    if top and left:
        return 13  # HTTOPLEFT
    if top and right:
        return 14  # HTTOPRIGHT
    if bottom and left:
        return 16  # HTBOTTOMLEFT
    if bottom and right:
        return 17  # HTBOTTOMRIGHT
    if left:
        return 10  # HTLEFT
    if right:
        return 11  # HTRIGHT
    if top:
        return 12  # HTTOP
    if bottom:
        return 15  # HTBOTTOM
    return None
