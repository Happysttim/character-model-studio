"""PyVista/VTK widget embedded directly in the Qt desktop application."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyvista as pv
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget
from pyvistaqt import QtInteractor

from character_model_studio.viewer.cameras import CameraPreset, apply_camera_preset
from character_model_studio.viewer.scene import LoadedModel, load_glb_model


class ModelViewport(QWidget):
    """Interactive embedded viewport for static model inspection."""

    def __init__(self, parent: QWidget | None = None, *, off_screen: bool = False) -> None:
        super().__init__(parent)
        self._plotter: Any = QtInteractor(self, off_screen=off_screen)
        self._plotter.set_background("#201B19")  # type: ignore[arg-type]
        self._model_actor: Any | None = None
        self._bounds_actor: Any | None = None
        self._grid_actor: Any | None = None
        self._loaded_model: LoadedModel | None = None
        self._turntable_timer = QTimer(self)
        self._turntable_timer.setInterval(33)
        self._turntable_timer.timeout.connect(self._advance_turntable)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plotter)

    @property
    def has_model(self) -> bool:
        """Whether a model is available for camera and display actions."""
        return self._loaded_model is not None

    @property
    def model_metadata(self) -> LoadedModel | None:
        """Return immutable metadata for the currently loaded GLB."""
        return self._loaded_model

    def load_glb(self, path: Path) -> LoadedModel:
        """Load a GLB after independent trimesh parsing succeeds."""
        loaded_model = load_glb_model(path)
        self._plotter.clear()
        mesh_options: dict[str, Any] = {
            "smooth_shading": True,
            "name": "review-model",
        }
        if loaded_model.vertex_colors is None:
            if loaded_model.base_color_texture is None:
                # A Shape-only GLB has no color payload. Keep it neutral so the
                # UI does not imply that a texture was generated.
                mesh_options["color"] = "#B8AAA1"
            else:
                mesh_options["texture"] = loaded_model.base_color_texture
        else:
            mesh_options["scalars"] = "vertex_rgba"
            mesh_options["rgb"] = True
        self._model_actor = self._plotter.add_mesh(loaded_model.mesh, **mesh_options)
        self._loaded_model = loaded_model
        self._grid_actor = None
        self._bounds_actor = None
        self.set_axes_visible(True)
        self.set_grid_visible(False)
        self.set_bounds_visible(False)
        self.apply_camera(CameraPreset.THREE_QUARTER)
        return loaded_model

    def apply_camera(self, preset: CameraPreset) -> None:
        """Apply a named review camera when a model has been loaded."""
        if self.has_model:
            apply_camera_preset(self._plotter, preset)

    def set_wireframe(self, enabled: bool) -> None:
        """Switch the reviewed mesh between solid and wireframe representations."""
        if self._model_actor is not None:
            if enabled:
                self._model_actor.prop.SetRepresentationToWireframe()
            else:
                self._model_actor.prop.SetRepresentationToSurface()
            self._plotter.render()

    def set_grid_visible(self, visible: bool) -> None:
        """Show a restrained floor grid beneath the reviewed mesh."""
        if not self.has_model:
            return
        model = self._loaded_model
        assert model is not None
        if self._grid_actor is None:
            bounds = model.mesh.bounds
            span = (
                max(
                    float(bounds[1] - bounds[0]),
                    float(bounds[3] - bounds[2]),
                    float(bounds[5] - bounds[4]),
                )
                * 1.5
            )
            plane = pv.Plane(i_size=span, j_size=span, i_resolution=12, j_resolution=12)
            self._grid_actor = self._plotter.add_mesh(
                plane,
                color="#6B5549",
                opacity=0.35,
                show_edges=True,
                name="review-grid",
            )
        self._grid_actor.SetVisibility(visible)
        self._plotter.render()

    def set_axes_visible(self, visible: bool) -> None:
        """Show or hide the small orientation axes widget."""
        self._plotter.add_axes(color="#FFE4CB", xlabel="X", ylabel="Y", zlabel="Z")
        self._plotter.renderer.axes_widget.SetEnabled(visible)
        self._plotter.render()

    def set_bounds_visible(self, visible: bool) -> None:
        """Show or hide a separate model bounding-box aid."""
        if not self.has_model:
            return
        model = self._loaded_model
        assert model is not None
        if self._bounds_actor is None:
            box = pv.Box(model.mesh.bounds)
            self._bounds_actor = self._plotter.add_mesh(
                box,
                color="#F2A65A",
                style="wireframe",
                line_width=2,
                name="review-bounds",
            )
        self._bounds_actor.SetVisibility(visible)
        self._plotter.render()

    def set_turntable_enabled(self, enabled: bool) -> None:
        """Start or stop subtle review-camera turntable motion."""
        if enabled and self.has_model:
            self._turntable_timer.start()
        else:
            self._turntable_timer.stop()

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        """Release the VTK widget before its Qt parent is destroyed."""
        self._turntable_timer.stop()
        self._plotter.clear()
        self._plotter.close()
        self._model_actor = None
        self._bounds_actor = None
        self._grid_actor = None
        self._loaded_model = None
        super().closeEvent(event)

    def _advance_turntable(self) -> None:
        if self.has_model:
            self._plotter.camera.Azimuth(1.0)
            self._plotter.render()
