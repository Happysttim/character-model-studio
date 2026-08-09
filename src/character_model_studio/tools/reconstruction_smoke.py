"""Offline-only real CUDA Hunyuan3D 2.0 Shape reconstruction smoke test."""

from __future__ import annotations

import gc
import json
import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import torch
from PIL import Image, ImageDraw

from character_model_studio.app.capabilities import Capability, probe_runtime
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.reconstruction.model_paths import resolve_hunyuan3d_2_shape_snapshot
from character_model_studio.reconstruction.providers.hunyuan2 import Hunyuan3D20Provider
from character_model_studio.validation.model import ModelValidator
from character_model_studio.viewer.scene import load_glb_model


def _gpu_memory(device: torch.device) -> dict[str, int]:
    free, total = torch.cuda.mem_get_info(device)
    return {
        "free_bytes": free,
        "total_bytes": total,
        "allocated_bytes": torch.cuda.memory_allocated(device),
        "reserved_bytes": torch.cuda.memory_reserved(device),
    }


def _create_input(path: Path) -> None:
    """Create a local neutral RGBA subject image; no user content is collected."""
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    subject = (205, 116, 68, 255)
    draw.ellipse((184, 72, 328, 216), fill=subject)
    draw.rounded_rectangle((164, 198, 348, 430), radius=66, fill=subject)
    draw.polygon(((164, 230), (88, 356), (150, 382), (210, 274)), fill=subject)
    draw.polygon(((348, 230), (424, 356), (362, 382), (302, 274)), fill=subject)
    draw.rectangle((190, 408, 242, 480), fill=subject)
    draw.rectangle((270, 408, 322, 480), fill=subject)
    image.save(path)


def _parameter_devices(provider: Hunyuan3D20Provider) -> dict[str, str]:
    pipeline: Any = provider._pipeline
    return {
        component: str(next(getattr(pipeline, component).parameters()).device)
        for component in ("model", "vae", "conditioner")
    }


def main() -> int:
    """Run one actual CUDA inference and emit only structured diagnostics."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    runtime = probe_runtime()
    if not runtime.gpu.cuda_available:
        print(json.dumps({"status": "BLOCKED_BY_ENVIRONMENT", "reason": "CUDA is unavailable"}))
        return 2
    if Capability.STANDARD_SHAPE not in runtime.capabilities:
        print(
            json.dumps(
                {"status": "BLOCKED_BY_ENVIRONMENT", "reason": "Standard Shape is VRAM-ineligible"}
            )
        )
        return 2

    device = torch.device("cuda:0")
    snapshot = resolve_hunyuan3d_2_shape_snapshot()
    output_root = Path(os.environ.get("CHARACTER_MODEL_STUDIO_DATA_DIR", ".local")) / "smoke"
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / "hunyuan3d-2-shape-smoke.glb"
    report_path = output_root / "hunyuan3d-2-shape-smoke.json"
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)
    before_load = _gpu_memory(device)
    provider = Hunyuan3D20Provider()
    started = time.perf_counter()
    result: dict[str, Any]
    try:
        provider.load()
        after_load = _gpu_memory(device)
        parameter_devices = _parameter_devices(provider)
        if any(not value.startswith("cuda:") for value in parameter_devices.values()):
            raise RuntimeError("Hunyuan3D Shape parameters are not resident on CUDA")
        with TemporaryDirectory(prefix="cms-hunyuan-shape-") as temporary_directory:
            input_path = Path(temporary_directory) / "shape-input.png"
            _create_input(input_path)
            provider.generate_shape([input_path], output_path, CancellationToken())
        torch.cuda.synchronize(device)
        inference_seconds = time.perf_counter() - started
        peak = {
            "allocated_bytes": torch.cuda.max_memory_allocated(device),
            "reserved_bytes": torch.cuda.max_memory_reserved(device),
        }
        validation = ModelValidator().validate(output_path)
        viewer = load_glb_model(output_path)
        result = {
            "status": "PASS" if validation.overall_status != "FAIL" else "FAIL",
            "provider": provider.name,
            "provider_version": provider.version,
            "quality_mode": "standard",
            "operation": "shape_reconstruction",
            "device": str(device),
            "gpu_name": runtime.gpu.device_name,
            "total_vram_bytes": runtime.gpu.total_vram_bytes,
            "snapshot_path": str(snapshot.snapshot_path),
            "checkpoint_path": str(snapshot.checkpoint_path),
            "before_load": before_load,
            "after_load": after_load,
            "parameter_devices": parameter_devices,
            "peak_vram": peak,
            "reconstruction_seconds": inference_seconds,
            "asset_path": str(output_path),
            "vertex_count": viewer.vertex_count,
            "face_count": viewer.face_count,
            "validation": validation.as_dict(),
            "viewer_load": "PASS",
        }
    except (OSError, RuntimeError, ValueError) as error:
        result = {
            "status": "FAIL",
            "provider": provider.name,
            "provider_version": provider.version,
            "quality_mode": "standard",
            "operation": "shape_reconstruction",
            "device": str(device),
            "error": str(error),
        }
    finally:
        provider.unload()
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.synchronize(device)
    result["after_unload"] = _gpu_memory(device)
    result["telemetry_path"] = str(report_path)
    report_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, default=str))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
