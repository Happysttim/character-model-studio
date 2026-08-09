"""Independent GLB parsing tests for the viewer layer."""

from __future__ import annotations

from pathlib import Path

import trimesh

from character_model_studio.viewer.scene import load_glb_model


def test_load_glb_model_converts_triangles_to_polydata(tmp_path: Path) -> None:
    fixture_path = tmp_path / "fixture.glb"
    trimesh.creation.box().export(fixture_path)

    loaded = load_glb_model(fixture_path)

    assert loaded.vertex_count == 8
    assert loaded.face_count == 12
    assert loaded.mesh.n_points == 8


def test_load_glb_model_keeps_vertex_colors_for_the_viewer(tmp_path: Path) -> None:
    fixture_path = tmp_path / "colored.glb"
    mesh = trimesh.creation.box()
    mesh.visual.vertex_colors = [31, 122, 201, 255]
    mesh.export(fixture_path)

    loaded = load_glb_model(fixture_path)

    assert loaded.vertex_colors is not None
    assert loaded.mesh["vertex_rgba"].shape == (8, 4)
