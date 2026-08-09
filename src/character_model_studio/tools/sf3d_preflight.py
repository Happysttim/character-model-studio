"""Offline preflight for a locally cached Stable Fast 3D model."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from character_model_studio.platform.windows.paths import resolve_application_paths

MODEL_FILENAME = "model.safetensors"
CONFIG_FILENAME = "config.yaml"


def main() -> int:
    """Report whether the local SF3D cache can proceed to runtime validation."""
    model_directory = _model_directory()
    config_path = model_directory / CONFIG_FILENAME
    weight_path = model_directory / MODEL_FILENAME
    requirements: list[dict[str, object]] = [
        _file_requirement("config", config_path),
        _file_requirement("weights", weight_path),
    ]
    dino_reference = _dino_reference(config_path)
    if dino_reference is not None:
        requirements.append(
            {
                "name": "DINOv2 image encoder",
                "status": "ACTION_REQUIRED",
                "configured_reference": dino_reference,
                "reason": (
                    "SF3D's upstream loader resolves this encoder separately; the app must "
                    "cache it locally and use an offline-only loader before real inference."
                ),
            }
        )

    missing_weights = not weight_path.is_file()
    result = {
        "status": "BLOCKED_BY_ENVIRONMENT" if missing_weights else "PENDING_RUNTIME_VALIDATION",
        "model_directory": str(model_directory),
        "requirements": requirements,
        "next_step": (
            "Download model.safetensors into the configured local cache."
            if missing_weights
            else "Install and validate the SF3D runtime with local-only model resolution."
        ),
    }
    print(json.dumps(result, ensure_ascii=False))
    return 2 if missing_weights else 0


def _model_directory() -> Path:
    configured = os.environ.get("CHARACTER_MODEL_STUDIO_SF3D_MODEL_DIR")
    if configured:
        return Path(configured)
    paths = resolve_application_paths()
    return paths.cache_directory / "sf3d" / "stable-fast-3d"


def _file_requirement(name: str, path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"name": name, "status": "MISSING", "path": str(path)}
    return {"name": name, "status": "READY", "path": str(path), "bytes": path.stat().st_size}


def _dino_reference(config_path: Path) -> str | None:
    if not config_path.is_file():
        return None
    match = re.search(
        r'^\s*pretrained_model_name_or_path:\s*["\']?([^"\'\s]+)',
        config_path.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    return match.group(1) if match else None


if __name__ == "__main__":
    raise SystemExit(main())
