"""Small native Qt motion helpers for meaningful UI state transitions."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


@dataclass(frozen=True, slots=True)
class MotionTimings:
    """Shared timing values in milliseconds."""

    instant: int = 0
    fast: int = 120
    standard: int = 180
    slow: int = 280


TIMINGS = MotionTimings()


class MotionPreferences:
    """In-memory accessibility preference used by the desktop shell."""

    def __init__(self) -> None:
        self.reduce_motion = False

    def duration(self, default_duration: int) -> int:
        """Return immediate feedback when reduced motion is requested."""
        return TIMINGS.instant if self.reduce_motion else default_duration


def fade_in(
    widget: QWidget, preferences: MotionPreferences, duration: int = TIMINGS.standard
) -> None:
    """Fade a widget into view without animating expensive blur effects."""
    effect = widget.graphicsEffect()
    opacity_effect = (
        effect if isinstance(effect, QGraphicsOpacityEffect) else QGraphicsOpacityEffect(widget)
    )
    if effect is None:
        widget.setGraphicsEffect(opacity_effect)

    animation = QPropertyAnimation(opacity_effect, b"opacity", widget)
    animation.setDuration(preferences.duration(duration))
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
