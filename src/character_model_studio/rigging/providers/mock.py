"""Fixture-only rigging provider for the local mock workflow."""

from __future__ import annotations

from character_model_studio.storage.repositories import LocalRepository


class MockRiggingProvider:
    """Publish a fixture rigged GLB through the application-facing rigging contract."""

    def run(self, repository: LocalRepository, accepted_attempt_id: str) -> str:
        """Create a fixture rig result only for an accepted model attempt."""
        return repository.create_mock_rig(accepted_attempt_id)
