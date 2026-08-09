# HARNESS.md

This file defines the verification contract for coding agents.

The harness is not only a test checklist. It defines the minimum evidence required before an implementation phase may be considered complete.

Provider facts in this document were verified against upstream documentation on 2026-08-09. Re-check upstream requirements before changing provider versions or VRAM thresholds.

## Goals

The harness must prove that the application:

- is a single local Windows Python desktop application;
- does not require a frontend server, backend server, REST API, Redis, Celery, PostgreSQL, MinIO, or other service infrastructure;
- stays responsive while doing capture, preprocessing, AI inference, rigging, validation, and animation work;
- uses the required Windows-native and CUDA paths;
- can capture a character from the screen;
- can reconstruct a 3D mesh from captured visual data;
- uses Hunyuan3D 2.0 as the default Standard reconstruction provider;
- exposes Hunyuan3D 2.1 only as an optional High Quality provider when compatibility and GPU checks pass;
- can generate textures when the selected provider/capability allows it;
- can validate generated 3D assets;
- can automatically generate a skeleton and skinning weights when the selected rigging provider is supported;
- can load and review rigged models;
- can display and manipulate bones;
- can create, preview, persist, and replay skeletal pose animation;
- correctly gates functionality according to provider compatibility and GPU capability;
- follows the visual system instead of generating a generic AI dashboard.

Passing unit tests alone is not sufficient when a phase requires Windows, GPU, capture, 3D rendering, or visual verification.

---

## Canonical commands

The implementation should expose equivalent commands through scripts, a `Makefile`, `justfile`, PowerShell scripts, or `python -m tools...`.

```text
bootstrap

format
lint
typecheck

test
test-ui
test-storage
test-capture

test-ai-mock
test-provider-compatibility
test-gpu
test-reconstruction
test-rigging
test-animation

test-model-validation
test-rigged-model-validation
test-integration

build
package
verify
```

Windows-native commands may be PowerShell-first.

A command may internally compose smaller commands, but the canonical behavior above must remain available.

---

## Minimum tool expectations

Recommended development tools:

- `uv` for environment and lockfile management;
- `ruff` for formatting and linting;
- `mypy` or `pyright` for type checks;
- `pytest`;
- `pytest-qt` for Qt behavior tests;
- `pytest-cov`;
- `trimesh` for mesh and GLB inspection;
- `pygltflib` or an equivalent tested glTF structural layer for skins/animations;
- NumPy plus tested quaternion utilities for skeletal math;
- PyTorch with CUDA for AI workloads;
- packaging with `PyInstaller` initially unless the packaging phase demonstrates a more compatible alternative.

Do not introduce Docker as a runtime dependency for the desktop application.

Do not create a local HTTP server merely to separate application modules or AI providers.

---

## Python runtime and provider compatibility policy

The preferred project runtime is **CPython 3.11.x** because the maximum-scope auto-rigging lane requires Python 3.11+.

The harness must verify actual provider compatibility instead of assuming that one Python/PyTorch/CUDA combination works for every provider.

Reference provider constraints:

- Hunyuan3D 2.0: default Standard provider; official README reports Windows support, ~6 GB Shape, ~16 GB Shape + Texture total.
- Hunyuan3D 2.1: optional High Quality provider; upstream tested with Python 3.10 + PyTorch 2.5.1+cu124 and reports ~10 GB Shape, ~21 GB Texture, ~29 GB combined Shape + Texture.
- SkinTokens / TokenRig: default maximum-scope auto-rigging reference; upstream requires Python >= 3.11, CUDA Toolkit >= 12.1, and at least 14 GB NVIDIA GPU memory for inference.
- UniRig: allowed alternate rigging provider; upstream documents Python 3.11 and PyTorch >= 2.3.1, but the product must not invent a VRAM threshold without evidence.

If a provider cannot initialize in the project runtime, report:

```text
PROVIDER_RUNTIME_INCOMPATIBLE
```

The agent must not silently:

