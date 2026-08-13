"""Absolute-import entry point for the PyInstaller Windows executable."""

from __future__ import annotations

import os
import traceback
from pathlib import Path


def main() -> int:
    """Start the package and preserve actionable startup diagnostics locally."""
    try:
        # Keep this import inside the guard: a frozen, windowed executable has no
        # console for a missing dynamic dependency to report itself.
        from character_model_studio.main import run

        return run()
    except BaseException:  # pragma: no cover - exercised by frozen smoke only
        data_root = Path(os.environ.get("CHARACTER_MODEL_STUDIO_DATA_DIR", Path.cwd()))
        try:
            data_root.mkdir(parents=True, exist_ok=True)
            (data_root / "package-startup-error.log").write_text(
                traceback.format_exc(), encoding="utf-8"
            )
        except OSError:
            # The original exception remains more useful than a log-write failure.
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
