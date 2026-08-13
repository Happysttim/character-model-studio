# Phase 05 — Windows Region Capture

## Goal

Implement the real Windows capture experience.

## Tasks

- Global `Alt + /` registration.
- Monitor-aware region selection overlay.
- DPI-correct physical pixel conversion.
- DXcam region capture.
- recording indicator excluded from captured image.
- H.264 MP4 encoding.
- finalize thumbnail/metadata.
- capture preview and discard/re-record.
- error recovery for display/device changes.

## Acceptance criteria

- Captured file matches selected region.
- 30 FPS target is reasonably maintained on target hardware.
- multi-monitor cross-boundary selection is blocked for MVP.
- hotkey starts/stops reliably.
- DPI test matrix is documented.

## Completion evidence

Record commands run, tests passed, manual checks performed, and any environment blockers. A phase is not complete from code generation alone.
