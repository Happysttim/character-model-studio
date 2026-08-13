# 03 — Windows Capture

## User interaction

Global hotkey: `Alt + /`.

Idle:

- first hotkey opens the region-selection overlay.

Recording:

- same hotkey stops recording.

## Region selector

- transparent, borderless overlay;
- spans the active monitor used for selection;
- dim outside selected region;
- selection rectangle uses warm high-contrast handles/border;
- display pixel size near the selection without obscuring the subject;
- Esc cancels;
- Enter confirms when a valid region exists;
- minimum capture size must be enforced.

## Multi-monitor rule

MVP selection may not span more than one physical monitor.

If the drag crosses a monitor boundary, clamp or reject with a clear explanation.

## DPI

Region coordinates must be correct under Windows display scaling. Treat Qt logical coordinates and physical capture pixels as different coordinate spaces.

## Capture backend

Primary baseline: DXcam using Windows Desktop Duplication API.

Requirements:

- target 30 FPS by default;
- support selected rectangular region;
- no audio;
- stable stop/restart;
- Direct3D/full-screen applications should be supported where the underlying capture API allows;
- frames are timestamped.

## Encoding

Canonical capture artifact:

- MP4 container;
- H.264 video;
- 30 FPS target;
- no audio;
- preserve exact pixel dimensions of capture region where encoder constraints permit.

Encoding implementation is adapter-based. PyAV is the preferred Python media binding for the MVP. Hardware H.264 should be used when a tested codec path is available; fallback behavior must be explicit and surfaced in diagnostics rather than silently misreported.

## Recording indicator

Show a small non-intrusive overlay near the selected region:

- warm red/orange recording dot;
- `REC`;
- elapsed `mm:ss`;
- does not become part of captured pixels.

## Capture completion

After stopping:

- finalize the file;
- generate poster frame/thumbnail;
- show duration/resolution/FPS;
- allow playback or scrub preview;
- allow discard or proceed to reconstruction.

## Existing video import

The Capture workspace must also allow a user to select a local MP4, MOV, MKV, or AVI file. Import must copy the selected source into the managed project capture folder, generate a representative thumbnail, and continue through the same preview, segmentation, reconstruction, validation, and review flow as a recorded capture. File copying, decoding, and thumbnail generation run outside the UI thread.
