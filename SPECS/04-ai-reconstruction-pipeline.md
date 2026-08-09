# 04 — AI Reconstruction Pipeline

## Goal

Convert a local character capture into a reviewable GLB without leaving the desktop application, using Hunyuan3D 2.0 by default and Hunyuan3D 2.1 only as an optional High Quality mode.

## Pipeline

```text
Capture MP4
→ probe/decode
→ extract candidate frames
→ score quality
→ remove near-duplicates
→ select representative views
→ optional character isolation
→ normalize inputs
→ selected CUDA reconstruction provider
→ optional texture stage
→ geometry/material normalization
→ GLB
```

## Frame extraction

The pipeline must preserve enough source information to audit how the generated model was produced.

Candidate frames should be scored using factors such as:

- sharpness;
- subject size;
- clipping/cropping;
- occlusion;
- UI/effect interference;
- near-duplicate similarity;
- mask confidence when segmentation is used.

Do not require one exact scoring formula before empirical testing.

## Representative views

Aim to obtain diversity such as:

- front-ish;
- back-ish;
- left/right profile-ish;
- three-quarter views.

Favor viewpoint diversity over selecting multiple nearly identical sharp frames.

## Segmentation

Expose a `SegmentationProvider` abstraction.

Windows-native operation is mandatory. Do not make WSL a required runtime.

The pipeline must be able to:

- run without segmentation if the selected reconstruction provider supports it;
- use a lightweight Windows-compatible background-isolation provider where necessary;
- store masks/alpha inputs as attempt artifacts for debugging.

For the current Windows baseline, use the locally cached `rembg` `isnet-anime` ONNX model. The provider runs through
ONNX Runtime `CUDAExecutionProvider`, is unloaded before Hunyuan Shape load, and must never silently use a CPU
execution provider. Model download is an explicit user action; reconstruction resolves only the configured local cache.

## Reconstruction provider contract

Expose a `ReconstructionProvider` contract conceptually equivalent to:

```text
probe()
capabilities()
load()
generate_shape(inputs, options, progress, cancellation)
generate_texture(mesh, inputs, options, progress, cancellation)  # when supported
unload()
```

Provider-specific libraries must not leak into the UI layer.

## Standard mode — Hunyuan3D 2.0

This is the **default product mode**.

Reference upstream capability:

- Windows support;
- ~6 GB VRAM for Shape generation;
- ~16 GB VRAM for Shape + Texture generation in total.

Standard mode should prioritize broad consumer-GPU compatibility and predictable local execution.

Do not disable Standard Shape merely because the GPU cannot run Standard Texture.

## Experimental textured mode — Stable Fast 3D

Stable Fast 3D is an explicit opt-in alternative that generates Shape and texture together from one isolated RGBA input. It must resolve its SF3D, DINOv2, and CLIP weights from local caches only, run on CUDA, and persist a textured GLB plus the normal validation report. It does not replace Hunyuan3D 2.0 Standard mode.

## High Quality mode — Hunyuan3D 2.1

This is an **optional user-selected mode**.

Reference upstream capability:

- ~10 GB VRAM for Shape;
- ~21 GB VRAM for Texture;
- ~29 GB VRAM for the documented combined Shape + Texture configuration;
- upstream tested environment: Python 3.10 + PyTorch 2.5.1+cu124.

High Quality mode is available only when:

1. the GPU VRAM gate passes for the requested operation; and
2. the Hunyuan3D 2.1 adapter passes runtime compatibility in the actual project environment.

If either condition fails, disable the option and explain why.

## Quality-mode behavior

The user must be able to see which mode will be used before generation.

Persist:

- `quality_mode`: `standard` or `high_quality`;
- provider name;
- provider/checkpoint version;
- shape/texture options;
- selected source frames;
- runtime/device metrics.

Never silently retry with a different Hunyuan generation without surfacing the change as a new attempt/configuration.

## Model loading and VRAM lifecycle

- lazy-load heavy weights;
- show model-loading state;
- cache a provider only while it is safe/useful;
- release it before another heavyweight provider needs the memory;
- expose an explicit release-GPU-memory action if feasible;
- do not reload weights for every operation without reason;
- do not assume reconstruction, texture and rigging providers fit simultaneously.

For 21–28 GB High Quality devices, any sequential 2.1 Shape/Texture strategy must be treated as a separately verified configuration rather than as the official 29 GB combined path.

## Output

Canonical reconstruction output is GLB / glTF 2.0.

Store provenance metadata with each attempt:

- quality mode;
- provider/model version;
- selected input frames;
- inference parameters;
- random seed if controllable;
- device/GPU;
- total/free/peak VRAM metrics where available;
- runtime duration;
- warnings/errors.
