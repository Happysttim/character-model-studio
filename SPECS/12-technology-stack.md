# 12 — Technology Stack

## Required application language

Python only for application code.

## Python baseline

Preferred project baseline: **CPython 3.11.x**.

Reason: the maximum-scope rigging lane requires Python 3.11+.

Every enabled reconstruction provider must pass compatibility tests in this single application runtime. Hunyuan3D 2.1 is optional and must not force the whole application back to Python 3.10 unless the user explicitly approves an architecture/runtime change.

## Desktop UI

**PySide6 / Qt Widgets**

Why:

- native Windows desktop integration;
- mature widget/event model;
- Python bindings;
- custom drawing/effects;
- animation primitives;
- integration path for VTK/PyVista;
- no browser runtime.

Do not use QML unless the user later changes the Python-only UI requirement.

## Local task execution

PySide6 `QThread`, `QThreadPool`, `QRunnable`, signals/slots, plus narrowly used Python concurrency helpers.

No remote queue and no local HTTP server.

## Capture

DXcam for high-performance Windows screen capture via Desktop Duplication.

PyAV/OpenCV/Pillow/NumPy for media and image handling.

## AI reconstruction

PyTorch CUDA is the main tensor/inference runtime.

Provider code is isolated.

- Default Standard provider: Hunyuan3D 2.0.
- Optional High Quality provider: Hunyuan3D 2.1.
- Optional experimental multi-view provider: Hunyuan3D-2GP (Hunyuan3D-2mv Shape + Delight/Paint Texture).

Hunyuan3D-2GP uses a locally verified `transformers==4.49.0` compatibility lane, `mmgp`, and rebuilt `mesh_processor`/`custom_rasterizer_kernel` extensions. Its Paint/UV stage may execute in an app-owned local Python child process to keep the PySide6 process responsive; this remains a local desktop application process boundary, not a server.

Optional ONNX Runtime may be used for lightweight auxiliary models only when CUDA/runtime compatibility is explicitly tested.

## Auto rigging

Provider-based Python adapters.

- Reference: SkinTokens / TokenRig.
- Implemented lane: UniRig in its own project-owned CPython 3.11 environment, communicating by local process result/log/artifact only.

Rigging provider output must include or be convertible into:

- skeleton hierarchy;
- joints/bones;
- skinning weights;
- inverse-bind data or equivalent information needed to serialize a valid rigged glTF/GLB.

Provider output validation is mandatory before the animation editor consumes it.

## 3D processing

### `trimesh`

Use for:

- GLB load/export;
- geometry inspection;
- bounding boxes;
- connected components;
- mesh metrics;
- validation helpers.

### `pygltflib` or equivalent

Use for structural glTF access when needed:

- skins;
- joints;
- nodes;
- inverse-bind matrices;
- animation channels/samplers;
- serialization checks.

Do not use it as the only geometry validator.

### PyVista + VTK + pyvistaqt

Use for the embedded interactive model viewer and skeleton visualization.

Do not make the viewer the only GLB validator.

## Skeletal animation math

Baseline libraries:

- NumPy;
- SciPy rotation utilities or an equivalently tested quaternion implementation.

Required math behavior:

- local bone transforms;
- bind/inverse-bind transforms;
- linear blend skinning preview or equivalent correct deformation path;
- normalized quaternions;
- `[x, y, z, w]` storage order;
- quaternion SLERP/shortest-path interpolation.

Plain Euler-angle linear interpolation is not allowed for skeletal rotation animation.

If CPU skinning is too slow after profiling, implement a GPU skinning path inside the Python/VTK rendering architecture rather than adding a browser renderer.

## Local data

- Python `sqlite3`;
- `pathlib`;
- JSON for portable attempt/rig/pose/animation metadata where useful.

Avoid an ORM until domain complexity demonstrates a need.

## Windows integration

Use Python `ctypes`/`wintypes` for small stable Win32/DWM calls such as:

- global hotkey registration;
- window backdrop attributes;
- DPI/monitor helpers where Qt does not provide the required physical-coordinate behavior.

Keep these calls isolated.

For Windows VTK teardown, retain Qt ownership of the interactor/OpenGL context. Do not invoke duplicate VTK explicit cleanup from a late widget close event.

## Packaging

PyInstaller is the first packaging baseline.

Evaluate Nuitka only after the full native dependency stack works because AI/VTK/CUDA/native-extension packaging complexity matters more than theoretical compiler benefits.
