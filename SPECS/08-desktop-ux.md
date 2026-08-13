# 08 — Desktop UX

## Main information architecture

Use a content-oriented desktop workspace, not a generic analytics dashboard.

Recommended top-level areas:

- Projects
- Capture
- Processing/Attempts
- Review
- Rig
- Animate
- Settings/Diagnostics

Navigation may use a compact text-and-icon sidebar or top/side hybrid, but labels must remain visible at normal desktop widths.

## Main window

Recommended minimum size: approximately 1180 × 760 logical px.

Layout should scale comfortably to 1440p and 4K displays with DPI scaling.

## Project screen

Show projects and recent captures as working items, not KPI cards.

Each item should surface:

- name;
- thumbnail where available;
- last modified time;
- accepted model state;
- rig availability;
- animation availability;
- current attempt state if active.

## Capture screen

Before capture:

- concise guidance about rotating the character and avoiding occlusion;
- prominent `Select & Record` action;
- current hotkey;
- GPU readiness summary only if relevant to the next step.

During capture:

- avoid showing a heavyweight modal that covers the target application;
- use the external overlay/indicator defined in the capture spec.

After capture:

- video preview;
- duration/resolution;
- discard/re-record;
- Reconstruction Quality selector;
- Standard mode selected by default;
- High Quality availability/reason;
- generate model action.

The same section must offer `Import existing video`. Import is a peer of recording, not a separate workflow: its preview, provider selector, processing state, and review handoff are identical after the managed local copy is created.

## Reconstruction Quality control

The UI must make the provider policy understandable without exposing research-model complexity unnecessarily.

Recommended labels:

```text
Standard
Lower VRAM · Default

High Quality
Higher VRAM · Optional
```

Detailed diagnostics may reveal provider names. The main workflow may show them in secondary text/tooltips.

Do not silently auto-upgrade to High Quality.

## Processing screen

Show actual stage progression:

- Preparing frames
- Selecting views
- Isolating character when used
- Loading Standard/High Quality model
- Generating geometry
- Generating/processing texture when used
- Running isolated local texture process when the provider requires process isolation
- Normalizing GLB
- Validating model
- Loading rigging model when used
- Generating skeleton and skinning
- Validating rig

Do not represent indeterminate AI work as a fake exact percentage.

Processing logs must be readable on the warm surface and include a local date/time for each user-visible task event. Logs describe stages and actionable failures; raw stack traces remain in diagnostics rather than the primary view.

## Review screen

The review screen is the primary static-model work surface. Prioritize model visibility and source comparison.

When a model is accepted and auto-rigging is eligible, expose a clear next action such as `Create Rig`.

If local auto-rigging is unavailable, explain the reason but continue to allow importing/opening an already rigged asset where supported.

## Rig workspace

Required visible elements:

- large model viewport;
- skeleton overlay toggle;
- bone hierarchy/search panel;
- selected-bone information;
- validation summary;
- retry/regenerate rig action where applicable;
- continue-to-animation action only for a valid rig.

Avoid turning the rig workspace into a dense DCC clone. Surface only the controls required by the specification.

## Animate workspace

Required baseline controls:

- bone selection and local rotation editing;
- bind-pose reset;
- save From Pose;
- save To Pose;
- swap From/To;
- duplicate/reset pose;
- duration;
- play/pause;
- seek;
- loop preview;
- save animation state.

Use a compact timeline/progress strip where appropriate. Do not imitate a web video editor.

## Errors

Errors should explain:

1. what failed;
2. whether user data was preserved;
3. what the user can do next;
4. whether the issue is GPU VRAM, provider compatibility, model validity, or another cause;
5. whether diagnostics can be copied/opened.

Avoid raw stack traces in the primary UI.
