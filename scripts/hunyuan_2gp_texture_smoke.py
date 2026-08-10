"""Run local-only, sequential-CUDA Hunyuan3D-Paint texture inference on a GLB."""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse existing shape mesh, local RGBA reference and output locations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mesh", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model-cache", type=Path, required=True)
    return parser.parse_args()


def memory_snapshot(torch: object) -> dict[str, int]:
    """Record CUDA allocator and device-memory facts."""
    cuda = torch.cuda
    free, total = cuda.mem_get_info(0)
    return {
        "free_bytes": int(free),
        "total_bytes": int(total),
        "allocated_bytes": int(cuda.memory_allocated(0)),
        "reserved_bytes": int(cuda.memory_reserved(0)),
    }


def parameter_devices(pipeline: object) -> list[str]:
    """Collect the parameter device set of a loaded diffusion pipeline."""
    return sorted(
        {
            str(parameter.device)
            for parameter in pipeline.components.values()
            if hasattr(parameter, "parameters")
            for parameter in parameter.parameters()
        }
    )


def require_cuda_parameters(name: str, pipeline: object) -> None:
    """Reject a stage unless every tracked model parameter is resident on CUDA."""
    devices = parameter_devices(pipeline)
    if not devices or any(not device.startswith("cuda:") for device in devices):
        raise RuntimeError(f"{name} is not resident entirely on CUDA: {devices}")


def main() -> None:
    """Texture a local mesh by loading Delight and Paint sequentially onto CUDA."""
    args = parse_args()
    required_directories = (
        args.model_cache / "tencent" / "Hunyuan3D-2" / "hunyuan3d-delight-v2-0",
        args.model_cache / "tencent" / "Hunyuan3D-2" / "hunyuan3d-paint-v2-0",
    )
    if not args.mesh.is_file() or not args.reference.is_file():
        raise FileNotFoundError("The local Shape GLB and RGBA reference image must both exist")
    if any(not directory.is_dir() for directory in required_directories):
        raise FileNotFoundError("The local Hunyuan Paint or Delight checkpoint is missing")

    os.environ["HY3DGEN_MODELS"] = str(args.model_cache.resolve())
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_MODULES_CACHE"] = str((args.model_cache / "modules").resolve())

    import torch

    torch_lib = Path(torch.__file__).parent / "lib"
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(torch_lib))
    import trimesh
    from hy3dgen.texgen import Hunyuan3DPaintPipeline
    from hy3dgen.texgen.utils.uv_warp_utils import mesh_uv_wrap
    from PIL import Image

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required; Texture will not use a CPU fallback")
    torch.cuda.set_device(0)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(0)
    before_load = memory_snapshot(torch)
    started = time.perf_counter()

    texture_pipeline = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
    delight = texture_pipeline.models["delight_model"]
    paint = texture_pipeline.models["multiview_model"]
    delight.device = "cuda:0"
    paint.device = "cuda:0"
    input_image = Image.open(args.reference).convert("RGBA")
    mesh = trimesh.load(args.mesh, force="mesh")

    delight.pipeline.to("cuda:0")
    require_cuda_parameters("Delight", delight.pipeline)
    image_prompt = texture_pipeline.recenter_image(input_image)
    image_prompt = delight(image_prompt)
    delight.pipeline.to("cpu")
    torch.cuda.empty_cache()
    after_delight = memory_snapshot(torch)

    mesh = mesh_uv_wrap(mesh)
    texture_pipeline.render.load_mesh(mesh)
    elevations = texture_pipeline.config.candidate_camera_elevs
    azimuths = texture_pipeline.config.candidate_camera_azims
    weights = texture_pipeline.config.candidate_view_weights
    normal_maps = texture_pipeline.render_normal_multiview(elevations, azimuths, use_abs_coor=True)
    position_maps = texture_pipeline.render_position_multiview(elevations, azimuths)
    camera_info = [
        (((azimuth // 30) + 9) % 12) // {-20: 1, 0: 1, 20: 1, -90: 3, 90: 3}[elevation]
        + {-20: 0, 0: 12, 20: 24, -90: 36, 90: 40}[elevation]
        for azimuth, elevation in zip(azimuths, elevations, strict=True)
    ]

    paint.pipeline.to("cuda:0")
    require_cuda_parameters("Paint", paint.pipeline)
    multiviews = paint(image_prompt, normal_maps + position_maps, camera_info)
    paint.pipeline.to("cpu")
    torch.cuda.empty_cache()
    after_paint = memory_snapshot(torch)

    render_size = texture_pipeline.config.render_size
    multiviews = [image.resize((render_size, render_size)) for image in multiviews]
    texture, mask = texture_pipeline.bake_from_multiview(
        multiviews, elevations, azimuths, weights, method=texture_pipeline.config.merge_method
    )
    mask_np = (mask.squeeze(-1).cpu().numpy() * 255).astype("uint8")
    texture = texture_pipeline.texture_inpaint(texture, mask_np)
    texture_pipeline.render.set_texture(texture)
    textured_mesh = texture_pipeline.render.save_mesh()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    textured_mesh.export(args.output)
    elapsed_seconds = time.perf_counter() - started
    peak = {
        "allocated_bytes": int(torch.cuda.max_memory_allocated(0)),
        "reserved_bytes": int(torch.cuda.max_memory_reserved(0)),
    }

    del textured_mesh
    del texture_pipeline
    gc.collect()
    torch.cuda.empty_cache()
    after_unload = memory_snapshot(torch)
    loaded = trimesh.load(args.output, force="mesh")
    texture_present = bool(
        loaded.visual.kind == "texture"
        and getattr(loaded.visual, "uv", None) is not None
        and getattr(loaded.visual.material, "baseColorTexture", None) is not None
    )
    report = {
        "provider": "Hunyuan3D-2GP / Hunyuan3D-Paint Texture",
        "cuda_device": "cuda:0",
        "gpu": torch.cuda.get_device_name(0),
        "local_files_only": True,
        "mesh": str(args.mesh.resolve()),
        "reference": str(args.reference.resolve()),
        "before_load": before_load,
        "after_delight": after_delight,
        "after_paint": after_paint,
        "peak": peak,
        "after_unload": after_unload,
        "elapsed_seconds": elapsed_seconds,
        "vertices": int(len(loaded.vertices)),
        "faces": int(len(loaded.faces)),
        "base_color_texture": texture_present,
        "output": str(args.output.resolve()),
    }
    report_path = args.output.with_suffix(".json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
