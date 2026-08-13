# Phase 07 — Real Reconstruction Pipeline

## Goal

Generate an actual GLB from local captured input using the Standard provider first, while supporting an optional High Quality provider behind capability checks.

## Tasks

- video probe/frame extraction;
- frame scoring/deduplication;
- representative view selection;
- Windows-native CUDA segmentation adapter with persisted RGBA/mask artifacts;
- normalized provider input artifacts;
- Hunyuan3D 2.0 Standard provider adapter;
- Hunyuan3D 2.1 High Quality provider adapter only when Phase 00/06 compatibility is proven;
- Standard geometry generation;
- Standard texture generation when 2.0 capability permits;
- High Quality shape/texture only according to the explicit 2.1 capability gate;
- GLB normalization/export;
- progress/cancellation/error surfaces;
- record quality mode/provider/version/inputs/metrics.

## Acceptance criteria

- a representative capture generates a non-empty GLB locally using Standard mode;
- a real CUDA path is evidenced;
- generated GLB opens in the Phase 03 viewer;
- attempt artifacts and metadata persist;
- Standard vs High Quality is explicit in history;
- user can regenerate with different parameters/quality without losing the prior attempt;
- High Quality unavailable state is truthful and does not break Standard mode.

## Completion evidence

Record commands run, tests passed, manual checks, actual provider/version, VRAM metrics, and any environment blockers.
