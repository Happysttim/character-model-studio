"""Absolute-import entry point for the PyInstaller Windows executable."""

from __future__ import annotations

from character_model_studio.main import run


if __name__ == "__main__":
    raise SystemExit(run())
