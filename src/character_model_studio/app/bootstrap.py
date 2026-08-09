"""Application composition that is safe to run before the first UI paint."""

from __future__ import annotations

import os
from dataclasses import dataclass
from logging import Logger

from character_model_studio.app.capabilities import RuntimeCapabilities, probe_runtime
from character_model_studio.common.logging import configure_logging
from character_model_studio.platform.windows.paths import (
    ApplicationPaths,
    resolve_application_paths,
)
from character_model_studio.storage.database import initialize_database
from character_model_studio.storage.repositories import LocalRepository


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """Runtime services created during desktop application startup."""

    paths: ApplicationPaths
    logger: Logger
    runtime: RuntimeCapabilities | None = None
    repository: LocalRepository | None = None


def create_application_context() -> ApplicationContext:
    """Initialize local storage and logging without loading heavyweight providers."""
    paths = resolve_application_paths()
    paths.ensure_exists()
    hunyuan_cache = paths.cache_directory / "hunyuan3d-2"
    huggingface_cache = paths.cache_directory / "huggingface"
    segmentation_cache = paths.cache_directory / "segmentation" / "rembg"
    hunyuan_cache.mkdir(parents=True, exist_ok=True)
    huggingface_cache.mkdir(parents=True, exist_ok=True)
    segmentation_cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HY3DGEN_MODELS", str(hunyuan_cache))
    os.environ.setdefault("HF_HOME", str(huggingface_cache))
    os.environ.setdefault("U2NET_HOME", str(segmentation_cache))
    logger = configure_logging(paths.logs_directory)
    initialize_database(paths.database_path)
    repository = LocalRepository(paths.database_path, paths.projects_directory)
    recovered_attempts = repository.recover_interrupted_attempts()
    runtime = probe_runtime()
    logger.info("Application context initialized; recovered_attempts=%s", recovered_attempts)
    return ApplicationContext(paths=paths, logger=logger, runtime=runtime, repository=repository)
