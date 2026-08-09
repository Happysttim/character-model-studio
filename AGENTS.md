# AGENTS.md

## 1. Authority order

When instructions conflict, follow this order:

1. Current explicit user instruction.
2. This `AGENTS.md`.
3. The relevant file under `SPECS/`.
4. The active phase under `PHASES/`.
5. `HARNESS.md`.
6. `README.md`.
7. Existing implementation code.

Existing code has the lowest authority because this is a greenfield project.

## 2. Non-negotiable architecture

This product is a **single Windows desktop application written in Python**.

### Required

- Application code: Python.
- Desktop UI: PySide6 / Qt Widgets authored from Python.
- Local persistence: SQLite + project folders.
- Local background execution: Qt threads / thread pools and Python task objects.
- AI inference: local NVIDIA CUDA through PyTorch-compatible providers.
- 3D inspection, rigging review, pose editing and skeletal animation: embedded in the same desktop app.

### Forbidden

Do not introduce any of the following unless the user explicitly changes the specification:

- C# application code.
- JavaScript or TypeScript application code.
- QML application files.
- React, Next.js, Electron, Tauri, browser-based UI.
- FastAPI, Flask, Django, aiohttp or another local HTTP server.
- REST, GraphQL, WebSocket or RPC boundaries inside the app.
- Redis, Celery, Dramatiq, RabbitMQ, Kafka.
- PostgreSQL, MySQL, MongoDB server dependencies.
- MinIO or another object-storage service.
- Docker as a runtime requirement.
- Microservices.
- Separate frontend/backend repositories.
- A background Windows service or daemon.

Native runtime libraries used by Python packages are allowed. The application itself remains Python.

## 3. Greenfield rule

The previous project is intentionally discarded.

Do not:

- migrate legacy database schemas;
- preserve legacy API contracts;
- recreate old service boundaries;
- copy the old C# MVVM layout;
- keep obsolete web/server implementations merely for compatibility.

Rigging and skeletal animation are **not legacy exclusions**. They are part of the new project's maximum target and must be implemented only according to the new Python specifications.

## 4. Supported platform

- Windows 11 is the primary target.
- Windows 10 may be supported where feasible, with visual fallback for DWM backdrop effects.
- x64 is the primary architecture.
- NVIDIA GPU with CUDA is required for local AI reconstruction and AI auto-rigging providers.
- Non-AI editing/viewing features should remain available when their required assets already exist.

## 5. Python baseline and provider compatibility

The preferred application baseline is **CPython 3.11.x** because the maximum-scope rigging provider lane requires Python 3.11+.

Provider compatibility must be proven, not assumed:

- Hunyuan3D 2.0 is the default reconstruction provider.
- Hunyuan3D 2.1 is an optional high-quality provider. Its upstream tested lane is Python 3.10 + PyTorch 2.5.1+cu124, so compatibility with the project's Python 3.11 runtime must be smoke-tested before it is enabled.
- SkinTokens / TokenRig is the default maximum-scope auto-rigging reference provider and currently requires Python 3.11+, CUDA Toolkit 12.1+, and an NVIDIA GPU with at least 14 GB VRAM for inference.
- UniRig may be implemented as an alternate rigging provider, but no product VRAM threshold may be invented for it without a reproducible local smoke test or an authoritative upstream requirement.

The application remains one local Python desktop application. Do not silently introduce a hidden HTTP backend or service to solve dependency conflicts.

If required providers cannot coexist in the selected runtime, report `PROVIDER_RUNTIME_INCOMPATIBLE` and document the exact blocker before changing architecture.

## 6. Reconstruction quality modes

The product exposes two reconstruction quality modes:

### Standard

- Default provider: **Hunyuan3D 2.0**.
- Primary goal: broad consumer-GPU compatibility.
- Official upstream reference: approximately 6 GB VRAM for Shape and 16 GB for Shape + Texture in total.

### High Quality

- Optional provider: **Hunyuan3D 2.1**.
- Must be disabled with an explanation when provider/runtime/GPU requirements are not satisfied.
- Official upstream reference: approximately 10 GB VRAM for Shape, 21 GB for Texture, and 29 GB for the documented combined Shape + Texture configuration.

Do not silently substitute 2.1 for 2.0 or vice versa. Persist the provider and quality mode used for every attempt.

## 7. UI implementation rule

Use PySide6 Qt Widgets from Python. Custom widgets, custom painting, style sheets, `QPropertyAnimation`, `QVariantAnimation`, and native DWM calls are allowed.

Do not use QML. Do not embed a webview to build the main UI.

## 8. UI visual acceptance rules

The phrase "glassmorphism" is not sufficient by itself. The implementation must follow `SPECS/09-ui-design-system.md`.

The following patterns are rejected:

- monochrome blue, monochrome purple, or black/gray-only product UI;
- neon cyberpunk treatment;
- giant gradient hero cards;
- meaningless KPI/dashboard cards;
- an icon-only left rail as the primary navigation;
- every component rendered as the same rounded rectangle;
- excessive pill buttons or tags;
- huge whitespace that reduces information density;
- generic AI-chat visual language;
- fake terminal panels used as decoration;
- randomly generated gradients behind every section;
- default Material/Fluent clone without product-specific composition;
- visual hierarchy based only on border radius and shadows.

