"""Buttons, inputs, status indicators, dialogs, and toasts."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from character_model_studio.ui.motion import MotionPreferences, fade_in


class PrimaryButton(QPushButton):
    """Warm, high-contrast primary action button."""

    def __init__(self, text: str, parent: QFrame | None = None) -> None:
        super().__init__(text, parent)
        self.setProperty("buttonKind", "primary")


class SecondaryButton(QPushButton):
    """Glass-surface secondary action button."""

    def __init__(self, text: str, parent: QFrame | None = None) -> None:
        super().__init__(text, parent)
        self.setProperty("buttonKind", "secondary")


class StyledLineEdit(QLineEdit):
    """Compact input with the centralized focus treatment."""

    def __init__(self, placeholder: str = "", parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)


class StatusIndicator(QFrame):
    """Small semantic status indicator; it is not a navigation or action pill."""

    def __init__(self, text: str, tone: str = "info", parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self.setProperty("glassLevel", "floating")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 4, 9, 4)
        self.label = QLabel(text, self)
        self.label.setProperty("statusTone", tone)
        layout.addWidget(self.label)


class AppDialog(QDialog):
    """A restrained dialog surface for controlled user-facing messages."""

    def __init__(self, title: str, message: str, parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(message, self))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, parent=self)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class Toast(QFrame):
    """Transient floating feedback surface."""

    def __init__(self, preferences: MotionPreferences, parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self._preferences = preferences
        self.setObjectName("toast")
        self.setProperty("glassLevel", "floating")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        self._label = QLabel(self)
        layout.addWidget(self._label)
        self.hide()

    def show_message(self, message: str, timeout_ms: int = 2600) -> None:
        """Display a truthful, brief feedback message."""
        self._label.setText(message)
        self.adjustSize()
        self.show()
        fade_in(self, self._preferences)
        QTimer.singleShot(timeout_ms, self.hide)
