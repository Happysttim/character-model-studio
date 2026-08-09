# Phase 06 GPU / AI Runtime Foundation Report

**Status:** `PASS_WITH_WARNINGS`

## Delivered

- Runtime CUDA probe that keeps total physical VRAM, current free VRAM, allocated VRAM, and reserved VRAM distinct.
- Product VRAM classification using only total physical VRAM and the exact policy thresholds from `SPECS/11-gpu-runtime.md`.
- Independent capability flags for CUDA, Standard shape/textured workflow, High Quality shape/texture/combined workflow, auto-rigging, skeleton editing, animation editing, animation playback, and full-product lanes.
- Separate provider readiness reporting for Hunyuan3D 2.0, Hunyuan3D 2.1, and SkinTokens / TokenRig. Adapter installation and VRAM eligibility are both retained instead of being conflated.
- Abstract reconstruction and rigging provider contracts with explicit lazy `load`/`unload` lifecycle methods.
- Serialized heavyweight task lane that unloads one provider before another provider can own GPU memory, plus CUDA OOM error mapping.
- Diagnostics and capture quality UI that display actionable provider/runtime readiness without selecting High Quality silently.
- Canonical `test-gpu` and `test-provider-compatibility` commands.

## Validation

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-gpu
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-provider-compatibility
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 verify
```

The real CUDA smoke test passed: a CUDA-resident PyTorch tensor operation executed and remained on the selected CUDA device. The runtime derived the `STANDARD_SHAPE_PLUS_HQ_SHAPE_CANDIDATE` tier from total physical VRAM; free VRAM was recorded separately at runtime.

The full verification suite passed format, lint, strict type checks, and automated tests. Capability policy tests cover every documented VRAM threshold and prove that editor capabilities are not incorrectly disabled when CUDA is unavailable. Heavyweight-lane tests prove each lifecycle unloads before the next one loads.

## Provider Readiness / Blockers

- Hunyuan3D 2.0: `NOT_INSTALLED`. Its adapter and weights are absent, so no initialization or inference is claimed.
- Hunyuan3D 2.1: `NOT_INSTALLED`. It remains optional and unavailable; it is not selected in place of Standard.
- SkinTokens / TokenRig: `VRAM_INELIGIBLE`, and its adapter/weights are absent. No auto-rigging capability is claimed.

No CPU fallback was used for the CUDA smoke test. Since no eligible real provider adapter is installed, real provider initialization, inference, output validation, and unload smoke testing remain blocked rather than mocked.

## Privacy

GPU model, driver, absolute paths, account information, and raw telemetry values are resolved only at local runtime. They are not hardcoded in source or committed to this report.

## Deferred by Design

- Real provider adapters, checkpoint installation, and Standard reconstruction: Phase 07.
- Static model validation: Phase 08.
- Reconstruction MVP integration: Phase 09.

## Phase Decision

Phase 06 runtime foundation is complete with documented provider-environment blockers. Do not begin Phase 07 or a later phase until explicitly requested.
