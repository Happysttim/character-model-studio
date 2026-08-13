# Phase 09 — Reconstruction MVP Integration

## Goal

Connect capture, real reconstruction, static validation and review into the first usable product milestone.

## Scenario

`hotkey capture → preview → generate → preprocess → CUDA reconstruction → validate → review → accept/reject/regenerate`

## Tasks

- resolve navigation/state race conditions;
- startup recovery for interrupted reconstruction attempts;
- Standard/High Quality selection/readiness UX;
- progress/error UX polish;
- source-frame comparison;
- project history/reopen;
- diagnostics copy/open-log actions;
- final UI anti-pattern review for reconstruction surfaces;
- performance profiling of UI-thread responsiveness.

## Acceptance criteria

- complete Reconstruction MVP scenario works without server components;
- Standard Hunyuan3D 2.0 is the default real path;
- user data survives restart;
- failure states are actionable;
- visual system is consistent across all real screens;
- maximum-scope rigging phases can consume an accepted model without architectural rewrite.

## Milestone

Completion marks the **Reconstruction MVP**, not the end of the project.
