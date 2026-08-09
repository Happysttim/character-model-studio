"""Small local fixtures used only to exercise the Phase 03 review surface."""

from __future__ import annotations

from pathlib import Path

import trimesh
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap


def ensure_sample_glb(directory: Path) -> Path:
    """Create a tiny synthetic GLB fixture when no review asset is available."""
    directory.mkdir(parents=True, exist_ok=True)
    fixture_path = directory / "viewer-sample.glb"
    if fixture_path.exists():
        return fixture_path

    mesh = trimesh.creation.icosphere(subdivisions=2, radius=0.85)
    mesh.visual.vertex_colors = [242, 166, 90, 255]
    mesh.export(fixture_path)
    return fixture_path


def source_reference_pixmap() -> QPixmap:
    """Create an abstract source-reference fixture without storing user imagery."""
    image = QImage(440, 260, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor("#2A211E"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#FFBE88"), 3))
    painter.setBrush(QColor("#C96A4B"))
    painter.drawEllipse(QPointF(220, 86), 42, 42)
    painter.setBrush(QColor("#E97B67"))
    painter.drawRoundedRect(164, 128, 112, 94, 28, 28)
    painter.setPen(QPen(QColor("#FFE4CB"), 2, Qt.PenStyle.DashLine))
    painter.drawRect(120, 40, 200, 190)
    painter.end()
    return QPixmap.fromImage(image)
