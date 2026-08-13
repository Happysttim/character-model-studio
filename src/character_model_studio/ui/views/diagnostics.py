"""Compact runtime readiness display without decorative dashboard metrics."""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from character_model_studio.app.bootstrap import ApplicationContext
from character_model_studio.ui.widgets.controls import SecondaryButton
from character_model_studio.ui.widgets.glass import GlassPanel


class DiagnosticsWorkspace(QWidget):
    """Show locally probed CUDA and provider readiness in actionable text."""

    def __init__(self, context: ApplicationContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = GlassPanel("secondary", self)
        panel_layout = QVBoxLayout(panel)
        runtime = context.runtime
        if runtime is None:
            text = "Runtime diagnostics are unavailable. Restart the application to probe CUDA."
        else:
            gpu = runtime.gpu
            total = _format_gib(gpu.total_vram_bytes)
            free = _format_gib(gpu.free_vram_bytes)
            text = "\n".join(
                (
                    f"CUDA: {'ready' if gpu.cuda_available else 'unavailable'}",
                    f"GPU: {gpu.device_name or 'not detected'}",
                    f"VRAM: total {total}; free {free}; tier {runtime.tier}",
                    f"Standard — {runtime.standard.status}: {runtime.standard.reason}",
                    f"High Quality — {runtime.high_quality.status}: {runtime.high_quality.reason}",
                    f"Rigging — {runtime.rigging.status}: {runtime.rigging.reason}",
                )
            )
        label = QLabel(text, panel)
        label.setWordWrap(True)
        panel_layout.addWidget(label)
        self.reduce_motion = QCheckBox("Reduce motion", panel)
        self.reduce_motion.setObjectName("reduceMotionToggle")
        panel_layout.addWidget(self.reduce_motion)
        copy_diagnostics = SecondaryButton("Copy diagnostics", panel)
        copy_diagnostics.clicked.connect(lambda: _copy_diagnostics(text))
        panel_layout.addWidget(copy_diagnostics)
        open_logs = SecondaryButton("Open log folder", panel)
        open_logs.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(context.paths.logs_directory)))
        )
        panel_layout.addWidget(open_logs)
        layout.addWidget(panel)
        layout.addStretch(1)


def _format_gib(value: int | None) -> str:
    return "unavailable" if value is None else f"{value / 1024**3:.1f} GiB"


def _copy_diagnostics(text: str) -> None:
    QGuiApplication.clipboard().setText(text)
