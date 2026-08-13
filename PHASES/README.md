# Implementation Phases

This is a greenfield project. No phase assumes legacy source migration.

| Phase | Name | Initial status |
|---:|---|---|
| 00 | Environment Validation | Evidence recorded |
| 01 | Python Repository Scaffold | Evidence recorded |
| 02 | Design System and Desktop Shell | Evidence recorded; screenshots must be refreshed after major shell changes |
| 03 | Embedded 3D Model Viewer | Evidence recorded; Windows teardown smoke is required after VTK lifecycle changes |
| 04 | Local Mock Workflow | Evidence recorded |
| 05 | Windows Region Capture | Evidence recorded |
| 06 | GPU / AI Runtime Foundation | Evidence recorded |
| 07 | Real Reconstruction Pipeline | Evidence recorded |
| 08 | Static Model Validation | Evidence recorded |
| 09 | Reconstruction MVP Integration | Evidence recorded |
| 10 | Automatic Rigging | Implemented with UniRig isolated-runtime evidence; consolidate phase report on next phase audit |
| 11 | Rigged Model Validation | Implemented; includes real rig and deformation validation |
| 12 | Skeleton Pose and Animation | Implemented; CPU LBS is the current preview path |
| 13 | Maximum-Scope Product Integration | Implemented; final full-path/manual capability audit remains required |
| 14 | Windows Packaging | Packaging baseline exists; clean-account distributable proof remains required |

## Order rule

Implement phases in order unless the user explicitly changes priorities.

Do not begin the expensive real-AI phase until the local mock workflow proves that the UI/state/storage/viewer architecture works without a server.

Phase 09 is a usable **Reconstruction MVP milestone**, not project completion.

The current maximum product target is reached through Phase 13 and packaged in Phase 14.
