# 07 — Local Data Model

## Storage model

Use SQLite for metadata and ordinary filesystem directories for large assets.

## Core entities

### Project

- id
- name
- created_at
- updated_at
- optional notes
- ui_language (`en` or `ko`, stored in application settings rather than per-model metadata)

### Capture

- id
- project_id
- video_relative_path
- thumbnail_relative_path
- duration_ms
- width
- height
- fps
- created_at

### ModelAttempt

- id
- capture_id
- sequence_number
- status
- quality_mode
- provider
- provider_version
- parameters_json
- started_at
- finished_at
- failure_code
- failure_message

### AttemptArtifact

- attempt_id
- kind
- relative_path
- sha256 when useful
- metadata_json

Kinds may include selected frame, mask, normalized input, raw mesh, textured mesh, final GLB, validation report, and log excerpt.

For multi-view attempts, retain each selected view, isolated RGBA image, alpha mask, chronological label, source-frame index, and timestamp as attempt provenance. Retain a temporary Shape GLB separately from the final textured GLB when texture generation is requested.

### ValidationReport

- attempt_id
- overall_status
- report_json
- created_at

### ModelReview

- attempt_id
- decision
- reason_code
- notes
- reviewed_at

### RigAttempt

- id
- model_attempt_id
- sequence_number
- status
- provider
- provider_version
- parameters_json
- started_at
- finished_at
- failure_code
- failure_message

### RigAsset

- rig_attempt_id
- rigged_glb_relative_path
- skeleton_metadata_relative_path when separately stored
- joint_count
- root_joint_name/id
- created_at

For a texture-preserving UniRig result, retain the original accepted source GLB, provider FBX/intermediate artifacts as local attempt evidence when needed, the merged rigged GLB, and merge-stage log separately. The original static asset is never overwritten.

### RigValidationReport

- rig_attempt_id
- overall_status
- report_json
- created_at

### PoseDocument

- id
- rig_attempt_id
- name
- pose_json_relative_path or normalized JSON payload
- created_at
- updated_at

### AnimationClip

- id
- rig_attempt_id
- name
- from_pose_id when using two-pose mode
- to_pose_id when using two-pose mode
- duration_ms
- fps
- easing
- loop_preview
- animation_json_relative_path or normalized JSON payload
- created_at
- updated_at

## Filesystem

Recommended project directory:

```text
Projects/<project-id>/
  project.json
  captures/<capture-id>/
    capture.mp4
    thumbnail.jpg
  attempts/<attempt-id>/
    inputs/
    masks/
    mesh.glb
    model.glb
    validation.json
    attempt.json
    rigs/<rig-attempt-id>/
      rigged.glb
      rig-validation.json
      rig-attempt.json
      poses/
        <pose-id>.json
      animations/
        <clip-id>.json
```

SQLite may be global app metadata while project folders contain durable project assets.

## Pose serialization rules

- local bone rotations use normalized quaternions;
- quaternion component order is `[x, y, z, w]`;
- pose documents reference the rig/model revision they were authored against;
- unknown extra bones should be preserved where possible;
- missing bones fall back to bind-pose transforms when loading a compatible pose.

## Migration policy

Schema migrations are only for future versions of this new Python application. There is no migration path from the discarded legacy backend database.
