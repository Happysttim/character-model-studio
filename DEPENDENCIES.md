# Dependency Policy

This is a dependency specification, not a promise that every heavyweight model package or checkpoint is bundled into the first executable.

Provider facts in this document were verified against upstream documentation on 2026-08-09. Coding agents must re-check upstream requirements before changing pinned versions.

## Runtime baseline

| Area | Baseline | Purpose |
|---|---|---|
| Python | CPython 3.11.x preferred | Supports maximum-scope rigging lane; reconstruction providers must pass compatibility smoke tests |
| Desktop UI | PySide6 6.11.x compatible | Native Qt Widgets UI |
| Capture | DXcam | Windows Desktop Duplication screen capture |
| Images/video | NumPy, Pillow, OpenCV, PyAV | Frame processing and media encoding/decoding |
| AI runtime | PyTorch CUDA | Local GPU inference |
| Standard reconstruction | Hunyuan3D 2.0 adapter | Default lower-VRAM image-to-3D provider |
| High-quality reconstruction | Hunyuan3D 2.1 adapter | Optional higher-VRAM/PBR quality mode |
| Experimental multi-view reconstruction | Hunyuan3D-2GP adapter | Explicit multi-view Shape + Texture lane; never replaces Standard |
| Auto rigging | SkinTokens / TokenRig adapter | Default maximum-scope skeleton + skinning provider |
| Alternate auto rigging | Instance-Rig adapter | Isolated TensorFlow provider; enable only after CUDA device smoke proof |
| 3D model processing | trimesh | GLB parsing, geometry inspection, normalization/export |
| glTF rig/animation data | pygltflib or equivalent pure-Python glTF layer | Skins, joints, animation channels and serialization |
| Animation math | NumPy + SciPy rotation tools or equivalent tested quaternion utilities | Local transforms, SLERP, interpolation, LBS helpers |
| Embedded 3D rendering | PyVista + VTK + pyvistaqt | Interactive Qt-embedded model/skeleton viewer |
| GPU telemetry | PyTorch CUDA APIs; optional `nvidia-ml-py` | GPU/VRAM reporting |
| Local persistence | Python `sqlite3` | Projects, captures, attempts, rigs, poses, reviews |
| Logging | stdlib `logging` + rotating files | Local diagnostics |
| Tests | pytest, pytest-qt, pytest-cov | Test harness |
| Quality | ruff, mypy/pyright | Formatting/lint/types |
| Environment | uv | Reproducible local environment/lock |
| Packaging | PyInstaller baseline | Windows distributable |

## Python-only application interpretation

Application behavior and orchestration are authored in Python. Native DLLs and compiled extensions brought by PySide6, PyTorch, VTK, CUDA, DXcam dependencies, media codecs, and AI providers are acceptable.

The following are not allowed as application layers:

- C# client;
- Node/JavaScript frontend;
- QML UI;
- local web server;
- service containers.

## Provider compatibility lane

The maximum-scope project needs one application runtime that can host desktop, reconstruction and rigging dependencies.

### Project baseline

Start Phase 00 from **CPython 3.11.x** because:

- SkinTokens currently requires Python >= 3.11;
- Instance-Rig supports Python 3.11 in an isolated runtime;
- the application must eventually support rigging/animation, not only static reconstruction.

### Hunyuan3D 2.0

Hunyuan3D 2.0 is the default reconstruction provider because its official documentation reports approximately:

- 6 GB VRAM for Shape generation;
- 16 GB VRAM for Shape + Texture generation in total;
- Windows support.

Its adapter must still pass the selected Python/PyTorch/CUDA/native-extension smoke tests before Phase 07 is considered unblocked.

### Hunyuan3D 2.1

Hunyuan3D 2.1 is an **optional High Quality provider**.

Its upstream README reports a tested environment of:

- Python 3.10;
- PyTorch 2.5.1 + CUDA 12.4;
- approximately 10 GB VRAM for Shape;
- approximately 21 GB VRAM for Texture;
- approximately 29 GB VRAM for the documented combined Shape + Texture configuration.

Because the project baseline is Python 3.11, 2.1 must not be enabled merely because the GPU has enough VRAM. A real import/load/inference smoke test in the project runtime is also required.

If the 2.1 adapter cannot coexist with the project runtime, report `PROVIDER_RUNTIME_INCOMPATIBLE`. Do not add a hidden HTTP service to work around it.

### Hunyuan3D-2GP experimental multi-view lane