- downgrade functionality;
- change the default provider;
- create a hidden backend/server;
- claim provider compatibility without a real initialization test.

---

## `bootstrap`

Must:

1. verify supported Windows;
2. report Windows version/build and x64 architecture;
3. verify the configured CPython 3.11 baseline;
4. create/sync the virtual environment;
5. install desktop/dev dependencies;
6. verify PySide6 initialization;
7. verify the configured 3D rendering stack;
8. verify `trimesh` and glTF rig/animation parsing dependencies;
9. report installed reconstruction provider state;
10. report installed rigging provider state;
11. report NVIDIA driver/GPU state;
12. report CUDA state;
13. report physical GPU model;
14. report total physical VRAM;
15. report currently free VRAM separately;
16. derive the application's capability set;
17. create local app data directories in a safe development location;
18. record the provider compatibility matrix.

`bootstrap` must distinguish:

```text
PASS
WARNING
BLOCKED_BY_ENVIRONMENT
PROVIDER_RUNTIME_INCOMPATIBLE
```

Available/free VRAM must never be substituted for total physical VRAM when assigning a product tier. Record both values.

---

## `test-provider-compatibility`

This test exists because the single-process Python application must support providers with different upstream dependency expectations.

It must verify, within the actual project environment:

- Hunyuan3D 2.0 adapter import;
- Hunyuan3D 2.0 provider initialization or the earliest safe smoke point;
- optional Hunyuan3D 2.1 adapter import and initialization when installed;
- SkinTokens/TokenRig adapter import and initialization when installed/eligible;
- optional UniRig adapter import and initialization when installed;
- custom native extensions required by an enabled provider;
- PySide6 + VTK/PyVista still import successfully in the same environment;
- the selected PyTorch/CUDA build is the one actually used by providers.

A provider may be marked unavailable without failing the entire desktop app, but:

- Hunyuan3D 2.0 compatibility is required before real Standard reconstruction is considered available;
- a rigging provider is required before maximum-scope auto-rigging is considered available.

Do not solve incompatibility by creating a local HTTP service.

---

## `test-ui`

Automated checks should verify:

- main window can instantiate;
- major navigation destinations can open;
- progress signals do not freeze the event loop;
- long-running jobs execute outside the UI thread;
- modal overlays close correctly;
- region-selector geometry behaves correctly;
- theme token values are centralized;
- Reconstruction Quality exposes `Standard` and `High Quality` distinctly;
- High Quality controls are disabled with an actionable reason when unavailable;
- GPU/provider capability-dependent controls are correctly enabled/disabled;
- 3D review workspace can instantiate;
- rigging/skeleton workspace can instantiate;
- animation workspace can instantiate;
- unsupported actions explain why they are unavailable;
- imported rigged assets can still enter animation editing even when local auto-rigging AI is unavailable.

Manual visual checks are also mandatory for UI phases.

---

## Visual manual acceptance

At each major UI phase, record screenshots for at least:

- home/project view;
- capture-ready view;
- active-capture view;
- processing/reconstruction view;
- Standard vs High Quality provider selection/readiness state;
- 3D review view;
- rigging/skeleton view;
- pose/animation view;
- error/GPU-unavailable state.

Reject the phase if the UI violates the anti-pattern list in `AGENTS.md` or `SPECS/09-ui-design-system.md`.

Passing unit tests, default Qt styling, or placeholder panels are not substitutes for visual review.

---

## `test-capture`

Must verify at minimum:

- region coordinates are correct at 100%, 125%, 150%, and 200% DPI where the test environment allows;
- one-monitor-only constraint is enforced for the reconstruction MVP;
- selected area matches encoded output dimensions;
- capture start/stop is idempotent;
- global hotkey registration and release are correct;
- capture resources are released after stopping;
- repeated capture sessions do not leak handles/resources;
- no audio is recorded;
- output metadata matches configured FPS/codec expectations;
- the resulting capture can be reopened by preprocessing.

