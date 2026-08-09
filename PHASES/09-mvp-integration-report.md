# Phase 09 MVP Integration Report

**Status:** `PASS_WITH_WARNINGS`

## Delivered

- Native Capture workspace connection from recorded MP4 preview to project-local capture registration, real Standard Shape attempt, background progress/error/cancellation state, persisted validation, and review navigation.
- Standard attempts now isolate the selected character frame through the local CUDA segmentation provider before Hunyuan Shape inference, preserving the original frame, RGBA foreground, and alpha mask as attempt artifacts.
- Review workspace connection that opens the real generated GLB, displays the selected source frame, persists Accept/Reject decisions, and returns Regenerate to Capture without a server boundary.
- Startup recovery that marks interrupted active attempts as failed while preserving their artifacts and leaving non-active attempts untouched.
- Project-history query for reopening local project metadata.
- Diagnostics actions for copying the local runtime report and opening the local log folder.
- Integration harness command `test-integration`.

## Automated Validation

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-integration
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-reconstruction
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 verify
```

The automated integration test continues to cover the local Mock Standard contract:

```text
project -> fixture capture -> reconstruction attempt -> mock GLB/texture
-> static validation -> viewer conversion -> accept -> restart -> persisted acceptance
```

It also verifies interrupted-attempt recovery and project history reopening. The real offline Standard workflow smoke
separately proves local MP4 preprocessing, CUDA Shape generation, persisted validation, viewer conversion, and
review-ready publication using the downloaded local checkpoint. Full verification passed formatting, linting, strict
type checks, and twenty-eight tests.

## Provider Warning

Hunyuan3D 2.0 Standard Shape is available through the local cache-only provider path. Texture is intentionally not
loaded because the current capability policy does not qualify the Standard textured pipeline. High Quality remains
explicitly disabled by its independent readiness gate.

## Manual Follow-up

The integrated screens still require a manual Windows visual acceptance pass using an actual on-screen character:
capture preview, real processing progress, cancellation/error wording, generated-model source comparison, and review
actions. The automated real smoke uses a generated local capture fixture, so it does not measure visual fidelity to a
user's character.

## Privacy

The integration test uses generated fixtures under a temporary local project root. No raw user capture data, machine-specific paths, or hardware identifiers are committed.

## Phase Decision

The local MVP integration contract is complete with the documented real-provider and manual-visual warnings. Do not begin Phase 10 or a later phase until explicitly requested.
