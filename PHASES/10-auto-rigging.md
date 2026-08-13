# Phase 10 — Automatic Rigging

## Goal

Generate a usable skeleton and skinning weights for an accepted/valid model inside the same Python application.

## Tasks

- implement `RiggingProvider` contract;
- retain SkinTokens/TokenRig as the reference contract when compatible;
- implement UniRig as the current project provider in an application-owned isolated CPython runtime, with independently reproduced 8 GiB total-VRAM readiness evidence;
- create rig attempt persistence/state machine;
- unload reconstruction/texture providers before rigging when required;
- normalize provider input without overwriting the accepted source model;
- generate skeleton + skinning weights;
- normalize/serialize rigged GLB;
- preserve texture/materials when provider transfer path supports it;
- run the UniRig FBX-to-original-GLB texture transfer as a distinct, validated stage;
- keep FlashAttention/native dependencies isolated and stage-specific so they do not contaminate the desktop Python runtime;
- expose progress/cancellation/error UX;
- add rig review workspace and skeleton overlay.

## Acceptance criteria

- a real eligible GPU/provider produces a rig containing both skeleton and usable skinning weights;
- rigged result can be reopened;
- source model remains intact;
- provider is gated independently from reconstruction capability;
- UI remains responsive;
- provider can be unloaded after completion.

## Current technical decision

UniRig is the implemented production lane. Skeleton, skinning, and textured-source merge run sequentially in a short-lived local child runtime; they never form a server boundary. SkinTokens/TokenRig remains a reference option and may only be enabled after its own runtime/GPU proof.
