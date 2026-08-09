# 02 — Application Lifecycle and Local Workflow

## Startup

On startup the app must:

1. configure logging;
2. resolve local application data paths;
3. open/migrate the local SQLite schema;
4. detect Windows version/DPI environment;
5. probe capture capability;
6. probe NVIDIA/PyTorch CUDA capability without loading full model weights;
7. derive provider/capability readiness for Standard, High Quality and auto-rigging;
8. restore last project/window state where safe;
9. show the main window quickly.

Full AI model loading must not block first paint.

## Project flow

A project contains captures, reconstruction attempts, optional rigs, and animation documents.

```text
Project
  ├─ Capture A
  │   ├─ Attempt 1 — rejected
  │   └─ Attempt 2 — accepted
  │       └─ Rig Attempt 1 — accepted
  │           ├─ Pose: From
  │           ├─ Pose: To
  │           └─ Animation Clip 1
  └─ Capture B
      └─ Attempt 1 — pending
```

## Reconstruction attempt state machine

Recommended states:

```text
CREATED
→ PREPROCESSING
→ RECONSTRUCTING
→ TEXTURING (optional)
→ VALIDATING_MODEL
→ READY_FOR_REVIEW
→ ACCEPTED | REJECTED
```

Failure/cancellation states:

```text
FAILED
CANCELLED
```

Regeneration creates a new reconstruction attempt. It does not overwrite prior attempts.

## Rigging state machine

Rigging is a separate attempt linked to a valid model attempt:

```text
CREATED
→ LOADING_RIG_PROVIDER
→ RIGGING
→ VALIDATING_RIG
→ READY_FOR_RIG_REVIEW
→ ACCEPTED | REJECTED
```

Failure/cancellation states:

```text
FAILED
CANCELLED
```

A rejected rig does not invalidate the underlying accepted static model.

## Animation document lifecycle

A valid rig can create animation state without further AI inference:

```text
RIG_READY
→ EDITING_POSE
→ PREVIEWING_ANIMATION
→ SAVED
```

Animation data must remain independently editable after application restart.

## Progress

Each long task must emit structured progress:

- stage identifier;
- human label;
- percent when measurable;
- current item/total when meaningful;
- cancellable flag;
- elapsed time;
- optional GPU memory status.

Do not fabricate fake smooth progress percentages for indeterminate model stages. Use indeterminate progress with truthful stage labels instead.
