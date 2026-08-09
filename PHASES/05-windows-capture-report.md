# Phase 05 Windows Region Capture Report

**Status:** `PASS_WITH_WARNINGS`

## Delivered

- Windows `Ctrl+Alt+S` global hotkey registration/release through an isolated native-event filter.
- One-monitor transparent region selector with warm high-contrast boundary, dimensions, Escape cancel, Enter confirmation, and minimum physical-pixel size enforcement.
- DPI-aware logical-to-physical conversion, including 100%, 125%, 150%, and 200% automated geometry coverage.
- DXcam Desktop Duplication adapter for BGR region frames.
- Background Qt-thread capture worker with idempotent stop, frame-dimension protection, timestamped elapsed updates, and resource release.
- Local PyAV MP4/H.264 encoder, thumbnail generation, local preview surface, discard, and re-record workflow.
- A recording indicator positioned outside the selected source region so it is not included by the region capture.
- Capture failure messaging that preserves existing project data.

## Automated Validation

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-capture
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 verify
```

`test-capture` passed seven tests: the four DPI scale factors, one-monitor/minimum-size rejection, idempotent worker stop/resource release, thumbnail output, and reopening a real PyAV-generated H.264 MP4. `verify` passed format, lint, strict type checks, and all seventeen tests.

## Windows Smoke Checks

- A real DXcam Desktop Duplication smoke test captured a `320 × 240` region and verified the frame dimensions.
- A real DXcam frame was encoded to a temporary H.264 MP4 and thumbnail at the same `320 × 240` dimensions. The temporary artifacts were deleted without inspecting or retaining screen content.
- Windows successfully registered and released `Ctrl+Alt+S` in a live Qt process.

## DPI Matrix

| Display scale | Automated logical-to-physical result |
| --- | --- |
| 100% | 1.00× conversion |
| 125% | 1.25× conversion |
| 150% | 1.50× conversion |
| 200% | 2.00× conversion |

## Warning / Manual Follow-up

Sustained 30 FPS and visual overlay placement across mixed-DPI, multi-monitor desktop layouts must still be confirmed interactively on representative target displays. The implementation rejects cross-monitor regions for the MVP and does not silently fall back to a generic screenshot loop.

## Privacy

No machine-specific paths, hardware identifiers, account information, or captured-frame content is embedded in source or this report. Capture artifacts remain local and are only deleted through the explicit Discard action.

## Deferred by Design

- Associating a finalized capture with the selected project and launch of reconstruction: Phase 09 integration.
- Frame selection, quality scoring, and segmentation: their assigned reconstruction phases.
- Real CUDA reconstruction and provider loading: Phase 06 and Phase 07.

## Phase Decision

Phase 05 implementation and automated/native smoke criteria are met with the documented manual visual/performance follow-up. Do not begin Phase 06 or a later phase until explicitly requested.
