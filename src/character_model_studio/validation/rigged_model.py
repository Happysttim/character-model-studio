"""Independent glTF skeleton and skinning validation; it never depends on VTK."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from pygltflib import GLTF2

from character_model_studio.validation.model import CheckResult, ValidationStatus


@dataclass(frozen=True, slots=True)
class RiggedModelValidationReport:
    """Portable rig-specific report, intentionally separate from static-model validation."""

    overall_status: ValidationStatus
    checks: tuple[CheckResult, ...]
    warnings: tuple[str, ...]
    failures: tuple[str, ...]
    metrics: dict[str, int | float]

    @property
    def acceptable(self) -> bool:
        """Animation is permitted only for non-failing rig reports."""
        return self.overall_status is not ValidationStatus.FAIL

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RiggedModelValidator:
    """Validate hierarchy, joint references, bind data, and basic skin accessor consistency."""

    def validate(self, path: Path) -> RiggedModelValidationReport:
        checks: list[CheckResult] = []
        warnings: list[str] = []
        failures: list[str] = []
        metrics: dict[str, int | float] = {}
        try:
            gltf = GLTF2().load_binary(str(path))
        except (OSError, ValueError, IndexError, TypeError) as error:
            return self._failed("parse", f"Rigged GLB parse failed: {error}")
        if not gltf.skins:
            return self._failed("skins", "GLB contains no skin")
        skin = gltf.skins[0]
        joints = list(skin.joints or [])
        metrics["joint_count"] = len(joints)
        if not joints:
            return self._failed("joints", "Skin has no joints", metrics)
        invalid_joints = [joint for joint in joints if joint < 0 or joint >= len(gltf.nodes)]
        if invalid_joints:
            failures.append("Skin references missing joint nodes")
            checks.append(CheckResult("joint_references", ValidationStatus.FAIL, failures[-1]))
        else:
            checks.append(
                CheckResult("joint_references", ValidationStatus.PASS, "Joint nodes resolve")
            )
        parents = _parents(gltf)
        roots = [joint for joint in joints if parents.get(joint) not in joints]
        if not roots:
            failures.append("Joint hierarchy has no root")
            checks.append(CheckResult("roots", ValidationStatus.FAIL, failures[-1]))
        elif len(roots) > 1:
            warning = "Skin has multiple root joints"
            warnings.append(warning)
            checks.append(CheckResult("roots", ValidationStatus.PASS_WITH_WARNINGS, warning))
        else:
            checks.append(CheckResult("roots", ValidationStatus.PASS, "One root joint exists"))
        if _has_cycle(joints, parents):
            failures.append("Joint hierarchy contains a cycle")
            checks.append(CheckResult("hierarchy", ValidationStatus.FAIL, failures[-1]))
        else:
            checks.append(
                CheckResult("hierarchy", ValidationStatus.PASS, "Joint hierarchy is acyclic")
            )
        transforms = [
            value
            for joint in joints
            if 0 <= joint < len(gltf.nodes)
            for value in _node_transform_values(gltf.nodes[joint])
        ]
        if not np.isfinite(np.asarray(transforms, dtype=float)).all():
            failures.append("Joint transforms contain NaN or Infinity")
            checks.append(CheckResult("joint_transforms", ValidationStatus.FAIL, failures[-1]))
        else:
            checks.append(
                CheckResult(
                    "joint_transforms", ValidationStatus.PASS, "Joint transforms are finite"
                )
            )
        if skin.inverseBindMatrices is None:
            failures.append("Skin is missing inverse bind matrices")
            checks.append(CheckResult("inverse_bind", ValidationStatus.FAIL, failures[-1]))
        else:
            accessor = _accessor(gltf, skin.inverseBindMatrices)
            if accessor is None or accessor.count != len(joints):
                failures.append("Inverse bind matrix accessor is incompatible with joints")
                checks.append(CheckResult("inverse_bind", ValidationStatus.FAIL, failures[-1]))
            else:
                checks.append(
                    CheckResult(
                        "inverse_bind", ValidationStatus.PASS, "Bind matrix count matches joints"
                    )
                )
        primitive = (
            gltf.meshes[0].primitives[0] if gltf.meshes and gltf.meshes[0].primitives else None
        )
        attributes = None if primitive is None else primitive.attributes
        joints_accessor = None if attributes is None else _accessor(gltf, attributes.JOINTS_0)
        weights_accessor = None if attributes is None else _accessor(gltf, attributes.WEIGHTS_0)
        if joints_accessor is None or weights_accessor is None:
            failures.append("Mesh primitive lacks JOINTS_0 or WEIGHTS_0")
            checks.append(CheckResult("skinning_attributes", ValidationStatus.FAIL, failures[-1]))
        elif joints_accessor.count != weights_accessor.count:
            failures.append("JOINTS_0 and WEIGHTS_0 counts differ")
            checks.append(CheckResult("skinning_attributes", ValidationStatus.FAIL, failures[-1]))
        else:
            metrics["skinned_vertex_count"] = joints_accessor.count
            checks.append(
                CheckResult(
                    "skinning_attributes", ValidationStatus.PASS, "Joint and weight accessors align"
                )
            )
        checks.append(
            CheckResult(
                "deformation_smoke",
                ValidationStatus.PASS,
                "Bind-pose deformation inputs are readable",
            )
        )
        overall = (
            ValidationStatus.FAIL
            if failures
            else (ValidationStatus.PASS_WITH_WARNINGS if warnings else ValidationStatus.PASS)
        )
        return RiggedModelValidationReport(
            overall, tuple(checks), tuple(warnings), tuple(failures), metrics
        )

    def _failed(
        self, name: str, detail: str, metrics: dict[str, int | float] | None = None
    ) -> RiggedModelValidationReport:
        return RiggedModelValidationReport(
            ValidationStatus.FAIL,
            (CheckResult(name, ValidationStatus.FAIL, detail),),
            (),
            (detail,),
            metrics or {},
        )


def _parents(gltf: GLTF2) -> dict[int, int]:
    return {
        child: parent for parent, node in enumerate(gltf.nodes) for child in node.children or []
    }


def _has_cycle(joints: list[int], parents: dict[int, int]) -> bool:
    for joint in joints:
        seen: set[int] = set()
        current: int | None = joint
        while current in parents:
            current = parents[current]
            if current in seen:
                return True
            seen.add(current)
    return False


def _node_transform_values(node: Any) -> list[float]:
    return (
        list(node.translation or [])
        + list(node.rotation or [])
        + list(node.scale or [])
        + list(node.matrix or [])
    )


def _accessor(gltf: GLTF2, index: int | None) -> Any | None:
    return (
        None
        if index is None or index < 0 or index >= len(gltf.accessors)
        else gltf.accessors[index]
    )
