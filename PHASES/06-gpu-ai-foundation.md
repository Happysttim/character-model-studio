# Phase 06 — GPU / AI Runtime Foundation

## Goal

Create the in-app CUDA execution and capability lanes without yet requiring the full production workflow.

## Tasks

- Implement GPU capability service.
- Implement Standard/High Quality reconstruction mode model.
- Implement reconstruction provider interface.
- Implement rigging provider interface.
- Implement heavyweight AI task lane/orchestrator.
- Implement lazy load/unload lifecycle.
- Implement truthful total/free/peak VRAM telemetry.
- Implement product VRAM tier classification from `SPECS/11-gpu-runtime.md`.
- Implement provider compatibility/readiness state independent from VRAM state.
- Implement CUDA OOM/error mapping.
- Run Hunyuan3D 2.0 Standard initialization smoke test when eligible.
- Run optional Hunyuan3D 2.1 initialization smoke test when installed/eligible.
- Run selected rigging-provider initialization smoke test when installed/eligible.
- Expose readiness/requirements in Diagnostics and generation UX.

## Acceptance criteria

- Real CUDA execution is proven.
- Standard/HQ/rigging capabilities are distinct.
- Hunyuan3D 2.0 is the default Standard policy.
- Hunyuan3D 2.1 is never silently selected.
- UI stays responsive during GPU smoke work.
- no CPU fallback is reported as a GPU success.
- no API server/worker process architecture is introduced.

## Completion evidence

Record commands run, tests passed, manual checks, detected tier, provider readiness and environment blockers.
