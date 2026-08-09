# Phase 00 Environment Validation Report

**Phase status:** `WARNING`
**Revalidated:** 2026-08-09 (Asia/Seoul)

The core Python 3.11 desktop-development runtime is configured and its required Phase 00 smoke tests pass. Hunyuan and rigging providers/weights are intentionally not installed yet, so their real initialization and inference tests remain deferred to their provider phases.

## 1. Current Phase

`PHASES/00-environment-validation.md` only. Phase 01 implementation has not started.

## 2. Work Performed

- Installed CPython 3.11.9 and `uv 0.12.3`; added the Python 3.11 Scripts directory to the user `PATH` for future terminals.
- Created the project-local `.venv` with CPython 3.11 and installed the Phase 00 desktop, capture, 3D, GLB, test, quality, packaging, and CUDA runtime dependencies.
- Re-ran real CUDA, Qt Widgets, DXcam, PyVista/VTK/pyvistaqt, trimesh GLB, and PyInstaller smoke tests in that same runtime.
- Kept all AI model providers and weights uninstalled; no mock or CPU fallback was used for GPU tests.

## 3. Windows / Python Environment

| Item | Status | Actual result |
|---|---|---|
| OS | WARNING | Windows 10 Home, DisplayVersion 25H2, build 26200.8973, x64. Windows 10 is the supported fallback target; Windows 11 is primary. |
| Python baseline | PASS | CPython 3.11.9 x64; `.venv` uses this interpreter. |
| `uv` | PASS | `uv 0.12.3`; installed in `C:\Users\a0107\AppData\Local\Programs\Python\Python311\Scripts` and added to the user `PATH`. |
| Runtime isolation | PASS | All revalidation commands cleared inherited `PYTHONPATH` and used `.venv\Scripts\python.exe`. |
| Environment hygiene | WARNING | Existing global `PYTHONPATH=E:\lang\Python310\Lib\site-packages` can contaminate ad-hoc shells. Project commands must clear it or activate the isolated environment. |

## 4. GPU Model and VRAM

| Item | Status | Actual result |
|---|---|---|
| GPU | PASS | NVIDIA GeForce RTX 4070 Ti |
| NVIDIA driver | PASS | 591.86 |
| Total physical VRAM | PASS | 12,282 MiB (12.0 GiB) from `nvidia-smi`; PyTorch reported 12,878,086,144 bytes. |
| Free VRAM | PASS | 10,048 MiB from `nvidia-smi`; PyTorch measured 11,561,738,240 bytes immediately before the CUDA smoke. These are diagnostics, not tier inputs. |
| CUDA Toolkit | PASS | `nvcc` CUDA Toolkit 12.4.131. |

## 5. CUDA / PyTorch Status

| Item | Status | Actual result |
|---|---|---|
| PyTorch runtime | PASS | `.venv`: `torch 2.5.1+cu124`, `torchvision 0.20.1+cu124`, `torchaudio 2.5.1+cu124`. |
| CUDA availability | PASS | `torch.cuda.is_available()` returned true; one CUDA device is available. |
| Real CUDA operation | PASS | `torch.arange(1, 1_000_001, device='cuda:0').square().mean()` completed at `cuda:0`, returned `333333856256.0`, and result-device residency remained `cuda:0`. |
| CUDA telemetry | PASS | Device compute capability is 8.9. Total/free memory was recorded before allocation; no CPU fallback was used. |

## 6. Hunyuan3D 2.0 Status

`WARNING` — no Hunyuan3D 2.0 adapter/source or model weights are installed. The 12.0 GiB hardware tier is eligible for its 6 GB Shape reference requirement, but provider initialization, CUDA inference, output validation, and unload verification have not run. Standard Shape must remain unavailable until those real checks pass.

## 7. Hunyuan3D 2.1 Status

`WARNING` — no Hunyuan3D 2.1 adapter/source or weights are installed. The GPU is only a High Quality Shape candidate by total VRAM; it does not meet the 21 GB Texture or 29 GB documented combined-pipeline references. No incompatibility is proven, so this is not `PROVIDER_RUNTIME_INCOMPATIBLE`.

## 8. Rigging Provider Status

`WARNING` — SkinTokens / TokenRig and UniRig are not installed. SkinTokens is additionally VRAM-gated: this 12.0 GiB GPU is below its documented 14 GB inference requirement. Neither provider was substituted, mocked, or run on CPU.

## 9. Detected GPU Capability

**Hardware VRAM tier:** `STANDARD_SHAPE_PLUS_HQ_SHAPE_CANDIDATE` (10–13 GB), derived from total physical VRAM only.

