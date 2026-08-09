"""Safe module entry point for Character Model Studio's isolated project Python runtime."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _remove_inherited_pythonpath() -> None:
    """Prevent globally injected third-party packages from shadowing the project venv."""
    inherited = os.environ.pop("PYTHONPATH", "")
    if not inherited:
        return
    inherited_paths = {Path(item).resolve() for item in inherited.split(os.pathsep) if item}
    sys.path[:] = [
        item for item in sys.path if not item or Path(item).resolve() not in inherited_paths
    ]


_remove_inherited_pythonpath()

from .main import run  # noqa: E402

raise SystemExit(run())