Where supported, verify that the Windows GPU capture path is actually used rather than silently falling back to a slow generic screenshot loop.

---

## GPU capability model

GPU support must be represented as **independent capabilities**, not one `gpu_supported` boolean.

At minimum expose:

```text
CUDA
STANDARD_SHAPE
STANDARD_TEXTURED_PIPELINE
HIGH_QUALITY_SHAPE
HIGH_QUALITY_TEXTURE
HIGH_QUALITY_COMBINED_PIPELINE
AUTO_RIGGING
SKELETON_EDITING
ANIMATION_EDITING
ANIMATION_PLAYBACK
STANDARD_FULL_PRODUCT
HIGH_QUALITY_FULL_PRODUCT
```

Editor capabilities are not identical to AI-generation capabilities.

For example, a machine with insufficient VRAM for auto-rigging may still edit/play animation on an imported rigged GLB.

---

## Default provider policy

### Standard reconstruction

Default provider:

```text
Hunyuan3D 2.0
```

Official upstream reference policy:

- Shape: ~6 GB VRAM;
- Shape + Texture total: ~16 GB VRAM.

This is the default product path.

### High Quality reconstruction

Optional provider:

```text
Hunyuan3D 2.1
```

Official upstream reference policy:

- Shape: ~10 GB VRAM;
- Texture: ~21 GB VRAM;
- documented combined Shape + Texture: ~29 GB VRAM.

High Quality mode requires both:

1. GPU capability; and
2. provider/runtime compatibility.

Enough VRAM alone does not make High Quality available.

### Default auto-rigging

Reference provider:

```text
SkinTokens / TokenRig
```

Current upstream inference prerequisite:

```text
NVIDIA GPU VRAM >= 14 GB
```

plus its documented software requirements.

Alternate providers such as UniRig must advertise their own verified capabilities. Do not reuse the SkinTokens threshold for them automatically.

---

## Product VRAM tiers

The table below is the product's conservative **reference tier classification** when using:

- Hunyuan3D 2.0 for Standard reconstruction;
- Hunyuan3D 2.1 for optional High Quality reconstruction;
- SkinTokens/TokenRig for the default auto-rigging lane;
- sequential loading/unloading of heavyweight providers.

| Total VRAM | Product tier | Required harness assertion |
|---|---|---|
| `< 6 GB` | `NO_LOCAL_RECONSTRUCTION` | Default Hunyuan3D 2.0 reconstruction is disabled. Import/view/edit non-AI features may remain available. |
| `6–9 GB` | `STANDARD_SHAPE` | Hunyuan3D 2.0 Shape may be enabled after provider smoke test. Standard Texture, default auto-rigging, and 2.1 High Quality are disabled by VRAM policy. |
| `10–13 GB` | `STANDARD_SHAPE_PLUS_HQ_SHAPE_CANDIDATE` | Hunyuan3D 2.0 Shape is eligible. Hunyuan3D 2.1 Shape may be offered only if its runtime smoke test passes. Standard 2.0 full Texture path and default SkinTokens auto-rigging remain disabled. |
| `14–15 GB` | `RIGGED_UNTEXTURED_STANDARD` | Hunyuan3D 2.0 Shape and default SkinTokens auto-rigging are eligible. Skeleton/Skinning/Pose/Animation workflow is eligible. Standard 2.0 Shape+Texture total path remains below its official 16 GB reference. |
| `16–20 GB` | `STANDARD_FULL` | Hunyuan3D 2.0 Shape+Texture and default SkinTokens auto-rigging are eligible sequentially. The project's maximum Standard-quality workflow is eligible. 2.1 Shape may also be eligible if runtime-compatible; 2.1 Texture is disabled by VRAM policy. |
| `21–28 GB` | `STANDARD_FULL_PLUS_HQ_SEQUENTIAL_CANDIDATE` | Standard full workflow is eligible. Hunyuan3D 2.1 Shape and Texture individual stages meet their published VRAM figures, but the documented combined 2.1 pipeline is below its 29 GB reference. Any sequential low-memory 2.1 path must be explicitly configured and proven by real smoke test before being called supported. |
| `29 GB+` | `HIGH_QUALITY_FULL` | Hunyuan3D 2.1 documented combined Shape+Texture range is eligible, plus default auto-rigging and skeletal animation, subject to runtime compatibility. |

