# Phase 07 Real Reconstruction Pipeline Report

**Status:** `PASS_WITH_WARNINGS`

## Completed Foundation Work

- Connected the locally cloned Hunyuan3D-2 source to the project virtual environment as an editable `hy3dgen` package.
- Installed the Shape pipeline's non-server Python dependencies. FastAPI, Uvicorn, Gradio, and other demo/server dependencies were intentionally excluded from the desktop application runtime.
- Configured `HY3DGEN_MODELS` and `HF_HOME` at application bootstrap to use the app-local cache directory, and created those directories automatically.
- Corrected Standard provider discovery to the official `hy3dgen` package name.
- Added a lazy Hunyuan3D 2.0 Standard provider adapter with CUDA-only load behavior, cancellation checks, canonical GLB export, and explicit unload/cache release.
- Proved `hy3dgen.shapegen` imports in the project Python 3.11 + CUDA runtime without loading model weights.

## Real Standard Shape Validation

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 bootstrap
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 verify
powershell -ExecutionPolicy Bypass -File .\scripts\cms.ps1 test-reconstruction
```

The Standard Shape smoke test resolved only the configured local Hugging Face cache. It did not invoke an
online model download, CPU fallback, Mock provider, Texture provider, Hunyuan3D 2.1, or any rigging provider.
It loaded the Shape pipeline on CUDA, proved the DiT model, VAE, and conditioner parameter devices were CUDA,
generated a non-empty GLB, passed static model validation, converted the GLB for the embedded viewer, and unloaded
the provider before recording post-unload VRAM telemetry.

The runtime result is written only to the configured local application data directory as structured telemetry. It
contains the dynamic device, cache, checkpoint, timing, output, geometry, validation, and VRAM measurements without
committing machine-specific values to this repository.

## Shape Snapshot Completeness

The upstream Shape pipeline's `hunyuan3d-dit-v2-0/config.yaml` describes its DiT model, ShapeVAE, conditioner,
scheduler, and image processor. The selected fp16 safetensors Shape checkpoint contains their state and is sufficient
for Shape-only initialization. No separate repository-level config, VAE directory, image processor directory, or
Texture model is required for this tested Shape path.

The Hugging Face cache client considers a Shape-only snapshot incomplete because unrelated repository files are absent.
The application therefore resolves the local cache index and then validates the exact Shape config and checkpoint it
uses. This avoids a full repository download while preserving an offline-only inference path.

## Remaining Warnings

- The smoke input is a generated neutral RGBA fixture, not a user capture; capture-to-real-provider UI acceptance
  remains a manual follow-up.
- Texture generation, Hunyuan3D 2.1, auto-rigging, and animation were intentionally not loaded or tested.
- High Quality readiness remains independently gated by its provider/runtime and VRAM policy.

## Privacy

The cache configuration is derived dynamically from the configured application data root. No user path, account information, GPU model, raw capture content, or model weights are committed to the repository.

## Next Required Authority

Do not begin a later phase without explicit user authorization.