| Capability | Status |
|---|---|
| CUDA | PASS — real CPython 3.11 CUDA operation completed |
| Shape Reconstruction | WARNING — VRAM eligible, but Hunyuan 2.0 is uninstalled/unproven |
| Texture Generation | WARNING — Standard 16 GB reference gate not met |
| Auto Rigging | WARNING — SkinTokens 14 GB reference gate not met and provider uninstalled |
| Skeleton Editing / Pose Editing / Animation Playback | PASS — required desktop/3D runtime compatibility is proven; future feature implementation remains required |
| Standard Full Pipeline | WARNING — 16 GB reference gate not met |
| High Quality Shape | WARNING — VRAM candidate only; provider uninstalled/unproven |
| High Quality Texture | WARNING — 21 GB reference gate not met |
| High Quality Full Pipeline | WARNING — 29 GB reference gate not met |

## 10. PASS Items

- CPython 3.11.9, `uv 0.12.3`, project-local `.venv`, and a single verified dependency runtime.
- PySide6 6.11.1 / Qt 6.11.1 real Qt Widgets window initialization, display, event processing, and close.
- DXcam 0.3.0 Desktop Duplication capture: actual BGR frame `(1440, 2560, 3)` / `uint8` from output 0.
- PyVista 0.48.4, VTK 9.6.2, and pyvistaqt 0.12.0 real `QtInteractor` scene initialization.
- trimesh 5.0.0 generated, exported, and reloaded a valid GLB fixture with one geometry.
- pygltflib 1.16.5 import, PyAV 18.0.0 import, and all listed test/quality dependencies import.
- Real CUDA:0 PyTorch tensor calculation with `torch 2.5.1+cu124`.
- PyInstaller 6.22.0 built and launched a one-folder PySide6 package successfully.

## 11. WARNING Items

- Windows 10 is the fallback, not primary Windows 11 target.
- Global `PYTHONPATH` is cross-version and must not be inherited by project commands.
- 12.0 GiB VRAM is below Standard Texture, SkinTokens, High Quality Texture, and High Quality Full Pipeline reference gates.
- Provider code and weights are not present; real provider tests were intentionally not fabricated.

## 12. BLOCKED / FAIL Items

| Item | Status | Evidence |
|---|---|---|
| Hunyuan3D 2.0 real provider test | `BLOCKED_BY_ENVIRONMENT` | Adapter/source and weights are not installed. |
| Hunyuan3D 2.1 real provider test | `BLOCKED_BY_ENVIRONMENT` | Adapter/source and weights are not installed. |
| SkinTokens / TokenRig real provider test | `BLOCKED_BY_ENVIRONMENT` | Provider is uninstalled; hardware also fails its 14 GB VRAM reference gate. |
| UniRig real provider test | `BLOCKED_BY_ENVIRONMENT` | Provider is uninstalled. |
| Standard Texture / Full Pipeline | WARNING | Intentionally VRAM-gated by the 16 GB reference requirement. |
| High Quality Texture / Full Pipeline | WARNING | Intentionally VRAM-gated by the 21 GB / 29 GB reference requirements. |

## 13. Commands and Tests Run

```powershell
winget install --id Python.Python.3.11 --exact --scope user ...
py -3.11 -m ensurepip --upgrade
py -3.11 -m pip install uv
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe --index-url https://download.pytorch.org/whl/cu124 torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
uv pip install --python .venv\Scripts\python.exe PySide6==6.11.1 dxcam numpy scipy pillow opencv-python av pyvista vtk pyvistaqt trimesh pygltflib nvidia-ml-py pytest pytest-qt pytest-cov ruff mypy pyinstaller

.\.venv\Scripts\python.exe -  # imports, CUDA:0 tensor, Qt Widgets, GLB, QtInteractor
.\.venv\Scripts\python.exe -  # DXcam actual frame capture
.\.venv\Scripts\python.exe -m PyInstaller --onedir --windowed ...
```

The CUDA smoke synchronized the device and asserted CUDA residency. The DXcam test used actual desktop capture. The package smoke built a fresh one-folder executable and it started/exited successfully.

## 14. Generated or Modified Files

- Updated this evidence report: `PHASES/00-environment-validation-report.md`.
- Created ignored development environment: `.venv/`.
- A temporary PyInstaller probe was created only for the package smoke and then removed.
- No application source, scaffold, provider, UI, storage, or Phase 01 files were created.

## 15. Next Phase Eligibility

The core Phase 00 environment gate is complete with the warnings above. Phase 01 may proceed only when explicitly requested. Real provider availability remains a separate later-phase requirement; it must be proven with provider-specific CUDA initialization, representative inference, output validation, telemetry, and unload checks.
