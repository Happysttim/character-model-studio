# Phase 14 — Windows Packaging

## Goal

Create a distributable Windows build and prove both reconstruction-MVP and maximum-scope editor features outside the development environment.

## Tasks

- PyInstaller one-folder build baseline;
- collect Qt plugins;
- collect VTK/PyVista runtime dependencies;
- collect glTF/animation parser dependencies;
- define AI provider/model-cache discovery;
- verify required segmentation setup and explicit optional model-cache selection without hardcoded user paths;
- collect or document Hunyuan3D-2GP native extensions and its app-owned local Python child-process Texture lane when configured;
- collect or document the optional UniRig external checkout, isolated runtime, local checkpoints, and stage-specific native wheel cache;
- keep model weights separate when practical;
- clean-account launch smoke test;
- Standard provider discovery/smoke test from packaged app on an eligible machine;
- High Quality provider discovery/gating verification;
- rigging provider discovery/gating verification;
- fixture rig/skeleton/animation playback test without requiring AI weights;
- package a Windows VTK shutdown smoke proving Qt-owned interactor cleanup does not emit `wglMakeCurrent` errors;
- verify logs/config/projects use user-writable directories;
- document antivirus/signing/native-extension issues if encountered.

## Acceptance criteria

- packaged app launches without Python installed system-wide;
- core UI/viewer works;
- Standard provider runs on a compatible packaged target or the exact distribution blocker is documented;
- optional High Quality status is truthful;
- optional SF3D and Hunyuan3D-2GP readiness is truthful and their absent weights do not block launch;
- rigging capability status is truthful;
- fixture skeleton/pose/animation editing works;
- no backend process or local server needs manual startup.

## Current technical decision

Optional provider weights and isolated provider runtimes remain outside the main package and are resolved from configured local cache paths. The packaged desktop application must retain all non-AI review, rigged-GLB, pose, animation, project, and language-selection features when optional AI weights are absent.
