"""Local-only resolution of heavyweight reconstruction model snapshots."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import scan_cache_dir

HUNYUAN3D_2_REPOSITORY = "tencent/Hunyuan3D-2"
HUNYUAN3D_2_SHAPE_SUBFOLDER = "hunyuan3d-dit-v2-0"
HUNYUAN3D_2_SHAPE_CONFIG = "config.yaml"
HUNYUAN3D_2_SHAPE_CHECKPOINT = "model.fp16.safetensors"


@dataclass(frozen=True, slots=True)
class ShapeModelSnapshot:
    """A locally available Hunyuan3D 2.0 Shape snapshot and its required artifacts."""

    snapshot_path: Path
    shape_model_path: Path
    config_path: Path
    checkpoint_path: Path


class LocalModelUnavailableError(RuntimeError):
    """Raised when a requested model has not been downloaded into the local cache."""


def resolve_hunyuan3d_2_shape_snapshot() -> ShapeModelSnapshot:
    """Resolve the configured local cache without permitting a network model download.

    An explicit snapshot directory may be supplied with
    ``CHARACTER_MODEL_STUDIO_HUNYUAN3D_2_SNAPSHOT``. Otherwise Hugging Face's local
    cache index is inspected directly. This permits a valid Shape-only partial snapshot
    without treating unrelated Texture files as a required repository download.
    """
    configured_snapshot = os.environ.get("CHARACTER_MODEL_STUDIO_HUNYUAN3D_2_SNAPSHOT")
    if configured_snapshot:
        snapshot_path = Path(configured_snapshot).expanduser()
    else:
        try:
            cache_info = scan_cache_dir()
            repository = next(
                (repo for repo in cache_info.repos if repo.repo_id == HUNYUAN3D_2_REPOSITORY),
                None,
            )
            if repository is None or not repository.revisions:
                raise LocalModelUnavailableError("Hunyuan3D 2.0 cache entry was not found")
            snapshot_path = Path(next(iter(repository.revisions)).snapshot_path)
        except (ImportError, OSError, ValueError) as error:
            raise LocalModelUnavailableError(
                "Hunyuan3D 2.0 Shape is not available in the configured local Hugging Face "
                "cache. Download its Shape files first; this application will not download weights "
                "during inference."
            ) from error
    shape_model_path = snapshot_path / HUNYUAN3D_2_SHAPE_SUBFOLDER
    snapshot = ShapeModelSnapshot(
        snapshot_path=snapshot_path,
        shape_model_path=shape_model_path,
        config_path=shape_model_path / HUNYUAN3D_2_SHAPE_CONFIG,
        checkpoint_path=shape_model_path / HUNYUAN3D_2_SHAPE_CHECKPOINT,
    )
    missing = [
        path.name for path in (snapshot.config_path, snapshot.checkpoint_path) if not path.is_file()
    ]
    if missing:
        raise LocalModelUnavailableError(
            "Hunyuan3D 2.0 Shape snapshot is incomplete; missing " + ", ".join(missing)
        )
    return snapshot
