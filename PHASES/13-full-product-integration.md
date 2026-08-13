# Phase 13 — Maximum-Scope Product Integration

## Goal

Connect the complete local workflow from capture through skeletal animation.

## Scenario

```text
capture
→ preprocess
→ Standard/High Quality reconstruction
→ optional texture
→ static validation/review
→ auto-rig
→ rig validation/review
→ pose editing
→ skeletal animation preview
→ save/reopen
```

## Tasks

- reconcile cross-stage state transitions;
- verify provider unload/reload behavior between heavyweight CUDA stages;
- verify Hunyuan3D-2GP Texture and UniRig stages use their application-owned child processes without freezing the parent Qt process;
- verify a new/imported GLB invalidates stale Rig and Animate viewport state before the next asset is loaded;
- verify the persisted language setting changes all registered workspace labels between Korean and English;
- verify Windows viewer shutdown does not emit late VTK `wglMakeCurrent` cleanup diagnostics;
- verify Standard Full path on an eligible 16GB+ reference environment when available;
- verify High Quality path only on an eligible/runtime-compatible environment;
- test capability-gated skipping on lower-VRAM machines;
- verify project reopen preserves static model, rig, poses and animation;
- polish progress/error/recovery UX across all stages;
- final warm-glass visual consistency review;
- final UI-thread responsiveness profiling.

## Acceptance criteria

- highest supported path runs end-to-end without server components;
- intentionally unsupported stages are clearly gated rather than failing late;
- accepted static assets survive rigging failures;
- accepted rigs/animation survive later reconstruction attempts;
- provider and VRAM telemetry are truthful;
- project can be closed/reopened with maximum-scope state intact.

## Current technical decision

The maximum-scope workflow uses explicit local process boundaries only for upstream runtime isolation. Reconstruction, texture, rigging, validation, pose/animation persistence, and UI navigation remain application-owned local desktop stages with no HTTP/RPC service.
