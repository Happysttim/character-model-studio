# 20 — Rigged Model Validation

## Goal

Validate skeleton, skinning, and animation structure independently from static mesh validity.

A valid mesh can still have an invalid rig.

## Result levels

Use:

```text
PASS
PASS_WITH_WARNINGS
FAIL
```

## Skeleton checks

At minimum:

- root joint exists;
- joint/node references resolve;
- hierarchy is acyclic;
- parent/child relationships are internally consistent;
- joint transforms are finite;
- local/world matrix derivation does not produce NaN/Infinity;
- duplicate IDs/names are handled deterministically;
- unexpected multiple roots are warning/failure according to provider contract.

## Skinning checks

At minimum:

- skin references existing joints;
- inverse-bind matrices exist when required and are finite;
- vertex joint indices are in range;
- skin weights are finite;
- negative weights are rejected where invalid;
- per-vertex weights are normalized within tolerance or normalized with an explicit warning/repair policy;
- all-zero influences are detected;
- deformation can be evaluated on a small test pose without crashing;
- mesh/skin vertex counts and accessors are compatible.

## Texture/material preservation

For textured source models:

- material references remain valid;
- texture assets remain accessible;
- rigging did not accidentally replace the accepted source asset;
- texture loss is reported if the selected provider cannot preserve it.

## Animation structure checks

For stored/imported clips:

- target nodes/bones exist;
- timestamps are finite and ordered;
- rotations are valid quaternions;
- quaternions can be normalized safely;
- translation/scale channels have compatible dimensions;
- clip duration is non-negative;
- references match the rig revision.

## Viewer independence

A rig is not valid merely because VTK can draw bone lines.

Validation must operate independently of viewport success.

## Repair policy

Safe deterministic repairs may be offered, for example:

- quaternion normalization;
- small skin-weight normalization error;
- metadata regeneration.

Do not silently repair structural hierarchy corruption, missing joints, or incompatible skin data and then report a clean pass.
