# Phase 00 — Environment Validation

## Goal

Prove that the chosen Windows/Python/GPU/3D/provider stack can coexist before implementation grows around it.

## Tasks

- Verify Windows 11 x64 target machine.
- Verify preferred Python 3.11 environment.
- Install/import PySide6 and instantiate a Qt Widgets window.
- Install/import DXcam and capture a test frame.
- Install/import PyVista, VTK, pyvistaqt and open a simple embedded scene.
- Install/import trimesh and load a sample GLB.
- Install/import the chosen glTF rig/animation parser and inspect a fixture rigged GLB.
- Verify PyTorch CUDA tensor execution.
- Document GPU model, driver, total VRAM and current free VRAM.
- Classify the product VRAM tier from `SPECS/11-gpu-runtime.md`.
- Test the Hunyuan3D 2.0 Standard compatibility lane or record the exact blocker.
- Probe Hunyuan3D 2.1 High Quality compatibility separately; it is optional and must not block the Standard lane unless shared dependencies conflict.
- Test the selected auto-rigging provider compatibility lane, with SkinTokens/TokenRig as the default reference.
- Verify that PySide6/VTK still work in the same project runtime after provider dependencies are installed.
- Verify packaging feasibility of a minimal PySide6 app separately from AI weights.

## Acceptance criteria

- Core desktop stack works natively on Windows.
- No WSL/server is required for app startup.
- CUDA smoke test passes on the target GPU or phase status is explicitly `BLOCKED_BY_ENVIRONMENT`.
- Hunyuan3D 2.0 Standard compatibility result is recorded.
- Rigging-provider compatibility result is recorded.
- High Quality 2.1 is marked `AVAILABLE`, `UNAVAILABLE_BY_GPU`, or `PROVIDER_RUNTIME_INCOMPATIBLE`; it is not assumed.
- Compatibility versions are recorded before Phase 01 pins them.

## Completion evidence

Record commands run, tests passed, manual checks performed, provider compatibility matrix, detected capability tier, and any environment blockers.
