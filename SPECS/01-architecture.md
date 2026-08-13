# 01 — Architecture

## Architecture style

Modular monolithic desktop application.

All primary modules are owned by one Python desktop application and communicate through Python interfaces and Qt signals.

```text
┌──────────────────────────────────────────────────┐
│              Character Model Studio              │
│                                                  │
│  UI / Navigation / View Models                   │
│            │                                     │
│            ▼                                     │
│  Application Orchestrator                        │
│   ├─ Capture Controller                          │
│   ├─ Reconstruction Controller                   │
│   ├─ Review Controller                           │
│   ├─ Rigging Controller                          │
│   ├─ Animation Controller                        │
│   └─ Background Task Lanes                       │
│            │                                     │
│   ┌────────┼──────────┬───────────┬─────────┐     │
│   ▼        ▼          ▼           ▼         ▼     │
│ Capture  Preprocess  Reconstruct  Rigging  Validate│
│   │                    │           │               │
│ DXcam/OpenCV        PyTorch CUDA  PyTorch CUDA    │
│                        │           │               │
│                        ▼           ▼               │
│                    GLB Mesh    Rigged GLB          │
│                        │           │               │
│                  ┌─────┴───────────┴──────┐        │
│                  ▼                        ▼        │
│             Local Storage       Embedded 3D/Anim  │
│             SQLite/files        PyVista/VTK       │
└──────────────────────────────────────────────────┘
```

## No frontend/backend boundary

Do not use localhost networking as an internal architecture technique.

Bad:

`PySide6 → HTTP → FastAPI → queue → worker`

Required:

`PySide6 → controller method → background task → provider → result signal`

## Module boundaries

Recommended source layout:

```text
src/character_model_studio/
  app/
    bootstrap.py
    services.py
    orchestration.py
    capabilities.py
  domain/
    models.py
    states.py
    errors.py
  ui/
    main_window.py
    navigation.py
    theme.py
    widgets/
    views/
  capture/
    controller.py
    region_selector.py
    dxcam_source.py
    encoder.py
  preprocess/
    frames.py
    scoring.py
    segmentation.py
  reconstruction/
    interfaces.py
    runner.py
    providers/
      hunyuan2.py
      hunyuan21.py
  rigging/
    interfaces.py
    runner.py
    validation.py
    providers/
      skintokens.py
      instance_rig.py
  animation/
    skeleton.py
    skinning.py
    pose.py
    clip.py
    interpolation.py
  validation/
    glb_validator.py
    rig_validator.py
    report.py
  viewer/
    widget.py
    scene.py
    cameras.py
    skeleton_overlay.py
    gizmos.py
  storage/
    database.py
    repositories.py
    project_files.py
  platform/windows/
    hotkeys.py
    dpi.py
    dwm.py
    paths.py
  common/
    logging.py
    cancellation.py
    ids.py
```

## Background work

Use one application-owned task orchestration layer.

- UI thread: UI only.
- capture lane: capture and encoding.
- preprocessing pool: CPU-bound frame work where safe.
- reconstruction lane: one heavyweight reconstruction/texture provider operation at a time by default.
- rigging lane: one heavyweight rigging provider operation at a time by default.
- validation lane: background CPU work.
- animation playback: UI/render timing path only; never block on AI inference.

Heavy CUDA providers should be loaded/unloaded sequentially so consumer GPUs do not need reconstruction, texture, and rigging models resident simultaneously.

If an upstream Texture/UV implementation still harms GUI responsiveness inside a Qt worker thread, isolate that one stage in an application-owned local Python child process. The parent app owns launch, cancellation, logs, result validation, and lifecycle; this is not a backend service.

## Provider abstraction

The UI depends on application-facing interfaces, not model libraries.

Required abstractions include:

- `ReconstructionProvider`;
- optional independent `TextureProvider` behavior;
- `RiggingProvider`;
- `SegmentationProvider`;
- capability/readiness services.

Default policy:

- Standard reconstruction: Hunyuan3D 2.0.
- High Quality reconstruction: Hunyuan3D 2.1.
- Experimental multi-view textured reconstruction: Hunyuan3D-2GP.
- Auto rigging reference: SkinTokens/TokenRig.

## Local persistence

- SQLite stores metadata/state.
- Binary assets live in project folders.
- Database stores relative paths, hashes and metadata; not multi-GB blobs.
