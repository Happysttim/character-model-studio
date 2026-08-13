"""Pose serialization and shortest-path quaternion interpolation."""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, sin, sqrt
from typing import cast

Quaternion = tuple[float, float, float, float]


def normalize_quaternion(value: Quaternion) -> Quaternion:
    """Normalize project-order `[x, y, z, w]` quaternions and reject zero values."""
    length = sqrt(sum(component * component for component in value))
    if length <= 1e-12:
        raise ValueError("A rotation quaternion cannot be zero")
    return tuple(component / length for component in value)  # type: ignore[return-value]


def slerp(start: Quaternion, end: Quaternion, progress: float) -> Quaternion:
    """Interpolate rotations via shortest-path SLERP; Euler interpolation is never used."""
    a = normalize_quaternion(start)
    b = normalize_quaternion(end)
    dot = sum(first * second for first, second in zip(a, b, strict=True))
    if dot < 0:
        b = (-b[0], -b[1], -b[2], -b[3])
        dot = -dot
    dot = max(-1.0, min(1.0, dot))
    if dot > 0.9995:
        return normalize_quaternion(
            cast(Quaternion, tuple(a[i] + progress * (b[i] - a[i]) for i in range(4)))
        )
    angle = acos(dot)
    scale_a = sin((1 - progress) * angle) / sin(angle)
    scale_b = sin(progress * angle) / sin(angle)
    return normalize_quaternion(
        cast(Quaternion, tuple(scale_a * a[i] + scale_b * b[i] for i in range(4)))
    )


@dataclass(frozen=True, slots=True)
class PoseDocument:
    """Local bone rotations for one specific persisted rig revision."""

    rig_revision: str
    bones: dict[str, Quaternion]

    def as_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "rigRevision": self.rig_revision,
            "bones": {key: list(normalize_quaternion(value)) for key, value in self.bones.items()},
        }


def interpolate_pose(start: PoseDocument, end: PoseDocument, progress: float) -> PoseDocument:
    """SLERP all matching bones and retain bind identity for absent counterparts."""
    if start.rig_revision != end.rig_revision:
        raise ValueError("Cannot interpolate poses from different rig revisions")
    identity: Quaternion = (0.0, 0.0, 0.0, 1.0)
    keys = set(start.bones) | set(end.bones)
    return PoseDocument(
        start.rig_revision,
        {
            key: slerp(start.bones.get(key, identity), end.bones.get(key, identity), progress)
            for key in keys
        },
    )
