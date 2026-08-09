# 00 — Product

## Product name

Character Model Studio

## Product goal

Enable a Windows user to record a visible character, reconstruct a 3D asset locally with AI, technically validate and review the model, automatically rig supported results, and create/preview skeletal pose animation in the same desktop application.

## Primary value

The user should not need to understand AI runtimes, model servers, storage servers, rigging command-line tools, or external 3D conversion pipelines.

The maximum product workflow is:

`Capture → Reconstruct → Validate → Review → Rig → Validate Rig → Pose/Animate → Save`

## Primary user story

As a user, I can select the region containing a character, record useful views, generate a GLB locally with my GPU, inspect it, optionally texture it, automatically create a usable skeleton and skinning weights when my GPU/provider supports it, manipulate bones, preview skeletal animation, and keep or regenerate earlier reconstruction attempts.

## Reconstruction quality modes

### Standard

- Default: Hunyuan3D 2.0.
- Consumer-GPU-oriented path.

### High Quality

- Optional: Hunyuan3D 2.1.
- Must be gated by runtime compatibility and GPU capability.

The selected quality mode and provider must be explicit and persisted per attempt.

## Functional continuity

Keep:

- global capture hotkey;
- region selector;
- recording state/elapsed time;
- local capture review;
- frame extraction and quality selection;
- AI reconstruction;
- GLB output;
- technical validation;
- 3D orbit/pan/zoom viewer;
- standard camera views;
- wireframe/solid inspection;
- grid, axis and bounding-box aids;
- source-vs-result review;
- Accept / Reject / Regenerate;
- attempt history and local project persistence.

Maximum target also includes:

- automatic skeleton generation;
- automatic skinning weights;
- rigged GLB persistence;
- skeleton overlay/review;
- bone selection/local rotation;
- From Pose / To Pose;
- pose reset/swap/duplicate;
- skeletal animation preview;
- play/pause/seek/loop;
- animation persistence/reopen.

Change from the discarded architecture:

- one Python application instead of C# + backend;
- no server boundary;
- no HTTP upload;
- no remote queue;
- no object-storage service;
- no server database.

## Milestones

### Reconstruction MVP

`Capture → Generate → Validate → Review → Accept/Reject/Regenerate`

### Maximum scope

`Reconstruction MVP → Auto Rigging → Rig Validation → Pose → Skeletal Animation`

## Current exclusions

Unless explicitly added later:

- mandatory Blender runtime;
- headless server rendering;
- animated MP4 export pipeline;
- cloud sync;
- accounts/authentication;
- multi-user collaboration.
