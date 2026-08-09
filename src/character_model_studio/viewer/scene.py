"""Independent GLB parsing and conversion for viewer rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pyvista as pv
import trimesh


@dataclass(frozen=True, slots=True)
class LoadedModel:
    """Parsed mesh metadata and the rendering dataset derived from it."""

    source_path: Path
    mesh: pv.PolyData
    vertex_count: int
    face_count: int
    vertex_colors: np.ndarray | None
    base_color_texture: pv.Texture | None


def load_glb_model(path: Path) -> LoadedModel:
    """Parse a GLB with trimesh before converting supported triangles to PyVista."""
    if not path.is_file():
        raise FileNotFoundError(f"Model file does not exist: {path}")

    loaded: Any = trimesh.load(path, force="scene")
    geometries: list[Any] = [
        geometry for geometry in loaded.geometry.values() if isinstance(geometry, trimesh.Trimesh)
    ]
    if not geometries:
        raise ValueError("The GLB does not contain a triangular mesh.")

    mesh: Any = geometries[0] if len(geometries) == 1 else trimesh.util.concatenate(geometries)
    if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        raise ValueError("The GLB mesh is empty.")
    if not np.isfinite(mesh.vertices).all():
        raise ValueError("The GLB contains non-finite vertex values.")

    faces = np.column_stack(
        (np.full(len(mesh.faces), 3, dtype=np.int64), mesh.faces.astype(np.int64, copy=False))
    ).ravel()
    poly_data = pv.PolyData(mesh.vertices.astype(float, copy=False), faces)
    vertex_colors: np.ndarray | None = None
    if mesh.visual.kind == "vertex":
        vertex_colors = np.asarray(mesh.visual.vertex_colors, dtype=np.uint8)
        if vertex_colors.shape == (len(mesh.vertices), 4):
            poly_data["vertex_rgba"] = vertex_colors
        else:
            vertex_colors = None
    base_color_texture = _load_base_color_texture(mesh, poly_data)
    return LoadedModel(
        source_path=path,
        mesh=poly_data,
        vertex_count=len(mesh.vertices),
        face_count=len(mesh.faces),
        vertex_colors=vertex_colors,
        base_color_texture=base_color_texture,
    )


def _load_base_color_texture(mesh: Any, poly_data: pv.PolyData) -> pv.Texture | None:
    """Attach a glTF base-color texture and UVs when the GLB supplies both."""
    if mesh.visual.kind != "texture":
        return None
    uv = getattr(mesh.visual, "uv", None)
    image = getattr(mesh.visual.material, "baseColorTexture", None)
    if uv is None or image is None or np.shape(uv) != (len(mesh.vertices), 2):
        return None
    texture_coordinates = np.asarray(uv, dtype=float)
    poly_data.active_texture_coordinates = texture_coordinates
    return pv.Texture(np.asarray(image.convert("RGB")))  # type: ignore[no-untyped-call]
