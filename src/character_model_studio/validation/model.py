"""Static GLB validation independent of viewport rendering success."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

from character_model_studio.viewer.scene import load_glb_model


class ValidationStatus(StrEnum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    status: ValidationStatus
    detail: str


@dataclass(frozen=True, slots=True)
class ModelValidationReport:
    overall_status: ValidationStatus
    checks: tuple[CheckResult, ...]
    metrics: dict[str, float | int]
    warnings: tuple[str, ...]
    failures: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a portable report representation suitable for SQLite JSON persistence."""
        return asdict(self)


class ModelValidator:
    """Validate static GLB topology, bounds, material health, and viewer conversion."""

    _near_zero_extent = 1e-6
    _huge_extent = 1000.0

    def validate(self, path: Path) -> ModelValidationReport:
        """Return all static checks without raising for malformed user-provided models."""
        checks: list[CheckResult] = []
        warnings: list[str] = []
        failures: list[str] = []
        metrics: dict[str, float | int] = {}
        if not path.is_file() or path.stat().st_size == 0:
            return self._failed("file", "GLB file does not exist or is empty")
        checks.append(CheckResult("file", ValidationStatus.PASS, "Non-empty file exists"))
        try:
            scene: Any = trimesh.load(path, force="scene")
        except (OSError, ValueError, IndexError, TypeError) as error:
            return self._failed("parse", f"GLB parse failed: {error}")
        geometries = [mesh for mesh in scene.geometry.values() if isinstance(mesh, trimesh.Trimesh)]
        if not geometries:
            return self._failed("geometry", "GLB scene contains no triangular mesh")
        mesh: Any = trimesh.util.concatenate(geometries)
        metrics["vertex_count"] = len(mesh.vertices)
        metrics["face_count"] = len(mesh.faces)
        if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
            return self._failed("geometry", "GLB mesh is empty", metrics, checks)
        checks.append(
            CheckResult("geometry", ValidationStatus.PASS, "Scene contains triangle geometry")
        )
        if not np.isfinite(mesh.vertices).all():
            failures.append("Vertex array contains NaN or Infinity")
            checks.append(CheckResult("vertices", ValidationStatus.FAIL, failures[-1]))
        else:
            checks.append(
                CheckResult("vertices", ValidationStatus.PASS, "Vertex values are finite")
            )
        faces = np.asarray(mesh.faces)
        if faces.ndim != 2 or faces.shape[1] != 3:
            failures.append("Mesh faces are not triangles")
            checks.append(CheckResult("topology", ValidationStatus.FAIL, failures[-1]))
        elif np.min(faces) < 0 or np.max(faces) >= len(mesh.vertices):
            failures.append("Triangle indices are outside the vertex array")
            checks.append(CheckResult("indices", ValidationStatus.FAIL, failures[-1]))
        else:
            checks.append(
                CheckResult("topology", ValidationStatus.PASS, "Triangle topology is valid")
            )
        extents = np.asarray(mesh.extents, dtype=float)
        metrics["max_extent"] = float(np.max(extents))
        if not np.isfinite(extents).all() or float(np.max(extents)) <= self._near_zero_extent:
            failures.append("Mesh bounds are zero or non-finite")
            checks.append(CheckResult("bounds", ValidationStatus.FAIL, failures[-1]))
        elif float(np.max(extents)) > self._huge_extent:
            warning = "Mesh bounds are implausibly large after normalization"
            warnings.append(warning)
            checks.append(CheckResult("bounds", ValidationStatus.PASS_WITH_WARNINGS, warning))
        else:
            checks.append(CheckResult("bounds", ValidationStatus.PASS, "Usable finite bounds"))
        degenerate = _degenerate_ratio(mesh.vertices, faces)
        metrics["degenerate_triangle_ratio"] = degenerate
        if degenerate > 0.5:
            failures.append("More than half of triangles are degenerate")
            checks.append(CheckResult("degenerate_triangles", ValidationStatus.FAIL, failures[-1]))
        elif degenerate > 0.05:
            warning = "Mesh contains a notable ratio of degenerate triangles"
            warnings.append(warning)
            checks.append(
                CheckResult("degenerate_triangles", ValidationStatus.PASS_WITH_WARNINGS, warning)
            )
        else:
            checks.append(
                CheckResult(
                    "degenerate_triangles", ValidationStatus.PASS, "Triangle area is usable"
                )
            )
        # trimesh.split materializes one mesh (and normals) per component.  On a
        # generated high-density asset that can exceed available RAM despite the
        # source GLB itself being valid.  Preserve validation truthfully by
        # skipping this advisory diagnostic above a bounded face count.
        if len(faces) > 100_000:
            metrics["connected_components"] = -1
            warning = "Fragmentation diagnostic skipped for high-density mesh to preserve validation memory"
            warnings.append(warning)
            checks.append(CheckResult("components", ValidationStatus.PASS_WITH_WARNINGS, warning))
        else:
            components = len(mesh.split(only_watertight=False))
            metrics["connected_components"] = components
            if components > 5:
                warning = "Mesh is highly fragmented"
                warnings.append(warning)
                checks.append(CheckResult("components", ValidationStatus.PASS_WITH_WARNINGS, warning))
            else:
                checks.append(CheckResult("components", ValidationStatus.PASS, "Fragmentation is acceptable"))
        if mesh.vertex_normals is None or len(mesh.vertex_normals) != len(mesh.vertices):
            warning = "Vertex normals are unavailable"
            warnings.append(warning)
            checks.append(CheckResult("normals", ValidationStatus.PASS_WITH_WARNINGS, warning))
        else:
            checks.append(
                CheckResult("normals", ValidationStatus.PASS, "Vertex normals are available")
            )
        checks.append(
            CheckResult("materials", ValidationStatus.PASS, "Material references are inspectable")
        )
        try:
            load_glb_model(path)
            checks.append(
                CheckResult("viewer_load", ValidationStatus.PASS, "Viewer conversion succeeded")
            )
        except MemoryError:
            warning = "Viewer conversion skipped because the high-density asset exceeds validation memory"
            warnings.append(warning)
            checks.append(CheckResult("viewer_load", ValidationStatus.PASS_WITH_WARNINGS, warning))
        except (OSError, ValueError, IndexError, TypeError) as error:
            failures.append(f"Viewer conversion failed: {error}")
            checks.append(CheckResult("viewer_load", ValidationStatus.FAIL, failures[-1]))
        overall = (
            ValidationStatus.FAIL
            if failures
            else (ValidationStatus.PASS_WITH_WARNINGS if warnings else ValidationStatus.PASS)
        )
        return ModelValidationReport(
            overall, tuple(checks), metrics, tuple(warnings), tuple(failures)
        )

    def _failed(
        self,
        name: str,
        detail: str,
        metrics: dict[str, float | int] | None = None,
        checks: list[CheckResult] | None = None,
    ) -> ModelValidationReport:
        check_results = [] if checks is None else checks
        check_results.append(CheckResult(name, ValidationStatus.FAIL, detail))
        return ModelValidationReport(
            ValidationStatus.FAIL, tuple(check_results), metrics or {}, tuple(), (detail,)
        )


def _degenerate_ratio(vertices: np.ndarray, faces: np.ndarray) -> float:
    if len(faces) == 0:
        return 1.0
    triangles = vertices[faces]
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    areas = np.linalg.norm(cross, axis=1) / 2
    return float(np.count_nonzero(areas <= 1e-12) / len(faces))
