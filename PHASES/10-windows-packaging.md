# Phase 10 — Windows Packaging

## Goal

Create a distributable Windows build and prove it outside the development environment.

## Tasks

- PyInstaller one-folder build baseline;
- collect Qt plugins;
- collect VTK/PyVista runtime dependencies;
- define AI provider/model-cache discovery;
- package explicit local model-download guidance: required segmentation plus optional Standard, SF3D, and Hunyuan3D-2GP Shape/Texture caches;
- verify the app-owned local Python child-process Texture lane when Hunyuan3D-2GP is configured;
- keep model weights separate when practical;
- clean-account launch smoke test;
- GPU provider smoke test from packaged app;
- verify logs/config/projects use user-writable directories;
- document antivirus/signing issues if encountered.

## Acceptance criteria

- packaged app launches without Python installed system-wide;
- core UI/viewer works;
- target GPU can run configured reconstruction provider from packaged environment or exact distribution blocker is documented;
- no backend process or local server needs manual startup.

## Completion evidence

Record commands run, tests passed, manual checks performed, and any environment blockers. A phase is not complete from code generation alone.
