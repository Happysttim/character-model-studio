# 18 — Automatic Rigging Pipeline

## Goal

Convert a technically valid reconstructed or imported character mesh into a usable rigged asset containing a valid skeleton hierarchy and skinning weights, entirely inside the local Python desktop application.

## Entry conditions

Auto-rigging may start only when:

- the source mesh passes static model validation or is explicitly accepted with non-blocking warnings;
- the selected rigging provider is installed and runtime-compatible;
- the provider's GPU capability requirements are satisfied;
- no conflicting heavyweight CUDA provider currently owns the GPU.

An imported rigged asset may skip AI auto-rigging and proceed directly to rig validation.

## Provider abstraction

Expose a `RiggingProvider` contract conceptually equivalent to:

```text
probe()
capabilities()
load()
rig(mesh_path, options, progress, cancellation)
unload()
```

The provider output must be normalized into the application's rig domain model before UI consumption.

## Default provider reference

Default maximum-scope provider: **SkinTokens / TokenRig**.

Reference upstream requirements verified 2026-08-09:

- NVIDIA GPU with at least 14 GB VRAM for inference;
- Python >= 3.11;
- CUDA Toolkit >= 12.1;
- produces skeleton hierarchy + dense skinning weights.

Do not enable this provider below its upstream VRAM requirement.

## Alternate provider

Instance-Rig may be implemented behind the same interface in an isolated TensorFlow runtime. It must expose CUDA; CPU auto-rigging is forbidden.

Do not assign it a product VRAM threshold without authoritative upstream documentation or a recorded real-device smoke test.

## Input preparation

The rigging pipeline may normalize:

- model scale;
- world transform;
- mesh orientation;
- scene flattening where safe;
- disconnected components according to provider constraints.

Normalization must not silently destroy textures or the accepted source model. Produce a provider input artifact when destructive conversion is needed.

## Required output

A successful full auto-rigging result must include:

- one or more skeleton roots according to the provider contract;
- valid bone/joint hierarchy;
- local joint transforms;
- skinning weights for deformable vertices;
- valid joint references;
- enough bind/inverse-bind information to serialize and evaluate deformation;
- a rigged GLB or an intermediate representation that is deterministically converted to canonical rigged GLB.

Bone positions alone are not sufficient.

## Texture preservation

When the source model is textured, preserve materials/textures whenever the provider/transfer path supports it.

If a provider cannot preserve texture/material data:

- do not overwrite the accepted source model;
- surface the limitation before rigging;
- keep both the original static model and the rigged derivative as separate artifacts.

## Provider lifecycle

Auto-rigging is a heavyweight CUDA stage.

Before loading the rigging provider:

- persist reconstruction/texture output;
- unload Hunyuan provider(s) when required;
- verify sufficient free VRAM for the selected rigging provider;
- report a useful OOM/readiness error rather than falling back to CPU silently.

## Cancellation

If the provider permits safe cancellation:

- stop work;
- mark the rig attempt `CANCELLED`;
- do not publish partial output as a successful rig;
- release provider/GPU resources;
- preserve the source model and previous rigs.

## Review

After generation:

- run `SPECS/20-rigged-model-validation.md`;
- show skeleton overlay;
- allow bone hierarchy inspection;
- show provider/version/metrics;
- allow Accept / Reject / Regenerate Rig.

A rejected rig must not reject the underlying reconstruction automatically.
