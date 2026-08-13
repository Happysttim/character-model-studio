"""Quaternion pose persistence primitives."""

from __future__ import annotations

from character_model_studio.animation.poses import (
    PoseDocument,
    interpolate_pose,
    normalize_quaternion,
    slerp,
)
from character_model_studio.animation.skinning import load_skinned_asset
from character_model_studio.rigging.fixture_glb import write_fixture_rigged_glb


def test_slerp_uses_shortest_path_and_normalizes() -> None:
    midpoint = slerp((0.0, 0.0, 0.0, 1.0), (0.0, 0.0, 0.0, -1.0), 0.5)
    assert midpoint == (0.0, 0.0, 0.0, 1.0)
    assert normalize_quaternion((0.0, 0.0, 0.0, 2.0)) == (0.0, 0.0, 0.0, 1.0)


def test_pose_interpolation_preserves_rig_revision() -> None:
    start = PoseDocument("rig-1", {"spine": (0.0, 0.0, 0.0, 1.0)})
    end = PoseDocument("rig-1", {"spine": (0.0, 0.0, 1.0, 0.0)})
    result = interpolate_pose(start, end, 0.5)
    assert result.rig_revision == "rig-1"
    assert abs(sum(value * value for value in result.bones["spine"]) - 1.0) < 1e-8


def test_cpu_linear_blend_skinning_deforms_fixture_and_updates_child_joint(tmp_path) -> None:
    path = tmp_path / "rigged.glb"
    write_fixture_rigged_glb(path)
    asset = load_skinned_asset(path)

    bind_vertices, bind_joints = asset.deform({})
    posed_vertices, posed_joints = asset.deform({"Root": (0.0, 0.0, 0.70710678, 0.70710678)})

    assert bind_vertices.shape == posed_vertices.shape == (4, 3)
    assert not (bind_vertices == posed_vertices).all()
    assert not (bind_joints == posed_joints).all()
