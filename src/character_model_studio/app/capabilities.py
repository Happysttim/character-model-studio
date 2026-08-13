"""Truthful CUDA, VRAM-tier, and provider-readiness evaluation."""

from __future__ import annotations

import importlib.util
import importlib.metadata
import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Capability(StrEnum):
    CUDA = "CUDA"
    CHARACTER_SEGMENTATION = "CHARACTER_SEGMENTATION"
    STANDARD_SHAPE = "STANDARD_SHAPE"
    STANDARD_TEXTURED_PIPELINE = "STANDARD_TEXTURED_PIPELINE"
    EXPERIMENTAL_SF3D_TEXTURED_PIPELINE = "EXPERIMENTAL_SF3D_TEXTURED_PIPELINE"
    EXPERIMENTAL_HUNYUAN2GP_TEXTURED_PIPELINE = "EXPERIMENTAL_HUNYUAN2GP_TEXTURED_PIPELINE"
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
    segmentation: ProviderReadiness
    sf3d: ProviderReadiness
    hunyuan2gp: ProviderReadiness
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
    standard = _standard_provider_readiness(capability_set)
    segmentation = _segmentation_provider_readiness(capability_set)
    sf3d = _sf3d_provider_readiness(gpu, capability_set)
    hunyuan2gp = _hunyuan2gp_provider_readiness(gpu)
    if segmentation.status is ReadinessStatus.READY:
        capability_set = frozenset({*capability_set, Capability.CHARACTER_SEGMENTATION})
    if sf3d.status is ReadinessStatus.READY:
        capability_set = frozenset(
            {*capability_set, Capability.EXPERIMENTAL_SF3D_TEXTURED_PIPELINE}
        )
    if hunyuan2gp.status is ReadinessStatus.READY:
        capability_set = frozenset(
            {*capability_set, Capability.EXPERIMENTAL_HUNYUAN2GP_TEXTURED_PIPELINE}
        )
    return RuntimeCapabilities(
        gpu,
        tier,
        capability_set,
        standard,
        segmentation,
        sf3d,
        hunyuan2gp,
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


def _standard_provider_readiness(capabilities: frozenset[Capability]) -> ProviderReadiness:
    """Check Hunyuan 2.0 adapter and local Shape artifacts without loading its weights."""
    readiness = _provider_readiness(
        "Hunyuan3D 2.0", "hy3dgen", Capability.STANDARD_SHAPE, capabilities
    )
    if readiness.status is not ReadinessStatus.PROVIDER_RUNTIME_INCOMPATIBLE:
        return readiness
    try:
        from character_model_studio.reconstruction.model_paths import (
            LocalModelUnavailableError,
            resolve_hunyuan3d_2_shape_snapshot,
        )

        resolve_hunyuan3d_2_shape_snapshot()
    except LocalModelUnavailableError as error:
        return ProviderReadiness(
            "Hunyuan3D 2.0",
            ReadinessStatus.PROVIDER_RUNTIME_INCOMPATIBLE,
            str(error),
            True,
            True,
        )
    return ProviderReadiness(
        "Hunyuan3D 2.0",
        ReadinessStatus.READY,
        "Local Shape checkpoint is ready; weights remain lazy-loaded until reconstruction starts",
        True,
        True,
    )


def _segmentation_provider_readiness(
    capabilities: frozenset[Capability],
) -> ProviderReadiness:
    """Check local rembg model/CUDA provider availability without loading the model."""
    provider_name = "rembg isnet-anime"
    installed = (
        importlib.util.find_spec("rembg") is not None
        and importlib.util.find_spec("onnxruntime") is not None
    )
    if Capability.CUDA not in capabilities:
        return ProviderReadiness(
            provider_name,
            ReadinessStatus.CUDA_UNAVAILABLE,
            "CUDA is unavailable; background isolation will not fall back to CPU",
            installed,
            False,
        )
    if not installed:
        return ProviderReadiness(
            provider_name,
            ReadinessStatus.NOT_INSTALLED,
            "Install rembg[gpu] and onnxruntime-gpu to enable local background isolation",
            False,
            True,
        )
    try:
        import onnxruntime as ort

        if "CUDAExecutionProvider" not in ort.get_available_providers():
            return ProviderReadiness(
                provider_name,
                ReadinessStatus.PROVIDER_RUNTIME_INCOMPATIBLE,
                "ONNX Runtime CUDAExecutionProvider is unavailable",
                True,
                True,
            )
    except (ImportError, OSError, RuntimeError) as error:
        return ProviderReadiness(
            provider_name,
            ReadinessStatus.PROVIDER_RUNTIME_INCOMPATIBLE,
            f"ONNX Runtime could not report CUDA support: {error}",
            True,
            True,
        )
    model_name = os.environ.get("CHARACTER_MODEL_STUDIO_SEGMENTATION_MODEL", "isnet-anime")
    cache_directory = os.environ.get("U2NET_HOME")
    model_path = Path(cache_directory) / f"{model_name}.onnx" if cache_directory else None
    if model_path is None or not model_path.is_file():
        return ProviderReadiness(
            provider_name,
            ReadinessStatus.NOT_INSTALLED,
            "The selected local segmentation model has not been downloaded",
            True,
            True,
        )
    return ProviderReadiness(
        provider_name,
        ReadinessStatus.READY,
        "Local isnet-anime model and ONNX Runtime CUDA provider are ready",
        True,
        True,
    )


def _sf3d_provider_readiness(
    gpu: GpuSnapshot, capabilities: frozenset[Capability]
) -> ProviderReadiness:
    """Check the explicit local SF3D cache and compiled extensions without loading weights."""
    name = "Stable Fast 3D (Experimental)"
    if Capability.CUDA not in capabilities:
        return ProviderReadiness(
            name, ReadinessStatus.CUDA_UNAVAILABLE, "CUDA is unavailable", False, False
        )
    minimum = 6 * GIB
    eligible = gpu.total_vram_bytes is not None and gpu.total_vram_bytes >= minimum
    if not eligible:
        return ProviderReadiness(
            name,
            ReadinessStatus.VRAM_INELIGIBLE,
            "Total physical VRAM is below the validated SF3D lane",
            False,
            False,
        )
    paths = _sf3d_paths()
    required = (
        paths[0] / "config.yaml",
        paths[0] / "model.safetensors",
        paths[1] / "config.json",
        paths[1] / "model.safetensors",
        paths[2] / "sf3d" / "system.py",
    )
    extensions = all(
        importlib.util.find_spec(module) is not None
        for module in ("texture_baker", "uv_unwrapper", "open_clip", "jaxtyping")
    )
    missing = [path.name for path in required if not path.is_file()]
    if missing or not extensions:
        detail = (
            "missing local artifacts: " + ", ".join(missing)
            if missing
            else "SF3D native runtime extensions are not installed"
        )
        return ProviderReadiness(name, ReadinessStatus.NOT_INSTALLED, detail, False, True)
    return ProviderReadiness(
        name,
        ReadinessStatus.READY,
        "Local SF3D, DINO, CLIP cache and native extensions are ready",
        True,
        True,
    )


def _sf3d_paths() -> tuple[Path, Path, Path]:
    from character_model_studio.platform.windows.paths import resolve_application_paths

    cache = resolve_application_paths().cache_directory / "sf3d"
    root = Path(__file__).resolve().parents[3]
    return (
        Path(os.environ.get("CHARACTER_MODEL_STUDIO_SF3D_MODEL_DIR", cache / "stable-fast-3d")),
        Path(os.environ.get("CHARACTER_MODEL_STUDIO_SF3D_DINO_DIR", cache / "dinov2-large")),
        Path(
            os.environ.get(
                "CHARACTER_MODEL_STUDIO_SF3D_SOURCE_DIR", root / "external" / "StableFast3D"
            )
        ),
    )


def _hunyuan2gp_provider_readiness(gpu: GpuSnapshot) -> ProviderReadiness:
    """Verify the isolated experimental runtime without importing or loading weights.

    Hunyuan3D-2GP upstream pins Transformers 4.49.  The desktop application's
    shared runtime is intentionally not downgraded during a readiness probe:
    doing that could destabilize the existing provider lanes.  The selection is
    therefore disabled until a compatible, tested runtime is configured.
    """
    name = "Hunyuan3D-2GP (Experimental Multi-view)"
    if not gpu.cuda_available:
        return ProviderReadiness(
            name, ReadinessStatus.CUDA_UNAVAILABLE, "CUDA is unavailable", False, False
        )
    from character_model_studio.reconstruction.hunyuan2gp_paths import resolve_hunyuan2gp_paths

    paths = resolve_hunyuan2gp_paths()
    required = (
        paths.source_directory / "hy3dgen" / "shapegen" / "__init__.py",
        paths.shape_directory / "config.yaml",
        paths.shape_directory / "model.fp16.safetensors",
        paths.delight_directory / "model_index.json",
        paths.paint_directory / "model_index.json",
        paths.paint_directory / "unet" / "diffusion_pytorch_model.bin",
    )
    missing = [
        str(path.relative_to(paths.model_cache))
        if path.is_relative_to(paths.model_cache)
        else path.name
        for path in required
        if not path.is_file()
    ]
    if missing:
        return ProviderReadiness(
            name,
            ReadinessStatus.NOT_INSTALLED,
            "Missing local 2GP artifacts: " + ", ".join(missing),
            False,
            True,
        )
    try:
        transformers_version = importlib.metadata.version("transformers")
    except importlib.metadata.PackageNotFoundError:
        return ProviderReadiness(
            name, ReadinessStatus.NOT_INSTALLED, "Transformers is not installed", False, True
        )
    if transformers_version != "4.49.0":
        return ProviderReadiness(
            name,
            ReadinessStatus.PROVIDER_RUNTIME_INCOMPATIBLE,
            f"Hunyuan3D-2GP requires Transformers 4.49.0; active runtime has {transformers_version}. No dependency was changed automatically.",
            True,
            True,
        )
    extensions = all(
        importlib.util.find_spec(module) is not None
        for module in ("mesh_processor", "custom_rasterizer_kernel")
    )
    if not extensions:
        return ProviderReadiness(
            name,
            ReadinessStatus.NOT_INSTALLED,
            "Hunyuan3D-2GP native extensions are not installed in the active Python runtime",
            True,
            True,
        )
    return ProviderReadiness(
        name,
        ReadinessStatus.READY,
        "Local multi-view Shape, Delight, Paint and native extensions are ready",
        True,
        True,
    )
