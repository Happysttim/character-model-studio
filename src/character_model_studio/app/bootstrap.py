"""Application composition that is safe to run before the first UI paint."""

from __future__ import annotations

from dataclasses import dataclass
from logging import Logger

from character_model_studio.common.logging import configure_logging
from character_model_studio.platform.windows.paths import (
    ApplicationPaths,
    resolve_application_paths,
)
from character_model_studio.storage.database import initialize_database


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """Runtime services created during desktop application startup."""

    paths: ApplicationPaths
    logger: Logger


def create_application_context() -> ApplicationContext:
    """Initialize local storage and logging without loading heavyweight providers."""
    paths = resolve_application_paths()
    paths.ensure_exists()
    logger = configure_logging(paths.logs_directory)
    initialize_database(paths.database_path)
    logger.info("Application context initialized")
    return ApplicationContext(paths=paths, logger=logger)
