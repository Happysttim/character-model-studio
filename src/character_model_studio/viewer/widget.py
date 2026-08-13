"""PyVista/VTK widget embedded directly in the Qt desktop application."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyvista as pv
from pygltflib import GLTF2
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget
from pyvistaqt import QtInteractor

from character_model_studio.animation.poses import Quaternion
from character_model_studio.animation.skinning import SkinnedAsset, load_skinned_asset
from character_model_studio.viewer.cameras import CameraPreset, apply_camera_preset
from character_model_studio.viewer.scene import LoadedModel, load_glb_model


class ModelViewport(QWidget):
    """Interactive embedded viewport for static model inspection."""

    skeleton_joint_picked = Signal(int)

    def __init__(self, parent: QWidget | None = None, *, off_screen: bool = False) -> None:
        super().__init__(parent)
        self._plotter: Any = QtInteractor(self, off_screen=off_screen)
        self._plotter.set_background("#201B19")  # type: ignore[arg-type]
        self._model_actor: Any | None = None
        self._bounds_actor: Any | None = None
        self._grid_actor: Any | None = None
        self._skeleton_actor: Any | None = None
        self._joint_actor: Any | None = None
        self._selected_joint_actor: Any | None = None
        self._skeleton_points: list[list[float]] = []
        self._skeleton_edges: list[tuple[int, int]] = []
        self._skinned_asset: SkinnedAsset | None = None
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
        self._skeleton_actor = None
        self._joint_actor = None
        self._selected_joint_actor = None
        self._skinned_asset = None
        self.set_axes_visible(True)
        self.set_grid_visible(False)
        self.set_bounds_visible(False)
        self.apply_camera(CameraPreset.THREE_QUARTER)
        return loaded_model

    def set_skeleton_overlay(self, rigged_path: Path, visible: bool) -> bool:
        """Render joint points and parent-child lines from a rigged GLB when present."""
        if not visible:
            for actor in (self._skeleton_actor, self._joint_actor):
                if actor is not None:
                    actor.SetVisibility(False)
            self._plotter.render()
            return self._skeleton_actor is not None
        joints, edges = _load_skeleton_geometry(rigged_path)
        self._skeleton_points = joints
        self._skeleton_edges = edges
        if not joints:
            return False
        if self._skeleton_actor is None:
            if edges:
                lines = pv.PolyData(joints)
                lines.lines = [value for start, end in edges for value in (2, start, end)]
                self._skeleton_actor = self._plotter.add_mesh(
                    lines, color="#E97B67", line_width=3, name="skeleton-overlay"
                )
            points = pv.PolyData(joints)
            self._joint_actor = self._plotter.add_mesh(
                points,
                color="#FFD7A3",
                point_size=12,
                render_points_as_spheres=True,
                name="skeleton-joints",
            )
        for actor in (self._skeleton_actor, self._joint_actor):
            if actor is not None:
                actor.SetVisibility(True)
        self._plotter.render()
        return True

    def enable_cpu_skinning(self, rigged_path: Path) -> bool:
        """Decode the GLB skin once so animation edits can deform VTK mesh points."""
        asset = load_skinned_asset(rigged_path)
        if self._loaded_model is None or len(asset.vertices) != self._loaded_model.mesh.n_points:
            return False
        self._skinned_asset = asset
        return True

    def apply_skeletal_pose(self, rotations: dict[str, Quaternion]) -> bool:
        """Apply CPU LBS and update both mesh vertices and parent-child overlay geometry."""
        if self._skinned_asset is None or self._loaded_model is None:
            return False
        vertices, joints = self._skinned_asset.deform(rotations)
        self._loaded_model.mesh.points = vertices
        self._skeleton_points = joints.tolist()
        if self._joint_actor is not None:
            self._joint_actor.mapper.SetInputData(pv.PolyData(joints))
        if self._skeleton_actor is not None and self._skeleton_edges:
            lines = pv.PolyData(joints)
            lines.lines = [
                value for start, end in self._skeleton_edges for value in (2, start, end)
            ]
            self._skeleton_actor.mapper.SetInputData(lines)
        self._plotter.render()
        return True

    def enable_skeleton_picking(self) -> None:
        """Map a clicked/dragged overlay point to the nearest selectable joint."""

        def picked(point: Any) -> None:
            if not self._skeleton_points or point is None:
                return
            nearest = min(
                range(len(self._skeleton_points)),
                key=lambda index: sum(
                    (float(point[i]) - self._skeleton_points[index][i]) ** 2 for i in range(3)
                ),
            )
            self.skeleton_joint_picked.emit(nearest)

        self._plotter.enable_point_picking(callback=picked, show_message=False, left_clicking=True)

    def select_skeleton_joint(self, rigged_path: Path, joint_index: int) -> bool:
        """Highlight a selected joint so bone editing has visible viewer feedback."""
        joints = self._skeleton_points
        if not joints:
            joints, _edges = _load_skeleton_geometry(rigged_path)
        if joint_index < 0 or joint_index >= len(joints):
            return False
        point = pv.PolyData([joints[joint_index]])
        if self._selected_joint_actor is None:
            self._selected_joint_actor = self._plotter.add_mesh(
                point,
                color="#F2A65A",
                point_size=20,
                render_points_as_spheres=True,
                name="selected-skeleton-joint",
            )
        else:
            self._selected_joint_actor.mapper.SetInputData(point)
            self._selected_joint_actor.SetVisibility(True)
        self._plotter.render()
        return True

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
        self._skeleton_actor = None
        self._joint_actor = None
        self._selected_joint_actor = None
        self._skinned_asset = None
        self._loaded_model = None
        super().closeEvent(event)

    def _advance_turntable(self) -> None:
        if self.has_model:
            self._plotter.camera.Azimuth(1.0)
            self._plotter.render()


def _load_skeleton_geometry(path: Path) -> tuple[list[list[float]], list[tuple[int, int]]]:
    """Extract world-space joint locations and hierarchy edges from a GLB skin."""
    gltf = GLTF2().load_binary(str(path))
    if not gltf.skins:
        return [], []
    skin = gltf.skins[0]
    joint_nodes = list(skin.joints or [])
    if not joint_nodes:
        return [], []
    parents: dict[int, int] = {}
    for parent_index, node in enumerate(gltf.nodes):
        for child_index in node.children or []:
            parents[child_index] = parent_index
    joint_set = set(joint_nodes)
    positions = [_node_world_translation(gltf, node_index, parents) for node_index in joint_nodes]
    by_node = {node_index: index for index, node_index in enumerate(joint_nodes)}
    edges = [
        (by_node[parent], by_node[node])
        for node, parent in parents.items()
        if node in joint_set and parent in joint_set
    ]
    return positions, edges


def _node_world_translation(gltf: GLTF2, node_index: int, parents: dict[int, int]) -> list[float]:
    """Accumulate translation-only joint positions for the visual review overlay."""
    position = [0.0, 0.0, 0.0]
    current: int | None = node_index
    while current is not None:
        translation = gltf.nodes[current].translation or [0.0, 0.0, 0.0]
        position = [position[index] + float(translation[index]) for index in range(3)]
        current = parents.get(current)
    return position
