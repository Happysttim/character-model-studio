"""Reproducible one-folder packaging entry point for the Windows desktop application."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Build the distribution without embedding user data or model checkpoints."""
    root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(root / "dist"),
        "--workpath",
        str(root / "build"),
        str(root / "packaging" / "character_model_studio.spec"),
    ]
    return subprocess.run(command, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
