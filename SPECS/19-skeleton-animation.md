# 19 — Skeleton Pose and Animation

## Goal

Allow a user to manipulate a valid rigged character directly in the Python desktop application, store poses, and preview skeletal animation without requiring Blender or a browser runtime.

## Entry conditions

Animation editing is available when:

- rig validation passes or contains only explicitly allowed warnings;
- skeleton hierarchy is loadable;
- skinning data is usable for mesh deformation.

Local AI auto-rigging is not required if the user opens an already compatible rigged GLB.

## Viewer/editor baseline

Use the embedded PySide6 + PyVista/VTK viewer architecture.

Required visual aids:

- skeleton overlay;
- selected-bone highlight;
- joint markers;
- local-axis or rotation gizmo;
- optional bone hierarchy tree/search;
- bind-pose reset.

## Bone rotation mode

Baseline editing is FK/local bone rotation.

Required behavior:

- select a bone from the skeleton or hierarchy;
- rotate it in local coordinates;
- update descendants correctly;
- update skinned mesh deformation;
- apply joint limits when metadata exists;
- do not store an undo entry for every intermediate drag frame.

IK, foot lock, mirror pose and advanced DCC features are later candidates unless explicitly promoted.

## Pose model

Minimum pose schema concept:

```json
{
  "schemaVersion": 1,
  "rigRevision": "uuid-or-hash",
  "root": {
    "position": [0, 0, 0],
    "rotation": [0, 0, 0, 1],
    "scale": [1, 1, 1]
  },
  "bones": {
    "bone-id": [0, 0, 0, 1]
  }
}
```

Rules:

- quaternion component order is `[x, y, z, w]` project-wide;
- bone rotations are stored in local space;
- quaternions are normalized before storage;
- pose must reference a compatible rig revision;
- missing compatible bones fall back to bind pose;
- unknown extra bones should be preserved where feasible.

## Pose actions

Required baseline:

- Save From Pose;
- Save To Pose;
- Reset current pose to bind pose;
- Swap From/To;
- Duplicate pose;
- rename saved pose;
- reload saved pose.

## Animation model

The first maximum-scope animation workflow is two-pose interpolation, while the internal schema should permit future multi-keyframe expansion.

Minimum animation concept:

```json
{
  "schemaVersion": 1,
  "rigRevision": "uuid-or-hash",
  "fromPoseId": "uuid",
  "toPoseId": "uuid",
  "durationMs": 2000,
  "fps": 30,
  "easing": "easeInOutCubic",
  "rootMotion": false,
  "loopPreview": true
}
```

## Interpolation

Required:

- bone rotation: quaternion SLERP or an equivalently correct shortest-path quaternion interpolation;
- root position: linear or selected cubic easing;
- scale: linear interpolation unless a future spec changes it;
- selected easing applies to normalized animation progress;
- plain Euler-angle linear interpolation is forbidden.

## Playback controls

Required:

- play;
- pause;
- resume;
- stop/reset;
- seek/scrub;
- loop toggle;
- duration control;
- current-time display.

Target smoothness:

- aim for 60 FPS on ordinary reviewed assets;
- 30 FPS minimum target for acceptable preview;
- measure before adding complexity.

## Skinning/deformation

Initial preview may use correct CPU linear blend skinning if performance is acceptable.

If profiling proves CPU deformation inadequate:

- implement GPU skinning inside the existing Python/VTK rendering path;
- do not add a browser/Three.js renderer solely for animation.

## Undo/redo

Use command or snapshot history.

- one drag action should produce one meaningful history entry;
- cap history size;
- pose load/reset/swap should be undoable where practical.

## Persistence

Animation state must survive application restart.

Persist:

- rig revision;
- pose documents;
- animation clips;
- duration/FPS/easing;
- loop/root-motion flags;
- optional editor state that is useful to reopen the work.

## Current non-goals

Not required by the current maximum target:

- AI motion generation;
- IK authoring;
- motion capture retargeting;
- Blender runtime;
- final MP4 rendering/export.
