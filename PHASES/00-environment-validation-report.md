# Phase 00 Environment Validation Report

**Phase status:** `WARNING`

## Result

The project development runtime was configured successfully with CPython 3.11, `uv`, and a project-local virtual environment. The same runtime passed real CUDA tensor, PySide6 Qt Widgets, DXcam Desktop Duplication, PyVista/VTK/pyvistaqt, trimesh GLB, and minimal PyInstaller application smoke tests.

## Environment Classification

| Area | Status | Result |
|---|---|---|
| Windows target | WARNING | A supported 64-bit Windows fallback environment was validated. Windows 11 remains the primary target. |
| Python baseline | PASS | CPython 3.11 project runtime is installed and isolated. |
| Dependency tool | PASS | `uv` is installed and available to new user shells. |
| NVIDIA CUDA | PASS | A CUDA-capable NVIDIA device completed a real CUDA-resident PyTorch operation. |
| Desktop/3D stack | PASS | Qt Widgets, capture, 3D embedding, GLB, glTF parsing, media, and packaging smoke tests passed in one runtime. |
| Hunyuan3D 2.0 | WARNING | Provider adapter/source and weights are not installed. |
| Hunyuan3D 2.1 | WARNING | Provider adapter/source and weights are not installed. |
| Rigging providers | WARNING | Provider adapters and weights are not installed. |

The hardware-derived capability tier and free-memory diagnostics were measured only at runtime. They are deliberately excluded from this repository; future application telemetry must resolve them dynamically and keep local diagnostics out of source-controlled documentation.

## Tests Performed

```powershell
uv venv --python 3.11 .venv
uv pip install ...
uv lock
uv sync --locked --group dev

# Real smoke tests in the isolated runtime
<python> -  # CUDA tensor, Qt Widgets, GLB, QtInteractor
<python> -  # DXcam actual frame capture
<python> -m PyInstaller --onedir --windowed ...
```

The CUDA test explicitly synchronized the selected device and asserted CUDA tensor residency. It did not use a CPU fallback. Provider initialization, representative inference, output validation, telemetry, and unload tests remain future provider-specific work.

## Development Data Policy

No model name, driver version, device-memory value, account identifier, or absolute developer-machine path is hardcoded in this report. Runtime diagnostics may collect the information needed for local troubleshooting without committing it to the repository.

## Phase Decision

The core Phase 00 environment gate is complete with the provider warnings above. Phase 01 was authorized separately; later phases must continue to verify provider compatibility in the selected single-process Python runtime.
