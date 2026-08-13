# Phase 09 — MVP Integration

## Goal

Connect all real modules into the product workflow.

## Scenario

`hotkey capture → preview → generate → preprocess → CUDA reconstruction → validate → review → accept/reject/regenerate`

## Tasks

- resolve navigation/state race conditions;
- startup recovery for interrupted attempts;
- progress/error UX polish;
- source-frame comparison;
- project history/reopen;
- diagnostics copy/open-log actions;
- final UI anti-pattern review;
- performance profiling of UI thread responsiveness.

## Acceptance criteria

- complete MVP scenario works without server components;
- user data survives restart;
- failure states are actionable;
- visual system is consistent across all real screens.

## Completion evidence

Record commands run, tests passed, manual checks performed, and any environment blockers. A phase is not complete from code generation alone.
