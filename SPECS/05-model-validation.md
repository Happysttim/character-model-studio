# 05 — Model Validation

## Purpose

Validation determines whether the generated GLB is technically usable and inspectable. It does not measure visual faithfulness to the source character.

## Result levels

- `PASS`
- `PASS_WITH_WARNINGS`
- `FAIL`

## Required checks

At minimum:

- file exists and non-zero length;
- GLB parses;
- scene contains geometry;
- vertex arrays are finite;
- indices are in range;
- triangle topology is structurally valid;
- non-zero usable bounds;
- bounds are not implausibly extreme after normalization;
- degenerate triangle ratio;
- connected-component count/fragmentation warning;
- normals availability/consistency where relevant;
- material presence;
- texture/image reference health where applicable;
- transform hierarchy can be resolved;
- final viewer load smoke test.

## Libraries

Use `trimesh` as the primary geometry inspection layer. Use lower-level glTF parsing only when required for a check that trimesh does not expose.

## Report

The validation report must include:

- overall status;
- check-by-check status;
- metrics;
- warnings;
- fatal reasons;
- recommended action where useful.

The user can still inspect warning-level models.

For high-density generated meshes, diagnostics must remain bounded in memory. A connected-component calculation that would materialize excessive mesh copies may be skipped with `PASS_WITH_WARNINGS`; it must not turn a successfully generated GLB into a false reconstruction failure. Likewise, a viewer-conversion `MemoryError` is a warning-level diagnostic when core GLB parsing and geometry checks have passed.

## Rigging boundary

This specification validates the static 3D asset layer. Skeleton, skinning and animation structure are validated separately by `SPECS/20-rigged-model-validation.md`.

A static `PASS` does not imply that a later rig is valid.