These tiers are **not** a claim that every run consumes exactly those amounts.

Provider-specific requirements remain authoritative.

A test may not substitute current free VRAM for total physical VRAM tier classification.

---

## Provider-specific capability override policy

VRAM tiers are reference defaults, not permission to fabricate capability.

A provider-specific capability may override a default tier only when the project records:

- provider name;
- provider version/checkpoint;
- Python/PyTorch/CUDA environment;
- GPU model;
- total VRAM;
- a real initialization test;
- a representative inference smoke test;
- peak VRAM where practical;
- actual output validation.

A coding agent may not lower a threshold merely to make a test pass.

---

## Provider lifecycle verification

Because the application targets consumer GPUs, heavyweight AI providers must support explicit lifecycle management.

The intended sequence is:

```text
load reconstruction provider
→ generate shape
→ persist result
→ unload/release provider when the next heavyweight stage needs memory

→ load texture stage/provider when enabled
→ generate texture
→ persist result
→ unload/release

→ load rigging provider when enabled
→ generate skeleton + skinning
→ persist result
→ unload/release
```

The app must not depend on Hunyuan and rigging models fitting in VRAM simultaneously.

The harness should record VRAM before/after each provider lifecycle where practical.

A provider memory leak that prevents the next eligible stage from running is a harness failure.

---

## `test-gpu`

A passing real GPU test must prove:

- `torch.cuda.is_available()` is true;
- a CUDA device can be selected;
- a real CUDA tensor operation executes;
- result tensor remains on CUDA;
- GPU name is recorded;
- total physical VRAM is recorded;
- free VRAM is recorded separately;
- product VRAM tier is derived from total physical VRAM;
- provider/runtime compatibility is applied after the VRAM gate;
- Hunyuan3D 2.0 initialization is attempted when Standard capability is eligible;
- Hunyuan3D 2.1 initialization is attempted only when installed/requested and its High Quality capability is eligible;
- rigging-provider initialization is attempted when its capability is eligible;
- representative eligible inference smoke tests run on CUDA;
- GPU/VRAM telemetry is recorded;
- provider unload behavior is verified.

If the machine has no compatible GPU, report `BLOCKED_BY_ENVIRONMENT`; do not convert the test to CPU and call it passed.

The test must not:

- silently use CPU;
- use mock inference and call the GPU test passed;
- classify using current free VRAM;
- claim 2.0 Texture because Shape fits;
- claim 2.1 High Quality because Standard fits;
- claim rigging because reconstruction fits.

---

## `test-ai-mock`

Must run without heavyweight model weights and prove:

- capture → attempt state transitions;
- Standard/High Quality option persistence;
- progress reporting;
- cancellation behavior;
- mock GLB result publication;
- mock textured-result publication;
- mock rigged-result publication;
- Accept/Reject/Regenerate behavior;
- application restart state restoration.

Mock providers must use the same application-facing contracts as real providers.

---

## `test-reconstruction`

A real reconstruction test must prove the **Standard provider first**.

### Standard path

Verify:

- Hunyuan3D 2.0 adapter initializes;
- inference uses CUDA;
- representative input is accepted;
- a real mesh is generated;
- output contains vertices/faces;
- result serializes to the canonical GLB path;
- the embedded viewer opens the GLB;
- provider/version/quality-mode telemetry persists;
- provider resources can be unloaded.

For GPUs at or above the Standard Texture capability, also prove a real Shape + Texture result under the configured 2.0 path.

### High Quality path

High Quality is a separate optional test.

When eligible and installed, verify:

