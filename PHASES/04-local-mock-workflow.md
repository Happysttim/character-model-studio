# Phase 04 — Local Mock Workflow

## Goal

Prove the entirely local in-process workflow and future maximum-scope domain boundaries before heavyweight AI providers are introduced.

## Tasks

- Implement project/capture/reconstruction-attempt repositories.
- Implement reconstruction attempt state machine.
- Implement background task runner and progress signals.
- Add mock Standard and High Quality reconstruction providers that stage realistically and return fixture GLBs.
- Persist reconstruction quality mode/provider metadata.
- Implement cancellation.
- Implement attempt history.
- Implement Accept/Reject/Regenerate.
- Scaffold rig attempt, pose and animation persistence/domain contracts without real AI.
- Add a mock rigging provider that can publish a fixture rigged GLB for harness/UI tests.
- Verify restart persistence for accepted model and fixture rig/animation metadata.

## Acceptance criteria

End-to-end local reconstruction workflow works with no sockets/server:

`capture fixture → attempt → mock progress → GLB → review → accept/reject/regenerate`.

The domain/storage architecture can also represent:

`accepted model → mock rig → pose/animation state`

without introducing a second application or service boundary.

## Completion evidence

Record commands run, tests passed, manual checks performed, and any environment blockers.
