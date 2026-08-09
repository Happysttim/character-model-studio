"""Persisted local Capture-to-textured-GLB SF3D workflow smoke test."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory

from character_model_studio.app.bootstrap import create_application_context
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.reconstruction.standard_workflow import StandardShapeWorkflow
from character_model_studio.storage.database import initialize_database
from character_model_studio.storage.repositories import LocalRepository
from character_model_studio.tools.real_workflow_smoke import _write_fixture_capture


def main() -> int:
    """Verify an SF3D attempt persists a textured GLB and validation report locally."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture")
    parser.add_argument("--output")
    arguments = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    create_application_context()
    with TemporaryDirectory(prefix="cms-sf3d-workflow-") as temporary_directory:
        root = Path(temporary_directory)
        database_path = root / "studio.sqlite3"
        projects_root = root / "projects"
        initialize_database(database_path)
        repository = LocalRepository(database_path, projects_root)
        project = repository.create_project("CUDA textured smoke")
        source_capture = Path(arguments.capture) if arguments.capture else root / "capture.mp4"
        if not arguments.capture:
            _write_fixture_capture(source_capture)
        capture = repository.register_capture_file(project.id, source_capture)
        attempt = repository.create_attempt(
            capture.id,
            "experimental_textured",
            provider="Stable Fast 3D",
            provider_version="upstream-local-experimental",
            parameters={"texture_stage": "generated", "input_selection": "sharpest_sample"},
        )
        result_path = StandardShapeWorkflow().run(
            repository, attempt.id, CancellationToken(), lambda _update: None
        )
        if arguments.output:
            output = Path(arguments.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            copy2(result_path, output)
        completed = repository.get_attempt(attempt.id)
        persisted = completed.metrics or {}
        print(
            json.dumps(
                {
                    "status": completed.status.value,
                    "provider": completed.provider,
                    "result_exists": result_path.is_file(),
                    "project_relative_model": completed.model_relative_path,
                    "metrics_persisted": bool(persisted),
                    "validation_status": repository.validation_status(attempt.id),
                    "texture_stage": persisted.get("texture_stage"),
                    "vertex_count": persisted.get("vertex_count"),
                    "face_count": persisted.get("face_count"),
                    "export_path": str(Path(arguments.output)) if arguments.output else None,
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
