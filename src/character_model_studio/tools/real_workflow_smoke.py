"""Real persisted Capture-to-Shape workflow smoke test using only local CUDA weights."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from character_model_studio.capture.recorder import PyAvH264Encoder
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.reconstruction.standard_workflow import StandardShapeWorkflow
from character_model_studio.storage.database import initialize_database
from character_model_studio.storage.repositories import LocalRepository


def _write_fixture_capture(path: Path) -> None:
    """Create a local non-personal MP4 accepted by the frame selector used for capture output."""
    frame = np.full((512, 512, 3), 245, dtype=np.uint8)
    frame[90:450, 205:307] = (68, 116, 205)
    frame[140:240, 165:347] = (68, 116, 205)
    encoder = PyAvH264Encoder(path, 512, 512, 12)
    for index in range(12):
        varied = frame.copy()
        varied[index * 8 : index * 8 + 8, :, :] = 180
        encoder.write(varied)
    encoder.close()


def main() -> int:
    """Run a real provider through project persistence and print non-sensitive result metadata."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    with TemporaryDirectory(prefix="cms-real-shape-") as temporary_directory:
        root = Path(temporary_directory)
        database_path = root / "studio.sqlite3"
        projects_root = root / "projects"
        initialize_database(database_path)
        repository = LocalRepository(database_path, projects_root)
        project = repository.create_project("CUDA Shape smoke")
        source_capture = root / "capture.mp4"
        _write_fixture_capture(source_capture)
        capture = repository.register_capture_file(project.id, source_capture)
        attempt = repository.create_attempt(
            capture.id,
            "standard",
            provider="Hunyuan3D 2.0",
            provider_version="2.0.2",
            parameters={"texture_stage": "disabled", "input_selection": "sharpest_sample"},
        )
        result_path = StandardShapeWorkflow().run(
            repository, attempt.id, CancellationToken(), lambda _update: None
        )
        completed = repository.get_attempt(attempt.id)
        persisted = completed.metrics or {}
        print(
            json.dumps(
                {
                    "status": completed.status.value,
                    "provider": completed.provider,
                    "provider_version": completed.provider_version,
                    "result_exists": result_path.is_file(),
                    "project_relative_model": completed.model_relative_path,
                    "metrics_persisted": bool(persisted),
                    "validation_status": repository.validation_status(attempt.id),
                    "vertex_count": persisted.get("vertex_count"),
                    "face_count": persisted.get("face_count"),
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
