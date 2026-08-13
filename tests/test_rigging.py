"""Rigging persistence and explicitly-labelled fixture coverage."""

from __future__ import annotations

from pygltflib import GLTF2

from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.reconstruction.mock import MockReconstructionProvider
from character_model_studio.rigging.providers.mock import MockRiggingProvider
from character_model_studio.rigging.providers.unirig import UniRigProvider
from character_model_studio.storage.database import initialize_database
from character_model_studio.storage.repositories import LocalRepository


def test_fixture_rig_has_skin_joints_and_normalized_vertex_weights(tmp_path) -> None:
    database = tmp_path / "app.sqlite3"
    initialize_database(database)
    repository = LocalRepository(database, tmp_path / "Projects")
    capture = repository.create_fixture_capture(repository.create_project("Fixture").id)
    attempt = repository.create_attempt(capture.id, "standard")
    MockReconstructionProvider().run(
        repository, attempt.id, CancellationToken(), progress=lambda _update: None
    )
    repository.decide(attempt.id, accepted=True)

    rig_id = MockRiggingProvider().run(repository, attempt.id)
    rig = repository.get_rig_attempt(rig_id)

    assert rig.provider == "fixture-rigging"
    assert rig.rigged_relative_path is not None
    gltf = GLTF2().load_binary(str(repository.projects_root / rig.rigged_relative_path))
    assert len(gltf.skins) == 1
    assert len(gltf.skins[0].joints) == 2
    primitive = gltf.meshes[0].primitives[0]
    assert primitive.attributes.JOINTS_0 is not None
    assert primitive.attributes.WEIGHTS_0 is not None


def test_unirig_probe_never_downloads_or_loads_weights() -> None:
    """The optional provider is a local readiness check, not an implicit network action."""
    readiness = UniRigProvider().probe()

    assert readiness.provider == "UniRig"
    assert readiness.status.value in {
        "READY",
        "NOT_INSTALLED",
        "VRAM_INELIGIBLE",
        "CUDA_UNAVAILABLE",
        "PROVIDER_RUNTIME_INCOMPATIBLE",
    }
