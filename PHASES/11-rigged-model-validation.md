# Phase 11 — Rigged Model Validation

## Goal

Implement the independent skeleton/skinning validation contract.

## Tasks

- implement checks from `SPECS/20-rigged-model-validation.md`;
- fixture suite for valid/invalid hierarchy;
- fixture suite for invalid joint references and transforms;
- fixture suite for skin-weight normalization/reference failures;
- deformation smoke test;
- decode a valid rigged GLB's `JOINTS_0`, `WEIGHTS_0`, and inverse-bind matrices and prove a non-bind test pose changes mesh vertices;
- assert textured rig output retains material/image references when the selected provider promises texture preservation;
- rig validation report persistence;
- review-screen summary and drill-down;
- ensure a valid static mesh with invalid rig remains viewable as a static model.

## Acceptance criteria

- fixture suite classifies expected pass/warning/fail cases;
- malformed rigs fail without crashing the app;
- real generated rigs receive persisted reports;
- animation editing is enabled only for acceptable rigs.

## Current technical decision

Rig validation remains independent of VTK. A successful VTK skeleton overlay is insufficient: hierarchy, accessors, inverse-bind matrices, weight normalization, and a CPU deformation smoke must all remain acceptable before animation editing is enabled.
