# Phase 08 Model Validation Report

**Status:** `PASS_WITH_WARNINGS`

## Delivered

- Static GLB validator isolated from rendering and rig validation.
- `PASS`, `PASS_WITH_WARNINGS`, and `FAIL` report model with check-by-check detail, metrics, warnings, and failures.
- Checks for file presence, parsing, geometry, finite vertices, triangle topology/index range, usable/extreme bounds, degenerate triangles, fragmentation, normals, materials, and viewer conversion.
- SQLite `validation_reports` persistence associated with reconstruction attempts.
- Qt background validation runner and Review workspace summary/detail output. Warning results remain reviewable.
- Canonical `test-model-validation` command.

## Validation

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-model-validation
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 verify
```

The fixture suite passed valid untextured GLB, malformed data, empty data, fragmented geometry, viewer conversion,
and persisted-report coverage. Full verification passed format, lint, strict type checks, and twenty-eight tests.

## Real Provider Evidence

The actual local Hunyuan3D 2.0 Standard Shape workflow now runs the validator after CUDA mesh generation, persists the
report before publishing review readiness, and records the validation outcome in attempt provenance. The offline
workflow smoke completed with `READY_FOR_REVIEW` and a persisted `PASS` report. Its detailed machine-specific
telemetry remains only in the configured local application-data directory.

## Warning

The real workflow smoke uses a generated local MP4 fixture rather than a user capture. The full capture-to-review UI
interaction remains Phase 09 integration work.

## Boundary

Static mesh validation does not validate skeletons, skin weights, inverse-bind matrices, or animation channels. Those checks remain exclusively in Phase 11.

## Privacy

Fixtures are generated locally and contain no user capture content. Reports persist metrics and check results, not raw captured frames or model binary data.

## Phase Decision

Phase 08 fixture and architecture acceptance is complete with the documented real-provider dependency warning. Do not begin Phase 09 or a later phase until explicitly requested.
