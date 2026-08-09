# 14 — Security and Privacy

## Local-first rule

Captured video, extracted frames and generated models remain local by default.

No telemetry, cloud upload or remote API is assumed.

## User disclosure

The UI should clearly state when a selected provider would require downloading model weights. Future online providers must require an explicit spec change and user-visible disclosure.

## Logs

Do not log raw image bytes or full video contents.

Log paths and metadata only where required for diagnostics.

## Project deletion

Deletion must distinguish:

- removing a project from the recent list;
- deleting project files from disk.

Destructive deletion requires confirmation.

## Model weights

Store downloaded weights in a dedicated cache location. Verify source/checksum when the provider distribution supports it.

The local segmentation model follows the same rule. Its explicit download command writes to the configured `U2NET_HOME`
cache; reconstruction must not initiate a model download. Isolated RGBA frames and alpha masks are local project artifacts
and receive the same handling as the source capture.

## Arbitrary files

Treat imported GLB/video files as untrusted input. Parse in background tasks, validate file type/size, and surface parser failures rather than crashing the UI.
