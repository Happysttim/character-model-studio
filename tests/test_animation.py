"""Quaternion pose persistence primitives."""

from __future__ import annotations

from character_model_studio.animation.poses import (
    PoseDocument,
    interpolate_pose,
    normalize_quaternion,
    slerp,
)


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
