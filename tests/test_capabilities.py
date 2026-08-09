"""Pure policy tests for independent total-VRAM capability classification."""

from __future__ import annotations

from character_model_studio.app.capabilities import (
    Capability,
    VramTier,
    _capabilities,
    classify_vram,
)
from character_model_studio.app.heavyweight_lane import HeavyweightTaskLane

GIB = 1024**3


def test_vram_tiers_use_total_physical_memory_boundaries() -> None:
    assert classify_vram(5 * GIB) is VramTier.NO_LOCAL_RECONSTRUCTION
    assert classify_vram(6 * GIB) is VramTier.STANDARD_SHAPE
    assert classify_vram(10 * GIB) is VramTier.STANDARD_SHAPE_PLUS_HQ_SHAPE_CANDIDATE
    assert classify_vram(14 * GIB) is VramTier.RIGGED_UNTEXTURED_STANDARD
    assert classify_vram(16 * GIB) is VramTier.STANDARD_FULL
    assert classify_vram(21 * GIB) is VramTier.STANDARD_FULL_PLUS_HQ_SEQUENTIAL_CANDIDATE
    assert classify_vram(29 * GIB) is VramTier.HIGH_QUALITY_FULL


def test_editor_capabilities_do_not_depend_on_cuda() -> None:
    capabilities = _capabilities(False, VramTier.NO_LOCAL_RECONSTRUCTION)

    assert Capability.CUDA not in capabilities
    assert Capability.STANDARD_SHAPE not in capabilities
    assert Capability.SKELETON_EDITING in capabilities
    assert Capability.ANIMATION_EDITING in capabilities
    assert Capability.ANIMATION_PLAYBACK in capabilities


def test_high_quality_combined_requires_its_own_vram_tier() -> None:
    sequential = _capabilities(True, VramTier.STANDARD_FULL_PLUS_HQ_SEQUENTIAL_CANDIDATE)
    full = _capabilities(True, VramTier.HIGH_QUALITY_FULL)

    assert Capability.HIGH_QUALITY_TEXTURE in sequential
    assert Capability.HIGH_QUALITY_COMBINED_PIPELINE not in sequential
    assert Capability.HIGH_QUALITY_COMBINED_PIPELINE in full


def test_heavyweight_lane_unloads_before_the_next_owner() -> None:
    events: list[str] = []
    lane = HeavyweightTaskLane()

    first = lane.run(
        lambda: events.append("load-a"), lambda: "a", lambda: events.append("unload-a")
    )
    second = lane.run(
        lambda: events.append("load-b"), lambda: "b", lambda: events.append("unload-b")
    )

    assert (first, second) == ("a", "b")
    assert events == ["load-a", "unload-a", "load-b", "unload-b"]
