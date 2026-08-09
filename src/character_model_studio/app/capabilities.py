"""Truthful CUDA, VRAM-tier, and provider-readiness evaluation."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from enum import StrEnum


class Capability(StrEnum):
    CUDA = "CUDA"
    STANDARD_SHAPE = "STANDARD_SHAPE"
    STANDARD_TEXTURED_PIPELINE = "STANDARD_TEXTURED_PIPELINE"
    HIGH_QUALITY_SHAPE = "HIGH_QUALITY_SHAPE"
    HIGH_QUALITY_TEXTURE = "HIGH_QUALITY_TEXTURE"
    HIGH_QUALITY_COMBINED_PIPELINE = "HIGH_QUALITY_COMBINED_PIPELINE"
    AUTO_RIGGING = "AUTO_RIGGING"
    SKELETON_EDITING = "SKELETON_EDITING"
    ANIMATION_EDITING = "ANIMATION_EDITING"
    ANIMATION_PLAYBACK = "ANIMATION_PLAYBACK"
    STANDARD_FULL_PRODUCT = "STANDARD_FULL_PRODUCT"
    HIGH_QUALITY_FULL_PRODUCT = "HIGH_QUALITY_FULL_PRODUCT"


class VramTier(StrEnum):
    NO_LOCAL_RECONSTRUCTION = "NO_LOCAL_RECONSTRUCTION"
    STANDARD_SHAPE = "STANDARD_SHAPE"
    STANDARD_SHAPE_PLUS_HQ_SHAPE_CANDIDATE = "STANDARD_SHAPE_PLUS_HQ_SHAPE_CANDIDATE"
    RIGGED_UNTEXTURED_STANDARD = "RIGGED_UNTEXTURED_STANDARD"
    STANDARD_FULL = "STANDARD_FULL"
    STANDARD_FULL_PLUS_HQ_SEQUENTIAL_CANDIDATE = "STANDARD_FULL_PLUS_HQ_SEQUENTIAL_CANDIDATE"
    HIGH_QUALITY_FULL = "HIGH_QUALITY_FULL"


class ReadinessStatus(StrEnum):
    READY = "READY"
    NOT_INSTALLED = "NOT_INSTALLED"
    VRAM_INELIGIBLE = "VRAM_INELIGIBLE"
    CUDA_UNAVAILABLE = "CUDA_UNAVAILABLE"
    PROVIDER_RUNTIME_INCOMPATIBLE = "PROVIDER_RUNTIME_INCOMPATIBLE"


@dataclass(frozen=True, slots=True)
class GpuSnapshot:
    cuda_available: bool
    device_name: str | None
    total_vram_bytes: int | None
    free_vram_bytes: int | None
    allocated_vram_bytes: int | None
    reserved_vram_bytes: int | None
    torch_version: str
    cuda_runtime: str | None


@dataclass(frozen=True, slots=True)
class ProviderReadiness:
    provider: str
    status: ReadinessStatus
    reason: str
    adapter_installed: bool
    vram_eligible: bool


@dataclass(frozen=True, slots=True)
class RuntimeCapabilities:
    gpu: GpuSnapshot
    tier: VramTier
    capabilities: frozenset[Capability]
    standard: ProviderReadiness
    high_quality: ProviderReadiness
    rigging: ProviderReadiness


GIB = 1024**3


def classify_vram(total_vram_bytes: int | None) -> VramTier:
    """Classify only total physical VRAM using the published product thresholds."""
    total_gib = 0 if total_vram_bytes is None else total_vram_bytes / GIB
    if total_gib < 6:
        return VramTier.NO_LOCAL_RECONSTRUCTION
    if total_gib < 10:
        return VramTier.STANDARD_SHAPE
    if total_gib < 14:
        return VramTier.STANDARD_SHAPE_PLUS_HQ_SHAPE_CANDIDATE
    if total_gib < 16:
        return VramTier.RIGGED_UNTEXTURED_STANDARD
    if total_gib < 21:
        return VramTier.STANDARD_FULL
    if total_gib < 29:
        return VramTier.STANDARD_FULL_PLUS_HQ_SEQUENTIAL_CANDIDATE
    return VramTier.HIGH_QUALITY_FULL


def probe_runtime() -> RuntimeCapabilities:
    """Perform a cheap startup probe without loading provider weights."""
    import torch

    cuda_available = torch.cuda.is_available()
    if cuda_available:
        properties = torch.cuda.get_device_properties(0)
        free, total = torch.cuda.mem_get_info(0)
        gpu = GpuSnapshot(
            True,
            properties.name,
            total,
            free,
            torch.cuda.memory_allocated(0),
            torch.cuda.memory_reserved(0),
            torch.__version__,
            torch.version.cuda,
        )
    else:
        gpu = GpuSnapshot(
            False, None, None, None, None, None, torch.__version__, torch.version.cuda
        )
    tier = classify_vram(gpu.total_vram_bytes)
    capability_set = _capabilities(gpu.cuda_available, tier)
    return RuntimeCapabilities(
        gpu,
        tier,
        capability_set,
        _provider_readiness(
            "Hunyuan3D 2.0", "hunyuan3d", Capability.STANDARD_SHAPE, capability_set
        ),
        _provider_readiness(
            "Hunyuan3D 2.1", "hunyuan3d_2_1", Capability.HIGH_QUALITY_SHAPE, capability_set
        ),
        _provider_readiness(
            "SkinTokens / TokenRig", "skintokens", Capability.AUTO_RIGGING, capability_set
        ),
    )


def _capabilities(cuda_available: bool, tier: VramTier) -> frozenset[Capability]:
    capabilities = {
        Capability.SKELETON_EDITING,
        Capability.ANIMATION_EDITING,
        Capability.ANIMATION_PLAYBACK,
    }
    if not cuda_available:
        return frozenset(capabilities)
    capabilities.add(Capability.CUDA)
    if tier is not VramTier.NO_LOCAL_RECONSTRUCTION:
        capabilities.add(Capability.STANDARD_SHAPE)
    if tier in {
        VramTier.RIGGED_UNTEXTURED_STANDARD,
        VramTier.STANDARD_FULL,
        VramTier.STANDARD_FULL_PLUS_HQ_SEQUENTIAL_CANDIDATE,
        VramTier.HIGH_QUALITY_FULL,
    }:
        capabilities.add(Capability.AUTO_RIGGING)
    if tier in {
        VramTier.STANDARD_FULL,
        VramTier.STANDARD_FULL_PLUS_HQ_SEQUENTIAL_CANDIDATE,
        VramTier.HIGH_QUALITY_FULL,
    }:
        capabilities.update(
            {Capability.STANDARD_TEXTURED_PIPELINE, Capability.STANDARD_FULL_PRODUCT}
        )
    if tier in {
        VramTier.STANDARD_SHAPE_PLUS_HQ_SHAPE_CANDIDATE,
        VramTier.RIGGED_UNTEXTURED_STANDARD,
        VramTier.STANDARD_FULL,
        VramTier.STANDARD_FULL_PLUS_HQ_SEQUENTIAL_CANDIDATE,
        VramTier.HIGH_QUALITY_FULL,
    }:
        capabilities.add(Capability.HIGH_QUALITY_SHAPE)
    if tier in {VramTier.STANDARD_FULL_PLUS_HQ_SEQUENTIAL_CANDIDATE, VramTier.HIGH_QUALITY_FULL}:
        capabilities.add(Capability.HIGH_QUALITY_TEXTURE)
    if tier is VramTier.HIGH_QUALITY_FULL:
        capabilities.update(
            {Capability.HIGH_QUALITY_COMBINED_PIPELINE, Capability.HIGH_QUALITY_FULL_PRODUCT}
        )
    return frozenset(capabilities)


def _provider_readiness(
    provider: str, module: str, required_capability: Capability, capabilities: frozenset[Capability]
) -> ProviderReadiness:
    installed = importlib.util.find_spec(module) is not None
    vram_eligible = required_capability in capabilities
    if Capability.CUDA not in capabilities:
        return ProviderReadiness(
            provider, ReadinessStatus.CUDA_UNAVAILABLE, "CUDA is unavailable", installed, False
        )
    if not vram_eligible:
        return ProviderReadiness(
            provider,
            ReadinessStatus.VRAM_INELIGIBLE,
            "Total physical VRAM is below this provider lane",
            installed,
            False,
        )
    if not installed:
        return ProviderReadiness(
            provider,
            ReadinessStatus.NOT_INSTALLED,
            "Provider adapter and weights are not installed",
            False,
            True,
        )
    return ProviderReadiness(
        provider,
        ReadinessStatus.PROVIDER_RUNTIME_INCOMPATIBLE,
        "Provider adapter discovery succeeded; initialization smoke test is not implemented",
        True,
        True,
    )
