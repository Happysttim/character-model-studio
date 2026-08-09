# 13 — Windows Platform Requirements

## Target

Primary: Windows 11 x64.

Fallback target: Windows 10 x64 where core application features work, with reduced backdrop effects.

## Backdrop/material

On Windows 11 builds supporting `DWMWA_SYSTEMBACKDROP_TYPE`, the app may request a system backdrop through DWM.

The application must also define its own warm fallback background because Mica/Acrylic availability depends on OS/version/system policy.

## Global hotkey

Register `Alt + /` through a Windows global hotkey mechanism and release it cleanly at shutdown.

If registration fails because another application owns the combination:

- show the conflict;
- allow configurable hotkey later or provide a manual capture action.

## DPI awareness

The app must be per-monitor DPI aware through Qt/Windows-supported behavior.

Test physical capture coordinates at multiple scale factors.

## Paths

Use appropriate user-local locations for:

- app configuration;
- logs;
- cache/model weights;
- default projects.

Never require write access to `Program Files`.

## Power and sleep

A running reconstruction should handle lock/sleep/resume gracefully. At minimum, detect failed GPU work and preserve attempt state rather than leaving `RECONSTRUCTING` forever.

## File associations

Not required for MVP.