- Hunyuan3D 2.1 runtime compatibility;
- High Quality Shape generation;
- High Quality Texture only when its capability allows it;
- documented combined path only when the 29 GB+ capability is eligible, unless a separately verified sequential/low-memory configuration is explicitly recorded.

Standard success must not imply High Quality success.

---

## `test-rigging`

Automatic rigging is a separate AI verification stage.

A passing real rigging test must prove:

```text
mesh
→ rigging provider
→ skeleton hierarchy
→ skinning weights
→ rigged asset
```

At minimum verify:

- configured provider initializes on the intended CUDA device;
- provider receives a valid mesh;
- at least one root joint exists;
- skeleton contains a valid parent/child hierarchy;
- there are no cyclic bone relationships;
- joint transforms are finite;
- skinning weights are produced;
- skinning weights reference valid joints;
- vertex influences are finite;
- per-vertex weights satisfy normalization tolerance;
- deformation can be evaluated using the generated rig;
- rigged result can be serialized and reopened;
- embedded viewer can display the skeleton;
- textures are preserved where the provider/transfer contract supports it.

A test that generates bone positions but no usable skinning weights does not count as full auto-rigging success.

For the default SkinTokens lane, auto-rigging must remain disabled below its current upstream 14 GB inference requirement.

---

## `test-animation`

Animation playback itself is not treated as heavyweight AI inference once a valid rig exists.

Verify:

- a rigged model can enter animation mode;
- skeleton can be shown/hidden;
- bones can be selected;
- local bone rotation can be edited;
- parent/child propagation is correct;
- bind pose can be restored;
- quaternion values remain normalized;
- quaternion storage order is `[x, y, z, w]`;
- From Pose can be saved;
- To Pose can be saved;
- From/To can be swapped;
- pose can be duplicated/reset;
- at least two key poses can form an animation;
- rotation interpolation uses quaternion SLERP/shortest path rather than Euler linear interpolation;
- root translation interpolation is deterministic;
- play/pause/resume/seek/stop work;
- loop preview works;
- playback does not freeze the Qt event loop;
- skinned mesh deformation follows the skeleton;
- animation state can be saved and restored after restart.

If a more general keyframe timeline is implemented, additionally verify ordered timestamps and deterministic interpolation between keyframes.

AI motion generation is not part of this test unless separately specified later.

---

## `test-model-validation`

Fixture coverage must include:

- valid untextured GLB;
- valid textured GLB;
- empty scene;
- no mesh;
- invalid indices;
- NaN/Infinity vertices;
- zero/near-zero bounds;
- degenerate triangles;
- missing texture references where representable;
- disconnected geometry warning case;
- unexpectedly huge bounds warning/failure case;
- invalid transform values.

Validation should distinguish:

```text
PASS
PASS_WITH_WARNINGS
FAIL
```

Visual similarity to the source capture is not equivalent to technical model validity.

---

## `test-rigged-model-validation`

Rigged asset fixtures must include:

- valid rigged GLB;
- valid textured + rigged GLB;
- missing root bone;
- cyclic hierarchy;
- invalid parent index;
- invalid joint reference;
- NaN/Infinity joint transform;
- skinning weights referencing missing joints;
- invalid/negative weights where disallowed;
- non-normalized weights;
- all-zero vertex influence;
- malformed inverse-bind matrices;
- mesh without a compatible skin;
- skeleton without skinned geometry;
- malformed animation channel/target where representable.

The validator must distinguish:

- mesh validity;
- material/texture validity;
- skeleton validity;
- skinning validity;
- animation validity.

A mesh may be valid while its rig is invalid.

---

## `test-integration`

### Reconstruction MVP milestone

The first integration milestone executes:

```text
create project
→ register/import sample capture
→ run preprocessing
→ run Standard mock or real reconstruction
→ validate GLB
→ open review state
→ accept result
→ restart app state layer
→ verify accepted asset persists
```

### Maximum-scope integration