This optional lane is separate from Standard Hunyuan3D 2.0 and High Quality Hunyuan3D 2.1. It requires local source code, local checkpoints, and a verified runtime combination including Hunyuan3D-2mv Shape, Hunyuan3D Delight/Paint Texture, `transformers==4.49.0`, `mmgp`, and rebuilt `mesh_processor`/`custom_rasterizer_kernel` extensions in the active application Python runtime.

Shape and Texture must both pass CUDA-only smoke tests before this provider becomes `READY`. The validated experimental lane requires at least 12 GiB total VRAM; this does not lower or change the published Standard/Higher Quality capability tiers. Texture is run in an app-owned local Python child process because its upstream Paint/UV operations can otherwise make the GUI process unresponsive.

### SkinTokens / TokenRig

SkinTokens is the default maximum-scope auto-rigging reference because it generates both:

- skeleton hierarchy;
- dense per-vertex skinning weights.

Its current upstream prerequisites include:

- NVIDIA GPU with at least 14 GB memory for inference;
- Python >= 3.11;
- CUDA Toolkit >= 12.1.

Treat these as provider-specific requirements, not universal rigging requirements.

### Instance-Rig

Instance-Rig is an allowed alternate provider. It uses TensorFlow, BodyPix and Open3D in an isolated runtime.

Do **not** hard-code an Instance-Rig VRAM threshold unless a current authoritative upstream requirement exists or the project records a reproducible real-device smoke test. Its TensorFlow runtime must expose a CUDA device; CPU fallback is forbidden.

## PyTorch/CUDA version policy

Do not blindly combine the newest PyTorch/CUDA wheel with research-provider native extensions.

Phase 00 must establish and record a reproducible compatibility matrix covering:

- Python;
- PyTorch;
- CUDA runtime/toolkit where required;
- Hunyuan3D 2.0;
- optional Hunyuan3D 2.1;
- SkinTokens/TokenRig;
- optional Instance-Rig isolated runtime;
- custom rasterizers / flash-attn / sparse-convolution extensions when used;
- PySide6;
- VTK/PyVista;
- packaging baseline.

A provider may be marked unavailable while the rest of the app remains usable.

## Reconstruction quality policy

Expose explicit modes rather than silently choosing a provider:

### Standard

- Hunyuan3D 2.0.
- Default selection.
- Consumer-GPU-oriented path.

### High Quality

- Hunyuan3D 2.1.
- User-selectable only when runtime and GPU capability checks pass.
- Must show the additional VRAM/runtime requirements in the UI.

Persist quality mode, provider, provider version and inference options for each reconstruction attempt.

## Segmentation

Segmentation is provider-based because Windows-native compatibility differs among research models.

Preferred strategy:

1. make segmentation optional when the reconstruction provider can use a clean input directly;
2. provide a lightweight Windows-compatible background-removal adapter when needed;
3. add SAM-family adapters only after native Windows installation and GPU execution are proven.

Current baseline provider:

- `rembg[gpu]` 2.0.78 with `onnxruntime-gpu` 1.26.0;
- `isnet-anime.onnx` for game/anime character isolation (approximately 176 MB);
- model cache resolved through `U2NET_HOME`, derived from the configured application-data root;
- `CUDAExecutionProvider` is mandatory for production isolation. Do not accept ONNX Runtime CPU fallback;
- the model is downloaded only through the explicit local model-download command, never during reconstruction.

`isnet-anime` is required for the capture-to-reconstruction MVP path. The desktop application may still launch for browsing/imported asset review when it is absent, but reconstruction controls must remain unavailable with an actionable readiness reason.

Do not require WSL for the Windows desktop product.

## UI motion

No separate UI-animation framework is required.

Use PySide6/Qt animation primitives:

- `QPropertyAnimation`;
- `QVariantAnimation`;
- `QParallelAnimationGroup`;
- `QSequentialAnimationGroup`;
- opacity/effect animations;
- custom widget properties when necessary.

## Skeletal animation stack

Character animation is part of the maximum product target.

Initial implementation should avoid adding Blender as a mandatory runtime dependency.

Use the local Python stack for:

- glTF skin/joint parsing and serialization;
- skeleton hierarchy inspection;
- local bone transforms;
- bind/inverse-bind matrix handling;
- linear blend skinning where required for preview;
- quaternion SLERP;
- From/To Pose and keyframe persistence;
- animation playback in the embedded viewer.

`pygltflib` is an allowed baseline for glTF structural access. `NumPy` and tested quaternion utilities such as `scipy.spatial.transform` may be used for animation math.

If profiling proves CPU skinning is inadequate, a GPU skinning implementation may be added inside the existing Python/VTK rendering architecture. Do not introduce a browser renderer solely for skeletal animation.
