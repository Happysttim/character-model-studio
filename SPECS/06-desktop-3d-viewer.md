# 06 — Embedded Desktop 3D Viewer

## Purpose

Static and rigged models must be inspectable without opening Blender or a browser.

## Baseline stack

- PyVista;
- VTK;
- `pyvistaqt.QtInteractor` embedded in the PySide6 application;
- trimesh for independent GLB inspection/normalization;
- pygltflib or equivalent for glTF skins/joints/animation structure where needed.

## Required static interaction

- orbit;
- pan;
- zoom;
- fit model;
- reset camera;
- front/back/left/right/top views;
- three-quarter preset;
- turntable mode;
- solid mode;
- wireframe mode;
- grid toggle;
- axes toggle;
- bounding-box toggle;
- neutral/studio-light background treatment compatible with the app theme.

## Review layout

The reconstruction review screen must combine:

- large 3D viewport;
- source reference frame strip or comparison pane;
- validation summary;
- attempt metadata including Standard/High Quality mode;
- Accept / Reject / Regenerate actions.

The 3D viewport should be visually dominant but not consume the entire screen at the expense of review controls.

Large generated textured meshes may receive a technical `PASS_WITH_WARNINGS` when optional viewer conversion exceeds a bounded validation-memory budget. The review UI must show that diagnostic clearly and still permit the user to inspect the source GLB when the core asset checks passed.

## Review actions

### Accept

Marks this reconstruction attempt as an accepted source model for later rigging/animation.

### Reject

Requires or strongly encourages a short reason category, for example:

- geometry distortion;
- missing body part;
- bad back/side reconstruction;
- texture issue;
- wrong proportions;
- other.

### Regenerate

Creates a new reconstruction attempt using the same capture, with optional parameter/quality changes. Prior attempts remain accessible.

## Rigged-model viewer extensions

When a valid rig is present, the same embedded viewer architecture must support:

- skeleton overlay;
- show/hide bones;
- joint markers;
- selected-bone highlight;
- parent/child context;
- local rotation gizmo or equivalent manipulation control;
- bind-pose reset;
- skinned-mesh deformation preview.

The viewer must not infer rig validity merely because the skeleton can be drawn.

## Character animation scope

Turntable camera motion remains available, but it is separate from skeletal character animation.

Maximum-scope skeletal animation is defined in `SPECS/19-skeleton-animation.md`.
