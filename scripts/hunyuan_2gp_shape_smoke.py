"""Run a local-only CUDA Hunyuan3D-2mv shape inference and export a GLB."""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse configured local model/input/output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs", type=Path, help="Directory containing front/left/back/right PNG inputs"
    )
    parser.add_argument("output", type=Path)
    parser.add_argument("--model-cache", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--octree-resolution", type=int, default=384)
    parser.add_argument("--num-chunks", type=int, default=8000)
    parser.add_argument("--seed", type=int, default=12345)
    return parser.parse_args()


def memory_snapshot(torch: object) -> dict[str, int]:
    """Return CUDA allocator and device-memory facts without relying on a fixed GPU model."""
    cuda = torch.cuda
    free, total = cuda.mem_get_info(0)
    return {
        "free_bytes": int(free),
        "total_bytes": int(total),
        "allocated_bytes": int(cuda.memory_allocated(0)),
        "reserved_bytes": int(cuda.memory_reserved(0)),
    }


def main() -> None:
    """Run an actual CUDA-only multiview mesh generation from existing local files."""
    args = parse_args()
    model_directory = args.model_cache / "tencent" / "Hunyuan3D-2mv" / "hunyuan3d-dit-v2-mv"
    required = (model_directory / "config.yaml", model_directory / "model.fp16.safetensors")
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required local model files are missing: {missing}")

    os.environ["HY3DGEN_MODELS"] = str(args.model_cache.resolve())
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    import torch
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
    from PIL import Image

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required; CPU fallback is prohibited")
    torch.cuda.set_device(0)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(0)
    before_load = memory_snapshot(torch)
    device_name = torch.cuda.get_device_name(0)

    images = {}
    input_paths: dict[str, str] = {}
    for name in ("front", "left", "back", "right"):
        path = args.inputs / f"{name}.png"
        if path.is_file():
            images[name] = Image.open(path).convert("RGBA")
            input_paths[name] = str(path.resolve())
    if len(images) < 3:
        raise ValueError("At least three local multiview PNG inputs are required")

    started = time.perf_counter()
    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        "tencent/Hunyuan3D-2mv",
        subfolder="hunyuan3d-dit-v2-mv",
        variant="fp16",
        device="cuda:0",
    )
    after_load = memory_snapshot(torch)
    parameter_devices = sorted({str(parameter.device) for parameter in pipeline.model.parameters()})
    if parameter_devices != ["cuda:0"]:
        raise RuntimeError(f"Shape model parameters are not CUDA-only: {parameter_devices}")

    mesh = pipeline(
        image=images,
        num_inference_steps=args.steps,
        octree_resolution=args.octree_resolution,
        num_chunks=args.num_chunks,
        generator=torch.manual_seed(args.seed),
        output_type="trimesh",
    )[0]
    if not len(mesh.vertices) or not len(mesh.faces):
        raise RuntimeError("CUDA inference returned an empty mesh")
    vertex_count = int(len(mesh.vertices))
    face_count = int(len(mesh.faces))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(args.output)
    peak = {
        "allocated_bytes": int(torch.cuda.max_memory_allocated(0)),
        "reserved_bytes": int(torch.cuda.max_memory_reserved(0)),
    }
    elapsed_seconds = time.perf_counter() - started

    del mesh
    del pipeline
    gc.collect()
    torch.cuda.empty_cache()
    after_unload = memory_snapshot(torch)
    report = {
        "provider": "Hunyuan3D-2GP / Hunyuan3D-2mv Shape",
        "checkpoint": str(required[1]),
        "inputs": input_paths,
        "cuda_device": "cuda:0",
        "gpu": device_name,
        "model_parameter_devices": parameter_devices,
        "local_files_only": True,
        "before_load": before_load,
        "after_load": after_load,
        "peak": peak,
        "after_unload": after_unload,
        "elapsed_seconds": elapsed_seconds,
        "steps": args.steps,
        "vertices": vertex_count,
        "faces": face_count,
        "output": str(args.output.resolve()),
    }
    report_path = args.output.with_suffix(".json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
