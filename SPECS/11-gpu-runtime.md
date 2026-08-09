# 11 — GPU and AI Runtime

## Required production path

NVIDIA CUDA is required for real local AI reconstruction and for GPU-based auto-rigging providers.

The app may run in a limited mode without CUDA for:

- project browsing;
- capture playback;
- static 3D viewing;
- imported rigged-model viewing;
- pose/animation editing on existing compatible rigs where rendering permits;
- mock development/testing.

AI actions must be disabled with actionable readiness messages when their required CUDA/provider capability is unavailable.

## Startup probe

Probe cheaply:

- PyTorch import;
- CUDA available;
- device count;
- primary GPU name;
- total physical VRAM;
- currently free VRAM when available;
- installed provider adapters;
- cached provider weights/checkpoints.

Do not load full reconstruction or rigging model weights at startup.

## Capability model

Do not represent GPU support as one boolean.

At minimum derive:

- `CUDA`
- `CHARACTER_SEGMENTATION`
- `STANDARD_SHAPE`
- `STANDARD_TEXTURED_PIPELINE`
- `HIGH_QUALITY_SHAPE`
- `HIGH_QUALITY_TEXTURE`
- `HIGH_QUALITY_COMBINED_PIPELINE`
- `AUTO_RIGGING`
- `SKELETON_EDITING`
- `ANIMATION_EDITING`
- `ANIMATION_PLAYBACK`
- `STANDARD_FULL_PRODUCT`
- `HIGH_QUALITY_FULL_PRODUCT`

Editor capabilities may remain available when AI generation capabilities are unavailable, provided the user already has a compatible rigged asset.

## Reconstruction providers

### Standard — Hunyuan3D 2.0

This is the default provider.

Official upstream documentation reports approximately:

- 6 GB VRAM for Shape generation;
- 16 GB VRAM for Shape + Texture generation in total;
- Windows support.

### High Quality — Hunyuan3D 2.1

This is optional.

Official upstream documentation reports approximately:

- 10 GB VRAM for Shape generation;
- 21 GB VRAM for Texture generation;
- 29 GB VRAM for the documented combined Shape + Texture configuration;
- tested environment of Python 3.10 + PyTorch 2.5.1+cu124.

Because the application baseline is Python 3.11, High Quality must also pass a runtime compatibility test before being enabled.

## Auto-rigging providers

### Default reference — SkinTokens / TokenRig

Current upstream prerequisites include:

- NVIDIA GPU with at least 14 GB memory for inference;
- Python >= 3.11;
- CUDA Toolkit >= 12.1.

The provider generates a complete skeleton hierarchy and skinning weights from a mesh.

### Alternate — UniRig

UniRig may be added as a provider adapter.

Its upstream documentation targets Python 3.11 and PyTorch >= 2.3.1.

Do not assign a product VRAM threshold to UniRig without a current authoritative requirement or a reproducible local smoke test recorded by the project.

## Product VRAM tiers

The default product policy uses total physical VRAM for classification.

| Total VRAM | Tier | Reference behavior |
|---|---|---|
| `< 6 GB` | `NO_LOCAL_RECONSTRUCTION` | Hunyuan3D 2.0 local reconstruction disabled. Non-AI/import/edit features may still work. |
| `6–9 GB` | `STANDARD_SHAPE` | Standard 2.0 Shape eligible. Standard Texture and default SkinTokens auto-rigging unavailable. |
| `10–13 GB` | `STANDARD_SHAPE_PLUS_HQ_SHAPE_CANDIDATE` | Standard Shape eligible. 2.1 High Quality Shape may be offered only after runtime smoke test. Standard full Texture and default SkinTokens rigging remain unavailable. |
| `14–15 GB` | `RIGGED_UNTEXTURED_STANDARD` | Standard Shape + default SkinTokens rigging eligible sequentially. Skeleton/Skinning/Pose/Animation eligible. Standard 2.0 full Shape+Texture remains below its official 16 GB reference. |
| `16–20 GB` | `STANDARD_FULL` | Standard 2.0 Shape+Texture + default SkinTokens rigging + skeletal animation eligible sequentially. This is the first default tier for the maximum Standard-quality product workflow. |
| `21–28 GB` | `STANDARD_FULL_PLUS_HQ_SEQUENTIAL_CANDIDATE` | Standard full is eligible. 2.1 Shape and Texture individual stages meet published figures, but any sequential low-memory 2.1 workflow must be separately proven and may not be called the documented combined path. |
| `29 GB+` | `HIGH_QUALITY_FULL` | 2.1 documented combined Shape+Texture range plus default rigging and animation are eligible, subject to runtime compatibility. |

These are conservative product defaults, not exact runtime-memory guarantees.

Provider-specific requirements remain authoritative.

Do not classify using current free VRAM. Record free VRAM only for diagnostics and OOM-risk warnings.

## Reconstruction ownership

Default concurrency: one heavyweight AI operation on the primary CUDA device.

The CUDA segmentation provider must unload before Hunyuan Shape loading begins. Its runtime readiness is independent
from the total-VRAM product tier: total VRAM determines tier assignment, while free VRAM is recorded as an operation
start warning only.

Frame preprocessing may overlap where it does not create harmful VRAM pressure.

Do not run Hunyuan reconstruction/texture and auto-rigging models concurrently by default.

## Provider lifecycle

Expected sequence for consumer GPUs:

```text
load reconstruction provider
→ generate shape
→ save result
→ unload/release if needed

→ load texture stage/provider when supported
→ generate texture
→ save result
→ unload/release

→ load rigging provider when supported
→ generate skeleton + skinning
→ save result
→ unload/release
```

The app must not require all heavyweight AI providers to fit simultaneously.

## Memory policy

- record allocated/reserved VRAM when possible;
- record total and free VRAM separately;
- catch CUDA OOM separately;
- offer provider-specific low-VRAM modes only when validated;
- release large temporary tensors between stages;
- do not call aggressive cache clearing in tight loops;
- verify that unloading one provider leaves enough memory for the next eligible provider.

## Version compatibility

Maintain a compatibility matrix for:

- Windows build;
- NVIDIA driver;
- Python;
- PyTorch build/CUDA runtime;
- provider commit/version/checkpoint;
- custom compiled extensions;
- PySide6/Qt;
- VTK/PyVista;
- packaging environment.

Enough VRAM does not override runtime incompatibility.
