# 17 — Roadmap and Open Questions

## Reconstruction MVP milestone

The Reconstruction MVP has been manually exercised with local capture/import, CUDA segmentation, reconstruction, GLB validation, and review. Future changes must preserve this local-only flow while keeping optional provider readiness truthful.

- Python Windows desktop shell;
- warm glassmorphism design system;
- local projects/captures;
- global region capture;
- reconstruction attempt orchestration;
- Hunyuan3D 2.0 Standard CUDA provider;
- optional Hunyuan3D 2.1 High Quality provider when compatible;
- GLB validation;
- embedded 3D review;
- Accept/Reject/Regenerate.

## Maximum current target

After the reconstruction MVP:

- automatic skeleton generation through the configured UniRig isolated lane;
- automatic skinning weights;
- rigged GLB persistence;
- rig validation;
- skeleton/bone review;
- local bone rotation editing;
- From Pose / To Pose;
- pose reset/swap/duplicate;
- quaternion-interpolated skeletal animation;
- play/pause/seek/loop;
- animation persistence/reopen;
- final Windows packaging smoke test.

## Later candidates

Only add through explicit specification updates:

- configurable segmentation providers beyond the baseline;
- additional reconstruction models;
- batch capture processing;
- model repair tools;
- topology simplification controls;
- texture editing;
- manual skin-weight painting;
- IK target editing;
- foot lock;
- mirror pose;
- pose preset libraries;
- AI motion generation;
- animated MP4 rendering/export;
- optional Blender export helper;
- optional cloud provider.

## Open questions to resolve during implementation

1. Whether a future SkinTokens/TokenRig implementation can coexist with the project runtime; UniRig deliberately uses an isolated local runtime instead of requiring one shared AI environment.
2. Whether Hunyuan3D 2.1 can be supported reliably inside the same Python 3.11 application runtime; if not, High Quality remains unavailable until the user approves an architecture change.
3. Exact provider commit/checkpoint proven on the target GPU fleet.
4. Whether UniRig's provider-specific 8 GiB smoke evidence remains reliable across supported GPU families and complex textured source assets.
5. Final H.264 encoder path across NVIDIA/Intel/AMD capture machines.
6. Whether Windows 10 remains a shipping target or best-effort fallback.
7. Final installer/signing approach.
8. Whether CPU LBS remains responsive for the largest supported rigged assets or GPU skinning is required for animation preview.

These questions must not be answered by reintroducing a server architecture without explicit user approval.
