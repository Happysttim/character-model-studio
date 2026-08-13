"""Validate a locally generated UniRig asset without substituting fixture geometry."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pygltflib import GLTF2

from character_model_studio.platform.windows.paths import resolve_application_paths
from character_model_studio.validation.model import ModelValidator
from character_model_studio.validation.rigged_model import RiggedModelValidator


def resolve_real_rigged_asset() -> Path:
    """Resolve an explicitly configured real rig, falling back to local exports."""
    configured = os.environ.get("CHARACTER_MODEL_STUDIO_REAL_RIGGED_GLB")
    if configured:
        return Path(configured)
    exports = resolve_application_paths().root_directory / "exports"
    return exports / "unirig-textured-rigged-smoke.glb"


def main() -> int:
    """Assert skeleton, weights, and source texture resources exist in a real asset."""
    asset = resolve_real_rigged_asset()
    if not asset.is_file():
        raise FileNotFoundError(
            "Real UniRig GLB is required for this smoke test. Set "
            "CHARACTER_MODEL_STUDIO_REAL_RIGGED_GLB or export a real rigged GLB first."
        )
    rig_report = RiggedModelValidator().validate(asset)
    static_report = ModelValidator().validate(asset)
    gltf = GLTF2().load_binary(str(asset))
    if not rig_report.acceptable:
        raise RuntimeError(f"Real UniRig GLB failed rig validation: {rig_report.failures}")
    if not gltf.skins or not gltf.materials or not gltf.textures or not gltf.images:
        raise RuntimeError("Real UniRig GLB must contain a skin and preserved texture resources")
    print(
        json.dumps(
            {
                "status": "PASS",
                "asset": str(asset),
                "rig_validation": rig_report.overall_status.value,
                "static_validation": static_report.overall_status.value,
                "joint_count": rig_report.metrics.get("joint_count"),
                "skinned_vertex_count": rig_report.metrics.get("skinned_vertex_count"),
                "materials": len(gltf.materials),
                "textures": len(gltf.textures),
                "images": len(gltf.images),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
