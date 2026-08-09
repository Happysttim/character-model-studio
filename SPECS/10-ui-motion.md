# 10 — UI Motion and Animation

## Purpose

Motion should clarify state changes and spatial relationships. It must not make the creative tool feel like a landing page.

## Technology

Use native PySide6 animation classes from Python:

- `QPropertyAnimation`;
- `QVariantAnimation`;
- `QParallelAnimationGroup`;
- `QSequentialAnimationGroup`;
- `QGraphicsOpacityEffect` where appropriate.

No separate JavaScript/QML animation layer.

## Timing tokens

```text
instant     0–80 ms    direct feedback
fast        120–160 ms hover/focus/compact reveal
standard    180–240 ms panel/state transitions
slow        280–360 ms major workspace change
```

Avoid transitions longer than ~400 ms for normal navigation.

## Easing

Prefer restrained ease-out or in-out curves. Avoid overshoot/bounce for ordinary workspace movement.

## Required motion

- hover/focus feedback;
- navigation selection transition;
- processing-stage change;
- drawer/detail pane reveal;
- toast/error appearance;
- capture selector feedback;
- subtle model-view mode transitions when practical;
- turntable camera motion.

## Reduce motion

Expose a `Reduce motion` setting or respect relevant accessibility/system preferences where feasible.

When reduced:

- replace large transitions with fades or immediate state changes;
- keep essential progress feedback.

## Performance

Do not animate expensive blur kernels continuously. Prefer opacity/position/size/color transitions on already-rendered surfaces.

## Distinction from character animation

This specification controls **UI transitions and widget motion only**.

Character skeleton/pose animation is a separate product feature defined in `SPECS/19-skeleton-animation.md` and must not be implemented using UI animation classes as a substitute for correct skeletal transform math.