The completed product integration test should execute the highest supported capability path:

```text
create project
→ capture/import source
→ preprocess/select views
→ reconstruct with selected quality mode
→ texture when supported
→ validate static model
→ review model
→ auto-rig when supported
→ validate skeleton + skinning
→ open rig review
→ create From Pose
→ create To Pose
→ preview skeletal animation
→ persist animation
→ accept result
→ restart application/state layer
→ reopen project
→ verify model/texture/rig/poses/animation persist
```

For GPUs that do not support all AI capabilities, execute the highest supported path and clearly report intentionally skipped gated stages.

A skipped stage due to an intentional capability gate is not a failure.

A stage that should be supported according to detected capability but fails is a failure.

---

## Responsiveness verification

Heavy operations must never execute directly on the Qt UI thread.

Verify responsiveness during:

- video preprocessing;
- frame extraction;
- segmentation;
- Shape reconstruction;
- Texture generation;
- auto-rigging;
- mesh validation;
- rig validation;
- large model loading;
- project serialization where significant.

At minimum:

- UI event processing continues;
- progress events arrive;
- cancellation requests are accepted where supported;
- windows remain repaintable;
- worker exceptions propagate to controlled UI error states.

A visually frozen window is a failure even if the underlying task eventually completes.

---

## Cancellation and recovery

Long-running operations should support cancellation where the underlying provider permits safe cancellation.

Verify cancellation during:

```text
capture
preprocessing
reconstruction
texture generation
rigging
```

After cancellation:

- UI returns to a stable state;
- partial artifacts are not treated as successful output;
- provider resources are released;
- CUDA memory is released where possible;
- the project remains usable;
- a new attempt can start without restarting the app whenever practical.

Unexpected provider crashes must not corrupt previously accepted assets.

---

## Telemetry requirements

Development telemetry should record at minimum:

```text
operation
quality_mode
provider
provider_version
device_name
device_index
total_vram
free_vram_before
peak_vram_if_available
duration
result
failure_reason
```

AI operations should record enough configuration metadata to reproduce the provider setup without storing private user source content in logs.

Do not log raw captured frames or binary model data by default.

---

## Packaging verification

`package` / `verify` must check:

- app starts on a clean supported Windows test account;
- required Qt plugins are included;
- VTK/PyVista runtime assets are included;
- glTF/animation parser dependencies are included;
- native DLL discovery is deterministic;
- CUDA/native-extension failures produce useful messages;
- model weights are handled according to packaging policy;
- large model weights are not accidentally duplicated inside the package;
- user data is not stored inside the installation directory;
- uninstalling/replacing the app does not delete user projects;
- GPU capability detection works in the packaged app;
- Standard provider discovery works;
- High Quality provider remains optional and truthfully gated;
- rigging provider discovery works;
- global hotkeys work;
- capture works;
- static 3D viewer works;
- skeleton overlay and animation editor work on fixture rigged assets even when AI weights are absent.

---

## Final `verify`

`verify` is the release-level harness entry point.

For the completed maximum-scope build it should cover:

```text
format
→ lint
→ typecheck
→ unit tests
→ UI tests
→ storage tests
→ capture tests
→ provider compatibility tests
→ GPU tests
→ reconstruction tests
→ static model validation
→ rigging tests
→ rigged-model validation
→ animation tests
→ integration tests
→ build
→ package smoke test
```

A release report must state an overall result:

```text
PASS
PASS_WITH_WARNINGS
BLOCKED_BY_ENVIRONMENT
PROVIDER_RUNTIME_INCOMPATIBLE
FAIL
```

and separately report capabilities:

```text
CUDA
Standard Shape
Standard Shape + Texture
High Quality Shape
High Quality Texture
High Quality Combined Pipeline
Auto Rigging
Skeleton Editing
Pose Editing
Animation Playback
Standard Full Product
High Quality Full Product
```

The application must never describe itself simply as `GPU Supported` when only a subset of GPU-dependent capabilities is available.
