# Character Model Studio — Python Greenfield Harness

This repository specification defines a **greenfield Windows-only Python desktop application** for capturing a visible character, reconstructing a 3D model locally with GPU-accelerated AI, validating and reviewing the result, automatically rigging supported meshes, and authoring/previewing skeletal animation in the same application.

## Critical reset decision

The previous C# desktop + Python backend architecture is obsolete and must not be migrated.

- Do not port C# code.
- Do not preserve FastAPI endpoints.
- Do not create a frontend/backend split.
- Do not create an HTTP server, REST API, Redis queue, Celery worker, PostgreSQL service, MinIO service, or Docker-based runtime architecture.
- Start implementation from an empty application source tree.

## Product shape

The product is one Windows desktop application written in Python.

```text
User
  ↓
Python Desktop App
  ├─ PySide6 UI
  ├─ Windows screen-region capture
  ├─ local task orchestration
  ├─ local video/frame preprocessing
  ├─ Standard AI reconstruction — Hunyuan3D 2.0
  ├─ optional High Quality reconstruction — Hunyuan3D 2.1
  ├─ static GLB validation
  ├─ embedded 3D viewer
  ├─ auto-rigging provider
  ├─ skeleton/skinning validation
  ├─ pose + skeletal animation editor
  └─ local SQLite + project files
```

There is no network boundary between UI and AI processing. Modules communicate by Python calls and Qt signals.

## Reconstruction quality modes

### Standard — default

- Hunyuan3D 2.0.
- Lower VRAM target.
- Official upstream reference: ~6 GB Shape, ~16 GB Shape + Texture total.

### High Quality — optional

- Hunyuan3D 2.1.
- Enabled only when runtime/provider/GPU checks pass.
- Official upstream reference: ~10 GB Shape, ~21 GB Texture, ~29 GB documented combined Shape + Texture.

## Reconstruction MVP milestone

1. Launch the Windows app.
2. Create or open a project.
3. Press `Alt + /` to select a screen region.
4. Record useful views of the character.
5. Review the capture and start reconstruction.
6. Extract/select representative frames locally.
7. Run Standard or eligible High Quality reconstruction on NVIDIA CUDA.
8. Produce a GLB asset.
9. Run technical model validation.
10. Review the model in the embedded 3D viewer.
11. `Accept`, `Reject`, or `Regenerate`.

## Maximum product target

The project continues beyond the reconstruction MVP:

1. Automatically generate a skeleton and skinning weights when a supported rigging provider is available.
2. Validate the rig independently from static mesh validity.
3. Display skeleton/bones over the model.
4. Select and rotate bones in local space.
5. Save/reset/swap From Pose and To Pose.
6. Preview skeletal animation using quaternion interpolation.
7. Play/pause/seek/loop animation.
8. Persist and reopen rig, pose, and animation state.

Animated MP4 rendering/export and mandatory Blender integration are not part of the current maximum target unless explicitly added later.

## UI direction

The application must use a **warm, high-visibility glassmorphism design**. It must not look like a generic AI-generated dashboard.

See:

- `SPECS/08-desktop-ux.md`
- `SPECS/09-ui-design-system.md`
- `SPECS/10-ui-motion.md`

## Read order for coding agents

1. `AGENTS.md`
2. `DEPENDENCIES.md`
3. relevant `SPECS/*.md`
4. current file in `PHASES/`
5. `HARNESS.md`
6. this `README.md`

## Current implementation state

`GREENFIELD / NOT_STARTED`

No legacy application code is authoritative.
