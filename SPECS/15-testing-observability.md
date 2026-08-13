# 15 — Testing and Observability

## Logs

Use structured, human-readable local logs with rotating files.

Every reconstruction/rigging operation should include a correlation/attempt ID.

## Diagnostics view

Provide a lightweight diagnostics screen showing:

- app version;
- Python version;
- Windows version;
- PySide6/Qt version;
- GPU name;
- total VRAM;
- currently free VRAM;
- detected product VRAM tier;
- PyTorch version;
- CUDA availability/runtime reported by PyTorch;
- Standard provider/version/readiness;
- Segmentation provider/model/readiness and CUDA execution-provider status;
- High Quality provider/version/readiness;
- rigging provider/version/readiness;
- storage paths;
- log directory action.

## Metrics per AI attempt

Record:

- stage durations;
- number of candidate/selected frames;
- quality mode;
- provider/version;
- model load time;
- inference duration;
- total/free/peak VRAM when available;
- output file size;
- validation status.
- child-process exit status and final output existence when a provider uses local process isolation.

For rigging attempts also record:

- joint count;
- provider runtime;
- rig validation status.

These are diagnostics, not decorative dashboard KPIs.

## Animation diagnostics

Record only useful technical information such as:

- rig revision;
- pose/clip IDs;
- duration;
- playback FPS estimate when profiling;
- deformation errors/warnings.

Do not spam per-frame logs during normal playback.

## Crash/failure recovery

At startup, attempts left in transient states from an abnormal exit must be reconciled to an interrupted/failed state with preserved completed artifacts.

Saved poses/animations linked to an accepted rig must not be deleted because a later regeneration attempt fails.

## Test pyramid

- unit: domain, scoring, validation, skeleton/animation math;
- Qt tests: navigation/state, region selector, rig/animation controls;
- integration: local workflow with mock providers;
- Windows manual/automation: capture and DPI;
- GPU smoke: real Standard reconstruction, optional High Quality, rigging provider readiness;
- experimental multi-view GPU smoke: CUDA Shape plus CUDA Texture with a textured GLB assertion before enabling Hunyuan3D-2GP;
- packaging smoke: clean machine/account launch and fixture rig/animation editing.