The UI must use a warm palette, visible text contrast, layered glass surfaces, restrained accent colors, and content-first layouts.

## 9. Responsiveness and task execution

Never block the Qt UI thread with:

- video encoding;
- OpenCV frame extraction;
- AI model loading;
- CUDA inference;
- texture generation;
- auto-rigging;
- GLB/rig validation;
- large file I/O.

Use signals to report progress back to the UI.

Heavy tasks remain part of the same application and use application-owned task lanes. Do not turn a worker into a server.

By default, only one heavyweight CUDA provider may own the primary GPU at a time. Reconstruction, texture and rigging providers should be loaded/unloaded sequentially unless a tested configuration explicitly proves simultaneous residency is safe.

## 10. GPU policy

Production AI operations must not silently fall back to CPU.

If a required CUDA path is unavailable:

- disable only the affected AI capability;
- show a clear readiness reason;
- preserve project browsing, capture review, imported-model viewing and non-AI editing where possible;
- do not claim a successful GPU run.

Every real AI attempt must record:

- GPU name;
- CUDA availability;
- selected CUDA device;
- total physical VRAM;
- free VRAM at operation start;
- provider name/version;
- operation/quality mode;
- start/end timestamps;
- elapsed time;
- peak allocated/reserved VRAM where measurable;
- output path;
- success/failure reason.

## 11. AI provider abstraction

Do not spread model-specific calls through the UI.

Use interfaces similar to:

- `ReconstructionProvider`
- `TextureProvider` when texture is independently executable
- `RiggingProvider`
- `SegmentationProvider`
- `FrameSelectionStrategy`

Baseline character-isolation policy:

- Default local segmentation provider: `rembg` with the locally cached `isnet-anime` model.
- Segmentation must use ONNX Runtime `CUDAExecutionProvider`; do not silently execute it on CPU.
- Model downloads are explicit user actions. Inference resolves only the configured local cache path.
- Persist the selected source frame, isolated RGBA input, alpha mask, provider, and model identifier with the attempt.

Default/optional provider policy:

- Standard reconstruction: Hunyuan3D 2.0.
- High-quality reconstruction: Hunyuan3D 2.1.
- Default auto-rigging reference: SkinTokens / TokenRig.
- Alternate rigging provider candidate: UniRig.

The UI and project model must not need rewriting when a provider changes.

## 12. 3D, rigging and animation rules

- Canonical generated asset: GLB / glTF 2.0.
- Parsing/validation logic must be separate from rendering logic.
- A viewer successfully opening a model does not equal a validation pass.
- A valid static mesh does not imply a valid rig.
- A valid rig does not imply the character visually matches the source.
- Human review remains authoritative for visual fidelity.
- Skeleton hierarchy and skinning weights must be validated before animation editing is enabled.
- Bone rotations are stored as normalized local-space quaternions using `[x, y, z, w]` ordering.
- Skeletal rotation interpolation uses quaternion SLERP or an equivalently correct shortest-path quaternion interpolation; plain Euler linear interpolation is forbidden.

## 13. Product milestones and maximum scope

### Reconstruction MVP milestone

The first usable milestone ends at:

`Capture → Reconstruct → Validate → 3D Review → Accept/Reject/Regenerate`

### Maximum target

The project does **not** end at the Reconstruction MVP. The maximum target also includes:

- automatic skeleton generation;
- automatic skinning weights;
- rigged GLB persistence;
- skeleton overlay/review;
- bone selection and local rotation editing;
- From Pose / To Pose storage;
- pose reset/swap/duplicate;
- keyframe-capable skeletal animation state;
- quaternion interpolation;
- play/pause/seek/loop preview;
- animation persistence and reopen.

The following remain outside the current maximum target unless explicitly reintroduced:

- mandatory Blender runtime;
- server-side rendering;
- animated MP4 render/export pipeline;
- cloud sync;
- accounts/authentication;
- multi-user collaboration.

UI motion/transition animation is required and is separate from character skeletal animation.

## 14. Code quality

- Type hint public module APIs.
- Prefer dataclasses or small domain objects for stable data structures.
- Keep platform-specific Win32 code under `platform/windows/`.
- Keep reconstruction code under `reconstruction/providers/`.
- Keep rigging code under `rigging/providers/`.
- Keep skeletal animation math separate from UI widgets.
- Keep UI widgets free of AI model implementation details.
- Do not hide exceptions with `except Exception: pass`.
- User-facing failures require actionable messages and structured logs.
- Use deterministic IDs and project-relative paths where feasible.

## 15. Documentation completion rule

A phase is not complete when code merely exists. It is complete only when:

1. acceptance criteria in the phase are met;
2. required harness commands pass;
3. manual Windows checks are documented when automation cannot verify them;
4. the code still respects this architecture and UI specification.
