"""Exercise quaternion pose interpolation against a real validated rig asset."""

from __future__ import annotations

import json

from pygltflib import GLTF2

from character_model_studio.animation.poses import PoseDocument, interpolate_pose
from character_model_studio.tools.real_rigging_smoke import resolve_real_rigged_asset
from character_model_studio.validation.rigged_model import RiggedModelValidator


def main() -> int:
    """Prove the Phase 12 pose domain consumes a real rig, not a fixture rig."""
    asset = resolve_real_rigged_asset()
    report = RiggedModelValidator().validate(asset)
    if not report.acceptable:
        raise RuntimeError(f"Animation requires an acceptable real rig: {report.failures}")
    gltf = GLTF2().load_binary(str(asset))
    skin = gltf.skins[0]
    bone = gltf.nodes[skin.joints[0]].name or f"joint-{skin.joints[0]}"
    start = PoseDocument("real-unirig-smoke", {bone: (0.0, 0.0, 0.0, 1.0)})
    end = PoseDocument("real-unirig-smoke", {bone: (0.0, 0.0, 1.0, 0.0)})
    midpoint = interpolate_pose(start, end, 0.5)
    quaternion = midpoint.bones[bone]
    print(
        json.dumps(
            {
                "status": "PASS",
                "asset": str(asset),
                "joint_count": report.metrics.get("joint_count"),
                "animated_bone": bone,
                "midpoint_quaternion": quaternion,
                "interpolation": "shortest-path-slerp",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
