"""Reusable primary and secondary glass surface widgets."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QWidget


class GlassPanel(QFrame):
    """A semantic glass panel with one of the design-system depth levels."""

    def __init__(self, level: str = "secondary", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("glassLevel", level)
