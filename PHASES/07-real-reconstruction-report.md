# Phase 07 Real Reconstruction Pipeline Report

**Status:** `BLOCKED_BY_ENVIRONMENT`

## Completed Foundation Work

- Connected the locally cloned Hunyuan3D-2 source to the project virtual environment as an editable `hy3dgen` package.
- Installed the Shape pipeline's non-server Python dependencies. FastAPI, Uvicorn, Gradio, and other demo/server dependencies were intentionally excluded from the desktop application runtime.
- Configured `HY3DGEN_MODELS` and `HF_HOME` at application bootstrap to use the app-local cache directory, and created those directories automatically.
- Corrected Standard provider discovery to the official `hy3dgen` package name.
- Added a lazy Hunyuan3D 2.0 Standard provider adapter with CUDA-only load behavior, cancellation checks, canonical GLB export, and explicit unload/cache release.
- Proved `hy3dgen.shapegen` imports in the project Python 3.11 + CUDA runtime without loading model weights.

## Validation

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 bootstrap
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 verify
```

The full project verification passed format, lint, strict type checks, and all automated tests. The installed Standard adapter's lazy probe and the configured local cache environment passed without downloading weights.

## Blocker

No Hunyuan3D 2.0 model weights are present in the configured local cache. The official `from_pretrained` load would therefore initiate a model download, which was not requested in the dependency/cache setup step. No provider load, real inference, GLB output, or texture result is claimed.

Consequently, Phase 07 acceptance criteria requiring a representative capture to generate a real local GLB cannot yet be met. High Quality remains unavailable and is not substituted for Standard.

## Privacy

The cache configuration is derived dynamically from the configured application data root. No user path, account information, GPU model, raw capture content, or model weights are committed to the repository.

## Next Required Authority

Explicit authorization to download the official Hunyuan3D 2.0 weights into the configured local cache is required before the real Standard load/inference smoke test can run.
