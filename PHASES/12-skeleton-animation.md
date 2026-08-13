# Phase 12 — Skeleton Pose and Animation

## Goal

Allow users to manipulate bones, store poses, and preview skeletal animation in the embedded Python viewer.

## Tasks

- skeleton overlay/hierarchy interaction;
- selected-bone local rotation editing;
- glTF accessor decoding, hierarchical local/world transform composition, CPU linear blend skinning, and VTK point updates for pose preview;
- bind-pose reset;
- correct skinned-mesh deformation;
- pose serialization using normalized `[x, y, z, w]` quaternions;
- From Pose / To Pose save/load;
- reset/swap/duplicate pose;
- quaternion SLERP/shortest-path interpolation;
- duration/easing controls;
- play/pause/resume/seek/stop/loop;
- persistence/reopen;
- undo/redo at meaningful edit granularity;
- performance profiling with representative rigs.

## Acceptance criteria

- a fixture and a generated valid rig can be posed;
- parent/child transforms and mesh deformation are correct;
- From/To animation previews without UI freeze;
- Euler linear interpolation is not used for bone rotations;
- saved animation reopens with equivalent pose/clip state;
- 30 FPS minimum preview target is met on representative assets or a documented performance blocker exists.

## Current technical decision

The initial renderer path is verified CPU LBS: it reads `POSITION`, `JOINTS_0`, `WEIGHTS_0`, and inverse-bind matrices from the opened GLB and applies normalized local quaternion poses through parent/child transforms. GPU skinning is a later optimization only if profiling establishes that CPU LBS misses the target.
