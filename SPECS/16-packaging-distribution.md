# 16 — Packaging and Distribution

## Goal

Ship one Windows desktop application that launches normally without starting a backend service.

## Baseline packager

PyInstaller for the first distributable.

## Packaging layers

Separate conceptually:

1. desktop application/runtime;
2. common 3D/capture native dependencies;
3. reconstruction provider code/native extensions;
4. rigging provider code/native extensions;
5. large model weights/cache;
6. user project data.

Do not force multi-gigabyte model weights into the main executable unless a later distribution decision explicitly requires it.

## Provider packaging policy

Standard reconstruction is Hunyuan3D 2.0.

High Quality Hunyuan3D 2.1 remains optional and must not break installation/startup when unavailable or runtime-incompatible.

Rigging weights are also optional at install time, but the app must clearly expose whether the configured rigging provider is installed and usable.

Experimental providers such as Hunyuan3D-2GP are optional at install time. Packaging must discover their external source/native extensions and local Shape/Delight/Paint cache without embedding user-specific paths. If configured, the package must also support the app-owned local Python child-process Texture stage.

The package must still open fixture static/rigged GLBs and use the pose/animation editor without downloading AI weights.

## First-run model setup

Preferred:

- app package installs without heavyweight model weights;
- diagnostics/settings can download/configure selected providers;
- Standard provider is presented as the default reconstruction setup;
- `isnet-anime` segmentation setup is required before the capture-to-reconstruction action is enabled;
- experimental SF3D and Hunyuan3D-2GP Shape/Texture setup is explicitly user-selected;
- High Quality setup is optional;
- rigging provider setup is optional until the user needs auto-rigging;
- download progress and required disk/VRAM/runtime compatibility are clear;
- weights are cached outside the install directory.

Offline/manual model placement may be supported.

## Build output

Initial development can use one-folder distribution because debugging native DLL discovery is easier.

One-file packaging is optional and must not be pursued if it makes PyTorch/VTK/CUDA/provider startup unreliable.

## User data

Projects, captures, generated models, rigs, poses, animations and logs must use user-writable data locations outside the installation directory.

Application update/uninstall must not silently delete project data.

## Signing/installer

Code signing and final installer technology are later distribution tasks, but the source tree should not block them.
